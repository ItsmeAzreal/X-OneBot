"""
Twilio provider implementation.
"""
from typing import Dict, Any, Optional, List
from twilio.rest import Client
from app.services.phone.providers.base import BasePhoneProvider, PhoneNumberInfo
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class TwilioProvider(BasePhoneProvider):
    """Twilio phone provider implementation."""

    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.provider_name = "twilio"

    async def search_available_numbers(
        self,
        country_code: str,
        region: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[PhoneNumberInfo]:
        """Search for available Twilio numbers."""

        try:
            # Map country code to country
            country_map = {
                "+371": "LV",  # Latvia (might not have)
                "+372": "EE",  # Estonia
                "+370": "LT",  # Lithuania
                "+1": "US",    # USA
            }

            country = country_map.get(country_code, "US")

            # Search for numbers
            available = self.client.available_phone_numbers(country).local.list(
                limit=10
            )

            numbers = []
            for number in available:
                info = PhoneNumberInfo(
                    number=number.phone_number,
                    country_code=country_code,
                    provider=self.provider_name,
                    capabilities=self._parse_capabilities(number.capabilities),
                    monthly_cost=15.00,  # Twilio typical cost
                    setup_cost=1.00,
                    region=number.region
                )
                numbers.append(info)

            return numbers

        except Exception as e:
            logger.error(f"Twilio search failed: {e}")
            return []

    async def provision_number(
        self,
        phone_number: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """Provision a Twilio number."""

        try:
            purchased = self.client.incoming_phone_numbers.create(
                phone_number=phone_number,
                voice_url=f"{webhook_url}/voice/incoming",
                sms_url=f"{webhook_url}/sms/incoming",
                voice_method="POST",
                sms_method="POST"
            )

            return {
                "success": True,
                "sid": purchased.sid,
                "number": purchased.phone_number,
                "provider": self.provider_name
            }

        except Exception as e:
            logger.error(f"Twilio provision failed: {e}")
            return {"success": False, "error": str(e)}

    async def release_number(self, phone_number: str) -> bool:
        """Release a Twilio number."""

        try:
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=phone_number
            )

            if numbers:
                numbers[0].delete()
                return True
            return False

        except Exception as e:
            logger.error(f"Twilio release failed: {e}")
            return False

    async def setup_forwarding(
        self,
        from_number: str,
        to_number: str,
        extension: Optional[str] = None
    ) -> bool:
        """Setup call forwarding in Twilio."""

        try:
            # Update the number's voice webhook
            numbers = self.client.incoming_phone_numbers.list(
                phone_number=from_number
            )

            if numbers:
                # Create TwiML for forwarding
                twiml = f'<Response><Dial>{to_number}'
                if extension:
                    twiml += f'<Extension>{extension}</Extension>'
                twiml += '</Dial></Response>'

                numbers[0].update(
                    voice_url=f"{settings.API_URL}/api/v1/voice/forward",
                    voice_method="POST"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Twilio forwarding setup failed: {e}")
            return False

    async def send_sms(
        self,
        to_number: str,
        from_number: str,
        message: str
    ) -> bool:
        """Send SMS via Twilio."""

        try:
            message = self.client.messages.create(
                to=to_number,
                from_=from_number,
                body=message
            )
            return message.sid is not None

        except Exception as e:
            logger.error(f"Twilio SMS failed: {e}")
            return False

    async def make_call(
        self,
        to_number: str,
        from_number: str,
        twiml_url: str
    ) -> str:
        """Make outbound call via Twilio."""

        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=twiml_url,
                method="POST"
            )
            return call.sid

        except Exception as e:
            logger.error(f"Twilio call failed: {e}")
            return ""

    def _parse_capabilities(self, twilio_capabilities: Dict) -> List[str]:
        """Parse Twilio capabilities to our format."""
        capabilities = []
        if twilio_capabilities.get("voice"):
            capabilities.append("voice")
        if twilio_capabilities.get("SMS"):
            capabilities.append("sms")
        if twilio_capabilities.get("MMS"):
            capabilities.append("mms")
        return capabilities