"""
Week 3 Setup Script - Initialize AI services and vector database.
Run this after updating the code to set up Week 3 features.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models import Business, MenuItem
from app.services.ai.rag_search import RAGSearchService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_week3():
    """Initialize Week 3 AI features."""
    db: Session = SessionLocal()
    
    try:
        logger.info("Setting up Week 3 AI features...")
        
        # Initialize RAG search service
        rag_service = RAGSearchService(db)
        
        # Index all existing businesses
        businesses = db.query(Business).all()
        
        for business in businesses:
            logger.info(f"Indexing menu for {business.name}...")
            rag_service.index_menu_items(business.id)
            
            # Add sample FAQs
            sample_faqs = [
                {
                    "question": "What are your hours?",
                    "answer": f"We're open {business.settings.get('working_hours', 'daily from 9 AM to 9 PM')}."
                },
                {
                    "question": "Do you have vegan options?",
                    "answer": "Yes! We have several vegan options marked on our menu. Just ask and I'll show them to you."
                },
                {
                    "question": "Can I make a reservation?",
                    "answer": "Absolutely! I can help you book a table. Just tell me when you'd like to visit and how many people."
                },
                {
                    "question": "Do you offer delivery?",
                    "answer": "We offer both pickup and delivery options. Delivery is available through our partners."
                },
                {
                    "question": "What payment methods do you accept?",
                    "answer": "We accept cash, all major credit cards, and digital payments through our app."
                }
            ]
            
            rag_service.index_faqs(business.id, sample_faqs)
        
        logger.info("✅ Week 3 setup complete!")
        logger.info("AI features are now active:")
        logger.info("  - Universal bot routing")
        logger.info("  - Multi-model AI (Groq, Claude, GPT)")
        logger.info("  - RAG search for menus")
        logger.info("  - Voice call support")
        logger.info("  - WhatsApp integration")
        logger.info("  - Personality customization")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    setup_week3()