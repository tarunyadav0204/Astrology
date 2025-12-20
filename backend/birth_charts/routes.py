from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import traceback
from auth import get_current_user, User

router = APIRouter()

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
