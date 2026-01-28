import google.generativeai as genai
import json
import os
import html
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
env_paths = [
    '.env',
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    '/home/tarun_yadav/AstrologyApp/backend/.env'
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path}")
        break
else:
    print("No .env file found in any expected location")

class GeminiWealthAnalyzer:
    """Gemini AI integration for personalized wealth insights"""
    
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"Current working directory: {os.getcwd()}")
        print(f"API key found: {bool(api_key)}")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Try different model names in order of preference
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
    
    def generate_wealth_insights(self, wealth_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized wealth insights using Gemini AI"""
        
        # Prepare structured data for Gemini
        context = self._prepare_context(wealth_data, chart_data)
        
        # Generate insights
        prompt = self._create_wealth_prompt(context)
        
        # Generate insights using Gemini AI
        response = self.model.generate_content(prompt)
        insights = self._parse_response(response.text)
        return {
            'success': True,
            'insights': insights,
            'raw_response': response.text
        }
    
    def _prepare_context(self, wealth_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare structured context for Gemini using actual data structure"""
        
        # Extract planetary analysis
        planetary_summary = {}
        if 'planet_analysis' in wealth_data:
            for planet, analysis in wealth_data['planet_analysis'].items():
                basic_analysis = analysis['basic_analysis']
                overall_assessment = basic_analysis['overall_assessment']
                wealth_impact = analysis['wealth_impact']
                
                planetary_summary[planet] = {
                    'grade': overall_assessment['classical_grade'],
                    'score': overall_assessment['overall_strength_score'],
                    'strengths': overall_assessment['key_strengths'],
                    'weaknesses': overall_assessment['key_weaknesses'],
                    'wealth_impact': wealth_impact['reasoning'],
                    'impact_type': wealth_impact['impact_type'],
                    'element': analysis['element'],
                    'wealth_systems': analysis['wealth_systems']
                }
        
        # Extract house analysis
        house_summary = {}
        if 'house_analysis' in wealth_data:
            for house_num, analysis in wealth_data['house_analysis'].items():
                house_analysis = analysis['house_analysis']
                overall_assessment = house_analysis['overall_house_assessment']
                
                house_summary[house_num] = {
                    'grade': overall_assessment['classical_grade'],
                    'score': overall_assessment['overall_strength_score'],
                    'wealth_significance': analysis['wealth_significance'],
                    'wealth_interpretation': analysis['wealth_interpretation'],
                    'residents': [p['planet'] for p in house_analysis['resident_planets']]
                }
        
        # Extract wealth constitution and yogas
        wealth_constitution = wealth_data['wealth_constitution']
        yogas = wealth_data['yoga_analysis']
        
        # Extract chart data
        chart_summary = self._extract_chart_data(chart_data)
        
        # Extract special points
        special_points = self._extract_special_points(wealth_data, chart_data)
        
        # Get wealth activations for 2 years (like health analysis)
        wealth_activations = self._get_wealth_activations(wealth_data, chart_data)
        
        return {
            'birth_details': {
                'name': wealth_data.get('name', ''),
                'date': wealth_data.get('date', ''),
                'time': wealth_data.get('time', ''),
                'place': wealth_data.get('place', ''),
                'latitude': wealth_data.get('latitude', 0.0),
                'longitude': wealth_data.get('longitude', 0.0),
                'timezone': wealth_data.get('timezone', 'UTC+0')
            },
            'chart_data': chart_summary,
            'special_points': special_points,
            'planetary_summary': planetary_summary,
            'house_summary': house_summary,
            'wealth_constitution': wealth_constitution,
            'income_sources': wealth_data['income_sources'],
            'dhana_yogas': yogas['dhana_yogas'],
            'lakshmi_yogas': yogas['lakshmi_yogas'],
            'raja_yogas': yogas['raja_yogas'],
            'viparita_yogas': yogas['viparita_yogas'],
            'total_beneficial': yogas['total_beneficial'],
            'total_afflictions': yogas['total_afflictions'],
            'wealth_score': wealth_data['wealth_score'],
            'wealth_activations_2_years': wealth_activations
        }
    
    def _create_wealth_prompt(self, context: Dict[str, Any]) -> str:
        """Create comprehensive wealth analysis prompt for Gemini"""
        
        return f"""
You are a master Vedic astrologer specializing in wealth and prosperity analysis. Analyze this birth chart data and provide personalized wealth insights.

CHART DATA:
{json.dumps(context, indent=2)}

Generate a comprehensive wealth analysis with these sections:

1. **Wealth Overview** (2-3 sentences)
   - Overall financial constitution and potential
   - Primary wealth-building strengths and challenges

2. **Income Analysis** (2-3 sentences)
   - Primary income sources and patterns
   - Career-based vs business-based earning potential

3. **Investment Guidance** (4-5 bullet points)
   - Best investment types based on planetary strengths
   - Timing for major financial decisions
   - Risk tolerance and investment style
   - Sectors and asset classes to focus on

4. **Business Prospects** (4-5 bullet points)
   - Entrepreneurial potential and business aptitude
   - Best business sectors based on planetary combinations
   - Partnership vs solo business recommendations
   - Timing for business ventures

5. **Financial Challenges** (3-4 bullet points)
   - Potential obstacles to wealth accumulation
   - Periods of financial stress or loss
   - Areas requiring careful financial planning

6. **Prosperity Indicators** (2-3 sentences)
   - Natural wealth-building abilities
   - Long-term financial growth potential

7. **Wealth Timeline (Next 6 Months)** (Show ALL activations)
   - Process ALL entries in wealth_activations_2_years.wealth_activations array chronologically
   - Filter to show only activations within next 6 months from current date
   - For each activation entry, create one bullet point with format:
     "[activation_date] to [end_date]: Transit [transit_planet] [aspect_type] natal [natal_planet] in [natal_house] house (Strength [activation_strength]) - [wealth interpretation]"
   - Do NOT group multiple activations together
   - Mention each planet combination individually with its specific date range
   - Include ALL activations regardless of strength

8. **Career & Money** (4-5 bullet points)
   - Professional paths for maximum financial success
   - Skills and talents that can be monetized
   - Authority vs service-based career recommendations
   - Government vs private sector suitability

WEALTH ANALYSIS GUIDELINES:
- Use planetary grades and house assessments from context
- Reference specific yogas (Dhana, Lakshmi, Raja, Viparita)
- Explain astrological reasoning for recommendations
- Focus on practical, actionable financial guidance
- Consider 2nd house (accumulation), 5th house (speculation), 9th house (fortune), 11th house (gains)
- Analyze Jupiter (wisdom wealth), Venus (luxury wealth), Mercury (business wealth)
- Reference wealth constitution type from context

HOUSE-SPECIFIC WEALTH INTERPRETATIONS:
- 2nd House: Accumulated wealth, family assets, speech value, food business
- 5th House: Speculation, investments, stock market, entertainment business
- 9th House: Fortune, luck, dharmic wealth, publishing, higher education
- 11th House: Income, gains, network wealth, large organizations
- 10th House: Career income, authority-based wealth, reputation value
- 4th House: Real estate, property, land, vehicles, mother's wealth
- 7th House: Partnership wealth, spouse's income, business collaborations

PLANETARY WEALTH SIGNIFICANCES:
- Jupiter: Teaching, consulting, dharmic business, wisdom-based income
- Venus: Arts, beauty, luxury goods, entertainment, hospitality
- Mercury: Business, trade, communication, technology, writing
- Sun: Authority positions, government jobs, leadership roles
- Moon: Public dealings, real estate, food business, emotional intelligence
- Mars: Property, sports, engineering, military, police, surgery
- Saturn: Hard work income, mining, labor, slow but steady wealth
- Rahu: Foreign connections, technology, sudden gains, unconventional
- Ketu: Spiritual wealth, detachment from materialism, hidden assets

WEALTH ACTIVATIONS DATA USAGE:
The wealth_activations_2_years contains an array of planetary activations where each activation has:
- activation_date: Start date of activation (YYYY-MM-DD format)
- end_date: End date of activation (YYYY-MM-DD format)
- transit_planet: Transit planet (the planet that is moving and creating the aspect)
- natal_planet: Natal planet (the birth chart planet being aspected)
- aspect_type: The aspect relationship (e.g., "7th_house" means transit_planet casts 7th aspect on natal_planet)
- natal_house: House number where natal_planet is located
- activation_strength: Numerical strength (0-100)
- description: Text description of the activation

WEALTH-SPECIFIC ACTIVATION INTERPRETATIONS:
- When natal_house is 2: Wealth accumulation, family assets, speech value, food business
- When natal_house is 5: Speculation, investments, stock market, entertainment business
- When natal_house is 9: Fortune, luck, dharmic wealth, publishing, higher education
- When natal_house is 11: Income, gains, network wealth, large organizations
- When natal_house is 10: Career income, authority-based wealth, reputation value
- When natal_house is 4: Real estate, property, land, vehicles, mother's wealth
- When natal_house is 7: Partnership wealth, spouse's income, business collaborations

PLANETARY WEALTH ACTIVATION EFFECTS:
- Jupiter activations: Teaching income, consulting, dharmic business, wisdom-based wealth
- Venus activations: Arts income, beauty business, luxury goods, entertainment wealth
- Mercury activations: Business income, trade, communication, technology wealth
- Sun activations: Authority income, government jobs, leadership positions
- Moon activations: Public wealth, real estate, food business, emotional intelligence
- Mars activations: Property wealth, sports income, engineering business
- Saturn activations: Hard work income, mining, labor, slow but steady wealth
- Rahu activations: Foreign wealth, technology income, sudden gains
- Ketu activations: Spiritual wealth, detachment from materialism, hidden assets

GUIDELINES:
- Use conversational, encouraging tone
- Avoid financial advice or investment recommendations
- Focus on astrological patterns and timing
- ALWAYS explain astrological reasoning using activation data
- MUST use wealth_activations_2_years data for section 7
- Provide exact dates from activation.activation_date field
- Reference planetary grades and house assessments
- Be specific about timing and actionable guidance

CRITICAL: You MUST respond ONLY with valid JSON format. Do not include any text before or after the JSON. Start your response with {{ and end with }}. Return ONLY the JSON object with the 8 sections as keys. Do NOT add any explanatory text, greetings, or markdown formatting.
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
        
        # Decode HTML entities
        for _ in range(3):
            response_text = html.unescape(response_text)
        
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
            
            # Map Gemini response keys to expected frontend keys
            key_mapping = {
                'Wealth Overview': 'wealth_overview',
                'wealth_overview': 'wealth_overview',
                'Income Analysis': 'income_analysis',
                'income_analysis': 'income_analysis',
                'Investment Guidance': 'investment_guidance',
                'investment_guidance': 'investment_guidance',
                'Business Prospects': 'business_prospects',
                'business_prospects': 'business_prospects',
                'Financial Challenges': 'financial_challenges',
                'financial_challenges': 'financial_challenges',
                'Prosperity Indicators': 'prosperity_indicators',
                'prosperity_indicators': 'prosperity_indicators',
                'Wealth Timeline (Next 6 Months)': 'wealth_timeline_6_months',
                'wealth_timeline_6_months': 'wealth_timeline_6_months',
                'Career & Money': 'career_money',
                'career_money': 'career_money'
            }
            
            parsed = {}
            # Set defaults
            for frontend_key in ['wealth_overview', 'income_analysis', 'investment_guidance', 'business_prospects', 'financial_challenges', 'prosperity_indicators', 'wealth_timeline_6_months', 'career_money']:
                parsed[frontend_key] = '' if frontend_key in ['wealth_overview', 'income_analysis', 'prosperity_indicators'] else []
            
            # Map actual content
            for gemini_key, frontend_key in key_mapping.items():
                if gemini_key in raw_parsed and raw_parsed[gemini_key]:
                    parsed[frontend_key] = raw_parsed[gemini_key]
            
            return parsed
        except (ValueError, json.JSONDecodeError) as e:
            print(f"JSON parsing failed: {e}")
        
        # Return error response if parsing fails
        return {
            'wealth_overview': 'AI response parsing failed. Please try again.',
            'income_analysis': 'Unable to parse AI response. Please try again.',
            'investment_guidance': [],
            'business_prospects': [],
            'financial_challenges': [],
            'prosperity_indicators': 'Please try generating insights again.',
            'wealth_timeline_6_months': [],
            'career_money': []
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
    
    def _extract_special_points(self, wealth_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract special astrological points from actual data sources"""
        
        special_points = {
            'yogi_lords': [],
            'avayogi_lords': [],
            'dagdha_lords': [],
            'tithi_shunya_lords': [],
            'badhaka_lords': []
        }
        
        # Extract from planet analysis special lordships
        if 'planet_analysis' in wealth_data:
            for planet, analysis in wealth_data['planet_analysis'].items():
                basic_analysis = analysis['basic_analysis']
                special_lordships = basic_analysis['special_lordships']
                
                if special_lordships['is_yogi_lord']:
                    special_points['yogi_lords'].append(planet)
                if special_lordships['is_avayogi_lord']:
                    special_points['avayogi_lords'].append(planet)
                if special_lordships['is_dagdha_lord']:
                    special_points['dagdha_lords'].append(planet)
                if special_lordships['is_tithi_shunya_lord']:
                    special_points['tithi_shunya_lords'].append(planet)
                if special_lordships['is_badhaka_lord']:
                    special_points['badhaka_lords'].append(planet)
        
        return special_points
    
    def _get_wealth_activations(self, wealth_data: Dict[str, Any], chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get wealth activations for next 2 years using wealth-focused activation system"""
        try:
            from wealth.wealth_activation_calculator import WealthActivationCalculator
            
            # Extract birth data from wealth_data
            birth_data = {
                'name': wealth_data.get('name', ''),
                'date': wealth_data.get('date', ''),
                'time': wealth_data.get('time', ''),
                'latitude': wealth_data.get('latitude', 0.0),
                'longitude': wealth_data.get('longitude', 0.0),
                'timezone': wealth_data.get('timezone', 'UTC+0')
            }
            
            print(f"Debug - Birth data for wealth activations: {birth_data}")
            
            if not birth_data['date']:
                print("Debug - No birth date found, returning empty activations")
                return {'wealth_activations': [], 'error': 'Birth data not available'}
            
            calculator = WealthActivationCalculator()
            activations_list = calculator.calculate_wealth_activations(birth_data)
            
            activations_result = {
                'wealth_activations': activations_list,
                'total_activations': len(activations_list)
            }
            
            print(f"Debug - Wealth activations count: {activations_result.get('total_activations', 0)}")
            return activations_result
            
        except ImportError as e:
            print(f"WealthActivationCalculator not found: {e}")
            return {'wealth_activations': [], 'error': 'WealthActivationCalculator not available'}
        except Exception as e:
            print(f"Error getting wealth activations: {e}")
            return {'wealth_activations': [], 'error': str(e)}