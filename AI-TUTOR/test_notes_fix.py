import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from utils.llm_api import generate_technical_notes

async def test_notes():
    topic = "File I/O in Python"
    print(f"\n--- Testing AI Notes Content: {topic} ---")
    notes = await generate_technical_notes(topic)
    print("\n[AI OUTPUT START]")
    print(notes)
    print("[AI OUTPUT END]\n")
    
    if "<h2>" in notes or "<h3>" in notes:
        print("SUCCESS: Found structured headings.")
    if "<code>" in notes or "<pre>" in notes:
        print("SUCCESS: Found code snippets.")
    if "Overview" in notes and "available" in notes:
        print("WARNING: Falling back to local notes. Check API connection.")

if __name__ == "__main__":
    asyncio.run(test_notes())
