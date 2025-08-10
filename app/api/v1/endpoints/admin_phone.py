"""
Admin dashboard endpoints for phone management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.config.database import get_db
from app.core.dependencies import get_current_business
from app.models import PhoneNumber, Business
from app.schemas.phone import PhoneConfigRequest, PhoneStatusResponse

router = APIRouter()


@router.get("/phone-status")
async def get_phone_status(
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Get current phone configuration and status."""

    # Get all phone numbers for business
    phone_numbers = db.query(PhoneNumber).filter(
        PhoneNumber.business_id == business.id
    ).all()

    return {
        "configuration": {
            "type": business.phone_config,
            "monthly_cost": business.custom_number_monthly_cost,
            "features": business.phone_features
        },
        "phone_numbers": [
            {
                "id": p.id,
                "number": p.phone_number,
                "provider": p.provider,
                "status": p.status,
                "is_primary": p.is_primary,
                "capabilities": p.capabilities,
                "is_existing": p.provider == "existing"
            }
            for p in phone_numbers
        ],
        "usage": business.phone_usage or {}
    }


@router.post("/update-phone-config")
async def update_phone_configuration(
    config: PhoneConfigRequest,
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Update phone configuration for business."""

    # Update business phone config
    business.phone_config = config.phone_type
    business.phone_features = config.features

    # Calculate new monthly cost
    base_cost = 0
    if config.phone_type in ["custom_only", "both"]:
        base_cost = 15 if config.phone_type == "custom_only" else 20

    if config.features.get("whatsapp_enabled"):
        base_cost += 10

    business.custom_number_monthly_cost = base_cost

    db.commit()

    return {
        "success": True,
        "new_monthly_cost": base_cost,
        "message": "Phone configuration updated"
    }


@router.get("/available-providers")
async def get_available_providers(
    country_code: str = "+371"
):
    """Get list of available providers for a country."""

    providers = []

    # Check each provider's availability
    if country_code == "+371":  # Latvia
        providers = [
            {
                "name": "vonage",
                "display_name": "Vonage",
                "has_numbers": True,
                "estimated_cost": 12.00,
                "features": ["voice", "sms"]
            },
            {
                "name": "existing",
                "display_name": "Use Your Existing Number",
                "has_numbers": True,
                "estimated_cost": 0,
                "features": ["voice"]
            }
        ]
    elif country_code == "+372":  # Estonia
        providers = [
            {
                "name": "twilio",
                "display_name": "Twilio",
                "has_numbers": True,
                "estimated_cost": 15.00,
                "features": ["voice", "sms", "whatsapp"]
            }
        ]

    return {"providers": providers}