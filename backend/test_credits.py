#!/usr/bin/env python3
"""
Test script to verify credit system functionality
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_credit_system():
    print("🧪 Testing Credit System...")
    
    # Test user credentials (you'll need to register/login first)
    login_data = {
        "phone": "1234567890",  # Replace with your test phone
        "password": "test123"   # Replace with your test password
    }
    
    try:
        # Login to get token
        print("1. Logging in...")
        login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print("Please register a test user first or update credentials in test_credits.py")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test credit balance
        print("2. Checking credit balance...")
        balance_response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
        if balance_response.status_code == 200:
            balance = balance_response.json()["credits"]
            print(f"✅ Current balance: {balance} credits")
        else:
            print(f"❌ Balance check failed: {balance_response.status_code}")
        
        # Test promo code redemption
        print("3. Testing promo code redemption...")
        redeem_response = requests.post(
            f"{BASE_URL}/api/credits/redeem", 
            json={"code": "WELCOME001"}, 
            headers=headers
        )
        if redeem_response.status_code == 200:
            result = redeem_response.json()
            print(f"✅ Promo code redeemed: {result['message']}")
        else:
            print(f"❌ Promo code redemption failed: {redeem_response.status_code}")
            print(redeem_response.text)
        
        # Check balance again
        print("4. Checking balance after redemption...")
        balance_response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
        if balance_response.status_code == 200:
            new_balance = balance_response.json()["credits"]
            print(f"✅ New balance: {new_balance} credits")
        
        # Test transaction history
        print("5. Checking transaction history...")
        history_response = requests.get(f"{BASE_URL}/api/credits/history", headers=headers)
        if history_response.status_code == 200:
            transactions = history_response.json()["transactions"]
            print(f"✅ Found {len(transactions)} transactions")
            if transactions:
                print(f"   Latest: {transactions[0]['description']} ({transactions[0]['amount']} credits)")
        
        print("\n🎉 Credit system test completed successfully!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the backend server is running on localhost:8001")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_credit_system()