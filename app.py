import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- 1. RAG ENGINE CONNECTION ---
try:
    # Documents search panna intha function help pannum
    from rag_engine import get_rag_response
except ImportError:
    def get_rag_response(query):
        return "Bank Knowledge Base is currently offline."

app = Flask(__name__)
app.config['SECRET_KEY'] = 'stb-bank-ultra-secret'

# Database Setup
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'stb_bank.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=1000.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(customer_id='angel').first():
            hashed_pwd = generate_password_hash('angel123', method='pbkdf2:sha256')
            admin = User(customer_id='angel', password=hashed_pwd, balance=185902.75)
            db.session.add(admin)
            db.session.commit()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cid = request.form.get('customer_id')
        pwd = request.form.get('password')
        user = User.query.filter_by(customer_id=cid).first()
        if user and check_password_hash(user.password, pwd):
            login_user(user)
            return redirect(url_for('dashboard'))
        return "❌ Login Failed! <a href='/login'>Try Again</a>"
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Glassmorphism design template call
    return render_template('dashboard.html', balance=current_user.balance)

@app.route('/transfers')
@login_required
def transfers():
    # Correct plural filename check
    return render_template('transfers.html')

@app.route('/accounts')
@login_required
def accounts():
    return render_template('accounts.html')

@app.route('/cards')
@login_required
def cards():
    return render_template('cards.html')

@app.route('/investment')
@login_required
def investment():
    return render_template('investment.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# --- OPTIMIZED AI LOGIC (RAG + Project Features) ---
@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    data = request.get_json()
    user_query = data.get('question', '').lower()
    
    # Speed Optimization: Instant reply for common project-related queries
    if "balance" in user_query:
        answer = f"Your current balance is ₹ {current_user.balance:,.2f}."
    elif "transfer" in user_query or "send money" in user_query:
        answer = "To send money, please visit the 'TRANSFERS' page from your dashboard."
    elif "logout" in user_query:
        answer = "You can logout safely using the Logout button at the top right."
    
    # External Bank Questions: Use RAG Engine
    else:
        try:
            # Bank documents search logic
            answer = get_rag_response(user_query)
        except Exception as e:
            print(f"RAG Error: {e}")
            answer = "I'm having a bit of trouble accessing our bank records. Could you try asking again?"
        
    return jsonify({"answer": answer})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(port=8000, debug=True)