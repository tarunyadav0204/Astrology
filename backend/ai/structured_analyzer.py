import copy
import json
import logging
import os
import re
from typing import Any, Dict, Optional
from ai.response_parser import ResponseParser

logger = logging.getLogger(__name__)


def _usage_from_response(response: Any) -> Dict[str, int]:
    usage_meta = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(usage_meta, "prompt_token_count", 0) or 0)
    output_tokens = int(getattr(usage_meta, "candidates_token_count", 0) or 0)
    cached_tokens = int(getattr(usage_meta, "cached_content_token_count", 0) or 0)
    total_tokens = int(getattr(usage_meta, "total_token_count", 0) or (input_tokens + output_tokens))
    non_cached = max(input_tokens - cached_tokens, 0) if input_tokens > 0 else 0
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_tokens": cached_tokens,
        "non_cached_input_tokens": non_cached,
        "total_tokens": total_tokens,
    }


def _strip_shadbala_from_context_for_llm(obj: Any) -> Any:
    """Remove Shadbala / strength_analysis payloads from context sent to Gemini (analysis parity with chat)."""
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k == "strength_analysis":
                continue
            if "shadbala" in str(k).lower():
                continue
            out[k] = _strip_shadbala_from_context_for_llm(v)
        return out
    if isinstance(obj, list):
        return [_strip_shadbala_from_context_for_llm(x) for x in obj]
    return obj

class StructuredAnalysisAnalyzer:
    """Dedicated analyzer for JSON-only astrological reports"""
    
    def __init__(self, *, llm_lane: str = "analysis"):
        from utils.admin_settings import (
            CHAT_LLM_DEEPSEEK,
            get_analysis_llm_vendor,
            get_report_llm_vendor,
        )

        lane = (llm_lane or "analysis").strip().lower()
        use_report = lane == "report"
        vendor = get_report_llm_vendor() if use_report else get_analysis_llm_vendor()

        if vendor == CHAT_LLM_DEEPSEEK:
            if not os.getenv("DEEPSEEK_API_KEY"):
                raise ValueError("DEEPSEEK_API_KEY not set")
        else:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set")
        from ai.analysis_llm_backend import build_analysis_llm_model, build_report_llm_model

        builder = build_report_llm_model if use_report else build_analysis_llm_model
        self.model, self.model_name, self.vendor = builder()
        self.llm_lane = "report" if use_report else "analysis"

    async def generate_structured_report(
        self,
        question: str,
        context: Dict,
        language: str = 'english',
        *,
        model_override: Optional[Any] = None,
        shared_context_cached: bool = False,
    ) -> Dict:
        """Generates a strict JSON report with interactive term tags."""
        
        system_instruction = f"""
You are a Vedic Astrology Data Engine. Return ONLY raw JSON - no markdown, no explanations.

RULES:
1. Start immediately with {{ - no text before
2. End with }} - no text after  
3. NO ```json blocks
4. Do NOT use XML/HTML tags inside JSON string values. Do not write <term id="...">.
5. Include "glossary" key with term definitions instead of inline term tags
6. Use <br> for line breaks in strings
7. Language: {language}
8. CRITICAL: Each "answer" field must be detailed and comprehensive
9. Provide thorough analysis with specific planetary positions and classical references
10. Include practical guidance and remedies in each answer
"""

        # Serialize context safely (no Shadbala / strength_analysis in LLM payload)
        context_for_llm = _strip_shadbala_from_context_for_llm(copy.deepcopy(context))
        context_json = json.dumps(context_for_llm, indent=2, default=str)
        cache_note = ""
        if shared_context_cached or model_override is not None:
            cache_note = (
                "\n\nCACHED SHARED CONTEXT:\n"
                "Pair-level evidence is already loaded in the cached shared context for this request. "
                "Use it together with the chapter CONTEXT below. Do not invent facts missing from either."
            )
        prompt = (
            f"{system_instruction}{cache_note}\n\n"
            f"CONTEXT:\n{context_json}\n\n"
            f"REQUIRED FIELDS & QUESTIONS:\n{question}"
        )

        try:
            selected_model = model_override or self.model
            logger.debug(
                "analysis_llm call vendor=%s model=%s prompt_chars=%s cached_model=%s",
                self.vendor,
                self.model_name,
                len(prompt),
                "yes" if model_override is not None else "no",
            )
            response = await selected_model.generate_content_async(
                prompt,
                request_options={'timeout': 600}
            )

            usage = _usage_from_response(response)
            raw_text = response.text.strip()
            logger.debug(
                "analysis_llm response vendor=%s model=%s chars=%s input=%s output=%s cached=%s",
                self.vendor,
                self.model_name,
                len(raw_text),
                usage["input_tokens"],
                usage["output_tokens"],
                usage["cached_tokens"],
            )
            
            # Use the existing ResponseParser to handle accidental markers or leakage
            parsed_result = ResponseParser.parse_response(raw_text)
            
            # Attempt to parse the content as JSON
            try:
                # Clean accidental markdown backticks if Gemini ignored the instruction
                json_clean = re.sub(r'^```json\s*|```$', '', parsed_result['content'], flags=re.MULTILINE).strip()
                # Older prompts asked for <term id="..."> labels. Inside JSON strings,
                # the id="..." quotes make otherwise valid JSON impossible to parse.
                # Keep the readable term text and parse the structured payload.
                json_clean = re.sub(
                    r'<term\b[^>]*>(.*?)</term>',
                    r'\1',
                    json_clean,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                
                # Find the main JSON object using bracket counting
                start_idx = json_clean.find('{')
                if start_idx == -1:
                    raise json.JSONDecodeError("No opening brace found", json_clean, 0)
                
                # Count braces to find the proper end
                brace_count = 0
                end_idx = start_idx
                for i in range(start_idx, len(json_clean)):
                    if json_clean[i] == '{':
                        brace_count += 1
                    elif json_clean[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i
                            break
                
                json_clean = json_clean[start_idx:end_idx + 1]
                
                final_data = json.loads(json_clean)
                
                return {
                    'success': True,
                    'data': final_data,
                    'terms': parsed_result['terms'],
                    'glossary': final_data.get('glossary', parsed_result['glossary']),
                    'usage': usage,
                }
            except json.JSONDecodeError as json_error:
                logger.warning(
                    "analysis_llm json parse failed: %s content_preview=%s",
                    json_error,
                    (json_clean[:300] if "json_clean" in locals() else "N/A"),
                )
                # If JSON fails, we still return the content for the frontend fallback logic
                return {
                    'success': True,
                    'is_raw': True,
                    'response': parsed_result['content'],
                    'terms': parsed_result['terms'],
                    'glossary': parsed_result['glossary'],
                    'usage': usage,
                }

        except Exception as e:
            logger.exception("analysis_llm api error: %s", e)
            return {'success': False, 'error': str(e)}
