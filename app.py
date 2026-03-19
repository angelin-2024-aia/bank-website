import os
import requests
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "stb-bank-ultra-secret-2026"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "stb_bank.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db            = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

ML_API = "http://127.0.0.1:8000/classify"

def check_security():
    try:
        r = requests.post(ML_API, json={"attack_type": "normal"}, timeout=1)
        return r.json()
    except Exception:
        return {"anomaly": "normal"}

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id          = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    balance     = db.Column(db.Float, default=1000.0)
    full_name   = db.Column(db.String(100), default="STB Customer")
    email       = db.Column(db.String(120), default="customer@stbbank.com")
    is_frozen   = db.Column(db.Boolean, default=False)

class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"
    id          = db.Column(db.Integer, primary_key=True)
    ts_utc      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source_ip   = db.Column(db.String(64))
    customer_id = db.Column(db.String(64))
    success     = db.Column(db.Boolean)
    reason      = db.Column(db.String(64))

class Transaction(db.Model):
    __tablename__ = "transactions"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    ts_utc      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    amount      = db.Column(db.Float)
    to_account  = db.Column(db.String(30))
    note        = db.Column(db.String(100))
    status      = db.Column(db.String(20), default="success")

class LoanApplication(db.Model):
    __tablename__ = "loan_applications"
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    ts_utc      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    loan_type   = db.Column(db.String(50))
    amount      = db.Column(db.Float)
    status      = db.Column(db.String(20), default="Pending")

class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id          = db.Column(db.Integer, primary_key=True)
    ts_utc      = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    name        = db.Column(db.String(100))
    email       = db.Column(db.String(120))
    subject     = db.Column(db.String(200))
    message     = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(customer_id="angel").first():
            db.session.add(User(
                customer_id="angel",
                password=generate_password_hash("angel123"),
                balance=185902.75,
                full_name="Angel Priya",
                email="angel@stbbank.com"
            ))
            db.session.commit()
def rule_based_detection(username, password):
    # SQL Injection patterns
    if "'" in username or "OR" in username.upper():
        return True

    # Very short password (suspicious)
    if len(password) < 3:
        return True

    return False
def record_attempt(cid, success, reason):
    db.session.add(LoginAttempt(
        ts_utc=datetime.now(timezone.utc),
        source_ip=request.remote_addr,
        customer_id=cid, success=success, reason=reason
    ))
    db.session.commit()
user_attempts = {}
def log_attack(username, password):
    record_attempt(username, False, "ML_Detected_Attack")
def get_attempts(ip):
    if ip not in user_attempts:
        user_attempts[ip] = 0
    user_attempts[ip] += 1
    return user_attempts[ip]


user_last_time = {}

def get_time_gap(ip):
    import time
    now = time.time()
    
    if ip in user_last_time:
        gap = now - user_last_time[ip]
    else:
        gap = 5  # assume normal first attempt
    
    user_last_time[ip] = now
    return gap
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    msg = None
    if request.method == "POST":
        db.session.add(ContactMessage(
            name=request.form.get("name",""),
            email=request.form.get("email",""),
            subject=request.form.get("subject",""),
            message=request.form.get("message","")
        ))
        db.session.commit()
        msg = ("success", "Message sent! We will reply within 24 hours.")
    return render_template("contact.html", msg=msg)

@app.route("/status")
def get_status():
    last = LoginAttempt.query.filter_by(success=False).order_by(LoginAttempt.ts_utc.desc()).first()
    if last:
        delta = (datetime.now(timezone.utc) - last.ts_utc.replace(tzinfo=timezone.utc)).seconds
        status = "ATTACK" if delta < 60 else "NORMAL"
    else:
        status = "NORMAL"
    return jsonify({"status": status})

from flask import request
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'GET':
        return render_template("login.html")

    data = request.get_json()
    username = data.get('customer_id')
    password = data.get('password')

    ip = request.remote_addr

    attempts = get_attempts(ip)

    # 🚨 Attack detection
    if attempts > 5:

        log_attack(username, password)

        # ✅ send to WSL
        try:
            requests.post("http://172.31.145.94:5000/log", json={
                "username": username,
                "password": password,
                "ip": ip,
                "attack_type": "brute_force"
            }, timeout=1)
        except Exception as e:
            print("WSL error:", e)

        return jsonify({
            "success": True,
            "redirect": "/fake_dashboard"
        })

    # 🔐 Normal login
    user = User.query.filter_by(customer_id=username).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({
            "success": True,
            "redirect": "/dashboard"
        })

    return jsonify({"success": False})

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.ts_utc.desc()).limit(5).all()
    return render_template("dashboard.html", balance=current_user.balance, transactions=txns)

@app.route("/accounts")
@login_required
def accounts():
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.ts_utc.desc()).limit(5).all()
    return render_template("accounts.html", transactions=txns)

@app.route("/cards")
@login_required
def cards():
    return render_template("cards.html")

@app.route("/investment")
@login_required
def investment():
    return render_template("investment.html")

