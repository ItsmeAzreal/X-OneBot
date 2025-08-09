"""
Voice Processing Service - Handles voice calls and speech processing.
Integrates with Twilio for calls, Whisper for STT, and ElevenLabs for TTS.
"""
import io
import asyncio
from typing import Optional, Dict, Any
import openai
from elevenlabs import generate, set_api_key
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

# Initialize services
openai.api_key = settings.OPENAI_API_KEY
set_api_key(settings.ELEVENLABS_API_KEY)


class VoiceHandler:
    """
    Handles voice interactions for phone calls.
    
    Features:
    1. Speech-to-text (Whisper)
    2. Text-to-speech (ElevenLabs)
    3. Phone call handling (Twilio)
    4. Voice personality customization
    """
    
    def __init__(self):
        # Twilio client
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Voice settings per business
        self.voice_profiles = {
            "friendly": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75
                }
            },
            "professional": {
                "voice_id": "ErXwobaYiN019PkySvjV",  # Antoni
                "settings": {
                    "stability": 0.85,
                    "similarity_boost": 0.65
                }
            }
        }
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """
        Convert speech to text using Whisper.
        
        Args:
            audio_data: Audio bytes (WAV, MP3, etc.)
            
        Returns:
            Transcribed text
        """
        try:
            # Create file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Transcribe with Whisper
            response = await asyncio.to_thread(
                openai.Audio.transcribe,
                model="whisper-1",
                file=audio_file,
                language="en"  # Auto-detect if not specified
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return ""
    
    async def text_to_speech(
        self,
        text: str,
        voice_profile: str = "friendly"
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs.
        
        Args:
            text: Text to speak
            voice_profile: Voice personality to use
            
        Returns:
            Audio bytes (MP3)
        """
        try:
            profile = self.voice_profiles.get(voice_profile, self.voice_profiles["friendly"])
            
            # Generate speech
            audio = generate(
                text=text,
                voice=profile["voice_id"],
                model="eleven_monolingual_v1",
                **profile["settings"]
            )
            
            # Convert generator to bytes
            audio_bytes = b"".join(audio)
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            # Return empty audio on failure
            return b""
    
    def handle_incoming_call(self, from_number: str) -> str:
        """
        Handle incoming phone call with TwiML response.
        
        Args:
            from_number: Caller's phone number
            
        Returns:
            TwiML response XML
        """
        response = VoiceResponse()
        
        # Greeting
        response.say(
            "Welcome to XoneBot! I can help you order food or make a reservation. "
            "Which cafe would you like to connect to?",
            voice="Polly.Joanna"
        )
        
        # Gather input
        gather = Gather(
            input="speech",
            timeout=3,
            language="en-US",
            action="/api/v1/voice/process",
            method="POST"
        )
        
        response.append(gather)
        
        # If no input
        response.say("I didn't catch that. Please try again.")
        response.redirect("/api/v1/voice/welcome")
        
        return str(response)
    
    def process_voice_input(
        self,
        speech_result: str,
        session_data: Dict[str, Any]
    ) -> str:
        """
        Process voice input and generate TwiML response.
        
        Args:
            speech_result: Transcribed speech
            session_data: Call session data
            
        Returns:
            TwiML response XML
        """
        response = VoiceResponse()
        
        # Process through chat service (simplified for now)
        if "coffee" in speech_result.lower():
            response.say(
                "Great! I found Sunrise Cafe nearby. "
                "Would you like to hear their menu or make a reservation?",
                voice="Polly.Joanna"
            )
        else:
            response.say(
                f"You said: {speech_result}. "
                "I can help you order food or make a reservation.",
                voice="Polly.Joanna"
            )
        
        # Continue gathering
        gather = Gather(
            input="speech",
            timeout=3,
            action="/api/v1/voice/process",
            method="POST"
        )
        response.append(gather)
        
        return str(response)
    
    async def create_outbound_call(
        self,
        to_number: str,
        message: str
    ) -> str:
        """
        Make an outbound call with a message.
        
        Args:
            to_number: Number to call
            message: Message to speak
            
        Returns:
            Call SID
        """
        try:
            call = self.twilio_client.calls.create(
                to=to_number,
                from_=settings.TWILIO_PHONE_NUMBER,
                twiml=f'<Response><Say>{message}</Say></Response>'
            )
            return call.sid
        except Exception as e:
            logger.error(f"Outbound call failed: {e}")
            return ""