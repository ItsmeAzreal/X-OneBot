# File: run_order_update_test.py

import requests
import json
import random

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {"username": "admin@thegrandcafe.com", "password": "securepassword123"}

def get_auth_headers():
    """Logs in and returns the authorization headers."""
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=LOGIN_DATA)
        login_response.raise_for_status()
        token = login_response.json().get("access_token")
        print("✅ Login successful.")
        return {"Authorization": f"Bearer {token}"}
    except requests.exceptions.RequestException:
        return None

def setup_cafe_and_place_order(headers):
    """Creates all necessary items and places an order, returning the order ID."""
    try:
        # Create a menu item
        category_data = {"name": f"Category-{random.randint(100,999)}"}
        cat_response = requests.post(f"{BASE_URL}/api/v1/menu/categories", json=category_data, headers=headers)
        category_id = cat_response.json().get("id")
        item_data = {"name": "Cappuccino", "base_price": 4.50, "category_id": category_id}
        item_response = requests.post(f"{BASE_URL}/api/v1/menu/items", json=item_data, headers=headers)
        item_id = item_response.json().get("id")
        
        # Create a table
        table_data = {"table_number": f"Table-{random.randint(100,999)}", "capacity": 2}
        table_response = requests.post(f"{BASE_URL}/api/v1/tables/", json=table_data, headers=headers)
        table_id = table_response.json().get("id")
        
        # Place the order
        order_data = {"table_id": table_id, "items": [{"item_id": item_id, "name": "Cappuccino", "quantity": 1, "unit_price": 4.50, "subtotal": 4.50}]}
        order_response = requests.post(f"{BASE_URL}/api/v1/orders/", json=order_data, headers=headers)
        order_id = order_response.json().get("id")
        
        print(f"✅ Full setup complete. Placed new order with ID: {order_id}")
        return order_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Setup failed. Cannot test update. Error: {e}")
        return None

# --- Test Execution ---
print("🚀 Starting Phase 2.3: Order Status Update Test")
print("-" * 50)

auth_headers = get_auth_headers()
if auth_headers:
    # First, place a new order to get an ID to work with.
    order_id = setup_cafe_and_place_order(auth_headers)

    if order_id:
        try:
            # This is the data for our status update.
            status_update_data = {
                "status": "preparing",
                "message": "Your order is now being prepared by the kitchen.",
                "estimated_time": 15 # minutes
            }

            print(f"\nAttempting to update status for Order ID: {order_id}...")
            # Make the authenticated PUT request to the /orders/{order_id}/status endpoint.
            response = requests.put(
                f"{BASE_URL}/api/v1/orders/{order_id}/status",
                json=status_update_data,
                headers=auth_headers
            )

            response.raise_for_status()

            # A successful update returns a 200 OK status.
            print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
            print("\nOrder status updated successfully:")
            updated_status = response.json().get("status")
            print(f"  New Status: {updated_status.upper()}") # Should be 'PREPARING'

        except requests.exceptions.HTTPError as http_err:
            print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
            print(f"Response: {http_err.response.text}")
            
print("-" * 50)

#done--------------