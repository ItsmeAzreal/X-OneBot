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
from app.services.ai.personality_engine import PersonalityEngine
# Import ChatMemory to access the session context after processing
from app.services.ai.chat_memory import ChatMemory
import logging

logger = logging.getLogger(__name__)


class EnhancedChatService:
    """
    Full-featured chat service with AI integration.
    """
    
    def __init__(self, db: Session, business_id: Optional[int] = None):
        self.db = db
        self.business_id = business_id
        self.universal_bot = UniversalBot(db)
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
        
        # === FIX START: The logic is now correctly restructured ===

        # 1. Process the message through the universal bot FIRST. This will handle
        #    the cafe selection process and determine the business context.
        response = await self.universal_bot.process_message(
            session_id=session_id,
            message=message,
            channel=channel,
            location=context.get("location") if context else None
        )
        
        # 2. After processing, load the session memory to see if a business was selected.
        memory = ChatMemory(session_id)
        session_context = memory.get_context()
        # The final business_id is either from the table context or from the session memory.
        final_business_id = self.business_id or session_context.get("selected_business")

        # 3. Apply personality to the response only if a business context now exists.
        if final_business_id:
            business = self.db.query(Business).filter(Business.id == final_business_id).first()
            if business:
                personality = business.branding_config.get("bot_personality", "friendly")
                response["message"] = self.personality_engine.apply_personality(
                    response["message"],
                    personality
                )
        
        # 4. NOW, save the conversation to the database, but only if a business_id is known.
        # This prevents the database error for the first message from a universal user.
        if final_business_id:
            # Save the original user message
            user_message = Message(
                session_id=session_id,
                business_id=final_business_id,
                sender_type="customer",
                content=message,
                message_type="text"
            )
            self.db.add(user_message)
            
            # Save the final bot response
            bot_message = Message(
                session_id=session_id,
                business_id=final_business_id,
                sender_type="bot",
                content=response["message"],
                message_type="text",
                intent_detected=response.get("intent", "unknown"),
                ai_model_used=response.get("model_used", "unknown"),
                response_time_ms=response.get("response_time_ms")
            )
            self.db.add(bot_message)
            
            self.db.commit()
        
        # === FIX END ===
        
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