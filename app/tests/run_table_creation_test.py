# File: run_table_creation_test.py

import requests
import json
import random

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

def get_auth_token():
    """Helper function to log in and return the access token."""
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=LOGIN_DATA)
        login_response.raise_for_status()
        token = login_response.json().get("access_token")
        print("✅ Login successful. Token obtained.")
        return token
    except requests.exceptions.RequestException as err:
        print(f"❌ Login failed during setup. Cannot proceed. Error: {err}")
        return None

# --- Test Execution ---
print("🚀 Starting Phase 2.1: Table & QR Code Management Test")
print("-" * 50)

access_token = get_auth_token()

if access_token:
    try:
        # We need to send the token to prove we are authorized to create a table.
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # The data for our new table.
        # We use a random number to avoid errors if we run the test multiple times.
        table_number = f"Test-Table-{random.randint(100, 999)}"
        table_data = {
            "table_number": table_number,
            "capacity": 4
        }

        print(f"\nAttempting to create a new table: '{table_number}'...")
        # Make the authenticated POST request to the /tables endpoint.
        response = requests.post(
            f"{BASE_URL}/api/v1/tables/",
            json=table_data,
            headers=auth_headers
        )

        response.raise_for_status()

        # A successful creation returns a 201 Created status.
        print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
        print("\nTable created successfully:")
        print(json.dumps(response.json(), indent=2))

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
        print("\nServer Response:")
        print(json.dumps(http_err.response.json(), indent=2))
        
    except requests.exceptions.RequestException as err:
        print(f"❌ FAILED! Could not connect to the server during the table creation request. Error: {err}")

print("-" * 50)

#DONE--------------