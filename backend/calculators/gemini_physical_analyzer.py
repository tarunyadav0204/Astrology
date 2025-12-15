import google.generativeai as genai
import os
import logging
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
from physical_traits_cache import PhysicalTraitsCache

# Load environment variables
env_paths = [
    '.env',
    os.path.join(os.path.dirname(__file__), '..', '.env'),
    '/home/tarun_yadav/AstrologyApp/backend/.env'
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break

class GeminiPhysicalAnalyzer:
    """
    Uses Gemini AI to analyze astrological data and generate accurate physical trait descriptions.
    """
    
    def __init__(self):
        self.cache = PhysicalTraitsCache()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Use the same model selection logic as chat analyzer
        model_names = [
            'models/gemini-2.5-flash',
            'models/gemini-2.0-flash-exp', 
            'models/gemini-2.0-flash',
            'models/gemini-1.5-flash',
            'models/gemini-flash-latest'
        ]
        
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                logging.info(f"✅ Initialized Gemini model: {model_name}")
                break
            except Exception as e:
                logging.warning(f"⚠️ Model {model_name} not available: {e}")
                continue
        
        if not self.model:
            raise ValueError("No available Gemini model found")
    
    def analyze_physical_traits(self, chart_data: Dict, birth_data: Dict, birth_chart_id: int = None) -> List[Dict]:
        """
        Analyze chart data using Gemini AI to generate physical trait descriptions.
        """
        try:
            # Check cache first if we have birth_chart_id
            if birth_chart_id:
                cached_traits = self.cache.get_cached_traits(birth_chart_id)
                if cached_traits:
                    logging.info(f"Retrieved {len(cached_traits)} traits from cache")
                    return cached_traits
            
            # Prepare astrological context
            astrological_context = self._prepare_astrological_context(chart_data, birth_data)
            
            # Create prompt for Gemini
            prompt = self._create_analysis_prompt(astrological_context)
            prompt_chars = len(prompt)
            logging.info(f"📤 Sending {prompt_chars} characters to Gemini")
            
            # Get Gemini analysis
            response = self.model.generate_content(prompt)
            response_chars = len(response.text)
            logging.info(f"📥 Received {response_chars} characters from Gemini")
            
            # Parse and format response
            traits = self._parse_gemini_response(response.text, astrological_context)
            
            # Cache the results if we have birth_chart_id
            if birth_chart_id:
                self.cache.cache_traits(birth_chart_id, traits)
            
            logging.info(f"Gemini generated {len(traits)} physical traits")
            return traits
            
        except Exception as e:
            logging.error(f"Gemini analysis error: {e}")
            astrological_context = self._prepare_astrological_context(chart_data, birth_data)
            return self._fallback_traits(astrological_context.get('ascendant_sign', 'Aries'))
    
    def _prepare_astrological_context(self, chart_data: Dict, birth_data: Dict) -> Dict:
        """Prepare structured astrological data for Gemini analysis."""
        
        asc_degree = chart_data.get('ascendant', 0)
        asc_sign = int(asc_degree / 30)
        
        # 1. Get planets in 1st house
        first_house_planets = []
        for planet, data in chart_data.get('planets', {}).items():
            if planet in ['Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi', 'InduLagna']:
                continue
            planet_sign = int(data['longitude'] / 30)
            if planet_sign == asc_sign:
                first_house_planets.append({
                    'name': planet,
                    'degree': data['longitude'] % 30,
                    'distance_from_asc': abs((data['longitude'] % 30) - (asc_degree % 30))
                })
        
        # 2. Get planets aspecting 1st house
        aspecting_planets = []
        for planet, data in chart_data.get('planets', {}).items():
            if planet in ['Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi', 'InduLagna']:
                continue
            
            p_sign = int(data['longitude'] / 30)
            
            # Vedic aspects: All planets aspect 7th from themselves
            aspects = [7]  # Default aspect
            if planet == 'Mars':
                aspects = [4, 7, 8]
            elif planet == 'Jupiter':
                aspects = [5, 7, 9]
            elif planet == 'Saturn':
                aspects = [3, 7, 10]
            
            for asp in aspects:
                target_sign = (p_sign + asp - 1) % 12
                if target_sign == asc_sign:
                    aspecting_planets.append({
                        'name': planet,
                        'type': 'Aspect',
                        'aspect_number': asp
                    })
        
        # Get nakshatra
        nakshatra_index = int(asc_degree / 13.333333)
        nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
            "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
            "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
            "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
            "Uttara Bhadrapada", "Revati"
        ]
        
        sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        return {
            'ascendant_sign': sign_names[asc_sign],
            'ascendant_degree': asc_degree % 30,
            'nakshatra': nakshatra_names[nakshatra_index] if nakshatra_index < len(nakshatra_names) else "Unknown",
            'first_house_planets': first_house_planets,
            'aspecting_planets': aspecting_planets,
            'birth_info': {
                'name': birth_data.get('name', 'Native'),
                'gender': birth_data.get('gender', 'Unknown')
            }
        }
    
    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create a detailed prompt for Gemini to analyze physical traits."""
        
        planets_text = ""
        if context['first_house_planets']:
            planets_list = []
            for p in context['first_house_planets']:
                if p['distance_from_asc'] < 5:
                    planets_list.append(f"{p['name']} (DOMINANT - Within 5° of Ascendant)")
                else:
                    planets_list.append(f"{p['name']} at {p['degree']:.1f}°")
            planets_text = f"Planets in 1st house: {', '.join(planets_list)}"
        else:
            planets_text = "No planets in 1st house"
        
        aspects_text = ""
        if context.get('aspecting_planets'):
            aspect_list = [f"{p['name']} ({p['aspect_number']}th aspect)" for p in context['aspecting_planets']]
            aspects_text = f"Planets aspecting 1st house: {', '.join(aspect_list)}"
        else:
            aspects_text = "No major aspects to 1st house"
        
        prompt = f"""
