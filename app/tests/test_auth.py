import requests
import json
import pytest

# --- Configuration ---
# If your application is running on a different address or port, change this URL.
BASE_URL = "http://127.0.0.1:8000"

# --- Test Data ---
registration_data = {
    "business_name": "The Grand Cafe",
    "business_slug": "the-grand-cafe",
    "admin_email": "admin@thegrandcafe.com",
    "admin_password": "securepassword123",
    "admin_name": "John Doe"
}

login_data = {
    "username": "admin@thegrandcafe.com",
    "password": "securepassword123"
}

def run_tests():
    """Runs the authentication tests."""
    print("🚀 Starting Authentication and Authorization Tests...\n")

    # --- Test 1: Register a New Business ---
    print("--- Test 1: Registering a new business ---")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print(f"✅ Registration successful! (Status Code: {response.status_code})")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Registration failed! (Status Code: {http_err.response.status_code})")
        print(f"Error: {http_err}")
        try:
            print("Response Body:")
            print(json.dumps(http_err.response.json(), indent=2))
        except json.JSONDecodeError:
            print("Could not decode JSON from response.")
        return  # Stop if registration fails
    except requests.exceptions.RequestException as err:
        print(f"❌ An error occurred: {err}")
        return

    print("\n" + "="*40 + "\n")

    # --- Test 2: Login with Valid Credentials ---
    print("--- Test 2: Logging in with the new user ---")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        print(f"✅ Login successful! (Status Code: {response.status_code})")
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Login failed! (Status Code: {http_err.response.status_code})")
        print(f"Error: {http_err}")
        try:
            print("Response Body:")
            print(json.dumps(http_err.response.json(), indent=2))
        except json.JSONDecodeError:
            print("Could not decode JSON from response.")
    except requests.exceptions.RequestException as err:
        print(f"❌ An error occurred: {err}")


if __name__ == "__main__":
    run_tests()