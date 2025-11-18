#!/usr/bin/env python3
"""
Credit System Initialization Script
Run this script to set up the credit system and create initial promo codes
"""

from credit_service import CreditService
from admin.promo_manager import PromoCodeManager

def init_credit_system():
    """Initialize the credit system"""
    print("Initializing credit system...")
    
    # Initialize credit service (creates tables)
    credit_service = CreditService()
    print("✓ Credit tables created")
    
    # Initialize promo manager
    promo_manager = PromoCodeManager()
    
    # Create some initial promo codes
    welcome_codes = promo_manager.create_bulk_codes(
        prefix="WELCOME",
        count=100,
        credits=50,
        max_uses=1,
        expires_days=90
    )
    print(f"✓ Created {len(welcome_codes)} WELCOME promo codes (50 credits each)")
    
    # Create premium promo codes
    premium_codes = promo_manager.create_bulk_codes(
        prefix="PREMIUM",
        count=50,
        credits=200,
        max_uses=1,
        expires_days=60
    )
    print(f"✓ Created {len(premium_codes)} PREMIUM promo codes (200 credits each)")
    
    # Create VIP codes (higher value, limited)
    vip_codes = promo_manager.create_bulk_codes(
        prefix="VIP",
        count=10,
        credits=500,
        max_uses=1,
        expires_days=30
    )
    print(f"✓ Created {len(vip_codes)} VIP promo codes (500 credits each)")
    
    print("\n🎉 Credit system initialized successfully!")
    print("\nSample promo codes:")
    print(f"Welcome codes: {welcome_codes[:5]}...")
    print(f"Premium codes: {premium_codes[:3]}...")
    print(f"VIP codes: {vip_codes[:2]}...")
    
    return True

if __name__ == "__main__":
    init_credit_system()