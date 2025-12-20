import google.generativeai as genai
import json
import os
from typing import Dict

class IntentRouter:
    """
    Classifies user queries into 'Birth Chart' vs 'Annual' analysis.
    Uses Gemini Flash for ultra-fast (<1s) classification.
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
        
    async def classify_intent(self, user_question: str) -> Dict[str, str]:
        """
        Returns: {'mode': 'birth' | 'annual', 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}}
        """
        import time
        from datetime import datetime
        
        intent_start = time.time()
        print(f"\n{'='*80}")
        print(f"🧠 INTENT CLASSIFICATION STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        
        current_year = datetime.now().year
        
        prompt = f"""
        Classify this astrology question and determine if transit data is needed:

        MODES:
        1. "annual": YEARLY forecasts, specific calendar years (e.g. "How is my 2026?", "What does next year hold?")
        2. "birth": General life analysis, personality, "When will..." timing questions (e.g. "When will I get married?", "What are my strengths?")

        TRANSIT DETECTION:
        - "When will..." questions → needs_transits: true
        - "What period is good for..." → needs_transits: true
        - "How is 2025/next year..." → needs_transits: true
        - "Marriage timing" → needs_transits: true
        - Personality/yoga/general questions → needs_transits: false

        Question: "{user_question}"

        CRITICAL: For ANY mode requiring transits, set startYear and endYear to ONLY the specific year/period mentioned in the question.
        - If question mentions "2026", use startYear: 2026, endYear: 2026
        - If question mentions "Q1 2026", use startYear: 2026, endYear: 2026, months: ["January", "February", "March"]
        - If question mentions "March-June 2025", use startYear: 2025, endYear: 2025, months: ["March", "April", "May", "June"]
        - If question mentions "next year", use startYear: {current_year + 1}, endYear: {current_year + 1}
        - For general timing questions without specific year, use startYear: {current_year}, endYear: {current_year + 2}

        Return ONLY a JSON object:
        {{
            "mode": "annual" or "birth",
            "category": "category_name",
            "year": SPECIFIC_YEAR_FROM_QUESTION (only for annual mode),
            "needs_transits": true or false,
            "transit_request": {{
                "startYear": SPECIFIC_YEAR_FROM_QUESTION,
                "endYear": SPECIFIC_YEAR_FROM_QUESTION,
                "yearMonthMap": {{
                    "SPECIFIC_YEAR_FROM_QUESTION": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                }}
            }}
        }}

        EXAMPLES:
        - "Tell me about my health in 2026" → startYear: 2026, endYear: 2026, yearMonthMap: {{"2026": [all 12 months]}}
        - "How is Q1 2026 for my career?" → startYear: 2026, endYear: 2026, yearMonthMap: {{"2026": ["January", "February", "March"]}}
        - "Marriage prospects in March-June 2025?" → startYear: 2025, endYear: 2025, yearMonthMap: {{"2025": ["March", "April", "May", "June"]}}
        - "What are my strengths?" → needs_transits: false
        - "When will I get married?" → startYear: {current_year}, endYear: {current_year + 2} (general timing)
        
        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, travel, visa, foreign, gain, wish, general
        """
        
        print(f"\n📤 INTENT ROUTER REQUEST:")
        print(f"Model: {self.model._model_name if hasattr(self.model, '_model_name') else 'Unknown'}")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"\nFull Prompt:\n{prompt}")
        
        try:
            gemini_start = time.time()
            response = await self.model.generate_content_async(prompt)
            gemini_time = time.time() - gemini_start
            
            print(f"\n📥 INTENT ROUTER RESPONSE:")
            print(f"Gemini API time: {gemini_time:.3f}s")
            print(f"Raw response: {response.text}")
            
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            print(f"\n✅ INTENT CLASSIFICATION COMPLETE")
            print(f"Result: {result}")
            print(f"Total time: {total_time:.3f}s")
            print(f"{'='*80}\n")
            
            # Add fallback values if missing
            if 'needs_transits' not in result:
                result['needs_transits'] = result['mode'] in ['birth', 'annual'] and any(word in user_question.lower() for word in ['when', 'timing', 'period', 'year', '2025', '2026', '2027'])
            
            if result.get('needs_transits') and 'transit_request' not in result:
                result['transit_request'] = {
                    "startYear": current_year,
                    "endYear": current_year + 2,
                    "yearMonthMap": {
                        str(current_year): ["January", "February", "March", "April", "May", "June"],
                        str(current_year + 1): ["January", "February", "March", "April", "May", "June"],
                        str(current_year + 2): ["January", "February", "March", "April", "May", "June"]
                    }
                }
            
            return result
        except Exception as e:
            total_time = time.time() - intent_start
            print(f"\n❌ INTENT CLASSIFICATION FAILED")
            print(f"Error: {e}")
            print(f"Total time: {total_time:.3f}s")
            
            # Fallback with crude keyword detection for timing questions
            is_timing_question = any(w in user_question.lower() for w in ['when', 'time', 'date', 'year', 'month', 'will i', 'should i'])
            
            if is_timing_question:
                print(f"🔍 Fallback detected timing question, enabling transits")
                print(f"{'='*80}\n")
                return {
                    "mode": "birth",
                    "category": "timing",
                    "needs_transits": True,
                    "transit_request": {
                        "startYear": current_year,
                        "endYear": current_year + 2,
                        "yearMonthMap": {
                            str(current_year): ["January", "February", "March", "April", "May", "June"],
                            str(current_year + 1): ["January", "February", "March", "April", "May", "June"],
                            str(current_year + 2): ["January", "February", "March", "April", "May", "June"]
                        }
                    }
                }
            else:
                print(f"Falling back to birth mode without transits")
                print(f"{'='*80}\n")
                return {
                    "mode": "birth", 
                    "category": "general",
                    "needs_transits": False
                }
