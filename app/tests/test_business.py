import requests
import json

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000"
LOGIN_DATA = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}
HEADERS = {
    "Content-Type": "application/json"
}

# --- HELPER FUNCTIONS ---

def print_test_header(name):
    """Prints a clear header for each test scenario."""
    print(f"--- {name} ---")

def print_test_result(success, test_name, response):
    """Formats and prints the result of a test."""
    status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
    if success:
        print(f"✅ {test_name}: PASSED (Status Code: {status_code})")
    else:
        print(f"❌ {test_name}: FAILED (Status Code: {status_code})")
    
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except (json.JSONDecodeError, AttributeError, TypeError):
        print(f"Response Content: {response.text if hasattr(response, 'text') else 'N/A'}")
    print("\n" + "="*40 + "\n")

def get_auth_token_and_business_id():
    """Logs in and retrieves the auth token and business ID."""
    print_test_header("Step 0: Authentication")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=LOGIN_DATA,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        token = response.json().get("access_token")
        headers_with_token = {"Authorization": f"Bearer {token}"}
        
        user_info_resp = requests.post(f"{BASE_URL}/api/v1/auth/test-token", headers=headers_with_token)
        user_info_resp.raise_for_status()
        
        business_id = user_info_resp.json().get("business_id")
        
        if token and business_id:
            print("✅ Authentication: PASSED. Token and business ID obtained.\n")
            return token, business_id
        else:
            print("❌ Authentication: FAILED. Token or Business ID is missing.\n")
            return None, None
            
    except requests.exceptions.RequestException as err:
        print(f"❌ Authentication: FAILED. Error: {err.response.text if err.response else err}\n")
        return None, None

def set_business_phone_config(business_id, token, config):
    """Helper to set the business's phone configuration for a test."""
    print(f"   Setting phone_config to: '{config}'...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    phone_config_data = {"phone_config": config, "enable_whatsapp": True}
    response = requests.post(
        f"{BASE_URL}/api/v1/business/{business_id}/phone-setup",
        json=phone_config_data, headers=headers
    )
    if response.status_code >= 400:
        print(f"   ❌ CRITICAL: Could not set phone config. Status: {response.status_code}")
        print(f"   Response: {response.text}")
        raise Exception("Backend error during test setup.")
    print("   Setup complete.")

# --- TEST SUITE ---

def run_tests():
    print("🚀 Starting Business and Phone Configuration Test Suite...\n")
    token, business_id = get_auth_token_and_business_id()
    if not token or not business_id:
        print("Aborting tests due to authentication failure.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Test 1: Phone Setup and Status Check
    print_test_header("Test 1: Phone Setup and Status Check")
    try:
        set_business_phone_config(business_id, token, "custom_only")
        response = requests.get(f"{BASE_URL}/api/v1/business/{business_id}/phone-status", headers=headers)
        response.raise_for_status()
        print_test_result(True, "Phone Setup and Status Check", response)
    except Exception as err:
        print(f"   Test 1 failed unexpectedly: {err}")

    # Test 2: Human Transfer - "Sad Path" (Correctly Denied)
    print_test_header("Test 2: Human Transfer (Universal Plan - Should be Denied)")
    try:
        set_business_phone_config(business_id, token, "universal_only")
        response = requests.post(
            f"{BASE_URL}/api/v1/business/{business_id}/transfer-to-human",
            json={"call_sid": "mock_call_sid_12345"},
            headers=headers
        )
        is_correct_failure = response.status_code == 400
        print_test_result(is_correct_failure, "Deny transfer for universal plan", response)
    except Exception as err:
         print(f"   Test 2 failed unexpectedly: {err}")

    # Test 3: Human Transfer - "Happy Path" (Correctly Allowed)
    print_test_header("Test 3: Human Transfer (Custom Plan - Should Succeed)")
    try:
        set_business_phone_config(business_id, token, "custom_only")
        response = requests.post(
            f"{BASE_URL}/api/v1/business/{business_id}/transfer-to-human",
            json={"call_sid": "mock_call_sid_12345"},
            headers=headers
        )
        is_success = response.status_code == 200
        print_test_result(is_success, "Allow transfer for custom plan", response)
    except Exception as err:
        print(f"   Test 3 failed unexpectedly: {err}")

if __name__ == "__main__":
    run_tests()