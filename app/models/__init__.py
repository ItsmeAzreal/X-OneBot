"""
Database models package.

This file makes it easy to import all models at once.
It also ensures all models are registered with SQLAlchemy.
"""
from app.models.base import BaseModel, Base
from app.models.business import Business, SubscriptionPlan, PhoneNumberType
from app.models.user import User, UserRole
from app.models.menu import MenuCategory, MenuItem
from app.models.table import Table, TableStatus
from app.models.order import Order, OrderStatus, PaymentStatus, PaymentMethod
from app.models.message import Message 
from app.models.phone_number import PhoneNumber, NumberStatus, NumberProvider
# Export all models
__all__ = [
    # Base
    "BaseModel",
    "Base",
    
    # Business
    "Business",
    "SubscriptionPlan",
    
    # User
    "User", 
    "UserRole",
    
    # Menu
    "MenuCategory",
    "MenuItem",
    
    # Table
    "Table",
    "TableStatus",
    
    # Order
    "Order",
    "OrderStatus",
    "PaymentStatus",
    "PaymentMethod",

    # ADD Message to this list
    "Message",
]