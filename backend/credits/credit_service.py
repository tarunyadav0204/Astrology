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
                max_uses_per_user INTEGER DEFAULT 1,
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
                FOREIGN KEY (userid) REFERENCES users (userid)
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
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'career_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('career_analysis_cost', 12, 'Credits per career analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'progeny_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('progeny_analysis_cost', 15, 'Credits per progeny analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'trading_daily_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('trading_daily_cost', 5, 'Credits per daily trading forecast')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'trading_monthly_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('trading_monthly_cost', 20, 'Credits per monthly trading calendar')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'childbirth_planner_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('childbirth_planner_cost', 8, 'Credits per childbirth muhurat planning')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'vehicle_purchase_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('vehicle_purchase_cost', 10, 'Credits per vehicle purchase muhurat')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'griha_pravesh_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('griha_pravesh_cost', 15, 'Credits per griha pravesh muhurat')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'gold_purchase_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('gold_purchase_cost', 12, 'Credits per gold purchase muhurat')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'business_opening_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('business_opening_cost', 20, 'Credits per business opening muhurat')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'event_timeline_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('event_timeline_cost', 100, 'Credits per yearly event timeline analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'partnership_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('partnership_analysis_cost', 2, 'Credits per partnership compatibility analysis')
            ''')
        
        cursor.execute("SELECT COUNT(*) FROM credit_settings WHERE setting_key = 'karma_analysis_cost'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO credit_settings (setting_key, setting_value, description)
                VALUES ('karma_analysis_cost', 25, 'Credits per karma analysis')
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
    
    def refund_credits(self, userid: int, amount: int, feature: str, description: str = None) -> bool:
        """Refund credits to user account"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_balance = self.get_user_credits(userid)
        new_balance = current_balance + amount
        
        cursor.execute("""
            UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE userid = ?
        """, (new_balance, userid))
        
        cursor.execute("""
            INSERT INTO credit_transactions 
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (?, 'refund', ?, ?, ?, ?, ?)
        """, (userid, amount, new_balance, 'refund', feature, description))
        
        conn.commit()
        conn.close()
        return True
    
    def redeem_promo_code(self, userid: int, code: str) -> Dict:
        """Redeem promo code for credits"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.execute('BEGIN IMMEDIATE')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at 
                FROM promo_codes WHERE code = ?
            """, (code,))
            promo = cursor.fetchone()
            
            if not promo:
                return {"success": False, "message": "Invalid promo code"}
            
            promo_id, credits, max_uses, max_uses_per_user, used_count, is_active, expires_at = promo
            
            if not is_active:
                return {"success": False, "message": "Promo code is inactive"}
            
            if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
                return {"success": False, "message": "Promo code has expired"}
            
            # Check how many times this user has used this promo code
            cursor.execute("""
                SELECT COUNT(*) FROM promo_code_usage WHERE promo_code_id = ? AND userid = ?
            """, (promo_id, userid))
            user_usage_count = cursor.fetchone()[0]
            
            if user_usage_count >= max_uses_per_user:
                return {"success": False, "message": f"You have already used this promo code {max_uses_per_user} time(s)"}
            
            # Record usage first
            cursor.execute("""
                INSERT INTO promo_code_usage (promo_code_id, userid, credits_earned)
                VALUES (?, ?, ?)
            """, (promo_id, userid, credits))
            
            # Update user credits directly in this transaction
            current_balance = self.get_user_credits(userid)
            new_balance = current_balance + credits
            
            cursor.execute("""
                INSERT OR REPLACE INTO user_credits (userid, credits, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (userid, new_balance))
            
            cursor.execute("""
                INSERT INTO credit_transactions 
                (userid, transaction_type, amount, balance_after, source, reference_id, description)
                VALUES (?, 'earned', ?, ?, ?, ?, ?)
            """, (userid, credits, new_balance, 'promo_code', code, f"Promo code: {code}"))
            
            # Update promo code usage count
            cursor.execute("""
                UPDATE promo_codes SET used_count = used_count + 1 WHERE id = ?
            """, (promo_id,))
            
            conn.commit()
            
            return {
                "success": True, 
                "message": f"Successfully redeemed {credits} credits!",
                "credits_earned": credits
            }
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error in redeem_promo_code: {str(e)}")
            return {"success": False, "message": "An error occurred while redeeming the promo code"}
        finally:
            if conn:
                conn.close()
    
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
            WHERE setting_key IN ('chat_question_cost', 'premium_chat_cost', 'partnership_analysis_cost', 'wealth_analysis_cost', 'marriage_analysis_cost', 'health_analysis_cost', 'education_analysis_cost', 'career_analysis_cost', 'progeny_analysis_cost', 'trading_daily_cost', 'trading_monthly_cost', 'childbirth_planner_cost', 'vehicle_purchase_cost', 'griha_pravesh_cost', 'gold_purchase_cost', 'business_opening_cost', 'event_timeline_cost', 'karma_analysis_cost')
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
        """Get credit transaction history for user. reference_id is the activity/feature for spends."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT transaction_type, amount, balance_after, source, reference_id, description, created_at
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
                "reference_id": row[4],
                "description": row[5],
                "date": row[6]
            })
        
        conn.close()
        return transactions

    def get_daily_activity(self, target_date: str) -> List[Dict]:
        """
        Get all credit transactions for a given date (YYYY-MM-DD) across all users.
        Returns list with user info and transaction details, ordered by time (newest first).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.transaction_type, ct.amount, ct.balance_after,
                   ct.source, ct.reference_id, ct.description, ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE date(ct.created_at) = ?
            ORDER BY ct.created_at DESC
        """, (target_date,))
        rows = cursor.fetchall()
        conn.close()

        transactions = []
        for row in rows:
            transactions.append({
                "id": row[0],
                "userid": row[1],
                "user_name": row[2] or "",
                "user_phone": row[3] or "",
                "type": row[4],
                "amount": row[5],
                "balance_after": row[6],
                "source": row[7],
                "reference_id": row[8],
                "description": row[9],
                "created_at": row[10],
            })
        return transactions

    def get_dashboard_stats(self, from_date: str, to_date: str) -> Dict:
        """
        Aggregate stats for admin dashboard: top users by activity count,
        distribution by activity (reference_id), and daily time series.
        from_date, to_date: YYYY-MM-DD inclusive.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ct.userid, u.name, u.phone, COUNT(*) AS cnt
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE ct.transaction_type = 'spent'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            GROUP BY ct.userid
            ORDER BY cnt DESC
            LIMIT 10
        """, (from_date, to_date))
        top_users = [
            {"userid": r[0], "user_name": r[1] or "", "user_phone": r[2] or "", "transaction_count": r[3]}
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT COALESCE(ct.reference_id, 'other') AS activity,
                   COUNT(*) AS cnt,
                   SUM(-ct.amount) AS total_credits
            FROM credit_transactions ct
            WHERE ct.transaction_type = 'spent'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            GROUP BY COALESCE(ct.reference_id, 'other')
            ORDER BY total_credits DESC
        """, (from_date, to_date))
        distribution = [
            {"activity": r[0], "transaction_count": r[1], "total_credits": r[2] or 0}
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT date(ct.created_at) AS d,
                   SUM(CASE WHEN ct.transaction_type IN ('earned', 'refund') THEN ct.amount ELSE 0 END) AS earned,
                   SUM(CASE WHEN ct.transaction_type = 'spent' THEN -ct.amount ELSE 0 END) AS spent,
                   COUNT(*) AS transaction_count
            FROM credit_transactions ct
            WHERE date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            GROUP BY date(ct.created_at)
            ORDER BY d
        """, (from_date, to_date))
        time_series = [
            {"date": r[0], "earned": r[1] or 0, "spent": r[2] or 0, "transaction_count": r[3]}
            for r in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                SUM(CASE WHEN transaction_type IN ('earned', 'refund') THEN amount ELSE 0 END),
                SUM(CASE WHEN transaction_type = 'spent' THEN -amount ELSE 0 END),
                COUNT(*)
            FROM credit_transactions
            WHERE date(created_at) >= ? AND date(created_at) <= ?
        """, (from_date, to_date))
        row = cursor.fetchone()
        total_earned = row[0] or 0
        total_spent = row[1] or 0
        total_count = row[2] or 0

        conn.close()
        return {
            "from_date": from_date,
            "to_date": to_date,
            "summary": {
                "total_earned": total_earned,
                "total_spent": total_spent,
                "transaction_count": total_count,
            },
            "top_users_by_activity": top_users,
            "distribution_by_activity": distribution,
            "time_series": time_series,
        }