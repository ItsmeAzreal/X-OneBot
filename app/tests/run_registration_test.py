# File: run_registration_test.py

import requests
import json

# --- Configuration ---
# The address where your FastAPI server is running.
BASE_URL = "http://127.0.0.1:8000"

# --- The "Payload" ---
# This is the data we will send to your API. It needs to match the structure
# you defined in your `RegisterBusinessRequest` schema.
registration_data = {
    "business_name": "The Grand Cafe",
    "business_slug": "the-grand-cafe",
    "admin_email": "admin@thegrandcafe.com",
    "admin_password": "securepassword123",
    "admin_name": "John Doe"
}

# --- Test Execution ---
print("🚀 Starting Phase 1.1: New Business Registration Test")
print("-" * 50)

try:
    # This is the core of the test. The `requests.post` function sends an
    # HTTP POST request to your API endpoint.
    print(f"Sending registration data for '{registration_data['business_name']}' to the server...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=registration_data
    )

    # This is a crucial helper. If the server returns an error code (like 404 or 500),
    # this line will automatically raise an exception and our `except` block below will catch it.
    response.raise_for_status()

    # If we get here, it means the request was successful (HTTP status 201).
    print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
    print("\nServer Response (this is your access token):")
    # We use json.dumps to "pretty-print" the JSON response from the server.
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.HTTPError as http_err:
    # This code runs only if `response.raise_for_status()` finds an error.
    print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
    print("This is expected if you run the test more than once, as the user already exists.")
    print("\nServer Response:")
    print(json.dumps(http_err.response.json(), indent=2))

except requests.exceptions.RequestException as err:
    # This code runs if the script couldn't connect to the server at all.
    print("❌ FAILED! Could not connect to the server.")
    print("Please make sure your `uvicorn app.main:app --reload` server is running.")
    print(f"Error details: {err}")

print("-" * 50)