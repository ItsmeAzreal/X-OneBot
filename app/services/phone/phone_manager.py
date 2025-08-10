"""
Phone Number Management Service.
Handles provisioning and management of universal and custom numbers.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from twilio.rest import Client
from app.models import Business, PhoneNumber, NumberStatus, NumberProvider, PhoneNumberType
from app.config.settings import settings
import logging
import random

logger = logging.getLogger(__name__)


class PhoneManager:
    """
    Manages phone number provisioning and routing.
    
    Features:
    1. Universal number registration
    2. Custom number provisioning
    3. WhatsApp integration
    4. Usage tracking
    5. Number pool management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.twilio_client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Universal number configuration
        self.universal_number = settings.UNIVERSAL_BOT_NUMBER
        
        # Available Latvian number prefixes
        self.latvian_prefixes = [
            "+37120", "+37121", "+37122", "+37123",
            "+37124", "+37125", "+37126", "+37127",
            "+37128", "+37129"
        ]
    
    def onboard_business(
        self,
        business_id: int,
        phone_config: PhoneNumberType,
        wants_whatsapp: bool = False
    ) -> Dict[str, Any]:
        """
        Onboard a business with phone configuration.
        
        Args:
            business_id: Business to onboard
            phone_config: Phone configuration type
            wants_whatsapp: Whether to enable WhatsApp
            
        Returns:
            Provisioning details
        """
        
        business = self.db.query(Business).filter(
            Business.id == business_id
        ).first()
        
        if not business:
            raise ValueError(f"Business {business_id} not found")
        
        result = {
            "business_id": business_id,
            "universal_access": False,
            "custom_number": None,
            "whatsapp_enabled": False,
            "monthly_cost": 0
        }
        
        # Update business phone configuration
        business.phone_config = phone_config
        
        # Handle based on configuration type
        if phone_config == PhoneNumberType.UNIVERSAL_ONLY:
            # Free tier - only universal access
            result["universal_access"] = True
            self._register_on_universal(business)
            
        elif phone_config == PhoneNumberType.CUSTOM_ONLY:
            # Custom number only
            custom_number = self._provision_custom_number(business)
            result["custom_number"] = custom_number.phone_number
            result["monthly_cost"] = 15.00  # Base cost for custom number
            
            if wants_whatsapp:
                self._setup_whatsapp(business, custom_number)
                result["whatsapp_enabled"] = True
                result["monthly_cost"] += 10.00  # WhatsApp addon
                
        elif phone_config == PhoneNumberType.BOTH:
            # Both universal and custom
            result["universal_access"] = True
            self._register_on_universal(business)
            
            custom_number = self._provision_custom_number(business)
            result["custom_number"] = custom_number.phone_number
            result["monthly_cost"] = 20.00  # Premium pricing
            
            if wants_whatsapp:
                self._setup_whatsapp(business, custom_number)
                result["whatsapp_enabled"] = True
                result["monthly_cost"] += 10.00
        
        # Update business with pricing
        business.custom_number_monthly_cost = result["monthly_cost"]
        
        # Set phone features
        business.phone_features = {
            "voice_enabled": True,
            "whatsapp_enabled": wants_whatsapp,
            "sms_enabled": True,
            "transfer_to_human": phone_config != PhoneNumberType.UNIVERSAL_ONLY,
            "voice_personality": business.branding_config.get("bot_personality", "friendly"),
            "monthly_minutes_limit": 1000 if phone_config == PhoneNumberType.UNIVERSAL_ONLY else 5000
        }
        
        self.db.commit()
        
        logger.info(f"Business {business.name} onboarded with {phone_config} configuration")
        
        return result
    
    def _register_on_universal(self, business: Business):
        """Register business on universal number."""
        
        # Check if already has universal access
        existing = self.db.query(PhoneNumber).filter(
            PhoneNumber.business_id == business.id,
            PhoneNumber.is_universal == True
        ).first()
        
        if existing:
            return existing
        
        # Create universal number registration
        universal_registration = PhoneNumber(
            business_id=business.id,
            phone_number=self.universal_number,
            country_code="+1",
            provider=NumberProvider.BOTH,
            is_universal=True,
            is_primary=business.phone_config == PhoneNumberType.UNIVERSAL_ONLY,
            status=NumberStatus.ACTIVE,
            capabilities={
                "voice": True,
                "sms": True,
                "whatsapp": True
            },
            activated_at=datetime.utcnow()
        )
        
        self.db.add(universal_registration)
        self.db.commit()
        
        logger.info(f"Business {business.name} registered on universal number")
        
        return universal_registration
    
    def _provision_custom_number(self, business: Business) -> PhoneNumber:
        """Provision a custom Latvian number for business."""
        
        try:
            # Search for available Latvian numbers
            available_numbers = self.twilio_client.available_phone_numbers("LV").local.list(
                limit=10,
                # capabilities=["voice", "sms"]
            )
            
            if not available_numbers:
                # Fallback to generating a mock number for testing
                logger.warning("No real numbers available, using mock number")
                number = self._generate_mock_latvian_number()
                sid = f"PN_MOCK_{business.id}"
            else:
                # Purchase the first available number
                selected = available_numbers[0]
                purchased = self.twilio_client.incoming_phone_numbers.create(
                    phone_number=selected.phone_number,
                    voice_url=f"{settings.API_URL}/api/v1/voice/incoming",
                    sms_url=f"{settings.API_URL}/api/v1/sms/incoming",
                    voice_method="POST",
                    sms_method="POST"
                )
                number = purchased.phone_number
                sid = purchased.sid
            
            # Create phone number record
            phone_record = PhoneNumber(
                business_id=business.id,
                phone_number=number,
                country_code="+371",
                provider=NumberProvider.TWILIO,
                twilio_sid=sid,
                is_universal=False,
                is_primary=True,
                status=NumberStatus.ACTIVE,
                capabilities={
                    "voice": True,
                    "sms": True,
                    "whatsapp": False
                },
                monthly_limit={
                    "voice_minutes": 5000,
                    "sms_count": 10000
                },
                activated_at=datetime.utcnow()
            )
            
            self.db.add(phone_record)
            
            # Update business with custom number
            business.custom_phone_number = number
            business.custom_phone_sid = sid
            
            self.db.commit()
            
            logger.info(f"Provisioned {number} for business {business.name}")
            
            return phone_record
            
        except Exception as e:
            logger.error(f"Failed to provision number: {e}")
            # Fallback to mock number
            return self._create_mock_number(business)
    
    def _setup_whatsapp(self, business: Business, phone_number: PhoneNumber):
        """Setup WhatsApp Business for custom number."""
        
        # In production, this would:
        # 1. Register number with WhatsApp Business API
        # 2. Configure webhooks
        # 3. Set up message templates
        
        # For now, update the record
        phone_number.capabilities["whatsapp"] = True
        phone_number.whatsapp_id = f"WA_{phone_number.phone_number}"
        
        business.custom_whatsapp_number = phone_number.phone_number
        business.phone_features["whatsapp_enabled"] = True
        
        self.db.commit()
        
        logger.info(f"WhatsApp enabled for {phone_number.phone_number}")
    
    def _generate_mock_latvian_number(self) -> str:
        """Generate a mock Latvian phone number for testing."""
        prefix = random.choice(self.latvian_prefixes)
        suffix = "".join([str(random.randint(0, 9)) for _ in range(6)])
        return f"{prefix}{suffix}"
    
    def _create_mock_number(self, business: Business) -> PhoneNumber:
        """Create a mock phone number record for testing."""
        
        mock_number = self._generate_mock_latvian_number()
        
        phone_record = PhoneNumber(
            business_id=business.id,
            phone_number=mock_number,
            country_code="+371",
            provider=NumberProvider.TWILIO,
            twilio_sid=f"MOCK_SID_{business.id}",
            is_universal=False,
            is_primary=True,
            status=NumberStatus.ACTIVE,
            capabilities={
                "voice": True,
                "sms": True,
                "whatsapp": False
            },
            activated_at=datetime.utcnow()
        )
        
        self.db.add(phone_record)
        business.custom_phone_number = mock_number
        self.db.commit()
        
        return phone_record
    
    def route_incoming_call(
        self,
        to_number: str,
        from_number: str
    ) -> Optional[int]:
        """
        Route incoming call to appropriate business.
        
        Args:
            to_number: Number that was called
            from_number: Caller's number
            
        Returns:
            Business ID if found, None otherwise
        """
        
        # Check if it's the universal number
        if to_number == self.universal_number:
            # Universal number - will need to determine business
            # This is handled by the universal bot
            return None
        
        # Check for custom number
        phone_record = self.db.query(PhoneNumber).filter(
            PhoneNumber.phone_number == to_number,
            PhoneNumber.is_universal == False,
            PhoneNumber.status == NumberStatus.ACTIVE
        ).first()
        
        if phone_record:
            return phone_record.business_id
        
        return None
    
    def transfer_to_human(
        self,
        business_id: int,
        call_sid: str
    ) -> bool:
        """
        Transfer call to human staff.
        
        Args:
            business_id: Business ID
            call_sid: Twilio call SID
            
        Returns:
            Success status
        """
        
        business = self.db.query(Business).filter(
            Business.id == business_id
        ).first()
        
        if not business:
            return False
        
        # Check if human transfer is enabled
        if not business.phone_features.get("transfer_to_human"):
            logger.warning(f"Human transfer not enabled for business {business_id}")
            return False
        
        # Get staff phone number from contact info
        staff_number = business.contact_info.get("staff_phone")
        
        if not staff_number:
            logger.error(f"No staff number configured for business {business_id}")
            return False
        
        try:
            # Update the call to transfer
            call = self.twilio_client.calls(call_sid).update(
                twiml=f'''
                <Response>
                    <Say>Transferring you to our staff. Please hold.</Say>
                    <Dial>{staff_number}</Dial>
                </Response>
                '''
            )
            
            logger.info(f"Call {call_sid} transferred to {staff_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer call: {e}")
            return False
    
    def check_usage_limits(self, business_id: int) -> Dict[str, Any]:
        """Check if business has exceeded usage limits."""
        
        business = self.db.query(Business).filter(
            Business.id == business_id
        ).first()
        
        if not business:
            return {"error": "Business not found"}
        
        usage = business.phone_usage or {}
        features = business.phone_features or {}
        
        # Get monthly limits based on plan
        if business.phone_config == PhoneNumberType.UNIVERSAL_ONLY:
            limits = {
                "voice_minutes": 100,
                "sms_count": 500,
                "whatsapp_messages": 1000
            }
        else:
            limits = {
                "voice_minutes": features.get("monthly_minutes_limit", 5000),
                "sms_count": 10000,
                "whatsapp_messages": 50000
            }
        
        # Check each limit
        return {
            "voice": {
                "used": usage.get("voice_minutes_used", 0),
                "limit": limits["voice_minutes"],
                "exceeded": usage.get("voice_minutes_used", 0) >= limits["voice_minutes"]
            },
            "sms": {
                "used": usage.get("sms_sent", 0),
                "limit": limits["sms_count"],
                "exceeded": usage.get("sms_sent", 0) >= limits["sms_count"]
            },
            "whatsapp": {
                "used": usage.get("whatsapp_messages", 0),
                "limit": limits["whatsapp_messages"],
                "exceeded": usage.get("whatsapp_messages", 0) >= limits["whatsapp_messages"]
            }
        }