import requests
try:
    response = requests.get('http://127.0.0.1:5000/api/heartbeat')
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
