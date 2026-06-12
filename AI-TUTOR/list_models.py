import os
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai

def list_models():
    api_key = os.environ.get('GEMINI_API_KEY')
    print(f"Key: {api_key[:8]}...")
    genai.configure(api_key=api_key)
    try:
        print("\nAvailable models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"FAILED to list models: {e}")

if __name__ == "__main__":
    list_models()
