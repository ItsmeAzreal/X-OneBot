"""Application settings using Pydantic."""
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This uses Pydantic to:
    1. Load values from .env file
    2. Validate data types
    3. Provide defaults
    """
    
    # API Settings
    PROJECT_NAME: str = "XoneBot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # --- START: ADD THESE NEW SETTINGS ---
    
    # AI Language Models
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # Voice Services
    ELEVENLABS_API_KEY: Optional[str] = None
    WHISPER_API_KEY: Optional[str] = None # Note: This will likely be the same as OPENAI_API_KEY

    # Vector Database
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None

    # External Services (Twilio, WhatsApp, Stripe)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    UNIVERSAL_BOT_NUMBER: Optional[str] = None

    WHATSAPP_BUSINESS_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    STRIPE_SECRET_KEY: Optional[str] = None

    # Add these new settings to your existing settings.py

    # Phone Provider Settings
    VONAGE_API_KEY: Optional[str] = None
    VONAGE_API_SECRET: Optional[str] = None
    VONAGE_APPLICATION_ID: Optional[str] = None

    MESSAGEBIRD_API_KEY: Optional[str] = None

    # Regional Phone Numbers
    ESTONIA_RECEIVER_NUMBER: Optional[str] = None  # For receiving forwarded calls
    LITHUANIA_RECEIVER_NUMBER: Optional[str] = None

    # Provider Selection
    DEFAULT_PHONE_PROVIDER: str = "twilio"  # Can be: twilio, vonage, messagebird
    PREFERRED_PROVIDERS_BY_REGION: Dict[str, List[str]] = {
    "LV": ["vonage", "messagebird"],  # Latvia
    "EE": ["twilio", "vonage"],       # Estonia
    "LT": ["vonage", "twilio"],       # Lithuania
    
    }
    
    # --- END: ADD THESE NEW SETTINGS ---

    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached settings instance.
    
    @lru_cache ensures we only create one instance
    and reuse it throughout the application.
    """
    return Settings()


# Create a single instance
settings = get_settings()