import requests
import json

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000"
# It's good practice to use clear, descriptive user credentials for tests
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
        # Pretty-print the JSON response
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except (json.JSONDecodeError, AttributeError, TypeError):
        # Handle cases where response is not JSON or not a response object
        print(f"Response Content: {response.text if hasattr(response, 'text') else 'N/A'}")
    print("\n" + "="*40 + "\n")

def get_auth_token_and_business_id():
    """Logs in and retrieves the auth token and business ID for subsequent tests."""
    print_test_header("Step 0: Authentication")
    try:
        # Use a `data` parameter for form data, not `json`
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=LOGIN_DATA,
            # The content-type for OAuth2PasswordRequestForm should be application/x-www-form-urlencoded
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()  # This will raise an exception for 4xx/5xx errors
        
        token = response.json().get("access_token")
        headers_with_token = {"Authorization": f"Bearer {token}"}
        
        # Test the token to get user/business info
        user_info_resp = requests.post(f"{BASE_URL}/api/v1/auth/test-token", headers=headers_with_token)
        user_info_resp.raise_for_status()
        
        business_id = user_info_resp.json().get("business_id")
        
        if token and business_id:
            print("✅ Authentication: PASSED. Token and business ID obtained.\n")
            return token, business_id
        else:
            print("❌ Authentication: FAILED. Token or Business ID is missing in the response.\n")
            return None, None
            
    except requests.exceptions.RequestException as err:
        print(f"❌ Authentication: FAILED. Could not log in. Error: {err.response.text if err.response else err}\n")
        return None, None

def set_business_phone_config(business_id, token, config):
    """Helper to set the business's phone configuration for a test."""
    print(f"   Setting phone_config to: '{config}'...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # NOTE: This assumes you have an endpoint to update the business model directly.
    # If you don't, you would need to set this in the database for the test user.
    # For this example, we'll simulate the phone-setup call.
    phone_config_data = {"phone_config": config, "enable_whatsapp": True}
    response = requests.post(
        f"{BASE_URL}/api/v1/business/{business_id}/phone-setup",
        json=phone_config_data, headers=headers
    )
    # A 500 error here indicates a backend bug. The test should not proceed.
    if response.status_code == 500:
        print("   ❌ CRITICAL: Backend crashed while setting phone config. Fix the `PhoneManager` typo in `business.py` endpoint.")
        raise Exception("Backend crashed during test setup.")
    print("   Setup complete.")


# --- TEST SUITE ---

def run_tests():
    print("🚀 Starting Business and Phone Configuration Test Suite...\n")
    token, business_id = get_auth_token_and_business_id()
    if not token or not business_id:
        print("Aborting tests due to authentication failure.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Test 1: Phone Setup Endpoint
    # This was failing with a 500 error. The fix is in your backend code:
    # In `app/api/v1/endpoints/business.py`, change `PhoneManager` to `MultiProviderPhoneManager`.
    print_test_header("Test 1: Phone Setup")
    try:
        set_business_phone_config(business_id, token, "custom_only")
        # Check the status to confirm the change
        response = requests.get(f"{BASE_URL}/api/v1/business/{business_id}/phone-status", headers=headers)
        response.raise_for_status()
        print_test_result(True, "Phone Setup and Status Check", response)
    except Exception as err:
        print(f"   Test 1 failed unexpectedly: {err}")


    # Test 2: Human Transfer - "Sad Path" (Expected Failure)
    # This test CHECKS that the bouncer is working. It should fail for a universal plan.
    print_test_header("Test 2: Human Transfer (Universal Plan - Should be Denied)")
    try:
        # Arrange: Ensure the business has a 'universal_only' plan
        set_business_phone_config(business_id, token, "universal_only")
        
        # Act
        response = requests.post(
            f"{BASE_URL}/api/v1/business/{business_id}/transfer-to-human",
            json={"call_sid": "mock_call_sid_12345"},
            headers=headers
        )
        
        # Assert: The test PASSES if the status code is 400.
        is_correct_failure = response.status_code == 400
        print_test_result(is_correct_failure, "Deny transfer for universal plan", response)
        
    except Exception as err:
         print(f"   Test 2 failed unexpectedly: {err}")


    # Test 3: Human Transfer - "Happy Path" (Expected Success)
    # This test CHECKS that a business with the correct plan CAN use the feature.
    print_test_header("Test 3: Human Transfer (Custom Plan - Should Succeed)")
    try:
        # Arrange: Give the business a 'custom_only' plan
        set_business_phone_config(business_id, token, "custom_only")

        # Act
        response = requests.post(
            f"{BASE_URL}/api/v1/business/{business_id}/transfer-to-human",
            json={"call_sid": "mock_call_sid_12345"},
            headers=headers
        )

        # Assert: The test PASSES if the status code is 200.
        is_success = response.status_code == 200
        print_test_result(is_success, "Allow transfer for custom plan", response)
        
    except Exception as err:
        print(f"   Test 3 failed unexpectedly: {err}")


if __name__ == "__main__":
    run_tests()