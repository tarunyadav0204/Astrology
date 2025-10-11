#!/usr/bin/env python3
import sqlite3
import bcrypt

def test_login():
    phone = "9810690066"
    password = "#Tarun1454"
    
    # Get user from database
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT userid, name, phone, password, role FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        print("❌ User not found")
        return False
    
    print(f"✅ User found: {user[1]} ({user[2]})")
    
    # Test password verification
    stored_hash = user[3]
    print(f"Stored hash: {stored_hash[:50]}...")
    
    try:
        is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        if is_valid:
            print("✅ Password verification successful")
            return True
        else:
            print("❌ Password verification failed")
            return False
    except Exception as e:
        print(f"❌ Error during password verification: {e}")
        return False

if __name__ == "__main__":
    test_login()