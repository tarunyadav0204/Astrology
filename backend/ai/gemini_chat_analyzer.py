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


def _env_chat_thinking_level_high_enabled() -> bool:
    """Opt out with GEMINI_CHAT_THINKING_LEVEL_HIGH=false if the REST thinking path misbehaves."""
    raw = (os.getenv("GEMINI_CHAT_THINKING_LEVEL_HIGH") or "true").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _normalize_model_id_for_rest(model_name: str) -> str:
    n = (model_name or "").strip()
    if n.startswith("models/"):
        n = n[len("models/") :]
    return n


def _model_supports_gemini3_thinking_level(model_name: str) -> bool:
    """
    thinkingConfig.thinkingLevel is for Gemini 3+ (REST). Gemini 2.5 uses thinkingBudget instead;
    sending thinkingLevel to 2.5 can error, so we only enable for gemini-3* ids.
    """
    mid = _normalize_model_id_for_rest(model_name).lower()
    return "gemini-3" in mid


def _extract_text_from_generate_content_json(data: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for cand in data.get("candidates") or []:
        content = cand.get("content") or {}
        for part in content.get("parts") or []:
            if part.get("thought"):
                continue
            t = part.get("text")
            if t:
                chunks.append(t)
    return "".join(chunks).strip()


def _generate_content_rest_v1beta(
    model_name: str,
    prompt: str,
    api_key: str,
    thinking_level: str = "high",
) -> str:
    """Synchronous REST call; run via asyncio.to_thread. Adds thinkingConfig for Gemini 3."""
    import requests

    mid = _normalize_model_id_for_rest(model_name)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{mid}:generateContent"
    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "topP": 0.95,
            "topK": 40,
            "thinkingConfig": {"thinkingLevel": thinking_level},
        },
    }
    r = requests.post(url, params={"key": api_key}, json=body, timeout=600)
    if not r.ok:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"Gemini REST {r.status_code}: {detail}")
    data = r.json()
    if data.get("promptFeedback", {}).get("blockReason"):
        raise RuntimeError(f"Prompt blocked: {data.get('promptFeedback')}")
    text = _extract_text_from_generate_content_json(data)
    if not text:
        raise RuntimeError("Empty candidates/parts in Gemini REST response")
    return text


