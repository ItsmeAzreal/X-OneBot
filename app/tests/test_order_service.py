# # tests/test_order_service.py

# import pytest
# from app.services.business.order_service import OrderService
# from app.models import MenuItem # You'll need to mock or create a dummy version of this

# # A fixture to create an instance of our service.
# # Pytest will automatically run this and pass the result to any test that needs it.
# @pytest.fixture
# def order_service():
#     # Since we are unit testing, we don't need a real database session.
#     # We can pass `None`.
#     return OrderService(db=None)

# # A dummy MenuItem object for testing purposes.
# # We don't need a real database record.
# @pytest.fixture
# def sample_menu_item():
#     return MenuItem(
#         base_price=10.0,
#         customizations=[
#             {
#                 "name": "Size",
#                 "options": ["Small", "Medium", "Large"],
#                 "price_diff": [0, 2.0, 4.0]
#             }
#         ]
#     )

# def test_calculate_item_price_no_customizations(order_service, sample_menu_item):
#     """
#     Tests the price calculation for a single item with no customizations.
#     """
#     # Arrange: Set up our inputs
#     menu_item = sample_menu_item
#     customizations = {}
#     quantity = 2

#     # Act: Call the method we want to test
#     total_price = order_service._calculate_item_price(menu_item, customizations, quantity)

#     # Assert: Check if the result is what we expect
#     assert total_price == 20.0

# def test_calculate_item_price_with_customizations(order_service, sample_menu_item):
#     """
#     Tests the price calculation with an added customization cost.
#     """
#     # Arrange
#     menu_item = sample_menu_item
#     customizations = {"Size": "Large"} # This should add $4.0
#     quantity = 1

#     # Act
#     total_price = order_service._calculate_item_price(menu_item, customizations, quantity)

#     # Assert (10.0 base + 4.0 customization) * 1 quantity
#     assert total_price == 14.0