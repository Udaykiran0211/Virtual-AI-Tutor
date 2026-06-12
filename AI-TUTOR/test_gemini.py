import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')

async def test_gemini():
    print(f"Testing Gemini with key: {api_key[:10]}...")
    genai.configure(api_key=api_key)
    
    # Try multiple common names if one fails
    models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-flash-latest']
    
    for model_name in models_to_try:
        print(f"\nTrying model: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async("Say hello")
            print(f"Success with {model_name}: {response.text}")
            return
        except Exception as e:
            print(f"Failed with {model_name}: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
