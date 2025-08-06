"""Tests for order processing."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models import Business, User, MenuItem, Order, OrderStatus
from app.config.database import get_db
from app.core.security import get_password_hash

client = TestClient(app)


@pytest.fixture
def test_db():
    """Create test database session."""
    # This would use a test database in practice
    pass


@pytest.fixture
def test_business(test_db):
    """Create test business."""
    business = Business(
        name="Test Cafe",
        slug="test-cafe",
        subscription_plan="pro"
    )
    test_db.add(business)
    test_db.commit()
    return business


@pytest.fixture
def test_user(test_db, test_business):
    """Create test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpass"),
        business_id=test_business.id,
        role="owner"
    )
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "testpass"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_order(test_db, test_business, auth_headers):
    """Test order creation."""
    # Create test menu item
    item = MenuItem(
        business_id=test_business.id,
        name="Test Coffee",
        base_price=5.00,
        is_available=True
    )
    test_db.add(item)
    test_db.commit()
    
    # Create order
    order_data = {
        "items": [
            {
                "item_id": item.id,
                "name": item.name,
                "quantity": 2,
                "unit_price": item.base_price,
                "customizations": {},
                "subtotal": 10.00
            }
        ],
        "table_id": 1,
        "payment_method": "cash"
    }
    
    response = client.post(
        "/api/v1/orders/",
        json=order_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["subtotal"] == 10.00
    assert data["status"] == "pending"


def test_update_order_status(test_db, test_business, auth_headers):
    """Test order status update."""
    # Create test order
    order = Order(
        business_id=test_business.id,
        items=[],
        subtotal=10.00,
        total_amount=10.80,
        status=OrderStatus.PENDING
    )
    test_db.add(order)
    test_db.commit()
    
    # Update status
    response = client.put(
        f"/api/v1/orders/{order.id}/status",
        json={"status": "confirmed"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


def test_get_active_orders(test_db, test_business, auth_headers):
    """Test getting active orders."""
    # Create test orders
    for i in range(3):
        order = Order(
            business_id=test_business.id,
            items=[],
            subtotal=10.00,
            total_amount=10.80,
            status=OrderStatus.PENDING if i < 2 else OrderStatus.COMPLETED
        )
        test_db.add(order)
    test_db.commit()
    
    # Get active orders
    response = client.get(
        "/api/v1/orders/active",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Only pending orders


def test_websocket_connection():
    """Test WebSocket connection."""
    from fastapi.testclient import TestClient
    
    with client.websocket_connect("/api/v1/chat/ws/test-session") as websocket:
        # Should receive connection message
        data = websocket.receive_json()
        assert data["type"] == "connected"
        
        # Send message
        websocket.send_json({"message": "Hello"})
        
        # Receive response
        response = websocket.receive_json()
        assert response["type"] == "message"
        assert "message" in response# XoneBot Week 2: Order Processing, WebSockets & Chat Foundation



