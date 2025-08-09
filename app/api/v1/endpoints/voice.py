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
    CallSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle incoming voice call from Twilio."""
    
    voice_handler = VoiceHandler()
    
    # Generate TwiML response
    response = voice_handler.handle_incoming_call(From)
    
    return response


@router.post("/process")
async def process_voice_input(
    request: Request,
    SpeechResult: str = Form(None),
    CallSid: str = Form(...),
    From: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process voice input from caller."""
    
    if not SpeechResult:
        # No speech detected
        return """
        <Response>
            <Say>I didn't hear anything. Please try again.</Say>
            <Redirect>/api/v1/voice/incoming</Redirect>
        </Response>
        """
    
    # Process through universal bot
    bot = UniversalBot(db)
    response = await bot.process_message(
        session_id=CallSid,
        message=SpeechResult,
        channel="voice"
    )
    
    # Convert to TwiML
    voice_handler = VoiceHandler()
    twiml_response = voice_handler.process_voice_input(
        SpeechResult,
        {"session_id": CallSid, "from": From, "response": response}# XoneBot Week 3: Complete AI Integration & Universal Bot System

## 📋 Week 3 Overview
Transform XoneBot into an intelligent, universal AI assistant that serves multiple cafés through intelligent routing, multi-language support, and advanced AI capabilities.

---

## 🔧 Step 1: Update Environment Variables

### **File: `.env`** (Add these new variables)
```env
# AI Models
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...

# Voice Services
ELEVENLABS_API_KEY=...
WHISPER_API_KEY=...

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=...

# WhatsApp
WHATSAPP_BUSINESS_TOKEN=...
WHATSAPP_VERIFY_TOKEN=...

# Universal Bot Config
UNIVERSAL_BOT_NUMBER=+1-800-CAFE-BOT
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,es,fr,de,it,pt,zh,ja

# AI Model Costs (per 1000 tokens)
GROQ_COST=0.001
CLAUDE_COST=0.01
GPT4_COST=0.02