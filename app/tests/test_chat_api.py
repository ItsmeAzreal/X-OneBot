# app/tests/test_chat_api.py

import requests
import json
import uuid

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000"

# --- HELPER FUNCTIONS ---
# To keep this script self-contained, we'll include a simple print helper.
def print_test_header(name):
    print(f"--- {name} ---")

def print_test_result(success, test_name, response):
    status_code = response.status_code if hasattr(response, 'status_code') else 'N/A'
    if success:
        print(f"✅ {test_name}: PASSED (Status Code: {status_code})")
    else:
        print(f"❌ {test_name}: FAILED (Status Code: {status_code})")
    
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except (json.JSONDecodeError, AttributeError):
        print(f"Response Content: {response.text if hasattr(response, 'text') else 'N/A'}")
    print("\n" + "="*40 + "\n")


# --- TEST SUITE ---

def run_chat_tests():
    """Runs the AI chat system test flow."""
    print("🚀 Starting AI Chat API Test Suite...\n")
    
    # For this test, we don't need to be logged in, as the chat is for guests.
    # We will simulate a new customer starting a conversation.
    headers = {"Content-Type": "application/json"}
    
    # --- Test 1: Send a simple greeting ---
    print_test_header("Test 1: Send a Greeting to the Universal Bot")
    try:
        # We generate a unique session_id for this conversation test
        session_id = f"test-session-{uuid.uuid4()}"
        
        chat_data = {
            "message": "hello",
            "session_id": session_id,
            "table_id": None # We are not at a specific table yet
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json=chat_data,
            headers=headers
        )
        response.raise_for_status() # Check for HTTP errors
        
        # Assert: The test PASSES if we get a 200 OK and a response message.
        response_json = response.json()
        is_success = "message" in response_json and len(response_json["message"]) > 0
        
        print_test_result(is_success, "Send Greeting", response)
        
    except requests.exceptions.RequestException as err:
        print_test_result(False, "Send Greeting", err.response if err.response else err)
        return

    # --- Test 2: Ask for the menu ---
    print_test_header("Test 2: Ask for the Menu")
    try:
        # Continue the same conversation using the session_id from the first test
        chat_data = {
            "message": "show me the menu",
            "session_id": session_id,
            "table_id": None
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/message",
            json=chat_data,
            headers=headers
        )
        response.raise_for_status()
        
        response_json = response.json()
        is_success = "message" in response_json and "menu" in response_json["message"].lower()
        
        print_test_result(is_success, "Ask for Menu", response)
        
    except requests.exceptions.RequestException as err:
        print_test_result(False, "Ask for Menu", err.response if err.response else err)


if __name__ == "__main__":
    run_chat_tests()