from fastapi import APIRouter, Depends, HTTPException
import traceback
from auth import get_current_user, User
from pydantic import BaseModel
from encryption_utils import EncryptionManager
from db import get_conn, execute

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
async def get_birth_charts(
    search: str = "",
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    print(f"Search query: '{search}', Limit: {limit}, Offset: {offset}")
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    with get_conn() as conn:
        # Name is encrypted at rest in most environments. For encrypted mode, SQL LIKE
        # cannot search plaintext, so we decrypt+filter in Python for search queries.
        if search.strip() and encryptor:
            cur = execute(
                conn,
                """
                SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation
                FROM birth_charts
                WHERE userid = %s
                ORDER BY created_at DESC
                """,
                (current_user.userid,),
            )
            all_rows = cur.fetchall() or []
            needle = search.strip().lower()
            filtered_rows = []
            for row in all_rows:
                try:
                    dec_name = encryptor.decrypt(row[2]) if row[2] else ""
                    if needle in dec_name.lower():
                        filtered_rows.append(row)
                except Exception:
                    # Skip malformed encrypted rows in search mode.
                    continue
            total = len(filtered_rows)
            rows = filtered_rows[offset:offset + limit]
        elif search.strip():
            search_pattern = f"%{search.strip()}%"
            cur = execute(
                conn,
                """
                SELECT COUNT(*) FROM birth_charts
                WHERE userid = %s AND name ILIKE %s
                """,
                (current_user.userid, search_pattern),
            )
            total = int(cur.fetchone()[0] or 0)
            cur = execute(
                conn,
                """
                SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation
                FROM birth_charts
                WHERE userid = %s AND name ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (current_user.userid, search_pattern, limit, offset),
            )
            rows = cur.fetchall() or []
        else:
            cur = execute(
                conn,
                """
                SELECT COUNT(*) FROM birth_charts
                WHERE userid = %s
                """,
                (current_user.userid,),
            )
            total = int(cur.fetchone()[0] or 0)
            cur = execute(
                conn,
                """
                SELECT id, userid, name, date, time, latitude, longitude, timezone, created_at, place, gender, relation
                FROM birth_charts
                WHERE userid = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (current_user.userid, limit, offset),
            )
            rows = cur.fetchall() or []

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
    
    return {
        'charts': charts,
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + len(charts)) < total,
    }

@router.put("/birth-charts/{chart_id}/set-as-self")
async def set_chart_as_self(chart_id: int, current_user: User = Depends(get_current_user)):
    """
    Set a birth chart as 'self' and clear all other 'self' relations for the user.
    This ensures only one chart can be marked as 'self' at a time.
    """
    conn = None
    try:
        conn_ctx = get_conn()
        conn = conn_ctx.__enter__()
        cursor = conn.cursor()

        print(f"🔍 [SET_SELF_DEBUG] Setting chart {chart_id} as self for user {current_user.userid}")
        
        # Verify the chart belongs to the current user
        cursor.execute(
            "SELECT id, name FROM birth_charts WHERE id=%s AND userid=%s",
            (chart_id, current_user.userid),
        )
        result = cursor.fetchone()
        print(f"🔍 [SET_SELF_DEBUG] Chart verification result: {result}")
        
        if not result:
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        # Check current self charts before clearing
        cursor.execute(
            'SELECT id, name FROM birth_charts WHERE userid=%s AND relation=%s',
            (current_user.userid, "self"),
        )
        current_self_charts = cursor.fetchall()
        print(f"🔍 [SET_SELF_DEBUG] Current self charts before clearing: {current_self_charts}")
        
        # 1. Clear all existing 'self' relations for this user
        cursor.execute(
            """
            UPDATE birth_charts
            SET relation='other'
            WHERE userid=%s AND relation='self'
            """,
            (current_user.userid,),
        )
        print(f"🔍 [SET_SELF_DEBUG] Cleared {cursor.rowcount} existing self relations")
        
        # 2. Set the specified chart as 'self'
        cursor.execute(
            """
            UPDATE birth_charts
            SET relation='self'
            WHERE id=%s AND userid=%s
            """,
            (chart_id, current_user.userid),
        )
        print(f"🔍 [SET_SELF_DEBUG] Set chart {chart_id} as self, rows affected: {cursor.rowcount}")
        
        # Verify the final state
        cursor.execute(
            'SELECT id, name, relation FROM birth_charts WHERE userid=%s AND relation=%s',
            (current_user.userid, "self"),
        )
        final_self_charts = cursor.fetchall()
        print(f"✅ [SET_SELF_DEBUG] Final self charts after update: {final_self_charts}")
        
        # Commit transaction
        conn.commit()
        return {"message": "Chart set as self successfully", "chart_id": chart_id}
    
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error in set_chart_as_self: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update chart: {str(e)}")
    finally:
        if conn:
            conn_ctx.__exit__(None, None, None)