@app.route("/loans")
@login_required
def loans():
    my_loans = LoanApplication.query.filter_by(user_id=current_user.id).order_by(LoanApplication.ts_utc.desc()).all()
    return render_template("loans.html", my_loans=my_loans)

@app.route("/support")
@login_required
def support():
    return render_template("support.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/statements")
@login_required
def statements():
    all_txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.ts_utc.desc()).all()
    return render_template("statements.html", transactions=all_txns)

@app.route("/transfers", methods=["GET", "POST"])
@login_required
def transfers():
    msg = None
    if request.method == "POST":
        to_acc = request.form.get("to_account", "").strip()
        try:
            amt = float(request.form.get("amount", 0))
        except ValueError:
            amt = 0
        note = request.form.get("note", "")
        if current_user.is_frozen:
            msg = ("error", "Your account is frozen. Please contact support.")
        elif amt <= 0:
            msg = ("error", "Amount must be greater than zero.")
        elif amt > current_user.balance:
            msg = ("error", "Insufficient balance.")
        elif not to_acc:
            msg = ("error", "Please enter a valid account number.")
        else:
            current_user.balance -= amt
            db.session.add(Transaction(user_id=current_user.id, amount=amt, to_account=to_acc, note=note))
            db.session.commit()
            msg = ("success", f"Rs.{amt:,.2f} transferred to {to_acc} successfully!")
    txns = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.ts_utc.desc()).limit(10).all()
    return render_template("transfers.html", msg=msg, transactions=txns)

@app.route("/update-profile", methods=["POST"])
@login_required
def update_profile():
    full_name = request.form.get("full_name", "").strip()
    email     = request.form.get("email", "").strip()
    if full_name: current_user.full_name = full_name
    if email:     current_user.email     = email
    db.session.commit()
    return redirect(url_for("settings") + "?msg=success:Profile updated successfully!")

@app.route("/change-pin", methods=["POST"])
@login_required
def change_pin():
    old_pin = request.form.get("old_pin", "")
    new_pin = request.form.get("new_pin", "")
    if not check_password_hash(current_user.password, old_pin):
        return redirect(url_for("cards") + "?msg=error:Old password is incorrect!")
    if len(new_pin) < 4:
        return redirect(url_for("cards") + "?msg=error:Password must be at least 4 characters!")
    current_user.password = generate_password_hash(new_pin)
    db.session.commit()
    return redirect(url_for("cards") + "?msg=success:Password changed successfully!")

@app.route("/apply-loan", methods=["POST"])
@login_required
def apply_loan():
    loan_type = request.form.get("loan_type", "Personal Loan")
    try:
        amount = float(request.form.get("loan_amount", 0))
    except ValueError:
        amount = 0
    if amount <= 0:
        return redirect(url_for("loans") + "?msg=error:Please enter a valid amount!")
    db.session.add(LoanApplication(user_id=current_user.id, loan_type=loan_type, amount=amount))
    db.session.commit()
    return redirect(url_for("loans") + f"?msg=success:Loan application submitted successfully!")

@app.route("/block-card", methods=["POST"])
@login_required
def block_card():
    return redirect(url_for("cards") + "?msg=success:Card blocked! Contact support to unblock.")

@app.route("/freeze-cards", methods=["POST"])
@login_required
def freeze_cards():
    current_user.is_frozen = True
    db.session.commit()
    logout_user()
    return redirect(url_for("login"))
@app.route("/honeypot-action", methods=["POST"])
def honeypot_action():
    data = request.get_json()

    print("🚨 Attacker Action:", data)   # terminal log

    # optional: store in DB
    db.session.add(LoginAttempt(
        customer_id=data.get("user", "unknown"),
        success=False,
        reason="HONEYPOT_ACTIVITY"
    ))
    db.session.commit()

    return {"status": "logged"}
@app.route("/fake_dashboard")
def fake_dashboard():
    return render_template("honeypot/fake_dashboard.html")

@app.route("/api/last-attack-type")
def get_last_attack():
    last = LoginAttempt.query.filter_by(success=False).order_by(LoginAttempt.ts_utc.desc()).first()
    if last:
        return jsonify({"attack_type": last.reason, "customer_id": last.customer_id, "ip_address": last.source_ip, "timestamp": last.ts_utc.strftime("%Y-%m-%d %H:%M:%S UTC"), "status": "Blocked by AI Shield"})
    return jsonify({"attack_type": "None", "message": "No attacks detected."})

@app.route("/api/attack-log")
def attack_log():
    attempts = LoginAttempt.query.filter_by(success=False).order_by(LoginAttempt.ts_utc.desc()).limit(20).all()
    return jsonify([{"ip": a.source_ip, "id": a.customer_id, "reason": a.reason, "timestamp": a.ts_utc.strftime("%Y-%m-%d %H:%M:%S")} for a in attempts])

@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    try:
        from rag_engine import get_rag_response
        data = request.get_json()
        answer = get_rag_response(data.get("question", ""))
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"AI engine offline. ({str(e)})"})

@app.route("/api/rag-query", methods=["POST"])
def rag_query():
    return ask_ai()

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001, debug=True)
