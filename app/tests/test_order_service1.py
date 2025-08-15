# # app/tests/test_order_service.py

# import pytest
# from app.services.business.order_service import OrderService
# from app.models import MenuItem
# from app.schemas.order import OrderCreate, OrderItemSchema # Import schemas

# # ... (keep your existing fixtures) ...

# def test_create_order_with_invalid_item_id(mocker): # `mocker` is a fixture from pytest-mock
#     """
#     Tests that creating an order with a non-existent menu item raises a ValueError.
#     """
#     # Arrange
#     # 1. Mock the database dependency
#     mock_db_session = mocker.MagicMock()
#     # 2. Configure the mock: when `db.query(MenuItem).filter().first()` is called,
#     #    it should return `None`, simulating that the item was not found.
#     mock_db_session.query.return_value.filter.return_value.first.return_value = None

#     # 3. Create the OrderService with our mock database
#     order_service = OrderService(db=mock_db_session)

#     # 4. Prepare the order data with an item_id we know is invalid
#     invalid_order_data = OrderCreate(
#         items=[OrderItemSchema(item_id=999, name="Fake Item", quantity=1, unit_price=10.0, subtotal=10.0)],
#         # ... add any other required fields for OrderCreate
#     )
#     business_id = 1

#     # Act & Assert
#     # We expect a ValueError to be raised. `pytest.raises` is a context manager
#     # that will "catch" the expected exception. If the exception is raised,
#     # the test passes. If it's not raised, the test fails.
#     with pytest.raises(ValueError, match="Menu item 999 not found"):
#         order_service.create_order(business_id=business_id, order_data=invalid_order_data)