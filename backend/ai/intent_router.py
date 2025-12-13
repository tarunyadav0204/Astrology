import google.generativeai as genai
import json
import os
from typing import Dict

class IntentRouter:
    """
    Classifies user queries into 'Birth Chart' vs 'Prashna' (Horary) analysis.
    Uses Gemini Flash for ultra-fast (<1s) classification.
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
        
    async def classify_intent(self, user_question: str) -> Dict[str, str]:
        """
        Returns: {'mode': 'prashna' | 'birth', 'category': 'job'|'love'|...}
        """
        import time
        
        intent_start = time.time()
        print(f"\n{'='*80}")
        print(f"🧠 INTENT CLASSIFICATION STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        
        prompt = f"""
        Classify this astrology question into one of two modes:
        
        1. "prashna": ONLY for SPECIFIC BINARY OUTCOMES or immediate crisis resolution. These are YES/NO questions about a specific event or decision happening RIGHT NOW.
           Examples: 
           - "Will I get THIS job?" (specific job offer)
           - "Where is my lost wallet?"
           - "Will he propose to me?" (specific action)
           - "Should I sign this contract today?"
           - "Is she cheating on me?" (specific suspicion)
           - "Will I recover from this illness?" (current health crisis)
           
        2. "birth": For general life analysis, personality, relationships, timeline forecasts (monthly/yearly), "When will..." questions, "How is..." questions, and ongoing situations.
           Examples:
           - "When will I get married?" (general timing)
           - "What is my career path?"
           - "How is my relationship with my wife?" (ongoing relationship analysis)
           - "How is my month/year?" (timeline forecast)
           - "Tell me about my health" (general health analysis)
           - "What does my chart say about love?" (general analysis)
           - "How is 2026 for me?" (yearly forecast)

        CRITICAL RULES:
        - If the question asks "How is..." or "What about..." or "Tell me about..." → ALWAYS "birth"
        - If the question mentions a time period (this month, this year, 2026, etc.) → ALWAYS "birth"
        - If the question is "When will..." → ALWAYS "birth"
        - ONLY use "prashna" for specific YES/NO decisions or lost object queries

        Question: "{user_question}"

        Return ONLY a JSON object: {{"mode": "prashna" or "birth", "category": "category_name"}}
        
        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, travel, visa, foreign, gain, wish, lost_item, court_case, enemy, competition
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
            
            return result
        except Exception as e:
            total_time = time.time() - intent_start
            print(f"\n❌ INTENT CLASSIFICATION FAILED")
            print(f"Error: {e}")
            print(f"Total time: {total_time:.3f}s")
            print(f"Falling back to birth mode")
            print(f"{'='*80}\n")
            return {"mode": "birth", "category": "general"}
