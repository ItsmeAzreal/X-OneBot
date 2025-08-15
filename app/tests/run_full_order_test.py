# File: run_full_order_test.py

import requests
import json
import random

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

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

def create_menu_item(headers):
    """Creates a category and a menu item, then returns the item's ID."""
    try:
        # Create a category first
        category_data = {"name": "Beverages"}
        cat_response = requests.post(f"{BASE_URL}/api/v1/menu/categories", json=category_data, headers=headers)
        cat_response.raise_for_status()
        category_id = cat_response.json().get("id")
        print(f"✅ Menu category 'Beverages' created with ID: {category_id}")

        # Now create the menu item
        item_data = {
            "name": "Cappuccino",
            "description": "Rich espresso with steamed milk foam",
            "base_price": 4.50,
            "category_id": category_id
        }
        item_response = requests.post(f"{BASE_URL}/api/v1/menu/items", json=item_data, headers=headers)
        item_response.raise_for_status()
        item_id = item_response.json().get("id")
        print(f"✅ Menu item 'Cappuccino' created with ID: {item_id}")
        return item_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create a menu item. Error: {e.response.text}")
        return None

def create_test_table(headers):
    """Creates a new table for the order."""
    try:
        table_number = f"Order-Test-Table-{random.randint(100, 999)}"
        table_data = {"table_number": table_number, "capacity": 2}
        response = requests.post(f"{BASE_URL}/api/v1/tables/", json=table_data, headers=headers)
        response.raise_for_status()
        table_id = response.json().get("id")
        print(f"✅ Test table '{table_number}' created with ID: {table_id}")
        return table_id
    except requests.exceptions.RequestException:
        return None

# --- Test Execution ---
print("🚀 Starting Full Order Placement Test (Phase 2.2)")
print("-" * 50)

auth_headers = get_auth_headers()
if auth_headers:
    menu_item_id = create_menu_item(auth_headers)
    table_id = create_test_table(auth_headers)

    if table_id and menu_item_id:
        try:
            order_data = {
                "table_id": table_id,
                "items": [{
                    "item_id": menu_item_id, # Use the ID of the item we just created
                    "name": "Cappuccino",
                    "quantity": 1,
                    "unit_price": 4.50,
                    "subtotal": 4.50
                }]
            }
            print(f"\nAttempting to place an order at Table ID: {table_id}...")
            response = requests.post(f"{BASE_URL}/api/v1/orders/", json=order_data, headers=auth_headers)
            response.raise_for_status()
            
            print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
            print("\nOrder created successfully:")
            print(json.dumps(response.json(), indent=2))

        except requests.exceptions.HTTPError as http_err:
            print(f"❌ FAILED! Server error: {http_err.response.status_code}")
            print(f"Response: {http_err.response.text}")

print("-" * 50)