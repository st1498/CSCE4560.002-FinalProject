from sqlalchemy import String, DateTime, Enum, Numeric, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from decimal import Decimal
import enum

# --------------------------------------------------
# DEFINING THE TABLES FOR THE DATABASE
# --------------------------------------------------

# Base Model
class Base(DeclarativeBase):
    pass

# Create the Products table
class Product(Base):
    __tablename__ = 'Products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column()
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))

# Create the Customers table
class Customer(Base):
    __tablename__ = 'Customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(20))
    last_name: Mapped[str] = mapped_column(String(20))
    username: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str] = mapped_column(String(20), unique=True)
    password_hash: Mapped[str] = mapped_column(String(250), unique=True)
    date_registered: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# Create the Orders table and an Enum class for the order status
class OrderStatus(enum.Enum):
    pending = 'pending',
    sold = 'sold'

class Order(Base):
    __tablename__ = 'Orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    num_items: Mapped[int] = mapped_column()
    total_cost: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus))
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id))
    customer_id: Mapped[int] = mapped_column(ForeignKey(Customer.id))

# Create the Subscriptions table
class Subscription(Base):
    __tablename__ = 'Subscriptions'
    id: Mapped[int] = mapped_column(primary_key=True)
    license_key: Mapped[str] = mapped_column(String(20), unique=True)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    product_id: Mapped[int] = mapped_column(ForeignKey(Product.id))
    customer_id: Mapped[int] = mapped_column(ForeignKey(Customer.id))
