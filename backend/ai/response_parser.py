import re
import json
import html
from typing import Dict, List, Tuple

class ResponseParser:
    """Extracts technical terms and glossary from Gemini responses"""
    
    @staticmethod
    def parse_response(text: str) -> Dict:
        """
        Parses AI response to extract content, terms, and glossary.
        Works for both JSON-based routes and Markdown-based chat.
        """
        # 1. Initialize defaults
        result = {
            'content': text,
            'terms': [],
            'glossary': {}
        }

        # 2. Attempt JSON-first extraction (For Education/Marriage routes)
        json_match = re.search(r'({.*})', text, re.DOTALL)
        if json_match:
            try:
                # Clean and parse the JSON
                clean_json = html.unescape(json_match.group(1))
                parsed_data = json.loads(clean_json)
                
                # If it has a glossary key, extract it
                if isinstance(parsed_data, dict) and 'glossary' in parsed_data:
                    result['glossary'] = parsed_data['glossary']
                    result['terms'] = list(parsed_data['glossary'].keys())
                    # The 'content' remains the full text so the routes can still extract fields
                    return result
            except (json.JSONDecodeError, Exception):
                pass # Fall back to marker-based parsing if JSON is malformed

        # 3. Fallback: Marker-based parsing (For Chat/Analysis)
        if "GLOSSARY_START" in text and "GLOSSARY_END" in text:
            try:
                glossary_part = text.split("GLOSSARY_START")[1].split("GLOSSARY_END")[0].strip()
                # Clean markers and potential backticks/markdown
                glossary_json = re.sub(r'^```(?:json)?\s*|```$', '', glossary_part).strip()
                
                # Try parsing as single JSON object first
                try:
                    parsed_glossary = json.loads(glossary_json)
                    # Normalize all keys to lowercase and strip whitespace
                    result['glossary'] = {k.strip().lower(): v for k, v in parsed_glossary.items()}
                except json.JSONDecodeError:
                    # If that fails, try parsing multiple JSON objects (one per line)
                    result['glossary'] = {}
                    for line in glossary_json.split('\n'):
                        line = line.strip()
                        if line and line.startswith('{'):
                            try:
                                obj = json.loads(line)
                                if 'term' in obj and 'definition' in obj:
                                    result['glossary'][obj['term'].strip().lower()] = obj['definition']
                            except:
                                continue
                
                result['terms'] = list(result['glossary'].keys())
                # Remove the glossary block from the visible content
                result['content'] = text.split("GLOSSARY_START")[0].strip()
                print(f"✅ Glossary parsed: {len(result['terms'])} terms found")
            except Exception as e:
                print(f"⚠️ Marker-based glossary parse failed: {e}")
                print(f"   Glossary part: {glossary_part[:200] if 'glossary_part' in locals() else 'N/A'}...")

        # 4. Extract Terms via Regex (if not already found via glossary keys)
        if not result['terms']:
            term_matches = re.findall(r'<term id="([^"]+)">', text)
            result['terms'] = list(set(term_matches))
            print(f"🔍 Extracted {len(result['terms'])} terms via regex: {result['terms'][:5]}...")
        else:
            print(f"🔍 Using {len(result['terms'])} terms from glossary")

        return result
    
    @staticmethod
    def parse_images_in_chat_response(text: str) -> Dict:
        """
        Specialized, robust parser for chat responses. Extracts summary image, glossary,
        and terms in a single pass, handling truncated responses gracefully.
        """
        print(f"\n🔍 ROBUST PARSER DEBUG:")
        
        content = text
        summary_image_prompt = None
        parsed_glossary = {}
        term_ids = []

        # 1. Extract Summary Image Prompt
        if 'SUMMARY_IMAGE_START' in content and 'SUMMARY_IMAGE_END' in content:
            try:
                prompt_section = content.split('SUMMARY_IMAGE_START')[1].split('SUMMARY_IMAGE_END')[0]
                summary_image_prompt = prompt_section.strip()
                content = re.sub(r'SUMMARY_IMAGE_START.*?SUMMARY_IMAGE_END', '', content, flags=re.DOTALL).strip()
                print(f"   ✅ Extracted summary image prompt ({len(summary_image_prompt)} chars).")
            except Exception as e:
                print(f"   ⚠️ Summary image extraction failed: {e}")

        # 2. Extract and Parse Glossary (handles truncation)
        if 'GLOSSARY_START' in content:
            try:
                # Isolate the glossary part, even if it's cut off
                glossary_part = content.split('GLOSSARY_START')[1]
                if 'GLOSSARY_END' in glossary_part:
                    glossary_part = glossary_part.split('GLOSSARY_END')[0]
                
                # Clean up and find the JSON part
                glossary_json_str = re.sub(r'^```(?:json)?\s*|```$', '', glossary_part).strip()
                
                # Attempt to parse the (potentially partial) JSON
                try:
                    # Find the start of the JSON object
                    json_start = glossary_json_str.find('{')
                    if json_start != -1:
                        # Find the last valid closing brace for a partial parse
                        last_brace = glossary_json_str.rfind('}')
                        json_to_parse = glossary_json_str[json_start : last_brace + 1]
                        
                        # In case of truncation, the JSON might be incomplete.
                        # We can try to fix it by finding the last complete entry.
                        last_comma = json_to_parse.rfind(',')
                        if last_comma > json_to_parse.rfind(':'): # Ensure comma is after the last value
                            json_to_parse = json_to_parse[:last_comma] + '}'
                        
                        parsed_glossary = json.loads(json_to_parse)
                        # Normalize keys
                        parsed_glossary = {k.strip().lower(): v for k, v in parsed_glossary.items()}
                        print(f"   ✅ Glossary parsed ({len(parsed_glossary)} terms).")
                except json.JSONDecodeError:
                    print(f"   ⚠️ JSON decode failed, likely due to truncation. Trying regex fallback.")
                    # Fallback for severely truncated JSON
                    entries = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', glossary_json_str)
                    for k, v in entries:
                        parsed_glossary[k.strip().lower()] = v
                    print(f"   ✅ Glossary recovered via regex ({len(parsed_glossary)} terms).")

                # Clean the glossary block from the final content
                content = re.sub(r'GLOSSARY_START.*', '', content, flags=re.DOTALL).strip()

            except Exception as e:
                print(f"   ⚠️ Major glossary processing failure: {e}")
        
        # 3. Extract Term IDs from the content
        term_ids = re.findall(r'<term id="([^"]+)">', content)
        # Use glossary keys as the definitive list of terms if available
        if parsed_glossary:
            term_ids = list(set(term_ids) | set(parsed_glossary.keys()))
        else:
            term_ids = list(set(term_ids))
            
        print(f"   ✅ Final term list: {len(term_ids)} unique terms.")

        # 4. Extract Follow-up Questions
        follow_up_questions = []
        follow_up_match = re.search(r'<div class="follow-up-questions">(.*?)</div>', content, re.DOTALL)
        if follow_up_match:
            follow_up_html = follow_up_match.group(1)
            # Extract questions from the inner HTML, assuming they are simple text lines
            questions = [line.strip() for line in follow_up_html.split('\n') if line.strip()]
            follow_up_questions = questions
            # Remove the div from the main content
            content = re.sub(r'<div class="follow-up-questions">.*?</div>', '', content, flags=re.DOTALL).strip()
            print(f"   ✅ Extracted {len(follow_up_questions)} follow-up questions.")

        # 5. Extract Analysis Steps
        analysis_steps = []
        steps_match = re.search(r'### Analysis Steps\s*\n([\s\S]*?)(?=\n###|\Z)', content, re.IGNORECASE)
        if steps_match:
            steps_text = steps_match.group(1)
            analysis_steps = [line.replace('-', '').strip() for line in steps_text.split('\n') if line.strip().startswith('-')]
            # Remove the section from the main content
            content = re.sub(r'### Analysis Steps\s*\n([\s\S]*?)(?=\n###|\Z)', '', content, re.IGNORECASE).strip()
            print(f"   ✅ Extracted {len(analysis_steps)} analysis steps.")

        # 6. Assemble final result
        result = {
            'content': content,
            'terms': term_ids,
            'glossary': parsed_glossary,
            'summary_image_prompt': summary_image_prompt,
            'follow_up_questions': follow_up_questions,
            'analysis_steps': analysis_steps,
        }
        
        return result
    
    @staticmethod
    def get_term_definitions(term_ids: List[str], glossary: Dict[str, str]) -> Dict[str, str]:
        """Get definitions for specific term IDs"""
        return {term_id: glossary.get(term_id, f"Definition for {term_id}") 
                for term_id in term_ids}