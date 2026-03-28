import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No GEMINI_API_KEY found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Testing available models for quota...")
working_models = []
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            model_name = m.name.replace('models/', '')
            print(f"Testing {model_name}...", end=" ", flush=True)
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hi", generation_config={"max_output_tokens": 10})
                print("SUCCESS")
                working_models.append(model_name)
            except Exception as e:
                print(f"FAILED ({str(e)[:50]}...)")
            # Sleep a bit to avoid triggering rate limits just by testing
            time.sleep(1)
except Exception as e:
    print(f"Error listing models: {str(e)}")

print("\nSummary of working models:")
for wm in working_models:
    print(f"- {wm}")
