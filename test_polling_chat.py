#!/usr/bin/env python3
"""
Test script for polling chat architecture
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_TOKEN = "your_test_token_here"  # Replace with actual token

def test_polling_chat():
    """Test the new polling chat endpoints"""
    
    headers = {"Authorization": f"Bearer {TEST_USER_TOKEN}"}
    
    print("🧪 Testing Polling Chat Architecture")
    print("=" * 50)
    
    # 1. Create a chat session
    print("1️⃣ Creating chat session...")
    session_response = requests.post(f"{BASE_URL}/chat/session", headers=headers)
    
    if session_response.status_code != 200:
        print(f"❌ Failed to create session: {session_response.status_code}")
        return
    
    session_id = session_response.json()["session_id"]
    print(f"✅ Created session: {session_id}")
    
    # 2. Ask a question (async)
    print("\n2️⃣ Asking question asynchronously...")
    question_data = {
        "session_id": session_id,
        "question": "What does my birth chart say about my career prospects?",
        "language": "english",
        "response_style": "detailed"
    }
    
    ask_response = requests.post(f"{BASE_URL}/chat/ask", json=question_data, headers=headers)
    
    if ask_response.status_code != 200:
        print(f"❌ Failed to ask question: {ask_response.status_code}")
        print(ask_response.text)
        return
    
    ask_result = ask_response.json()
    message_id = ask_result["message_id"]
    print(f"✅ Question submitted! Message ID: {message_id}")
    print(f"📝 Status: {ask_result['status']}")
    print(f"💬 Message: {ask_result['message']}")
    
    # 3. Poll for response
    print(f"\n3️⃣ Polling for response (message_id: {message_id})...")
    
    max_polls = 40  # 40 polls * 3 seconds = 2 minutes max
    poll_count = 0
    
    while poll_count < max_polls:
        poll_count += 1
        print(f"🔄 Poll #{poll_count}...")
        
        status_response = requests.get(f"{BASE_URL}/chat/status/{message_id}", headers=headers)
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            break
        
        status_result = status_response.json()
        print(f"📊 Status: {status_result['status']}")
        
        if status_result["status"] == "completed":
            print("🎉 Response completed!")
            print(f"📝 Content length: {len(status_result.get('content', ''))}")
            print(f"⏰ Completed at: {status_result.get('completed_at')}")
            print("\n📄 Response preview:")
            print(status_result.get('content', '')[:200] + "...")
            break
        
        elif status_result["status"] == "failed":
            print("❌ Response failed!")
            print(f"🚨 Error: {status_result.get('error_message')}")
            break
        
        elif status_result["status"] == "processing":
            print(f"⏳ Still processing... ({status_result.get('message', '')})")
            time.sleep(3)  # Wait 3 seconds before next poll
        
        else:
            print(f"❓ Unknown status: {status_result['status']}")
            break
    
    if poll_count >= max_polls:
        print("⏰ Polling timeout reached")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_polling_chat()