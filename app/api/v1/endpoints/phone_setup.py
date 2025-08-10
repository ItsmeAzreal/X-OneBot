"""
Phone setup endpoints for café owners.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.dependencies import get_current_business
from app.services.phone.multi_provider_manager import MultiProviderPhoneManager
from typing import Optional

router = APIRouter()


@router.get("/search-numbers")
async def search_available_numbers(
    country_code: str = "+371",
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Search for available phone numbers."""

    manager = MultiProviderPhoneManager(db)
    numbers = await manager.search_numbers(country_code)

    return {
        "available_numbers": [
            {
                "number": n.number,
                "provider": n.provider,
                "monthly_cost": n.monthly_cost,
                "capabilities": n.capabilities
            }
            for n in numbers
        ]
    }


@router.post("/provision-number")
async def provision_new_number(
    phone_number: str,
    provider: str,
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Provision a new phone number for the business."""

    manager = MultiProviderPhoneManager(db)

    # Find the number info
    numbers = await manager.search_numbers(phone_number[:4])
    number_info = next((n for n in numbers if n.number == phone_number), None)

    if not number_info:
        raise HTTPException(status_code=404, detail="Number not available")

    result = await manager.provision_number(business.id, number_info)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    return {
        "success": True,
        "number": phone_number,
        "message": "Number provisioned successfully"
    }


@router.post("/setup-existing-number")
async def setup_existing_number(
    existing_number: str,
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Setup café's existing phone number."""

    manager = MultiProviderPhoneManager(db)
    result = manager.setup_existing_number(business.id, existing_number)

    return {
        "success": True,
        "phone_id": result["phone_id"],
        "extension_code": result["extension_code"],
        "forwarding_number": result["forwarding_number"],
        "instructions": result["instructions"]
    }


@router.post("/verify-existing-number")
async def verify_existing_number(
    phone_id: int,
    verification_code: str,
    db: Session = Depends(get_db),
    business = Depends(get_current_business)
):
    """Verify that existing number forwarding is working."""

    manager = MultiProviderPhoneManager(db)
    success = manager.verify_existing_number(
        business.id,
        phone_id,
        verification_code
    )

    if not success:
        raise HTTPException(status_code=400, detail="Verification failed")

    return {
        "success": True,
        "message": "Phone number verified and activated"
    }