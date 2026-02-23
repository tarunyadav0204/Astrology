import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any

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
    
    def has_transaction_with_reference(self, userid: int, source: str, reference_id: str) -> bool:
        """Return True if a transaction already exists with this source and reference_id (for idempotency)."""
        if not reference_id:
            return False
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM credit_transactions WHERE userid = ? AND source = ? AND reference_id = ? LIMIT 1",
            (userid, source, reference_id),
        )
        found = cursor.fetchone() is not None
        conn.close()
        return found

    def add_credits(self, userid: int, amount: int, source: str, reference_id: str = None, description: str = None, metadata: str = None) -> bool:
        """Add credits to user account. metadata: optional JSON (e.g. Google Play purchase_token, purchase_time for support)."""
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
            (userid, transaction_type, amount, balance_after, source, reference_id, description, metadata)
            VALUES (?, 'earned', ?, ?, ?, ?, ?, ?)
        """, (userid, amount, new_balance, source, reference_id, description, metadata))
        
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

    def is_google_play_order_reversed(self, userid: int, order_id: str) -> bool:
        """True if we already have a google_play_refund transaction for this user and order_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM credit_transactions
            WHERE userid = ? AND source = 'google_play_refund' AND reference_id = ?
            LIMIT 1
        """, (userid, order_id))
        found = cursor.fetchone() is not None
        conn.close()
        return found

    def reverse_google_play_purchase(self, userid: int, order_id: str, amount: Optional[int] = None):
        """
        Reverse a Google Play credit grant (after refund via Play API or Console).
        Deducts amount (default: full original) and records a reversal.
        Idempotent: returns error if order not found or already reversed.
        Returns: (True, amount_deducted, original_amount) or (False, error_message, None).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT amount FROM credit_transactions
            WHERE userid = ? AND source = 'google_play' AND reference_id = ? AND transaction_type = 'earned'
            LIMIT 1
        """, (userid, order_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Order not found or not a Google Play credit transaction", None
        original_amount = row[0]
        deduct = amount if amount is not None else original_amount
        if deduct <= 0 or deduct > original_amount:
            conn.close()
            return False, "Invalid amount (must be positive and not exceed original)", None
        cursor.execute("""
            SELECT 1 FROM credit_transactions
            WHERE userid = ? AND source = 'google_play_refund' AND reference_id = ?
            LIMIT 1
        """, (userid, order_id))
        if cursor.fetchone():
            conn.close()
            return False, "This order was already reversed", None
        current_balance = self.get_user_credits(userid)
        new_balance = current_balance - deduct
        cursor.execute("""
            UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?
        """, (new_balance, userid))
        cursor.execute("""
            INSERT INTO credit_transactions
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (?, 'spent', ?, ?, 'google_play_refund', ?, ?)
        """, (userid, -deduct, new_balance, order_id, f"Reversal: Google Play refund for order {order_id}"))
        conn.commit()
        conn.close()
        return True, deduct, original_amount

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

    def search_transactions(self, from_date: str, to_date: str, query: Optional[str] = None, limit: int = 500) -> List[Dict]:
        """
        Search credit transactions across all users for a date range, with optional
        wildcard search on user name or phone. Dates are YYYY-MM-DD inclusive.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        sql = """
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.transaction_type, ct.amount, ct.balance_after,
                   ct.source, ct.reference_id, ct.description, ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE date(ct.created_at) >= ? AND date(ct.created_at) <= ?
        """
        params: List[Any] = [from_date, to_date]

        if query:
            like = f"%{query}%"
            sql += " AND (u.name LIKE ? OR u.phone LIKE ?)"
            params.extend([like, like])

        sql += " ORDER BY ct.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
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

    def get_google_play_transactions(
        self,
        from_date: str,
        to_date: str,
        query: Optional[str] = None,
        order_id_filter: Optional[str] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        List Google Play credit transactions (source='google_play') with user info,
        purchase_token from metadata, and status (Credited / Reversed).
        Reversed = exists a row with source='google_play_refund' and same userid + reference_id.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        sql = """
            SELECT ct.id, ct.userid, u.name, u.phone,
                   ct.reference_id, ct.amount, ct.metadata, ct.created_at
            FROM credit_transactions ct
            LEFT JOIN users u ON u.userid = ct.userid
            WHERE ct.source = 'google_play'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
        """
        params: List[Any] = [from_date, to_date]
        if query:
            like = f"%{query}%"
            sql += " AND (u.name LIKE ? OR u.phone LIKE ?)"
            params.extend([like, like])
        if order_id_filter and order_id_filter.strip():
            sql += " AND ct.reference_id LIKE ?"
            params.append(f"%{order_id_filter.strip()}%")
        sql += " ORDER BY ct.created_at DESC LIMIT ?"
        params.append(limit)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        # (userid, order_id) -> total reversed amount (for partial display)
        reversed_amounts = {}
        cursor.execute("""
            SELECT userid, reference_id, SUM(ABS(amount)) FROM credit_transactions
            WHERE source = 'google_play_refund' AND reference_id IS NOT NULL
            GROUP BY userid, reference_id
        """)
        for r in cursor.fetchall():
            reversed_amounts[(r[0], r[1])] = r[2]
        conn.close()
        out = []
        for row in rows:
            tx_id, userid, name, phone, order_id, amount, metadata_json, created_at = row
            purchase_token = ""
            if metadata_json:
                try:
                    meta = json.loads(metadata_json)
                    purchase_token = meta.get("purchase_token") or ""
                except Exception:
                    pass
            key = (userid, order_id)
            reversed_amt = reversed_amounts.get(key, 0)
            status = "Reversed" if reversed_amt else "Credited"
            out.append({
                "id": tx_id,
                "userid": userid,
                "user_name": name or "",
                "user_phone": phone or "",
                "order_id": order_id or "",
                "purchase_token": purchase_token,
                "amount": amount,
                "created_at": created_at,
                "status": status,
                "reversed_amount": reversed_amt if reversed_amt else None,
            })
        return out

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
        top_userids = {u["userid"] for u in top_users}

        cursor.execute("""
            SELECT ct.userid, COALESCE(ct.reference_id, 'other') AS activity, COUNT(*) AS cnt
            FROM credit_transactions ct
            WHERE ct.transaction_type = 'spent'
              AND date(ct.created_at) >= ? AND date(ct.created_at) <= ?
            GROUP BY ct.userid, COALESCE(ct.reference_id, 'other')
        """, (from_date, to_date))
        activity_breakdown = {}
        for row in cursor.fetchall():
            uid, activity, cnt = row[0], row[1], row[2]
            if uid in top_userids:
                if uid not in activity_breakdown:
                    activity_breakdown[uid] = []
                activity_breakdown[uid].append({"activity": activity, "count": cnt})

        for u in top_users:
            u["by_activity"] = activity_breakdown.get(u["userid"], [])

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