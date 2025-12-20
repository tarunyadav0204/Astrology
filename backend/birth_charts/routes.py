from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import traceback
from auth import get_current_user, User
from pydantic import BaseModel

router = APIRouter()

class ShareChartRequest(BaseModel):
    chart_id: int
    target_user_id: int

@router.put("/birth-charts/{chart_id}/set-as-self")
async def set_chart_as_self(chart_id: int, current_user: User = Depends(get_current_user)):
    """
    Set a birth chart as 'self' and clear all other 'self' relations for the user.
    This ensures only one chart can be marked as 'self' at a time.
    """
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        print(f"Setting chart {chart_id} as self for user {current_user.userid}")
        
        # Verify the chart belongs to the current user
        cursor.execute('SELECT id FROM birth_charts WHERE id=? AND userid=?', (chart_id, current_user.userid))
        result = cursor.fetchone()
        print(f"Chart verification result: {result}")
        
        if not result:
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        # 1. Clear all existing 'self' relations for this user
        cursor.execute('''
            UPDATE birth_charts 
            SET relation='other' 
            WHERE userid=? AND relation='self'
        ''', (current_user.userid,))
        print(f"Cleared {cursor.rowcount} existing self relations")
        
        # 2. Set the specified chart as 'self'
        cursor.execute('''
            UPDATE birth_charts 
            SET relation='self' 
            WHERE id=? AND userid=?
        ''', (chart_id, current_user.userid))
        print(f"Set chart {chart_id} as self, rows affected: {cursor.rowcount}")
        
        # Commit transaction
        conn.commit()
        return {"message": "Chart set as self successfully", "chart_id": chart_id}
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error in set_chart_as_self: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update chart: {str(e)}")
    finally:
        conn.close()

@router.get("/users/search")
async def search_users(query: str, current_user: User = Depends(get_current_user)):
    """Search users by name or phone (minimum 4 characters)"""
    if len(query) < 4:
        return {"users": []}
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    search_pattern = f'%{query}%'
    cursor.execute('''
        SELECT userid, name, phone FROM users 
        WHERE (name LIKE ? OR phone LIKE ?) AND userid != ?
        LIMIT 20
    ''', (search_pattern, search_pattern, current_user.userid))
    
    users = []
    for row in cursor.fetchall():
        users.append({
            'userid': row[0],
            'name': row[1],
            'phone': row[2][-4:]  # Only show last 4 digits for privacy
        })
    
    conn.close()
    return {"users": users}

@router.post("/charts/share")
async def share_chart(request: ShareChartRequest, current_user: User = Depends(get_current_user)):
    """Share a birth chart with another user by creating a copy"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        # Verify the chart belongs to current user
        cursor.execute('SELECT id FROM birth_charts WHERE id=? AND userid=?', 
                      (request.chart_id, current_user.userid))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        # Verify target user exists
        cursor.execute('SELECT userid FROM users WHERE userid=?', (request.target_user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target user not found")
        
        # Copy encrypted data as-is to target user
        cursor.execute('''
            INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
            SELECT ?, name, date, time, latitude, longitude, timezone, place, gender, 'shared'
            FROM birth_charts WHERE id=?
        ''', (request.target_user_id, request.chart_id))
        
        conn.commit()
        new_chart_id = cursor.lastrowid
        
        return {
            "message": "Chart shared successfully",
            "shared_chart_id": new_chart_id
        }
    
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to share chart: {str(e)}")
    finally:
        conn.close()
