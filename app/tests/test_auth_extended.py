import requests
import json

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"

# --- Test Data ---
registration_data = {
    "business_name": "The Grand Cafe",
    "business_slug": "the-grand-cafe",
    "admin_email": "admin@thegrandcafe.com",
    "admin_password": "securepassword123",
    "admin_name": "John Doe"
}

# --- Helper Function ---
def print_test_result(success, test_name, response):
    if success:
        print(f"✅ {test_name} successful! (Status Code: {response.status_code})")
        try:
            print("Response Body:")
            print(json.dumps(response.json(), indent=2))
        except (json.JSONDecodeError, AttributeError):
            print("No JSON body in response.")
    else:
        print(f"❌ {test_name} failed as expected! (Status Code: {response.status_code})")
        try:
            print("Response Body:")
            print(json.dumps(response.json(), indent=2))
        except (json.JSONDecodeError, AttributeError):
            print("No JSON body in response.")
    print("\n" + "="*40 + "\n")


def run_tests():
    """Runs the extended authentication tests."""
    print("🚀 Starting Extended Authentication Tests...\n")

    # --- Test 1: Access a Protected Route ---
    # First, let's get a token by logging in.
    print("--- Logging in to get a token for protected route test ---")
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": registration_data["admin_email"], "password": registration_data["admin_password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        login_response.raise_for_status()
        access_token = login_response.json().get("access_token")
        print("✅ Successfully obtained token.\n")
    except requests.exceptions.RequestException as err:
        print(f"❌ Could not log in to get a token. Error: {err}")
        return

    print("--- Test 1: Accessing a protected route with a valid token ---")
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/test-token", headers=headers)
        response.raise_for_status()
        print_test_result(True, "Protected route access", response)
    except requests.exceptions.HTTPError as http_err:
        print_test_result(False, "Protected route access", http_err.response)

    # --- Test 2: Attempt Duplicate Registration ---
    print("--- Test 2: Attempting to register the same business again ---")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=registration_data)
        # We expect this to fail with a 409 Conflict error
        print_test_result(response.status_code != 409, "Duplicate registration", response)
    except requests.exceptions.RequestException as err:
        print(f"❌ An error occurred: {err}")

    # --- Test 3: Attempt Login with Invalid Password ---
    print("--- Test 3: Attempting to log in with an invalid password ---")
    invalid_login_data = {"username": registration_data["admin_email"], "password": "wrongpassword"}
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=invalid_login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # We expect this to fail with a 401 Unauthorized error
        print_test_result(response.status_code != 401, "Invalid password login", response)
    except requests.exceptions.RequestException as err:
        print(f"❌ An error occurred: {err}")


if __name__ == "__main__":
    run_tests()