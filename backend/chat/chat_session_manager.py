import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

class ChatSessionManager:
    """Manages chat conversation history and sessions"""
    
    def __init__(self):
        self._init_chat_table()
    
    def _init_chat_table(self):
        """Initialize chat conversations table"""
        from db import get_conn, execute
        with get_conn() as conn:
            execute(conn, '''
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    id SERIAL PRIMARY KEY,
                    birth_hash TEXT,
                    conversation_data TEXT,
                    clarification_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_conversation_history(self, birth_hash: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for birth data"""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(
                conn,
                'SELECT conversation_data FROM chat_conversations WHERE birth_hash = ? ORDER BY updated_at DESC LIMIT ?',
                (birth_hash, 1),
            )
            result = cursor.fetchone()
        
        if result:
            conversation_data = json.loads(result[0])
            messages = conversation_data.get('messages', [])
            # Return messages in {question, response} format, sorted by timestamp
            # Sort by timestamp to ensure correct order
            sorted_messages = sorted(messages, key=lambda x: x.get('timestamp', ''))
            return sorted_messages[-limit:] if len(sorted_messages) > limit else sorted_messages
        
        return []
    
    def add_message(self, birth_hash: str, user_question: str, ai_response: str):
        """Add message to conversation history"""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = conn.cursor()
            # Get existing conversation
            execute(conn, 'SELECT conversation_data FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
            result = cursor.fetchone()
        
        if result:
            conversation_data = json.loads(result[0])
        else:
            conversation_data = {'messages': []}
        
        # Add new message
        conversation_data['messages'].append({
            'timestamp': datetime.now().isoformat(),
            'question': user_question,
            'response': ai_response
        })
        
        # Keep only last 50 messages
        if len(conversation_data['messages']) > 50:
            conversation_data['messages'] = conversation_data['messages'][-50:]
        
            # Update or insert
            if result:
                execute(
                    conn,
                    'UPDATE chat_conversations SET conversation_data = ?, updated_at = ? WHERE birth_hash = ?',
                    (json.dumps(conversation_data), datetime.now().isoformat(), birth_hash),
                )
            else:
                execute(
                    conn,
                    'INSERT INTO chat_conversations (birth_hash, conversation_data) VALUES (?, ?)',
                    (birth_hash, json.dumps(conversation_data)),
                )
            conn.commit()
    
    def create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def clear_conversation(self, birth_hash: str):
        """Clear conversation history for birth data"""
        from db import get_conn, execute
        with get_conn() as conn:
            execute(conn, 'DELETE FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
            conn.commit()
    
    def add_individual_message(self, birth_hash: str, message: Dict):
        """Add individual message to conversation history"""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = conn.cursor()
            execute(conn, 'SELECT conversation_data FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
            result = cursor.fetchone()
        
        if result:
            conversation_data = json.loads(result[0])
        else:
            conversation_data = {'messages': []}
        
        # Add new message
        conversation_data['messages'].append(message)
        
        # Keep only last 100 messages
        if len(conversation_data['messages']) > 100:
            conversation_data['messages'] = conversation_data['messages'][-100:]
        
            if result:
                execute(
                    conn,
                    'UPDATE chat_conversations SET conversation_data = ?, updated_at = ? WHERE birth_hash = ?',
                    (json.dumps(conversation_data), datetime.now().isoformat(), birth_hash),
                )
            else:
                execute(
                    conn,
                    'INSERT INTO chat_conversations (birth_hash, conversation_data) VALUES (?, ?)',
                    (birth_hash, json.dumps(conversation_data)),
                )
            conn.commit()

    
    def get_clarification_count(self, birth_hash: str) -> int:
        """Get current clarification count for session"""
        from db import get_conn, execute
        with get_conn() as conn:
            cursor = execute(
                conn,
                'SELECT clarification_count FROM chat_conversations WHERE birth_hash = ?',
                (birth_hash,),
            )
            result = cursor.fetchone()
        return result[0] if result else 0
    
    def increment_clarification_count(self, birth_hash: str):
        """Increment clarification count"""
        from db import get_conn, execute
        with get_conn() as conn:
            execute(
                conn,
                'UPDATE chat_conversations SET clarification_count = clarification_count + 1 WHERE birth_hash = ?',
                (birth_hash,),
            )
            conn.commit()
    
    def reset_clarification_count(self, birth_hash: str):
        """Reset clarification count to 0"""
        from db import get_conn, execute
        with get_conn() as conn:
            execute(
                conn,
                'UPDATE chat_conversations SET clarification_count = 0 WHERE birth_hash = ?',
                (birth_hash,),
            )
            conn.commit()
