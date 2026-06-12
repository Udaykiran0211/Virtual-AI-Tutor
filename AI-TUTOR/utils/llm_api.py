import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
except Exception:
    google_genai = None
    genai_types = None

# Simple Disk Cache
CACHE_FILE = os.path.join('data', 'ai_cache.json')

def get_from_cache(category, key):
    if not os.path.exists(CACHE_FILE): return None
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
        return cache.get(category, {}).get(key)
    except: return None

def save_to_cache(category, key, value):
    os.makedirs('data', exist_ok=True)
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except: cache = {}
    if category not in cache: cache[category] = {}
    cache[category][key] = value
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except: pass

def get_client():
    """Get a configured Gemini client using the new google.genai SDK."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key or google_genai is None: return None
    try:
        return google_genai.Client(api_key=api_key)
    except Exception as e:
        print(f"DEBUG: Error creating genai client: {e}", flush=True)
        return None

# Model preference order — lightest/cheapest first to conserve quota
MODEL_PRIORITY = [
    'gemini-2.5-flash-lite',
    'gemini-flash-lite-latest',
    'gemini-2.5-flash',
    'gemini-flash-latest',
    'gemini-2.0-flash-lite',
    'gemini-2.0-flash',
]

def _is_quota_or_not_found(err_str):
    """Return True if the error is a recoverable quota or 404 error."""
    return any(k in err_str for k in ['429', '404', 'RESOURCE_EXHAUSTED', 'not found', 'quota'])

async def _generate_with_fallback(client, prompt, preferred_model=None):
    """Try models in priority order until one succeeds."""
    if client is None: return None
    models = list(MODEL_PRIORITY)
    if preferred_model and preferred_model in models:
        models.remove(preferred_model)
        models.insert(0, preferred_model)

    for model_name in models:
        try:
            def call(m=model_name):
                return client.models.generate_content(model=m, contents=prompt)
            response = await asyncio.to_thread(call)
            print(f"DEBUG: Used model {model_name}", flush=True)
            return response.text
        except Exception as e:
            err = str(e)
            if _is_quota_or_not_found(err):
                print(f"DEBUG: Model {model_name} skipped ({err[:60]})", flush=True)
                continue
            print(f"DEBUG: Model {model_name} unexpected error: {e}", flush=True)
    return None

def extract_json(text):
    """Robustly extracts JSON from AI responses."""
    try:
        if '```' in text:
            parts = text.split('```')
            if len(parts) >= 3:
                content = parts[1]
                if content.startswith('json'): content = content[4:]
                return content.strip()
        start_obj = text.find('{')
        start_arr = text.find('[')
        if (start_obj != -1 and (start_arr == -1 or start_obj < start_arr)):
            end = text.rfind('}')
            if end != -1: return text[start_obj:end+1].strip()
        elif (start_arr != -1):
            end = text.rfind(']')
            if end != -1: return text[start_arr:end+1].strip()
        return text.strip()
    except: return text.strip()

def generate_simple_notes(topic_name):
    """Fallback notes when AI is unavailable."""
    return f"""
    <h3>{topic_name} Overview</h3>
    <p>This module covers the core principles of {topic_name}. Key highlights include:</p>
    <ul>
        <li><strong>Main Goal</strong>: Understanding how {topic_name} fits into larger technical architectures.</li>
        <li><strong>Key Operations</strong>: Common functions, methods, and syntax patterns.</li>
        <li><strong>Best Practices</strong>: Common conventions used by industry professionals.</li>
    </ul>
    <p><em>Note: Full AI analysis is temporarily unavailable. Please try again in a few minutes.</em></p>
    """

def generate_simple_quiz(topic):
    return [
        {"question": f"What is core to {topic}?", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": 1, "explanation": f"Option B is core because it defines the fundamental execution context of {topic}."},
        {"question": f"How does the following code behave?\n```python\nx = 10\nif x > 5: print('Large')\n```", "options": ["Prints Large", "Prints Small", "Error", "No output"], "answer": 0, "explanation": "The condition 10 > 5 is true, so the print statement executes."},
        {"question": f"Best tool for {topic}?", "options": ["Tool A", "Tool B", "Tool C", "Tool D"], "answer": 2, "explanation": "Tool C is industry-standard for high-performance operations."},
        {"question": f"Primary risk in {topic}?", "options": ["Cost", "Security", "Complexity", "Time"], "answer": 1, "explanation": "Security is the primary concern when handling external inputs in this context."},
        {"question": f"Who uses {topic}?", "options": ["Devs", "Managers", "Users", "Everyone"], "answer": 0, "explanation": "Developers use this to build the underlying architecture."},
        {"question": f"What does this snippet do?\n```python\n[i**2 for i in range(3)]\n```", "options": ["[0, 1, 4]", "[1, 2, 3]", "Error", "[0, 1, 2]"], "answer": 0, "explanation": "This is a list comprehension that squares numbers from 0 to 2."},
        {"question": f"First step in {topic}?", "options": ["Planning", "Coding", "Testing", "Deploying"], "answer": 0, "explanation": "Planning ensures requirements are met before any code is written."},
        {"question": f"Worst practice in {topic}?", "options": ["Laziness", "Glitches", "Hack", "Shortcut"], "answer": 2, "explanation": "Using a 'hack' introduces technical debt and potential security vulnerabilities."},
        {"question": f"Ideal environment for {topic}?", "options": ["Cloud", "Local", "Hybrid", "Any"], "answer": 3, "explanation": "Modern implementations are designed to be environment-agnostic."},
        {"question": f"Main benefit of {topic}?", "options": ["ROI", "Speed", "Quality", "Efficiency"], "answer": 1, "explanation": "Speed is the most cited benefit for adoption in fast-paced teams."},
    ]

# ─────────────────────────────────────────────
# Public API functions
# ─────────────────────────────────────────────

async def generate_technical_notes(topic_name, language="programming"):
    cache_key = f"{topic_name}_{language}"
    cached = get_from_cache('notes', cache_key)
    if cached: return cached

    client = get_client()
    if client is None: return generate_simple_notes(topic_name)

    prompt = f"""
    Generate detailed technical learning notes for the topic: {topic_name} in the context of {language}.
    Structure the response with high-quality HTML:
    1. <h2>Brief Introduction</h2>: Definition and importance.
    2. <h2>Core Technical Concepts</h2>: Detailed bullet points with explanation.
    3. <h2>Code Example</h2>: A practical, well-commented code snippet using <pre><code>, specifically in {language} if applicable.
    4. <h2>Common Pitfalls & Best Practices</h2>: Practical advice.
    Use <ul>, <li>, <strong>, <code>. Max 600 words.
    """

    for attempt in range(4):
        try:
            if attempt > 0:
                delay = min(4 * (2 ** attempt), 30)
                print(f"DEBUG: Notes retry in {delay}s...", flush=True)
                await asyncio.sleep(delay)
            text = await _generate_with_fallback(client, prompt)
            if text:
                save_to_cache('notes', cache_key, text)
                return text
        except Exception as e:
            print(f"DEBUG: Notes attempt {attempt+1} error: {e}", flush=True)

    return generate_simple_notes(topic_name)


async def get_chat_response(query, topic, history=[], is_interview_mode=False):
    client = get_client()
    if client is None:
        return "Chat unavailable — API key not configured."

    if is_interview_mode:
        prompt = f"Topic: {topic}. User Query: {query}. As a strict technical interviewer for {topic}, evaluate the candidate's answer if provided, then ask a new difficult question. Do NOT provide answers directly. Be concise (2-3 sentences max)."
    else:
        prompt = f"Topic: {topic}. User Query: {query}. Be a helpful technical tutor. Concise (2-3 sentences max)."

    # Build conversation context from history
    if history:
        history_text = "\n".join([f"{'User' if h.get('role') == 'user' else 'Assistant'}: {h.get('content', '')}" for h in history[-6:]])
        prompt = f"Previous conversation:\n{history_text}\n\n{prompt}"

    models = list(MODEL_PRIORITY)
    for model_name in models:
        try:
            def call(m=model_name, p=prompt):
                return client.models.generate_content(model=m, contents=p)
            response = await asyncio.to_thread(call)
            return response.text
        except Exception as e:
            err = str(e)
            if _is_quota_or_not_found(err):
                continue
            if 'quota' in err.lower() or '429' in err:
                return "I'm a bit busy right now due to high demand (API quota reached). Please try again in ~30 seconds!"
            return f"I'm having a bit of trouble connecting. Could you repeat that? ({err[:50]})"

    return "All AI models are currently busy. Please try again in a few minutes — the quota resets soon!"


async def generate_quiz_review(errors, topic):
    client = get_client()
    if client is None: return "<p>AI feedback unavailable.</p>"
    prompt = f"The user just failed these questions on {topic}:\n{errors}\nProvide a concise, encouraging technical explanation for why they might be struggling and clarify the concepts. Format with HTML tags like <p>, <ul>, <li>, <strong>."
    text = await _generate_with_fallback(client, prompt)
    return text or "<p>Unable to generate review at this time.</p>"


async def generate_quiz(topic, language="programming"):
    client = get_client()
    if client is None: return generate_simple_quiz(topic)
    try:
        prompt = f"Generate 15 MCQ strictly and exclusively about the specific topic '{topic}' in the context of {language}. All 15 questions MUST be heavily focused specifically on '{topic}'. Mandate 5 questions include {language} code snippets in backticks relevant to {topic}. Return ONLY a JSON array of objects with keys: question, options (array of 4), answer (0-indexed int), explanation (1 sentence). No extra text."
        text = await _generate_with_fallback(client, prompt)
        if text:
            data = json.loads(extract_json(text))
            if data: return data
    except Exception as e:
        print(f"DEBUG: Quiz generation error: {e}", flush=True)
    return generate_simple_quiz(topic)


async def generate_custom_roadmap(goal, language):
    cache_key = f"{goal}_{language}"
    cached = get_from_cache('roadmap', cache_key)
    if cached: return cached

    client = get_client()
    if client is None: return get_fallback_roadmap(goal, language)

    for attempt in range(3):
        try:
            if attempt > 0: await asyncio.sleep(5)
            prompt = f"Roadmap for goal: {goal} ({language}). Return ONLY JSON: {{\"beginner\", \"intermediate\", \"advanced\"}} with arrays of {{id, topic, description}}. Max 2 items per level."
            text = await _generate_with_fallback(client, prompt)
            if text:
                data = json.loads(extract_json(text))
                if data:
                    save_to_cache('roadmap', cache_key, data)
                    return data
        except Exception as e:
            print(f"DEBUG: Roadmap attempt {attempt+1} error: {e}", flush=True)

    return get_fallback_roadmap(goal, language)


def get_fallback_roadmap(goal, language):
    return {
        "beginner": [{"id": "fb_01", "topic": f"Intro to {language}", "description": "Basic syntax"}, {"id": "fb_02", "topic": "Fundamentals", "description": "Core logic"}],
        "intermediate": [{"id": "fb_03", "topic": "Architecture", "description": "Structure"}, {"id": "fb_04", "topic": "Data", "description": "Storage"}],
        "advanced": [{"id": "fb_05", "topic": "Polish", "description": "Refinement"}, {"id": "fb_06", "topic": "Deployment", "description": "Launch"}]
    }
