# File: run_order_placement_test.py

import requests
import json
import random

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

def get_auth_token_and_headers():
    """Logs in and returns the token and authorization headers."""
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=LOGIN_DATA)
        login_response.raise_for_status()
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login successful. Token obtained.")
        return headers
    except requests.exceptions.RequestException as err:
        print(f"❌ Login failed. Cannot proceed. Error: {err}")
        return None

def create_test_table(headers):
    """Creates a new table to ensure the test has a valid table_id."""
    try:
        table_number = f"Order-Test-Table-{random.randint(100, 999)}"
        table_data = {"table_number": table_number, "capacity": 2}
        response = requests.post(f"{BASE_URL}/api/v1/tables/", json=table_data, headers=headers)
        response.raise_for_status()
        table_id = response.json().get("id")
        print(f"✅ Test table '{table_number}' created with ID: {table_id}")
        return table_id
    except requests.exceptions.RequestException:
        print("❌ Failed to create a test table. Cannot place order.")
        return None

# --- Test Execution ---
print("🚀 Starting Phase 2.2: Order Placement Test")
print("-" * 50)

auth_headers = get_auth_token_and_headers()

if auth_headers:
    # First, create a table to order from.
    table_id = create_test_table(auth_headers)

    if table_id:
        try:
            # This is the data for our new order.
            # We assume a menu item with id=1 exists from your seed script.
            order_data = {
                "table_id": table_id,
                "items": [
                    {
                        "item_id": 1,
                        "name": "Cappuccino",
                        "quantity": 2,
                        "unit_price": 4.50,
                        "customizations": {"size": "Large", "milk": "Oat"},
                        "subtotal": 9.00
                    }
                ],
                "customer_name": "Test Customer"
            }

            print(f"\nAttempting to place an order at Table ID: {table_id}...")
            # Make the authenticated POST request to the /orders endpoint.
            response = requests.post(
                f"{BASE_URL}/api/v1/orders/",
                json=order_data,
                headers=auth_headers
            )

            response.raise_for_status()

            # A successful order creation returns a 201 Created status.
            print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
            print("\nOrder created successfully:")
            print(json.dumps(response.json(), indent=2))

        except requests.exceptions.HTTPError as http_err:
            print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
            print("\nServer Response:")
            print(json.dumps(http_err.response.json(), indent=2))
        
        except requests.exceptions.RequestException as err:
            print(f"❌ FAILED! Could not connect to the server during the order request. Error: {err}")

print("-" * 50)