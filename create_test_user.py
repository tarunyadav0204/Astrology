#!/usr/bin/env python3

import sqlite3
import bcrypt
import requests
import json

def create_test_user():
    """Create a test user in the database"""
    conn = sqlite3.connect('backend/astrology.db')
    cursor = conn.cursor()
    
    # Check if test user already exists
    cursor.execute("SELECT userid FROM users WHERE phone = ?", ("+919999999999",))
    if cursor.fetchone():
        print("Test user already exists")
        conn.close()
        return
    
    # Create test user
    password = "testpass123"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    cursor.execute(
        "INSERT INTO users (name, phone, password, role) VALUES (?, ?, ?, ?)",
        ("Test User", "+919999999999", hashed_password, "user")
    )
    conn.commit()
    
    # Get user ID
    cursor.execute("SELECT userid FROM users WHERE phone = ?", ("+919999999999",))
    user_id = cursor.fetchone()[0]
    
    # Give user some credits
    cursor.execute("""
        INSERT OR REPLACE INTO user_credits (userid, credits, updated_at)
        VALUES (?, ?, datetime('now'))
    """, (user_id, 100))
    
    conn.commit()
    conn.close()
    
    print(f"Created test user with ID: {user_id} and 100 credits")

def test_login():
    """Test login with the test user"""
    data = {
        "phone": "+919999999999",
        "password": "testpass123"
    }
    
    try:
        response = requests.post("http://localhost:8001/api/login", json=data)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Login successful!")
            print(f"Token: {result['access_token'][:50]}...")
            print(f"User: {result['user']}")
            return result['access_token']
        else:
            print(f"Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Login request failed: {e}")
        return None

if __name__ == "__main__":
    create_test_user()
    token = test_login()
    
    if token:
        print(f"\nUse this token for testing: {token}")