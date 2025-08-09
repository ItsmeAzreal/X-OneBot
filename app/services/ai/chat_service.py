"""
Enhanced Chat Service with full AI integration.
This replaces the basic chat service from Week 2.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from app.models import Message, Business, MenuItem
from app.services.ai.universal_bot import UniversalBot
from app.services.ai.response_generator import ResponseGenerator
from app.services.ai.personality_engine import PersonalityEngine
import logging

logger = logging.getLogger(__name__)


class EnhancedChatService:
    """
    Full-featured chat service with AI integration.
    
    Features:
    1. Universal bot routing
    2. Multi-model AI support
    3. RAG search integration
    4. Voice and WhatsApp support
    5. Personality customization
    """
    
    def __init__(self, db: Session, business_id: Optional[int] = None):
        self.db = db
        self.business_id = business_id
        self.universal_bot = UniversalBot(db)
        self.response_generator = ResponseGenerator()
        self.personality_engine = PersonalityEngine()
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        table_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        channel: str = "chat"
    ) -> Dict[str, Any]:
        """
        Process a chat message with full AI capabilities.
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
        
        # Process through universal bot
        response = await self.universal_bot.process_message(
            session_id=session_id,
            message=message,
            channel=channel,
            location=context.get("location") if context else None
        )
        
        # Apply personality if business is selected
        if self.business_id:
            business = self.db.query(Business).filter(
                Business.id == self.business_id
            ).first()
            
            if business:
                personality = business.branding_config.get("bot_personality", "friendly")
                response["message"] = self.personality_engine.apply_personality(
                    response["message"],
                    personality
                )
        
        # Save bot response
        bot_message = Message(
            session_id=session_id,
            business_id=self.business_id,
            sender_type="bot",
            content=response["message"],
            message_type="text",
            intent_detected=response.get("intent", "unknown"),
            ai_model_used=response.get("model_used", "unknown"),
            response_time_ms=response.get("response_time_ms"),
            created_at=datetime.utcnow()
        )
        self.db.add(bot_message)
        
        self.db.commit()
        
        return {
            "message": response["message"],
            "suggested_actions": response.get("suggested_actions", []),
            "metadata": {
                "session_id": session_id,
                "table_id": table_id,
                "timestamp": datetime.utcnow().isoformat(),
                "model_used": response.get("model_used"),
                "intent": response.get("intent")
            }
        }