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
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        
    async def classify_intent(self, user_question: str, chat_history: list = None, user_facts: dict = None, clarification_count: int = 0) -> Dict[str, str]:
        """
        Returns: {'status': 'CLARIFY' | 'READY', 'mode': 'birth' | 'annual', 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}, 'extracted_context': {...}}
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
            for msg in chat_history[-3:]:  # Last 3 exchanges
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
        
        prompt = f"""
        You are a clarification assistant for an astrology chatbot. Your job is to determine if a question is too vague and needs clarification.
        
        CURRENT DATE CONTEXT:
        - Today's Date: {current_date}
        - Current Year: {current_year}
        - Current Month: {current_month}
        
        IMPORTANT: When user asks about "next 3 months", "next 6 months", or relative time periods, calculate from TODAY'S DATE ({current_date}).
        Example: If today is 2024-12-20 and user asks "next 3 months", that means January-March 2025, NOT 2024.
        {history_text}
        {facts_text}
        {clarification_limit_text}
        
        🚨🚨🚨 BLOCKING RULE - READ THIS FIRST 🚨🚨🚨
        Before generating ANY clarification question, you MUST:
        1. Read the "KNOWN USER BACKGROUND" section above
        2. Check if the information you want to ask is ALREADY THERE
        3. If it IS there, DO NOT ask for it - skip to asking about the specific aspect instead
        
        Example: User background shows "CAREER: Employed in Amazon as a Senior Software Development Manager"
        ❌ WRONG: "Are you currently employed or running a business?"
        ✅ CORRECT: "What specific aspect of your career would you like to explore - promotion timing, salary growth, job change, or career direction?"
        
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
        Based on the question topic, determine which divisional charts are needed:
        - D1 (Rashi): Always include for basic analysis
        - D3 (Drekkana): Siblings, courage, communication, short travels
        - D4 (Chaturthamsa): Property, home, mother, education, vehicles
        - D7 (Saptamsa): Children, creativity, progeny
        - D9 (Navamsa): Marriage, spouse, dharma, spiritual strength (always include)
        - D10 (Dasamsa): Career, profession, reputation, father
        - D12 (Dwadasamsa): Parents, ancestry, past life
        - D16 (Shodasamsa): Vehicles, happiness, luxuries
        - D20 (Vimsamsa): Spirituality, religious practices
        - D24 (Chaturvimsamsa): Education, learning, knowledge
        - D27 (Nakshatramsa): Strengths, weaknesses, general fortune
        - D30 (Trimsamsa): Misfortunes, diseases, enemies
        - D40 (Khavedamsa): Maternal relatives, auspicious/inauspicious events
        - D45 (Akshavedamsa): Character, conduct, general behavior
        - D60 (Shashtiamsa): General fortune, karmic patterns
        
        Examples:
        - "When will I get married?" → ["D1", "D9", "D7"]
        - "How is my career?" → ["D1", "D9", "D10", "Karkamsa"]
        - "What does my birth chart say about my career?" → ["D1", "D9", "D10", "Karkamsa"]
        - "Tell me about my siblings" → ["D1", "D3", "D9"]
        - "Property purchase timing?" → ["D1", "D4", "D9", "D12"]
        - "Children prospects?" → ["D1", "D7", "D9"]
        - "Health issues?" → ["D1", "D9", "D30"]
        - "Education/learning?" → ["D1", "D9", "D24"]
        - "Spiritual growth?" → ["D1", "D9", "D20", "Swamsa"]
        - "What is my life purpose?" → ["D1", "D9", "Karkamsa", "Swamsa"]
        
        CRITICAL RULES FOR CLARIFICATION:
        
        1. ALWAYS return status: "CLARIFY" for these types of questions:
           - "Tell me about my [year]" (e.g., "Tell me about my 2026", "Tell me about next year")
           - "How is my [year]?" (e.g., "How is my 2026?", "How is next year?")
           - "What about [year]?" (e.g., "What about 2026?")
           - "Tell me about my [topic]" without specifics (e.g., "Tell me about my career", "Tell me about marriage")
           - "What about [topic]?" without specifics (e.g., "What about my health?")
           - Any question asking about a year/period WITHOUT mentioning a specific life area
        
        2. ONLY return status: "READY" when question has BOTH:
           - A specific life area (career, health, marriage, finance, etc.)
           - A clear focus or timeframe
           Examples: "When will I get married?", "Will I get promotion in 2025?", "How is my health in 2026?"
        
        3. When clarification is needed, craft a natural, conversational question that:
           
           🚨 CRITICAL: ALWAYS check the KNOWN USER BACKGROUND section first.
           - DO NOT ask for information already present in the user background
           - Example: If background shows "CAREER: Employed in Amazon", skip asking about employment status
           - Example: If background shows "FAMILY: Married in 2020", skip asking about marital status
           
           Your clarification question should:
           - Focus on narrowing down the SPECIFIC aspect they want to know (timing, prospects, challenges, etc.)
           - Gather NEW factual information NOT in the user background
           - Sound warm, natural, and conversational (not templated)
           - Be tailored to their exact question
           - Help you provide a more accurate astrological analysis
           
           💡 FACT EXTRACTION BONUS:
           The MORE specific facts you can extract in your clarification question, the BETTER our future responses will be.
           - Instead of just asking "What aspect?", try to extract concrete details
           - Examples of valuable facts: specific job titles, company names, years of experience, number of children, ages, education levels, health conditions, locations, dates of major events
           - These facts will be stored and used to personalize ALL future astrological guidance for this user
        
        4. 🚨 ABSOLUTE MAXIMUM: 1 clarification per conversation - NO EXCEPTIONS
           - After 1 clarification, you MUST return status: "READY" regardless of information completeness
           - The clarification_count parameter tracks how many you've already asked
           - If clarification_count >= 1, you are FORBIDDEN from asking another question
        
        MODES:
        1. "annual": YEARLY forecasts, specific calendar years (e.g. "How is my 2026?", "What does next year hold?")
        2. "birth": General life analysis, personality, "When will..." timing questions (e.g. "When will I get married?", "What are my strengths?")

        TRANSIT DETECTION:
        - "When will..." questions → needs_transits: true
        - "What period is good for..." → needs_transits: true
        - "How is 2025/next year..." → needs_transits: true
        - "Marriage timing" → needs_transits: true
        - Questions involving 'when', 'growth', or 'timing' → ALWAYS set needs_transits: true
        - Career questions about promotions/hikes → needs_transits: true
        - Personality/yoga/general questions → needs_transits: false

        CRITICAL: For ANY mode requiring transits, set startYear and endYear to ONLY the specific year/period mentioned in the question.
        - If question mentions "2026", use startYear: 2026, endYear: 2026
        - If question mentions "Q1 2026", use startYear: 2026, endYear: 2026, months: ["January", "February", "March"]
        - If question mentions "March-June 2025", use startYear: 2025, endYear: 2025, months: ["March", "April", "May", "June"]
        - If question mentions "next year", use startYear: {current_year + 1}, endYear: {current_year + 1}
        - For general timing questions without specific year, use startYear: {current_year}, endYear: {current_year + 2}

        Return ONLY a JSON object:
        {{
            "status": "CLARIFY" or "READY",
            "clarification_question": "Your clarifying question here (only if status=CLARIFY)",
            "extracted_context": {{"timeframe": "2025", "aspect": "promotion"}},
            "mode": "annual" or "birth",
            "category": "category_name",
            "year": SPECIFIC_YEAR_FROM_QUESTION (only for annual mode),
            "needs_transits": true or false,
            "divisional_charts": ["D3", "D9", "D10"],
            "transit_request": {{
                "startYear": SPECIFIC_YEAR_FROM_QUESTION,
                "endYear": SPECIFIC_YEAR_FROM_QUESTION,
                "yearMonthMap": {{
                    "SPECIFIC_YEAR_FROM_QUESTION": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                }}
            }}
        }}

        EXAMPLES (use these to identify similar patterns):
        
        Question: "How is my 2026?"
        Response: {{"status": "CLARIFY", "clarification_question": "To provide the most accurate guidance, which area would you like me to focus on?", "mode": "annual", "year": 2026}}
        
        Question: "Tell me about next year"
        Response: {{"status": "CLARIFY", "clarification_question": "To provide the most accurate guidance, which area would you like me to focus on?", "mode": "annual", "year": {current_year + 1}}}
        
        Question: "How is my health in 2026?"
        Response: {{"status": "READY", "mode": "annual", "category": "health", "year": 2026, "needs_transits": true, "divisional_charts": ["D1", "D9", "D30"]}}
        
        Question: "When will I get married?"
        Response: {{"status": "READY", "mode": "birth", "category": "marriage", "needs_transits": true, "divisional_charts": ["D1", "D9", "D7"]}}
        
        Question: "Tell me about my siblings"
        Response: {{"status": "READY", "mode": "birth", "category": "siblings", "needs_transits": false, "divisional_charts": ["D1", "D3", "D9"]}}
        
        - "Tell me about my health in 2026" -> startYear: 2026, endYear: 2026, yearMonthMap: {{"2026": [all 12 months]}}
        - "How is Q1 2026 for my career?" → startYear: 2026, endYear: 2026, yearMonthMap: {{"2026": ["January", "February", "March"]}}
        - "Marriage prospects in March-June 2025?" → startYear: 2025, endYear: 2025, yearMonthMap: {{"2025": ["March", "April", "May", "June"]}}
        - "What are my strengths?" → needs_transits: false
        - "When will I get married?" → startYear: {current_year}, endYear: {current_year + 2} (general timing)
        
        Categories: job, career, promotion, business, love, relationship, marriage, partner, wealth, money, finance, health, disease, property, home, child, pregnancy, education, travel, visa, foreign, gain, wish, general
        """
        
        # print(f"\n📤 INTENT ROUTER REQUEST:")
        # print(f"Model: {self.model._model_name if hasattr(self.model, '_model_name') else 'Unknown'}")
        # print(f"Prompt length: {len(prompt)} characters")
        # print(f"\nFull Prompt:\n{prompt}")
        
        
        try:
            gemini_start = time.time()
            
            response = await self.model.generate_content_async(prompt)
            gemini_time = time.time() - gemini_start
            
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            print(f"✅ Intent: {result.get('status')} | Mode: {result.get('mode')} | Category: {result.get('category')} | Time: {total_time:.2f}s")
            
            # Add fallback values if missing
            if 'status' not in result:
                result['status'] = 'READY'  # Default to ready
            if 'mode' not in result:
                result['mode'] = 'birth'  # Default to birth mode
            if 'category' not in result:
                result['category'] = 'general'  # Default category
            if 'extracted_context' not in result:
                result['extracted_context'] = {}
            if 'needs_transits' not in result:
                result['needs_transits'] = result['mode'] in ['birth', 'annual'] and any(word in user_question.lower() for word in ['when', 'timing', 'period', 'year', '2025', '2026', '2027'])
            if 'divisional_charts' not in result:
                # Default divisional charts based on category
                category = result.get('category', 'general')
                result['divisional_charts'] = self._get_default_divisional_charts(category)
            
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
                    "status": "READY",
                    "extracted_context": {},
                    "mode": "birth",
                    "category": "timing",
                    "needs_transits": True,
                    "divisional_charts": ["D1", "D9"],
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
                    "status": "READY",
                    "extracted_context": {},
                    "mode": "birth", 
                    "category": "general",
                    "needs_transits": False,
                    "divisional_charts": ["D1", "D9"]
                }
    
    def _get_default_divisional_charts(self, category: str) -> list:
        """Get default divisional charts based on question category"""
        chart_mapping = {
            'marriage': ['D1', 'D9', 'D7'],
            'career': ['D1', 'D9', 'D10', 'Karkamsa'],
            'job': ['D1', 'D9', 'D10', 'Karkamsa'],
            'promotion': ['D1', 'D9', 'D10', 'Karkamsa'],
            'business': ['D1', 'D9', 'D10', 'Karkamsa'],
            'soul': ['D1', 'D9', 'D20', 'Swamsa'],
            'spirituality': ['D1', 'D9', 'D20', 'Swamsa'],
            'purpose': ['D1', 'D9', 'Karkamsa', 'Swamsa'],
            'dharma': ['D1', 'D9', 'Karkamsa', 'Swamsa'],
            'health': ['D1', 'D9', 'D30'],
            'disease': ['D1', 'D9', 'D30'],
            'children': ['D1', 'D7', 'D9'],
            'child': ['D1', 'D7', 'D9'],
            'pregnancy': ['D1', 'D7', 'D9'],
            'siblings': ['D1', 'D3', 'D9'],
            'property': ['D1', 'D4', 'D9', 'D12'],
            'home': ['D1', 'D4', 'D9'],
            'mother': ['D1', 'D4', 'D9', 'D12'],
            'father': ['D1', 'D9', 'D10', 'D12'],
            'education': ['D1', 'D9', 'D24'],
            'learning': ['D1', 'D9', 'D24'],
            'spirituality': ['D1', 'D9', 'D20'],
            'religion': ['D1', 'D9', 'D20'],
            'vehicles': ['D1', 'D4', 'D16'],
            'travel': ['D1', 'D3', 'D9'],
            'foreign': ['D1', 'D9', 'D12'],
            'visa': ['D1', 'D9', 'D12'],
            'wealth': ['D1', 'D9', 'D10'],
            'money': ['D1', 'D9', 'D10'],
            'finance': ['D1', 'D9', 'D10'],
            'love': ['D1', 'D7', 'D9'],
            'relationship': ['D1', 'D7', 'D9'],
            'partner': ['D1', 'D7', 'D9'],
            'timing': ['D1', 'D9'],
            'general': ['D1', 'D9']
        }
        
        return chart_mapping.get(category.lower(), ['D1', 'D9'])
