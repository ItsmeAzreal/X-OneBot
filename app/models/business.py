"""Updated Business model with phone number configuration."""
from sqlalchemy import Column, String, JSON, Boolean, Enum as SQLEnum, DateTime, Float
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class SubscriptionPlan(str, enum.Enum):
    """Subscription tiers for SaaS model."""
    BASIC = "basic"  # $29/month - Universal number only
    PRO = "pro"  # $79/month - Universal + Custom number
    ENTERPRISE = "enterprise"  # $199/month - Everything


class PhoneNumberType(str, enum.Enum):
    """Phone number configuration types."""
    UNIVERSAL_ONLY = "universal_only"  # Free - only on universal bot
    CUSTOM_ONLY = "custom_only"  # Paid - only custom number
    BOTH = "both"  # Paid - universal + custom


class Business(BaseModel):
    """
    Updated Business model with phone configuration.
    """
    __tablename__ = "businesses"
    
    # Basic Information (existing fields)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(String(500))
    
    # Subscription
    subscription_plan = Column(
        SQLEnum(SubscriptionPlan),
        default=SubscriptionPlan.BASIC,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    trial_ends_at = Column(DateTime(timezone=True))
    
    # NEW: Phone Number Configuration
    phone_config = Column(
        SQLEnum(PhoneNumberType),
        default=PhoneNumberType.UNIVERSAL_ONLY,
        nullable=False
    )
    
    # NEW: Custom phone numbers (if applicable)
    custom_phone_number = Column(String(20))  # Their dedicated number
    custom_whatsapp_number = Column(String(20))  # WhatsApp Business number
    custom_phone_sid = Column(String(50))  # Twilio SID for the number
    
    # NEW: Phone features
    phone_features = Column(JSON, default=dict)
    # Example: {
    #   "voice_enabled": true,
    #   "whatsapp_enabled": false,
    #   "sms_enabled": true,
    #   "transfer_to_human": true,
    #   "business_hours_only": false,
    #   "voice_personality": "friendly",
    #   "monthly_minutes_limit": 1000
    # }
    
    # NEW: Phone usage tracking
    phone_usage = Column(JSON, default=dict)
    # Example: {
    #   "voice_minutes_used": 450,
    #   "sms_sent": 1200,
    #   "whatsapp_messages": 3400,
    #   "last_reset_date": "2024-01-01"
    # }
    
    # NEW: Custom number pricing
    custom_number_monthly_cost = Column(Float, default=0.0)
    
    # Existing fields...
    settings = Column(JSON, default=dict)
    branding_config = Column(JSON, default=dict)
    contact_info = Column(JSON, default=dict)
    
    # Relationships
    users = relationship("User", back_populates="business", cascade="all, delete-orphan")
    menu_categories = relationship("MenuCategory", back_populates="business", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="business", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="business", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="business", cascade="all, delete-orphan")
    phone_numbers = relationship("PhoneNumber", back_populates="business", cascade="all, delete-orphan")