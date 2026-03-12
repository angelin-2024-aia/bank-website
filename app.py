import os
import requests
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# ---------------- APP SETUP ----------------
app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "stb-bank-ultra-secret"

# Database file path setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "stb_bank.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- ML API CONFIG ----------------
# ML server unga laptop-laye run aagudhu-na 127.0.0.1 use pannunga
# Vera machine-na andha machine-oda IP-ah podunga
ML_API = "http://127.0.0.1:5000/classify"

def check_security():
    """Calls the ML server to check for anomalies during login."""
    try:
        print("Calling ML server...")
        response = requests.post(
            ML_API,
            json={"attack_type": "phishing"}, # Simulation input
            timeout=5
        )
        return response.json()
    except Exception as e:
        print(f"ML Server Error: {e}")
        # Server off-la irundha normal-ah allow panna indha fallback
        return {"anomaly": "normal"}

# ---------------- MODELS ----------------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=1000.0)

class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"
    id = db.Column(db.Integer, primary_key=True)
    ts_utc = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source_ip = db.Column(db.String(64))
    customer_id = db.Column(db.String(64))
    success = db.Column(db.Boolean)
    reason = db.Column(db.String(64))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ---------------- DB INIT ----------------
def init_db():
    with app.app_context():
        db.create_all()
        # Default user creation for demo
        if not User.query.filter_by(customer_id="angel").first():
            hashed_pwd = generate_password_hash("angel123")
            user = User(
                customer_id="angel",
                password=hashed_pwd,
                balance=185902.75
            )
            db.session.add(user)
            db.session.commit()

# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def get_status():
    """Used by frontend to check system health or global attack status."""
    return jsonify({"status": "NORMAL"})
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form
        cid = data.get("customer_id")
        pwd = data.get("password")

        # 🚨 STEP 1 — CALL ML SERVER FOR ATTACK DETECTION
        ml_result = check_security()

        # 🚨 STEP 2 — If ML detects 'anomaly', send to FAKE DASHBOARD (The Trap)
        if ml_result.get("anomaly") == "anomaly":
            record_attempt(cid or "unknown", False, "ml_detected_attack")
            return jsonify({
                "success": True, # Success nu sonna dhaan JS redirect pannum
                "redirect": "/fake_dashboard"
            })

        # ✅ STEP 3 — Normal Authentication
        user = User.query.filter_by(customer_id=cid).first()

        # 🚨 STEP 4 — If password is wrong, also send to FAKE DASHBOARD (Honeypot Logic)
        if not user or not check_password_hash(user.password, pwd):
            record_attempt(cid, False, "auth_failed")
            # Attacker-ah ematha namba "Success" nu solli fake page-ku anupuroam
            return jsonify({
                "success": True,
                "redirect": "/fake_dashboard"
            })

        # SUCCESSFUL LOGIN (Real User)
        record_attempt(cid, True, "ok")
        login_user(user)

        return jsonify({
            "success": True,
            "redirect": "/dashboard"
        })

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", balance=current_user.balance)

# ---------------- FUNCTIONAL PAGES ----------------
# Indha routes irundha dhaan dashboard-la irukura buttons vela seiyum

@app.route("/transfers")
@login_required
def transfers():
    return render_template("transfers.html")

@app.route("/accounts")
@login_required
def accounts():
    return render_template("accounts.html")

@app.route("/cards")
@login_required
def cards():
    return render_template("cards.html")

@app.route("/investment")
@login_required
def investment():
    return render_template("investment.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/fake_dashboard")
def fake_dashboard():
    """Redirect target for isolated 'attackers' in the honeypot demo."""
    return render_template("honeypot/fake_dashboard.html")

# ---------------- API ENDPOINTS ----------------

@app.route("/api/last-attack-type")
def get_last_attack():
    """Fetches the most recent failed login attempt for the dashboard live feed."""
    last_attack = LoginAttempt.query.filter_by(success=False).order_by(LoginAttempt.ts_utc.desc()).first()
    
    if last_attack:
        return jsonify({
            "attack_type": last_attack.reason,
            "customer_id": last_attack.customer_id,
            "ip_address": last_attack.source_ip,
            "timestamp": last_attack.ts_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Blocked by AI Shield"
        })
    else:
        return jsonify({
            "attack_type": "None",
            "message": "No attacks detected recently."
        })

# ---------------- HELPERS ----------------

def record_attempt(cid, success, reason):
    """Records every login attempt into the database for logging/analysis."""
    attempt = LoginAttempt(
        ts_utc=datetime.now(timezone.utc),
        source_ip=request.remote_addr,
        customer_id=cid,
        success=success,
        reason=reason
    )
    db.session.add(attempt)
    db.session.commit()

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    # host="0.0.0.0" allows external devices like Siva's laptop to connect
    app.run(host="0.0.0.0", port=8000, debug=True)