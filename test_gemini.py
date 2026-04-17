import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
if not key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Hello")
    print("Gemini Response:", response.text)
except Exception as e:
    print("Gemini Error:", str(e))
