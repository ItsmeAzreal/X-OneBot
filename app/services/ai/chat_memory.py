"""
Chat Memory Service - Manages conversation context and history.
Provides memory management for maintaining coherent conversations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import json
import redis
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ChatMemory:
    """
    Manages conversation memory and context.
    
    Features:
    1. Short-term memory (current session)
    2. Long-term memory (user preferences)
    3. Context management (selected cafe, cart, etc.)
    4. Memory summarization for long conversations
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        
        # Redis for persistent storage
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        
        # Memory stores
        self.short_term_memory = deque(maxlen=20)  # Last 20 messages
        self.context = self._load_context()
        self.user_profile = self._load_user_profile()
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add message to memory."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add to short-term memory
        self.short_term_memory.append(message)
        
        # Store in Redis
        key = f"chat:history:{self.session_id}"
        self.redis_client.lpush(key, json.dumps(message))
        self.redis_client.expire(key, 3600 * 24)  # Expire after 24 hours
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return list(self.short_term_memory)[-limit:]
    
    def update_context(self, updates: Dict[str, Any]):
        """Update conversation context."""
        self.context.update(updates)
        self._save_context()
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self.context
    
    def update_user_profile(self, updates: Dict[str, Any]):
        """Update user profile with preferences."""
        self.user_profile.update(updates)
        self._save_user_profile()
    
    def _load_context(self) -> Dict[str, Any]:
        """Load context from Redis."""
        key = f"chat:context:{self.session_id}"
        context = self.redis_client.get(key)
        if context:
            return json.loads(context)
        return {
            "session_id": self.session_id,
            "started_at": datetime.utcnow().isoformat(),
            "selected_business": None,
            "table_id": None,
            "cart": [],
            "language": "en",
            "state": "initial"
        }
    
    def _save_context(self):
        """Save context to Redis."""
        key = f"chat:context:{self.session_id}"
        self.redis_client.setex(
            key,
            3600 * 24,  # 24 hours
            json.dumps(self.context)
        )
    
    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile from Redis."""
        # For now, use session-based profile
        # In production, this would be tied to user account
        key = f"user:profile:{self.session_id}"
        profile = self.redis_client.get(key)
        if profile:
            return json.loads(profile)
        return {
            "dietary_restrictions": [],
            "favorite_items": [],
            "order_history": [],
            "preferences": {}
        }
    
    def _save_user_profile(self):
        """Save user profile to Redis."""
        key = f"user:profile:{self.session_id}"
        self.redis_client.setex(
            key,
            3600 * 24 * 30,  # 30 days
            json.dumps(self.user_profile)
        )
    
    def summarize_conversation(self) -> str:
        """Summarize conversation for context."""
        if not self.short_term_memory:
            return "No conversation history."
        
        summary = []
        for msg in list(self.short_term_memory)[-5:]:  # Last 5 messages
            role = "Customer" if msg["role"] == "user" else "Bot"
            summary.append(f"{role}: {msg['content'][:100]}...")
        
        return "\n".join(summary)