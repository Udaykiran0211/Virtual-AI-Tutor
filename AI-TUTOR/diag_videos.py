import os
import json
import re
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def parse_duration(duration_str):
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    total_seconds = 0
    if hours: total_seconds += int(hours.group(1)) * 3600
    if minutes: total_seconds += int(minutes.group(1)) * 60
    if seconds: total_seconds += int(seconds.group(1))
    return total_seconds

def diagnostic():
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("No API Key")
        return
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    queries = [
        "python variables and loops tutorial",
        "python functions and objects tutorial",
        "cpp basics and pointers tutorial"
    ]
    
    for q in queries:
        print(f"\nResults for: {q}")
        res = youtube.search().list(
            q=q,
            part='id,snippet',
            maxResults=20,
            type='video',
            videoEmbeddable='true',
            videoCategoryId='27'
        ).execute()
        
        ids = [item['id']['videoId'] for item in res.get('items', [])]
        if not ids:
            print("No videos found")
            continue
            
        vres = youtube.videos().list(
            part='contentDetails,status',
            id=','.join(ids)
        ).execute()
        
        for v in vres.get('items', []):
            dur = parse_duration(v['contentDetails']['duration'])
            embed = v['status']['embeddable']
            print(f"ID: {v['id']} | Duration: {dur/60:.1f}m | Embed: {embed}")

if __name__ == "__main__":
    diagnostic()
