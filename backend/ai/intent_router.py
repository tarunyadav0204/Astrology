import google.generativeai as genai
import json
import os
from typing import Dict

class IntentRouter:
    """
    Classifies user queries into various analysis modes for the astrology chat AI.
    Uses Gemini Flash for ultra-fast (<1s) classification.
    """
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        
    async def classify_intent(self, user_question: str, chat_history: list = None, user_facts: dict = None, clarification_count: int = 0, language: str = 'english', force_ready: bool = False, d1_chart: dict = None) -> Dict[str, str]:
        """
        Returns: {'status': 'CLARIFY' | 'READY', 'mode': 'PREDICT_DAILY' | 'ANALYZE_PERSONALITY' | ..., 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}, 'extracted_context': {...}, 'context_type': 'birth' | 'annual'}
        """
        chat_history = chat_history or []
        user_facts = user_facts or {}
        import time
        from datetime import datetime
        
        intent_start = time.time()
        print(f"\n{'='*80}")
        print(f"🧠 INTENT CLASSIFICATION STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%B')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Build conversation context
        history_text = ""
        if chat_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in chat_history[-3:]:
                history_text += f"Q: {msg.get('question', '')}\nA: {msg.get('response', '')}\n"
        
        # Build user facts context
        facts_text = ""
        if user_facts:
            facts_text = "\n\nKNOWN USER BACKGROUND:\n"
            for category, items in user_facts.items():
                fact_str = ", ".join(items) if isinstance(items, list) else str(items)
                facts_text += f"- {category.upper()}: {fact_str}\n"
            facts_text += "\nIMPORTANT: Do NOT ask for information already present in the user background.\n"
        
        # Add clarification limit enforcement
        clarification_limit_text = ""
        if clarification_count >= 1:
            clarification_limit_text = f"""

🚨🚨🚨 CRITICAL: CLARIFICATION LIMIT REACHED 🚨🚨🚨

You have ALREADY asked {clarification_count} clarification question(s).
The conversation history above shows your previous clarification question.
The current user message is their ANSWER to your clarification.

You are ABSOLUTELY FORBIDDEN from asking another clarification question.

You MUST:
1. Return status: "READY" 
2. Extract the category/timeframe from the user's answer
3. Set appropriate mode, needs_transits, and transit_request based on the COMBINED context of:
   - The original question (in conversation history)
   - The user's clarification answer (current question)

DO NOT generate a "clarification_question" field.
PROCEED WITH ANALYSIS NOW.
"""
        
        language_instruction = f"IMPORTANT: If you generate a clarification question, it MUST be in the following language: {language}"

        force_ready_instruction = ""
        if force_ready:
            force_ready_instruction = f"""
🚨🚨🚨 ABSOLUTE OVERRIDE - CLARIFICATION FORBIDDEN 🚨🚨🚨

You are ABSOLUTELY REQUIRED to return status: "READY".
You are ABSOLUTELY FORBIDDEN from returning status: "CLARIFY".
You MUST NOT generate a clarification_question.

The clarification limit has been reached OR this is a partnership analysis.
PROCEED WITH ANALYSIS IMMEDIATELY.

If the question seems vague, make reasonable assumptions and proceed.
Set appropriate mode, category, and divisional_charts based on the question context.
"""

        prompt = f"""
        You are a clarification assistant for an astrology chatbot. Your job is to determine if a question is too vague and needs clarification, and to classify the user's intent.
        
        🚨 CRITICAL INSTRUCTION FOR chart_insights:
        - When status is "READY", you MUST generate chart_insights array with 5-7 house insights
        - When status is "CLARIFY", set chart_insights to null
        - chart_insights is MANDATORY when status="READY"
        - DO NOT return null for chart_insights when status="READY"
        
        {force_ready_instruction}
        {language_instruction}

        CURRENT DATE CONTEXT:
        - Today's Date: {current_date}
        - Current Year: {current_year}
        - Current Month: {current_month}
        
        IMPORTANT: When user asks about "next 3 months", "next 6 months", or relative time periods, calculate from TODAY'S DATE ({current_date}).
        Example: If today is 2024-12-20 and user asks "next 3 months", that means January-March 2025, NOT 2024.
        {history_text}
        {facts_text}
        {clarification_limit_text}
        
        Current question: "{user_question}"
        
        CRITICAL FOLLOW-UP DETECTION:
        1. If the PREVIOUS assistant message was a FULL ANSWER (not a clarification question), and the current user message is:
           - A correction ("that's wrong", "incorrect", "planet position is wrong")
           - A follow-up ("tell me more", "what about...", "and...")
           - A clarification request ("what do you mean", "explain")
           - A short response referring to previous context ("yes", "no", "okay", single words)
           Then: Return status: "READY" immediately WITHOUT asking clarification. This is a continuation of the previous conversation.
        
        2. If the PREVIOUS assistant message was a clarification question asking which area to focus on, and the current user message is answering that (e.g., "career", "about my career", "health"), then:
           - Extract the area from the user's response
           - Return status: "READY" with the extracted category
           - Combine the original question context with the user's clarification response
        
        DIVISIONAL CHART DETECTION:
        Based on the question topic, determine which divisional charts are needed. Examples:
        - "When will I get married?" → ["D1", "D9", "D7"]
        - "How is my career?" → ["D1", "D9", "D10", "Karkamsa"]
        - "Tell me about my siblings" → ["D1", "D3", "D9"]
        
        CONTEXT_TYPE:
        1. "annual": For YEARLY forecasts, specific calendar years (e.g. "How is my 2026?", "What does next year hold?", "How is my career in 2026?")
        2. "birth": For general life analysis, personality, "When will..." timing questions, DAILY/SPECIFIC DATE questions (e.g. "When will I get married?", "What are my strengths?", "What events on Feb 2nd?", "How is today?", "What about this month?")

        🚨 CRITICAL CONTEXT_TYPE DISTINCTION:
        - Questions about SPECIFIC DAYS, DATES, or SHORT PERIODS (today, this week, this month) → ALWAYS use "birth" context_type.
        - Questions about ENTIRE YEARS or ANNUAL FORECASTS → use "annual" context_type.

        TRANSIT DETECTION:
        - "When will..." questions → needs_transits: true
        - "What period is good for..." → needs_transits: true
        - "How is 2025/next year..." → needs_transits: true
        - Career questions about promotions/hikes → needs_transits: true
        - Personality/yoga/general questions → needs_transits: false

        CRITICAL: For ANY context_type requiring transits, set startYear and endYear to ONLY the specific year/period mentioned.
        - "2026" → startYear: 2026, endYear: 2026
        - "next year" → startYear: {current_year + 1}, endYear: {current_year + 1}
        - General timing questions ("when will I...") → startYear: {current_year}, endYear: {current_year + 2}

        MODES (USER INTENT):
        You must choose one of the following modes based on the user's question. This determines the structure of the final answer.

        - "PREDICT_DAILY": For daily predictions (e.g., "How is today?", "What's in store for me today?").
        - "PREDICT_PERIOD_OUTLOOK": For general questions about a specific timeframe (e.g., "How will the next 6 months be for my career?"). This is for a deep-dive analysis.
        - "PREDICT_EVENT_TIMING": For "when will X happen?" questions (e.g., "When will I get married?").
        - "PREDICT_EVENTS_FOR_PERIOD": For listing numerous potential events over a period (e.g., "Tell me all events for this year."). This is for a timeline-style list.
        - "ANALYZE_TOPIC_POTENTIAL": Assesses the potential of a life area (e.g., "Tell me about my financial prospects.").
        - "ANALYZE_PERSONALITY": Describes the user's character based on their chart (e.g., "What does my chart say about me?", "What are my strengths?").
        - "ANALYZE_ROOT_CAUSE": For deep-seated "why" questions (e.g., "Why do I always struggle with self-confidence?").
        - "RECOMMEND_REMEDY_FOR_PROBLEM": Suggests remedies for a specific issue (e.g., "I have a lot of anxiety. What can I do?").

        CHART INSIGHTS:
        🚨 MANDATORY REQUIREMENT 🚨
        When status is "READY", you MUST generate chart_insights using the D1 chart data provided.
        DO NOT set chart_insights to null when status is "READY".
        
        D1 CHART DATA PROVIDED:
        {json.dumps(d1_chart) if d1_chart else 'No chart data available'}
        
        Generate a `chart_insights` array with 5-7 objects analyzing THIS NATIVE'S SPECIFIC CHART.
        Look at which planets are in which houses and signs, then provide SPECIFIC insights.
        
        Each object MUST have:
        - house_number: (1-12)
        - message: SPECIFIC insight about THIS native's chart (e.g., "Sun in 10th house in Capricorn indicates strong career ambitions and leadership in professional life")
        - highlight_type: "ascendant" | "planets" | "empty"
        
        DO NOT give generic house meanings. Analyze the ACTUAL planetary placements in the chart.
        
        Example:
        "chart_insights": [
            {{"house_number": 1, "message": "Virgo Ascendant reflects analytical nature and health consciousness", "highlight_type": "ascendant"}},
            {{"house_number": 2, "message": "Leo in 2nd house with Sun, Mercury, Venus, Mars - strong wealth potential through leadership", "highlight_type": "planets"}},
            {{"house_number": 5, "message": "Jupiter in 5th house blesses with intelligent children and creative wisdom", "highlight_type": "planets"}},
            {{"house_number": 7, "message": "Saturn in 7th house indicates mature, responsible partnerships", "highlight_type": "planets"}},
            {{"house_number": 10, "message": "Moon in 10th house creates public recognition and emotional career fulfillment", "highlight_type": "planets"}}
        ]

        Return ONLY a JSON object:
        {{
            "status": "CLARIFY" or "READY",
            "clarification_question": "Your clarifying question here (only if status=CLARIFY)",
            "chart_insights": [{{"house_number": 1, "message": "...", "highlight_type": "ascendant"}}],
            "mode": "PREDICT_DAILY" or "PREDICT_EVENT_TIMING" or "ANALYZE_PERSONALITY",
            "extracted_context": {{ "timeframe": "2025", "aspect": "promotion" }},
            "context_type": "annual" or "birth",
            "category": "category_name",
            "year": "SPECIFIC_YEAR_FROM_QUESTION (only for annual context_type)",
            "needs_transits": true or false,
            "divisional_charts": ["D3", "D9", "D10"],
            "transit_request": {{
                "startYear": "SPECIFIC_YEAR_FROM_QUESTION",
                "endYear": "SPECIFIC_YEAR_FROM_QUESTION",
                "yearMonthMap": {{
                    "SPECIFIC_YEAR_FROM_QUESTION": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                }}
            }}
        }}

        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, travel, visa, foreign, gain, wish, general, son, daughter, mother, father, spouse, siblings, children, family
        """
        
        print(f"\n📤 INTENT ROUTER REQUEST:")
        print(f"Model: {self.model._model_name if hasattr(self.model, '_model_name') else 'Unknown'}")
        print(f"Prompt length: {len(prompt)} characters")
        
        try:
            gemini_start = time.time()
            
            response = await self.model.generate_content_async(prompt)
            gemini_time = time.time() - gemini_start
            
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            print(f"🔍 RAW INTENT RESPONSE: {cleaned}")
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            print(f"✅ Intent: {result.get('status')} | Mode: {result.get('mode')} | Category: {result.get('category')} | Time: {total_time:.2f}s")
            
            # Add fallback values if missing
            if 'status' not in result:
                result['status'] = 'READY'
            if 'mode' not in result or result['mode'] is None:
                result['mode'] = 'PREDICT_EVENTS_FOR_PERIOD' if any(w in user_question.lower() for w in ['all events', 'events', 'timeline']) else 'ANALYZE_PERSONALITY'
            if 'context_type' not in result:
                result['context_type'] = 'birth'
            if 'category' not in result or result['category'] is None:
                result['category'] = 'general'
            if 'extracted_context' not in result:
                result['extracted_context'] = {}
            if 'needs_transits' not in result:
                result['needs_transits'] = result['context_type'] in ['birth', 'annual'] and any(word in user_question.lower() for word in ['when', 'timing', 'period', 'year', '2025', '2026', '2027'])
            if 'divisional_charts' not in result:
                result['divisional_charts'] = self._get_default_divisional_charts(result.get('category', 'general'))
            if 'chart_insights' not in result or not result['chart_insights']:
                result['chart_insights'] = [
                    {"house_number": 1, "message": "Analyzing your ascendant and personality", "highlight_type": "ascendant"},
                    {"house_number": 10, "message": "Examining career and public image", "highlight_type": "planets"}
                ]
            
            # Ensure chart_insights is a list, not null
            if result.get('chart_insights') is None:
                result['chart_insights'] = [
                    {"house_number": 1, "message": "Analyzing your ascendant and personality", "highlight_type": "ascendant"},
                    {"house_number": 10, "message": "Examining career and public image", "highlight_type": "planets"}
                ]
            
            if result.get('needs_transits') and 'transit_request' not in result:
                result['transit_request'] = {
                    "startYear": current_year,
                    "endYear": current_year + 2,
                    "yearMonthMap": {
                        str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] for y in range(current_year, current_year + 3)
                    }
                }
            
            return result
        except Exception as e:
            total_time = time.time() - intent_start
            print(f"\n❌ INTENT CLASSIFICATION FAILED")
            print(f"Error: {e}")
            print(f"Total time: {total_time:.3f}s")
            
            # Fallback logic
            is_timing_question = any(w in user_question.lower() for w in ['when', 'time', 'date', 'year', 'month', 'will i', 'should i'])
            is_daily_question = any(w in user_question.lower() for w in ['today', 'daily'])

            if is_daily_question:
                return {
                    "status": "READY", "extracted_context": {}, "mode": "PREDICT_DAILY", "context_type": "birth", "category": "general", "needs_transits": True,
                    "divisional_charts": ["D1", "D9"],
                    "transit_request": {
                        "startYear": current_year, "endYear": current_year,
                        "yearMonthMap": {str(current_year): [current_month]}
                    }
                }
            elif is_timing_question:
                return {
                    "status": "READY", "extracted_context": {}, "mode": "PREDICT_EVENT_TIMING", "context_type": "birth", "category": "timing", "needs_transits": True,
                    "divisional_charts": ["D1", "D9"],
                    "transit_request": {
                        "startYear": current_year, "endYear": current_year + 2,
                        "yearMonthMap": {str(y): ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"] for y in range(current_year, current_year + 3)}
                    }
                }
            else:
                return {
                    "status": "READY", "extracted_context": {}, "mode": "ANALYZE_PERSONALITY", "context_type": "birth", "category": "general", "needs_transits": False,
                    "divisional_charts": ["D1", "D9"]
                }
    
    def _get_default_divisional_charts(self, category: str) -> list:
        """Get default divisional charts based on question category"""
        chart_mapping = {
            'marriage': ['D1', 'D9', 'D7'], 'career': ['D1', 'D9', 'D10', 'Karkamsa'], 'job': ['D1', 'D9', 'D10', 'Karkamsa'],
            'promotion': ['D1', 'D9', 'D10', 'Karkamsa'], 'business': ['D1', 'D9', 'D10', 'Karkamsa'],
            'soul': ['D1', 'D9', 'D20', 'Swamsa'], 'spirituality': ['D1', 'D9', 'D20', 'Swamsa'], 'purpose': ['D1', 'D9', 'Karkamsa', 'Swamsa'],
            'dharma': ['D1', 'D9', 'Karkamsa', 'Swamsa'], 'health': ['D1', 'D9', 'D30'], 'disease': ['D1', 'D9', 'D30'],
            'children': ['D1', 'D7', 'D9'], 'child': ['D1', 'D7', 'D9'], 'pregnancy': ['D1', 'D7', 'D9'],
            'siblings': ['D1', 'D3', 'D9'], 'property': ['D1', 'D4', 'D9', 'D12'], 'home': ['D1', 'D4', 'D9'],
            'mother': ['D1', 'D4', 'D9', 'D12'], 'father': ['D1', 'D9', 'D10', 'D12'], 'education': ['D1', 'D9', 'D24'],
            'learning': ['D1', 'D9', 'D24'], 'vehicles': ['D1', 'D4', 'D16'], 'travel': ['D1', 'D3', 'D9'],
            'foreign': ['D1', 'D9', 'D12'], 'visa': ['D1', 'D9', 'D12'], 'wealth': ['D1', 'D9', 'D10'], 'money': ['D1', 'D9', 'D10'],
            'finance': ['D1', 'D9', 'D10'], 'love': ['D1', 'D7', 'D9'], 'relationship': ['D1', 'D7', 'D9'],
            'partner': ['D1', 'D7', 'D9'], 'timing': ['D1', 'D9'], 'general': ['D1', 'D9'], 'son': ['D1', 'D7', 'D9'],
            'daughter': ['D1', 'D7', 'D9'], 'spouse': ['D1', 'D7', 'D9'], 'family': ['D1', 'D9', 'D12']
        }
        return chart_mapping.get(category.lower(), ['D1', 'D9'])