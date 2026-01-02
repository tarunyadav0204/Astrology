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
                # Clean markers and potential backticks
                glossary_json = re.sub(r'^```json\s*|```$', '', glossary_part).strip()
                result['glossary'] = json.loads(glossary_json)
                result['terms'] = list(result['glossary'].keys())
                # Remove the glossary block from the visible content
                result['content'] = text.split("GLOSSARY_START")[0].strip()
            except Exception as e:
                print(f"⚠️ Marker-based glossary parse failed: {e}")

        # 4. Extract Terms via Regex (if not already found via glossary keys)
        if not result['terms']:
            term_matches = re.findall(r'<term id="([^"]+)">', text)
            result['terms'] = list(set(term_matches))

        return result
    
    @staticmethod
    def get_term_definitions(term_ids: List[str], glossary: Dict[str, str]) -> Dict[str, str]:
        """Get definitions for specific term IDs"""
        return {term_id: glossary.get(term_id, f"Definition for {term_id}") 
                for term_id in term_ids}