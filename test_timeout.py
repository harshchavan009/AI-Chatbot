import sys
import asyncio
from app.core.config import settings
import google.generativeai as genai

async def main():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-flash-lite-latest")
    
    try:
        print("Sending chat...")
        # attempt to send
        resp = await model.generate_content_async("Hello", request_options={"timeout": 3})
        print(resp.text)
    except Exception as e:
        print("Error:", type(e).__name__, str(e))

asyncio.run(main())
