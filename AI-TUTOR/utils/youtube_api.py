import os
import json
# Force pure-python implementation of protobuf to avoid binary incompatibility on Python 3.14
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

try:
    from googleapiclient.discovery import build
except (ImportError, TypeError):
    build = None

VIDEO_CACHE_FILE = os.path.join('data', 'video_cache.json')

def get_from_cache(query):
    if not os.path.exists(VIDEO_CACHE_FILE): return None
    try:
        with open(VIDEO_CACHE_FILE, 'r') as f:
            cache = json.load(f)
        return cache.get(query)
    except: return None

def save_to_cache(query, url):
    os.makedirs('data', exist_ok=True)
    cache = {}
    if os.path.exists(VIDEO_CACHE_FILE):
        try:
            with open(VIDEO_CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except: cache = {}
    cache[query] = url
    try:
        with open(VIDEO_CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except: pass

def parse_duration(duration_str):
    """Parses ISO 8601 duration string like PT1H2M30S to seconds."""
    import re
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    
    total_seconds = 0
    if hours: total_seconds += int(hours.group(1)) * 3600
    if minutes: total_seconds += int(minutes.group(1)) * 60
    if seconds: total_seconds += int(seconds.group(1))
    return total_seconds

def get_youtube_video(query, language="programming", force_refresh=False):
    # 1. Check Cache First (unless refresh is forced)
    cache_key = f"{language}_{query}"
    if not force_refresh:
        cached_url = get_from_cache(cache_key)
        if cached_url:
            print(f"DEBUG: Returning cached video for '{cache_key}'", flush=True)
            return cached_url

    if build is None:
        print("DEBUG: YouTube build client is not available.", flush=True)
        return None

    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("DEBUG: YOUTUBE_API_KEY not found.", flush=True)
        return None
    
    try:
        # 1. Search for potential candidates
        # Refined query to include "full tutorial" and "English" to improve relevance
        search_query = f"{language} {query} full programming tutorial English"
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        search_request = youtube.search().list(
            q=search_query,
            part='id,snippet',
            maxResults=25, 
            type='video',
            videoEmbeddable='true',
            videoCategoryId='27', # Education
            relevanceLanguage='en'
        )
        search_response = search_request.execute()
        
        candidates = search_response.get('items', [])
        if not candidates:
            # Fallback query if first one fails
            search_query = f"{language} {query} tutorial"
            search_request = youtube.search().list(
                q=search_query,
                part='id,snippet',
                maxResults=10,
                type='video'
            )
            search_response = search_request.execute()
            candidates = search_response.get('items', [])

        if not candidates:
            return None

        # 2. Verify durations and statuses
        video_ids = [item['id']['videoId'] for item in candidates]
        status_request = youtube.videos().list(
            part='status,contentDetails',
            id=','.join(video_ids)
        )
        status_response = status_request.execute()
        
        video_details = {item['id']: item for item in status_response.get('items', [])}

        for vid_id in video_ids:
            details = video_details.get(vid_id)
            if not details: continue
            
            duration_str = details.get('contentDetails', {}).get('duration', 'PT0S')
            total_seconds = parse_duration(duration_str)
            
            # FILTER: More flexible 10 to 60 minutes window for better educational content
            if total_seconds < 600 or total_seconds > 3600:
                print(f"DEBUG: Skipping {vid_id} - Duration {total_seconds}s outside 10-60m window.", flush=True)
                continue

            # Check embeddable and no region restrictions
            is_embeddable = details.get('status', {}).get('embeddable', False)
            region_restriction = details.get('contentDetails', {}).get('regionRestriction', {})
            blocked = region_restriction.get('blocked', [])
            
            if is_embeddable and not blocked:
                url = f"https://www.youtube.com/embed/{vid_id}"
                save_to_cache(cache_key, url)
                print(f"DEBUG: Found and cached verified video ID {vid_id} ({total_seconds}s) for '{cache_key}'", flush=True)
                return url

        print(f"DEBUG: No verified 10-60m videos found for '{cache_key}'.", flush=True)
        return get_fallback_video(language, query)

    except Exception as e:
        print(f"DEBUG: YouTube API Error: {str(e)}", flush=True)
        return get_fallback_video(language, query)


FALLBACK_VIDEOS = {
    'python': [
        'https://www.youtube.com/embed/u-OmVr_fT4s',
        'https://www.youtube.com/embed/ZDa-Z5JzLYM',
        'https://www.youtube.com/embed/9Os0o3wzS_I'
    ],
    'java': [
        'https://www.youtube.com/embed/qay771mqKOk',
        'https://www.youtube.com/embed/ZFx0ZFQMtH0',
        'https://www.youtube.com/embed/-xmJSKRo5ec'
    ],
    'cpp': [
        'https://www.youtube.com/embed/EvYmTCx9BFs',
        'https://www.youtube.com/embed/ePJxpxsnkGw',
        'https://www.youtube.com/embed/2pAY7Ftlfl0'
    ]
}

def get_fallback_video(language, query):
    lang_key = (language or 'python').lower()
    pool = FALLBACK_VIDEOS.get(lang_key, FALLBACK_VIDEOS['python'])
    idx = sum(ord(c) for c in (query or '')) % len(pool)
    return pool[idx]

