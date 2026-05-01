import asyncio
import aiohttp
import json

async def test_stream():
    async with aiohttp.ClientSession() as session:
        payload = {
            "session_id": "test_session",
            "user_input": "Explain Python programming language simply.",
            "language": "English",
            "model": "gemini-2.0-flash"
        }
        # Simulate local login with mock admin token, or bypass
        # Let's see if the endpoint requires auth.
        headers = {}
        # Wait, get_current_user might require a token. We will see.
        async with session.post('http://127.0.0.1:8000/api/chat/stream', json=payload, headers=headers) as resp:
            print(f"Status: {resp.status}")
            async for line in resp.content:
                if line:
                    print(line.decode('utf-8').strip())

if __name__ == "__main__":
    asyncio.run(test_stream())
