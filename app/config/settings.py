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
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False  # Log SQL queries
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str  # Used for JWT encoding
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # AI Services (for later)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # External Services (for later)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    
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