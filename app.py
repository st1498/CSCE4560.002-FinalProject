from flask import Flask, render_template, url_for, redirect, request, session, flash, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from authlib.integrations.flask_client import OAuth
from flask_limiter.util import get_remote_address
from models import Base, Customer, Subscription
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
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
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_for=1)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['PREFERRED_URL_SCHEME'] = 'https'

# --------------------------------------------------
# RATE LIMITING CONFIGURATION
# --------------------------------------------------

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour", "10 per minute"],
    storage_uri="redis://localhost:6379",
    strategy="fixed-window",
)

# Load the credentials from environment variable
load_dotenv('/var/www/html/.env')

the_host = os.getenv('HOST')
the_user = os.getenv('USER')
the_pass = os.getenv('PASSWORD')
the_port = os.getenv('PORT')
the_db = os.getenv("DB_NAME")

# Connect to the database using SQLAlchemy
#app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{the_user}:{the_pass}@{the_host}:{the_port}/{the_db}'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

db = SQLAlchemy(model_class=Base)
db.init_app(app)
with app.app_context():
    db.create_all()

# --------------------------------------------------
# PAYPAL CONFIG
# --------------------------------------------------

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "").strip()
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "").strip()
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
        password_hash= "GOOGLE_OAUTH_ONLY"
    )

    try:
        db.session.add(new_customer)
        db.session.commit()
        return new_customer.id
    except Exception as e:
        db.session.rollback()
        print("[DB ERROR] Could not add customer:", repr(e))
        return None


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
@limiter.limit("10 per minute")
def google_login():
    redirect_uri = url_for('google_authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri)


@app.route('/login/google/authorize')
def google_authorize():
    try:
        token = google.authorize_access_token()
        user_info = google.get(
            'https://openidconnect.googleapis.com/v1/userinfo'
        ).json()

        if not user_info:
            flash('Google login failed.', 'error')
            return redirect(url_for('signin'))

        email = user_info.get('email')
        first_name = user_info.get('given_name', 'Google')
        last_name = user_info.get('family_name', 'User')

        if not email:
            flash('Google account did not provide an email.', 'error')
            return redirect(url_for('signin'))

        # Check if this Google email already exists
        existing_user = db.session.execute(
            select(Customer).where(Customer.email == email)
        ).scalar_one_or_none()

        if existing_user:
            session['username'] = existing_user.username
            session['user_id'] = existing_user.id

            flash('Signed in with Google successfully.', 'success')
            return redirect(url_for('profile'))

        # Create username from email
        base_username = email.split('@')[0]
        username = base_username

        counter = 1
        while validate_username(username):
            username = f"{base_username}{counter}"
            counter += 1


        new_customer = Customer(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password_hash= "GOOGLE_OAUTH_ONLY"
        )

        db.session.add(new_customer)
        db.session.commit()

        session['username'] = new_customer.username
        session['user_id'] = new_customer.id

        flash('Google account linked and signed in successfully.', 'success')
        return redirect(url_for('profile'))

    except Exception as e:
        db.session.rollback()
        import traceback
        print("[GOOGLE OAUTH ERROR]", repr(e))
        traceback.print_exc()

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
@limiter.limit("10 per minute")
def checkout():
   
    return render_template(
        'checkout.html',
        paypal_client_id=PAYPAL_CLIENT_ID
    )

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

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']

    user = db.session.get(Customer, user_id)
    if not user:
        session.clear()
        flash("Profile not found. Please sign in again.", "error")
        return redirect(url_for('signin'))

    stmt = select(Subscription).where(Subscription.customer_id == user_id)
    subscriptions = db.session.execute(stmt).scalars().all()

    return render_template('profile.html', user=user, subscriptions=subscriptions)

@app.route('/change_password')
@limiter.limit("5 per minute")
def change_password():
    flash('Password management is disabled. Please sign in with Google.', 'info')
    return redirect(url_for('signin'))

@app.route('/forgot_password')
@limiter.limit("5 per minute")
def forgot_password():
    flash('Password recovery is disabled. Please sign in with Google.', 'info')
    return redirect(url_for('signin'))

@app.route('/signin')
@limiter.limit("5 per minute")
def signin():
    return render_template('signin.html')

@app.route('/signup')
@limiter.limit("5 per minute")
def signup():
    return render_template('signup.html')

# --------------------------------------------------
# PAYPAL ROUTES
# --------------------------------------------------

@app.route("/api/paypal/create-order", methods=["POST"])
@limiter.limit("10 per minute")
def create_order():
    try:
        order = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": "9.99"
                }
            }]
        }

        # Call PayPal API
        access_token = get_paypal_access_token()

        response = requests.post(
            "https://api-m.sandbox.paypal.com/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order
        )

        data = response.json()

        print("PAYPAL RESPONSE:", data)

        return jsonify({
            "id": data["id"]
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route("/api/paypal/capture-order", methods=["POST"])
@limiter.limit("10 per minute")
def capture_order(order_id):
    if "customer_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    try:
        access_token = get_paypal_token()

        response = requests.post(
            f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )

        data = response.json()
        print("PAYPAL CAPTURE RESPONSE:", data)

        if response.status_code not in [200, 201] or data.get("status") != "COMPLETED":
            return jsonify({"error": "Payment not completed", "paypal_response": data}), 400

        # save purchased product to user here
        product_id = session.get("checkout_product_id")

        purchase = Subscription(
            customer_id=session["customer_id"],
            product_id=product_id,
            paypal_order_id=order_id,
            status="active"
        )

        db.session.add(purchase)
        db.session.commit()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        print("CAPTURE ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
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
@limiter.limit("10 per minute")
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

# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized request"}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden request"}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "status": 429,
        "error": "Too many requests",
        "message": "Rate limit exceeded. Please try again later.",
    }), 429

#@app.errorhandler(500)
#def server_error(e):
#    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="None"
)
