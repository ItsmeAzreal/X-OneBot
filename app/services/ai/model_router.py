"""
AI Model Router - Intelligent routing between different AI models.
Routes to the most cost-effective model based on query complexity.
"""
from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
import time
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from groq import Groq
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Available AI models."""
    GROQ = "groq"  # Fast and cheap
    CLAUDE = "claude"  # Best reasoning
    GPT4 = "gpt4"  # Best language support
    GPT3_5 = "gpt3.5"  # Fallback


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"  # Menu queries, prices
    MODERATE = "moderate"  # Orders with modifications
    COMPLEX = "complex"  # Special requests, complaints
    MULTILINGUAL = "multilingual"  # Non-English queries


class ModelRouter:
    """
    Routes queries to the most appropriate AI model.
    
    Strategy:
    1. Simple queries → Groq (cheapest, fastest)
    2. Complex queries → Claude (best reasoning)
    3. Multilingual → GPT-4 (best language support)
    4. Fallback chain if primary model fails
    """
    
    def __init__(self):
        # Initialize models
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.claude = ChatAnthropic(
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            model_name="claude-3-sonnet-20240229"
        )
        self.gpt4 = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-4-turbo-preview"
        )
        self.gpt35 = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo"
        )
        
        # Cost tracking
        self.model_costs = {
            ModelType.GROQ: 0.001,
            ModelType.CLAUDE: 0.01,
            ModelType.GPT4: 0.02,
            ModelType.GPT3_5: 0.002
        }
    
    async def route_query(
        self,
        query: str,
        context: Dict[str, Any],
        language: str = "en",
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route query to appropriate model.
        
        Args:
            query: User's message
            context: Conversation context
            language: Detected language
            intent: Detected intent (if available)
            
        Returns:
            Response with model used and cost
        """
        start_time = time.time()
        
        # Determine complexity
        complexity = self._assess_complexity(query, intent, language)
        
        # Select primary model
        primary_model = self._select_model(complexity, language)
        
        # Try primary model with fallback chain
        response = await self._execute_with_fallback(
            query, context, primary_model, language
        )
        
        # Track metrics
        response_time = (time.time() - start_time) * 1000  # ms
        
        return {
            "response": response["text"],
            "model_used": response["model"],
            "response_time_ms": response_time,
            "cost": self.model_costs[response["model"]],
            "complexity": complexity
        }
    
    def _assess_complexity(
        self,
        query: str,
        intent: Optional[str],
        language: str
    ) -> QueryComplexity:
        """Assess query complexity."""
        query_lower = query.lower()
        
        # Non-English = multilingual complexity
        if language != "en":
            return QueryComplexity.MULTILINGUAL
        
        # Simple intents
        simple_intents = ["menu_inquiry", "price_check", "hours_inquiry"]
        if intent in simple_intents:
            return QueryComplexity.SIMPLE
        
        # Simple keywords
        simple_keywords = ["menu", "price", "cost", "hours", "open", "close"]
        if any(keyword in query_lower for keyword in simple_keywords):
            return QueryComplexity.SIMPLE
        
        # Complex indicators
        complex_indicators = [
            "but", "except", "without", "instead", "modify", "change",
            "allergic", "intolerant", "special", "complaint"
        ]
        if any(indicator in query_lower for indicator in complex_indicators):
            return QueryComplexity.COMPLEX
        
        # Default to moderate
        return QueryComplexity.MODERATE
    
    def _select_model(
        self,
        complexity: QueryComplexity,
        language: str
    ) -> ModelType:
        """Select primary model based on complexity."""
        if complexity == QueryComplexity.SIMPLE:
            return ModelType.GROQ
        elif complexity == QueryComplexity.COMPLEX:
            return ModelType.CLAUDE
        elif complexity == QueryComplexity.MULTILINGUAL:
            return ModelType.GPT4
        else:  # MODERATE
            return ModelType.GROQ  # Try cheap first
    
    async def _execute_with_fallback(
        self,
        query: str,
        context: Dict[str, Any],
        primary_model: ModelType,
        language: str
    ) -> Dict[str, Any]:
        """Execute query with fallback chain."""
        # Define fallback chains
        fallback_chains = {
            ModelType.GROQ: [ModelType.GROQ, ModelType.GPT3_5, ModelType.CLAUDE],
            ModelType.CLAUDE: [ModelType.CLAUDE, ModelType.GPT4, ModelType.GPT3_5],
            ModelType.GPT4: [ModelType.GPT4, ModelType.CLAUDE, ModelType.GPT3_5],
            ModelType.GPT3_5: [ModelType.GPT3_5, ModelType.GROQ, ModelType.CLAUDE]
        }
        
        chain = fallback_chains[primary_model]
        
        for model_type in chain:
            try:
                response = await self._call_model(
                    model_type, query, context, language
                )
                return {
                    "text": response,
                    "model": model_type
                }
            except Exception as e:
                logger.warning(f"Model {model_type} failed: {e}")
                continue
        
        # All models failed, return error response
        return {
            "text": "I apologize, I'm having trouble processing your request. Please try again or contact support.",
            "model": ModelType.GPT3_5
        }
    
    async def _call_model(
        self,
        model_type: ModelType,
        query: str,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Call specific model."""
        # Build prompt with context
        prompt = self._build_prompt(query, context, language)
        
        if model_type == ModelType.GROQ:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
            
        elif model_type == ModelType.CLAUDE:
            response = await self.claude.ainvoke(prompt)
            return response.content
            
        elif model_type == ModelType.GPT4:
            response = await self.gpt4.ainvoke(prompt)
            return response.content
            
        else:  # GPT3.5
            response = await self.gpt35.ainvoke(prompt)
            return response.content
    
    def _build_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Build prompt with context."""
        prompt = f"""You are an AI assistant for {context.get('business_name', 'a cafe')}.
        
Current context:
- Customer is at table: {context.get('table_number', 'Unknown')}
- Language preference: {language}
- Current cart: {context.get('cart', [])}
- Business hours: {context.get('business_hours', 'Not specified')}

Customer query: {query}

Please provide a helpful, friendly response. If the customer is ordering, confirm the items and prices.
If they have dietary restrictions, carefully check ingredients.
Always be polite and professional."""
        
        return prompt