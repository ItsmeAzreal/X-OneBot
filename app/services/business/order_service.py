"""Order processing business logic."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import Order, MenuItem, Table, OrderStatus, PaymentStatus
from app.schemas.order import OrderCreate, OrderItemSchema


class OrderService:
    """Service for managing orders."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_order(
        self,
        business_id: int,
        order_data: OrderCreate,
        customer_id: Optional[int] = None
    ) -> Order:
        """
        Create a new order with validation.
        
        Args:
            business_id: Business ID
            order_data: Order creation data
            customer_id: Optional customer ID
            
        Returns:
            Created order
            
        Raises:
            ValueError: If validation fails
        """
        # Validate items exist and are available
        validated_items = []
        subtotal = 0.0
        
        for item_data in order_data.items:
            menu_item = self.db.query(MenuItem).filter(
                MenuItem.id == item_data.item_id,
                MenuItem.business_id == business_id
            ).first()
            
            if not menu_item:
                raise ValueError(f"Menu item {item_data.item_id} not found")
            
            if not menu_item.is_available:
                raise ValueError(f"{menu_item.name} is not available")
            
            # Calculate item total with customizations
            item_total = self._calculate_item_price(
                menu_item,
                item_data.customizations,
                item_data.quantity
            )
            
            validated_items.append({
                "item_id": menu_item.id,
                "name": menu_item.name,
                "quantity": item_data.quantity,
                "unit_price": item_data.unit_price,
                "customizations": item_data.customizations,
                "subtotal": item_total
            })
            
            subtotal += item_total
        
        # Calculate tax (8% for demo)
        tax_rate = 0.08
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = round(subtotal + tax_amount, 2)
        
        # Create order
        order = Order(
            business_id=business_id,
            customer_id=customer_id,
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            customer_email=order_data.customer_email,
            table_id=order_data.table_id,
            order_type=order_data.order_type,
            items=validated_items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            tip_amount=0,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            payment_method=order_data.payment_method,
            special_instructions=order_data.special_instructions,
            session_id=str(uuid.uuid4())  # Generate session ID
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def _calculate_item_price(
        self,
        menu_item: MenuItem,
        customizations: Dict[str, Any],
        quantity: int
    ) -> float:
        """Calculate item price with customizations."""
        base_price = menu_item.base_price
        
        # Add customization costs
        for custom_type, selected_option in customizations.items():
            # Find matching customization in menu item
            for custom in menu_item.customizations:
                if custom.get("name") == custom_type:
                    options = custom.get("options", [])
                    price_diffs = custom.get("price_diff", [])
                    
                    if selected_option in options:
                        idx = options.index(selected_option)
                        if idx < len(price_diffs):
                            base_price += price_diffs[idx]
                    break
        
        return round(base_price * quantity, 2)
    
    def update_order_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        estimated_minutes: Optional[int] = None
    ) -> Order:
        """Update order status with validation."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            raise ValueError("Order not found")
        
        # Validate status transition
        if not self._is_valid_status_transition(order.status, new_status):
            raise ValueError(f"Invalid status transition from {order.status} to {new_status}")
        
        order.status = new_status
        
        # Set estimated time if provided
        if estimated_minutes:
            order.estimated_ready_time = datetime.utcnow() + timedelta(minutes=estimated_minutes)
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    def _is_valid_status_transition(
        self,
        current: OrderStatus,
        new: OrderStatus
    ) -> bool:
        """Check if status transition is valid."""
        # Can always cancel (except completed orders)
        if new == OrderStatus.CANCELLED:
            return current != OrderStatus.COMPLETED
        
        # Define valid transitions
        transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
            OrderStatus.COMPLETED: [],
            OrderStatus.CANCELLED: []
        }
        
        return new in transitions.get(current, [])