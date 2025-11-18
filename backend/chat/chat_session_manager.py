import sqlite3
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
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                birth_hash TEXT,
                conversation_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, birth_hash: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for birth data"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT conversation_data FROM chat_conversations WHERE birth_hash = ? ORDER BY updated_at DESC LIMIT ?',
            (birth_hash, 1)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            conversation_data = json.loads(result[0])
            messages = conversation_data.get('messages', [])
            # Convert old format to new format if needed
            formatted_messages = []
            for msg in messages:
                if isinstance(msg, dict) and 'question' in msg and 'response' in msg:
                    # Old format - convert to new
                    formatted_messages.append({
                        'role': 'user',
                        'content': msg['question'],
                        'timestamp': msg.get('timestamp', datetime.now().isoformat())
                    })
                    formatted_messages.append({
                        'role': 'assistant', 
                        'content': msg['response'],
                        'timestamp': msg.get('timestamp', datetime.now().isoformat())
                    })
                else:
                    # New format - use as is
                    formatted_messages.append(msg)
            
            return formatted_messages[-limit*2:] if len(formatted_messages) > limit*2 else formatted_messages
        
        return []
    
    def add_message(self, birth_hash: str, user_question: str, ai_response: str):
        """Add message to conversation history"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get existing conversation
        cursor.execute('SELECT conversation_data FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
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
            cursor.execute(
                'UPDATE chat_conversations SET conversation_data = ?, updated_at = ? WHERE birth_hash = ?',
                (json.dumps(conversation_data), datetime.now().isoformat(), birth_hash)
            )
        else:
            cursor.execute(
                'INSERT INTO chat_conversations (birth_hash, conversation_data) VALUES (?, ?)',
                (birth_hash, json.dumps(conversation_data))
            )
        
        conn.commit()
        conn.close()
    
    def create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def clear_conversation(self, birth_hash: str):
        """Clear conversation history for birth data"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
        conn.commit()
        conn.close()
    
    def add_individual_message(self, birth_hash: str, message: Dict):
        """Add individual message to conversation history"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Get existing conversation
        cursor.execute('SELECT conversation_data FROM chat_conversations WHERE birth_hash = ?', (birth_hash,))
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
        
        # Update or insert
        if result:
            cursor.execute(
                'UPDATE chat_conversations SET conversation_data = ?, updated_at = ? WHERE birth_hash = ?',
                (json.dumps(conversation_data), datetime.now().isoformat(), birth_hash)
            )
        else:
            cursor.execute(
                'INSERT INTO chat_conversations (birth_hash, conversation_data) VALUES (?, ?)',
                (birth_hash, json.dumps(conversation_data))
            )
        
        conn.commit()
        conn.close()