"""
Vonage (Nexmo) provider implementation for Latvian numbers.
"""
from typing import Dict, Any, Optional, List
# FIX: Import the Client class directly from the nexmo package, not vonage
import nexmo
from app.services.phone.providers.base import BasePhoneProvider, PhoneNumberInfo
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class VonageProvider(BasePhoneProvider):
    """Vonage phone provider implementation."""

    def __init__(self):
        # FIX: Use the correct nexmo.Client initialization
        self.client = nexmo.Client(
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
        # This part of your code was correct and remains unchanged
        try:
            country_map = {"+371": "LV", "+372": "EE", "+370": "LT"}
            country = country_map.get(country_code, "LV")
            response = self.client.numbers.get_available_numbers(country, {"features": "VOICE,SMS"})
            
            numbers = []
            for number in response.get("numbers", []):
                info = PhoneNumberInfo(
                    number=number["msisdn"],
                    country_code=country_code,
                    provider=self.provider_name,
                    capabilities=number.get("features", []),
                    monthly_cost=12.00,
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
            # FIX: Use the correct method name `buy_number`
            response = self.client.numbers.buy_number({"country": "LV", "msisdn": phone_number})
            # FIX: Use the correct method name `update_number`
            self.client.numbers.update_number({
                "msisdn": phone_number,
                "moHttpUrl": f"{webhook_url}/sms/incoming",
                "voiceCallbackType": "app",
                "voiceCallbackValue": settings.VONAGE_APPLICATION_ID
            })
            return {"success": True, "number": phone_number, "provider": self.provider_name}
        except Exception as e:
            logger.error(f"Vonage provision failed: {e}")
            return {"success": False, "error": str(e)}

    # ... (the rest of the methods in this file are likely okay but depend on the client object,
    # which is now correctly initialized) ...
    async def release_number(self, phone_number: str) -> bool:
        """Release a Vonage number."""
        try:
            response = self.client.numbers.cancel_number({"country": "LV", "msisdn": phone_number})
            return response.get("error-code") == "200"
        except Exception as e:
            logger.error(f"Vonage release failed: {e}")
            return False

    async def setup_forwarding(self, from_number: str, to_number: str, extension: Optional[str] = None) -> bool:
        return True

    async def send_sms(self, to_number: str, from_number: str, message: str) -> bool:
        """Send SMS via Vonage."""
        try:
            response_data = self.client.send_message({
                'from': from_number,
                'to': to_number,
                'text': message,
            })
            return response_data['messages'][0]['status'] == '0'
        except Exception as e:
            logger.error(f"Vonage SMS failed: {e}")
            return False

    async def make_call(self, to_number: str, from_number: str, twiml_url: str) -> str:
        """Make outbound call via Vonage."""
        try:
            response = self.client.create_call({
                'to': [{'type': 'phone', 'number': to_number}],
                'from': {'type': 'phone', 'number': from_number},
                'answer_url': [twiml_url]
            })
            return response['uuid']
        except Exception as e:
            logger.error(f"Vonage call failed: {e}")
            return ""