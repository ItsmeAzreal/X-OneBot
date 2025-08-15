"""
Updated Universal Bot Service with dual-number support.
Routes users to appropriate cafes based on number called.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Business, MenuItem, Table, PhoneNumber, PhoneNumberType
from app.services.ai.intent_detection import IntentDetector, Intent
from app.services.ai.model_router import ModelRouter
from app.services.ai.rag_search import RAGSearchService
from app.services.ai.chat_memory import ChatMemory
from app.services.phone.providers.multi_provider_manager import MultiProviderPhoneManager
import logging

logger = logging.getLogger(__name__)


class UniversalBot:
    """
    Updated universal bot with dual-number awareness.
    
    Flow:
    1. Identify if call is to universal or custom number
    2. Route appropriately based on configuration
    3. Handle transfer to human when needed
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.intent_detector = IntentDetector()
        self.model_router = ModelRouter()
        self.rag_service = RAGSearchService(db)
        self.phone_manager = MultiProviderPhoneManager(db)
    
    async def process_message(
        self,
        session_id: str,
        message: str,
        channel: str = "chat",
        phone_number: Optional[str] = None,  # Number that was called
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process message with phone number awareness.
        """
        
        # Initialize or load memory
        memory = ChatMemory(session_id)
        context = memory.get_context()
        
        # Check if this is a custom number call
        if phone_number and phone_number != settings.UNIVERSAL_BOT_NUMBER:
            # Direct custom number - route directly to business
            business_id = self.phone_manager.route_incoming_call(phone_number, "")
            if business_id:
                context["selected_business"] = business_id
                memory.update_context({"selected_business": business_id})
                logger.info(f"Routed to business {business_id} via custom number {phone_number}")
        
        # Add user message to memory
        memory.add_message("user", message)
        
        # Detect intent and language
        intent, language, entities = self.intent_detector.detect_intent(
            message, context
        )
        
        # Check for human transfer request
        if intent == Intent.HUMAN_REQUEST and context.get("selected_business"):
            return await self._handle_human_transfer(
                context["selected_business"],
                session_id,
                channel
            )
        
        # Update context with language
        if language != context.get("language"):
            memory.update_context({"language": language})
        
        # Route based on state and intent
        if not context.get("selected_business"):
            # No cafe selected yet - only for universal number
            if phone_number == settings.UNIVERSAL_BOT_NUMBER:
                response = await self._handle_cafe_selection(
                    message, intent, location, memory
                )
            else:
                # Shouldn't happen - custom number without business
                response = {
                    "message": "I'm having trouble identifying your cafe. Please try again.",
                    "error": True
                }
        else:
            # Cafe selected, handle normal interaction
            business = self.db.query(Business).filter(
                Business.id == context["selected_business"]
            ).first()
            
            # Check usage limits
            usage_status = self.phone_manager.check_usage_limits(business.id)
            
            if channel == "voice" and usage_status["voice"]["exceeded"]:
                response = {
                    "message": "I apologize, but we've reached our voice service limit for this month. Please try our chat or WhatsApp service instead.",
                    "limit_exceeded": True
                }
            else:
                response = await self._handle_business_interaction(
                    message, intent, context, memory
                )
        
        # Add bot response to memory
        memory.add_message("assistant", response["message"])
        
        return response
    
    async def _handle_human_transfer(
        self,
        business_id: int,
        session_id: str,
        channel: str
    ) -> Dict[str, Any]:
        """Handle request to transfer to human."""
        
        business = self.db.query(Business).filter(
            Business.id == business_id
        ).first()
        
        # Check if business has human transfer capability
        if business.phone_config == PhoneNumberType.UNIVERSAL_ONLY:
            return {
                "message": "I apologize, but direct staff transfer is not available on the universal number. You can reach our staff at the number listed on our website.",
                "transfer_available": False
            }
        
        if channel == "voice":
            # Attempt to transfer the call
            success = self.phone_manager.transfer_to_human(business_id, session_id)
            
            if success:
                return {
                    "message": "Transferring you to our staff now. Please hold.",
                    "action": "transfer",
                    "transfer_initiated": True
                }
            else:
                return {
                    "message": "I'm sorry, our staff is not available right now. Please leave a message or try again later.",
                    "transfer_failed": True
                }
        else:
            # For chat/WhatsApp, provide staff contact
            staff_contact = business.contact_info.get("staff_phone", "Not available")
            return {
                "message": f"To speak with our staff directly, please call {staff_contact}. They'll be happy to help you!",
                "staff_contact": staff_contact
            }
    
    async def _handle_cafe_selection(
        self,
        message: str,
        intent: Intent,
        location: Optional[Dict[str, float]],
        memory: ChatMemory
    ) -> Dict[str, Any]:
        """
        Handle cafe selection for universal number.
        Only businesses with universal access are shown.
        """
        
        if intent == Intent.CAFE_SELECTION or "cafe" in message.lower() or "coffee" in message.lower():
            # Find cafes with universal access
            cafes_query = self.db.query(Business).join(PhoneNumber).filter(
                PhoneNumber.is_universal == True,
                Business.is_active == True
            ).distinct()
            
            cafes = cafes_query.limit(5).all()
            
            if not cafes:
                return {
                    "message": "No cafes are currently available on our universal service. Please try again later.",
                    "state": "no_cafes"
                }
            
            # Format cafe list
            cafe_list = []
            for i, cafe in enumerate(cafes, 1):
                # Check if cafe also has custom number
                if cafe.phone_config == PhoneNumberType.BOTH:
                    note = " (Also has dedicated line)"
                else:
                    note = ""
                cafe_list.append(f"{i}. {cafe.name}{note}")
            
            response_text = (
                "Welcome to XoneBot! I can connect you to these cafes:\n\n" +
                "\n".join(cafe_list) +
                "\n\nWhich one would you like?"
            )
            
            # Store cafes in context
            memory.update_context({
                "nearby_cafes": [{"id": c.id, "name": c.name} for c in cafes]
            })
            
            return {
                "message": response_text,
                "suggested_actions": [cafe.name for cafe in cafes[:3]],
                "state": "selecting_cafe"
            }
        else:
            return {
                "message": "Hi! I'm XoneBot, connecting you to the best cafes. Which cafe would you like to order from?",
                "suggested_actions": ["Show available cafes", "Search by name"],
                "state": "initial"
            }
    
    def _find_businesses_with_universal_access(self) -> List[Business]:
        """Find all businesses that have universal number access."""
        
        return self.db.query(Business).filter(
            Business.is_active == True,
            Business.phone_config.in_([
                PhoneNumberType.UNIVERSAL_ONLY,
                PhoneNumberType.BOTH
            ])
        ).all()