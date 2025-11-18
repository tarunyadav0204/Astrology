#!/usr/bin/env python3
"""
Manually create promo codes
"""

import sqlite3
from datetime import datetime, timedelta

def create_promo_codes():
    """Create promo codes manually"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # Create WELCOME codes
    welcome_codes = []
    for i in range(1, 11):  # Create 10 codes
        code = f"WELCOME{i:03d}"
        try:
            cursor.execute("""
                INSERT INTO promo_codes (code, credits, max_uses, is_active)
                VALUES (?, ?, ?, ?)
            """, (code, 50, 1, True))
            welcome_codes.append(code)
        except sqlite3.IntegrityError:
            pass  # Code already exists
    
    # Create PREMIUM codes
    premium_codes = []
    for i in range(1, 6):  # Create 5 codes
        code = f"PREMIUM{i:03d}"
        try:
            cursor.execute("""
                INSERT INTO promo_codes (code, credits, max_uses, is_active)
                VALUES (?, ?, ?, ?)
            """, (code, 200, 1, True))
            premium_codes.append(code)
        except sqlite3.IntegrityError:
            pass
    
    # Create VIP codes
    vip_codes = []
    for i in range(1, 4):  # Create 3 codes
        code = f"VIP{i:03d}"
        try:
            cursor.execute("""
                INSERT INTO promo_codes (code, credits, max_uses, is_active)
                VALUES (?, ?, ?, ?)
            """, (code, 500, 1, True))
            vip_codes.append(code)
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {len(welcome_codes)} WELCOME codes: {welcome_codes}")
    print(f"✅ Created {len(premium_codes)} PREMIUM codes: {premium_codes}")
    print(f"✅ Created {len(vip_codes)} VIP codes: {vip_codes}")
    
    return welcome_codes + premium_codes + vip_codes

if __name__ == "__main__":
    create_promo_codes()