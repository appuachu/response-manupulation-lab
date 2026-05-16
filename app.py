from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import requests
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'VULN_SECRET_KEY'

# Server-side session config
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# Telegram bot details
TELEGRAM_BOT_TOKEN = '7745704358:AAEtaEE0kRGIojxESI0al7CS3HQey-I1RsM'
TELEGRAM_CHAT_ID = '7648971114'

# Hardcoded user info
users = {
    'vishnu': {
        'bank': 'Vishnu Bank: Account No. 123456789, IFSC: VBNK0001234'
    },
    'amal': {
        'bank': 'Amal Bank: Account No. 987654321, IFSC: AMLB0009876'
    }
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[ERROR] Failed to send Telegram message: {e}")

@app.route('/')
def index():
    return render_template('index3.html')

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        username = request.form.get('username')
        if username in users:
            otp = str(random.randint(1000, 9999))
            session['otp'] = otp
            session['username'] = username
            debug_msg = f"[DEBUG] OTP for {username}: {otp}"
            print(debug_msg)
            send_telegram_message(debug_msg)
            return redirect(url_for('otp'))
        return "User not found", 404
    return render_template('forget.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if entered_otp == session.get('otp'):
            return jsonify({
                'otp': entered_otp,
                'value': True,
                'redirect': '/'
            })
        else:
            return jsonify({
                'otp': entered_otp,
                'value': False,
                'redirect': '/login',
                'message': 'Invalid OTP'
            })
    return render_template('otp.html')

@app.route('/user-home')
def user_home():
    username = session.get('username')
    if username in users:
        return render_template('user_home.html', user=username, bank_info=users[username]['bank'])
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return "<h3>Login failed or redirected. Invalid OTP.</h3>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008, debug=True)
