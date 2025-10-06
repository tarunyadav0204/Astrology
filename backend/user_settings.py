from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3
import json

router = APIRouter(prefix="/user-settings", tags=["User Settings"])

class UserSettings(BaseModel):
    node_type: str = "mean"  # "mean" or "true"
    default_chart_style: str = "north"  # "north" or "south"

def init_settings_table():
    """Initialize user_settings table"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (userid),
            UNIQUE(user_id, setting_key)
        )
    """)
    
    conn.commit()
    conn.close()

# Initialize table on import
init_settings_table()

@router.get("/settings/{phone}")
async def get_user_settings(phone: str):
    """Get user settings"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT userid FROM users WHERE phone = ?", (phone,))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_result[0]
        
        # Get all settings for user
        cursor.execute("""
            SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?
        """, (user_id,))
        
        settings_rows = cursor.fetchall()
        conn.close()
        
        # Convert to dict
        settings = {}
        for key, value in settings_rows:
            try:
                settings[key] = json.loads(value)
            except:
                settings[key] = value
        
        # Return with defaults if no settings found
        return {
            "node_type": settings.get("node_type", "mean"),
            "default_chart_style": settings.get("default_chart_style", "north")
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings/{phone}")
async def update_user_settings(phone: str, settings: UserSettings):
    """Update user settings"""
    try:
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT userid FROM users WHERE phone = ?", (phone,))
        user_result = cursor.fetchone()
        if not user_result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = user_result[0]
        
        # Update each setting
        for key, value in settings.dict().items():
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings (user_id, setting_key, setting_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, key, json.dumps(value)))
        
        conn.commit()
        conn.close()
        
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))