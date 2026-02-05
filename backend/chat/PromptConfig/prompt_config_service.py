"""
Prompt Configuration Service
Handles database operations for dynamic prompt management
"""

import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime

class PromptConfigService:
    """Service for managing prompt configurations"""
    
    def __init__(self, db_path: str = 'astrology.db'):
        self.db_path = db_path
    
    def get_category_config(self, category_key: str) -> Optional[Dict]:
        """Get configuration for a specific category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category_key, category_name, required_modules, required_data_fields,
                   optional_data_fields, max_transit_activations, is_active
            FROM prompt_category_config
            WHERE category_key = ? AND is_active = 1
        ''', (category_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'category_key': row[0],
            'category_name': row[1],
            'required_modules': json.loads(row[2]),
            'required_data_fields': json.loads(row[3]),
            'optional_data_fields': json.loads(row[4]) if row[4] else [],
            'max_transit_activations': row[5],
            'is_active': bool(row[6])
        }
    
    def get_instruction_modules(self, module_keys: List[str]) -> str:
        """Get assembled instruction text from module keys"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(module_keys))
        cursor.execute(f'''
            SELECT instruction_text
            FROM prompt_instruction_modules
            WHERE module_key IN ({placeholders}) AND is_active = 1
            ORDER BY priority DESC
        ''', module_keys)
        
        rows = cursor.fetchall()
        conn.close()
        
        return '\n\n'.join(row[0] for row in rows)
    
    def log_performance(self, category_key: str, instruction_size: int, 
                       context_size: int, total_prompt_size: int,
                       response_time: float, success: bool, error_message: str = None):
        """Log performance metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prompt_performance_log 
            (category_key, instruction_size, context_size, total_prompt_size,
             response_time_seconds, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (category_key, instruction_size, context_size, total_prompt_size,
              response_time, success, error_message))
        
        conn.commit()
        conn.close()
    
    def get_all_categories(self) -> List[Dict]:
        """Get all active categories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category_key, category_name, required_modules, required_data_fields,
                   max_transit_activations
            FROM prompt_category_config
            WHERE is_active = 1
            ORDER BY category_name
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'category_key': row[0],
            'category_name': row[1],
            'required_modules': json.loads(row[2]),
            'required_data_fields': json.loads(row[3]),
            'max_transit_activations': row[4]
        } for row in rows]
