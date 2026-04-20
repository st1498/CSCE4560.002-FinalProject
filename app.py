from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from authlib.integrations.flask_client import OAuth
from models import Base, Customer, Subscription
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import select
from flask_cors import CORS
import requests
import secrets
import base64
import os

# --------------------------------------------------
# FLASK APP AND DATABASE INITIALIZATION
# --------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Load the credentials from environment variable
basedir = os.path.abspath(os.path.dirname(__name__))
load_dotenv(os.path.join(basedir, '.env'))

the_host = os.getenv('HOST')
the_user = os.getenv('USER')
the_pass = os.getenv('PASSWORD')
the_port = os.getenv('PORT')
the_db = os.getenv("DB_NAME")

# Connect to the database using SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{the_user}:{the_pass}@{the_host}:{the_port}/{the_db}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db = SQLAlchemy(model_class=Base)
db.init_app(app)

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


@app.route('/login/google')
def google_login():
    # Redirects the user to the Google login screen
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

        # Check if user exists by email using your existing function
        user_id = get_customer_id(email)

        if user_id:
            # User exists, grab their username and log them in
            customer = db.session.execute(select(Customer).where(Customer.id == user_id)).scalar_one_or_none()
            session['username'] = customer.username
            flash('Signed in with Google successfully.', 'success')
            return redirect(url_for('profile', user_id=user_id))
        else:
            # New user via Google: Auto-create an account
            # Generate a secure random password since they use Google to log in
            random_pass = secrets.token_urlsafe(16)
            password_hash = PasswordHasher.hash(random_pass)

            # Create a base username from their email prefix
            base_username = email.split('@')[0]
            username = base_username

            # Ensure the username is unique in your database
            counter = 1
            while validate_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            # Use your existing add_customer function
            user_details = (first_name, last_name, username, email, password_hash)
            add_customer(user_details)

            # Log them in
            new_user_id = get_customer_id(email)
            session['username'] = username
            flash('Google account linked and signed in successfully.', 'success')
            return redirect(url_for('profile', user_id=new_user_id))

    flash('Google login failed.', 'error')
    return redirect(url_for('signin'))

# --------------------------------------------------
# WEBSITE ROUTES
# --------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    if 'username' not in session:
        flash("Please log in to continue to checkout.", "warning")
        return redirect(url_for('signin'))

    return render_template('checkout.html', paypal_client_id=PAYPAL_CLIENT_ID)

@app.route('/confirmation')
def confirmation():
    if 'username' not in session:
        return redirect(url_for('signin'))
    return render_template('confirmation.html')

@app.route('/logout')
def logout():
    session.clear()  # This wipes the Flask session
    flash("You have been logged out safely.", "info")
    return redirect(url_for('index'))

@app.route('/product/<pk>')
def product_page(pk):
    if pk == '1':
        return render_template('product1.html')
    elif pk == '2':
        return render_template('product2.html')
    else:
        return redirect(url_for('index'))

@app.route('/profile/<int:user_id>')
def profile(user_id):
    # Ensure the logged-in user can only see their profile
    if 'username' not in session:
        return redirect(url_for('signin'))

    # Fetch user data
    user = db.session.get(Customer, user_id)
    if not user:
        flash("Profile not found.", "error")
        return redirect(url_for('index'))

    # Fetch subscriptions linked to this customer
    stmt = select(Subscription).where(Subscription.customer_id == user_id)
    subscriptions = db.session.execute(stmt).scalars().all()

    return render_template('profile.html', user=user, subscriptions=subscriptions)

@app.route('/change_password')
def change_password():
    flash('Password management is disabled. Please sign in with Google.', 'info')
    return redirect(url_for('signin'))

@app.route('/forgot_password')
def forgot_password():
    flash('Password recovery is disabled. Please sign in with Google.', 'info')
    return redirect(url_for('signin'))

@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

# --------------------------------------------------
# PAYPAL ROUTES
# --------------------------------------------------

@app.route("/api/paypal/create-order", methods=["POST"])
def paypal_create_order():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    total = calculate_cart_total()

    if total <= 0:
        return jsonify({"error": "Cart is empty"}), 400

    token = get_paypal_access_token()
    if not token:
        return jsonify({"error": "PayPal authentication failed"}), 500

    order_body = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "amount": {
                    "currency_code": "USD",
                    "value": f"{total:.2f}"
                },
                "description": "Safelock Security Order"
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
        return jsonify({"error": "Order creation failed"}), 500

    return jsonify(response.json())

@app.route("/api/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data or "orderID" not in data:
        return jsonify({"error": "Missing orderID"}), 400

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
        return jsonify({"error": "Capture failed"}), 500

    # Clear cart after successful payment
    session.pop('cart', None)

    return jsonify(response.json())
# --------------------------------------------------
# CART HELPERS
# --------------------------------------------------

def get_cart():
    """Retrieve cart from session"""
    return session.get('cart', [])


def calculate_cart_total():
    """Calculate total price of cart"""
    cart = get_cart()
    total = sum(item['price'] * item['qty'] for item in cart)
    return round(total, 2)

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    item = {
        "name": data.get("name"),
        "price": float(data.get("price")),
        "qty": int(data.get("qty", 1))
    }

    cart = session.get('cart', [])
    cart.append(item)
    session['cart'] = cart

    return jsonify({"message": "Item added", "cart": cart})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
