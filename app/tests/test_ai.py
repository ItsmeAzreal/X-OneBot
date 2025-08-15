# app/tests/test_orders_api.py

import requests
import json
import random

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

# --- Import Helper Functions from your other test file ---
# This avoids code duplication. Make sure both test files are in the same directory.
from test_business import get_auth_token_and_business_id, print_test_header, print_test_result


# --- TEST SUITE ---

def run_order_tests():
    """Runs the entire order management test flow."""
    print("🚀 Starting Order Management API Test Suite...\n")
    
    token, business_id = get_auth_token_and_business_id()
    if not token or not business_id:
        print("Aborting tests due to authentication failure.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # We need a table to place an order, so let's create one first.
    # We'll use this table_id in the next test.
    table_id = None 

    # --- Test 1: Create a New Table ---
    print_test_header("Test 1: Create a New Table")
    try:
        # Use a random table number to avoid conflicts on re-runs
        table_number = f"API-Test-{random.randint(100, 999)}"
        table_data = {"table_number": table_number, "capacity": 2}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/tables/",
            json=table_data,
            headers=headers
        )
        response.raise_for_status()
        
        # Save the ID of the new table for the next step
        table_id = response.json().get("id")
        
        print_test_result(True, f"Create Table '{table_number}'", response)
        
    except requests.exceptions.RequestException as err:
        print_test_result(False, "Create Table", err.response)
        return # Stop if we can't create a table

    # --- Test 2: Create a New Order for the Table ---
    if not table_id:
        print("Skipping order creation test because table creation failed.")
        return
        
    order_id = None # We'll store the new order's ID here
    
    print_test_header("Test 2: Create a New Order")
    try:
        order_data = {
            "table_id": table_id,
            "items": [
                {
                    "item_id": 1, # Assuming an item with ID 1 exists from your seed data
                    "name": "Cappuccino",
                    "quantity": 2,
                    "unit_price": 4.50,
                    "subtotal": 9.00
                }
            ],
            "customer_name": "API Test Customer"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/orders/",
            json=order_data,
            headers=headers
        )
        response.raise_for_status()
        
        order_id = response.json().get("id")
        
        print_test_result(True, f"Create Order for Table ID {table_id}", response)
        
    except requests.exceptions.RequestException as err:
        print_test_result(False, "Create Order", err.response)
        return

    # --- Test 3: Update the Order Status ---
    if not order_id:
        print("Skipping order update test because order creation failed.")
        return
        
    print_test_header("Test 3: Update Order Status to 'Preparing'")
    try:
        status_update_data = {
            "order_id": order_id,
            "status": "preparing",
            "estimated_time": 15 # minutes
        }
        
        response = requests.put(
            f"{BASE_URL}/api/v1/orders/{order_id}/status",
            json=status_update_data,
            headers=headers
        )
        response.raise_for_status()
        
        print_test_result(True, f"Update Order ID {order_id}", response)
        
    except requests.exceptions.RequestException as err:
        print_test_result(False, "Update Order Status", err.response)


if __name__ == "__main__":
    run_order_tests()