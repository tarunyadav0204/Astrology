import sqlite3
import json
import hashlib
from typing import Dict, List, Optional
from datetime import datetime

class PhysicalTraitsCache:
    def __init__(self, db_path: str = "astrology.db"):
        self.db_path = db_path
    

    
    def get_cached_traits(self, birth_chart_id: int) -> Optional[List[Dict]]:
        """Retrieve cached traits for this birth chart."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT traits_data FROM physical_traits_cache WHERE birth_chart_id = ?",
                (birth_chart_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
        return None
    
    def cache_traits(self, birth_chart_id: int, traits: List[Dict]):
        """Cache traits for this birth chart."""
        traits_json = json.dumps(traits)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO physical_traits_cache (birth_chart_id, traits_data) VALUES (?, ?)",
                (birth_chart_id, traits_json)
            )
            conn.commit()
    
    def has_feedback(self, birth_chart_id: int) -> bool:
        """Check if feedback already exists for this chart."""
        if not birth_chart_id:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT user_feedback FROM physical_traits_cache WHERE birth_chart_id = ? AND user_feedback IS NOT NULL",
                (birth_chart_id,)
            )
            return cursor.fetchone() is not None
    
    def update_feedback(self, birth_chart_id: int, feedback: str):
        """Update user feedback for cached traits."""
        if not birth_chart_id:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO physical_traits_cache (birth_chart_id, traits_data, user_feedback) VALUES (?, COALESCE((SELECT traits_data FROM physical_traits_cache WHERE birth_chart_id = ?), '[]'), ?)",
                (birth_chart_id, birth_chart_id, feedback)
            )
            conn.commit()