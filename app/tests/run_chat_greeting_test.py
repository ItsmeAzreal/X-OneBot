# File: run_chat_greeting_test.py

import requests
import json
import uuid

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000"

# --- Test Execution ---
print("🚀 Starting Phase 3.1: Initial Chat Interaction Test")
print("-" * 50)

try:
    # We generate a unique session_id to simulate a new customer starting a conversation.
    session_id = f"test-session-{uuid.uuid4()}"
    
    # This is the data for our chat message.
    chat_data = {
        "message": "hello",
        "session_id": session_id
    }

    print(f"Sending a greeting with new session_id: {session_id}...")
    # Make the POST request to the /chat/message endpoint.
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/message",
        json=chat_data
    )

    response.raise_for_status()

    # A successful chat response returns a 200 OK status.
    print(f"✅ SUCCESS! The server responded with Status Code: {response.status_code}")
    print("\nBot responded successfully:")
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.HTTPError as http_err:
    print(f"❌ FAILED! The server responded with an error: {http_err.response.status_code}")
    print(f"Response: {http_err.response.text}")

except requests.exceptions.RequestException as err:
    print(f"❌ FAILED! Could not connect to the server. Is it running?")
    print(f"Error: {err}")

print("-" * 50)

# DONE--------------