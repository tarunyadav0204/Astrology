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
                parsed_glossary = json.loads(glossary_json)
                # Normalize all keys to lowercase and strip whitespace
                result['glossary'] = {k.strip().lower(): v for k, v in parsed_glossary.items()}
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
        Specialized parser for chat responses that extracts single summary image prompt.
        """
        # Aggressive HTML entity decoding
        cleaned_text = text
        while '&lt;' in cleaned_text or '&gt;' in cleaned_text or '&quot;' in cleaned_text:
            cleaned_text = html.unescape(cleaned_text)
        
        print(f"\n🔍 PARSER DEBUG:")
        print(f"   Has SUMMARY_IMAGE: {'SUMMARY_IMAGE_START' in cleaned_text}")
        print(f"   Has GLOSSARY: {'GLOSSARY_START' in cleaned_text}")
        
        # Extract summary image prompt WITHOUT removing content
        summary_image_prompt = None
        if 'SUMMARY_IMAGE_START' in cleaned_text and 'SUMMARY_IMAGE_END' in cleaned_text:
            try:
                prompt_section = cleaned_text.split('SUMMARY_IMAGE_START')[1].split('SUMMARY_IMAGE_END')[0].strip()
                summary_image_prompt = prompt_section.strip()
                # Remove ONLY the image prompt block from visible content, keep everything else
                cleaned_text = re.sub(r'SUMMARY_IMAGE_START.*?SUMMARY_IMAGE_END', '', cleaned_text, flags=re.DOTALL).strip()
                print(f"   ✅ Extracted summary image prompt: {len(summary_image_prompt)} chars")
                print(f"   ✅ Cleaned text after image removal: {len(cleaned_text)} chars")
                print(f"   Has GLOSSARY after cleaning: {'GLOSSARY_START' in cleaned_text}")
            except Exception as e:
                print(f"   ⚠️ Summary image prompt extraction failed: {e}")
        
        # Use the standard parser on the cleaned text
        result = ResponseParser.parse_response(cleaned_text)
        result['summary_image_prompt'] = summary_image_prompt
        print(f"   Final result - Terms: {len(result['terms'])}, Glossary: {len(result['glossary'])}")
        return result
    
    @staticmethod
    def get_term_definitions(term_ids: List[str], glossary: Dict[str, str]) -> Dict[str, str]:
        """Get definitions for specific term IDs"""
        return {term_id: glossary.get(term_id, f"Definition for {term_id}") 
                for term_id in term_ids}