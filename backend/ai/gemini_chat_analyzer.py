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
            replicate_token = os.getenv('REPLICATE_API_TOKEN')
            if replicate_token:
                self.flux_service = FluxImageService()
                print(f"✅ Flux image service initialized successfully")
                print(f"   Token present: {bool(replicate_token)}")
                print(f"   Token length: {len(replicate_token) if replicate_token else 0}")
            else:
                self.flux_service = None
                print(f"⚠️ REPLICATE_API_TOKEN not found in environment")
                print(f"   Image generation will be disabled")
        except Exception as e:
            print(f"⚠️ Flux service initialization failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Image generation will be disabled")
            self.flux_service = None
        
        # Standard models (try in order of preference)
        model_names = [
            'models/gemini-3-flash-preview',
            'models/gemini-2.5-flash',
        ]
        self.model = None
        self.premium_model = None
        
        # Initialize standard model
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(
                    model_name,
                    generation_config=genai.GenerationConfig(
                        temperature=0,
                        top_p=0.95,
                        top_k=40
                    )
                )
                print(f"✅ Initialized standard model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        # Initialize premium model (Gemini 3 Flash Preview)
        try:
            self.premium_model = genai.GenerativeModel(
                'models/gemini-3-flash-preview',
                generation_config=genai.GenerationConfig(
                    temperature=0,
                    top_p=0.95,
                    top_k=40
                )
            )
            print(f"✅ Initialized premium model: gemini-3-flash-preview")
        except Exception as e:
            print(f"⚠️ Premium model not available, using standard: {e}")
            self.premium_model = self.model
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    async def generate_chat_response(self, user_question: str, astrological_context: Dict[str, Any], conversation_history: List[Dict] = None, language: str = 'english', response_style: str = 'detailed', user_context: Dict = None, premium_analysis: bool = False, mode: str = 'default') -> Dict[str, Any]:
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
            'mandatory_sections': 'ALWAYS include Nakshatra Insights section when nakshatra data is available in context.',
            'header_enforcement': 'You MUST use the exact headers defined in the RESPONSE FORMAT STRUCTURE, especially for Nadi Precision and Sudarshana analysis.'
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
        prompt = self._create_chat_prompt(user_question, pruned_context, conversation_history or [], language, response_style, user_context, premium_analysis, mode=mode)
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
            model_type = "Premium (Gemini 3.0 Flash)" if premium_analysis and self.premium_model else "Standard"
            
            
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
            

                # Log request size before sending to Gemini
                prompt_size = len(prompt)
                prompt_char_count = len(prompt)
                print(f"\n📏 GEMINI REQUEST SIZE: {prompt_char_count:,} characters ({prompt_size / 1024:.1f} KB)")
                
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
            
            # Parse and strip FAQ_META line (category + canonical_question for dashboard/FAQs)
            cleaned_text, faq_metadata = ResponseParser.parse_faq_metadata(cleaned_text)
            if faq_metadata:
                print(f"   📋 FAQ_META: category={faq_metadata.get('category')}, canonical_question={faq_metadata.get('canonical_question', '')[:50]}...")
            
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
            
            # Parse response for images / follow-ups / analysis steps
            parsed_response = ResponseParser.parse_images_in_chat_response(cleaned_text)

            # Resolve terms & glossary using our own glossary_terms table
            from ai.term_matcher import find_terms_in_text
            matched_term_ids, matched_glossary = find_terms_in_text(parsed_response['content'], language=language)

            print(f"\n🔍 RESPONSE PARSER DEBUG:")
            print(f"   Matched terms from glossary_terms: {matched_term_ids}")
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
                'terms': matched_term_ids,
                'glossary': matched_glossary,
                'summary_image': summary_image_url,
                'follow_up_questions': parsed_response.get('follow_up_questions', []),
                'analysis_steps': parsed_response.get('analysis_steps', []),
                'faq_metadata': faq_metadata,
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
            stack_trace = traceback.format_exc()
            print(f"❌ Stack trace: {stack_trace}")
            
            # Log error to database
            try:
                self._log_backend_error(
                    user_question=user_question,
                    error=e,
                    stack_trace=stack_trace,
                    astrological_context=astrological_context,
                    user_context=user_context
                )
            except Exception as log_error:
                print(f"⚠️ Failed to log error to database: {log_error}")
            
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
    
    
    def _log_backend_error(self, user_question: str, error: Exception, stack_trace: str, astrological_context: Dict, user_context: Dict = None):
        """Log backend errors to database for admin monitoring"""
        from utils.error_logger import log_chat_error
        
        user_id = user_context.get('user_id') if user_context else None
        username = user_context.get('user_name', 'Unknown') if user_context else 'Unknown'
        phone = user_context.get('user_phone', '') if user_context else ''
        birth_data = astrological_context.get('birth_details', {})
        
        log_chat_error(user_id, username, phone, error, user_question, birth_data, 'backend')
    
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

        # 2. Prune Bhav Chalit Redundancy
        if 'd1_chart' in clean and 'bhav_chalit' in clean['d1_chart']:
            clean['d1_chart'].pop('bhav_chalit', None)

        # 3. Prune Methodologies
        if 'transit_data_availability' in clean:
            clean['transit_data_availability'].pop('comprehensive_analysis_methodology', None)
            clean['transit_data_availability'].pop('quick_answer_requirements', None)
            
        # 4. Remove Response Structure (It's in System Prompt)
        clean.pop('RESPONSE_STRUCTURE_REQUIRED', None)
        
        # 5. Prune Transit Activations for long periods
        if 'transit_activations' in clean and isinstance(clean['transit_activations'], list):
            activations = clean['transit_activations']
            if len(activations) > 20:
                # If too many activations, prune less important fields to save tokens
                for act in activations:
                    # Remove redundant or heavy fields
                    act.pop('all_aspects_cast', None)
                    if 'ashtakavarga_filter' in act:
                        # Keep only the essential strength info
                        filter_data = act['ashtakavarga_filter']
                        act['ashtakavarga_filter'] = {
                            'sav': filter_data.get('sav_points'),
                            'bav': filter_data.get('bav_points'),
                            'strength': filter_data.get('final_strength')
                        }
                
                # If still too many (e.g. > 50), prioritize slow moving planets
                if len(activations) > 50:
                    slow_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu']
                    prioritized = [a for a in activations if a.get('transit_planet') in slow_planets]
                    others = [a for a in activations if a.get('transit_planet') not in slow_planets]
                    
                    # Keep all slow ones, and some of the others if space permits
                    clean['transit_activations'] = prioritized + others[:20]
                    # print(f"✂️ Pruned transit_activations from {len(activations)} to {len(clean['transit_activations'])}")

        return clean
    
    def _create_chat_prompt(self, user_question: str, context: Dict[str, Any], history: List[Dict], language: str = 'english', response_style: str = 'detailed', user_context: Dict = None, premium_analysis: bool = False, mode: str = 'default') -> str:
        """Create comprehensive chat prompt for Gemini by calling the centralized builder."""
        from ai.output_schema import build_final_prompt
        return build_final_prompt(user_question, context, history, language, response_style, user_context, premium_analysis, mode)