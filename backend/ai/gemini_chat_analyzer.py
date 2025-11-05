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
        
        # Add current date context to prevent AI from making assumptions
        enhanced_context = astrological_context.copy()
        enhanced_context['current_date_info'] = {
            'current_date': datetime.now().strftime("%Y-%m-%d"),
            'current_year': datetime.now().year,
            'current_month': datetime.now().strftime("%B"),
            'note': 'Use this for reference only. Do not assume transit positions.'
        }
        
        prompt = self._create_chat_prompt(user_question, enhanced_context, conversation_history or [])
        
        print(f"\n=== SENDING TO AI ===")
        print(f"Question: {user_question}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Context keys: {list(enhanced_context.keys()) if enhanced_context else 'None'}")
        print(f"History messages: {len(conversation_history or [])}")
        
        try:
            response = self.model.generate_content(prompt)
            
            # Validate response
            if not response or not hasattr(response, 'text') or not response.text:
                print(f"\n=== EMPTY AI RESPONSE ===")
                return {
                    'success': False,
                    'response': "I apologize, but I couldn't generate a response. Please try asking your question again.",
                    'error': 'Empty response from AI'
                }
            
            response_text = response.text.strip()
            if len(response_text) == 0:
                print(f"\n=== BLANK AI RESPONSE ===")
                return {
                    'success': False,
                    'response': "I received your question but couldn't generate a proper response. Please try rephrasing your question.",
                    'error': 'Blank response from AI'
                }
            
            print(f"\n=== RECEIVED FROM AI ===")
            print(f"Response length: {len(response_text)} chars")
            print(f"Response preview: {response_text[:200]}...")
            
            return {
                'success': True,
                'response': response_text,
                'raw_response': response_text
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
        
        # Get current date and time
        current_date = datetime.now()
        current_date_str = current_date.strftime("%B %d, %Y")
        current_time_str = current_date.strftime("%H:%M UTC")
        
        # Extract key chart information for emphasis
        ascendant_info = context.get('ascendant_info', {})
        ascendant_summary = f"ASCENDANT: {ascendant_info.get('sign_name', 'Unknown')} at {ascendant_info.get('exact_degree_in_sign', 0):.2f}°"
        
        # Custom JSON serializer for datetime objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        return f"""You are a master Vedic astrologer with deep knowledge of classical texts like Brihat Parashara Hora Shastra, Jaimini Sutras, and Phaladeepika. You provide insightful, accurate astrological guidance based on authentic Vedic principles.

IMPORTANT CURRENT DATE INFORMATION:
- Today's Date: {current_date_str}
- Current Time: {current_time_str}
- Current Year: {current_date.year}

CRITICAL CHART INFORMATION:
{ascendant_summary}

CRITICAL INSTRUCTIONS:
- ALWAYS use the EXACT ascendant information provided in the context - DO NOT calculate or guess
- The ascendant has been calculated using Swiss Ephemeris with Lahiri Ayanamsa - trust this calculation
- Use the current date provided above for accurate timing references
- If transit data is provided in the context, you may discuss current transits using that calculated data
- If NO transit data is provided but user asks about transits, explain you need calculated transit positions
- Do NOT guess or assume planetary positions - only use provided calculated data
- Focus primarily on birth chart analysis and dasha periods
- For timing questions, prioritize dasha periods but include transit data if available
- NEVER recalculate the ascendant - use the provided ascendant_info section

BIRTH CHART DATA:
{json.dumps(context, indent=2, default=json_serializer)}

{history_text}

CURRENT QUESTION: {user_question}

GUIDELINES:
- Use conversational, warm, and encouraging tone with beautiful formatting
- Always explain astrological reasoning with **bold planetary names** and specific positions
- Reference relevant *yogas*, *dashas*, and transit data when provided in the context
- Provide practical guidance with clear bullet points
- Mention classical sources in *italics* when relevant (*Parashara*, *Jaimini*, etc.)
- For timing questions, use dasha periods as primary method, supplemented by transit data if available
- Be specific about planetary degrees, house positions, and aspects from the provided data
- Use ### headers to organize different topics clearly
- Focus on empowerment and positive guidance with **bold emphasis**
- If asked about health, relationships, or career, use relevant chart factors
- You may discuss transits IF calculated transit data is provided in the context
- Use emojis sparingly for warmth: ✨ 🌟 💫 (only 1-2 per response)

RESPONSE FORMAT:
Use markdown formatting for beautiful presentation:
- **Bold text** for important points and planetary names
- ### Headers for main sections (e.g., ### Current Planetary Influences)
- • Bullet points for lists and key insights
- *Italics* for Sanskrit terms and classical references
- Line breaks between sections for readability

Structure your response with:
1. **Direct Answer** - Bold opening statement addressing the question
2. ### Astrological Analysis - Header followed by specific chart references
3. **Key Insights** - Bullet points of important findings
4. ### Timing & Guidance - Practical recommendations with timing
5. **Final Thoughts** - Encouraging conclusion

Remember: Be conversational yet structured, insightful yet accessible. Use formatting to make complex astrological information easy to read and visually appealing.
"""