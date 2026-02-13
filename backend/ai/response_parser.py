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
        Specialized, robust parser for chat responses. Extracts structured data
        in a specific order and cleans the content for display.
        """
        import html
        print(f"\n🔍 ROBUST PARSER V3 DEBUG:")
        
        # Decode ALL HTML entities in the raw text FIRST
        # Manual replacement FIRST for literal entity strings
        content = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
        # Then html.unescape for any standard HTML entities
        prev = None
        while prev != content:
            prev = content
            content = html.unescape(content)

        summary_image_prompt = None
        parsed_glossary = {}
        term_ids = []
        follow_up_questions = []
        analysis_steps = []

        # 1. Extract Summary Image Prompt
        if 'SUMMARY_IMAGE_START' in content and 'SUMMARY_IMAGE_END' in content:
            try:
                prompt_section = content.split('SUMMARY_IMAGE_START')[1].split('SUMMARY_IMAGE_END')[0]
                summary_image_prompt = prompt_section.strip()
                content = re.sub(r'SUMMARY_IMAGE_START.*?SUMMARY_IMAGE_END', '', content, flags=re.DOTALL)
                print(f"   ✅ Extracted summary image prompt.")
            except Exception as e:
                print(f"   ⚠️ Summary image extraction failed: {e}")

        # 2. Extract and Parse Glossary
        if 'GLOSSARY_START' in content and 'GLOSSARY_END' in content:
            try:
                glossary_part = content.split('GLOSSARY_START')[1].split('GLOSSARY_END')[0]
                glossary_json_str = re.sub(r'^```(?:json)?\s*|```$', '', glossary_part).strip()
                
                data = json.loads(glossary_json_str)
                if isinstance(data, list):
                    parsed_glossary = {item['term'].strip().lower(): item['description'] for item in data if 'term' in item and 'description' in item}
                elif isinstance(data, dict):
                    parsed_glossary = {k.strip().lower(): v for k, v in data.items()}
                
                content = re.sub(r'GLOSSARY_START.*?GLOSSARY_END', '', content, flags=re.DOTALL)
                print(f"   ✅ Glossary parsed ({len(parsed_glossary)} terms).")
            except Exception as e:
                print(f"   ⚠️ Glossary error: {e}")
        
        # 3. Extract Follow-up Questions from DECODED content (Hybrid Parser)
        print(f"   Checking for follow-up in decoded content: {'<div class="follow-up-questions">' in content}")
        follow_up_match = re.search(r'<div class="follow-up-questions">(.*?)</div>', content, re.DOTALL)
        if follow_up_match:
            print(f"   Found follow-up match!")
            question_block = follow_up_match.group(1).strip()
            print(f"   Question block: {question_block[:250]}")

            # 1. Try parsing as a list first (the new preferred format)
            possible_questions = question_block.split('\n')
            for line in possible_questions:
                cleaned_line = line.strip()
                if cleaned_line.startswith('-') or cleaned_line.startswith('❓'):
                    question_text = re.sub(r'^[\s\-❓*•]+', '', cleaned_line).strip()
                    if question_text:
                        follow_up_questions.append(question_text)
            
            print(f"   Found {len(follow_up_questions)} questions from list format.")

            # 2. If list parsing fails, fall back to div-based parsing
            if not follow_up_questions:
                print(f"   List parsing failed, falling back to div parsing.")
                q_matches = re.findall(r'<div>(.*?)</div>', question_block, re.DOTALL)
                print(f"   Found {len(q_matches)} questions from div format.")
                for q in q_matches:
                    cleaned_q = re.sub(r'^[\s❓*•-]+', '', q).strip()
                    if cleaned_q:
                        follow_up_questions.append(cleaned_q)

            # Remove the entire follow-up questions block from the content
            content = re.sub(r'<div class="follow-up-questions">.*?</div>', '', content, flags=re.DOTALL)
        else:
            print(f"   No follow-up match found")
        
        print(f"   ✅ Extracted {len(follow_up_questions)} follow-up questions.")
        if follow_up_questions:
            print(f"   📋 Questions: {follow_up_questions}")

        # 4. Extract Analysis Steps
        steps_match = re.search(r'### Analysis Steps\s*\n([\s\S]*?)(?=\n###|\Z)', content, re.IGNORECASE)
        if steps_match:
            steps_text = steps_match.group(1)
            analysis_steps = [line.replace('-', '').strip() for line in steps_text.split('\n') if line.strip().startswith('-')]
            content = re.sub(r'### Analysis Steps\s*\n([\s\S]*?)(?=\n###|\Z)', '', content, re.IGNORECASE)
            print(f"   ✅ Extracted {len(analysis_steps)} analysis steps.")

        # 5. Get all Term IDs from the content and glossary
        term_ids_from_content = re.findall(r'<term id="([^"]+)">', content)
        term_ids_from_glossary = list(parsed_glossary.keys())
        term_ids = list(set(term_ids_from_content) | set(term_ids_from_glossary))
        print(f"   ✅ Final term list: {len(term_ids)} unique terms.")
        
        # NOTE: Term tags are intentionally NOT stripped. The UI will handle them.
        print(f"   ✅ Term tags intentionally left in content for UI parsing.")

        # 6. Assemble final result
        result = {
            'content': content.strip(),
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