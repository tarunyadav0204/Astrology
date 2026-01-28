import google.generativeai as genai
import json
import os
import html
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
# Try multiple paths to find .env file
env_paths = [
    '.env',  # Current directory
    os.path.join(os.path.dirname(__file__), '..', '.env'),  # Parent directory
    '/home/tarun_yadav/AstrologyApp/backend/.env'  # Absolute path
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
        break
else:
    print("No .env file found in any expected location")

class GeminiHealthAnalyzer:
    """Gemini AI integration for personalized health insights"""
    
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"Current working directory: {os.getcwd()}")
        print(f"API key found: {bool(api_key)}")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Try different model names in order of preference (using available models)
        model_names = ['models/gemini-2.5-flash', 'models/gemini-flash-latest']
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
        
        # Generate insights using Gemini AI
        response = self.model.generate_content(prompt)
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
        
        # Get health activations for 3 years (past + future)
        health_activations = self._get_health_activations(health_data, chart_data)
        print(f"Debug - Final health_activations in context: {health_activations}")
        
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
            'total_afflictions': yogas.get('total_afflictions', 0),
            'health_activations_3_years': health_activations
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

7. **Accident & Surgery Possibilities** (3-4 bullet points)
   - Process each individual activation in health_activations_3_years.health_activations array
   - Focus on Mars activations
   - For each high-risk activation, state: "[exact date]: Transit [transit_planet] [aspect_type] natal [natal_planet] in [natal_house] house (Strength [activation_strength])"
   - Explain specific health risks for each planet combination

8. **Health Timeline (Next 6 Months)** (Show ALL activations)
   - Process ALL entries in health_activations_3_years.health_activations array chronologically
   - Filter to show only activations within next 6 months from current date
   - For each activation entry, create one bullet point with format:
     "[activation_date] to [end_date]: Transit [transit_planet] [aspect_type] natal [natal_planet] in [natal_house] house (Strength [activation_strength]) - [health interpretation]"
   - Do NOT group multiple activations together
   - Mention each planet combination individually with its specific date range
   - Include ALL activations regardless of strength

HEALTH ACTIVATIONS DATA USAGE:
The health_activations_3_years contains an array of planetary activations where each activation has:
- activation_date: Start date of activation (YYYY-MM-DD format)
- end_date: End date of activation (YYYY-MM-DD format)
- transit_planet: Transit planet (the planet that is moving and creating the aspect)
- natal_planet: Natal planet (the birth chart planet being aspected)
- aspect_type: The aspect relationship (e.g., "7th_house" means transit_planet casts 7th aspect on natal_planet)
- natal_house: House number where natal_planet is located
- activation_strength: Numerical strength (0-100)
- health_systems: Array of affected body systems
- description: Text description of the activation

ASPECT INTERPRETATION:
- When aspect_type is "7th_house": Transit planet casts 7th aspect on natal planet
- When aspect_type is "1st_house": Transit planet is conjunct with natal planet  
- When aspect_type is "4th_house": Transit planet casts 4th aspect on natal planet
- When aspect_type is "8th_house": Transit planet casts 8th aspect on natal planet

HOUSE-SPECIFIC ACTIVATION INTERPRETATIONS:
- When natal_house is 1: Head injuries, brain issues, overall vitality problems
- When natal_house is 2: Teeth, eyes, face, speech, throat, neck issues
- When natal_house is 6: Digestive problems, diseases, immune system issues
- When natal_house is 8: Surgeries, accidents, chronic diseases, reproductive issues
- When natal_house is 12: Hospitalization, sleep disorders, feet problems, foreign treatment

CLASSICAL INTERPRETATION GUIDELINES:
- Mars activations: Accidents, surgeries, blood disorders, inflammation
- Saturn activations: Chronic conditions, bone/joint issues, delays in healing, teeth problems, dental issues
- Rahu activations: Sudden illness, mysterious conditions, addictions
- Ketu activations: Spiritual healing, mysterious illness, detoxification
- Sun activations: Heart, vitality, bone issues, authority-related stress
- Moon activations: Mental health, fluid disorders, digestive issues
- Mercury activations: Nervous system, skin issues, communication stress
- Jupiter activations: Liver, diabetes, weight issues, optimism vs excess
- Venus activations: Reproductive health, kidney issues, beauty concerns

