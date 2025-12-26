import sqlite3
import html
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class CreditRequestService:
    def __init__(self, db_path: str = 'astrology.db'):
        self.db_path = db_path
        self.init_tables()
    
    def init_tables(self):
        """Initialize credit request table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                userid INTEGER NOT NULL,
                requested_amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                admin_notes TEXT,
                approved_amount INTEGER,
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (userid) REFERENCES users (userid),
                FOREIGN KEY (approved_by) REFERENCES users (userid)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def sanitize_reason(self, reason: str) -> str:
        """Sanitize credit request reason to prevent XSS"""
        if not reason:
            return ""
        
        # Strip HTML tags
        reason = re.sub(r'<[^>]*>', '', reason)
        
        # HTML escape special characters
        reason = html.escape(reason)
        
        # Remove script-like patterns
        reason = re.sub(r'javascript:', '', reason, flags=re.IGNORECASE)
        reason = re.sub(r'on\w+\s*=', '', reason, flags=re.IGNORECASE)
        
        # Limit length
        reason = reason[:500]
        
        # Remove excessive whitespace
        reason = ' '.join(reason.split())
        
        return reason
    
    def can_request_credits(self, userid: int) -> Dict:
        """Check if user can request credits (rate limiting)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check requests in last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM credit_requests 
            WHERE userid = ? AND created_at > ?
        """, (userid, yesterday))
        
        recent_requests = cursor.fetchone()[0]
        conn.close()
        
        if recent_requests >= 3:
            return {"can_request": False, "message": "Maximum 3 requests per day allowed"}
        
        return {"can_request": True, "message": ""}
    
    def create_request(self, userid: int, amount: int, reason: str) -> Dict:
        """Create new credit request"""
        # Rate limiting check
        rate_check = self.can_request_credits(userid)
        if not rate_check["can_request"]:
            return {"success": False, "message": rate_check["message"]}
        
        # Validate and sanitize inputs
        amount = max(1, min(100, int(amount)))  # Clamp between 1-100
        sanitized_reason = self.sanitize_reason(reason)
        
        if len(sanitized_reason.strip()) < 10:
            return {"success": False, "message": "Reason must be at least 10 characters"}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO credit_requests (userid, requested_amount, reason)
            VALUES (?, ?, ?)
        """, (userid, amount, sanitized_reason))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": "Credit request submitted successfully",
            "request_id": request_id
        }
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending credit requests for admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cr.id, cr.userid, u.name, cr.requested_amount, cr.reason, 
                   cr.created_at, cr.status
            FROM credit_requests cr
            LEFT JOIN users u ON cr.userid = u.userid
            WHERE cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """)
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                "id": row[0],
                "userid": row[1],
                "user_name": row[2] or "Unknown",
                "requested_amount": row[3],
                "reason": row[4],
                "created_at": row[5],
                "status": row[6]
            })
        
        conn.close()
        return requests
    
    def get_all_requests(self) -> List[Dict]:
        """Get all credit requests for admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cr.id, cr.userid, u.name, cr.requested_amount, cr.reason, 
                   cr.created_at, cr.status, cr.approved_amount, cr.admin_notes
            FROM credit_requests cr
            LEFT JOIN users u ON cr.userid = u.userid
            ORDER BY cr.created_at DESC
            LIMIT 100
        """)
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                "id": row[0],
                "userid": row[1],
                "user_name": row[2] or "Unknown",
                "requested_amount": row[3],
                "reason": row[4],
                "created_at": row[5],
                "status": row[6],
                "approved_amount": row[7],
                "admin_notes": row[8]
            })
        
        conn.close()
        return requests
    
    def approve_request(self, request_id: int, approved_amount: int, admin_notes: str, admin_userid: int) -> Dict:
        """Approve credit request and add credits"""
        from .credit_service import CreditService
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute("SELECT userid, requested_amount, status FROM credit_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()
        
        if not request:
            conn.close()
            return {"success": False, "message": "Request not found"}
        
        if request[2] != 'pending':
            conn.close()
            return {"success": False, "message": "Request already processed"}
        
        userid, requested_amount, status = request
        approved_amount = max(0, min(100, int(approved_amount)))
        
        # Update request status
        cursor.execute("""
            UPDATE credit_requests 
            SET status = 'approved', approved_amount = ?, admin_notes = ?, 
                approved_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (approved_amount, self.sanitize_reason(admin_notes), admin_userid, request_id))
        
        conn.commit()
        conn.close()
        
        # Add credits to user account
        if approved_amount > 0:
            credit_service = CreditService(self.db_path)
            credit_service.add_credits(
                userid, 
                approved_amount, 
                'admin_approval', 
                f'request_{request_id}',
                f'Credit request approved: {approved_amount} credits'
            )
        
        return {"success": True, "message": f"Request approved with {approved_amount} credits"}
    
    def reject_request(self, request_id: int, admin_notes: str, admin_userid: int) -> Dict:
        """Reject credit request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE credit_requests 
            SET status = 'rejected', admin_notes = ?, approved_by = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'pending'
        """, (self.sanitize_reason(admin_notes), admin_userid, request_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return {"success": False, "message": "Request not found or already processed"}
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Request rejected"}
    
    def get_user_requests(self, userid: int) -> List[Dict]:
        """Get user's credit request history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, requested_amount, reason, status, approved_amount, 
                   admin_notes, created_at, updated_at
            FROM credit_requests 
            WHERE userid = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (userid,))
        
        requests = []
        for row in cursor.fetchall():
            requests.append({
                "id": row[0],
                "requested_amount": row[1],
                "reason": row[2],
                "status": row[3],
                "approved_amount": row[4],
                "admin_notes": row[5],
                "created_at": row[6],
                "updated_at": row[7]
            })
        
        conn.close()
        return requests