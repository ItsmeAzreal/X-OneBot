"""
Updated voice endpoints to handle multiple providers and forwarding.
"""
from typing import Optional 
from app.models import Business, PhoneNumber
from twilio.twiml.voice_response import VoiceResponse
from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.ai.voice_handler import VoiceHandler
from app.services.ai.universal_bot import UniversalBot
from app.services.phone.providers.multi_provider_manager import MultiProviderPhoneManager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/incoming")
async def handle_incoming_call(
    request: Request,
    From: str = Form(...),
    To: str = Form(...),
    CallSid: str = Form(...),
    ForwardedFrom: Optional[str] = Form(None),  # For forwarded calls
    SipHeader_X_Extension: Optional[str] = Form(None),  # Extension code
    db: Session = Depends(get_db)
):
    """Handle incoming voice call from any provider."""

    # Check for extension code (forwarded calls)
    extension = SipHeader_X_Extension or request.headers.get("X-Extension")

    # Route the call
    phone_manager = MultiProviderPhoneManager(db)
    business_id = await phone_manager.route_incoming_call(
        to_number=To,
        from_number=From,
        extension=extension
    )

    # If specific business found, load their context
    if business_id:
        logger.info(f"Routed call to business {business_id}")
        # Load business-specific greeting
        business = db.query(Business).filter(Business.id == business_id).first()
        if business:
            greeting = f"Welcome to {business.name}. How can I help you today?"
        else:
            greeting = "Welcome. How can I help you today?"
    else:
        # Universal number - needs café selection
        greeting = "Welcome to XoneBot. Which café would you like to connect to?"

    # Generate the TwiML response directly here
    response = VoiceResponse()
    response.say(greeting, voice="Polly.Joanna")
    
    # Return the response as a string-like object for FastAPI to handle
    return str(response)


@router.post("/forward")
async def handle_forwarding_request(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle call forwarding setup requests."""

    # This endpoint handles the forwarding logic
    # when a café's existing number forwards to us

    data = await request.form()
    extension = data.get("Digits")  # Extension entered by system

    if extension:
        # Verify extension and route to business
        phone_manager = MultiProviderPhoneManager(db)

        # Find business by extension
        phone_record = db.query(PhoneNumber).filter(
            PhoneNumber.metadata["extension_code"].astext == extension
        ).first()

        if phone_record:
            # Route to business bot
            return f"""
            <Response>
                <Say>Connecting to {phone_record.business.name}</Say>
                <Redirect>/api/v1/voice/business/{phone_record.business.id}</Redirect>
            </Response>
            """

    # Extension not found
    return """
    <Response>
        <Say>Invalid extension code. Please check your setup.</Say>
        <Hangup/>
    </Response>
    """