HOUSE-SPECIFIC HEALTH AREAS:
- 1st House: Overall vitality, head, face, brain, general health
- 2nd House: Face, eyes, teeth, mouth, throat, speech, neck, right eye
- 3rd House: Arms, shoulders, hands, lungs, nervous system
- 4th House: Chest, heart, lungs, breasts, stomach
- 5th House: Heart, stomach, liver, pregnancy, children's health
- 6th House: Digestive system, intestines, kidney, diseases, enemies
- 7th House: Lower back, kidneys, reproductive organs, partnerships
- 8th House: Reproductive organs, chronic diseases, surgeries, accidents
- 9th House: Hips, thighs, liver, higher mind, fortune
- 10th House: Knees, bones, joints, career stress, reputation
- 11th House: Legs, ankles, circulation, gains, friendships
- 12th House: Feet, left eye, sleep, hospitalization, foreign places

FOR TIMING PREDICTIONS:
- Use activation_date and end_date for exact timing
- Interpret as: "Transit [transit_planet] [aspect_type] natal [natal_planet] in [natal_house] house"
- Use activation_strength (numerical 0-100) for severity assessment
- Reference health_systems array for affected body parts
- Create individual entries for each activation - do NOT group them together

GUIDELINES:
- Use conversational, encouraging tone
- Avoid medical diagnosis or treatment advice
- Focus on prevention and lifestyle optimization
- ALWAYS explain astrological reasoning using activation data
- Provide classical references when possible
- Include special points analysis in reasoning
- Reference planetary grades and house assessments
- MUST use health_activations_3_years data for sections 7 and 8
- Provide exact dates from activation.date field
- Be specific about timing and actionable guidance

