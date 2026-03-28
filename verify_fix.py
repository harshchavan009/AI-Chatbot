import requests
import json

base_url = "http://127.0.0.1:8000/api"

def test_flow():
    # 1. Signup
    print("Signing up...")
    signup_resp = requests.post(f"{base_url}/signup", json={"username": "testuser", "password": "password123"})
    print(f"Signup: {signup_resp.status_code} - {signup_resp.json()}")

    # 2. Login
    print("\nLogging in...")
    login_resp = requests.post(f"{base_url}/login", data={"username": "testuser", "password": "password123"})
    print(f"Login: {login_resp.status_code}")
    token = login_resp.json().get("access_token")
    if not token:
        print("Failed to get token")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Chat
    print("\nSending chat message: 'Who is modi'...")
    chat_resp = requests.post(
        f"{base_url}/chat", 
        json={"user_input": "Who is modi", "language": "English"},
        headers=headers,
        timeout=30
    )
    print(f"Chat Response: {chat_resp.status_code}")
    if chat_resp.status_code == 200:
        data = chat_resp.json()
        response_text = data.get('response', '')
        print(f"\nAI Response:\n{response_text}")
        if "experiencing high traffic" in response_text:
            print("\nFAILURE: Still hitting fallback/quota error.")
        else:
            print("\nSUCCESS: AI responded correctly!")
    else:
        print(f"Error: {chat_resp.text}")

if __name__ == "__main__":
    test_flow()
