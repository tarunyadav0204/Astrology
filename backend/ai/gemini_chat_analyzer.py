import google.generativeai as genai
import json
import os
import html
import asyncio
import re
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv
from ai.response_parser import ResponseParser
from ai.flux_image_service import FluxImageService

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
        
        # Initialize Flux image service
        try:
            self.flux_service = FluxImageService()
            print("✅ Flux image service initialized")
        except Exception as e:
            print(f"⚠️ Flux service unavailable: {e}")
            self.flux_service = None
        
        # Standard models (try in order of preference)
        model_names = [
            'models/gemini-3-flash-preview',
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash-exp',
            'models/gemini-2.0-flash',
            'models/gemini-1.5-flash',
            'models/gemini-flash-latest'
        ]
        self.model = None
        self.premium_model = None
        
        # Initialize standard model
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(
                    model_name,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        top_p=0.95,
                        top_k=40
                    )
                )
                print(f"✅ Initialized standard model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        # Initialize premium model (Gemini 3 Pro Preview)
        try:
            self.premium_model = genai.GenerativeModel(
                'models/gemini-3-pro-preview',
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40
                )
            )
            print(f"✅ Initialized premium model: gemini-3-pro-preview")
        except Exception as e:
            print(f"⚠️ Premium model not available, using standard: {e}")
            self.premium_model = self.model
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    async def generate_chat_response(self, user_question: str, astrological_context: Dict[str, Any], conversation_history: List[Dict] = None, language: str = 'english', response_style: str = 'detailed', user_context: Dict = None, premium_analysis: bool = False) -> Dict[str, Any]:
        """Generate chat response using astrological context - ASYNC VERSION"""
        import time
        from utils.admin_settings import is_debug_logging_enabled
        
        debug_logging = is_debug_logging_enabled()
        
        total_request_start = time.time()
        if debug_logging:
            print(f"\n🚀 GEMINI CHAT REQUEST STARTED")
            print(f"🔍 REQUEST TYPE: {'SECOND (with transit data)' if 'transit_activations' in astrological_context else 'FIRST (requesting transit data)'}")
        
        # Add current date context and calculate native's age
        enhanced_context = astrological_context.copy()
        
        # Calculate native's current age
        birth_date_str = enhanced_context.get('birth_details', {}).get('date')
        current_age = None
        if birth_date_str:
            try:
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
            'mandatory_sections': 'ALWAYS include Nakshatra Insights section when nakshatra data is available in context.',
            'header_enforcement': 'You MUST use the exact headers defined in the RESPONSE FORMAT STRUCTURE, especially for Nadi Precision and Sudarshana analysis.',
            'verdict_template': 'For predictions, use Rule J format: "Since this [yoga/event] appears in [X] out of 3 charts, confidence is [X*33]%"'
        }
        
        # Prune context to reduce token load
        # print("✂️ Pruning context to reduce token load...")
        pruned_context = self._prune_context(enhanced_context)
        
        # DEBUG: Check size reduction
        import json
        original_size = len(json.dumps(enhanced_context, default=str))
        pruned_size = len(json.dumps(pruned_context, default=str))
        # print(f"📉 Context compressed: {original_size} -> {pruned_size} chars (Saved {original_size - pruned_size} chars)")
        # print(f"💾 COMPRESSION RATIO: {((original_size - pruned_size) / original_size * 100):.1f}% reduction")
        
        prompt_start = time.time()
        prompt = self._create_chat_prompt(user_question, pruned_context, conversation_history or [], language, response_style, user_context, premium_analysis)
        prompt_time = time.time() - prompt_start
        
      
        
        # Cache optimization indicator
        has_transit_data = 'transit_activations' in enhanced_context
       
        # Determine if this is first or second call
        is_transit_call = 'transit_activations' in enhanced_context
        call_type = "SECOND_CALL_WITH_TRANSIT" if is_transit_call else "FIRST_CALL_REQUEST"
        # print(f"🎯 CALL TYPE DETECTED: {call_type}")
        

        
        # Log nakshatra data availability
        planetary_analysis = enhanced_context.get('planetary_analysis', {})
        nakshatra_count = sum(1 for planet_data in planetary_analysis.values() 
                             if isinstance(planet_data, dict) and 'nakshatra' in planet_data)
        # print(f"Nakshatra data available for {nakshatra_count} planets")
        # print(f"⭐ NAKSHATRA IMPACT: {'Included in cached data' if nakshatra_count > 0 else 'No nakshatra data'}")
        
        # Log if Moon nakshatra is available (most important)
        moon_data = planetary_analysis.get('Moon', {})
        moon_nakshatra = moon_data.get('nakshatra', {}) if isinstance(moon_data, dict) else {}
        # print(f"Moon nakshatra available: {bool(moon_nakshatra)}")
        if moon_nakshatra:
            print(f"🌙 MOON NAKSHATRA: {moon_nakshatra.get('name', 'Unknown')} (cached for future requests)")
        
        gemini_start_time = time.time()
        try:
            # Select model
            selected_model = self.premium_model if premium_analysis and self.premium_model else self.model
            model_type = "Premium (Gemini 3.0)" if premium_analysis and self.premium_model else "Standard"
            
            if debug_logging:
                print(f"\n=== CALLING GEMINI API (ASYNC) ===")
                print(f"Analysis Type: {model_type}")
                print(f"Model: {selected_model._model_name if hasattr(selected_model, '_model_name') else 'Unknown'}")
                print(f"Prompt length: {len(prompt)} characters")
                
                # Log full prompt
                print(f"\n{'='*80}")
                print(f"📤 FULL GEMINI REQUEST PROMPT")
                print(f"{'='*80}")
                print(prompt)
                print(f"\n{'='*80}")
                print(f"📝 END OF REQUEST PROMPT")
                print(f"{'='*80}\n")
            

            
            # CALL GEMINI ASYNC DIRECTLY with SDK timeout
            response = await asyncio.wait_for(
                selected_model.generate_content_async(
                    prompt,
                    request_options={'timeout': 600}
                ),
                timeout=600.0
            )
            
            gemini_total_time = time.time() - gemini_start_time
            total_request_time = time.time() - prompt_start
            
            if debug_logging:
                print(f"\n{'='*80}")
                print(f"📥 GEMINI RESPONSE #{call_type}")
                print(f"{'='*80}")
                if response and hasattr(response, 'text'):
                    response_text_preview = response.text
                    print(f"\n📝 COMPLETE GEMINI RESPONSE (ALL {len(response_text_preview)} CHARACTERS):")
                    print(response_text_preview)
                    print(f"\n{'='*80}")
                    print(f"📄 END OF GEMINI RESPONSE")
                    print(f"{'='*80}")
                    
                    # Log divisional chart mentions
                    divisional_mentions = []
                    for d_chart in ['D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60']:
                        if d_chart in response.text:
                            divisional_mentions.append(d_chart)
                    
                    if divisional_mentions:
                        print(f"\n📊 DIVISIONAL CHARTS MENTIONED: {', '.join(divisional_mentions)}")
                    else:
                        print(f"\n📊 NO DIVISIONAL CHARTS MENTIONED in response")
                else:
                    print(f"No response or empty response")
                print(f"{'='*80}\n")
                
                print(f"⏱️ Gemini API call time: {gemini_total_time:.2f}s")
            
            if not response or not hasattr(response, 'text') or not response.text:
                return {
                    'success': False,
                    'response': "I apologize, but I couldn't generate a response. Please try asking your question again.",
                    'error': 'Empty response from AI'
                }
            
            response_text = response.text.strip()
            if len(response_text) == 0:
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
                if native_name and native_name != 'the native':
                    cleaned_text = self._fix_pronoun_usage(cleaned_text, native_name)
            
            # Ensure response doesn't end abruptly (minimum length check)
            if len(cleaned_text) < 50:
                return {
                    'success': False,
                    'response': "I received a partial response. Please try asking your question again.",
                    'error': 'Response too short or corrupted'
                }
            # print(f"✅ Final response ready ({len(cleaned_text)} chars)")
            # print(f"📤 FINAL CLEANED RESPONSE (first 500 chars): {cleaned_text[:500]}...")
            # print(f"📤 FINAL CLEANED RESPONSE (last 200 chars): ...{cleaned_text[-200:]}")
            
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
                        # print(f"🎯 FINAL: GEMINI REQUESTED TRANSIT DATA: {start_year}-{end_year} ({', '.join(months)})")
                    except:
                        print(f"🎯 FINAL: GEMINI MADE TRANSIT REQUEST (JSON parse failed)")
                else:
                    print(f"🎯 FINAL: GEMINI MENTIONED TRANSIT REQUEST (no valid JSON)")
            
            # Check for specific sections to debug missing content
            has_nakshatra = 'nakshatra' in cleaned_text.lower() or 'नक्षत्र' in cleaned_text
            has_analysis_header = '### nakshatra insights' in cleaned_text.lower()
            # print(f"Contains nakshatra content: {has_nakshatra}")
            # print(f"Contains nakshatra header: {has_analysis_header}")
            # print(f"Response sections count: {cleaned_text.count('###')}")
            
            # Check if response contains JSON transit data request
            has_transit_request = "transitRequest" in cleaned_text and '"requestType"' in cleaned_text
            
            total_request_time = time.time() - total_request_start
            print(f"🚀 TOTAL GEMINI CHAT REQUEST TIME: {total_request_time:.2f}s")
            
            # Log performance summary for caching analysis
            is_transit_call = 'transit_activations' in cleaned_text or 'transit_activations' in str(enhanced_context)
            if is_transit_call:
                print(f"📊 PERFORMANCE SUMMARY - SECOND CALL: Total={total_request_time:.1f}s, Gemini={gemini_total_time:.1f}s")
            else:
                print(f"📊 PERFORMANCE SUMMARY - FIRST CALL: Total={total_request_time:.1f}s, Gemini={gemini_total_time:.1f}s")
            
            # Parse response for terms, glossary, and summary image
            parsed_response = ResponseParser.parse_images_in_chat_response(cleaned_text)
            
            print(f"\n🔍 RESPONSE PARSER DEBUG:")
            print(f"   Terms found: {parsed_response['terms']}")
            print(f"   Glossary keys: {list(parsed_response['glossary'].keys())}")
            print(f"   Summary image prompt exists: {bool(parsed_response.get('summary_image_prompt'))}")
            if parsed_response.get('summary_image_prompt'):
                print(f"   Summary image prompt preview: {parsed_response.get('summary_image_prompt', '')[:100]}...")
            print(f"   Content preview: {parsed_response['content'][:200]}...")
            
            # Generate summary image if prompt exists
            summary_image_url = None
            if self.flux_service and premium_analysis and parsed_response.get('summary_image_prompt'):
                try:
                    print(f"\n🎨 SUMMARY IMAGE GENERATION:")
                    print(f"   Premium analysis: {premium_analysis}")
                    print(f"   Flux service available: {bool(self.flux_service)}")
                    print(f"   Prompt exists: {bool(parsed_response.get('summary_image_prompt'))}")
                    print(f"   Prompt preview: {parsed_response.get('summary_image_prompt', '')[:150]}...")
                    
                    image_result = await self.flux_service.generate_image(parsed_response['summary_image_prompt'])
                    
                    print(f"\n🔍 IMAGE SERVICE RESPONSE:")
                    print(f"   Type: {type(image_result)}")
                    print(f"   Value: {image_result}")
                    print(f"   Is string: {isinstance(image_result, str)}")
                    print(f"   Is truthy: {bool(image_result)}")
                    
                    if image_result:
                        summary_image_url = image_result
                        print(f"   ✅ SUMMARY IMAGE SUCCESS: {summary_image_url}")
                    else:
                        print(f"   ❌ SUMMARY IMAGE FAILED: No URL returned")
                        
                except Exception as e:
                    print(f"   ⚠️ SUMMARY IMAGE EXCEPTION:")
                    print(f"      Error type: {type(e).__name__}")
                    print(f"      Error message: {str(e)}")
                    print(f"      Full error: {repr(e)}")
                    import traceback
                    print(f"      Stack trace: {traceback.format_exc()}")
            else:
                print(f"\n🎨 SUMMARY IMAGE SKIPPED:")
                print(f"   Premium analysis: {premium_analysis}")
                print(f"   Flux service available: {bool(self.flux_service)}")
                print(f"   Prompt exists: {bool(parsed_response.get('summary_image_prompt'))}")
            return {
                'success': True,
                'response': parsed_response['content'],
                'terms': parsed_response['terms'],
                'glossary': parsed_response['glossary'],
                'summary_image': summary_image_url,
                'raw_response': response_text,
                'has_transit_request': has_transit_request,
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time,
                    'gemini_processing_time': gemini_total_time
                }
            }
        except asyncio.TimeoutError:
            total_request_time = time.time() - total_request_start
            print(f"⏰ Gemini API timeout after {total_request_time:.2f}s")
            return {
                'success': False,
                'response': "Your question is taking longer than expected to process. Please try again with a more specific question.",
                'error': 'AI request timeout (600s)',
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time,
                    'gemini_processing_time': 600.0
                }
            }
        except Exception as e:
            total_request_time = time.time() - total_request_start
            print(f"❌ Error in generate_chat_response: {type(e).__name__}: {str(e)}")
            print(f"❌ Full error details: {repr(e)}")
            import traceback
            print(f"❌ Stack trace: {traceback.format_exc()}")
            
            # More specific error handling
            error_message = "I'm having trouble processing your question right now. Please try rephrasing it or try again later."
            
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                error_message = "I'm receiving too many requests right now. Please wait a moment and try again."
            elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                error_message = "There's a temporary service configuration issue. Please try again shortly."
            elif "content" in str(e).lower() or "safety" in str(e).lower():
                error_message = "I couldn't process this question due to content guidelines. Please try rephrasing your question."
            elif "timeout" in str(e).lower() or "deadline" in str(e).lower() or "504" in str(e):
                error_message = "The AI service took too long to respond. Please try a shorter or more specific question."
            elif "model" in str(e).lower() or "unavailable" in str(e).lower():
                error_message = "The AI service is temporarily unavailable. Please try again in a few minutes."
            elif "cancelled" in str(e).lower() or "499" in str(e):
                error_message = "The request was interrupted. Please try asking your question again."
            
            return {
                'success': False,
                'response': error_message,
                'error': str(e),
                'error_type': type(e).__name__,
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time if 'prompt_time' in locals() else 0,
                    'gemini_processing_time': gemini_total_time if 'gemini_total_time' in locals() else 0
                }
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
    
    def _extract_image_prompts(self, response_text: str) -> dict:
        """DEPRECATED: Extract image prompts from Gemini response (old inline method)"""
        return {}
    
    def _prune_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggressively removes heavy, redundant data to reduce token count.
        FIXED: Correctly handles nested dictionary paths found in logs.
        """
        import copy
        clean = copy.deepcopy(context)
        
        # 1. Prune Ashtakavarga (Corrected Logic)
        if 'ashtakavarga' in clean:
            for chart in ['d1_rashi', 'd9_navamsa']:
                if chart in clean['ashtakavarga']:
                    chart_data = clean['ashtakavarga'][chart]
                    
                    # Fix A: 'individual_charts' is inside 'sarvashtakavarga'
                    if 'sarvashtakavarga' in chart_data:
                        if isinstance(chart_data['sarvashtakavarga'], dict):
                            chart_data['sarvashtakavarga'].pop('individual_charts', None)
                    
                    # Fix B: 'bhinnashtakavarga' is at the chart root
                    chart_data.pop('bhinnashtakavarga', None)

        # 2. Prune Bhav Chalit Redundancy - REMOVED FOR ACCURACY
        # Bhava Chalit is CRITICAL for house predictions - planets can be in different houses than signs
        # if 'd1_chart' in clean and 'bhav_chalit' in clean['d1_chart']:
        #     clean['d1_chart'].pop('bhav_chalit', None)

        # 3. Prune Methodologies
        if 'transit_data_availability' in clean:
            clean['transit_data_availability'].pop('comprehensive_analysis_methodology', None)
            clean['transit_data_availability'].pop('quick_answer_requirements', None)
            
        # 4. Remove Response Structure (It's in System Prompt)
        clean.pop('RESPONSE_STRUCTURE_REQUIRED', None)
        
        return clean
    
    def _create_chat_prompt(self, user_question: str, context: Dict[str, Any], history: List[Dict], language: str = 'english', response_style: str = 'detailed', user_context: Dict = None, premium_analysis: bool = False) -> str:
        """Create comprehensive chat prompt for Gemini"""
        
        history_text = ""
        if history:
            history_text = "\n\nCONVERSATION HISTORY:\n"
            # Use last 3 messages for better context retention
            recent_messages = history[-3:] if len(history) >= 3 else history
            for msg in recent_messages:
                question = msg.get('question', '')[:500]  # Max 500 chars
                response = msg.get('response', '')[:500]   # Max 500 chars
                history_text += f"User: {question}\nAssistant: {response}\n\n"

        
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

TECHNICAL TERMS EDUCATION - MANDATORY:
Wrap ALL astrological terms in <term id="key">Term</term> format.

GLOSSARY FORMAT - CRITICAL:
At the very end of your response, add a clean JSON glossary with COMPREHENSIVE, LAYMAN-FRIENDLY definitions in this EXACT format:

GLOSSARY_START
{"d9": "D9 (Navamsa Chart) - A special chart that reveals your destiny, marriage compatibility, and spiritual path."}
GLOSSARY_END

"""
        else:
            # Build image instructions based on premium_analysis flag
            image_instructions = ""
            if premium_analysis:
                image_instructions = """
SUMMARY IMAGE - MANDATORY:
Create a prompt for a COMPOSITE NARRATIVE SKETCH. This image must act as a visual storyboard of your entire analysis.

🚨 STRUCTURE: 
The sketch should be divided into 3 distinct "vignettes" or small scenes within the same frame:
1. LEFT SCENE: Represents the "Current Challenge" (e.g., a person walking through a misty path).
2. CENTER SCENE: Represents the "Core Prediction/Verdict" (e.g., a large golden sun rising over a mountain).
3. RIGHT SCENE: Represents the "Future Outcome" (e.g., a harvest of fruit or a successful journey).

✅ VISUAL STYLE:
- Professional hand-drawn pencil sketch with watercolor washes.
- Use symbolic colors: Deep indigo for challenges, vibrant gold for success, and emerald green for growth.
- Minimalist and clean; avoid clutter.

🔤 TEXT LABELS:
- Use EXACTLY THREE short labels (one for each scene).
- Use ALL CAPS and specify "Clear, elegant, hand-lettered serif font."
- Examples: "CHALLENGE", "SUCCESS", "GROWTH".

Format:
SUMMARY_IMAGE_START
[Detailed prompt describing the three specific scenes, the visual style, and the three text labels.]
SUMMARY_IMAGE_END
"""
            
            response_format_instruction = f"""
RESPONSE FORMAT - DETAILED MODE:
Start with comprehensive Quick Answer then provide full analysis:

⚠️ CRITICAL HEADER FORMATTING RULES - STRICT ENFORCEMENT:
- Main sections use ### (three hashes): Key Insights, Astrological Analysis, Nakshatra Insights, Timing & Guidance
- Subsections use #### (four hashes) and MUST be placed INSIDE the Astrological Analysis section
- ABSOLUTELY FORBIDDEN: Do NOT use # or ## anywhere in your response
- The Parashari View, Jaimini Sutra Deep-Dive, Timing Synthesis, Nadi Precision, Triple Perspective, and Divisional Chart Analysis are ALL #### subsections

🏛️ JAIMINI QUICK ANSWER RULES:
- For STATUS/REPUTATION questions: Use `jaimini_full_analysis['wealth_sutras']['dhana_yoga_status']` as the verdict.
- For MARRIAGE questions: Use `jaimini_full_analysis['marriage_sutras']['marriage_stability']` as the primary answer.
- If Parashari and Jaimini conflict, the Jaimini Arudha (AL/UL) result is the FINAL VERDICT.

CORRECT FORMAT:
<div class="quick-answer-card">**Quick Answer**: [Complete summary using Jaimini verdict for status/marriage]</div>

### Key Insights
[Bullet points with specific predictions]
• **The Jaimini Secret**: [MANDATORY - Insight from `career_talents` or `wealth_sutras`]

### Astrological Analysis
You MUST write content directly under this header, then add subsections with ####. DO NOT leave this section empty.

#### The Parashari View
[Houses/Lords analysis]

#### Jaimini Sutra Deep-Dive (MANDATORY)
[Explain AL 2nd/11th for wealth, UL 2nd for marriage, Karkamsa planets for talents, Karaka yogas]

#### Nadi Precision (if applicable)
[Nadi links analysis]

#### Timing Synthesis
[Vimshottari + Chara Dasha + Yogini]

#### Triple Perspective (if applicable)
[Sudarshana analysis]

#### Divisional Chart Analysis (if applicable)
[D10 for career, D7 for children, D24 for education, etc. - use relevant chart based on question]

### Nakshatra Insights
[Nakshatra analysis with classical authority]

### Timing & Guidance
[Age-appropriate recommendations]

<div class="final-thoughts-card">**Final Thoughts**: [Balanced conclusion]</div>

TECHNICAL TERMS EDUCATION - MANDATORY:
Wrap ALL astrological terms in <term id="key">Term</term> format.

{image_instructions}

GLOSSARY FORMAT - CRITICAL:
At the very end, add JSON glossary:

GLOSSARY_START
{{"term": "definition"}}
GLOSSARY_END

FOLLOW-UP QUESTIONS - MANDATORY:
<div class="follow-up-questions">
📅 When will this happen?
🔮 What remedies can help?
💼 How to maximize success?
🌟 What should I focus on?
</div>

"""
        
        # Import the system instruction from ChatContextBuilder
        from chat.chat_context_builder import ChatContextBuilder
        
        # Check analysis type
        analysis_type = context.get('analysis_type', 'birth')
        
        if analysis_type == 'synastry':
            # Inject actual names into synastry instruction
            native_name = context.get('native', {}).get('birth_details', {}).get('name', 'Native')
            partner_name = context.get('partner', {}).get('birth_details', {}).get('name', 'Partner')
            print(f"\n👥 SYNASTRY MODE DETECTED")
            print(f"   Native: {native_name}")
            print(f"   Partner: {partner_name}")
            system_instruction = ChatContextBuilder.SYNASTRY_SYSTEM_INSTRUCTION.replace('{native_name}', native_name).replace('{partner_name}', partner_name)
            
        elif analysis_type == 'prashna':
            # === PRASHNA MODE ===
            print(f"\n🔮 PRASHNA MODE DETECTED")
            print(f"   Category: {context.get('prashna_focus_category', 'general')}")
            print(f"   Question time: {context.get('question_time', {})}")
            system_instruction = ChatContextBuilder.PRASHNA_SYSTEM_INSTRUCTION
            
        elif analysis_type == 'annual_forecast':
            # === ANNUAL MODE ===
            print(f"\n📅 ANNUAL MODE DETECTED")
            target_year = context.get('focus_year')
            annual_instruction = f"""
## SPECIAL INSTRUCTION: ANNUAL ANALYSIS ({target_year})
You are generating a "Yearly Roadmap". You must synthesize the Birth Chart (Long-term) with the Varshphal (This Year Only).

### SYNTHESIS PROTOCOL (MANDATORY):
1. **The "Background Tone" (Birth Chart):**
   - Check the Vimshottari Dasha (MD/AD/PD). If it is negative (e.g., Saturn-Rahu), the year will have an undercurrent of stress, even if the Varshphal is good.
   
2. **The "Active Focus" (Varshphal):**
   - ⚠️ MANDATORY TERMINOLOGY: You MUST explicitly mention the word **"Muntha"** and its house position from `varshphal['muntha_house']`.
   - ⚠️ MANDATORY TERMINOLOGY: You MUST explicitly mention the current **"Mudda Dasha"** planet from `varshphal['mudda_dasha']` and how it restricts or expands the birth dasha.
   - Example: "Your Muntha is in the 1st House, focusing this year on personal identity, while the Rahu Mudda Dasha (April-June) triggers the impulse to spend."
   - The Muntha house is the "Inescapable Focus" of the year (e.g., Muntha in 6th = Health/Enemies focus).

3. **Response Structure for Annual Queries:**
   - **Quick Answer:** Summarize the year's "Theme" (based on Muntha house).
   - **Key Insights:** List 3 wins and 1 challenge for {target_year}.
   - **Monthly Breakdown:** Group the year into phases based on the Mudda Dasha timeline.
"""
            system_instruction = ChatContextBuilder.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION + "\n\n" + annual_instruction
            
        elif analysis_type == 'mundane':
            # === MUNDANE MODE ===
            print(f"\n🌍 MUNDANE MODE DETECTED")
            from calculators.mundane.mundane_context_builder import MundaneContextBuilder
            system_instruction = MundaneContextBuilder.MUNDANE_SYSTEM_INSTRUCTION
            
            # Override response format for mundane
            response_format_instruction = """
RESPONSE FORMAT - MUNDANE MODE:
Start with Executive Summary then provide geopolitical analysis:

<div class="quick-answer-card">**Executive Summary**: [Complete risk assessment and market outlook in clear, professional language. Cover major economic, political, and market trends.]</div>

### Key Risk Factors
[Bullet points with specific risks and probabilities]

### Economic & Market Analysis
[Detailed analysis with timing and sectors]

### Geopolitical Outlook
[Political stability, conflicts, policy changes]

<div class="final-thoughts-card">**Strategic Outlook**: [Balanced conclusion with actionable insights]</div>

FOLLOW-UP QUESTIONS - MANDATORY:
Generate 3-4 contextually relevant follow-up questions based on the user's query. Examples for mundane analysis:
<div class="follow-up-questions">
📊 Which sectors will outperform?
⚠️ What are the major risk events?
💱 How will currency markets react?
🌍 What geopolitical shifts are likely?
</div>
"""
            
        else:
            # Default to Birth Chart
            system_instruction = ChatContextBuilder.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION
        
        # REORDERED FOR IMPLICIT CACHING: Static data first, dynamic data last
        prompt_parts = []
        
        # 1. STATIC: System Instructions
        prompt_parts.append(system_instruction)
        prompt_parts.append(f"{language_instruction}{response_format_instruction}{user_context_instruction}You are a master Vedic astrologer with deep knowledge of classical texts like Brihat Parashara Hora Shastra, Jaimini Sutras, and Phaladeepika. You provide insightful, accurate astrological guidance based on authentic Vedic principles.")
        
        # 2. STATIC: Birth Chart Data (CRITICAL FIX for caching)
        # Extract dynamic data to keep the static prefix identical across calls
        import copy
        static_context = copy.deepcopy(context)
        
        # Remove transit data from static context to maintain cache consistency
        transits = static_context.pop('transit_activations', None)
        
        # Log context structure
        # if is_synastry:
        #     print(f"\n📋 CONTEXT STRUCTURE (SYNASTRY):")
        #     print(f"   - analysis_type: {static_context.get('analysis_type')}")
        #     print(f"   - native.birth_details: {static_context.get('native', {}).get('birth_details', {}).get('name')}")
        #     print(f"   - partner.birth_details: {static_context.get('partner', {}).get('birth_details', {}).get('name')}")
        #     print(f"   - native context keys: {list(static_context.get('native', {}).keys())[:10]}...")
        #     print(f"   - partner context keys: {list(static_context.get('partner', {}).keys())[:10]}...")
        # else:
        #     print(f"\n📋 CONTEXT STRUCTURE (SINGLE):")
        #     print(f"   - birth_details: {static_context.get('birth_details', {}).get('name')}")
        #     print(f"   - context keys: {list(static_context.keys())[:15]}...")
        
        # Convert ONLY static context to JSON with deterministic ordering
        chart_json = json.dumps(static_context, indent=2, default=json_serializer, sort_keys=True)
        
        # Use appropriate label based on analysis type
        if analysis_type == 'mundane':
            data_label = "MUNDANE ASTROLOGY DATA"
        else:
            data_label = "BIRTH CHART DATA"
        
        prompt_parts.append(f"{data_label}:\n{chart_json}")
        
        print(f"   - Total context size: {len(chart_json)} characters")
        
        # 2.5. INJECT USER SEMANTIC MEMORY (if present)
        user_facts = context.get('user_facts')
        if user_facts:
            facts_text = "KNOWN USER BACKGROUND (Long-Term Memory):\n"
            if isinstance(user_facts, dict):
                for category, items in user_facts.items():
                    fact_str = ", ".join(items) if isinstance(items, list) else str(items)
                    facts_text += f"- {category.upper()}: {fact_str}\n"
            prompt_parts.append(facts_text)
            print(f"   - Injected {len(user_facts)} categories of user memory")
        
        # 3. DYNAMIC: Transit Data (if present) - This breaks cache prefix but that's OK
        if transits:
            transit_json = json.dumps(transits, indent=2, default=json_serializer, sort_keys=True)
            prompt_parts.append(f"PLANETARY TRANSIT DATA (DYNAMIC):\n{transit_json}")
            print(f"   - Transit data included: {len(transits)} activations")

        
        # 4. DYNAMIC: Date/Time (MOVED DOWN - breaks cache here)
        time_context = f"""IMPORTANT CURRENT DATE INFORMATION:
- Today's Date: {current_date_str}
- Current Time: {current_time_str}
- Current Year: {current_date.year}

CRITICAL CHART INFORMATION:
{ascendant_summary}"""
        prompt_parts.append(time_context)
        
        # 5. DYNAMIC: History & Question
        # Add reasoning scratchpad and enforcement checklist
        pd_info = context.get('current_dashas', {}).get('pratyantardasha', {})
        pd_hint = pd_info.get('analysis_hint', 'PD analysis required')
        muntha_house = context.get('varshphal', {}).get('muntha_house', 'N/A')
        has_varshphal = 'varshphal' in context
        vargottama_count = context.get('advanced_analysis', {}).get('vargottama_positions', {}).get('total_vargottama_planets', 0)
        
        reasoning_scratchpad = f"""
### 🔒 LOGIC GATE: PRE-RESPONSE VERIFICATION
Before writing the user response, you MUST internally verify (DO NOT include this in your response to the user):
1. PD_CHECK: Is the Pratyantardasha lord mentioned with its house? ({pd_hint})
2. VARGOTTAMA_VERIFY: List all planets where D1_sign == D9_sign. (Total count: {vargottama_count}. If 0, state "NONE").
3. ASPECT_VERIFY: List the signs aspected by the current Chara Dasha sign using ONLY the 'sign_aspects' mapping.
4. VARSHPHAL_CHECK: {'Did I mention Muntha (House ' + str(muntha_house) + ')?' if has_varshphal else 'Not applicable.'}

After internal verification, provide ONLY the Astrological Chat response (do not show the verification process):
"""
        
        data_supremacy_block = f"""
### ⚖️ THE "DATA OVER TRAINING" LAW
You are currently failing to match Sign IDs correctly. You MUST follow these rules or your response will be rejected:
1. **ASPECT CHECK**: Locate current sign_id in 'sign_aspects'. If the target sign ID is NOT in that list, you are legally forbidden from claiming an aspect.
   - Example: If Sign 9 aspects [1, 4, 7], do NOT mention Sign 0.
2. **HOUSE CHECK**: Do not count houses yourself. Read the 'house' or 'house_number' field in the JSON for every planet in D1, D9, and D10.
3. **NAKSHATRA CHECK**: Do not guess nakshatras. Read the 'nakshatra' string for the Dasha Lord directly from the 'planetary_analysis' object.
"""
        
        rejection_criteria = f"""
### 🚫 REJECTION CRITERIA (LOGICAL INTEGRITY)
Your response will be considered a mathematical and factual failure if:
1. **VARSHPHAL DISCREPANCY**: You mention a Muntha House or Year Lord different from the specific integers provided in the `varshphal` JSON object. You must read, not guess, these values.
2. **SECTION OMISSION**: You omit the #### Triple Perspective (Sudarshana) subsection. This section is mandatory for every analysis.
3. **MUDDA DASHA LOGIC**: If Varshphal data is present, you MUST explicitly name the current 'Mudda Dasha' planet and its significance.
4. **HOUSE SUPREMACY**: You are forbidden from counting houses. You must use the `house` or `house_number` integer assigned to each planet in the JSON. If JSON says house 8, you cannot call it house 1.
5. **TRANSIT DATA SOVEREIGNTY**: You must ONLY discuss transits for planets provided in the `PLANETARY TRANSIT DATA` JSON. If Rahu/Saturn transits are not in the JSON, you are FORBIDDEN from mentioning their current transit positions.
6. **ASPECT ID LOCK**: You must cross-check every aspect. If you claim Sign A aspects Sign B, and Sign ID B is not explicitly listed in `sign_aspects[ID_A]`, your analysis is factually void. There are no exceptions for "planets" or "traditional rules."
"""
        
        enforcement_block = f"""
### 🚨 CRITICAL COMPLIANCE CHECKLIST (MANDATORY)
Before generating your response, verify you have included:
1. **Pratyantar Dasha (3rd level):** {pd_hint} You MUST mention the house number in the RESPONSE BODY, not just internally.
2. **Varshphal Terms:** {'You MUST use the words "Muntha" (House ' + str(muntha_house) + ') AND "Mudda Dasha" in the response body. If you mention Varshphal, you MUST also list the current Mudda Dasha planet from varshphal["mudda_dasha"].' if has_varshphal else 'Not applicable for this query.'}
3. **Jaimini Sign Aspects (MATCHING PROTOCOL):** To prevent errors, you MUST list the sign_id for the current dasha, then list the aspected IDs directly from the sign_aspects dictionary in your hidden thought process. If Sign ID X is not in that list, you are strictly forbidden from claiming an aspect to it. You are strictly prohibited from using your training data to determine aspects.
4. **Vargottama Verification:** Total count is {vargottama_count}. If 0, NO planet is Vargottama. Do not use the term unless verified.
5. **Subsection Headers:** Use #### (four hashes) for all subsections under Astrological Analysis.
"""
        final_warning = f"""
### ⚠️ FINAL WARNING: NO EXTERNAL TRANSITS
You are strictly PROHIBITED from mentioning the transit position or influence of any planet (Saturn, Rahu, Ketu, etc.) if it is not explicitly listed in the `PLANETARY TRANSIT DATA` block.
- If Rahu is not in the transit JSON, you cannot say "Rahu is transiting your 1st house."
- You must act as if you do not know where any planet is unless the JSON defines its transit house for the current period.
"""
        prompt_parts.append(reasoning_scratchpad)
        prompt_parts.append(data_supremacy_block)
        prompt_parts.append(rejection_criteria)
        prompt_parts.append(final_warning)
        prompt_parts.append(enforcement_block)
        prompt_parts.append(f"{history_text}\nCURRENT QUESTION: {user_question}")
        
        full_prompt = "\n\n".join(prompt_parts)
        

        
        return full_prompt