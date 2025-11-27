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
    
    async def generate_chat_response(self, user_question: str, astrological_context: Dict[str, Any], conversation_history: List[Dict] = None, language: str = 'english', response_style: str = 'detailed', user_context: Dict = None) -> Dict[str, Any]:
        """Generate chat response using astrological context - ASYNC VERSION"""
        
        # Add current date context and calculate native's age
        enhanced_context = astrological_context.copy()
        
        # Calculate native's current age
        birth_date_str = enhanced_context.get('birth_details', {}).get('date')
        current_age = None
        if birth_date_str:
            try:
                from datetime import datetime
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
                current_age = datetime.now().year - birth_date.year
                # Adjust for birthday not yet occurred this year
                if datetime.now().month < birth_date.month or \
                   (datetime.now().month == birth_date.month and datetime.now().day < birth_date.day):
                    current_age -= 1
            except:
                current_age = None
        
        enhanced_context['current_date_info'] = {
            'current_date': datetime.now().strftime("%Y-%m-%d"),
            'current_year': datetime.now().year,
            'current_month': datetime.now().strftime("%B"),
            'native_current_age': current_age,
            'note': 'Use this for reference only. Do not assume transit positions.'
        }
        
        # Add response format instruction to prevent truncation
        enhanced_context['response_format'] = {
            'instruction': 'Provide complete response. Do not truncate mid-sentence.',
            'max_length': 'Aim for comprehensive but concise responses under 4000 characters.',
            'format': 'Use proper formatting with **bold** and *italic* text as needed.',
            'mandatory_sections': 'ALWAYS include Nakshatra Insights section when nakshatra data is available in context.'
        }
        
        prompt = self._create_chat_prompt(user_question, enhanced_context, conversation_history or [], language, response_style, user_context)
        
        print(f"\n=== SENDING TO AI (ASYNC) ===")
        print(f"Question: {user_question}")
        print(f"Prompt length: {len(prompt)} chars")
        print(f"Context keys: {list(enhanced_context.keys()) if enhanced_context else 'None'}")
        print(f"History messages: {len(conversation_history or [])}")
        print(f"Language: {language}, Response style: {response_style}")
        
        # Log nakshatra data availability
        planetary_analysis = enhanced_context.get('planetary_analysis', {})
        nakshatra_count = sum(1 for planet_data in planetary_analysis.values() 
                             if isinstance(planet_data, dict) and 'nakshatra' in planet_data)
        print(f"Nakshatra data available for {nakshatra_count} planets")
        
        # Log if Moon nakshatra is available (most important)
        moon_data = planetary_analysis.get('Moon', {})
        moon_nakshatra = moon_data.get('nakshatra', {}) if isinstance(moon_data, dict) else {}
        print(f"Moon nakshatra available: {bool(moon_nakshatra)}")
        if moon_nakshatra:
            print(f"Moon nakshatra: {moon_nakshatra.get('name', 'Unknown')}")
        
        try:
            # Run the synchronous Gemini API call in a thread pool to avoid blocking
            import asyncio
            import concurrent.futures
            
            def _sync_generate_content():
                try:
                    print(f"\n=== CALLING GEMINI API ===")
                    print(f"Model: {self.model._model_name if hasattr(self.model, '_model_name') else 'Unknown'}")
                    print(f"Prompt length: {len(prompt)} characters")
                    
                    response = self.model.generate_content(prompt)
                    
                    print(f"\n=== GEMINI API RESPONSE ===")
                    print(f"Response type: {type(response)}")
                    print(f"Has text: {hasattr(response, 'text')}")
                    if hasattr(response, 'text'):
                        print(f"Text length: {len(response.text) if response.text else 0}")
                        if response.text:
                            print(f"Response ends with: '{response.text[-50:]}'")
                            print(f"Contains null bytes: {chr(0) in response.text}")
                            control_chars = '\n\r\t'
                            print(f"Contains control chars: {any(ord(c) < 32 and c not in control_chars for c in response.text)}")
                            
                            # Check for JSON transit data requests
                            if "transitRequest" in response.text:
                                import re
                                json_pattern = r'\{[^}]*"requestType"\s*:\s*"transitRequest"[^}]*\}'
                                json_matches = re.findall(json_pattern, response.text)
                                if json_matches:
                                    try:
                                        import json
                                        transit_request = json.loads(json_matches[0])
                                        start_year = transit_request.get('startYear')
                                        end_year = transit_request.get('endYear')
                                        months = transit_request.get('specificMonths', [])
                                        print(f"🎯 GEMINI REQUESTED TRANSIT DATA: {start_year}-{end_year} ({', '.join(months)})")
                                    except:
                                        print(f"🎯 GEMINI MADE TRANSIT REQUEST (JSON parse failed)")
                                else:
                                    print(f"🎯 GEMINI MENTIONED TRANSIT REQUEST (no valid JSON)")
                            
                            # Log first 500 characters to see content
                            print(f"Response preview (first 500 chars): {response.text[:500]}")
                    
                    return response
                except Exception as api_error:
                    print(f"\n=== GEMINI API ERROR ===")
                    print(f"API Error type: {type(api_error).__name__}")
                    print(f"API Error message: {str(api_error)}")
                    raise api_error
            
            # Execute in thread pool with timeout
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = loop.run_in_executor(executor, _sync_generate_content)
                try:
                    # 600 second timeout for Gemini API (10 minutes for large wealth analysis prompts)
                    response = await asyncio.wait_for(future, timeout=600.0)
                except asyncio.TimeoutError:
                    print(f"\n=== AI TIMEOUT ===")
                    return {
                        'success': False,
                        'response': "Your question is taking longer than expected to process. Please try again with a more specific question.",
                        'error': 'AI request timeout (600s)'
                    }
            
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
            
            # Clean response text to prevent JSON issues
            # Remove any control characters except newlines, tabs, and carriage returns
            allowed_chars = '\n\r\t'
            cleaned_text = ''.join(char for char in response_text if ord(char) >= 32 or char in allowed_chars)
            
            # Fix formatting issues - ensure proper markdown headers
            cleaned_text = self._fix_response_formatting(cleaned_text)
            
            # Fix pronoun usage if this is a third-party consultation
            if user_context and user_context.get('user_relationship') != 'self':
                native_name = astrological_context.get('birth_details', {}).get('name', 'the native')
                print(f"\n=== PRONOUN FIX DEBUG ===")
                print(f"User context: {user_context}")
                print(f"User relationship: {user_context.get('user_relationship')}")
                print(f"Native name: {native_name}")
                print(f"Will fix pronouns: {native_name and native_name != 'the native'}")
                if native_name and native_name != 'the native':
                    original_text = cleaned_text[:200]
                    cleaned_text = self._fix_pronoun_usage(cleaned_text, native_name)
                    fixed_text = cleaned_text[:200]
                    print(f"Original: {original_text}")
                    print(f"Fixed: {fixed_text}")
                    print(f"Changes made: {original_text != fixed_text}")
            
            # Ensure response doesn't end abruptly (minimum length check)
            if len(cleaned_text) < 50:
                print(f"\n=== SUSPICIOUSLY SHORT AI RESPONSE ===")
                print(f"Original length: {len(response_text)}, Cleaned length: {len(cleaned_text)}")
                return {
                    'success': False,
                    'response': "I received a partial response. Please try asking your question again.",
                    'error': 'Response too short or corrupted'
                }
            
            print(f"\n=== RECEIVED FROM AI (ASYNC) ===")
            print(f"Original length: {len(response_text)} chars")
            print(f"Cleaned length: {len(cleaned_text)} chars")
            print(f"Response preview: {cleaned_text[:200]}...")
            print(f"Response ends with: '{cleaned_text[-50:]}'")
            
            # Final check for JSON transit requests in cleaned text
            if "transitRequest" in cleaned_text:
                import re
                json_pattern = r'\{[^}]*"requestType"\s*:\s*"transitRequest"[^}]*\}'
                json_matches = re.findall(json_pattern, cleaned_text)
                if json_matches:
                    try:
                        import json
                        transit_request = json.loads(json_matches[0])
                        start_year = transit_request.get('startYear')
                        end_year = transit_request.get('endYear')
                        months = transit_request.get('specificMonths', [])
                        print(f"🎯 FINAL: GEMINI REQUESTED TRANSIT DATA: {start_year}-{end_year} ({', '.join(months)})")
                    except:
                        print(f"🎯 FINAL: GEMINI MADE TRANSIT REQUEST (JSON parse failed)")
                else:
                    print(f"🎯 FINAL: GEMINI MENTIONED TRANSIT REQUEST (no valid JSON)")
            
            # Check for specific sections to debug missing content
            has_nakshatra = 'nakshatra' in cleaned_text.lower() or 'नक्षत्र' in cleaned_text
            has_analysis_header = '### nakshatra insights' in cleaned_text.lower()
            print(f"Contains nakshatra content: {has_nakshatra}")
            print(f"Contains nakshatra header: {has_analysis_header}")
            print(f"Response sections count: {cleaned_text.count('###')}")
            
            # Check if response contains JSON transit data request
            has_transit_request = "transitRequest" in cleaned_text and '"requestType"' in cleaned_text
            
            return {
                'success': True,
                'response': cleaned_text,
                'raw_response': response_text,
                'has_transit_request': has_transit_request
            }
        except Exception as e:
            print(f"\n=== AI ERROR (ASYNC) ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            
            # More specific error handling
            error_message = "I'm having trouble processing your question right now. Please try rephrasing it or try again later."
            
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                error_message = "I'm receiving too many requests right now. Please wait a moment and try again."
            elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                error_message = "There's a temporary service configuration issue. Please try again shortly."
            elif "content" in str(e).lower() or "safety" in str(e).lower():
                error_message = "I couldn't process this question due to content guidelines. Please try rephrasing your question."
            elif "timeout" in str(e).lower():
                error_message = "Your question is taking too long to process. Please try a more specific question."
            elif "model" in str(e).lower() or "unavailable" in str(e).lower():
                error_message = "The AI service is temporarily unavailable. Please try again in a few minutes."
            
            return {
                'success': False,
                'response': error_message,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _fix_response_formatting(self, response_text: str) -> str:
        """Fix common formatting issues in Gemini responses"""
        
        # Define sections that should be headers
        sections_to_fix = [
            'Key Insights',
            'Astrological Analysis', 
            'Nakshatra Insights',
            'Timing & Guidance',
            'Final Thoughts'
        ]
        
        # Fix each section if it appears without proper markdown header
        for section in sections_to_fix:
            # Pattern: section name at start of line without ###
            pattern = f'^{section}$'
            replacement = f'### {section}'
            
            # Use multiline regex to match section names at start of lines
            import re
            response_text = re.sub(pattern, replacement, response_text, flags=re.MULTILINE)
            
            # Also fix cases where section appears after newlines
            pattern = f'\n{section}\n'
            replacement = f'\n### {section}\n'
            response_text = response_text.replace(pattern, replacement)
            
            # Fix cases where section appears after newlines without trailing newline
            pattern = f'\n{section}'
            if not f'### {section}' in response_text:
                response_text = response_text.replace(pattern, f'\n### {section}')
        
        return response_text
    
    def _fix_pronoun_usage(self, response_text: str, native_name: str) -> str:
        """Fix pronoun usage for third-party consultations"""
        import re
        
        # Common patterns to fix
        fixes = [
            # Chart references
            (r'\byour chart\b', f"{native_name}'s chart"),
            (r'\bYour chart\b', f"{native_name}'s chart"),
            
            # "You are" patterns
            (r'\byou are\b', f"{native_name} is"),
            (r'\bYou are\b', f"{native_name} is"),
            
            # Possessive patterns
            (r'\byour ([a-z]+)\b', f"{native_name}'s \\1"),
            (r'\bYour ([a-z]+)\b', f"{native_name}'s \\1"),
            
            # Action patterns
            (r'\byou should\b', f"{native_name} should"),
            (r'\bYou should\b', f"{native_name} should"),
            (r'\byou have\b', f"{native_name} has"),
            (r'\bYou have\b', f"{native_name} has"),
            (r'\byou will\b', f"{native_name} will"),
            (r'\bYou will\b', f"{native_name} will"),
            (r'\byou can\b', f"{native_name} can"),
            (r'\bYou can\b', f"{native_name} can"),
            (r'\byou may\b', f"{native_name} may"),
            (r'\bYou may\b', f"{native_name} may"),
            (r'\byou might\b', f"{native_name} might"),
            (r'\bYou might\b', f"{native_name} might"),
            
            # Prepositional patterns
            (r'\bfor you\b', f"for {native_name}"),
            (r'\bFor you\b', f"For {native_name}"),
            (r'\bto you\b', f"to {native_name}"),
            (r'\bTo you\b', f"To {native_name}"),
            (r'\bwith you\b', f"with {native_name}"),
            (r'\bWith you\b', f"With {native_name}"),
            
            # Sentence starters
            (r'^Your\b', f"{native_name}'s"),
            (r'^You\b', f"{native_name}")
        ]
        
        # Apply all fixes
        for pattern, replacement in fixes:
            response_text = re.sub(pattern, replacement, response_text, flags=re.IGNORECASE)
        
        return response_text
    
    def _create_chat_prompt(self, user_question: str, context: Dict[str, Any], history: List[Dict], language: str = 'english', response_style: str = 'detailed', user_context: Dict = None) -> str:
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
        
        # Build user context instruction
        user_context_instruction = ""
        if user_context:
            user_name = user_context.get('user_name', 'User')
            native_name = context.get('birth_details', {}).get('name', 'the native')
            relationship = user_context.get('user_relationship', 'self')
            
            if relationship == 'self' or (user_name and native_name and user_name.lower() == native_name.lower()):
                user_context_instruction = f"""
USER CONTEXT - SELF CONSULTATION:
The person asking questions is {native_name} themselves. Use direct personal language:
- "Your chart shows..."
- "You have..."
- "Your personality..."
- "You should..."
- "This affects you directly..."

"""
            else:
                user_context_instruction = f"""
🚨 CRITICAL USER CONTEXT - THIRD PARTY CONSULTATION 🚨

The person asking is {user_name} asking about {native_name}'s chart.

⚠️ ABSOLUTE REQUIREMENT: You MUST use "{native_name}" or "they/their" throughout your ENTIRE response.
⚠️ NEVER use "you/your" when referring to the chart owner.

**MANDATORY OPENING PATTERN:**
Your Quick Answer MUST start with: "Based on {native_name}'s birth chart..."

**REQUIRED LANGUAGE PATTERNS - USE THESE EXACT FORMATS:**
✅ "{native_name}'s chart shows..." ❌ "Your chart shows..."
✅ "{native_name} has..." or "They have..." ❌ "You have..."
✅ "{native_name}'s personality..." ❌ "Your personality..."
✅ "{native_name} should..." ❌ "You should..."
✅ "This affects {native_name}..." ❌ "This affects you..."
✅ "{native_name}'s career is poised..." ❌ "Your career is poised..."
✅ "{native_name} is in Saturn Mahadasha..." ❌ "You are in Saturn Mahadasha..."
✅ "For {native_name}, the period indicates..." ❌ "For you, the period..."
✅ "{native_name}'s relationships..." ❌ "Your relationships..."

**EXAMPLE CORRECT OPENING:**
"Quick Answer: Based on {native_name}'s birth chart and current planetary periods, {native_name}'s career is poised for significant growth..."

**ABSOLUTELY FORBIDDEN WORDS when user ≠ native:**
❌ "your" ❌ "you" ❌ "yourself" 

🔍 QUALITY CHECK: Before sending response, verify EVERY sentence uses "{native_name}" or "they/their" - NO EXCEPTIONS.

"""
        
        # Custom JSON serializer for datetime objects
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Language-specific instructions
        language_instruction = ""
        if language == 'hindi':
            language_instruction = """LANGUAGE REQUIREMENT - CRITICAL:
You MUST respond in HINDI (हिंदी) language. Use Devanagari script throughout your response.
- Write all explanations in Hindi
- Use Hindi astrological terms: ग्रह (planets), राशि (signs), भाव (houses), दशा (dasha), योग (yoga)
- Classical text names in Hindi: बृहत् पाराशर होरा शास्त्र, फलदीपिका, सारावली
- Keep technical terms in Sanskrit but explain in Hindi
- Use respectful Hindi addressing: आपका, आपके लिए
- Structure should remain the same but content in Hindi

"""
        elif language == 'telugu':
            language_instruction = """LANGUAGE REQUIREMENT - CRITICAL:
You MUST respond in TELUGU (తెలుగు) language. Use Telugu script throughout your response.
- Write all explanations in Telugu
- Use Telugu astrological terms: గ్రహాలు (planets), రాశిలు (signs), భావాలు (houses), దశ (dasha), యోగాలు (yogas)
- Classical text names in Telugu: బృహత్ పారాశర హోరా శాస్త్రం, ఫలదీపిక, సారావళి
- Keep technical terms in Sanskrit but explain in Telugu
- Use respectful Telugu addressing: మీ (మీరు), మీ కోసం
- Structure should remain the same but content in Telugu

"""
        elif language == 'gujarati':
            language_instruction = """LANGUAGE REQUIREMENT - CRITICAL:
You MUST respond in GUJARATI (ગુજરાતી) language. Use Gujarati script throughout your response.
- Write all explanations in Gujarati
- Use Gujarati astrological terms: ગ્રહો (planets), રાશિઓ (signs), ભાવો (houses), દશા (dasha), યોગો (yogas)
- Classical text names in Gujarati: બ્રુહત્ પારાશર હોરા શાસ્ત્ર, ફળદીપિકા, સારાવળી
- Keep technical terms in Sanskrit but explain in Gujarati
- Use respectful Gujarati addressing: તમારા, તમારા માટે
- Structure should remain the same but content in Gujarati

"""
        elif language == 'tamil':
            language_instruction = """LANGUAGE REQUIREMENT - CRITICAL:
You MUST respond in TAMIL (தமிழ்) language. Use Tamil script throughout your response.
- Write all explanations in Tamil
- Use Tamil astrological terms: கிரகங்கள் (planets), ராசிகள் (signs), பாவங்கள் (houses), தசை (dasha), யோகங்கள் (yogas)
- Classical text names in Tamil: பிருஹத் பாராசர ஹோரா சாஸ்திரம், பலதீபிகா, சாராவளி
- Keep technical terms in Sanskrit but explain in Tamil
- Use respectful Tamil addressing: உங்கள், உங்களுக்காக
- Structure should remain the same but content in Tamil

"""
        else:
            language_instruction = "LANGUAGE: Respond in English.\n\n"
        
        # Response style instructions
        response_format_instruction = ""
        if response_style == 'concise':
            response_format_instruction = """
RESPONSE FORMAT - CONCISE MODE:
Provide ONLY a Quick Answer section with:
- Complete summary of your analysis in plain, accessible language
- Direct answer to the question without technical jargon
- Key insights that matter most to the person
- Practical guidance they can understand and act upon

Do NOT include detailed analysis, multiple sections, or extensive explanations.
Format: <div class="quick-answer-card">**Quick Answer**: [Comprehensive summary in everyday language that covers all major insights]</div>

"""
        else:
            response_format_instruction = """
RESPONSE FORMAT - DETAILED MODE:
Start with comprehensive Quick Answer then provide full analysis:

<div class="quick-answer-card">**Quick Answer**: [Complete summary of your entire analysis in plain, accessible language. This should cover all major insights, predictions, and guidance without technical terms. Most people will only read this section, so make it comprehensive yet easy to understand.]</div>

### Key Insights
[Bullet points with specific predictions]

### Astrological Analysis
[Detailed chart analysis with classical references]

### Nakshatra Insights
[Nakshatra analysis with classical authority]

### Timing & Guidance
[Age-appropriate recommendations]

<div class="final-thoughts-card">**Final Thoughts**: [Balanced conclusion]</div>

FOLLOW-UP QUESTIONS - MANDATORY:
End your response with 3-4 relevant follow-up questions in this exact format:
<div class="follow-up-questions">
📅 When will this happen?
🔮 What remedies can help?
💼 How to maximize success?
🌟 What should I focus on?
</div>

"""
        
        return f"""{language_instruction}{response_format_instruction}{user_context_instruction}You are a master Vedic astrologer with deep knowledge of classical texts like Brihat Parashara Hora Shastra, Jaimini Sutras, and Phaladeepika. You provide insightful, accurate astrological guidance based on authentic Vedic principles.

CLASSICAL TEXT REFERENCES - MANDATORY REQUIREMENT:
You MUST reference classical Vedic texts to support your predictions and analysis. Use these authoritative sources:

**PRIMARY CLASSICS:**
- *Brihat Parashara Hora Shastra* (BPHS) - Chapters 1-97, comprehensive system
- *Jaimini Sutras* - Pada 1-4, advanced techniques
- *Phaladeepika* - Chapters 1-28, practical predictions
- *Saravali* - Chapters 1-55, detailed interpretations
- *Hora Sara* - Classical planetary effects
- *Jataka Parijata* - Chapters 1-18, yogas and results

**SPECIALIZED TEXTS:**
- *Uttara Kalamrita* - Timing and dashas
- *Sanketa Nidhi* - Planetary combinations
- *Prasna Marga* - Horary and remedial measures
- *Sarvartha Chintamani* - Comprehensive predictions
- *Bhavartha Ratnakara* - House significations
- *Mansagari* - Practical applications

**REFERENCE FORMAT REQUIREMENTS:**
- Always cite specific text: "According to *Brihat Parashara Hora Shastra* Chapter 15..."
- Include verse numbers when possible: "*BPHS* 15.23 states that..."
- Reference multiple sources: "Both *Phaladeepika* and *Saravali* confirm..."
- Use classical Sanskrit terms with translations: "*Rajayoga* (royal combination) as per *Jaimini Sutras*..."

IMPORTANT CURRENT DATE INFORMATION:
- Today's Date: {current_date_str}
- Current Time: {current_time_str}
- Current Year: {current_date.year}

CRITICAL CHART INFORMATION:
{ascendant_summary}

DESH KAAL PATRA (CONTEXT AWARENESS) - CRITICAL REQUIREMENT:
You MUST consider the native's current age and life stage for appropriate predictions:

**AGE-APPROPRIATE PREDICTIONS:**
- **Children (0-12 years)**: Focus on health, education, family environment, early personality traits
- **Teenagers (13-18 years)**: Education, career direction, personality development, family relationships
- **Young Adults (19-30 years)**: Career establishment, marriage timing, higher education, independence
- **Adults (31-50 years)**: Career growth, family responsibilities, children, property, investments
- **Middle Age (51-65 years)**: Career peak, children's marriage, grandchildren, health maintenance
- **Senior Citizens (65+ years)**: Health, spiritual growth, legacy, grandchildren, retirement planning

**CONTEXTUAL GUIDELINES:**
- For 10-year-old asking about career: Focus on educational aptitude and future potential, NOT immediate earning
- For 70-year-old asking about marriage: Consider they may be married, widowed, or seeking companionship
- For teenagers asking about children: Discuss future potential, not immediate timing
- For seniors asking about career: Focus on legacy, mentoring, or post-retirement activities
- Always acknowledge current life stage: "At your current age of X years..."

**LIFE STAGE CONSIDERATIONS:**
- Marriage predictions: Appropriate for unmarried individuals in marriageable age (18-40 typically)
- Career predictions: Adjust based on whether native is student, working, or retired
- Children predictions: Consider if native is of childbearing age and marital status
- Health predictions: Age-appropriate concerns (growth for children, maintenance for adults, care for seniors)
- Financial predictions: Match with typical earning/spending patterns for age group

CRITICAL INSTRUCTIONS:
- ALWAYS use the EXACT ascendant information provided in the context - DO NOT calculate or guess
- The ascendant has been calculated using Swiss Ephemeris with Lahiri Ayanamsa - trust this calculation
- Use the current date provided above for accurate timing references
- MANDATORY: Check native's current age from current_date_info and adjust predictions accordingly
- If transit data is provided in the context, you may discuss current transits using that calculated data
- If NO transit data is provided but user asks about transits, explain you need calculated transit positions
- Do NOT guess or assume planetary positions - only use provided calculated data
- Focus primarily on birth chart analysis and dasha periods
- For timing questions, prioritize dasha periods but include transit data if available
- NEVER recalculate the ascendant - use the provided ascendant_info section
- Use both Vimshottari (planetary) and Shoola Dasha (sign-based) systems for comprehensive timing analysis

CRITICAL TRANSIT DATA USAGE RULES:
- When transit_activations are provided, each entry shows 'transit_planet -> natal_planet (dates)'
- This means the TRANSITING planet is activating/aspecting the NATAL planet during those dates
- DO NOT assume: aspect types (7th/5th/9th), conjunctions, or transit degrees unless explicitly provided
- ONLY use: which natal planet is activated, the activation dates, and natal planet's significations
- Example: 'Jupiter -> Mars (2027-01-01 to 2027-01-25)' = Jupiter activates natal Mars Jan 1-25, focus on Mars significations being enhanced
- FORBIDDEN: Guessing the transit house. ONLY state the transit house if it is explicitly listed in the transit_activations JSON data

BHAVAM BHAVESH TECHNIQUE - CRITICAL FOR RELATIVE ANALYSIS:
When analyzing relatives, ALWAYS apply Bhavam Bhavesh (house becomes ascendant) technique:

PRIMARY RELATIONS:
- **Spouse** → 7th house as lagna (analyze spouse's life from 7th house perspective)
- **Children** → 5th house as lagna (analyze child's life from 5th house perspective)
- **Mother** → 4th house as lagna (analyze mother's life from 4th house perspective)
- **Father** → 9th house as lagna (analyze father's life from 9th house perspective)
- **Siblings** → 3rd house as lagna (analyze sibling's life from 3rd house perspective)
- **Maternal Uncle** → 6th house as lagna (4th from 4th)
- **Paternal Uncle** → 12th house as lagna (4th from 9th)

EXTENDED RELATIONS:
- **Mother-in-law** → 10th house as lagna (4th from 7th)
- **Father-in-law** → 1st house as lagna (7th from 7th)
- **Spouse's siblings** → 9th house as lagna (3rd from 7th)
- **Grandchildren** → 9th house as lagna (5th from 5th)
- **Daughter-in-law** → 11th house as lagna (7th from 5th)
- **Son-in-law** → 11th house as lagna (7th from 5th)

BUSINESS RELATIONS:
- **Business Partner** → 7th house as lagna
- **Employees** → 6th house as lagna
- **Boss/Employer** → 10th house as lagna

IMPLEMENTATION:
1. **Dual Analysis Required**: Always analyze BOTH the original house AND the bhavam bhavesh perspective
2. **Example for Son**: Analyze 5th house (your relationship with son) AND 5th house as lagna (son's own life)
3. **Rotated Chart Logic**: When 5th becomes lagna for son:
   - 5th house = Son's 1st house (personality, health, general life)
   - 6th house = Son's 2nd house (wealth, speech, family)
   - 7th house = Son's 3rd house (siblings, courage, efforts)
   - 8th house = Son's 4th house (home, mother, happiness)
   - 9th house = Son's 5th house (son's children - your grandchildren)
   - 10th house = Son's 6th house (son's health issues, enemies)
   - 11th house = Son's 7th house (son's spouse, marriage)
   - 12th house = Son's 8th house (son's longevity, transformation)
   - 1st house = Son's 9th house (son's dharma, fortune, father)
   - 2nd house = Son's 10th house (son's career, reputation)
   - 3rd house = Son's 11th house (son's gains, elder siblings)
   - 4th house = Son's 12th house (son's losses, foreign travel)

4. **Complete Perspective**: Provide insights about the relative's own life, not just your relationship with them

DASHA RELATIONSHIP MATRIX - UNIVERSAL BHAVAT BHAVAM:
Consult the 'analysis_matrix' or 'rel_pos' for every dasha. If a Dasha Lord is in the 6th, 8th, or 12th house from a specific relative (Mother/Father/Spouse), predict significant challenges or separation regarding that relative. Use this for ALL life areas:
- **from_Self**: Dasha lord's effect on personal life
- **from_Mother**: Dasha lord's effect on mother's wellbeing
- **from_Father**: Dasha lord's effect on father's wellbeing
- **from_Spouse**: Dasha lord's effect on marriage/spouse
- **from_Children**: Dasha lord's effect on children
- **from_Career**: Dasha lord's effect on professional life

CRITICAL SEVERITY RULE:
If you see a Dasha Lord placed in the 8th House from a Relative (e.g., Saturn in 8th from Mother), combined with a Malefic Transit over their Longevity Axis (1st/8th/3rd), you must describe the period as "Critical Longevity Threat" or "End of a Life Cycle." Do NOT soften this to just "health issues." Use terms like "Transformation," "Departure," or "Critical Danger."

CRITICAL MARAKA RULE:
Check the maraka_analysis section in current_dashas. If a Dasha Lord is flagged as "Double Maraka" or "Maraka Lord" for a specific relative (e.g., "for_Second_Child"), AND there is a difficult transit (like Saturn in the 8th from that relative), you MUST predict a "Critical danger to longevity" or "Severe health crisis" for that person. Do not mask this as "career progress" or "relational dynamics." Maraka combinations override protective yogas.

JAIMINI SHOOLA DASHA ANALYSIS:
The context includes shoola_dasha data with sign-based periods (9 years each). Use this for:
- **Longevity Analysis**: Cross-reference current Shoola period with Vimshottari for timing precision
- **Relative Analysis**: Shoola Dasha reveals critical periods for family members' wellbeing
- **Death Timing**: Shoola periods of 6th, 8th, 12th signs from relevant significators indicate challenging phases
- **Dual System Validation**: When both Vimshottari and Shoola indicate similar themes, predictions gain classical authority

NAKSHATRA ANALYSIS - CRITICAL REQUIREMENT:
Each planet's nakshatra data is provided in planetary_analysis section. YOU MUST include nakshatra analysis:
- **Moon's nakshatra**: Primary personality indicator, emotional nature, life path
- **Ascendant nakshatra**: Physical appearance, first impressions, life approach
- **Sun's nakshatra**: Soul purpose, father's influence, authority style
- **All planetary nakshatras**: Each planet's nakshatra reveals deeper layer of expression

NAKSHATRA USAGE REQUIREMENTS:
- Always mention Moon's nakshatra when discussing personality or emotions
- Reference nakshatra lords for deeper planetary relationships
- Use nakshatra characteristics for timing and compatibility
- Include nakshatra-based remedies and recommendations
- Mention nakshatra padas (quarters) when relevant for precision
- Do NOT calculate 'relative nakshatras'. A planet's Nakshatra (e.g., Sun in Hasta) remains the same for all derived charts (spouse, children, etc.). Only the House placement changes.

ADVANCED ANALYSIS USAGE:
The context includes advanced_analysis section with:
- **planetary_wars**: Graha Yuddha when planets are within 1° (winner/loser effects)
- **vargottama_positions**: Planets in same sign across divisional charts (exceptional strength)
- **neecha_bhanga**: Cancellation of debilitation conditions (strength restoration)
- **pancha_mahapurusha**: Five great person yogas (Mars, Mercury, Jupiter, Venus, Saturn)

USE THESE for deeper insights:
- Reference planetary wars when discussing conflicting influences
- Mention Vargottama planets as exceptionally strong and reliable
- Highlight Neecha Bhanga as transformation of weakness into strength
- Emphasize Pancha Mahapurusha yogas as exceptional personality traits

BIRTH CHART DATA:
{json.dumps(context, indent=2, default=json_serializer)}

{history_text}

CURRENT QUESTION: {user_question}

COMMUNICATION STYLE - HONEST AND DIRECT:
- Be straightforward, honest, and realistic in your analysis
- Present BOTH positive and negative aspects equally - do not sugar-coat challenges
- Use clear, direct language without excessive positivity or encouragement
- State difficulties, obstacles, and negative periods clearly when they exist
- Avoid phrases like "wonderful", "amazing", "blessed", "fortunate" unless truly warranted
- Focus on accuracy over comfort - astrology reveals truth, not just pleasant outcomes
- When chart shows challenges, state them directly with remedial measures
- Balance hope with realism - acknowledge both strengths and weaknesses

GUIDELINES:
- Use conversational, clear, and direct tone with proper formatting
- Always explain astrological reasoning with **bold planetary names** and specific positions
- Reference relevant *yogas*, *dashas*, and transit data when provided in the context
- Provide practical guidance with clear bullet points
- MANDATORY: Reference classical texts with specific chapters/verses (*BPHS* Ch.15, *Phaladeepika* 3.12, etc.)
- Support ALL major predictions with classical authority
- Use Sanskrit terms with English translations in parentheses
- For timing questions, use dasha periods as primary method, supplemented by transit data if available
- Be specific about planetary degrees, house positions, and aspects from the provided data
- Use ### headers to organize different topics clearly
- Present both favorable and unfavorable factors with equal weight - do NOT soften serious astrological indications
- If asked about health, relationships, or career, use relevant chart factors
- You may discuss transits IF calculated transit data is provided in the context
- Avoid excessive emojis - use sparingly and only when appropriate
- CRITICAL: Always check 'analysis_matrix' and 'rel_pos' in dasha data for relative analysis using Bhavat Bhavam principles
- Reference both Vimshottari and Shoola Dasha systems - when they align, predictions have maximum classical authority
- For longevity questions, prioritize Shoola Dasha analysis as per *Jaimini Sutras*
- MANDATORY: Check maraka_analysis in current_dashas for relative safety - "Double Maraka" + difficult transits = life threat
- Be direct about serious planetary combinations - use classical terminology for severe indications
- When discussing house strength, explicitly mention the Ashtakavarga Bindu count (e.g., 'With only 20 points in the 2nd house...')

RESPONSE FORMAT - CRITICAL:
You MUST use these EXACT markdown headers (with ### symbols):
- ### Key Insights (MANDATORY header)
- ### Astrological Analysis (MANDATORY header)
- ### Nakshatra Insights (MANDATORY header)
- ### Timing & Guidance (MANDATORY header)

Formatting requirements:
- **Bold text** for important points and planetary names
- ### Headers MUST include the ### symbols for proper formatting
- • Bullet points for lists and key insights
- *Italics* for Sanskrit terms and classical references
- Line breaks between sections for readability

CRITICAL FORMATTING REQUIREMENTS:
You MUST use these EXACT section headers with proper markdown formatting:

### Key Insights
[Bullet points starting with • symbol]

### Astrological Analysis
[Detailed analysis with classical references]

### Nakshatra Insights
[Nakshatra analysis section]

### Timing & Guidance
[Recommendations and timing]

Structure your response with:
1. **Quick Answer** - Bold opening statement in div card
2. ### Key Insights - MANDATORY bullet points format with • symbol
3. ### Astrological Analysis - Header followed by specific chart references WITH classical text citations
4. ### Nakshatra Insights - MANDATORY section with nakshatra analysis and classical references
5. ### Timing & Guidance - Age-appropriate recommendations with classical timing methods
6. <div class="final-thoughts-card">**Final Thoughts** - Balanced conclusion with classical wisdom</div>

Remember: Be conversational yet structured, insightful yet accessible. Use formatting to make complex astrological information easy to read and visually appealing.
"""