class _SimpleTextResponse:
    __slots__ = ("text",)

    def __init__(self, text: str):
        self.text = text or ""


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
        
        from utils.admin_settings import get_gemini_chat_model, get_gemini_premium_model, GEMINI_MODEL_OPTIONS
        
        config_gen_config = genai.GenerationConfig(
            temperature=0,
            top_p=0.95,
            top_k=40
        )
        self._gen_config = config_gen_config
        self._model_cache = {}  # model_name -> GenerativeModel; resolved per request from admin settings
        self.model = None
        self.premium_model = None
        
        # Fallback models at startup (used if per-request model fails)
        preferred_standard = get_gemini_chat_model()
        fallback_standard = [preferred_standard] + [m[0] for m in GEMINI_MODEL_OPTIONS if m[0] != preferred_standard]
        for model_name in fallback_standard:
            try:
                self.model = genai.GenerativeModel(model_name, generation_config=config_gen_config)
                print(f"✅ Initialized fallback standard model: {model_name}")
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        preferred_premium = get_gemini_premium_model()
        try:
            self.premium_model = genai.GenerativeModel(preferred_premium, generation_config=config_gen_config)
            print(f"✅ Initialized fallback premium model: {preferred_premium}")
        except Exception as e:
            print(f"⚠️ Premium model {preferred_premium} not available, using standard: {e}")
            self.premium_model = self.model
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    def _get_model(self, premium_analysis: bool):
        """Resolve model from admin settings for this request (no server restart needed)."""
        from utils.admin_settings import get_gemini_chat_model, get_gemini_premium_model
        name = get_gemini_premium_model() if premium_analysis else get_gemini_chat_model()
        if name in self._model_cache:
            return self._model_cache[name]
        try:
            self._model_cache[name] = genai.GenerativeModel(name, generation_config=self._gen_config)
            return self._model_cache[name]
        except Exception as e:
            print(f"⚠️ Model {name} not available ({e}), using fallback")
            return self.premium_model if premium_analysis and self.premium_model else self.model

    @staticmethod
    def _openai_model_uses_responses_api(model_id: str) -> bool:
        """GPT-5+ flagship models use /v1/responses, not /v1/chat/completions."""
        m = (model_id or "").strip().lower()
        return m.startswith("gpt-5")

    async def _openai_chat_completion(
        self, prompt: str, model_id: str, premium_analysis: bool = False
    ) -> str:
        """OpenAI chat: Chat Completions (GPT-4 family) or Responses API (GPT-5 family)."""
        try:
            from openai import AsyncOpenAI
        except ImportError as e:
            raise RuntimeError(
                "The 'openai' package is not installed. Add it to backend requirements and run: "
                "pip install 'openai>=1.40.0'"
            ) from e

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        model_clean = (model_id or "").strip()
        mid = model_clean.lower()
        client = AsyncOpenAI(api_key=api_key, timeout=600.0)

        if self._openai_model_uses_responses_api(model_clean):
            # https://platform.openai.com/docs/guides/migrate-to-responses — GPT-5 series
            # Prefer low effort for speed; gpt-5.4-pro only accepts medium | high | xhigh (not low).
            if "-pro" in mid:
                reasoning_effort = "medium"
            else:
                reasoning_effort = "low"
            reasoning = {"effort": reasoning_effort}
            print(
                f"🧠 OpenAI Responses API: model={model_clean} "
                f"reasoning.effort={reasoning_effort}"
            )

            resp = await client.responses.create(
                model=model_clean,
                input=prompt,
                max_output_tokens=65536,
                reasoning=reasoning,
            )
            if getattr(resp, "error", None) is not None:
                err = resp.error
                msg = getattr(err, "message", None) or str(err)
                raise RuntimeError(msg)
            content = (resp.output_text or "").strip()
            if not content and getattr(resp, "output", None):
                # Fallback: aggregate text from output items if property missed edge cases
                parts = []
                for item in resp.output:
                    if getattr(item, "type", None) == "message":
                        for block in getattr(item, "content", []) or []:
                            if getattr(block, "type", None) == "output_text":
                                parts.append(getattr(block, "text", "") or "")
                content = "".join(parts).strip()
            if not content:
                raise RuntimeError("Blank OpenAI Responses API output")
            return content

        # Legacy Chat Completions (gpt-4o, gpt-4-turbo, etc.)
        temperature = 1.0 if mid.startswith("o") else 0.0
        resp = await client.chat.completions.create(
            model=model_clean,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=16384,
        )
        if not resp.choices:
            raise RuntimeError("Empty OpenAI choices")
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            raise RuntimeError("Blank OpenAI response content")
        return content

    async def generate_chat_response(
        self,
        user_question: str,
        astrological_context: Dict[str, Any],
        conversation_history: List[Dict] = None,
        language: str = "english",
        response_style: str = "detailed",
        user_context: Dict = None,
        premium_analysis: bool = False,
        mode: str = "default",
        *,
        use_thinking_level_high: bool = False,
    ) -> Dict[str, Any]:
        """Generate chat response using astrological context - ASYNC VERSION.

        use_thinking_level_high: When True (main chat only, after intent READY — not clarifications),
        uses REST v1beta with generationConfig.thinkingConfig.thinkingLevel=high for Gemini 3 models.
        Other models or failures fall back to the standard SDK call.
        """
        import time
        from utils.admin_settings import (
            is_debug_logging_enabled,
            get_chat_llm_provider,
            CHAT_LLM_OPENAI,
            get_openai_chat_model,
            get_openai_premium_model,
            get_gemini_chat_model,
            get_gemini_premium_model,
        )

        debug_logging = is_debug_logging_enabled()
        llm_provider = get_chat_llm_provider()

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
            model_type = "Premium" if premium_analysis else "Standard"
            response = None
            response_text = None
            model_name = ""

            if llm_provider == CHAT_LLM_OPENAI:
                model_name = get_openai_premium_model() if premium_analysis else get_openai_chat_model()
                print(f"🧠 OpenAI chat model: {model_name} ({model_type}, premium_analysis={premium_analysis})")

                if debug_logging:
                    print(f"\n=== CALLING OPENAI API (ASYNC) ===")
                    print(f"Analysis Type: {model_type}")
                    print(f"Model: {model_name}")
                    print(f"Prompt length: {len(prompt)} characters")
                    print(f"\n{'='*80}")
                    print(f"📤 FULL CHAT REQUEST PROMPT")
                    print(f"{'='*80}")
                    print(prompt)
                    print(f"\n{'='*80}")
                    print(f"📝 END OF REQUEST PROMPT")
                    print(f"{'='*80}\n")
                    prompt_size = len(prompt)
                    print(f"\n📏 OPENAI REQUEST SIZE: {prompt_size:,} characters ({prompt_size / 1024:.1f} KB)")

                response_text = await asyncio.wait_for(
                    self._openai_chat_completion(prompt, model_name, premium_analysis),
                    timeout=600.0,
                )
            else:
                # Resolve Gemini model from admin settings (no server restart needed)
                model_name = get_gemini_premium_model() if premium_analysis else get_gemini_chat_model()
                selected_model = self._get_model(premium_analysis)
                print(f"🧠 Gemini chat model: {model_name} ({model_type}, premium_analysis={premium_analysis})")

                if debug_logging:
                    print(f"\n=== CALLING GEMINI API (ASYNC) ===")
                    print(f"Analysis Type: {model_type}")
                    print(f"Model: {model_name}")
                    print(f"Prompt length: {len(prompt)} characters")
                    print(f"\n{'='*80}")
                    print(f"📤 FULL GEMINI REQUEST PROMPT")
                    print(f"{'='*80}")
                    print(prompt)
                    print(f"\n{'='*80}")
                    print(f"📝 END OF REQUEST PROMPT")
                    print(f"{'='*80}\n")
                    prompt_size = len(prompt)
                    prompt_char_count = len(prompt)
                    print(f"\n📏 GEMINI REQUEST SIZE: {prompt_char_count:,} characters ({prompt_size / 1024:.1f} KB)")

                api_key = os.getenv("GEMINI_API_KEY") or ""
                try_high_thinking = False
                if try_high_thinking:
                    try:
                        print(
                            f"🧩 Gemini chat: using REST thinkingLevel=high (model={model_name})"
                        )
                        raw = await asyncio.wait_for(
                            asyncio.to_thread(
                                _generate_content_rest_v1beta,
                                model_name,
                                prompt,
                                api_key,
                                "high",
                            ),
                            timeout=600.0,
                        )
                        response = _SimpleTextResponse(raw)
                    except Exception as rest_err:
                        print(
                            f"⚠️ REST thinkingLevel path failed ({type(rest_err).__name__}: {rest_err}); "
                            f"falling back to google-generativeai SDK"
                        )
                if response is None:
                    response = await asyncio.wait_for(
                        selected_model.generate_content_async(
                            prompt,
                            request_options={"timeout": 600},
                        ),
                        timeout=600.0,
                    )

                if response and hasattr(response, "text") and response.text:
                    response_text = response.text.strip()

            gemini_total_time = time.time() - gemini_start_time
            total_request_time = time.time() - prompt_start

            if debug_logging:
                tag = "OPENAI" if llm_provider == CHAT_LLM_OPENAI else "GEMINI"
                print(f"\n{'='*80}")
                print(f"📥 {tag} RESPONSE #{call_type}")
                print(f"{'='*80}")
                preview = (response_text or "") if response_text is not None else (
                    (response.text or "") if response and hasattr(response, "text") else ""
                )
                if preview:
                    print(f"\n📝 COMPLETE {tag} RESPONSE (ALL {len(preview)} CHARACTERS):")
                    print(preview)
                    print(f"\n{'='*80}")
                    print(f"📄 END OF {tag} RESPONSE")
                    print(f"{'='*80}")
                    divisional_mentions = []
                    for d_chart in ['D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60']:
                        if d_chart in preview:
                            divisional_mentions.append(d_chart)
                    if divisional_mentions:
                        print(f"\n📊 DIVISIONAL CHARTS MENTIONED: {', '.join(divisional_mentions)}")
                    else:
                        print(f"\n📊 NO DIVISIONAL CHARTS MENTIONED in response")
                else:
                    print("No response or empty response")
                print(f"{'='*80}\n")
                print(f"⏱️ {tag} API call time: {gemini_total_time:.2f}s")

            if not response_text:
                return {
                    'success': False,
                    'response': "I apologize, but I couldn't generate a response. Please try asking your question again.",
                    'error': 'Empty response from AI',
                    'chat_llm_model': model_name or None,
                    'timing': {
                        'chat_llm_provider': llm_provider,
                        'chat_llm_model': model_name or None,
                    },
                }

            if len(response_text) == 0:
                return {
                    'success': False,
                    'response': "I received your question but couldn't generate a proper response. Please try rephrasing your question.",
                    'error': 'Blank response from AI',
                    'chat_llm_model': model_name or None,
                    'timing': {
                        'chat_llm_provider': llm_provider,
                        'chat_llm_model': model_name or None,
                    },
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
                    'error': 'Response too short or corrupted',
                    'chat_llm_model': model_name or None,
                    'timing': {
                        'chat_llm_provider': llm_provider,
                        'chat_llm_model': model_name or None,
                    },
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
                'chat_llm_model': model_name or None,
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time,
                    'gemini_processing_time': gemini_total_time,
                    'chat_llm_provider': llm_provider,
                    'chat_llm_model': model_name or None,
                },
            }
        except asyncio.TimeoutError:
            total_request_time = time.time() - total_request_start
            print(f"⏰ Chat LLM API timeout after {total_request_time:.2f}s")
            _mn = model_name if "model_name" in locals() else None
            return {
                'success': False,
                'response': "Your question is taking longer than expected to process. Please try again with a more specific question.",
                'error': 'AI request timeout (600s)',
                'chat_llm_model': _mn,
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time,
                    'gemini_processing_time': 600.0,
                    'chat_llm_provider': llm_provider,
                    'chat_llm_model': _mn,
                },
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
            
            # More specific error handling (never expose raw provider payloads to end users)
            err_l = str(e).lower()
            error_message = "I'm having trouble processing your question right now. Please try rephrasing it or try again later."

            if (
                "429" in str(e)
                or "insufficient_quota" in err_l
                or "rate_limit" in err_l
                or "too many requests" in err_l
                or err_l.strip().startswith("429")
            ):
                error_message = (
                    "Our AI assistant is temporarily unavailable due to high demand or usage limits. "
                    "Please try again in a few minutes."
                )
            elif "quota" in err_l and "billing" in err_l:
                error_message = (
                    "The AI service limit was reached. Please try again later."
                )
            elif "quota" in err_l or "rate limit" in err_l:
                error_message = "I'm receiving too many requests right now. Please wait a moment and try again."
            elif "api key" in err_l or "authentication" in err_l:
                error_message = "There's a temporary service configuration issue. Please try again shortly."
            elif "content" in str(e).lower() or "safety" in str(e).lower():
                error_message = "I couldn't process this question due to content guidelines. Please try rephrasing your question."
            elif "timeout" in str(e).lower() or "deadline" in str(e).lower() or "504" in str(e):
                error_message = "The AI service took too long to respond. Please try a shorter or more specific question."
            elif "model" in str(e).lower() or "unavailable" in str(e).lower():
                error_message = "The AI service is temporarily unavailable. Please try again in a few minutes."
            elif "cancelled" in str(e).lower() or "499" in str(e):
                error_message = "The request was interrupted. Please try asking your question again."
            elif llm_provider == CHAT_LLM_OPENAI and (
                "openai" in type(e).__module__.lower()
                or "openai" in err_l
            ):
                error_message = (
                    "The AI assistant could not complete this answer. Please try again in a moment, "
                    "or rephrase your question."
                )
            
            _mn = model_name if "model_name" in locals() else None
            return {
                'success': False,
                'response': error_message,
                'error': str(e),
                'error_type': type(e).__name__,
                'chat_llm_model': _mn,
                'timing': {
                    'total_request_time': total_request_time,
                    'prompt_creation_time': prompt_time if 'prompt_time' in locals() else 0,
                    'gemini_processing_time': gemini_total_time if 'gemini_total_time' in locals() else 0,
                    'chat_llm_provider': llm_provider,
                    'chat_llm_model': _mn,
                },
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