from django import forms

class SignInForm(forms.Form):
    username_field = forms.CharField(max_length=30)
    password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())

class SignUpForm(forms.Form):
    full_name = forms.CharField(max_length=50)
    username = forms.CharField(max_length=20)
    email = forms.EmailField()
    password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())
    confirm_password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())

class ChangePassword(forms.Form):
    curr_password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())
    new_password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())
    confirm_password = forms.CharField(min_length=8, max_length=64, widget=forms.PasswordInput())

class PaymentDetails(forms.Form):
    pass