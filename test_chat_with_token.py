#!/usr/bin/env python3

import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint with valid token"""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIrOTE5OTk5OTk5OTk5IiwiZXhwIjoxNzY2MTU2MTA2fQ.LkIcGGhwqSlJfDfsGryona3mANcj9w2ACUJCK4KAsCU"
    
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
            timeout=60,
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("Streaming response:")
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode()
                    print(f"  {decoded_line}")
                    if decoded_line.startswith("data: "):
                        try:
                            data_part = decoded_line[6:]  # Remove "data: "
                            if data_part.strip():
                                parsed = json.loads(data_part)
                                if parsed.get('status') == 'error':
                                    print(f"  ERROR: {parsed.get('error')}")
                                    break
                                elif parsed.get('status') == 'complete':
                                    print(f"  COMPLETE: Response received")
                                    break
                        except json.JSONDecodeError:
                            pass
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chat_endpoint()