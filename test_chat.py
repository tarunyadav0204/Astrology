#!/usr/bin/env python3

import jwt
import requests
import json
from datetime import datetime, timedelta

# JWT Configuration (from .env)
JWT_SECRET = "629b255507125eaf87d6822a6b18548d90f90a7dd92510fa260233393e6a11a6"
ALGORITHM = "HS256"

def create_test_token():
    """Create a valid JWT token for testing"""
    payload = {
        "sub": "+919999999999",  # Test phone number
        "exp": datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token

def test_chat_endpoint():
    """Test the chat endpoint with valid token"""
    token = create_test_token()
    print(f"Generated token: {token[:50]}...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    data = {
        "name": "Test User",
        "date": "1990-01-01", 
        "time": "12:00",
        "place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "UTC+5:30",
        "question": "What does my chart say about me?"
    }
    
    try:
        print("Testing chat endpoint...")
        response = requests.post(
            "http://localhost:8001/api/chat/ask",
            headers=headers,
            json=data,
            timeout=30,
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Streaming response:")
            for line in response.iter_lines():
                if line:
                    print(f"  {line.decode()}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_chat_endpoint()