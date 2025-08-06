"""Order management endpoints."""
from typing import Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.core.dependencies import get_current_business, get_current_user
from app.models import Order, OrderStatus, PaymentStatus, Business, User, MenuItem
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderStatusUpdate
)
from app.services.business.order_service import OrderService
from app.services.notifications.notification_service import NotificationService
from app.services.websocket.connection_manager import manager

router = APIRouter()


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[OrderStatus] = None,
    table_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """
    Get orders for the business with optional filters.
    
    Query parameters:
    - status: Filter by order status
    - table_id: Filter by table
    - limit: Maximum number of orders to return
    - offset: Number of orders to skip
    """
    query = db.query(Order).filter(Order.business_id == business.id)
    
    if status:
        query = query.filter(Order.status == status)
    
    if table_id:
        query = query.filter(Order.table_id == table_id)
    
    # Order by most recent first
    orders = query.order_by(Order.created_at.desc()).limit(limit).offset(offset).all()
    
    return orders


@router.get("/active", response_model=List[OrderResponse])
async def get_active_orders(
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Get all active orders (not completed or cancelled)."""
    active_statuses = [
        OrderStatus.PENDING,
        OrderStatus.CONFIRMED,
        OrderStatus.PREPARING,
        OrderStatus.READY
    ]
    
    orders = db.query(Order).filter(
        Order.business_id == business.id,
        Order.status.in_(active_statuses)
    ).order_by(Order.created_at).all()
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """Get specific order details."""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business),
    current_user: Optional[User] = None  # Optional for guest orders
) -> Any:
    """
    Create a new order.
    
    This endpoint:
    1. Validates menu items exist and are available
    2. Calculates pricing including tax
    3. Creates the order record
    4. Sends notifications to kitchen
    5. Broadcasts update via WebSocket
    """
    order_service = OrderService(db)
    
    try:
        # Create order using service
        order = order_service.create_order(
            business_id=business.id,
            order_data=order_data,
            customer_id=current_user.id if current_user else None
        )
        
        # Send WebSocket notification to kitchen dashboard
        await manager.broadcast_to_business(
            business_id=business.id,
            message={
                "type": "new_order",
                "order_id": order.id,
                "table_id": order.table_id,
                "items": order.items,
                "total": order.total_amount
            }
        )
        
        # Schedule background notifications
        background_tasks.add_task(
            NotificationService.send_order_confirmation,
            order_id=order.id
        )
        
        return order
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """
    Update order status.
    
    Status flow:
    PENDING -> CONFIRMED -> PREPARING -> READY -> COMPLETED
    Any status can go to CANCELLED
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update status
    order.status = status_update.status
    
    # Set estimated time for certain statuses
    if status_update.status == OrderStatus.PREPARING and status_update.estimated_time:
        order.estimated_ready_time = datetime.utcnow() + timedelta(
            minutes=status_update.estimated_time
        )
    
    db.commit()
    db.refresh(order)
    
    # Send WebSocket notification
    await manager.broadcast_to_business(
        business_id=business.id,
        message={
            "type": "order_status_update",
            "order_id": order.id,
            "status": order.status,
            "message": status_update.message
        }
    )
    
    # If order is ready, notify customer
    if order.status == OrderStatus.READY:
        await manager.send_to_session(
            session_id=order.session_id,
            message={
                "type": "order_ready",
                "order_id": order.id,
                "message": "Your order is ready!"
            }
        )
    
    return order


@router.post("/{order_id}/payment", response_model=OrderResponse)
async def process_payment(
    order_id: int,
    payment_method: PaymentMethod,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> Any:
    """
    Process payment for an order.
    
    For online payments, this will integrate with Stripe (Week 4).
    For now, it just updates the payment status.
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already paid"
        )
    
    # Update payment status
    order.payment_method = payment_method
    
    if payment_method == PaymentMethod.CASH:
        # Cash payment will be marked as paid when actually received
        order.payment_status = PaymentStatus.PENDING
    else:
        # For demo, mark online payments as paid immediately
        # In production, this would integrate with Stripe
        order.payment_status = PaymentStatus.PAID
        order.status = OrderStatus.CONFIRMED
    
    db.commit()
    db.refresh(order)
    
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    business: Business = Depends(get_current_business)
) -> None:
    """
    Cancel an order.
    
    Orders can only be cancelled if they're not already completed.
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.business_id == business.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status == OrderStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed order"
        )
    
    # Update status to cancelled
    order.status = OrderStatus.CANCELLED
    
    # Refund if already paid (in production, trigger Stripe refund)
    if order.payment_status == PaymentStatus.PAID:
        order.payment_status = PaymentStatus.REFUNDED
    
    db.commit()
    
    # Notify kitchen
    await manager.broadcast_to_business(
        business_id=business.id,
        message={
            "type": "order_cancelled",
            "order_id": order.id
        }
    )