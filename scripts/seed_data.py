"""Seed database with sample data for testing."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models import Business, User, MenuCategory, MenuItem, Table, UserRole
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_data():
    """Add sample data to database."""
    db: Session = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Business).first():
            logger.info("Database already has data. Skipping seed.")
            return
        
        logger.info("Seeding database with sample data...")
        
        # Create sample business
        business = Business(
            name="Demo Cafe",
            slug="demo-cafe",
            description="A cozy cafe for testing XoneBot",
            subscription_plan="pro",
            contact_info={
                "phone": "+1234567890",
                "email": "demo@cafe.com",
                "address": "123 Demo Street"
            },
            settings={
                "working_hours": {
                    "mon": "8:00-20:00",
                    "tue": "8:00-20:00",
                    "wed": "8:00-20:00",
                    "thu": "8:00-20:00",
                    "fri": "8:00-22:00",
                    "sat": "9:00-22:00",
                    "sun": "9:00-18:00"
                },
                "languages": ["en", "es", "fr"],
                "timezone": "America/New_York"
            },
            branding_config={
                "primary_color": "#FF6B6B",
                "secondary_color": "#4ECDC4",
                "logo_url": "https://example.com/logo.png",
                "bot_personality": "friendly"
            }
        )
        db.add(business)
        db.commit()
        
        # Create admin user
        admin = User(
            email="admin@democafe.com",
            hashed_password=get_password_hash("demo123456"),
            name="Demo Admin",
            role=UserRole.OWNER,
            business_id=business.id,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        
        # Create staff user
        staff = User(
            email="staff@democafe.com",
            hashed_password=get_password_hash("staff123456"),
            name="Demo Staff",
            role=UserRole.STAFF,
            business_id=business.id,
            is_active=True,
            is_verified=True
        )
        db.add(staff)
        
        # Create menu categories
        beverages = MenuCategory(
            business_id=business.id,
            name="Beverages",
            description="Coffee, tea, and cold drinks",
            display_order=1,
            icon="☕"
        )
        db.add(beverages)
        
        food = MenuCategory(
            business_id=business.id,
            name="Food",
            description="Sandwiches, salads, and snacks",
            display_order=2,
            icon="🥪"
        )
        db.add(food)
        
        desserts = MenuCategory(
            business_id=business.id,
            name="Desserts",
            description="Sweet treats and pastries",
            display_order=3,
            icon="🍰"
        )
        db.add(desserts)
        
        db.commit()
        
        # Create menu items - Beverages
        cappuccino = MenuItem(
            business_id=business.id,
            category_id=beverages.id,
            name="Cappuccino",
            description="Rich espresso with steamed milk foam",
            base_price=4.50,
            preparation_time=5,
            dietary_tags=["vegetarian"],
            allergens=["milk"],
            calories=120,
            customizations=[
                {
                    "name": "Size",
                    "options": ["Small", "Medium", "Large"],
                    "price_diff": [0, 1.0, 2.0]
                },
                {
                    "name": "Milk",
                    "options": ["Regular", "Oat", "Almond", "Soy"],
                    "price_diff": [0, 0.5, 0.5, 0.5]
                }
            ]
        )
        db.add(cappuccino)
        
        latte = MenuItem(
            business_id=business.id,
            category_id=beverages.id,
            name="Latte",
            description="Smooth espresso with steamed milk",
            base_price=5.00,
            preparation_time=5,
            dietary_tags=["vegetarian"],
            allergens=["milk"],
            calories=150
        )
        db.add(latte)
        
        # Create menu items - Food
        sandwich = MenuItem(
            business_id=business.id,
            category_id=food.id,
            name="Club Sandwich",
            description="Triple-decker with turkey, bacon, lettuce, and tomato",
            base_price=12.00,
            preparation_time=10,
            allergens=["gluten", "eggs"],
            calories=450
        )
        db.add(sandwich)
        
        salad = MenuItem(
            business_id=business.id,
            category_id=food.id,
            name="Caesar Salad",
            description="Crisp romaine with parmesan and croutons",
            base_price=10.00,
            preparation_time=5,
            dietary_tags=["vegetarian"],
            allergens=["milk", "gluten", "eggs"],
            calories=300
        )
        db.add(salad)
        
        # Create tables
        for i in range(1, 11):
            table = Table(
                business_id=business.id,
                table_number=str(i),
                capacity=4 if i < 8 else 6,
                section="Main Floor" if i < 6 else "Patio",
                status="available"
            )
            db.add(table)
        
        db.commit()
        logger.info("Sample data created successfully!")
        
        # Print login credentials
        logger.info("\n=== Test Credentials ===")
        logger.info("Admin: admin@democafe.com / demo123456")
        logger.info("Staff: staff@democafe.com / staff123456")
        logger.info("========================\n")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()