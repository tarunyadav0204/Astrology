#!/usr/bin/env python3
"""
Test script to verify image integration in chat UI
"""
import sqlite3
import json
from datetime import datetime

def add_test_images_to_message():
    """Add test images to an existing chat message for UI testing"""
    
    # Sample images data
    test_images = [
        {
            "url": "https://replicate.delivery/pbxt/example1.jpg",
            "description": "Mystical Leo constellation with golden energy radiating from the lion's heart, representing your powerful Sun placement"
        },
        {
            "url": "https://replicate.delivery/pbxt/example2.jpg", 
            "description": "Mercury in exaltation showing swift communication and brilliant intellect through cosmic symbols"
        }
    ]
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Find the most recent assistant message
        cursor.execute('''
            SELECT message_id, content FROM chat_messages 
            WHERE sender = 'assistant' AND status = 'completed' 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if not result:
            print("❌ No assistant messages found")
            return
            
        message_id, content = result
        print(f"📝 Found message ID: {message_id}")
        print(f"📄 Content preview: {content[:100]}...")
        
        # Update the message with test images
        cursor.execute('''
            UPDATE chat_messages 
            SET images = ? 
            WHERE message_id = ?
        ''', (json.dumps(test_images), message_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added {len(test_images)} test images to message {message_id}")
        print("🎨 Test images:")
        for i, img in enumerate(test_images, 1):
            print(f"   {i}. {img['description']}")
        
        print("\n🔍 To test:")
        print("1. Open the chat modal in the frontend")
        print("2. Load the chat history")
        print("3. Look for images displayed below the message text")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_images_to_message()