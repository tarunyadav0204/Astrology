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
        Classify this astrology question into one of THREE modes:
        
        1. "prashna": Questions about IMMEDIATE outcomes, lost objects, specific events happening NOW or very soon, or YES/NO questions. (e.g. "Will I get this job?", "Where is my wallet?", "Will he call me back?", "How is my relationship this month?")
        
        2. "annual": Questions specifically asking about a YEARLY forecast, the upcoming year, or a specific calendar year. (e.g. "How is my 2026?", "What does next year hold?", "Annual forecast for 2025", "Birthday prediction").
        
        3. "birth": Questions about general life path, personality, long-term future, destiny, or "When will..." questions about general timing. (e.g. "When will I get married?", "What is my career path?", "What are my strengths?").

        Question: "{user_question}"

        Return ONLY a JSON object: {{"mode": "prashna" or "annual" or "birth", "category": "category_name", "year": 202X (only for annual)}}
        
        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, travel, visa, foreign, gain, wish, lost_item, court_case, enemy, competition, general
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