@router.get("/users/search")
async def search_users(query: str, current_user: User = Depends(get_current_user)):
    """Search users by name or phone (minimum 4 characters)"""
    if len(query) < 4:
        return {"users": []}
    search_pattern = f"%{query}%"
    digits_only = "".join(c for c in query if c.isdigit())
    digit_pattern = f"%{digits_only}%" if len(digits_only) >= 4 else ""
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT userid, name, phone FROM users
            WHERE (
                name ILIKE %s OR phone LIKE %s
                OR (
                    CASE WHEN char_length(%s) >= 4
                    THEN regexp_replace(COALESCE(phone, ''), '[^0-9]', '', 'g') LIKE %s
                    ELSE FALSE
                    END
                )
            ) AND userid != %s
            LIMIT 20
            """,
            (
                search_pattern,
                search_pattern,
                digits_only,
                digit_pattern,
                current_user.userid,
            ),
        )
        rows = cursor.fetchall() or []

    users = []
    for row in rows:
        phone = row[2] or ""
        users.append(
            {
                "userid": row[0],
                "name": row[1],
                "phone": phone[-4:] if phone else "",
            }
        )
    return {"users": users}

@router.post("/charts/share")
async def share_chart(request: ShareChartRequest, current_user: User = Depends(get_current_user)):
    """Share a birth chart with another user by creating a copy"""
    conn = None
    try:
        conn_ctx = get_conn()
        conn = conn_ctx.__enter__()
        cursor = conn.cursor()

        # Verify the chart belongs to current user
        cursor.execute(
            "SELECT id FROM birth_charts WHERE id=%s AND userid=%s",
            (request.chart_id, current_user.userid),
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        # Verify target user exists
        cursor.execute(
            "SELECT userid FROM users WHERE userid=%s", (request.target_user_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Target user not found")
        
        # Copy encrypted data as-is to target user
        cursor.execute(
            """
            INSERT INTO birth_charts (userid, name, date, time, latitude, longitude, timezone, place, gender, relation)
            SELECT %s, name, date, time, latitude, longitude, timezone, place, gender, 'shared'
            FROM birth_charts WHERE id=%s
            RETURNING id
            """,
            (request.target_user_id, request.chart_id),
        )
        new_row = cursor.fetchone()
        conn.commit()
        new_chart_id = new_row[0] if new_row else None
        
        return {
            "message": "Chart shared successfully",
            "shared_chart_id": new_chart_id
        }
    
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to share chart: {str(e)}")
    finally:
        if conn:
            conn_ctx.__exit__(None, None, None)
@router.put("/birth-charts/{chart_id}")
async def update_birth_chart(chart_id: int, birth_data: dict, current_user: User = Depends(get_current_user)):
    conn = None
    try:
        conn_ctx = get_conn()
        conn = conn_ctx.__enter__()
        cursor = conn.cursor()

        # Verify chart belongs to user
        cursor.execute(
            "SELECT id FROM birth_charts WHERE id=%s AND userid=%s",
            (chart_id, current_user.userid),
        )
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

        # Keep timezone behavior consistent with chart creation:
        # if client doesn't send timezone, derive it from coordinates.
        timezone_value = birth_data.get("timezone")
        if not timezone_value:
            try:
                from utils.timezone_service import get_timezone_from_coordinates
                timezone_value = get_timezone_from_coordinates(
                    float(birth_data["latitude"]),
                    float(birth_data["longitude"]),
                )
            except Exception:
                timezone_value = "UTC+0"

        cursor.execute(
            """
            UPDATE birth_charts
            SET name=%s, date=%s, time=%s, latitude=%s, longitude=%s, timezone=%s, place=%s, gender=%s
            WHERE id=%s AND userid=%s
            """,
            (
                enc_name,
                enc_date,
                enc_time,
                enc_lat,
                enc_lon,
                timezone_value,
                enc_place,
                birth_data.get("gender", ""),
                chart_id,
                current_user.userid,
            ),
        )

        conn.commit()
        return {"message": "Chart updated successfully"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update chart: {str(e)}")
    finally:
        if conn:
            conn_ctx.__exit__(None, None, None)

@router.delete("/birth-charts/{chart_id}")
async def delete_birth_chart(chart_id: int, current_user: User = Depends(get_current_user)):
    conn = None
    try:
        conn_ctx = get_conn()
        conn = conn_ctx.__enter__()
        cursor = conn.cursor()

        # Verify chart belongs to user
        cursor.execute(
            "SELECT id FROM birth_charts WHERE id=%s AND userid=%s",
            (chart_id, current_user.userid),
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chart not found or access denied")
        
        cursor.execute(
            "DELETE FROM birth_charts WHERE id=%s AND userid=%s",
            (chart_id, current_user.userid),
        )
        conn.commit()
        return {"message": "Chart deleted successfully"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete chart: {str(e)}")
    finally:
        if conn:
            conn_ctx.__exit__(None, None, None)