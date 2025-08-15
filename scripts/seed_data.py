"""Seed database with sample data for testing."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models import (
    Business, User, MenuCategory, MenuItem, Table, UserRole,
    PhoneNumber, NumberProvider, NumberStatus, PhoneNumberType
)
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_data(db: Session):
    """Add sample data to the provided database session."""
    try:
        if db.query(Business).first():
            logger.info("Database already has data. Skipping seed.")
            return

        logger.info("Seeding database with sample data...")

        # 1. Create the Business
        business = Business(
            name="Demo Cafe",
            slug="demo-cafe",
            description="A cozy cafe for testing XoneBot",
            subscription_plan="pro",
            phone_config=PhoneNumberType.UNIVERSAL_ONLY,
            contact_info={"phone": "+1234567890", "email": "demo@cafe.com"},
            settings={"working_hours": {"mon": "8:00-20:00"}, "languages": ["en"]},
            branding_config={"primary_color": "#FF6B6B", "bot_personality": "friendly"}
        )
        db.add(business)

        # --- START FIX ---
        # Flush the session to persist the business and generate its ID
        db.flush()
        # --- END FIX ---

        # 2. Create an Admin User for the Business (now business.id is available)
        admin = User(
            email="admin@democafe.com",
            hashed_password=get_password_hash("demo123456"),
            name="Demo Admin",
            role=UserRole.OWNER,
            business_id=business.id
        )
        db.add(admin)

        # 3. Create a Universal Phone Number and link it to the Business
        phone_number = PhoneNumber(
            business_id=business.id,
            phone_number="+18005550199",
            is_universal=True,
            status=NumberStatus.ACTIVE,
            provider=NumberProvider.TWILIO # Ensure this enum is set
        )
        db.add(phone_number)

        # Commit the entire transaction
        db.commit()

        logger.info("Sample data created successfully!")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    db_session = SessionLocal()
    try:
        seed_data(db_session)
        logger.info("\n=== Manual Seed Credentials ===")
        logger.info("Admin: admin@democafe.com / demo123456")
        logger.info("========================\n")
    finally:
        db_session.close()