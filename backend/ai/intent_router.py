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
        
    async def classify_intent(self, user_question: str, chat_history: list = None) -> Dict[str, str]:
        """
        Returns: {'status': 'CLARIFY' | 'READY', 'mode': 'birth' | 'annual', 'category': 'job'|'love'|..., 'needs_transits': bool, 'transit_request': {...}, 'extracted_context': {...}}
        """
        chat_history = chat_history or []
        import time
        from datetime import datetime
        
        intent_start = time.time()
        print(f"\n{'='*80}")
        print(f"🧠 INTENT CLASSIFICATION STARTED")
        print(f"{'='*80}")
        print(f"Question: {user_question}")
        
        current_year = datetime.now().year
        
        # Build conversation context
        history_text = ""
        if chat_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in chat_history[-3:]:  # Last 3 exchanges
                history_text += f"Q: {msg.get('question', '')}\nA: {msg.get('response', '')}\n"
        
        prompt = f"""
        You are a clarification assistant for an astrology chatbot. Your job is to determine if a question is too vague and needs clarification.
        {history_text}
        
        Current question: "{user_question}"
        
        CRITICAL: If the PREVIOUS assistant message was a clarification question asking which area to focus on, and the current user message is answering that (e.g., "career", "about my career", "health"), then:
        - Extract the area from the user's response
        - Return status: "READY" with the extracted category
        - Combine the original question context with the user's clarification response
        
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
        
        3. Clarification questions should be CONTEXTUAL and help gather facts. Use these examples as inspiration:
           - "Tell me about my kids" → "I'd love to help! How many children do you have, and what specific aspect would you like to know - their education, health, career prospects, or timing of children if you're planning?"
           - "How is my 2026?" → "To provide the most accurate guidance, which area would you like me to focus on? Career, Health, Relationships, Finance, or another specific area?"
           - "Tell me about my career" → "I can help with that! Are you currently employed or running a business? And what specifically would you like to know - job change timing, promotion prospects, salary growth, or career direction?"
           - "What about my marriage" → "I'd be happy to analyze that! Are you currently married, engaged, or looking for marriage? And what aspect concerns you - timing, compatibility, challenges, or harmony?"
           
           Generate similar contextual questions that:
           - Gather factual information (number of kids, marital status, employment status, etc.)
           - Narrow down the specific concern within that topic
           - Sound warm and conversational, not robotic
           - Are tailored to the user's specific question
        
        4. Max 2 clarifications per session - after that, return READY with available info
        
        MODES:
        1. "annual": YEARLY forecasts, specific calendar years (e.g. "How is my 2026?", "What does next year hold?")
        2. "birth": General life analysis, personality, "When will..." timing questions (e.g. "When will I get married?", "What are my strengths?")

        TRANSIT DETECTION:
        - "When will..." questions → needs_transits: true
        - "What period is good for..." → needs_transits: true
        - "How is 2025/next year..." → needs_transits: true
        - "Marriage timing" → needs_transits: true
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
        Response: {{"status": "READY", "mode": "annual", "category": "health", "year": 2026, "needs_transits": true}}
        
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
            
            # print(f"\n📥 INTENT ROUTER RESPONSE:")
            # print(f"Gemini API time: {gemini_time:.3f}s")
            # print(f"Raw response: {response.text}")
            
            cleaned = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned)
            
            total_time = time.time() - intent_start
            # print(f"\n✅ INTENT CLASSIFICATION COMPLETE")
            # print(f"Result: {result}")
            # print(f"Total time: {total_time:.3f}s")
            # print(f"{'='*80}\n")
            
            # Add fallback values if missing
            if 'status' not in result:
                result['status'] = 'READY'  # Default to ready
            if 'extracted_context' not in result:
                result['extracted_context'] = {}
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
                    "status": "READY",
                    "extracted_context": {},
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
                    "status": "READY",
                    "extracted_context": {},
                    "mode": "birth", 
                    "category": "general",
                    "needs_transits": False
                }
