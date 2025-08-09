"""
Personality Engine - Applies business-specific personality to responses.
Each cafe can have its own unique voice and style.
"""
from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class PersonalityEngine:
    """
    Applies personality traits to bot responses.
    
    Personalities:
    1. Friendly - Warm, emoji-heavy, casual
    2. Professional - Formal, efficient, minimal emoji
    3. Trendy - Hip, modern slang, instagram-worthy
    4. Cozy - Homey, comfortable, grandma's kitchen vibe
    """
    
    def __init__(self):
        self.personality_traits = {
            "friendly": {
                "formality": 0.3,
                "emoji_frequency": 0.8,
                "exclamation_frequency": 0.6,
                "humor_level": 0.5,
                "verbosity": 0.7
            },
            "professional": {
                "formality": 0.9,
                "emoji_frequency": 0.1,
                "exclamation_frequency": 0.2,
                "humor_level": 0.1,
                "verbosity": 0.5
            },
            "trendy": {
                "formality": 0.2,
                "emoji_frequency": 0.9,
                "exclamation_frequency": 0.8,
                "humor_level": 0.7,
                "verbosity": 0.6
            },
            "cozy": {
                "formality": 0.4,
                "emoji_frequency": 0.5,
                "exclamation_frequency": 0.4,
                "humor_level": 0.6,
                "verbosity": 0.8
            }
        }
        
        self.emoji_sets = {
            "friendly": ["😊", "🎉", "👍", "✨", "🌟", "💫", "🤗"],
            "professional": [".", ""],  # Minimal emoji
            "trendy": ["🔥", "💯", "✨", "🚀", "💪", "🎯", "⚡"],
            "cozy": ["☕", "🍰", "🏠", "💛", "🌻", "🧁", "🍪"]
        }
    
    def apply_personality(
        self,
        text: str,
        personality: str = "friendly",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Apply personality traits to text.
        
        Args:
            text: Original text
            personality: Personality type
            context: Additional context
            
        Returns:
            Personalized text
        """
        
        traits = self.personality_traits.get(personality, self.personality_traits["friendly"])
        
        # Apply transformations based on traits
        text = self._adjust_formality(text, traits["formality"])
        text = self._add_emoji(text, personality, traits["emoji_frequency"])
        text = self._adjust_punctuation(text, traits["exclamation_frequency"])
        
        # Add personality-specific phrases
        text = self._add_personality_phrases(text, personality)
        
        return text
    
    def _adjust_formality(self, text: str, formality: float) -> str:
        """Adjust formality level of text."""
        
        if formality < 0.5:
            # Make more casual
            replacements = {
                "Hello": "Hey",
                "Goodbye": "Bye",
                "Thank you": "Thanks",
                "You are welcome": "No problem",
                "Please": "Just"
            }
        else:
            # Make more formal
            replacements = {
                "Hey": "Hello",
                "Bye": "Goodbye",
                "Thanks": "Thank you",
                "No problem": "You are welcome",
                "Just": "Please"
            }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _add_emoji(
        self,
        text: str,
        personality: str,
        frequency: float
    ) -> str:
        """Add emoji based on frequency."""
        
        import random
        
        if random.random() > frequency:
            return text
        
        emoji_set = self.emoji_sets.get(personality, self.emoji_sets["friendly"])
        
        if not emoji_set or emoji_set == [""]:
            return text
        
        # Add emoji at end of sentences
        sentences = text.split(". ")
        for i in range(len(sentences)):
            if random.random() < frequency and i == len(sentences) - 1:
                emoji = random.choice(emoji_set)
                sentences[i] = sentences[i].rstrip(".!?") + f" {emoji}"
        
        return ". ".join(sentences)
    
    def _adjust_punctuation(self, text: str, exclamation_frequency: float) -> str:
        """Adjust punctuation based on personality."""
        
        import random
        
        if random.random() < exclamation_frequency:
            # Replace some periods with exclamations
            sentences = text.split(". ")
            for i in range(len(sentences)):
                if random.random() < exclamation_frequency:
                    sentences[i] = sentences[i].rstrip(".") + "!"
            
            text = " ".join(sentences)
        
        return text
    
    def _add_personality_phrases(self, text: str, personality: str) -> str:
        """Add personality-specific phrases."""
        
        phrases = {
            "friendly": {
                "prefix": ["Oh, ", "Actually, ", "You know what? "],
                "suffix": [" Hope that helps!", " Let me know if you need anything else!"]
            },
            "professional": {
                "prefix": ["", ""],
                "suffix": ["", ""]
            },
            "trendy": {
                "prefix": ["Okay so, ", "Real talk - ", "NGL, "],
                "suffix": [" You feel me?", " Fire, right?"]
            },
            "cozy": {
                "prefix": ["Well dear, ", "You know, ", ""],
                "suffix": [" Take your time!", " No rush at all!"]
            }
        }
        
        import random
        
        personality_phrases = phrases.get(personality, phrases["friendly"])
        
        # Occasionally add prefix
        if random.random() < 0.3:
            prefix = random.choice(personality_phrases["prefix"])
            text = prefix + text
        
        # Occasionally add suffix
        if random.random() < 0.3:
            suffix = random.choice(personality_phrases["suffix"])
            text = text.rstrip(".!?") + suffix
        
        return text