You are a master Vedic astrologer. For this physical analysis, you must STRICTLY refer to **Kalyana Varma's 'Saravali'** and **Mantreswara's 'Phaladeepika'**.

**CRITICAL INSTRUCTION:**
- Do not use generic horoscope language.
- Look for specific "Distinguishing Marks" (moles, scars, dental features, hair texture) mentioned in 'Saravali' for this specific Ascendant and Planet combination.
- If the text mentions a specific trait (e.g., "frog-like eyes" for Cancer or "prominent veins" for Saturn), use that specific descriptor.

CHART DATA:
- Ascendant: {context['ascendant_sign']} at {context['ascendant_degree']:.1f}°
- Nakshatra: {context['nakshatra']}
- {planets_text}
- {aspects_text}
- Gender: {context['birth_info']['gender']}

CLASSICAL PLANETARY INDICATORS IN 1ST HOUSE (Use these specific traits when planets are present):

**SUN in 1st House:**
- Prominent forehead or high hairline
- Sparse hair or early balding tendency
- Strong bone structure
- Commanding presence and upright posture
- Golden or copper-toned complexion
- Medium to tall height

**MOON in 1st House:**
- Round or full face
- Soft, fleshy body with tendency to fluctuate in weight
- Pale or luminous complexion
- Large, expressive eyes
- Generally attractive features
- Medium height

**MARS in 1st House:**
- Reddish complexion or warm undertones
- Athletic or muscular build
- Prominent nose or sharp features
- Scars or marks on face/head (especially if afflicted)
- Medium to tall height
- Strong, robust constitution

**MERCURY in 1st House:**
- Youthful appearance regardless of age
- Quick, animated gestures
- Articulate speech and expressive face
- Wheatish or olive complexion
- Medium height with proportionate build
- Bright, intelligent eyes

**JUPITER in 1st House:**
- Tendency to be overweight or stout build
- Large forehead or prominent features
- Golden or bright complexion
- Tall stature (if well-placed)
- Dignified bearing and presence
- Full, round face

**VENUS in 1st House:**
- Attractive, charming features
- Curly or wavy hair
- Clear, glowing complexion
- Dimples or pleasant smile
- Well-proportioned body
- Graceful movements

**SATURN in 1st House:**
- Excess body hair (especially on arms, legs)
- Prominent teeth or dental issues
- Darker or tanned complexion
- Tall, lean frame or bony structure
- Serious expression
- Prominent veins (if afflicted)

**RAHU in 1st House:**
- Distinctive or unusual appearance
- Glasses or weak eyesight
- Unconventional features
- Smoky or shadowed complexion
- Tall height
- Magnetic but mysterious presence

**KETU in 1st House:**
- Slight hump or curvature of upper back/shoulders
- Mysterious or detached expression
- Scar near eye or on face
- Pallid or matte complexion
- Lean build
- Spiritual or otherworldly aura

COMPLEXION ANALYSIS:
- Fire signs: Warm-toned, reddish, golden
- Earth signs: Medium, wheatish, stable
- Air signs: Variable, clear, balanced
- Water signs: Pale to medium, natural glow

INSTRUCTIONS:
1. If planets are in 1st house, PRIORITIZE their specific classical indicators
2. If 1st house is empty, analyze planets ASPECTING the 1st house as strong modifiers
3. Aspects have 75% strength of direct placement - still very significant
4. Combine planetary influences with ascendant sign characteristics
5. Be specific about observable features
6. Use realistic, moderate language
7. Focus on 3-4 most prominent traits

FORMAT: Return ONLY a valid JSON array:
[
  {{"trait": "Specific observable trait", "confidence": "High/Medium/Low", "source": "Planet/Sign/Nakshatra name"}}
]

