import google.generativeai as genai
import json
import os
import re
from typing import Dict, Any
from ai.response_parser import ResponseParser

class StructuredAnalysisAnalyzer:
    """Dedicated analyzer for JSON-only astrological reports"""
    
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('models/gemini-3-flash-preview')

    async def generate_structured_report(self, question: str, context: Dict, language: str = 'english') -> Dict:
        """Generates a strict JSON report with interactive term tags."""
        
        system_instruction = f"""
You are a Vedic Astrology Data Engine. Return ONLY raw JSON - no markdown, no explanations.

RULES:
1. Start immediately with {{ - no text before
2. End with }} - no text after  
3. NO ```json blocks
4. Wrap astrological terms: <term id="key">Term</term>
5. Include "glossary" key with term definitions
6. Use <br> for line breaks in strings
7. Language: {language}
8. CRITICAL: Each "answer" field must be detailed and comprehensive
9. Provide thorough analysis with specific planetary positions and classical references
10. Include practical guidance and remedies in each answer
"""

        # Serialize context safely
        context_json = json.dumps(context, indent=2, default=str)
        prompt = f"{system_instruction}\n\nCONTEXT:\n{context_json}\n\nREQUIRED FIELDS & QUESTIONS:\n{question}"

        try:
            print(f"🔄 CALLING GEMINI API with prompt length: {len(prompt)} chars")
            response = await self.model.generate_content_async(
                prompt,
                request_options={'timeout': 600}
            )
            
            raw_text = response.text.strip()
            print(f"📝 RAW GEMINI RESPONSE:")
            print(f"   Length: {len(raw_text)} chars")
            print(f"   First 500 chars: {raw_text[:500]}")
            print(f"   Last 200 chars: {raw_text[-200:]}")
            
            # Use the existing ResponseParser to handle accidental markers or leakage
            parsed_result = ResponseParser.parse_response(raw_text)
            print(f"📊 PARSED RESULT:")
            print(f"   Content length: {len(parsed_result['content'])} chars")
            print(f"   Terms count: {len(parsed_result['terms'])}")
            print(f"   Glossary count: {len(parsed_result['glossary'])}")
            
            # Attempt to parse the content as JSON
            try:
                # Clean accidental markdown backticks if Gemini ignored the instruction
                json_clean = re.sub(r'^```json\s*|```$', '', parsed_result['content'], flags=re.MULTILINE).strip()
                
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
                
                print(f"🧹 CLEANED JSON (first 300 chars): {json_clean[:300]}")
                final_data = json.loads(json_clean)
                print(f"✅ JSON PARSING SUCCESSFUL")
                
                return {
                    'success': True,
                    'data': final_data,
                    'terms': parsed_result['terms'],
                    'glossary': final_data.get('glossary', parsed_result['glossary'])
                }
            except json.JSONDecodeError as json_error:
                print(f"❌ JSON PARSING FAILED: {json_error}")
                print(f"   Cleaned content (first 500 chars): {json_clean[:500] if 'json_clean' in locals() else 'N/A'}")
                # If JSON fails, we still return the content for the frontend fallback logic
                return {
                    'success': True,
                    'is_raw': True,
                    'response': parsed_result['content'],
                    'terms': parsed_result['terms'],
                    'glossary': parsed_result['glossary']
                }

        except Exception as e:
            print(f"❌ GEMINI API ERROR: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"   Full traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}