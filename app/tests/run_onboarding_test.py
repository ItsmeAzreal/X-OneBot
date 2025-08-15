# File: run_onboarding_test.py

import requests
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

def get_auth_details():
    """Helper function to log in and get the token and business ID."""
    try:
        # First, log in to get the access token.
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=LOGIN_DATA)
        login_response.raise_for_status()
        access_token = login_response.json().get("access_token")

        # Now, use the token to ask the server "who am I?" to get the business_id.
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.post(f"{BASE_URL}/api/v1/auth/test-token", headers=headers)
        user_info_response.raise_for_status()
        business_id = user_info_response.json().get("business_id")

        if not access_token or not business_id:
            print("❌ Could not retrieve token or business ID.")
            return None, None, None
            
        print("✅ Login successful. Token and Business ID obtained.")
        return access_token, business_id, headers

    except requests.exceptions.RequestException as err:
        print(f"❌ Login failed during setup. Cannot proceed. Error: {err}")
        return None, None, None

# --- Test Execution ---
print("🚀 Starting Phase 1.3: Onboarding & Phone Setup Test")
print("-" * 50)

# 1. Get the necessary authentication details first.
access_token, business_id, auth_headers = get_auth_details()

# 2. Only proceed if we successfully logged in.
if access_token and business_id:
    try:
        # This is the data for our phone setup request.
        # We'll choose the simplest option: universal number only.
        phone_config_data = {
            "phone_config": "universal_only",
            "enable_whatsapp": False
        }

        print(f"\nSetting phone configuration for Business ID: {business_id}...")
        # Make the authenticated request to the business endpoint.
        response = requests.post(
            f"{BASE_URL}/api/v1/business/{business_id}/phone-setup",
            json=phone_config_data,
            headers=auth_headers  # Pass the authorization headers here!
        )

        response.raise_for_status()

        # A successful setup should return a 200 OK status.
        print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
        print("\nPhone configuration was successful:")
        print(json.dumps(response.json(), indent=2))

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
        print("\nServer Response:")
        print(json.dumps(http_err.response.json(), indent=2))
        
    except requests.exceptions.RequestException as err:
        print(f"❌ FAILED! Could not connect to the server during the setup request. Error: {err}")

print("-" * 50)