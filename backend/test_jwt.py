#!/usr/bin/env python3
"""
Test JWT functionality after secret change
"""

import os
import jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

print("🔐 JWT Test")
print("=" * 40)
print(f"Secret key found: {bool(SECRET_KEY)}")
print(f"Secret key preview: {SECRET_KEY[:10]}...{SECRET_KEY[-10:] if SECRET_KEY else 'None'}")

if not SECRET_KEY:
    print("❌ No JWT_SECRET found!")
    exit(1)

# Test token creation
test_payload = {
    "sub": "1234567890",
    "exp": datetime.utcnow() + timedelta(minutes=30)
}

try:
    # Create token
    token = jwt.encode(test_payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"✅ Token created: {token[:20]}...")
    
    # Verify token
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"✅ Token verified: {decoded['sub']}")
    
    print("\n🎉 JWT functionality is working correctly!")
    
except Exception as e:
    print(f"❌ JWT test failed: {e}")
    exit(1)