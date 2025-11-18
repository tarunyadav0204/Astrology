#!/usr/bin/env python3
"""
Add test credits to existing users
"""

import sqlite3
from credits.credit_service import CreditService

def add_test_credits():
    """Add credits to all existing users for testing"""
    credit_service = CreditService()
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT userid, name, phone FROM users")
    users = cursor.fetchall()
    
    if not users:
        print("No users found. Please register a user first.")
        return
    
    print(f"Found {len(users)} users. Adding test credits...")
    
    for userid, name, phone in users:
        # Add 100 test credits to each user
        success = credit_service.add_credits(
            userid=userid,
            amount=100,
            source='admin_bonus',
            reference_id='TEST_CREDITS',
            description='Test credits for development'
        )
        
        if success:
            balance = credit_service.get_user_credits(userid)
            print(f"✅ Added credits to {name} ({phone[-4:]}): {balance} total credits")
        else:
            print(f"❌ Failed to add credits to {name}")
    
    conn.close()
    print("\n🎉 Test credits added successfully!")

if __name__ == "__main__":
    add_test_credits()