Generate the JSON array now:
"""
        return prompt
    
    def _get_icon_for_trait(self, label: str) -> str:
        """Map trait description to appropriate icon type."""
        label = label.lower()
        if any(x in label for x in ['eye', 'gaze', 'glasses', 'vision']):
            return 'eyes'
        if any(x in label for x in ['hair', 'bald', 'curl', 'beard']):
            return 'hair'
        if any(x in label for x in ['scar', 'mark', 'mole', 'spot', 'birthmark']):
            return 'mark'
        if any(x in label for x in ['tall', 'short', 'height', 'stature']):
            return 'height'
        if any(x in label for x in ['build', 'muscular', 'athletic', 'stout', 'lean', 'robust']):
            return 'build'
        if any(x in label for x in ['complexion', 'skin', 'tone', 'color']):
            return 'skin'
        if any(x in label for x in ['nose', 'nostril']):
            return 'nose'
        if any(x in label for x in ['teeth', 'dental', 'smile']):
            return 'teeth'
        if any(x in label for x in ['hand', 'finger', 'palm']):
            return 'hands'
        if any(x in label for x in ['face', 'facial', 'cheek', 'chin', 'forehead']):
            return 'face'
        return 'body'
    
    def _parse_gemini_response(self, response_text: str, context: Dict = None) -> List[Dict]:
        """Parse Gemini's JSON response into trait objects."""
        try:
            import re
            
            logging.info(f"Raw Gemini response: {response_text[:500]}...")
            
            # Clean the response text
            cleaned_text = response_text.strip()
            
            # Extract JSON from response - try multiple patterns
            json_patterns = [
                r'\[\s*\{.*?\}\s*\]',  # Standard array
                r'```json\s*(\[.*?\])\s*```',  # Code block
                r'```\s*(\[.*?\])\s*```',  # Generic code block
            ]
            
            json_str = None
            for pattern in json_patterns:
                match = re.search(pattern, cleaned_text, re.DOTALL)
                if match:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    break
            
            if not json_str:
                # Try to find just the array part
                start = cleaned_text.find('[')
                end = cleaned_text.rfind(']')
                if start != -1 and end != -1 and end > start:
                    json_str = cleaned_text[start:end+1]
            
            if json_str:
                traits_data = json.loads(json_str)
                
                # Convert to our format
                formatted_traits = []
                for i, trait in enumerate(traits_data[:4]):  # Limit to 4 traits
                    trait_label = trait.get('trait', 'Distinctive appearance')
                    formatted_traits.append({
                        'feature': f'physical_trait_{i+1}',
                        'label': trait_label,
                        'confidence': trait.get('confidence', 'Medium'),
                        'source': trait.get('source', 'Astrological Analysis'),
                        'icon': self._get_icon_for_trait(trait_label)
                    })
                
                logging.info(f"Successfully parsed {len(formatted_traits)} traits from Gemini")
                return formatted_traits
            else:
                logging.warning("No JSON array found in Gemini response")
                return self._fallback_traits(context.get('ascendant_sign', 'Aries') if context else 'Aries')
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            logging.error(f"Attempted to parse: {json_str[:200] if 'json_str' in locals() else 'No JSON found'}")
            return self._fallback_traits(context.get('ascendant_sign', 'Aries') if context else 'Aries')
        except Exception as e:
            logging.error(f"Error parsing Gemini response: {e}")
            return self._fallback_traits(context.get('ascendant_sign', 'Aries') if context else 'Aries')
    
    def _fallback_traits(self, asc_sign_name: str = "Aries") -> List[Dict]:
        """Deterministic fallback based on Ascendant Sign - always specific."""
        
        fallbacks = {
            "Aries": {"trait": "Athletic build with prominent eyebrows or quick movements", "icon": "build"},
            "Taurus": {"trait": "Solid, sturdy build with thick neck or attractive facial features", "icon": "build"},
            "Gemini": {"trait": "Tall, slender frame with expressive hands or youthful appearance", "icon": "hands"},
            "Cancer": {"trait": "Round face with soft features or expressive, emotional eyes", "icon": "face"},
            "Leo": {"trait": "Broad shoulders with thick, mane-like hair or commanding presence", "icon": "hair"},
            "Virgo": {"trait": "Youthful appearance with clear skin or bright, analytical eyes", "icon": "eyes"},
            "Libra": {"trait": "Symmetrical features with charming smile or natural dimples", "icon": "face"},
            "Scorpio": {"trait": "Intense, penetrating gaze with deep-set eyes or strong physique", "icon": "eyes"},
            "Sagittarius": {"trait": "Tall frame with high forehead or open, friendly facial expression", "icon": "height"},
            "Capricorn": {"trait": "Lean, bony structure with prominent knees/teeth or serious expression", "icon": "build"},
            "Aquarius": {"trait": "Unconventional looks with tall height or distinct side profile", "icon": "height"},
            "Pisces": {"trait": "Dreamy, watery eyes with soft physique or shorter height", "icon": "eyes"}
        }
        
        fallback_data = fallbacks.get(asc_sign_name, {"trait": "Distinctive features with natural constitution", "icon": "body"})
        
        return [{
            'feature': 'physical_trait_1',
            'label': fallback_data["trait"],
            'confidence': 'Medium',
            'source': f'{asc_sign_name} Ascendant (Fallback)',
            'icon': fallback_data["icon"]
        }]