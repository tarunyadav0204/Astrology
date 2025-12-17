#!/usr/bin/env python3

import requests
import json

# Test the life predictions endpoint
url = "http://localhost:8001/api/ashtakavarga/life-predictions"

# Mock request data
test_data = {
    "birth_data": {
        "name": "Test User",
        "date": "1990-01-01",
        "time": "12:00",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "UTC+5:30",
        "place": "Delhi",
        "gender": "M"
    }
}

try:
    response = requests.post(url, json=test_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")