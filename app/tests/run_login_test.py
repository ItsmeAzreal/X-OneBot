# File: run_login_test.py

import requests
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"

# --- The "Payload" ---
# This data must match the user you created in the registration test.
# The login endpoint expects 'username' and 'password' fields.
login_data = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

# --- Test Execution ---
print("🚀 Starting Phase 1.2: Admin Login Test")
print("-" * 50)

try:
    # We send the login data to the /login endpoint.
    # Note: The API expects the data in a specific format called 'x-www-form-urlencoded',
    # so we pass it as `data=` instead of `json=`. The requests library handles the formatting.
    print(f"Attempting to log in as '{login_data['username']}'...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data=login_data
    )

    # Check for any HTTP errors.
    response.raise_for_status()

    # A successful login returns a 200 OK status.
    print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
    print("\nLogin successful! You received a new access token:")
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.HTTPError as http_err:
    # If login fails (e.g., wrong password), we'll end up here.
    print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
    print("Please check that the username and password match the registration test.")
    print("\nServer Response:")
    print(json.dumps(http_err.response.json(), indent=2))

except requests.exceptions.RequestException as err:
    # This runs if the script can't connect to the server.
    print("❌ FAILED! Could not connect to the server.")
    print("Is your `uvicorn` server still running?")
    print(f"Error details: {err}")

print("-" * 50)

#DONE----------