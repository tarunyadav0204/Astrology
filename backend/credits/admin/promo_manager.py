import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class PromoCodeManager:
    def __init__(self, db_path: str = 'astrology.db'):
        self.db_path = db_path
    
    def create_bulk_codes(self, prefix: str, count: int, credits: int, max_uses: int = 1, max_uses_per_user: int = 1, expires_days: int = 30) -> List[str]:
        """Create multiple promo codes with sequential numbering"""
        import random
        import string
        
        codes = []
        expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for i in range(1, count + 1):
            # Generate code like WELCOME001, WELCOME002, etc.
            code = f"{prefix}{i:03d}"
            
            try:
                cursor.execute("""
                    INSERT INTO promo_codes (code, credits, max_uses, max_uses_per_user, expires_at, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, credits, max_uses, max_uses_per_user, expires_at, None))  # No created_by for now
                codes.append(code)
            except sqlite3.IntegrityError:
                # Code already exists, skip
                continue
        
        conn.commit()
        conn.close()
        
        return codes
    
    def get_usage_stats(self) -> Dict:
        """Get promo code usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total codes
        cursor.execute("SELECT COUNT(*) FROM promo_codes")
        total_codes = cursor.fetchone()[0]
        
        # Active codes
        cursor.execute("SELECT COUNT(*) FROM promo_codes WHERE is_active = 1")
        active_codes = cursor.fetchone()[0]
        
        # Used codes
        cursor.execute("SELECT COUNT(*) FROM promo_codes WHERE used_count > 0")
        used_codes = cursor.fetchone()[0]
        
        # Total credits distributed
        cursor.execute("SELECT SUM(credits_earned) FROM promo_code_usage")
        total_credits = cursor.fetchone()[0] or 0
        
        # Recent usage (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM promo_code_usage WHERE used_at > ?
        """, (week_ago,))
        recent_usage = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_codes": total_codes,
            "active_codes": active_codes,
            "used_codes": used_codes,
            "total_credits_distributed": total_credits,
            "recent_usage_7_days": recent_usage
        }
    
    def deactivate_expired_codes(self) -> int:
        """Deactivate expired promo codes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE promo_codes 
            SET is_active = 0 
            WHERE expires_at < ? AND is_active = 1
        """, (datetime.now().isoformat(),))
        
        deactivated_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deactivated_count