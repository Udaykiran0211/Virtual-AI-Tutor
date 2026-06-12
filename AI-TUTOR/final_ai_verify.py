import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from utils.llm_api import generate_technical_notes, get_chat_response

async def final_verify():
    print("\n[1] Verifying Technical Notes (gemini-pro)...")
    notes = await generate_technical_notes("Python Decorators")
    if "<h2>" in notes and "Decorator" in notes:
        print("SUCCESS: Notes generated correctly.")
    else:
        print(f"FAILED: Notes check failed. Output length: {len(notes)}")

    print("\n[2] Verifying AI Chat (gemini-pro)...")
    chat = await get_chat_response("What is a decorator?", "Python Decorators", [])
    if len(chat) > 20 and "Error" not in chat:
        print("SUCCESS: Chat response received.")
        print(f"Response: {chat}")
    else:
        print(f"FAILED: Chat failed. Output: {chat}")

if __name__ == "__main__":
    asyncio.run(final_verify())
