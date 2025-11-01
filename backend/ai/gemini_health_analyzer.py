import google.generativeai as genai
import json
import os
import html
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiHealthAnalyzer:
    """Gemini AI integration for personalized health insights"""
    
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Try different model names in order of preference (using available models)
        model_names = ['models/gemini-2.5-flash', 'models/gemini-2.0-flash', 'models/gemini-flash-latest']
        self.model = None
        
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"Successfully loaded model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to load model {model_name}: {e}")
                continue
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    def generate_health_insights(self, health_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized health insights using Gemini AI"""
        
        # Prepare structured data for Gemini
        context = self._prepare_context(health_data, chart_data)
        
        # Generate insights
        prompt = self._create_health_prompt(context)
        
        response = self.model.generate_content(prompt)
        print(f"\n=== GEMINI RAW RESPONSE ===")
        print(response.text)
        print(f"=== END GEMINI RESPONSE ===\n")
        
        insights = self._parse_response(response.text)
        return {
            'success': True,
            'insights': insights,
            'raw_response': response.text
        }
    
    def _prepare_context(self, health_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured context for Gemini using actual data structure"""
        
        # Extract planetary analysis (actual structure)
        planetary_summary = {}
        if 'planet_analysis' in health_data:
            for planet, analysis in health_data['planet_analysis'].items():
                basic_analysis = analysis.get('basic_analysis', {})
                overall_assessment = basic_analysis.get('overall_assessment', {})
                health_impact = analysis.get('health_impact', {})
                
                planetary_summary[planet] = {
                    'grade': overall_assessment.get('classical_grade', 'Unknown'),
                    'score': overall_assessment.get('overall_strength_score', 0),
                    'strengths': overall_assessment.get('key_strengths', []),
                    'weaknesses': overall_assessment.get('key_weaknesses', []),
                    'health_impact': health_impact.get('reasoning', ''),
                    'impact_type': health_impact.get('impact_type', 'Unknown'),
                    'element': analysis.get('element', 'Unknown'),
                    'body_systems': analysis.get('body_systems', [])
                }
        
        # Extract house analysis (actual structure)
        house_summary = {}
        if 'house_analysis' in health_data:
            for house_num, analysis in health_data['house_analysis'].items():
                house_analysis = analysis.get('house_analysis', {})
                overall_assessment = house_analysis.get('overall_house_assessment', {})
                
                house_summary[house_num] = {
                    'grade': overall_assessment.get('classical_grade', 'Unknown'),
                    'score': overall_assessment.get('overall_strength_score', 0),
                    'health_significance': analysis.get('health_significance', ''),
                    'health_interpretation': analysis.get('health_interpretation', ''),
                    'residents': [p.get('planet') for p in house_analysis.get('resident_planets', [])]
                }
        
        # Extract constitution and yogas (actual structure)
        constitution = health_data.get('element_balance', {})
        yogas = health_data.get('yoga_analysis', {})
        
        # Extract chart data
        chart_summary = self._extract_chart_data(chart_data)
        
        # Extract special points from actual data
        special_points = self._extract_special_points(health_data, chart_data)
        
        return {
            'chart_data': chart_summary,
            'special_points': special_points,
            'planetary_summary': planetary_summary,
            'house_summary': house_summary,
            'constitution': constitution,
            'constitution_type': health_data.get('constitution_type', 'Unknown'),
            'beneficial_yogas': yogas.get('beneficial_yogas', []),
            'affliction_yogas': yogas.get('affliction_yogas', []),
            'total_beneficial': yogas.get('total_beneficial', 0),
            'total_afflictions': yogas.get('total_afflictions', 0)
        }
    
    def _create_health_prompt(self, context: Dict[str, Any]) -> str:
        """Create comprehensive health analysis prompt for Gemini"""
        
        return f"""
You are a master Vedic astrologer specializing in health analysis. Analyze this birth chart data and provide personalized health insights.

CHART DATA:
{json.dumps(context, indent=2)}

Generate a comprehensive health analysis with these sections:

1. **Health Overview** (2-3 sentences)
   - Overall health constitution and vitality
   - Primary strengths and vulnerabilities

2. **Constitutional Analysis** (2-3 sentences)
   - Ayurvedic dosha analysis based on elemental balance
   - Metabolic tendencies and digestive patterns

3. **Key Health Areas** (3-4 bullet points)
   - Specific body systems needing attention
   - Potential health challenges with astrological reasoning
   - Natural healing strengths

4. **Lifestyle Recommendations** (4-5 bullet points)
   - Dietary guidelines based on constitution
   - Exercise and daily routine suggestions
   - Stress management techniques
   - Optimal timing for health decisions

5. **Preventive Measures** (3-4 bullet points)
   - Specific health monitoring priorities
   - Seasonal health considerations
   - Remedial measures with astrological basis

6. **Positive Health Indicators** (2-3 sentences)
   - Natural resilience factors
   - Healing abilities and recovery potential

GUIDELINES:
- Use conversational, encouraging tone
- Avoid medical diagnosis or treatment advice
- Focus on prevention and lifestyle optimization
- ALWAYS explain astrological reasoning for predictions (e.g., "due to Mars in 6th house...")
- Provide classical references when possible (e.g., "As per Brihat Parashara Hora Shastra...")
- Include special points analysis (Yogi lords, Avayogi lords, Badhaka lords) in reasoning
- Reference planetary grades (Uttama/Madhyama/Adhama) and house assessments
- Provide actionable, practical guidance
- Be specific about timing when relevant

Format as JSON with sections as keys and content as values.
"""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured insights"""
        
        # Clean the response text
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Decode HTML entities comprehensively
        response_text = html.unescape(response_text)
        # Additional cleanup for any remaining entities
        response_text = response_text.replace('&quot;', '"').replace('&#39;', "'").replace('&amp;', '&')
        
        print(f"\n=== CLEANED RESPONSE ===\n{response_text[:500]}...\n=== END CLEANED ===\n")
        
        try:
            # Try to parse as JSON
            if response_text.startswith('{') and response_text.endswith('}'):
                raw_parsed = json.loads(response_text)
                print(f"\n=== PARSED JSON ===\n{raw_parsed}\n=== END PARSED ===\n")
                
                # Map Gemini response keys to expected frontend keys
                key_mapping = {
                    'Health Overview': 'health_overview',
                    'Constitutional Analysis': 'constitutional_analysis', 
                    'Key Health Areas': 'key_health_areas',
                    'Lifestyle Recommendations': 'lifestyle_recommendations',
                    'Preventive Measures': 'preventive_measures',
                    'Positive Health Indicators': 'positive_indicators'
                }
                
                parsed = {}
                for gemini_key, frontend_key in key_mapping.items():
                    if gemini_key in raw_parsed:
                        parsed[frontend_key] = raw_parsed[gemini_key]
                    else:
                        parsed[frontend_key] = '' if frontend_key in ['health_overview', 'constitutional_analysis', 'positive_indicators'] else []
                
                print(f"\n=== FINAL PARSED RESULT ===\n{parsed}\n=== END FINAL ===\n")
                return parsed
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Response text: {response_text[:500]}...")
        
        # Return error response if parsing fails
        return {
            'health_overview': 'AI response parsing failed',
            'constitutional_analysis': 'Unable to parse AI response. Please try again.',
            'key_health_areas': [],
            'lifestyle_recommendations': [],
            'preventive_measures': [],
            'positive_indicators': 'Please try generating insights again.'
        }
    
    def _extract_chart_data(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract essential chart data for Gemini"""
        
        # Extract planetary positions
        planets = {}
        if 'planets' in chart_data:
            for planet, data in chart_data['planets'].items():
                planets[planet] = {
                    'sign': data.get('sign', 0),
                    'sign_name': self._get_sign_name(data.get('sign', 0)),
                    'house': data.get('house', 1),
                    'degree': round(data.get('degree', 0), 1),
                    'retrograde': data.get('retrograde', False)
                }
        
        # Extract ascendant
        ascendant_degree = chart_data.get('ascendant', 0)
        ascendant_sign = int(ascendant_degree / 30)
        
        return {
            'ascendant': {
                'sign': ascendant_sign,
                'sign_name': self._get_sign_name(ascendant_sign),
                'degree': round(ascendant_degree % 30, 1)
            },
            'planets': planets,
            'ayanamsa': round(chart_data.get('ayanamsa', 0), 2)
        }
    
    def _get_sign_name(self, sign_number: int) -> str:
        """Get sign name from number"""
        signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        return signs[sign_number % 12]
    
    def _extract_special_points(self, health_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract special astrological points from actual data sources"""
        
        special_points = {
            'yogi_lords': [],
            'avayogi_lords': [],
            'dagdha_lords': [],
            'tithi_shunya_lords': [],
            'badhaka_lords': []
        }
        
        # Extract from planet analysis special lordships
        if 'planet_analysis' in health_data:
            for planet, analysis in health_data['planet_analysis'].items():
                basic_analysis = analysis.get('basic_analysis', {})
                special_lordships = basic_analysis.get('special_lordships', {})
                
                if special_lordships.get('is_yogi_lord'):
                    special_points['yogi_lords'].append(planet)
                if special_lordships.get('is_avayogi_lord'):
                    special_points['avayogi_lords'].append(planet)
                if special_lordships.get('is_dagdha_lord'):
                    special_points['dagdha_lords'].append(planet)
                if special_lordships.get('is_tithi_shunya_lord'):
                    special_points['tithi_shunya_lords'].append(planet)
                if special_lordships.get('is_badhaka_lord'):
                    special_points['badhaka_lords'].append(planet)
        
        return special_points