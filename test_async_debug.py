import asyncio
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        model_name = 'gemini-2.0-flash'
        contents = [{'role': 'user', 'parts': [{'text': 'Hello'}]}]
        
        print(f"Testing async (non-stream) with {model_name}...")
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=contents
        )
        print("Response:", response.text)
        
    except Exception as e:
        print("EXCEPTION:", str(e))
        import traceback
        traceback.print_exc()

asyncio.run(main())
