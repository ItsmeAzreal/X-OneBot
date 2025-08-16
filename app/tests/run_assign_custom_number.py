# File: run_assign_custom_number.py

import requests
import json

BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {"username": "admin@thegrandcafe.com", "password": "securepassword123"}

def get_auth_details():
    """Logs in to get the token and business ID."""
    try:
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", data=LOGIN_DATA)
        login_response.raise_for_status()
        access_token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info = requests.post(f"{BASE_URL}/api/v1/auth/test-token", headers=headers)
        business_id = user_info.json()["business_id"]
        return business_id, headers
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None

print("🚀 Starting Step 1: Assigning Custom Number...")
business_id, auth_headers = get_auth_details()

if business_id and auth_headers:
    # Set the phone config to 'custom_only' to get a dedicated number
    config_data = {"phone_config": "custom_only", "enable_whatsapp": True}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/business/{business_id}/phone-setup",
        json=config_data,
        headers=auth_headers
    )

    if response.status_code == 200:
        custom_number = response.json().get("custom_number")
        print(f"✅ SUCCESS! Assigned custom number: {custom_number}")
        print("Now we can test a direct call to this number.")
    else:
        print(f"❌ FAILED! Could not assign custom number. Status: {response.status_code}")