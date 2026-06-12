import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

session = requests.Session()

def test_endpoint(endpoint, data=None, method="GET"):
    print(f"\nTesting {method} {endpoint}...")
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "POST":
            resp = session.post(url, json=data, timeout=30)
        else:
            resp = session.get(url, params=data, timeout=10)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            try:
                print("Response:", json.dumps(resp.json(), indent=2)[:500] + "...")
            except:
                print("Response (not JSON):", resp.text[:200])
        else:
            print("Error Response:", resp.text[:200])
        return resp
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def login(username, password):
    print(f"\nAttempting login for {username}...")
    return test_endpoint("/login", {"username": username, "password": password}, method="POST")

if __name__ == "__main__":
    print("Wait for server to be ready...")
    
    # 1. Login
    login("testuser", "password123") # Assumes this user exists or we just signed up
    
    # 2. Core Features
    test_endpoint("/api/heartbeat")
    test_endpoint("/api/user_stats")
    
    # 3. Social Features
    test_endpoint("/api/friends/search", {"q": "test"})
    # Note: For these to work, we'd need multiple users and known IDs
    # But we can at least check if the endpoints exist and return something (even empty)
    test_endpoint("/api/friends/requests")
    test_endpoint("/api/friends/list")
    
    # 4. Content Features
    test_endpoint("/api/notes", {"topic": "Python Lists"}, method="POST")
    test_endpoint("/api/quiz", {"topic": "Python Lists"}, method="POST")
