import sqlite3
from datetime import datetime
from typing import Optional, Dict, List

class CreditService:
    def __init__(self, db_path: str = 'astrology.db'):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Initialize credit-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User credits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid),
                UNIQUE(userid)
            )
        ''')
        
        # Credit transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                source TEXT NOT NULL,
                reference_id TEXT,
                description TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid)
            )
        ''')
        
        # Promo codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                credits INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at TIMESTAMP,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (userid)
            )
        ''')
        
        # Promo code usage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promo_code_id INTEGER NOT NULL,
                userid INTEGER NOT NULL,
                credits_earned INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (promo_code_id) REFERENCES promo_codes (id),
                FOREIGN KEY (userid) REFERENCES users (userid),
                UNIQUE(promo_code_id, userid)
            )
        ''')
        
        # Credit settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value INTEGER NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default credit costs
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'chat_question_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('chat_question_cost', 1, 'Credits per chat question')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'wealth_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('wealth_analysis_cost', 5, 'Credits per wealth analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'marriage_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('marriage_analysis_cost', 3, 'Credits per marriage analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'health_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('health_analysis_cost', 3, 'Credits per health analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'education_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('education_analysis_cost', 3, 'Credits per education analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'premium_chat_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('premium_chat_cost', 10, 'Credits per premium deep analysis chat')
            ''')
        
        conn.commit()
        conn.close()
    
    def get_user_credits(self, userid: int) -> int:
        """Get current credit balance for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT credits FROM user_credits WHERE userid = ?", (userid,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
    
    def add_credits(self, userid: int, amount: int, source: str, reference_id: str = None, description: str = None) -> bool:
        """Add credits to user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_balance = self.get_user_credits(userid)
        new_balance = current_balance + amount
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_credits (userid, credits, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (userid, new_balance))
        
        cursor.execute("""
            INSERT INTO credit_transactions 
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (?, 'earned', ?, ?, ?, ?, ?)
        """, (userid, amount, new_balance, source, reference_id, description))
        
        conn.commit()
        conn.close()
        return True
    
    def spend_credits(self, userid: int, amount: int, feature: str, description: str = None) -> bool:
        """Spend credits for a feature"""
        current_balance = self.get_user_credits(userid)
        
        if current_balance < amount:
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        new_balance = current_balance - amount
        
        cursor.execute("""
            UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE userid = ?
        """, (new_balance, userid))
        
        cursor.execute("""
            INSERT INTO credit_transactions 
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (?, 'spent', ?, ?, ?, ?, ?)
        """, (userid, -amount, new_balance, 'feature_usage', feature, description))
        
        conn.commit()
        conn.close()
        return True
    
    def redeem_promo_code(self, userid: int, code: str) -> Dict:
        """Redeem promo code for credits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, credits, max_uses, used_count, is_active, expires_at 
            FROM promo_codes WHERE code = ?
        """, (code,))
        promo = cursor.fetchone()
        
        if not promo:
            conn.close()
            return {"success": False, "message": "Invalid promo code"}
        
        promo_id, credits, max_uses, used_count, is_active, expires_at = promo
        
        if not is_active:
            conn.close()
            return {"success": False, "message": "Promo code is inactive"}
        
        if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
            conn.close()
            return {"success": False, "message": "Promo code has expired"}
        
        # Check how many times this user has used this promo code
        cursor.execute("""
            SELECT COUNT(*) FROM promo_code_usage WHERE promo_code_id = ? AND userid = ?
        """, (promo_id, userid))
        user_usage_count = cursor.fetchone()[0]
        
        if user_usage_count >= max_uses:
            conn.close()
            return {"success": False, "message": f"You have already used this promo code {max_uses} time(s)"}
        
        self.add_credits(userid, credits, 'promo_code', code, f"Promo code: {code}")
        
        cursor.execute("""
            UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?
        """, (promo_id,))
        
        cursor.execute("""
            INSERT INTO promo_code_usage (promo_code_id, userid, credits_earned)
            VALUES (?, ?, ?)
        """, (promo_id, userid, credits))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": f"Successfully redeemed {credits} credits!",
            "credits_earned": credits
        }
    
    def get_credit_setting(self, setting_key: str) -> int:
        """Get credit cost setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM credit_settings WHERE setting_key = ?", (setting_key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 1
    
    def update_credit_setting(self, setting_key: str, value: int) -> bool:
        """Update credit cost setting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE credit_settings 
            SET setting_value = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE setting_key = ?
        """, (value, setting_key))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_all_credit_settings(self) -> List[Dict]:
        """Get all credit settings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT setting_key, setting_value, description 
            FROM credit_settings 
            WHERE setting_key IN ('chat_question_cost', 'premium_chat_cost', 'wealth_analysis_cost', 'marriage_analysis_cost', 'health_analysis_cost', 'education_analysis_cost')
            ORDER BY setting_key
        """)
        
        settings = []
        for row in cursor.fetchall():
            settings.append({
                "key": row[0],
                "value": row[1],
                "description": row[2]
            })
        
        conn.close()
        return settings
    
    def get_transaction_history(self, userid: int, limit: int = 50) -> List[Dict]:
        """Get credit transaction history for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_type, amount, balance_after, source, description, created_at
            FROM credit_transactions 
            WHERE userid = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (userid, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                "type": row[0],
                "amount": row[1],
                "balance_after": row[2],
                "source": row[3],
                "description": row[4],
                "date": row[5]
            })
        
        conn.close()
        return transactions