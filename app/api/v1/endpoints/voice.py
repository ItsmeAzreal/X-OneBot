"""Voice call endpoints for Twilio integration."""
from fastapi import APIRouter, Request, Form, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.ai.voice_handler import VoiceHandler
from app.services.ai.universal_bot import UniversalBot
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/incoming")
async def handle_incoming_call(
    request: Request,
    From: str = Form(...),
    To: str = Form(...), # Capture the number that was called
    CallSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle incoming voice call from Twilio."""
    
    # Process through universal bot first to get initial response
    bot = UniversalBot(db)
    response_data = await bot.process_message(
        session_id=CallSid,
        message="<CALL_START>", # Use a special message for the start of a call
        channel="voice",
        phone_number=To # Pass the number that was called to the bot
    )

    # Convert to TwiML
    voice_handler = VoiceHandler()
    twiml_response = voice_handler.generate_initial_twiml(response_data)
    
    return twiml_response


@router.post("/process")
async def process_voice_input(
    request: Request,
    SpeechResult: str = Form(None),
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...), # Also capture 'To' here for context
    db: Session = Depends(get_db)
):
    """Process voice input from caller."""
    
    voice_handler = VoiceHandler()

    if not SpeechResult:
        # No speech detected, generate a retry TwiML
        twiml_response = voice_handler.generate_retry_twiml("I didn't hear anything. Please try again.")
        return twiml_response

    # Process spoken text through universal bot
    bot = UniversalBot(db)
    response_data = await bot.process_message(
        session_id=CallSid,
        message=SpeechResult,
        channel="voice",
        phone_number=To
    )
    
    # Convert bot's text response back into TwiML for the user to hear
    twiml_response = voice_handler.generate_response_twiml(response_data)
    
    return twiml_response


@router.post("/status")
async def call_status(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle call status updates from Twilio."""
    logger.info(f"Call {CallSid} status: {CallStatus}")
    return ""