import google.generativeai as genai
import json
import os
import html
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_paths = [
    '.env',
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    '/home/tarun_yadav/AstrologyApp/backend/.env'
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

class GeminiChatAnalyzer:
    """Gemini AI integration for astrological chat conversations"""
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        model_names = ['models/gemini-2.5-flash', 'models/gemini-2.0-flash', 'models/gemini-flash-latest']
        self.model = None
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                continue
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    def generate_chat_response(self, user_question: str, astrological_context: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate chat response using astrological context"""
        
        prompt = self._create_chat_prompt(user_question, astrological_context, conversation_history or [])
        
        print(f"\n=== SENDING TO AI ===")
        print(f"Question: {user_question}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Context keys: {list(astrological_context.keys()) if astrological_context else 'None'}")
        print(f"History messages: {len(conversation_history or [])}")
        
        try:
            response = self.model.generate_content(prompt)
            print(f"\n=== RECEIVED FROM AI ===")
            print(f"Response length: {len(response.text)} chars")
            print(f"Response preview: {response.text[:200]}...")
            
            return {
                'success': True,
                'response': response.text,
                'raw_response': response.text
            }
        except Exception as e:
            print(f"\n=== AI ERROR ===")
            print(f"Error: {str(e)}")
            return {
                'success': False,
                'response': f"I apologize, but I'm having trouble analyzing your chart right now. Please try again.",
                'error': str(e)
            }
    
    def _create_chat_prompt(self, user_question: str, context: Dict[str, Any], history: List[Dict]) -> str:
        """Create comprehensive chat prompt for Gemini"""
        
        history_text = ""
        if history:
            history_text = "\n\nCONVERSATION HISTORY:\n"
            for msg in history[-5:]:  # Last 5 messages for context
                history_text += f"User: {msg.get('question', '')}\nAssistant: {msg.get('response', '')}\n\n"
        
        # Custom JSON serializer for datetime objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return f"""You are a master Vedic astrologer with deep knowledge of classical texts like Brihat Parashara Hora Shastra, Jaimini Sutras, and Phaladeepika. You provide insightful, accurate astrological guidance based on authentic Vedic principles.

BIRTH CHART DATA:
{json.dumps(context, indent=2, default=json_serializer)}

{history_text}

CURRENT QUESTION: {user_question}

GUIDELINES:
- Use conversational, warm, and encouraging tone
- Always explain astrological reasoning with specific planetary positions, aspects, and classical principles
- Reference relevant yogas, dashas, and transits when applicable
- Provide practical guidance and actionable insights
- Mention classical sources when relevant (Parashara, Jaimini, etc.)
- For timing questions, use dasha periods and transit data
- Be specific about planetary degrees, house positions, and aspects
- Avoid overly technical jargon - explain concepts clearly
- Focus on empowerment and positive guidance
- If asked about health, relationships, or career, use relevant chart factors

RESPONSE FORMAT:
Provide a natural, conversational response (not JSON). Include:
1. Direct answer to the question
2. Astrological reasoning with specific chart references
3. Practical guidance or recommendations
4. Any relevant timing information if applicable

Remember: You're having a conversation, not writing a report. Be personable and insightful while maintaining astrological accuracy.
"""