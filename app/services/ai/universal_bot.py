"""
AI-Powered Universal Bot - Let the LLMs handle everything naturally.
No templates, no scripts, just pure AI intelligence.
"""
from typing import Dict, Any, Optional, List
from app.config.settings import settings
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
    AI-Powered Universal Bot.
    
    Let the LLMs handle:
    - Language detection and switching
    - Natural conversation flow
    - Context awareness
    - Personality and tone
    - Everything a human assistant would do
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
        phone_number: Optional[str] = None,
        location: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Process message with pure AI intelligence - no templates.
        """
        
        # Initialize or load memory
        memory = ChatMemory(session_id)
        context = memory.get_context()
        
        # Add user message to memory
        memory.add_message("user", message)
        
        # Check if this is a custom number call (direct business routing)
        if phone_number and phone_number != settings.UNIVERSAL_BOT_NUMBER:
            business_id = self.phone_manager.route_incoming_call(phone_number, "")
            if business_id:
                context["selected_business"] = business_id
                memory.update_context({"selected_business": business_id})
                logger.info(f"Routed to business {business_id} via custom number {phone_number}")
        
        # Route based on conversation state
        if not context.get("selected_business"):
            # No café selected yet - handle café selection with AI
            response = await self._ai_handle_cafe_selection(message, memory, context)
        else:
            # Café selected - handle business conversation with AI
            response = await self._ai_handle_business_conversation(message, memory, context)

        # Add bot response to memory
        memory.add_message("assistant", response.get("message", ""))
        
        return response

    async def _ai_handle_cafe_selection(
        self,
        message: str,
        memory: ChatMemory,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Let AI handle café selection naturally - no scripts.
        """
        
        # Get available cafés
        cafes = self._find_businesses_with_universal_access()
        
        if not cafes:
            # Let AI handle "no cafés available" naturally
            prompt = f"""
            You are XoneBot, a helpful café assistant. A customer said: "{message}"
            
            Unfortunately, no cafés are currently available on our universal service.
            
            Respond naturally in their language (detect it automatically). Be apologetic but helpful.
            Suggest they try again later or provide alternative help.
            """
            
            ai_response = await self.model_router.route_query(
                query=prompt,
                context={"no_cafes": True},
                language="auto"
            )
            
            return {
                "message": ai_response["response"],
                "state": "no_cafes",
                "model_used": ai_response.get("model_used")
            }
        
        # Check if user mentioned a specific café
        selected_cafe = None
        for cafe in cafes:
            if cafe.name.lower() in message.lower():
                selected_cafe = cafe
                break
        
        if selected_cafe:
            # User selected a café - welcome them naturally
            memory.update_context({"selected_business": selected_cafe.id})
            
            prompt = f"""
            You are XoneBot, a helpful café assistant. A customer said: "{message}" and selected {selected_cafe.name}.
            
            Welcome them warmly to {selected_cafe.name} in their language (detect automatically).
            Be enthusiastic and ask how you can help them today.
            Sound like a real, friendly café worker would.
            """
            
            ai_response = await self.model_router.route_query(
                query=prompt,
                context={"selected_cafe": selected_cafe.name},
                language="auto"
            )
            
            return {
                "message": ai_response["response"],
                "state": "cafe_selected",
                "model_used": ai_response.get("model_used")
            }
        
        # No café selected yet - show options naturally
        cafe_names = [cafe.name for cafe in cafes]
        cafe_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(cafe_names)])
        
        prompt = f"""
        You are XoneBot, a helpful café assistant. A customer said: "{message}"
        
        Available cafés:
        {cafe_list}
        
        Respond naturally in their language (detect automatically). Help them choose a café.
        Be conversational and friendly, like a real person would be.
        Don't be robotic - sound enthusiastic about helping them find a great place!
        """
        
        ai_response = await self.model_router.route_query(
            query=prompt,
            context={"available_cafes": cafe_names},
            language="auto"
        )
        
        memory.update_context({"nearby_cafes": [{"id": c.id, "name": c.name} for c in cafes]})
        
        return {
            "message": ai_response["response"],
            "suggested_actions": cafe_names[:3],
            "state": "selecting_cafe",
            "model_used": ai_response.get("model_used")
        }

    async def _ai_handle_business_conversation(
        self,
        message: str,
        memory: ChatMemory,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Let AI handle business conversation naturally - full intelligence.
        """
        
        business_id = context.get("selected_business")
        business = self.db.query(Business).filter(Business.id == business_id).first()
        
        if not business:
            prompt = f"""
            You are XoneBot. A customer said: "{message}" but there's a technical issue.
            
            Apologize naturally in their language (detect automatically) and ask them to try again.
            Be helpful and professional.
            """
            
            ai_response = await self.model_router.route_query(
                query=prompt,
                context={"error": True},
                language="auto"
            )
            
            return {"message": ai_response["response"]}
        
        # Get menu items for context
        menu_items = self.db.query(MenuItem).filter(
            MenuItem.business_id == business_id,
            MenuItem.is_available == True
        ).all()
        
        # Build rich context for AI
        menu_context = []
        for item in menu_items:
            menu_context.append({
                "name": item.name,
                "description": item.description,
                "price": f"€{item.base_price}",
                "dietary_tags": item.dietary_tags,
                "allergens": item.allergens
            })
        
        # Get conversation history for context
        conversation_history = memory.get_conversation_history(limit=5)
        history_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in conversation_history[-3:]  # Last 3 messages
        ])
        
        # Let AI handle everything naturally
        prompt = f"""
        You are a helpful assistant at {business.name}. A customer just said: "{message}"
        
        Business Context:
        - Café name: {business.name}
        - You're helping with orders, questions, bookings, etc.
        
        Available Menu:
        {menu_context[:10]}  # First 10 items
        
        Recent Conversation:
        {history_text}
        
        Instructions:
        - Detect their language automatically and respond in the same language
        - Be natural, friendly, and conversational like a real café worker
        - Help with orders, menu questions, table bookings, hours, anything they need
        - If they want to order, help them through it naturally
        - If they ask about menu, show relevant items with prices
        - If they want to book a table, help them with that
        - Be enthusiastic about your café and make them feel welcome
        - Don't be robotic - sound human and warm
        
        Respond as a real person would, not like a scripted bot.
        """
        
        ai_response = await self.model_router.route_query(
            query=prompt,
            context={
                "business_name": business.name,
                "menu_items": menu_context,
                "conversation_history": conversation_history
            },
            language="auto"
        )
        
        return {
            "message": ai_response["response"],
            "business_context": business.name,
            "model_used": ai_response.get("model_used")
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