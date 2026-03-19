from django.db import models
from django.db.models.functions import Now


# Database to store product information
class Product(models.Model):   
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

# Database to store customer information
class Customer(models.Model):
    product_id = models.ForeignKey(Product, on_delete=models.PROTECT)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    username = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    password_hash = models.CharField(max_length=255)
    date_registered = models.DateTimeField(db_default=Now())

# Database to store order information
class Order(models.Model):
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('sold', 'Sold'),
    ]
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    product_id = models.ForeignKey(Product, on_delete=models.PROTECT)
    order_date = models.DateTimeField(db_default=Now())
    num_items = models.IntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)

# Database to store subscription information
class Subscription(models.Model):
    customer_id = models.ForeignKey(Customer, on_delete=models.PROTECT)
    product_id = models.ForeignKey(Product, on_delete=models.PROTECT)
    licence_key = models.CharField(max_length=20)
    subscribed = models.BooleanField(default=True)
    expiry_date = models.DateTimeField()
