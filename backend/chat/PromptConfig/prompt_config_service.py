"""
Prompt Configuration Service
Handles database operations for dynamic prompt management
"""

import json
from typing import Dict, List, Optional
from datetime import datetime

from db import get_conn, execute

class PromptConfigService:
    """Service for managing prompt configurations"""
    
    def __init__(self, db_path: str = 'astrology.db'):
        # db_path kept for backward compatibility but ignored; we now use shared Postgres connection
        self.db_path = db_path
    
    def get_category_config(self, category_key: str) -> Optional[Dict]:
        """Get configuration for a specific category"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT category_key, category_name, required_modules, required_data_fields,
                       optional_data_fields, max_transit_activations, is_active
                FROM prompt_category_config
                WHERE category_key = %s AND is_active = TRUE
                """,
                (category_key,),
            )
            row = cur.fetchone()
        
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
        if not module_keys:
            return ""
        placeholders = ",".join(["%s"] * len(module_keys))
        with get_conn() as conn:
            cur = execute(
                conn,
                f"""
                SELECT instruction_text
                FROM prompt_instruction_modules
                WHERE module_key IN ({placeholders}) AND is_active = TRUE
                ORDER BY priority DESC
                """,
                tuple(module_keys),
            )
            rows = cur.fetchall() or []
        
        return '\n\n'.join(row[0] for row in rows)
    
    def log_performance(self, category_key: str, instruction_size: int, 
                       context_size: int, total_prompt_size: int,
                       response_time: float, success: bool, error_message: str = None):
        """Log performance metrics"""
        with get_conn() as conn:
            execute(
                conn,
                """
                INSERT INTO prompt_performance_log
                    (category_key, instruction_size, context_size, total_prompt_size,
                     response_time_seconds, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    category_key,
                    instruction_size,
                    context_size,
                    total_prompt_size,
                    response_time,
                    success,
                    error_message,
                ),
            )
            conn.commit()

    def get_all_categories(self) -> List[Dict]:
        """Get all active categories"""
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT category_key, category_name, required_modules, required_data_fields,
                       max_transit_activations
                FROM prompt_category_config
                WHERE is_active = TRUE
                ORDER BY category_name
                """,
            )
            rows = cur.fetchall() or []

        return [
            {
                "category_key": row[0],
                "category_name": row[1],
                "required_modules": json.loads(row[2]),
                "required_data_fields": json.loads(row[3]),
                "max_transit_activations": row[4],
            }
            for row in rows
        ]
