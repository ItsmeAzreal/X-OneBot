"""Basic chat service - will be enhanced in Week 3."""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from app.models import Message, Business, MenuItem


class ChatService:
    """
    Basic chat service for Week 2.
    
    This will be enhanced in Week 3 with:
    - AI model integration
    - Intent detection
    - Context management
    - RAG search
    """
    
    def __init__(self, db: Session, business_id: Optional[int] = None):
        self.db = db
        self.business_id = business_id
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        table_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message.
        
        For Week 2, this provides basic responses.
        Week 3 will add AI processing.
        """
        # Save incoming message
        user_message = Message(
            session_id=session_id,
            business_id=self.business_id,
            sender_type="customer",
            content=message,
            message_type="text",
            created_at=datetime.utcnow()
        )
        self.db.add(user_message)
        
        # Generate response (basic for now)
        response_text, suggested_actions = self._generate_response(message)
        
        # Save bot response
        bot_message = Message(
            session_id=session_id,
            business_id=self.business_id,
            sender_type="bot",
            content=response_text,
            message_type="text",
            intent_detected="unknown",  # Will be enhanced in Week 3
            created_at=datetime.utcnow()
        )
        self.db.add(bot_message)
        
        self.db.commit()
        
        return {
            "message": response_text,
            "suggested_actions": suggested_actions,
            "metadata": {
                "session_id": session_id,
                "table_id": table_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_response(self, message: str) -> tuple[str, list]:
        """
        Generate basic response.
        
        Week 3 will replace this with AI model routing.
        """
        message_lower = message.lower()
        
        # Basic keyword matching for demo
        if any(word in message_lower for word in ["menu", "food", "drink", "eat"]):
            return (
                "I'd be happy to show you our menu! We have beverages, food, and desserts. What would you like to see?",
                ["Show beverages", "Show food", "Show desserts"]
            )
        
        elif any(word in message_lower for word in ["order", "want", "get", "have"]):
            return (
                "I can help you place an order! What would you like to have today?",
                ["View menu", "Popular items", "Today's specials"]
            )
        
        elif any(word in message_lower for word in ["book", "table", "reservation"]):
            return (
                "I can help you book a table. When would you like to visit us?",
                ["Today", "Tomorrow", "This weekend"]
            )
        
        elif any(word in message_lower for word in ["pay", "bill", "check"]):
            return (
                "I'll help you with the payment. Would you like to pay online or at the counter?",
                ["Pay online", "Pay at counter", "View bill"]
            )
        
        elif any(word in message_lower for word in ["hi", "hello", "hey"]):
            return (
                "Hello! Welcome to our cafe. I'm here to help you with ordering, table booking, or any questions you have.",
                ["View menu", "Book a table", "Today's specials"]
            )
        
        else:
            return (
                "I'm here to help! You can ask me about our menu, place an order, book a table, or ask any questions.",
                ["View menu", "Place order", "Book table", "Contact staff"]
            )