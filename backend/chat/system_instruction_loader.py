import sqlite3
import json
from typing import List, Optional

class SystemInstructionLoader:
    """Loads system instructions from database based on category configuration"""
    
    def __init__(self, db_path: str = 'astrology.db'):
        self.db_path = db_path
    
    def get_instructions_for_category(self, category_key: str, tier_key: str = 'normal') -> str:
        """Get assembled system instructions for a specific category and tier"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Get required modules for this category and tier
            cursor.execute("""
                SELECT required_modules
                FROM prompt_category_config
                WHERE category_key = ? AND tier_key = ?
            """, (category_key, tier_key))
            
            result = cursor.fetchone()
            if not result or not result['required_modules']:
                # Fallback to all active modules if no config
                return self._get_all_active_instructions()
            
            # Parse required modules
            try:
                required_module_keys = json.loads(result['required_modules'])
            except:
                required_module_keys = result['required_modules'].split(',')
            
            # Get instruction texts for required modules
            placeholders = ','.join('?' * len(required_module_keys))
            cursor.execute(f"""
                SELECT instruction_text
                FROM prompt_instruction_modules
                WHERE module_key IN ({placeholders})
                AND is_active = 1
                ORDER BY priority
            """, required_module_keys)
            
            modules = cursor.fetchall()
            
            # Assemble instructions
            instructions = '\n\n'.join([row['instruction_text'] for row in modules])
            
            return instructions if instructions else self._get_all_active_instructions()
            
        finally:
            conn.close()
    
    def _get_all_active_instructions(self) -> str:
        """Fallback: Get all active instructions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT instruction_text
                FROM prompt_instruction_modules
                WHERE is_active = 1
                ORDER BY priority
            """)
            
            modules = cursor.fetchall()
            return '\n\n'.join([row['instruction_text'] for row in modules])
            
        finally:
            conn.close()
