from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from datetime import datetime
from auth import get_current_user, User

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

router = APIRouter(prefix="/chat/feedback", tags=["chat_feedback"])

@router.post("/submit")
async def submit_feedback(request: FeedbackRequest, current_user: User = Depends(get_current_user)):
    """Submit feedback for a chat message"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Check if feedback already exists for this user and message
        cursor.execute(
            "SELECT id FROM message_feedback WHERE message_id = ?",
            (request.message_id,)
        )
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing feedback
            cursor.execute(
                "UPDATE message_feedback SET rating = ?, comment = ?, created_at = ? WHERE message_id = ?",
                (request.rating, request.comment, datetime.now(), request.message_id)
            )
        else:
            # Insert new feedback
            cursor.execute(
                "INSERT INTO message_feedback (message_id, rating, comment) VALUES (?, ?, ?)",
                (request.message_id, request.rating, request.comment)
            )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        print(f"❌ Feedback submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/stats")
async def get_feedback_stats(current_user: User = Depends(get_current_user)):
    """Get feedback statistics (admin only)"""
    print(f"📊 Feedback stats request from user: {current_user.phone if current_user else 'None'}, role: {current_user.role if current_user else 'None'}")
    
    if current_user.role != 'admin':
        print(f"❌ Access denied: User {current_user.phone} with role '{current_user.role}' attempted to access admin stats")
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get overall stats
        cursor.execute("SELECT COUNT(*), AVG(rating) FROM message_feedback")
        total_feedback, avg_rating = cursor.fetchone()
        
        # Get rating distribution
        cursor.execute("SELECT rating, COUNT(*) FROM message_feedback GROUP BY rating ORDER BY rating")
        rating_distribution = dict(cursor.fetchall())
        
        # Get recent feedback with user names in single query
        cursor.execute('''
            SELECT mf.rating, mf.comment, mf.created_at, COALESCE(u.name, 'Unknown User') as user_name
            FROM message_feedback mf
            LEFT JOIN chat_messages cm ON CAST(mf.message_id AS INTEGER) = cm.message_id
            LEFT JOIN chat_sessions cs ON cm.session_id = cs.session_id
            LEFT JOIN users u ON cs.user_id = u.userid
            ORDER BY mf.created_at DESC
            LIMIT 10
        ''')
        recent_feedback = cursor.fetchall()
        
        feedback_with_users = [
            {
                "rating": row[0],
                "comment": row[1] or '',
                "created_at": row[2],
                "user_name": row[3]
            }
            for row in recent_feedback
        ]
        
        conn.close()
        
        print(f"✅ Feedback stats retrieved successfully: {total_feedback} total, {len(feedback_with_users)} recent")
        return {
            "total_feedback": total_feedback or 0,
            "average_rating": round(avg_rating or 0, 2),
            "rating_distribution": rating_distribution,
            "recent_feedback": feedback_with_users
        }
        
    except Exception as e:
        print(f"❌ Feedback stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback stats: {str(e)}")

@router.get("/user-feedback")
async def get_user_feedback(current_user: User = Depends(get_current_user)):
    """Get feedback submitted by current user"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_id, rating, comment, created_at
            FROM message_feedback
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        
        feedback_list = cursor.fetchall()
        conn.close()
        
        return {
            "feedback": [
                {
                    "message_id": row[0],
                    "rating": row[1],
                    "comment": row[2],
                    "created_at": row[3]
                }
                for row in feedback_list
            ]
        }
        
    except Exception as e:
        print(f"❌ User feedback error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get user feedback: {str(e)}")