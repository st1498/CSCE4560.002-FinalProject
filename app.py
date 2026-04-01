from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from authlib.integrations.flask_client import OAuth
import secrets
#from argon2 import PasswordHasher, exceptions
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import select
from models import Customer
import os
import base64
import requests
from flask_cors import CORS

# --------------------------------------------------
# FLASK APP AND DATABASE INITIALIZATION
# --------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Load environment variables
load_dotenv()

the_host = os.getenv('HOST')
the_user = os.getenv('USER')
the_pass = os.getenv('PASSWORD')
the_port = os.getenv('PORT')
the_db = os.getenv('DB_NAME')

#app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{the_user}:{the_pass}@{the_host}:{the_port}/{the_db}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

#db = SQLAlchemy(app)

# --------------------------------------------------
# PAYPAL CONFIG
# --------------------------------------------------

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_BASE = "https://api-m.sandbox.paypal.com"

# --------------------------------------------------
# OAUTH INITIALIZATION
# --------------------------------------------------

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# --------------------------------------------------
# PASSWORD HASHING
# --------------------------------------------------

#def hashed_passwd(password: str):
#    ph = PasswordHasher()
#   return ph.hash(password)

# --------------------------------------------------
# PAYPAL TOKEN HELPER
# --------------------------------------------------

def get_paypal_access_token():

    auth = base64.b64encode(
        f"{PAYPAL_CLIENT_ID}:{PAYPAL_SECRET}".encode()
    ).decode()

    response = requests.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=10
    )

    if response.status_code != 200:
        print("[PayPal ERROR] Token request failed:", response.text)
        return None

    return response.json()["access_token"]

# --------------------------------------------------
# DATABASE COMMUNICATION
# --------------------------------------------------

def add_customer(user_details):

    first_name, last_name, username, email, password_hash = user_details

    new_customer = Customer(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password_hash=password_hash
    )

    try:
        db.session.add(new_customer)
        db.session.commit()
    except Exception:
        db.session.rollback()

def get_customer_id(user_input):

    if '@' in user_input:
        stmt = select(Customer).where(Customer.email == user_input)
    else:
        stmt = select(Customer).where(Customer.username == user_input)

    result = db.session.execute(stmt).scalar_one_or_none()
    return result.id if result else None

def validate_username(username) -> bool:
    stmt = select(Customer).where(Customer.username == username)
    result = db.session.execute(stmt).scalar_one_or_none()
    return True if result else False

def validate_email(email) -> bool:
    stmt = select(Customer).where(Customer.email == email)
    result = db.session.execute(stmt).scalar_one_or_none()
    return True if result else False

def validate_password(user_id, password) -> bool:

    ph = PasswordHasher()

    stmt = select(Customer).where(Customer.id == user_id)
    result = db.session.execute(stmt).scalar_one_or_none()

    if not result:
        return False

    password_hash = result.password_hash

    try:
        return ph.verify(password_hash, password)
    except exceptions.VerifyMismatchError:
        return False

# --------------------------------------------------
# GOOGLE LOGIN
# --------------------------------------------------

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def google_authorize():

    token = google.authorize_access_token()
    user_info = token.get('userinfo')

    if user_info:

        email = user_info.get('email')
        first_name = user_info.get('given_name', 'Google')
        last_name = user_info.get('family_name', 'User')

        user_id = get_customer_id(email)

        if user_id:

            customer = db.session.execute(
                select(Customer).where(Customer.id == user_id)
            ).scalar_one_or_none()

            session['username'] = customer.username
            flash('Signed in with Google successfully.', 'success')
            return redirect(url_for('profile', user_id=user_id))

        else:

            random_pass = secrets.token_urlsafe(16)
            password_hash = hashed_passwd(random_pass)

            base_username = email.split('@')[0]
            username = base_username

            counter = 1
            while validate_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            user_dets = (first_name, last_name, username, email, password_hash)
            add_customer(user_dets)

            new_user_id = get_customer_id(email)
            session['username'] = username

            flash('Google account linked and signed in successfully.', 'success')
            return redirect(url_for('profile', user_id=new_user_id))

    flash('Google login failed.', 'error')
    return redirect(url_for('signin'))

# --------------------------------------------------
# PASSWORD STRENGTH
# --------------------------------------------------

def is_strong_password(password: str) -> bool:

    if len(password) < 12:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    return has_upper and has_lower and has_digit and has_symbol

# --------------------------------------------------
# WEBSITE ROUTES
# --------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/product/<pk>')
def product_page(pk):

    if pk == '1':
        return render_template('product1.html')

    elif pk == '2':
        return render_template('product2.html')

    else:
        return redirect(url_for('index'))

@app.route('/profile/<user_id>')
def profile(user_id):
    return render_template('profile.html', user_id=user_id)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

# --------------------------------------------------
# SIGNIN
# --------------------------------------------------

@app.route('/signin', methods=['GET', 'POST'])
def signin():

    if request.method == 'POST':

        username = request.form.get('username-field', '').strip()
        password = request.form.get('password-field', '').strip()

        if not username or not password:
            flash('Please enter both username/email and password.', 'error')
            return redirect(url_for('signin'))

        user_id = get_customer_id(username)

        if user_id and validate_password(user_id, password):

            session['username'] = username
            flash('Signed in successfully.', 'success')

            return redirect(url_for('profile', user_id=user_id))

        flash('Incorrect username/email or password.', 'error')
        return redirect(url_for('signin'))

    return render_template('signin.html')

# --------------------------------------------------
# SIGNUP
# --------------------------------------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        fullname = request.form['fullname']
        username = request.form['username-signup']
        email = request.form['email-signup']
        password = request.form['pass-signup']
        confirm_password = request.form['confirm-pass']

        if not validate_username(username) and not validate_email(email):

            if password != confirm_password:
                flash('Password and confirm password do not match.', 'error')
                return redirect(url_for('signup'))

            password_hash = hashed_passwd(password)

            first_name = fullname.strip().split(' ')[0]
            last_name = fullname.strip().split(' ')[-1]

            user_dets = (first_name, last_name, username, email, password_hash)
            add_customer(user_dets)

            flash('Signup successful. Please sign in.', 'success')
            return redirect(url_for('signin'))

        flash('Username or email already exists.', 'error')
        return redirect(url_for('signup'))

    return render_template('signup.html')

# --------------------------------------------------
# PAYPAL ROUTES
# --------------------------------------------------


@app.route("/api/paypal/create-order", methods=["POST"])
def paypal_create_order():
    token = get_paypal_access_token()
    if not token:
        return jsonify({"error": "PayPal authentication failed"}), 500

    order_body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {"currency_code": "USD", "value": "10.00"},
                "description": "CyberMax Security Order"
            }
        ]
    }

    try:
        response = requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json=order_body,
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("[PayPal ERROR] Order creation failed:", e)
        return jsonify({"error": "Order creation failed", "details": str(e)}), 500

    return jsonify(response.json())


@app.route("/api/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    data = request.get_json()
    if not data or "orderID" not in data:
        return jsonify({"error": "Missing orderID in request body"}), 400

    orderID = data["orderID"]

    token = get_paypal_access_token()
    if not token:
        return jsonify({"error": "PayPal authentication failed"}), 500

    try:
        response = requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{orderID}/capture",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}"
            },
            timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("[PayPal ERROR] Capture failed:", e)
        return jsonify({"error": "Capture failed", "details": str(e)}), 500

    return jsonify(response.json())

# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)