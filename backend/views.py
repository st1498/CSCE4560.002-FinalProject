from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Customer
from .forms import SignInForm, SignUpForm, ChangePassword
from argon2 import PasswordHasher

# Home page
def index(request):
    return render(request, 'index.html')

# Function that displays the details of the VPN
def product1(request):
    return render(request, 'product1.html')

# Function that displays the details of the SaS
def product2(request):
    return render(request, 'product2.html')

# Function to handle sign in
def signin(request):
    return render(request, 'signin.html')

# Function to handle sign up
def signup(request):
    return render(request, 'signup.html')

# Function to change the user's password
def change_password(request):
    return render(request, 'change-password.html')

# Function to handle forgot password
def forgot_password(request):
    return render(request, 'forgot-password.html')
