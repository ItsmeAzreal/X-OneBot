"""
Intent Detection Service - Understands what customers want.
Uses pattern matching and NLP to classify user intentions.
"""
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import re
from langdetect import detect, LangDetectException
import logging

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Customer intent categories."""
    # Discovery
    CAFE_SELECTION = "cafe_selection"  # Choosing which cafe
    MENU_INQUIRY = "menu_inquiry"  # Asking about menu
    
    # Ordering
    ORDER_PLACEMENT = "order_placement"  # Placing an order
    ORDER_MODIFICATION = "order_modification"  # Changing order
    ORDER_STATUS = "order_status"  # Checking order status
    
    # Booking
    TABLE_BOOKING = "table_booking"  # Reserve a table
    BOOKING_MODIFICATION = "booking_modification"  # Change reservation
    
    # Payment
    PAYMENT_INTENT = "payment_intent"  # Want to pay
    BILL_REQUEST = "bill_request"  # Request bill
    
    # Information
    HOURS_INQUIRY = "hours_inquiry"  # Business hours
    LOCATION_INQUIRY = "location_inquiry"  # Where is cafe
    DIETARY_INQUIRY = "dietary_inquiry"  # Dietary restrictions
    
    # Support
    HELP_REQUEST = "help_request"  # Need help
    HUMAN_REQUEST = "human_request"  # Want human support
    COMPLAINT = "complaint"  # Expressing dissatisfaction
    
    # General
    GREETING = "greeting"  # Hello, hi
    THANKS = "thanks"  # Thank you
    GOODBYE = "goodbye"  # Bye
    UNKNOWN = "unknown"  # Can't determine


class IntentDetector:
    """
    Detects customer intent from messages.
    
    Uses:
    1. Keyword matching
    2. Pattern recognition
    3. Language detection
    4. Context awareness
    """
    
    def __init__(self):
        # Intent patterns (keyword lists)
        self.intent_patterns = {
            Intent.CAFE_SELECTION: [
                "which cafe", "show cafe", "list cafe", "nearby cafe",
                "coffee shop", "restaurant near"
            ],
            Intent.MENU_INQUIRY: [
                "menu", "what do you have", "show me food", "drinks",
                "what can i order", "options", "items", "dishes"
            ],
            Intent.ORDER_PLACEMENT: [
                "i want", "i'll have", "order", "get me", "i'd like",
                "can i have", "give me", "i'll take"
            ],
            Intent.TABLE_BOOKING: [
                "book", "reserve", "table for", "reservation",
                "booking", "make a reservation"
            ],
            Intent.PAYMENT_INTENT: [
                "pay", "bill", "check please", "payment", "checkout",
                "how much", "total"
            ],
            Intent.DIETARY_INQUIRY: [
                "vegan", "vegetarian", "gluten free", "dairy free",
                "allergic", "allergy", "dietary", "lactose"
            ],
            Intent.GREETING: [
                "hi", "hello", "hey", "good morning", "good afternoon",
                "good evening", "greetings"
            ],
            Intent.HELP_REQUEST: [
                "help", "how do i", "what is", "explain", "guide",
                "how to", "assistance"
            ],
            Intent.COMPLAINT: [
                "wrong", "mistake", "incorrect", "bad", "terrible",
                "awful", "disgusting", "cold", "not what i ordered"
            ]
        }
        
        # Multi-language greetings
        self.multilingual_greetings = {
            "es": ["hola", "buenos días", "buenas tardes"],
            "fr": ["bonjour", "bonsoir", "salut"],
            "de": ["hallo", "guten tag", "guten morgen"],
            "it": ["ciao", "buongiorno", "buonasera"],
            "pt": ["olá", "bom dia", "boa tarde"],
            "zh": ["你好", "您好", "早上好"],
            "ja": ["こんにちは", "おはよう", "こんばんは"]
        }
    
    def detect_intent(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Intent, str, Dict[str, Any]]:
        """
        Detect intent from message.
        
        Args:
            message: User's message
            context: Conversation context
            
        Returns:
            Tuple of (intent, language, entities)
        """
        # Detect language
        language = self._detect_language(message)
        
        # Extract entities
        entities = self._extract_entities(message)
        
        # Clean message for matching
        message_lower = message.lower().strip()
        
        # Check each intent pattern
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = self._calculate_intent_score(message_lower, patterns)
            if score > 0:
                intent_scores[intent] = score
        
        # Check multilingual greetings
        if language != "en":
            if self._is_multilingual_greeting(message_lower, language):
                intent_scores[Intent.GREETING] = 1.0
        
        # Context-aware adjustments
        if context:
            intent_scores = self._adjust_for_context(intent_scores, context)
        
        # Select highest scoring intent
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent = best_intent[0]
        else:
            intent = Intent.UNKNOWN
        
        logger.info(f"Detected intent: {intent} (language: {language})")
        
        return intent, language, entities
    
    def _detect_language(self, message: str) -> str:
        """Detect message language."""
        try:
            lang = detect(message)
            # Map to our supported languages
            supported = ["en", "es", "fr", "de", "it", "pt", "zh", "ja"]
            if lang in supported:
                return lang
            # Default to English for unsupported
            return "en"
        except LangDetectException:
            return "en"
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from message."""
        entities = {}
        
        # Extract numbers
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # Extract time
        time_pattern = r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?'
        times = re.findall(time_pattern, message)
        if times:
            entities["times"] = times
        
        # Extract dates
        date_keywords = ["today", "tomorrow", "monday", "tuesday", "wednesday",
                        "thursday", "friday", "saturday", "sunday"]
        for keyword in date_keywords:
            if keyword in message.lower():
                entities["date"] = keyword
                break
        
        # Extract quantity words
        quantity_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }
        for word, value in quantity_words.items():
            if word in message.lower():
                if "numbers" not in entities:
                    entities["numbers"] = []
                entities["numbers"].append(value)
        
        return entities
    
    def _calculate_intent_score(
        self,
        message: str,
        patterns: List[str]
    ) -> float:
        """Calculate how well message matches intent patterns."""
        score = 0.0
        message_words = set(message.split())
        
        for pattern in patterns:
            pattern_words = set(pattern.split())
            # Check exact phrase match
            if pattern in message:
                score += 1.0
            # Check word overlap
            elif pattern_words & message_words:
                overlap = len(pattern_words & message_words)
                score += overlap * 0.5
        
        return score
    
    def _is_multilingual_greeting(self, message: str, language: str) -> bool:
        """Check if message is a greeting in detected language."""
        if language in self.multilingual_greetings:
            greetings = self.multilingual_greetings[language]
            return any(greeting in message for greeting in greetings)
        return False
    
    def _adjust_for_context(
        self,
        intent_scores: Dict[Intent, float],
        context: Dict[str, Any]
    ) -> Dict[Intent, float]:
        """Adjust intent scores based on context."""
        # If user has items in cart, boost order-related intents
        if context.get("cart") and len(context["cart"]) > 0:
            if Intent.PAYMENT_INTENT in intent_scores:
                intent_scores[Intent.PAYMENT_INTENT] *= 1.5
            if Intent.ORDER_MODIFICATION in intent_scores:
                intent_scores[Intent.ORDER_MODIFICATION] *= 1.3
        
        # If user just selected a cafe, boost menu inquiry
        if context.get("cafe_just_selected"):
            if Intent.MENU_INQUIRY in intent_scores:
                intent_scores[Intent.MENU_INQUIRY] *= 1.5
        
        return intent_scores