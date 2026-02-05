from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import logging
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class FactCreate(BaseModel):
    birth_chart_id: int
    category: str
    fact: str
    confidence: Optional[float] = 1.0

class FactUpdate(BaseModel):
    category: Optional[str] = None
    fact: Optional[str] = None
    confidence: Optional[float] = None

def get_db_connection():
    conn = sqlite3.connect('astrology.db')
    conn.row_factory = sqlite3.Row
    return conn

def verify_chart_ownership(birth_chart_id: int, user_id: int):
    """Verify user owns the birth chart"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userid FROM birth_charts WHERE id = ?", (birth_chart_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Birth chart not found")
    if result['userid'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

@router.get("/facts/{birth_chart_id}")
async def get_facts(birth_chart_id: int, current_user: dict = Depends(get_current_user)):
    """Get all facts for a birth chart"""
    try:
        verify_chart_ownership(birth_chart_id, current_user.userid)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category, fact, confidence, extracted_at
            FROM user_facts
            WHERE birth_chart_id = ?
            ORDER BY category, extracted_at DESC
        """, (birth_chart_id,))
        
        facts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {"success": True, "facts": facts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching facts for chart {birth_chart_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch facts")

@router.post("/facts")
async def add_fact(fact_data: FactCreate, current_user: dict = Depends(get_current_user)):
    """Add a new fact"""
    conn = None
    try:
        verify_chart_ownership(fact_data.birth_chart_id, current_user.userid)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_facts (birth_chart_id, category, fact, confidence)
            VALUES (?, ?, ?, ?)
        """, (fact_data.birth_chart_id, fact_data.category, fact_data.fact, fact_data.confidence))
        
        fact_id = cursor.lastrowid
        conn.commit()
        
        return {"success": True, "fact_id": fact_id, "message": "Fact added"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding fact for chart {fact_data.birth_chart_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add fact")
    finally:
        if conn:
            conn.close()

@router.put("/facts/{fact_id}")
async def update_fact(fact_id: int, fact_data: FactUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing fact"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("""
            SELECT bc.userid FROM user_facts uf
            JOIN birth_charts bc ON bc.id = uf.birth_chart_id
            WHERE uf.id = ?
        """, (fact_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Fact not found")
        if result['userid'] != current_user.userid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build update query
        updates = []
        params = []
        if fact_data.category is not None:
            updates.append("category = ?")
            params.append(fact_data.category)
        if fact_data.fact is not None:
            updates.append("fact = ?")
            params.append(fact_data.fact)
        if fact_data.confidence is not None:
            updates.append("confidence = ?")
            params.append(fact_data.confidence)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(fact_id)
        cursor.execute(f"UPDATE user_facts SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        
        return {"success": True, "message": "Fact updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating fact {fact_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update fact")
    finally:
        if conn:
            conn.close()

@router.delete("/facts/{fact_id}")
async def delete_fact(fact_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a fact"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute("""
            SELECT bc.userid FROM user_facts uf
            JOIN birth_charts bc ON bc.id = uf.birth_chart_id
            WHERE uf.id = ?
        """, (fact_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Fact not found")
        if result['userid'] != current_user.userid:
            raise HTTPException(status_code=403, detail="Access denied")
        
        cursor.execute("DELETE FROM user_facts WHERE id = ?", (fact_id,))
        conn.commit()
        
        return {"success": True, "message": "Fact deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting fact {fact_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete fact")
    finally:
        if conn:
            conn.close()
