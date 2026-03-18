from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from auth import get_current_user, User
from db import get_conn, execute

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

router = APIRouter(prefix="/chat/feedback", tags=["chat_feedback"])

@router.post("/submit")
async def submit_feedback(request: FeedbackRequest, current_user: User = Depends(get_current_user)):
    """Submit feedback for a chat message"""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                "SELECT id FROM message_feedback WHERE message_id = %s",
                (request.message_id,),
            )
            existing = cur.fetchone()

            if existing:
                execute(
                    conn,
                    """
                    UPDATE message_feedback
                    SET rating = %s, comment = %s, created_at = %s
                    WHERE message_id = %s
                    """,
                    (request.rating, request.comment, datetime.now(), request.message_id),
                )
            else:
                execute(
                    conn,
                    """
                    INSERT INTO message_feedback (message_id, rating, comment, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (request.message_id, request.rating, request.comment, datetime.now()),
                )

        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        print(f"❌ Feedback submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/stats")
async def get_feedback_stats(
    page: int = 1,
    limit: int = 10,
    username: Optional[str] = None,
    rating: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get feedback statistics with pagination and search (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        with get_conn() as conn:
            cur = execute(conn, "SELECT COUNT(*), AVG(rating) FROM message_feedback", ())
            total_feedback, avg_rating = cur.fetchone() or (0, None)

            cur = execute(
                conn,
                "SELECT rating, COUNT(*) FROM message_feedback GROUP BY rating ORDER BY rating",
                (),
            )
            rating_distribution = {row[0]: row[1] for row in (cur.fetchall() or [])}

            where_conditions = []
            params = []

            if username:
                where_conditions.append(
                    "LOWER(COALESCE(u.name, 'Unknown User')) LIKE LOWER(%s)"
                )
                params.append(f"%{username}%")

            if rating:
                where_conditions.append("mf.rating = %s")
                params.append(rating)

            where_clause = " AND ".join(where_conditions)
            if where_clause:
                where_clause = "WHERE " + where_clause

            count_query = f"""
                SELECT COUNT(*)
                FROM message_feedback mf
                LEFT JOIN chat_messages cm ON mf.message_id = cm.message_id::text
                LEFT JOIN chat_sessions cs ON cm.session_id = cs.session_id
                LEFT JOIN users u ON cs.user_id = u.userid
                {where_clause}
            """
            cur = execute(conn, count_query, tuple(params))
            total_count = (cur.fetchone() or [0])[0]

            offset = (page - 1) * limit

            feedback_query = f"""
                SELECT mf.rating, mf.comment, mf.created_at, COALESCE(u.name, 'Unknown User') as user_name
                FROM message_feedback mf
                LEFT JOIN chat_messages cm ON mf.message_id = cm.message_id::text
                LEFT JOIN chat_sessions cs ON cm.session_id = cs.session_id
                LEFT JOIN users u ON cs.user_id = u.userid
                {where_clause}
                ORDER BY mf.created_at DESC
                LIMIT %s OFFSET %s
            """
            cur = execute(conn, feedback_query, tuple(params) + (limit, offset))
            feedback_results = cur.fetchall() or []

        feedback_with_users = [
            {
                "rating": row[0],
                "comment": row[1] or '',
                "created_at": row[2],
                "user_name": row[3]
            }
            for row in feedback_results
        ]

        return {
            "total_feedback": total_feedback or 0,
            "average_rating": round(avg_rating or 0, 2),
            "rating_distribution": rating_distribution,
            "feedback": feedback_with_users,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
        
    except Exception as e:
        print(f"❌ Feedback stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get feedback stats: {str(e)}")

@router.get("/user-feedback")
async def get_user_feedback(current_user: User = Depends(get_current_user)):
    """Get feedback submitted by current user"""
    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT message_id, rating, comment, created_at
                FROM message_feedback
                ORDER BY created_at DESC
                LIMIT 20
                """,
                (),
            )
            feedback_list = cur.fetchall() or []

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