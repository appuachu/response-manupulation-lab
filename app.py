from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import random
import requests
from flask_session import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import re
import time
from datetime import datetime
from functools import wraps
import threading

app = Flask(__name__)
app.secret_key = 'VULN_SECRET_KEY'

# Server-side session config
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Email configuration (Gmail)
EMAIL_ADDRESS = 'cyberstack@technovalley.co.in'
EMAIL_PASSWORD = 'jqex rmyp dixj fkkc'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# User database
users = {
    'vishnu': {
        'password': generate_password_hash('password123'),
        'bank': 'Vishnu Bank: Account No. 123456789, IFSC: VBNK0001234',
        'email': 'vishnu@example.com'
    },
    'amal': {
        'password': generate_password_hash('password456'),
        'bank': 'Amal Bank: Account No. 987654321, IFSC: AMLB0009876',
        'email': 'amal@example.com'
    }
}

# Store OTPs temporarily
otp_storage = {}

def send_email_otp(email, username, otp):
    """Send OTP via Gmail"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = '🔐 Password Reset OTP - SecureAuth'

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #2563eb, #1e40af); padding: 20px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">🔐 SecureAuth</h1>
            </div>
            <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                <h2 style="color: #1f2937;">Hi {username},</h2>
                <p style="color: #4b5563; font-size: 16px;">You requested to reset your password. Your OTP for password reset is:</p>
                <div style="background: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <span style="font-size: 48px; font-weight: bold; color: #2563eb; letter-spacing: 10px;">{otp}</span>
                </div>
                <p style="color: #6b7280; font-size: 14px;">This OTP is valid for <strong>5 minutes</strong>.</p>
                <p style="color: #6b7280; font-size: 14px;">If you didn't request this, please ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #9ca3af; font-size: 12px; text-align: center;">SecureAuth • Security Testing Platform</p>
                <div style="background: #f3f4f6; padding: 10px; border-radius: 4px; margin-top: 15px; text-align: center;">
                    <p style="color: #4b5563; font-size: 12px; margin: 0;">
                        <strong>Developed by:</strong> Aswan, Senior Cyber Security Consultant<br>
                        <span style="color: #6b7280;">Technovalley Software India Private Limited</span>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"[INFO] OTP email sent to {email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or not session.get('authenticated', False):
            flash('Please login first!', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session and session.get('authenticated', False):
        return redirect(url_for('user_home'))
    return render_template('index3.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        bank_info = request.form.get('bank_info', 'Default Bank: Account Info')

        if not username or not password or not email:
            flash('All fields are required!', 'error')
            return render_template('register.html')

        if username in users:
            flash('Username already exists!', 'error')
            return render_template('register.html')

        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            flash('Username must be 3-20 characters and contain only letters, numbers, and underscores.', 'error')
            return render_template('register.html')

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Invalid email format!', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('register.html')

        users[username] = {
            'password': generate_password_hash(password),
            'bank': bank_info,
            'email': email
        }

        flash('🎉 Registration successful! Please login.', 'success')
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and check_password_hash(users[username]['password'], password):
            session.pop('reset_username', None)
            session.pop('otp', None)
            session.pop('otp_verified', None)

            session['username'] = username
            session['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session['authenticated'] = True
            flash(f'Welcome back, {username}! 🎉', 'success')
            return redirect(url_for('user_home'))
        else:
            flash('❌ Invalid username or password!', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        username = request.form.get('username')

        if username in users:
            otp = str(random.randint(1000, 9999))

            session['otp'] = otp
            session['reset_username'] = username
            session['otp_verified'] = False

            otp_storage[username] = {
                'otp': otp,
                'timestamp': time.time(),
                'verified': False
            }

            print(f"\n{'='*50}")
            print(f"[OTP] OTP for {username}: {otp}")
            print(f"{'='*50}\n")

            email = users[username]['email']
            try:
                email_sent = send_email_otp(email, username, otp)
                if email_sent:
                    flash('📧 OTP sent to your registered email!', 'success')
                else:
                    flash('⚠️ OTP generated! Check console for OTP.', 'warning')
            except Exception as e:
                flash('⚠️ OTP generated! Check console for OTP.', 'warning')
                print(f"[ERROR] Email error: {e}")

            return redirect(url_for('otp'))
        else:
            flash('❌ User not found!', 'error')
            return render_template('forget.html')

    return render_template('forget.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if 'reset_username' not in session:
        flash('Please request OTP first!', 'error')
        return redirect(url_for('forget'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        username = session.get('reset_username')

        if not new_password or len(new_password) < 6:
            return jsonify({
                'otp': entered_otp,
                'value': False,
                'redirect': '/otp',
                'message': 'Password must be at least 6 characters!'
            })

        # Correct OTP
        if entered_otp == session.get('otp'):
            if username in users:
                users[username]['password'] = generate_password_hash(new_password)
                session['otp_verified'] = True
                session.pop('otp', None)

                print(f"\n{'='*50}")
                print(f"[SUCCESS] Correct OTP for {username}")
                print(f"[SUCCESS] New password: {new_password}")
                print(f"{'='*50}\n")

                return jsonify({
                    'otp': entered_otp,
                    'value': True,
                    'redirect': '/dashboard-access',
                    'message': 'Valid OTP'
                })
        else:
            # Wrong OTP - VULNERABILITY: Attacker intercepts this
            print(f"[!] Wrong OTP entered: {entered_otp} for {username}")
            return jsonify({
                'otp': entered_otp,
                'value': False,
                'redirect': '/otp',
                'message': 'Invalid OTP'
            })

    return render_template('otp.html')

# CRITICAL VULNERABILITY ENDPOINT
# This endpoint grants access based ONLY on the 'value' parameter
# The attacker can manipulate the response to gain access
@app.route('/dashboard-access')
def dashboard_access():
    """VULNERABILITY: Grants access without proper validation"""
    username = session.get('reset_username')

    if username and username in users:
        # GRANT ACCESS - THIS IS THE VULNERABILITY
        session['username'] = username
        session['authenticated'] = True
        session['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        session.pop('reset_username', None)
        session.pop('otp', None)

        print(f"\n{'='*60}")
        print(f"[!] ⚠️ RESPONSE MANIPULATION ATTACK SUCCESSFUL!")
        print(f"[!] Target User: {username}")
        print(f"[!] Access granted via manipulated response!")
        print(f"[!] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        return redirect(url_for('user_home'))

    flash('Access denied! Please verify OTP.', 'error')
    return redirect(url_for('login_page'))

@app.route('/user-home')
@login_required
def user_home():
    username = session.get('username')

    if username in users:
        last_login = session.get('last_login', 'First time login')
        return render_template('user_home.html',
                             user=username,
                             bank_info=users[username]['bank'],
                             email=users[username]['email'],
                             last_login=last_login)

    flash('User not found!', 'error')
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully! 👋', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