CRITICAL: You MUST respond ONLY with valid JSON format. Do not include any text before or after the JSON. Start your response with {{ and end with }}. Return ONLY the JSON object with the 8 sections as keys. Do NOT add any explanatory text, greetings, or markdown formatting.
"""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured insights"""
        
        print(f"Raw response length: {len(response_text)}")
        print(f"Raw response preview: {response_text[:200]}...")
        
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
        
        # Decode HTML entities comprehensively - multiple passes
        for _ in range(3):  # Multiple passes to handle nested encoding
            response_text = html.unescape(response_text)
        
        # Additional cleanup for any remaining entities
        response_text = response_text.replace('&quot;', '"').replace('&#39;', "'").replace('&amp;', '&')
        response_text = response_text.replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')
        
        print(f"Cleaned response preview: {response_text[:200]}...")
        
        try:
            # Find the JSON object boundaries
            start_idx = response_text.find('{')
            if start_idx == -1:
                raise ValueError("No JSON object found")
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = -1
            for i in range(start_idx, len(response_text)):
                if response_text[i] == '{':
                    brace_count += 1
                elif response_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx == -1:
                raise ValueError("No matching closing brace found")
            
            # Extract just the JSON part
            json_text = response_text[start_idx:end_idx]
            
            # Try to parse as JSON
            raw_parsed = json.loads(json_text)
            print(f"Successfully parsed JSON with keys: {list(raw_parsed.keys())}")
            print(f"Debug - Raw JSON sample: {str(raw_parsed)[:300]}...")
            
            # Map Gemini response keys to expected frontend keys
            key_mapping = {
                    'Health Overview': 'health_overview',
                    'health_overview': 'health_overview',
                    'Constitutional Analysis': 'constitutional_analysis',
                    'constitutional_analysis': 'constitutional_analysis',
                    'Key Health Areas': 'key_health_areas',
                    'key_health_areas': 'key_health_areas',
                    'Lifestyle Recommendations': 'lifestyle_recommendations',
                    'lifestyle_recommendations': 'lifestyle_recommendations',
                    'Preventive Measures': 'preventive_measures',
                    'preventive_measures': 'preventive_measures',
                    'Positive Health Indicators': 'positive_indicators',
                    'positive_health_indicators': 'positive_indicators',
                    'Accident & Surgery Possibilities': 'accident_surgery_possibilities',
                    'accident_surgery_possibilities': 'accident_surgery_possibilities',
                    'Health Timeline (Next 2 Years)': 'health_timeline_2_years',
                    'Health Timeline (Next 6 Months)': 'health_timeline_2_years',
                    'health_timeline_next_2_years': 'health_timeline_2_years'
            }
            
            parsed = {}
            # First, set defaults
            for frontend_key in ['health_overview', 'constitutional_analysis', 'key_health_areas', 'lifestyle_recommendations', 'preventive_measures', 'positive_indicators', 'accident_surgery_possibilities', 'health_timeline_2_years']:
                parsed[frontend_key] = '' if frontend_key in ['health_overview', 'constitutional_analysis', 'positive_indicators'] else []
            
            # Then, map actual content from Gemini response
            for gemini_key, frontend_key in key_mapping.items():
                if gemini_key in raw_parsed and raw_parsed[gemini_key]:
                    parsed[frontend_key] = raw_parsed[gemini_key]
            
            print(f"Final parsed keys: {list(parsed.keys())}")
            print(f"Debug - Parsed content sample:")
            for key, value in parsed.items():
                if isinstance(value, str):
                    print(f"  {key}: '{value[:100]}...'" if len(value) > 100 else f"  {key}: '{value}'")
                elif isinstance(value, list):
                    print(f"  {key}: {len(value)} items - {value[:2] if len(value) > 0 else 'empty'}")
                else:
                    print(f"  {key}: {type(value)} - {value}")
            return parsed
        except ValueError as ve:
            print(f"JSON extraction failed: {ve}")
            print(f"Response preview: {response_text[:500]}...")
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            print(f"Failed text: {json_text[:500] if 'json_text' in locals() else response_text[:500]}...")
        
        # Return error response if parsing fails
        return {
            'health_overview': f'AI response parsing failed. Response preview: {response_text[:100]}...',
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
    
    def _get_health_activations(self, health_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get health activations for next 2 years using existing activation system"""
        try:
            from health.health_activation_calculator import HealthActivationCalculator
            
            # Extract birth data from health_data or chart_data
            birth_data = {
                'name': health_data.get('name', ''),
                'date': health_data.get('date', ''),
                'time': health_data.get('time', ''),
                'latitude': health_data.get('latitude', 0.0),
                'longitude': health_data.get('longitude', 0.0),
                'timezone': health_data.get('timezone', 'UTC+0')
            }
            
            print(f"Debug - Birth data for activations: {birth_data}")
            print(f"Debug - Health data keys: {list(health_data.keys())}")
            print(f"Debug - Chart data keys: {list(chart_data.keys())}")
            
            # If birth data not in health_data, try to extract from chart_data or other sources
            if not birth_data['date']:
                # Try to get from chart_data or other sources
                if 'birth_details' in chart_data:
                    bd = chart_data['birth_details']
                    birth_data.update({
                        'date': bd.get('date', ''),
                        'time': bd.get('time', ''),
                        'latitude': bd.get('latitude', 0.0),
                        'longitude': bd.get('longitude', 0.0),
                        'timezone': bd.get('timezone', 'UTC+0')
                    })
                    print(f"Debug - Updated birth data from chart_data: {birth_data}")
                
                if not birth_data['date']:
                    print("Debug - No birth date found anywhere, returning empty activations")
                    return {'health_activations': [], 'error': 'Birth data not available'}
            
            calculator = HealthActivationCalculator()
            activations_list = calculator.calculate_health_activations(birth_data)
            
            activations_result = {
                'health_activations': activations_list,
                'total_activations': len(activations_list)
            }
            
            print(f"Debug - Activations result keys: {list(activations_result.keys())}")
            print(f"Debug - Activations count: {activations_result.get('total_activations', 0)}")
            return activations_result
            
        except Exception as e:
            print(f"Error getting health activations: {e}")
            return {'health_activations': [], 'error': str(e)}