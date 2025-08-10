"""Universal WhatsApp system for multiple cafés."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from app.models import Business, User, Order
from app.services.ai.language_service import LanguageService
from app.services.ai.chat_service import ChatService
from app.schemas.whatsapp import WhatsAppMessage, WhatsAppInteractiveMessage

logger = logging.getLogger(__name__)


class UniversalWhatsAppService:
    """
    Universal WhatsApp bot serving multiple cafés.
    One number to rule them all!
    """

    UNIVERSAL_NUMBER = "+1-800-XONEBOT"  # Your universal WhatsApp number

    def __init__(self, db: Session):
        self.db = db
        self.language_service = LanguageService()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}  # phone -> session data

    async def handle_universal_message(
        self,
        message: WhatsAppMessage
    ) -> Dict[str, Any]:
        """
        Handle incoming message to universal number.
        Routes to appropriate café based on context.
        """
        user_phone = message.from_number

        # Get or create session
        session = self.active_sessions.get(user_phone, {})

        # Detect language
        lang_result = self.language_service.detect_language(message.message_text)
        language = lang_result.detected_language.value

        # Update session language
        session['language'] = language

        # Check if user has selected a café
        if 'business_id' not in session:
            return await self._handle_cafe_selection(
                user_phone,
                message.message_text,
                language
            )

        # Route to selected café's context
        business_id = session['business_id']
        return await self._handle_cafe_conversation(
            business_id,
            user_phone,
            message,
            language
        )

    async def _handle_cafe_selection(
        self,
        user_phone: str,
        message_text: str,
        language: str
    ) -> Dict[str, Any]:
        """Handle café selection flow."""

        # Check if message contains café name
        businesses = self.db.query(Business).filter(
            Business.is_active == True
        ).all()

        # Try to match café name in message
        selected_business = None
        for business in businesses:
            if business.name.lower() in message_text.lower():
                selected_business = business
                break

        if selected_business:
            # Save selection in session
            self.active_sessions[user_phone] = {
                'business_id': selected_business.id,
                'language': language,
                'started_at': datetime.utcnow()
            }

            # Send welcome message for selected café
            welcome = self.language_service.get_template(
                language,
                'welcome'
            )

            return {
                'type': 'text',
                'message': f"{welcome} - {selected_business.name}",
                'business_id': selected_business.id
            }

        # Show café list
        cafe_list_msg = self._format_cafe_list(businesses, language)

        return {
            'type': 'interactive',
            'message': cafe_list_msg
        }

    def _format_cafe_list(
        self,
        businesses: List[Business],
        language: str
    ) -> WhatsAppInteractiveMessage:
        """Format café list as WhatsApp interactive message."""

        header = self.language_service.get_template(
            language,
            'select_cafe'
        )

        list_items = []
        for business in businesses[:10]:  # WhatsApp limit
            list_items.append({
                'id': str(business.id),
                'title': business.name,
                'description': business.description or "Great café!"
            })

        return WhatsAppInteractiveMessage(
            type='list',
            header=header,
            body="Choose your preferred café:",
            list_items=list_items
        )

    async def _handle_cafe_conversation(
        self,
        business_id: int,
        user_phone: str,
        message: WhatsAppMessage,
        language: str
    ) -> Dict[str, Any]:
        """Handle conversation with selected café."""

        # Get business
        business = self.db.query(Business).filter(
            Business.id == business_id
        ).first()

        if not business:
            # Reset session if business not found
            del self.active_sessions[user_phone]
            return {
                'type': 'text',
                'message': 'Café not found. Please select again.'
            }

        # Initialize chat service for this business
        chat_service = ChatService(self.db, business_id)

        # Process message with business context
        response = await chat_service.process_message(
            session_id=f"whatsapp_{user_phone}_{business_id}",
            message=message.message_text,
            context={
                'language': language,
                'channel': 'whatsapp',
                'phone': user_phone
            }
        )

        return {
            'type': 'text',
            'message': response['message'],
            'business_id': business_id
        }

    def reset_session(self, user_phone: str):
        """Reset user session to select new café."""
        if user_phone in self.active_sessions:
            del self.active_sessions[user_phone]