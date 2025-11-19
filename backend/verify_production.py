#!/usr/bin/env python3
"""
Production Environment Verification Script
Run this on your production server to verify JWT secret is properly configured
"""

import os
import sys
from dotenv import load_dotenv

def verify_jwt_secret():
    """Verify JWT secret is properly configured"""
    print("🔍 Verifying JWT Secret Configuration...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if JWT_SECRET exists
    jwt_secret = os.getenv('JWT_SECRET')
    
    if not jwt_secret:
        print("❌ ERROR: JWT_SECRET environment variable not found!")
        print("\n📋 To fix this:")
        print("1. Set environment variable: export JWT_SECRET='your-secret-key'")
        print("2. Or add to .env file: JWT_SECRET=your-secret-key")
        print("3. Or configure in your cloud platform settings")
        return False
    
    # Verify secret strength
    if len(jwt_secret) < 32:
        print(f"⚠️  WARNING: JWT secret is only {len(jwt_secret)} characters")
        print("   Recommended: At least 32 characters for security")
    
    # Check if it's the old weak secret
    if jwt_secret == "astrology-app-secret-key-2024":
        print("❌ ERROR: Using old weak JWT secret!")
        print("   This is a security vulnerability - change immediately")
        return False
    
    print(f"✅ JWT_SECRET found: {jwt_secret[:10]}...{jwt_secret[-10:]} ({len(jwt_secret)} chars)")
    print("✅ JWT secret configuration is valid")
    
    return True

def verify_dependencies():
    """Verify required dependencies are installed"""
    print("\n🔍 Verifying Dependencies...")
    
    try:
        import jwt
        print("✅ PyJWT installed")
    except ImportError:
        print("❌ PyJWT not installed: pip install PyJWT")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv installed")
    except ImportError:
        print("❌ python-dotenv not installed: pip install python-dotenv")
        return False
    
    return True

def test_jwt_functionality():
    """Test JWT token creation and verification"""
    print("\n🔍 Testing JWT Functionality...")
    
    try:
        import jwt
        from datetime import datetime, timedelta
        
        secret = os.getenv('JWT_SECRET')
        if not secret:
            print("❌ Cannot test JWT - no secret found")
            return False
        
        # Create test token
        payload = {
            'sub': 'test@example.com',
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        
        token = jwt.encode(payload, secret, algorithm='HS256')
        print(f"✅ JWT token created: {token[:20]}...")
        
        # Verify token
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        print(f"✅ JWT token verified: {decoded['sub']}")
        
        return True
        
    except Exception as e:
        print(f"❌ JWT test failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Production Environment Verification")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check JWT secret
    if not verify_jwt_secret():
        all_checks_passed = False
    
    # Check dependencies
    if not verify_dependencies():
        all_checks_passed = False
    
    # Test JWT functionality
    if not test_jwt_functionality():
        all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All checks passed! Production environment is ready.")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()