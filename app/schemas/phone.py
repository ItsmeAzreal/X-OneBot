"""Phone management schemas."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class PhoneProvider(str, Enum):
    """Supported phone providers."""
    TWILIO = "twilio"
    VONAGE = "vonage"
    WHATSAPP_CLOUD = "whatsapp_cloud"


class PhoneSetupOption(str, Enum):
    """Phone setup options for onboarding."""
    UNIVERSAL_ONLY = "universal_only"  # Free, shared number
    CUSTOM_NUMBER = "custom_number"    # Auto-provision new number
    OWN_NUMBER = "own_number"          # Use existing number
    BOTH = "both"                      # Universal + custom


class PhoneConfigRequest(BaseModel):
    """Phone configuration request."""
    setup_option: PhoneSetupOption
    provider: Optional[PhoneProvider] = PhoneProvider.TWILIO
    country_code: str = "US"
    area_code: Optional[str] = None
    existing_number: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "setup_option": "custom_number",
                "provider": "twilio",
                "country_code": "LV",
                "area_code": "371"
            }
        }


class PhoneStatusResponse(BaseModel):
    """Phone status response."""
    business_id: int
    setup_option: PhoneSetupOption
    universal_number: Optional[str] = None
    dedicated_number: Optional[str] = None
    provider: Optional[PhoneProvider] = None
    is_verified: bool = False
    is_active: bool = False
    whatsapp_connected: bool = False
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "business_id": 1,
                "setup_option": "both",
                "universal_number": "+1-800-XONEBOT",
                "dedicated_number": "+371-2012-3456",
                "provider": "twilio",
                "is_verified": True,
                "is_active": True,
                "whatsapp_connected": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class WhatsAppSetupRequest(BaseModel):
    """WhatsApp Business API setup request."""
    phone_number: str
    business_name: str
    business_description: Optional[str] = None
    business_address: Optional[str] = None
    business_email: Optional[str] = None
    verification_method: str = "sms"  # sms or voice


class OTPVerificationRequest(BaseModel):
    """OTP verification for phone ownership."""
    phone_number: str
    otp_code: str


class UniversalAccessRequest(BaseModel):
    """Request access to universal number."""
    business_id: int
    preferred_greeting: Optional[str] = None
    supported_languages: List[str] = ["en"]

    class Config:
        json_schema_extra = {
            "example": {
                "business_id": 1,
                "preferred_greeting": "Welcome to Sunrise Café!",
                "supported_languages": ["en", "lv", "ru"]
            }
        }