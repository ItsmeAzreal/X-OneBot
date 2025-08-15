"""
Main phone manager that orchestrates multiple providers.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.services.phone.providers.base import BasePhoneProvider, PhoneNumberInfo
from app.services.phone.providers.twilio_provider import TwilioProvider
from app.services.phone.providers.vonage_provider import VonageProvider
from app.services.phone.providers.existing_number_manager import ExistingNumberManager
from app.models import Business, PhoneNumber, PhoneNumberType
import logging

logger = logging.getLogger(__name__)


class MultiProviderPhoneManager:
    """
    Manages phone numbers across multiple providers.
    This is the main interface for phone operations.
    """

    def __init__(self, db: Session):
        self.db = db

        # Initialize providers
        self.providers: Dict[str, BasePhoneProvider] = {
            "twilio": TwilioProvider(),
            "vonage": VonageProvider(),
        }

        # Existing number manager
        self.existing_manager = ExistingNumberManager(db)

        # Provider priority for different regions
        self.regional_priority = {
            "+371": ["vonage", "twilio"],  # Latvia - Vonage first
            "+372": ["twilio", "vonage"],  # Estonia - Twilio first
            "+370": ["vonage", "twilio"],  # Lithuania
            "+1": ["twilio"],             # USA - Twilio only
        }

    async def search_numbers(
        self,
        country_code: str,
        preferred_provider: Optional[str] = None
    ) -> List[PhoneNumberInfo]:
        """
        Search for available numbers across all providers.

        Args:
            country_code: Country code to search
            preferred_provider: Preferred provider name

        Returns:
            List of available numbers from all providers
        """

        all_numbers = []

        # Get provider order
        if preferred_provider and preferred_provider in self.providers:
            provider_order = [preferred_provider] + [
                p for p in self.providers.keys() if p != preferred_provider
            ]
        else:
            provider_order = self.regional_priority.get(
                country_code,
                list(self.providers.keys())
            )

        # Search each provider
        for provider_name in provider_order:
            if provider_name in self.providers:
                provider = self.providers[provider_name]

                try:
                    numbers = await provider.search_available_numbers(
                        country_code=country_code
                    )
                    all_numbers.extend(numbers)

                    # If we found numbers, maybe stop searching
                    if numbers and len(all_numbers) >= 5:
                        break

                except Exception as e:
                    logger.error(f"Provider {provider_name} search failed: {e}")
                    continue

        return all_numbers

    async def provision_number(
        self,
        business_id: int,
        phone_number_info: PhoneNumberInfo
    ) -> Dict[str, Any]:
        """
        Provision a number for a business.

        Args:
            business_id: Business to provision for
            phone_number_info: Number information from search

        Returns:
            Provisioning result
        """

        provider = self.providers.get(phone_number_info.provider)

        if not provider:
            return {"success": False, "error": "Provider not found"}

        # Provision with provider
        result = await provider.provision_number(
            phone_number=phone_number_info.number,
            webhook_url=settings.API_URL
        )

        if result["success"]:
            # Create phone record
            phone_record = PhoneNumber(
                business_id=business_id,
                phone_number=phone_number_info.number,
                country_code=phone_number_info.country_code,
                provider=phone_number_info.provider,
                twilio_sid=result.get("sid"),
                is_universal=False,
                is_primary=True,
                status="active",
                capabilities=phone_number_info.capabilities,
                activated_at=datetime.utcnow()
            )

            self.db.add(phone_record)

            # Update business
            business = self.db.query(Business).filter(
                Business.id == business_id
            ).first()

            if business:
                business.custom_phone_number = phone_number_info.number
                business.custom_number_monthly_cost = phone_number_info.monthly_cost

            self.db.commit()

            logger.info(f"Provisioned {phone_number_info.number} for business {business_id}")

        return result

    def setup_existing_number(
        self,
        business_id: int,
        existing_number: str
    ) -> Dict[str, Any]:
        """
        Setup café's existing number.

        Args:
            business_id: Business ID
            existing_number: Their existing phone number

        Returns:
            Setup instructions and configuration
        """

        return self.existing_manager.setup_existing_number(
            business_id=business_id,
            existing_number=existing_number
        )

    def verify_existing_number(
        self,
        business_id: int,
        phone_id: int,
        verification_code: str
    ) -> bool:
        """Verify existing number setup."""

        return self.existing_manager.verify_existing_number(
            business_id=business_id,
            phone_id=phone_id,
            verification_code=verification_code
        )

    async def route_incoming_call(
        self,
        to_number: str,
        from_number: str,
        extension: Optional[str] = None
    ) -> Optional[int]:
        """
        Route incoming call to appropriate business.

        Args:
            to_number: Number that was called
            from_number: Caller's number
            extension: Extension code (for forwarded calls)

        Returns:
            Business ID if found
        """

        # Check if it's a forwarded call with extension
        if extension:
            phone_record = self.db.query(PhoneNumber).filter(
                PhoneNumber.metadata["extension_code"].astext == extension,
                PhoneNumber.status == "active"
            ).first()

            if phone_record:
                return phone_record.business_id

        # Check direct number
        phone_record = self.db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == to_number,
            PhoneNumber.status == "active"
        ).first()

        if phone_record:
            return phone_record.business_id

        # Check if universal number
        if to_number == settings.UNIVERSAL_BOT_NUMBER:
            return None  # Will be handled by universal bot

        return None