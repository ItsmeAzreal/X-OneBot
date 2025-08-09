"""WhatsApp webhook endpoints."""
from fastapi import APIRouter, Request, Query, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.external.whatsapp_service import WhatsAppService
from app.services.ai.universal_bot import UniversalBot
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """Verify WhatsApp webhook for Meta."""
    
    whatsapp_service = WhatsAppService()
    result = whatsapp_service.verify_webhook(hub_mode, hub_token, hub_challenge)
    
    if result:
        return int(result)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle incoming WhatsApp messages."""
    
    data = await request.json()
    whatsapp_service = WhatsAppService()
    
    # Process webhook data
    message_data = whatsapp_service.process_webhook(data)
    
    if not message_data:
        return {"status": "ok"}
    
    # Process through universal bot
    bot = UniversalBot(db)
    response = await bot.process_message(
        session_id=message_data["from"],
        message=message_data["text"],
        channel="whatsapp"
    )
    
    # Send response back via WhatsApp
    await whatsapp_service.send_message(
        to_number=message_data["from"],
        message=response["message"],
        buttons=response.get("suggested_actions", [])
    )
    
    return {"status": "ok"}