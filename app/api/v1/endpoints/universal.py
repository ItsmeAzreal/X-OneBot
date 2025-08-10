"""Universal system endpoints."""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import Business
from app.schemas.whatsapp import WhatsAppWebhook
from app.services.external.whatsapp_universal import UniversalWhatsAppService

router = APIRouter()


@router.post("/webhook")
async def universal_webhook(
    webhook_data: WhatsAppWebhook,
    db: Session = Depends(get_db)
) -> Any:
    """
    Universal WhatsApp webhook for all cafés.
    This single endpoint handles all incoming WhatsApp messages.
    """
    # Extract message from webhook
    message = webhook_data.get_message()
    if not message:
        return {"status": "no_message"}

    # Initialize universal service
    universal_service = UniversalWhatsAppService(db)

    # Handle message
    response = await universal_service.handle_universal_message(message)

    # In production, send response back through WhatsApp API
    # For now, log the response
    # logger.info(f"Response to {message.from_number}: {response}")

    return {"status": "processed", "response": response}


@router.get("/cafes")
async def get_available_cafes(
    location: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get list of available cafés."""
    query = db.query(Business).filter(Business.is_active == True)

    # In production, filter by location/distance
    if location:
        # Placeholder for location-based filtering
        pass

    cafes = query.all()

    return [
        {
            "id": cafe.id,
            "name": cafe.name,
            "description": cafe.description,
            "languages": cafe.settings.get("languages", ["en"]),
            "rating": 4.5,  # Placeholder - would come from reviews
            "distance": "0.5 km"  # Placeholder - would calculate from location
        }
        for cafe in cafes
    ]


@router.post("/select-cafe/{business_id}")
async def select_cafe(
    business_id: int,
    user_phone: str,
    db: Session = Depends(get_db)
) -> Any:
    """Select a café for conversation."""
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.is_active == True
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Café not found"
        )

    # In production, save selection to session/cache
    return {
        "message": f"Selected {business.name}",
        "business_id": business_id
    }