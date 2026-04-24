import requests
import json
import uuid

BASE_URL = "https://nova-ai-chatbot-8b04.onrender.com"

# 1. Signup / Handshake
print("Attempting handshake...")
res = requests.post(f"{BASE_URL}/api/auth/social_handshake", json={"username": "tester", "provider": "test"})
if res.status_code != 200:
    print("Handshake failed:", res.text)
    exit(1)

token = res.json()["access_token"]
print("Got token:", token[:10], "...")

# 2. Chat Stream
print("Sending chat request...")
session_id = str(uuid.uuid4())
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
payload = {
    "user_input": "Hello", 
    "session_id": session_id,
    "model": "gemini-flash-lite-latest"
}

res = requests.post(f"{BASE_URL}/api/chat/stream", headers=headers, json=payload, stream=True)
print("Status code:", res.status_code)
if res.status_code != 200:
    print("Response:", res.text)
else:
    for line in res.iter_lines():
        if line:
            print(line.decode('utf-8'))

print("Done")
