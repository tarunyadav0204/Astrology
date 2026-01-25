import google.generativeai as genai
import json
import os
import sqlite3
from typing import Dict, List

class FactExtractor:
    """Extract and store user facts from conversations using Gemini Flash"""
    
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        import os
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️ GEMINI_API_KEY not found - fact extraction disabled")
            self.model = None
            return
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.0-flash-exp')
    
    async def extract_facts(self, question: str, response: str, birth_chart_id: int):
        """Extract facts from Q&A pair and store them"""
        
        if not self.model:
            print("⚠️ Fact extraction skipped - model not initialized")
            return
        
        prompt = f"""Extract ONLY factual information that the USER explicitly stated about themselves.
DO NOT extract astrological predictions, analysis, or interpretations.

User's Question/Statement: {question}
Assistant's Response: {response}

RULES:
1. ONLY extract facts from the USER'S question/statement, NOT from the assistant's astrological analysis
2. Extract concrete personal information like:
   - "I work as a software engineer" → career fact
   - "I got married in 2020" → family/major_events fact
   - "I'm planning to move to Canada" → location/preferences fact
   - "I have two children" → family fact

3. CRITICAL - TEMPORAL CONTEXT:
   - If user mentions time-sensitive events ("I have surgery today", "I'm traveling next week"), include the temporal context
   - Format: "Surgery scheduled (mentioned on [current date])"
   - For ongoing states without dates ("I work as engineer"), no date needed
   - For past events with dates ("married in 2020"), include the year
   - For future plans ("planning to move"), mark as "planned" or "upcoming"

4. DO NOT extract:
   - Astrological predictions ("you will face challenges")
   - Chart interpretations ("partnerships are important for you")
   - Future forecasts ("2026 will be good for career")
   - General advice or analysis

Categories:
- career: Job, profession, work experience, industry
- family: Marital status, children, parents, siblings
- health: Medical conditions, health concerns, surgeries, treatments
- location: Current city, country, places lived
- preferences: Interests, hobbies, goals
- education: Degrees, studies, institutions
- relationships: Dating status, engagement, divorce
- major_events: Significant life events with dates
- temporary_events: Time-sensitive events (surgeries, trips, interviews)

Return ONLY a JSON array of facts:
[
  {{"category": "career", "fact": "Software Engineer with 2 years experience", "confidence": 0.9}},
  {{"category": "temporary_events", "fact": "Surgery scheduled (mentioned on {datetime.now().strftime('%Y-%m-%d')})", "confidence": 1.0}},
  {{"category": "family", "fact": "Married in 2020", "confidence": 1.0}}
]

If no USER-STATED facts found, return empty array: []
"""
        
        try:
            result = await self.model.generate_content_async(prompt)
            cleaned = result.text.replace('```json', '').replace('```', '').strip()
            facts = json.loads(cleaned)
            
            if facts:
                self._store_facts(facts, birth_chart_id)
                print(f"✅ Extracted {len(facts)} facts for birth_chart_id={birth_chart_id}")
            
        except Exception as e:
            print(f"❌ Fact extraction error: {e}")
    
    def _store_facts(self, facts: List[Dict], birth_chart_id: int):
        """Store facts in database"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        for fact_data in facts:
            cursor.execute("""
                INSERT INTO user_facts (birth_chart_id, category, fact, confidence)
                VALUES (?, ?, ?, ?)
            """, (
                birth_chart_id,
                fact_data['category'],
                fact_data['fact'],
                fact_data.get('confidence', 1.0)
            ))
        
        conn.commit()
        conn.close()
    
    def get_facts(self, birth_chart_id: int) -> Dict[str, List[str]]:
        """Retrieve all facts for a birth chart, filtering out old temporary events"""
        from datetime import datetime, timedelta
        
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, fact, extracted_at FROM user_facts
            WHERE birth_chart_id = ?
            ORDER BY extracted_at DESC
        """, (birth_chart_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        facts_by_category = {}
        cutoff_date = datetime.now() - timedelta(days=7)  # Filter temporary events older than 7 days
        
        for category, fact, extracted_at in rows:
            # Skip old temporary events
            if category == 'temporary_events':
                try:
                    fact_date = datetime.fromisoformat(extracted_at)
                    if fact_date < cutoff_date:
                        continue  # Skip this old temporary event
                except:
                    pass  # If date parsing fails, include it
            
            if category not in facts_by_category:
                facts_by_category[category] = []
            facts_by_category[category].append(fact)
        
        return facts_by_category
