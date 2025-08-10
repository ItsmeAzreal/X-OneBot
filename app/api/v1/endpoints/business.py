"""Updated business endpoints with phone configuration."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.dependencies import get_current_business
from app.models import Business, PhoneNumberType
from app.schemas.business import BusinessPhoneConfig, PhoneProvisioningResponse
from app.services.phone.phone_manager import PhoneManager

router = APIRouter()


@router.post("/{business_id}/phone-setup", response_model=PhoneProvisioningResponse)
async def setup_phone_configuration(
    business_id: int,
    config: BusinessPhoneConfig,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
) -> Any:
    """
    Configure phone setup for business during onboarding.
    
    Options:
    1. Universal only (free)
    2. Custom only (paid)
    3. Both (paid premium)
    """
    
    # Verify business ownership
    if current_business.id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to configure this business"
        )
    
    phone_manager = PhoneManager(db)
    
    # Process phone configuration
    result = phone_manager.onboard_business(
        business_id=business_id,
        phone_config=config.phone_config,
        wants_whatsapp=config.enable_whatsapp
    )
    
    return PhoneProvisioningResponse(
        business_id=result["business_id"],
        universal_access=result["universal_access"],
        custom_number=result["custom_number"],
        whatsapp_enabled=result["whatsapp_enabled"],
        monthly_cost=result["monthly_cost"],
        message="Phone configuration successful"
    )


@router.get("/{business_id}/phone-status")
async def get_phone_status(
    business_id: int,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
) -> Any:
    """Get current phone configuration and usage for business."""
    
    if current_business.id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    phone_manager = PhoneManager(db)
    usage = phone_manager.check_usage_limits(business_id)
    
    return {
        "phone_config": current_business.phone_config,
        "custom_number": current_business.custom_phone_number,
        "whatsapp_number": current_business.custom_whatsapp_number,
        "universal_access": current_business.phone_config in [
            PhoneNumberType.UNIVERSAL_ONLY,
            PhoneNumberType.BOTH
        ],
        "usage": usage,
        "monthly_cost": current_business.custom_number_monthly_cost
    }


@router.post("/{business_id}/transfer-to-human")
async def initiate_human_transfer(
    business_id: int,
    call_sid: str,
    db: Session = Depends(get_db),
    current_business: Business = Depends(get_current_business)
) -> Any:
    """Initiate transfer to human staff (custom numbers only)."""
    
    if current_business.id != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    if current_business.phone_config == PhoneNumberType.UNIVERSAL_ONLY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Human transfer not available for universal-only configuration"
        )
    
    phone_manager = PhoneManager(db)
    success = phone_manager.transfer_to_human(business_id, call_sid)
    
    if success:
        return {"status": "success", "message": "Transfer initiated"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transfer failed"
        )