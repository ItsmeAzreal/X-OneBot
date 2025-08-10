"""Onboarding endpoints for phone setup."""
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import random
import string
from datetime import datetime, timedelta
from app.config.database import get_db
from app.core.dependencies import get_current_business
from app.models import Business, MenuItem
from app.schemas.phone import (
    PhoneConfigRequest,
    PhoneStatusResponse,
    WhatsAppSetupRequest,
    OTPVerificationRequest,
    UniversalAccessRequest,
    PhoneSetupOption
)
from app.services.external.phone_manager import PhoneManagerService

router = APIRouter()


@router.post("/phone-setup")
async def setup_phone_system(
    config: PhoneConfigRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> PhoneStatusResponse:
    """
    Setup phone system based on selected option.
    Options:
    1. universal_only - Free, shared number
    2. custom_number - Auto-provision new number
    3. own_number - Use existing number with OTP
    4. both - Universal + custom number
    """
    phone_manager = PhoneManagerService(db)

    # Handle different setup options
    if config.setup_option == PhoneSetupOption.UNIVERSAL_ONLY:
        # Just register for universal access
        result = await phone_manager.register_universal_access(business.id)

    elif config.setup_option == PhoneSetupOption.CUSTOM_NUMBER:
        # Auto-provision new number
        result = await phone_manager.provision_new_number(
            business_id=business.id,
            country_code=config.country_code,
            area_code=config.area_code,
            provider=config.provider
        )

    elif config.setup_option == PhoneSetupOption.OWN_NUMBER:
        # Use existing number - need OTP verification
        if not config.existing_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Existing number required for this option"
            )

        # Send OTP for verification
        otp = await phone_manager.send_otp(config.existing_number)

        # Store OTP temporarily (in production, use Redis)
        # For now, return status indicating OTP sent
        result = {
            "status": "otp_sent",
            "phone_number": config.existing_number,
            "message": "Please verify ownership with OTP"
        }

    else:  # BOTH option
        # Register universal AND provision custom
        universal_result = await phone_manager.register_universal_access(business.id)
        custom_result = await phone_manager.provision_new_number(
            business_id=business.id,
            country_code=config.country_code,
            area_code=config.area_code,
            provider=config.provider
        )

        result = {
            "universal": universal_result,
            "custom": custom_result
        }

    # Update business settings
    business.settings = business.settings or {}
    business.settings['phone_setup'] = {
        'option': config.setup_option,
        'provider': config.provider,
        'setup_date': datetime.utcnow().isoformat()
    }
    db.commit()

    # Schedule WhatsApp setup in background
    if config.setup_option != PhoneSetupOption.UNIVERSAL_ONLY:
        background_tasks.add_task(
            phone_manager.setup_whatsapp_business,
            business.id
        )

    return PhoneStatusResponse(
        business_id=business.id,
        setup_option=config.setup_option,
        universal_number="+1-800-XONEBOT" if config.setup_option in [PhoneSetupOption.UNIVERSAL_ONLY, PhoneSetupOption.BOTH] else None,
        dedicated_number=result.get('phone_number') if config.setup_option != PhoneSetupOption.UNIVERSAL_ONLY else None,
        provider=config.provider,
        is_verified=False,
        is_active=False,
        whatsapp_connected=False,
        created_at=datetime.utcnow()
    )


@router.post("/whatsapp-verify")
async def verify_whatsapp_setup(
    otp_request: OTPVerificationRequest,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Verify WhatsApp Business API setup with OTP."""
    phone_manager = PhoneManagerService(db)

    # Verify OTP
    is_valid = await phone_manager.verify_otp(
        otp_request.phone_number,
        otp_request.otp_code
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )

    # Complete WhatsApp setup
    result = await phone_manager.complete_whatsapp_setup(
        business.id,
        otp_request.phone_number
    )

    return {
        "status": "verified",
        "whatsapp_connected": True,
        "message": "WhatsApp Business API successfully connected"
    }


@router.get("/progress")
async def get_onboarding_progress(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Get onboarding progress status."""

    steps_completed = []
    steps_pending = []

    # Check business profile
    if business.name and business.slug:
        steps_completed.append("business_profile")
    else:
        steps_pending.append("business_profile")

    # Check phone setup
    phone_setup = business.settings.get('phone_setup') if business.settings else None
    if phone_setup:
        steps_completed.append("phone_setup")
    else:
        steps_pending.append("phone_setup")

    # Check menu
    menu_items = db.query(MenuItem).filter(
        MenuItem.business_id == business.id
    ).count()
    if menu_items > 0:
        steps_completed.append("menu_setup")
    else:
        steps_pending.append("menu_setup")

    # Check WhatsApp
    whatsapp_connected = phone_setup.get('whatsapp_connected', False) if phone_setup else False
    if whatsapp_connected:
        steps_completed.append("whatsapp_setup")
    else:
        steps_pending.append("whatsapp_setup")

    progress_percentage = (len(steps_completed) / (len(steps_completed) + len(steps_pending))) * 100

    return {
        "progress_percentage": progress_percentage,
        "steps_completed": steps_completed,
        "steps_pending": steps_pending,
        "is_complete": len(steps_pending) == 0
    }