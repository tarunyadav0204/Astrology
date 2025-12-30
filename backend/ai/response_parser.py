import re
import json
from typing import Dict, List, Tuple

class ResponseParser:
    """Extracts technical terms and glossary from Gemini responses"""
    
    @staticmethod
    def parse_response(response_text: str) -> Dict:
        """
        Parse Gemini response to extract terms and glossary
        Returns: {
            'content': 'processed content with term IDs',
            'terms': ['list of term IDs found'],
            'glossary': {'term_id': 'definition'}
        }
        """
        # Decode HTML entities (handle double encoding)
        import html
        decoded_text = html.unescape(html.unescape(response_text))
        
        # Remove glossary section from content (both old and new formats)
        glossary_section_pattern = r'<div class="glossary-section">.*?</div>'
        cleaned_content = re.sub(glossary_section_pattern, '', decoded_text, flags=re.DOTALL)
        
        # Remove the new GLOSSARY_START/END section from content
        glossary_marker_pattern = r'GLOSSARY_START\s*\n\{[^}]+\}\s*\nGLOSSARY_END'
        cleaned_content = re.sub(glossary_marker_pattern, '', cleaned_content, flags=re.DOTALL)
        
        # Extract glossary JSON if present
        glossary = ResponseParser._extract_glossary(decoded_text)
        
        # Find all technical terms
        term_pattern = r'<term id="([^"]+)">([^<]+)</term>'
        terms_found = re.findall(term_pattern, decoded_text)
        
        # Build result
        result = {
            'content': cleaned_content.strip(),
            'terms': [term_id for term_id, _ in terms_found],
            'glossary': glossary
        }
        
        return result
    
    @staticmethod
    def _extract_glossary(text: str) -> Dict[str, str]:
        """Extract glossary from clean JSON format with markers"""
        glossary = {}
        
        # Look for the new clean format with markers
        marker_pattern = r'GLOSSARY_START\s*\n({[^}]+})\s*\nGLOSSARY_END'
        match = re.search(marker_pattern, text, re.DOTALL)
        
        if match:
            try:
                glossary_json = match.group(1)
                # Decode HTML entities in the JSON
                import html
                glossary_json = html.unescape(glossary_json)
                glossary = json.loads(glossary_json)
            except Exception as e:
                print(f"Error parsing clean glossary JSON: {e}")
        else:
            # Fallback: Look for the old HTML-encoded pattern
            json_pattern = r'```json\n\{\\&quot;glossary\\&quot;: \{([^}]+)\}\}\n```'
            match = re.search(json_pattern, text)
            
            if match:
                try:
                    import html
                    glossary_content = match.group(1)
                    
                    # Parse the key-value pairs - they are separated by commas
                    pairs = re.findall(r'\\&quot;([^\\]+)\\&quot;: \\&quot;([^\\"]+)\\&quot;', glossary_content)
                    for key, value in pairs:
                        glossary[key] = value
                        
                except Exception as e:
                    print(f"Error parsing legacy glossary: {e}")
        
        return glossary
    
    @staticmethod
    def get_term_definitions(term_ids: List[str], glossary: Dict[str, str]) -> Dict[str, str]:
        """Get definitions for specific term IDs"""
        return {term_id: glossary.get(term_id, f"Definition for {term_id}") 
                for term_id in term_ids}