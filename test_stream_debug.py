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
        system_instr = "You are an AI."
        print(f"Testing stream with {model_name}...")
        
        response_stream = await client.aio.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config={'system_instruction': system_instr, 'temperature': 0.7}
        )
        
        async for chunk in response_stream:
            print("CHUNK:", chunk.text)
            
        print("Success!")
    except Exception as e:
        print("EXCEPTION:", str(e))
        import traceback
        traceback.print_exc()

asyncio.run(main())
