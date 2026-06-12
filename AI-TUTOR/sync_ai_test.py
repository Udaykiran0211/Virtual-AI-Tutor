import os
import json
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

def test_sync():
    api_key = os.environ.get('GEMINI_API_KEY')
    print(f"Key loaded: {api_key[:8]}...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-flash-latest')
    
    print("\n[1] Testing basic generation...")
    try:
        response = model.generate_content("Hello, provide a 1-sentence test note about Python.")
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_sync()
