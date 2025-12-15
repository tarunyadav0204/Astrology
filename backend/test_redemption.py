#!/usr/bin/env python3
"""
Test promo code redemption logic
"""

import sys
sys.path.append('.')

from credits.credit_service import CreditService

def test_redemption():
    credit_service = CreditService()
    
    # Test redeeming TARUN_TEST for user 2
    result = credit_service.redeem_promo_code(2, 'TARUN_TEST')
    print(f"Redemption result: {result}")
    
    # Check current usage count
    import sqlite3
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM promo_code_usage WHERE promo_code_id = 35 AND userid = 2
    """)
    usage_count = cursor.fetchone()[0]
    print(f"Current usage count for user 2: {usage_count}")
    
    cursor.execute("""
        SELECT max_uses_per_user FROM promo_codes WHERE id = 35
    """)
    max_uses_per_user = cursor.fetchone()[0]
    print(f"Max uses per user: {max_uses_per_user}")
    
    conn.close()

if __name__ == "__main__":
    test_redemption()