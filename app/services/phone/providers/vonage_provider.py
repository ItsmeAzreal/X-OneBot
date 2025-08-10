"""
Vonage (Nexmo) provider implementation for Latvian numbers.
"""
from typing import Dict, Any, Optional, List
import vonage
from app.services.phone.providers.base import BasePhoneProvider, PhoneNumberInfo
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class VonageProvider(BasePhoneProvider):
    """Vonage phone provider implementation."""

    def __init__(self):
        self.client = vonage.Client(
            key=settings.VONAGE_API_KEY,
            secret=settings.VONAGE_API_SECRET
        )
        self.provider_name = "vonage"

    async def search_available_numbers(
        self,
        country_code: str,
        region: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> List[PhoneNumberInfo]:
        """Search for available Vonage numbers."""

        try:
            # Map country code to country
            country_map = {
                "+371": "LV",  # Latvia - Vonage has these!
                "+372": "EE",  # Estonia
                "+370": "LT",  # Lithuania
            }

            country = country_map.get(country_code, "LV")

            # Search for numbers
            response = self.client.numbers.get_available_numbers(
                country_code=country,
                features=["VOICE", "SMS"] if capabilities else None
            )

            numbers = []
            for number in response.get("numbers", []):
                info = PhoneNumberInfo(
                    number=number["msisdn"],
                    country_code=country_code,
                    provider=self.provider_name,
                    capabilities=number.get("features", []),
                    monthly_cost=12.00,  # Vonage typical cost
                    setup_cost=0.50,
                    region=number.get("region")
                )
                numbers.append(info)

            return numbers

        except Exception as e:
            logger.error(f"Vonage search failed: {e}")
            return []

    async def provision_number(
        self,
        phone_number: str,
        webhook_url: str
    ) -> Dict[str, Any]:
        """Provision a Vonage number."""

        try:
            response = self.client.numbers.buy_number({
                "country": "LV",
                "msisdn": phone_number
            })

            # Update webhooks
            self.client.numbers.update_number({
                "msisdn": phone_number,
                "moHttpUrl": f"{webhook_url}/sms/incoming",
                "voiceCallbackType": "app",
                "voiceCallbackValue": settings.VONAGE_APPLICATION_ID
            })

            return {
                "success": True,
                "number": phone_number,
                "provider": self.provider_name
            }

        except Exception as e:
            logger.error(f"Vonage provision failed: {e}")
            return {"success": False, "error": str(e)}

    async def release_number(self, phone_number: str) -> bool:
        """Release a Vonage number."""

        try:
            response = self.client.numbers.cancel_number({
                "msisdn": phone_number
            })
            return response.get("error-code") == "200"

        except Exception as e:
            logger.error(f"Vonage release failed: {e}")
            return False

    async def setup_forwarding(
        self,
        from_number: str,
        to_number: str,
        extension: Optional[str] = None
    ) -> bool:
        """Setup call forwarding in Vonage."""

        # Vonage uses NCCO for call control
        # This would be configured in the voice application
        return True

    async def send_sms(
        self,
        to_number: str,
        from_number: str,
        message: str
    ) -> bool:
        """Send SMS via Vonage."""

        try:
            response = self.client.sms.send_message({
                "from": from_number,
                "to": to_number,
                "text": message
            })

            return response["messages"][0]["status"] == "0"

        except Exception as e:
            logger.error(f"Vonage SMS failed: {e}")
            return False

    async def make_call(
        self,
        to_number: str,
        from_number: str,
        twiml_url: str
    ) -> str:
        """Make outbound call via Vonage."""

        try:
            response = self.client.voice.create_call({
                "to": [{"type": "phone", "number": to_number}],
                "from": {"type": "phone", "number": from_number},
                "answer_url": [twiml_url]
            })

            return response["uuid"]

        except Exception as e:
            logger.error(f"Vonage call failed: {e}")
            return ""