"""Notification service for orders and updates."""
from typing import Optional
from sqlalchemy.orm import Session
from app.config.database import SessionLocal
from app.models import Order, Business, User
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handle various notification types."""
    
    @staticmethod
    async def send_order_confirmation(order_id: int):
        """Send order confirmation to customer."""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return
            
            # Log for now - Week 4 will add actual SMS/Email
            logger.info(f"Order #{order.id} confirmed for {order.customer_name}")
            
            # In Week 4, this will:
            # 1. Send SMS via Twilio
            # 2. Send Email via SendGrid
            # 3. Send WhatsApp message
            
        finally:
            db.close()
    
    @staticmethod
    async def send_order_ready_notification(order_id: int):
        """Notify customer that order is ready."""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return
            
            logger.info(f"Order #{order.id} is ready for pickup")
            
            # Week 4 will add actual notifications
            
        finally:
            db.close()
    
    @staticmethod
    async def send_kitchen_alert(order_id: int):
        """Alert kitchen of new order."""
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                return
            
            logger.info(f"New order #{order.id} sent to kitchen")
            
            # This will integrate with kitchen display system
            
        finally:
            db.close()