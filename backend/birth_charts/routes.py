from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import traceback
from auth import get_current_user, User
from pydantic import BaseModel
from encryption_utils import EncryptionManager

try:
    encryptor = EncryptionManager()
except ValueError as e:
    print(f"WARNING: Encryption not configured: {e}")
    encryptor = None

router = APIRouter()

class ShareChartRequest(BaseModel):
    chart_id: int
    target_user_id: int

@router.get("/birth-charts")
async def get_birth_charts(search: str = "", limit: int = 50, current_user: User = Depends(get_current_user)):
    print(f"Search query: '{search}', Limit: {limit}")
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    if search.strip():
        search_pattern = f'%{search.strip()}%'
        print(f"Using search pattern: {search_pattern}")
        cursor.execute('''
            SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation FROM birth_charts 
            WHERE userid = ? AND name LIKE ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (current_user.userid, search_pattern, limit))
    else:
        print("No search query, returning all charts")
        cursor.execute('SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation FROM birth_charts WHERE userid = ? ORDER BY created_at DESC LIMIT ?', (current_user.userid, limit,))
    
    rows = cursor.fetchall()
    conn.close()

    charts = []
    for row in rows:
        if encryptor:
            chart = {
                'id': row[0],
                'userid': row[1],
                'name': encryptor.decrypt(row[2]),
                'date': encryptor.decrypt(row[3]),
                'time': encryptor.decrypt(row[4]),
                'latitude': float(encryptor.decrypt(str(row[5]))),
                'longitude': float(encryptor.decrypt(str(row[6]))),
                'timezone': row[7],
                'created_at': row[8],
                'place': encryptor.decrypt(row[9] or ''),
                'gender': row[10] or '',
                'relation': row[11] or 'other'
            }
        else:
            chart = {
                'id': row[0],
                'userid': row[1],
                'name': row[2],
                'date': row[3],
                'time': row[4],
                'latitude': row[5],
                'longitude': row[6],
                'timezone': row[7],
                'created_at': row[8],
                'place': row[9] or '',
                'gender': row[10] or '',
                'relation': row[11] or 'other'
            }
        charts.append(chart)
    
    return {'charts': charts}

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
@router.put("/birth-charts/{chart_id}")
async def update_birth_chart(chart_id: int, birth_data: dict, current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        # Verify chart belongs to user
        cursor.execute('SELECT id FROM birth_charts WHERE id=? AND userid=?', (chart_id, current_user.userid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        if encryptor:
            enc_name = encryptor.encrypt(birth_data['name'])
            enc_date = encryptor.encrypt(birth_data['date'])
            enc_time = encryptor.encrypt(birth_data['time'])
            enc_lat = encryptor.encrypt(str(birth_data['latitude']))
            enc_lon = encryptor.encrypt(str(birth_data['longitude']))
            enc_place = encryptor.encrypt(birth_data.get('place', ''))
        else:
            enc_name, enc_date, enc_time = birth_data['name'], birth_data['date'], birth_data['time']
            enc_lat, enc_lon, enc_place = str(birth_data['latitude']), str(birth_data['longitude']), birth_data.get('place', '')

        cursor.execute('''
            UPDATE birth_charts 
            SET name=?, date=?, time=?, latitude=?, longitude=?, timezone=?, place=?, gender=?
            WHERE id=? AND userid=?
        ''', (enc_name, enc_date, enc_time, enc_lat, enc_lon, 
            birth_data.get('timezone', 'UTC+0'), enc_place, birth_data.get('gender', ''), chart_id, current_user.userid))

        conn.commit()
        return {"message": "Chart updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update chart: {str(e)}")
    finally:
        conn.close()

@router.delete("/birth-charts/{chart_id}")
async def delete_birth_chart(chart_id: int, current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    try:
        # Verify chart belongs to user
        cursor.execute('SELECT id FROM birth_charts WHERE id=? AND userid=?', (chart_id, current_user.userid))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        cursor.execute('DELETE FROM birth_charts WHERE id=? AND userid=?', (chart_id, current_user.userid))
        conn.commit()
        return {"message": "Chart deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete chart: {str(e)}")
    finally:
        conn.close()