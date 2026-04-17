import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

print("Attempting handshake...")
res = requests.post(f"{BASE_URL}/api/auth/social_handshake", json={"username": "tester", "provider": "test"})
token = res.json()["access_token"]

print("Sending chat request...")
session_id = str(uuid.uuid4())
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "user_input": "Hello", 
    "session_id": session_id,
    "model": "gemini-flash-lite-latest"
}

res = requests.post(f"{BASE_URL}/api/chat", headers=headers, json=payload)
print("Status code:", res.status_code)
print("Response:", res.text)
print("Done")
