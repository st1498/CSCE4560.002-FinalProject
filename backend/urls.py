from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),

    # Product pages
    path('product1/', views.product1, name='Product 1'),
    path('product2/', views.product2, name='Product 2'),

    # User account management
    path('change-password/', views.change_password, name='Change Password'),
    path('forgot-password/', views.forgot_password, name='Forgot Password'),
    path('signin/', views.signin, name='Sign In'),
    path('signup/', views.signup, name='Sign Up')
]