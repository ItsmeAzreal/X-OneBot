"""Initialize database with tables and sample data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config.database import engine, Base
from app.models import *  # Import all models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


if __name__ == "__main__":
    init_db()