from flask import Flask, render_template, url_for, redirect, request, session, flash
from authlib.integrations.flask_client import OAuth
import secrets
from argon2 import PasswordHasher, exceptions
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import select
from models import Customer
import os

# --------------------------------------------------
# FLASK APP AND DATABASE INITIALIZATION
# --------------------------------------------------

app = Flask(__name__)       # Flask app

# Load the credentials from environment variable
load_dotenv()
the_host = os.getenv('HOST')
the_user = os.getenv('USER')
the_pass = os.getenv('PASSWORD')
the_port = os.getenv('PORT')
the_db = os.getenv('DB_NAME')


# Create the engine that connects to the database
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{the_user}:{the_pass}@{the_host}:{the_port}/{the_db}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)

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

def hashed_passwd(password:str):
    ph = PasswordHasher()
    return ph.hash(password)

# --------------------------------------------------
# DATABASE COMMUNICATION
# --------------------------------------------------

def add_customer(user_details):
    # Expected order of the input tuple is:
    # first name, last name, username, email, password_hash
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
    except Exception as e:
        db.session.rollback()

def get_customer_id(user_input):
    # Get the customer's id based on either their username or email
    if '@' in user_input:
        stmt = select(Customer).where(Customer.email == user_input)
    else:
        stmt = select(Customer).where(Customer.username == user_input)

    # Retrieve the information and return it
    result = db.session.execute(stmt).scalar_one_or_none()
    return result.id if result else None

def validate_username(username)->bool:
    stmt = select(Customer).where(Customer.username == username)
    result = db.session.execute(stmt).scalar_one_or_none()
    return True if result else False

def validate_email(email)->bool:
    stmt = select(Customer).where(Customer.email == email)
    result = db.session.execute(stmt).scalar_one_or_none()
    return True if result else False

def validate_password(user_id, password)->bool:
    ph = PasswordHasher()
    # Get the password hash for the user
    stmt = select(Customer).where(Customer.id == user_id)
    result = db.session.execute(stmt).scalar_one_or_none()
    if not result:
        return False

    password_hash = result.password_hash

    # Verify the hash
    try:
        return ph.verify(password_hash, password)
    except exceptions.VerifyMismatchError:
        return False

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
            password_hash = hashed_passwd(random_pass)
            
            # Create a base username from their email prefix
            base_username = email.split('@')[0]
            username = base_username
            
            # Ensure the username is unique in your database
            counter = 1
            while validate_username(username):
                username = f"{base_username}{counter}"
                counter += 1
                
            # Use your existing add_customer function
            user_dets = (first_name, last_name, username, email, password_hash)
            add_customer(user_dets)
            
            # Log them in
            new_user_id = get_customer_id(email)
            session['username'] = username
            flash('Google account linked and signed in successfully.', 'success')
            return redirect(url_for('profile', user_id=new_user_id))
            
    flash('Google login failed.', 'error')
    return redirect(url_for('signin'))

def is_strong_password(password: str)->bool:
    if len(password) < 12:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)

    return has_upper and has_lower and has_digit and has_symbol

# --------------------------------------------------
# TEMPLATE RENDERING AND URL ROUTING
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

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_pass = request.form.get('current-pass', '').strip()
        new_pass = request.form.get('new-pass', '').strip()
        confirm_pass = request.form.get('confirm-new-pass', '').strip()

        if not all([current_pass, new_pass, confirm_pass]):
            flash('Please complete all fields to change your password.', 'error')
            return redirect(url_for('change_password'))

        username = session.get('username')
        if not username:
            flash('Please log in first.', 'error')
            return redirect(url_for('signin'))

        user_id = get_customer_id(username)
        if not validate_password(user_id, current_pass):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('change_password'))

        if new_pass != confirm_pass:
            flash('New password and confirmation do not match.', 'error')
            return redirect(url_for('change_password'))

        if not is_strong_password(new_pass):
            flash('New password must be at least 12 chars and include upper, lower, number, and symbol.', 'error')
            return redirect(url_for('change_password'))

        # Get the customer ID then update the database with the new password
        customer = db.session.execute(select(Customer).where(Customer.id == user_id)).scalar_one_or_none()
        if customer:
            customer.password_hash = hashed_passwd(new_pass)
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('profile', user_id=user_id))

        flash('Could not find the current user, please log in again.', 'error')
        return redirect(url_for('signin'))

    return render_template('change-password.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('reset-email', '').strip()
        if not email:
            flash('Please provide your email to reset your password.', 'error')
            return redirect(url_for('forgot_password'))

        if validate_email(email):
            flash('Reset instructions sent to your email (simulated).', 'success')
        else:
            flash('Email not found in our database.', 'error')
        return redirect(url_for('signin'))

    return render_template('forgot-password.html')

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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username-signup']
        email = request.form['email-signup']
        password = request.form['pass-signup']
        confirm_password = request.form['confirm-pass']

        # If the username or email is not found in the database
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
    else:
        return render_template('signup.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
