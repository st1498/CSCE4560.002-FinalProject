import os
from dotenv import load_dotenv

# Load your .env explicitly
load_dotenv('/var/www/html/.env')

print("PAYPAL_CLIENT_ID =", repr(os.getenv("PAYPAL_CLIENT_ID")))
print("PAYPAL_SECRET    =", repr(os.getenv("PAYPAL_SECRET")))
print("GOOGLE_CLIENT_ID =", repr(os.getenv("GOOGLE_CLIENT_ID")))
print("GOOGLE_SECRET    =", repr(os.getenv("GOOGLE_CLIENT_SECRET")))
print("SECRET_KEY       =", repr(os.getenv("SECRET_KEY")))
