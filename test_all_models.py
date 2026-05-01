import asyncio
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-1.5-pro', 'gemini-pro-latest', 'gemini-2.5-flash', 'gemini-2.0-flash-lite']
    contents = [{'role': 'user', 'parts': [{'text': 'Hello'}]}]
    
    for model_name in models:
        print(f"Testing {model_name}...")
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=contents
            )
            print(f"Success! {model_name} works. Response: {response.text}")
        except Exception as e:
            print(f"Failed {model_name}: {str(e)}")

asyncio.run(main())
