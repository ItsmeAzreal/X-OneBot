"""
Response Generator - Creates natural, context-aware responses.
Applies personality and formatting based on business settings.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates natural language responses with personality.
    
    Features:
    1. Personality application
    2. Multi-language support
    3. Context-aware responses
    4. Dynamic formatting
    """
    
    def __init__(self):
        # Response templates by personality
        self.personalities = {
            "friendly": {
                "greeting": [
                    "Hey there! 😊 Welcome to {business_name}!",
                    "Hi! Great to see you at {business_name}! 🎉",
                    "Hello! Ready to make your day delicious? ☕"
                ],
                "order_confirm": [
                    "Awesome choice! I've added {item} to your order 🛒",
                    "Perfect! {item} is now in your cart ✨",
                    "Great taste! {item} added successfully 👍"
                ],
                "thanks": [
                    "You're welcome! Enjoy your visit! 😊",
                    "My pleasure! Have an amazing day! 🌟",
                    "Happy to help! See you soon! 👋"
                ]
            },
            "professional": {
                "greeting": [
                    "Good {time_of_day}. Welcome to {business_name}.",
                    "Welcome to {business_name}. How may I assist you today?",
                    "Thank you for choosing {business_name}."
                ],
                "order_confirm": [
                    "I have added {item} to your order.",
                    "{item} has been successfully added to your cart.",
                    "Your order has been updated with {item}."
                ],
                "thanks": [
                    "You are welcome. Thank you for your order.",
                    "It was my pleasure to assist you.",
                    "Thank you for choosing us."
                ]
            },
            "casual": {
                "greeting": [
                    "Yo! Welcome to {business_name}! What's good?",
                    "Hey! Ready to grab something awesome?",
                    "What's up! Welcome to the spot! 🔥"
                ],
                "order_confirm": [
                    "Nice! Got {item} locked in for you!",
                    "Boom! {item} is in the bag!",
                    "Sweet! {item} coming right up!"
                ],
                "thanks": [
                    "No prob! Catch you later!",
                    "You got it! Peace out!",
                    "All good! Take it easy!"
                ]
            }
        }
        
        # Multi-language templates
        self.multilingual = {
            "es": {
                "greeting": "¡Hola! Bienvenido a {business_name}!",
                "menu_prompt": "¿Qué le gustaría ordenar hoy?",
                "order_confirm": "Perfecto! He agregado {item} a su orden.",
                "thanks": "¡De nada! ¡Que tenga un buen día!"
            },
            "fr": {
                "greeting": "Bonjour! Bienvenue chez {business_name}!",
                "menu_prompt": "Que souhaitez-vous commander aujourd'hui?",
                "order_confirm": "Parfait! J'ai ajouté {item} à votre commande.",
                "thanks": "Je vous en prie! Bonne journée!"
            }
        }
    
    def generate_response(
        self,
        intent: str,
        context: Dict[str, Any],
        personality: str = "friendly",
        language: str = "en"
    ) -> str:
        """
        Generate response based on intent and context.
        
        Args:
            intent: Detected intent
            context: Conversation context
            personality: Business personality type
            language: Response language
            
        Returns:
            Generated response text
        """
        
        # Handle non-English languages
        if language != "en" and language in self.multilingual:
            return self._generate_multilingual(intent, context, language)
        
        # Get personality templates
        templates = self.personalities.get(personality, self.personalities["friendly"])
        
        # Select template based on intent
        if intent == "greeting":
            template = random.choice(templates["greeting"])
        elif intent == "order_confirmation":
            template = random.choice(templates["order_confirm"])
        elif intent == "thanks":
            template = random.choice(templates["thanks"])
        else:
            # Default response
            template = "I can help you with that."
        
        # Format template with context
        response = self._format_template(template, context)
        
        return response
    
    def _format_template(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """Format template with context values."""
        
        # Add time of day
        hour = datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"
        
        # Format values
        format_values = {
            "business_name": context.get("business_name", "our cafe"),
            "time_of_day": time_of_day,
            "item": context.get("item_name", "that item"),
            "customer_name": context.get("customer_name", "there"),
            "total": context.get("total", 0)
        }
        
        try:
            return template.format(**format_values)
        except KeyError:
            return template
    
    def _generate_multilingual(
        self,
        intent: str,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Generate response in non-English language."""
        
        templates = self.multilingual.get(language, {})
        
        # Map intent to template
        intent_map = {
            "greeting": "greeting",
            "menu_inquiry": "menu_prompt",
            "order_confirmation": "order_confirm",
            "thanks": "thanks"
        }
        
        template_key = intent_map.get(intent, "greeting")
        template = templates.get(template_key, "...")
        
        return self._format_template(template, context)
    
    def format_menu_items(
        self,
        items: List[Dict[str, Any]],
        personality: str = "friendly"
    ) -> str:
        """Format menu items for display."""
        
        if not items:
            return "No items available at the moment."
        
        # Different formatting by personality
        if personality == "friendly":
            lines = ["Here's what we've got for you! 🍽️\n"]
            for item in items:
                line = f"🔸 **{item['name']}** - ${item['price']}"
                if item.get('description'):
                    line += f"\n   _{item['description']}_"
                lines.append(line)
        
        elif personality == "professional":
            lines = ["Available items:\n"]
            for item in items:
                line = f"• {item['name']} - ${item['price']}"
                if item.get('description'):
                    line += f"\n  {item['description']}"
                lines.append(line)
        
        else:  # casual
            lines = ["Check these out:\n"]
            for item in items:
                line = f"→ {item['name']} (${item['price']})"
                lines.append(line)
        
        return "\n".join(lines)
    
    def format_order_summary(
        self,
        cart: List[Dict[str, Any]],
        personality: str = "friendly"
    ) -> str:
        """Format order summary."""
        
        if not cart:
            return "Your cart is empty."
        
        total = sum(item['price'] * item['quantity'] for item in cart)
        
        if personality == "friendly":
            lines = ["📝 Your order so far:\n"]
            for item in cart:
                lines.append(f"  {item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
            lines.append(f"\n💰 Total: ${total:.2f}")
        
        else:
            lines = ["Order Summary:\n"]
            for item in cart:
                lines.append(f"{item['quantity']}x {item['name']} - ${item['price'] * item['quantity']:.2f}")
            lines.append(f"\nTotal: ${total:.2f}")
        
        return "\n".join(lines)