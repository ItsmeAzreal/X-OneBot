"""Business model for multi-tenant architecture."""
from sqlalchemy import Column, String, JSON, Boolean, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class SubscriptionPlan(str, enum.Enum):
    """Subscription tiers for SaaS model."""
    BASIC = "basic"  # $29/month
    PRO = "pro"  # $79/month
    ENTERPRISE = "enterprise"  # $199/month


class Business(BaseModel):
    """
    Represents a cafe/restaurant using XoneBot.
    
    This is the core of our multi-tenant architecture.
    Every other model will reference a business_id.
    """
    __tablename__ = "businesses"
    
    # Basic Information
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
    
    # Configuration (stored as JSON for flexibility)
    settings = Column(JSON, default=dict)
    # Example: {
    #   "working_hours": {"mon": "9-17", "tue": "9-17"},
    #   "languages": ["en", "es"],
    #   "timezone": "America/New_York"
    # }
    
    branding_config = Column(JSON, default=dict)
    # Example: {
    #   "primary_color": "#FF6B6B",
    #   "logo_url": "https://...",
    #   "bot_personality": "friendly"
    # }
    
    contact_info = Column(JSON, default=dict)
    # Example: {
    #   "phone": "+1234567890",
    #   "email": "hello@cafe.com",
    #   "address": "123 Main St"
    # }
    
    # Relationships (one business has many...)
    users = relationship("User", back_populates="business", cascade="all, delete-orphan")
    menu_categories = relationship("MenuCategory", back_populates="business", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="business", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="business", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="business", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Business {self.name} ({self.slug})>"