import os
import json
from datetime import datetime
import google.generativeai as genai
from calculators.ashtakavarga import AshtakavargaCalculator

# Global oracle instance to maintain cache across requests
_oracle_instance = None

def get_oracle_instance():
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = AshtakvargaOracle()
    return _oracle_instance

class AshtakvargaOracle:
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Sign names for reference
        self.sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        

    
    def generate_complete_oracle(self, birth_data, ashtakvarga_data, date, query_type='general', timeline_years=3):
        """Generate complete oracle response with insights and timeline in single Gemini call"""
        
        try:
            # Extract key data for Gemini
            sarva = ashtakvarga_data.get('ashtakavarga', {}).get('sarvashtakavarga', {})
            total_bindus = ashtakvarga_data.get('ashtakavarga', {}).get('total_bindus', 0)
            
            # Get chart data for proper house calculation
            chart_data = ashtakvarga_data.get('chart_data', {})
            ascendant = chart_data.get('ascendant', 0)
            ascendant_sign = int(ascendant / 30) if ascendant else 0
            
            # Find strongest and weakest signs
            if sarva and len(sarva) > 0:
                strongest_sign = max(sarva.keys(), key=lambda k: sarva[k])
                weakest_sign = min(sarva.keys(), key=lambda k: sarva[k])
                # Convert to int if string
                strongest_sign = int(strongest_sign) if isinstance(strongest_sign, str) else strongest_sign
                weakest_sign = int(weakest_sign) if isinstance(weakest_sign, str) else weakest_sign
                max_bindus = sarva.get(str(strongest_sign), sarva.get(strongest_sign, 0))
                min_bindus = sarva.get(str(weakest_sign), sarva.get(weakest_sign, 0))
            else:
                strongest_sign = 0
                weakest_sign = 0
                max_bindus = 0
                min_bindus = 0
            
            strength_percentage = int((total_bindus / 337) * 100) if total_bindus > 0 else 50
            
            # Format distribution for prompt with proper house numbers
            distribution_text = ""
            for i in range(12):
                # Keys are strings in the sarva dict, so use str(i)
                points = sarva.get(str(i), 0) if sarva else 0
                strength = "Strong" if points >= 30 else "Weak" if points <= 25 else "Moderate"
                # Calculate proper house number from ascendant
                house_num = ((i - ascendant_sign) % 12) + 1
                distribution_text += f"- {self.sign_names[i]} (House {house_num}): {points} points ({strength})\n"

            # CONSTRUCTION THE PROMPT
            # CHANGED: "Ancient Oracle" -> "Analytical Astrologer"
            # FIXED: Added birth_data['date'] separately from current date
            prompt = f"""
You are an expert Vedic Astrologer specializing in Ashtakavarga. 
Your goal is to provide CLEAR, DATA-DRIVEN, and PRACTICAL life guidance. 
Do NOT use flowery, mystical, or poetic language. Speak like a professional consultant.

USER PROFILE:
- Name: {birth_data.get('name', 'Client')}
- Birth Date: {birth_data.get('date')} (YYYY-MM-DD)
- Current Date for Analysis: {date}

ASHTAKAVARGA DATA (The Logic):
- Total Strength: {strength_percentage}% ({total_bindus}/337 points)
- Strongest Sector: {self.sign_names[strongest_sign]} ({max_bindus} points)
- Weakest Sector: {self.sign_names[weakest_sign]} ({min_bindus} points)

ZODIAC SCORECARD (Bindus per Sign):
{distribution_text}

INSTRUCTIONS:
1. Analyze the "Strongest Sign" and explain specifically what life area it helps (e.g., "High points in Libra (7th House) indicates strong partnerships").
2. Analyze the "Weakest Sign" and give a specific warning.
3. For the timeline, look at the transit of Saturn and Jupiter (approximate) over the next {timeline_years} years.
   - If they enter a high-point sign (>30), predict success.
   - If they enter a low-point sign (<25), predict challenges.

REQUIRED JSON FORMAT:
{{
  "oracle_message": "3-4 sentences summarizing their current strength based on the points. MENTION SPECIFIC POINT COUNTS in the text.",
  "power_actions": [
    {{"type": "do", "text": "Specific action based on their strongest sign"}},
    {{"type": "avoid", "text": "Specific warning based on their weakest sign"}}
  ],
  "cosmic_strength": {strength_percentage},
  "pillar_insights": [
    "Aries: [Points] - [One sentence analysis]",
    "Taurus: [Points] - [One sentence analysis]",
    ... (for all 12 signs)
  ],
  "timeline_events": {{
    "general": [
      {{"title": "Event", "date_range": "Month Year", "description": "Description", "score": 8}}
    ],
    "love": [
      {{"title": "Event", "date_range": "Month Year", "description": "Description", "score": 8}}
    ],
    "wealth": [
      {{"title": "Event", "date_range": "Month Year", "description": "Description", "score": 8}}
    ],
    "career": [
      {{"title": "Event", "date_range": "Month Year", "description": "Description", "score": 8}}
    ],
    "health": [
      {{"title": "Event", "date_range": "Month Year", "description": "Description", "score": 8}}
    ]
  }}
}}

CRITICAL: You MUST create 3-4 timeline events for next {timeline_years} years for EACH of these 5 categories:
- general (overall life events)
- love (relationships, marriage, partnerships) 
- wealth (money, investments, property)
- career (job, business, professional growth)
- health (physical wellness, medical events)

Each timeline event must have: title, date_range, description, score (1-10).

Return ONLY valid JSON. No markdown formatting. No explanatory text.
"""
            response = self.model.generate_content(prompt)
            
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            complete_data = json.loads(text.strip())
            return complete_data
            
        except Exception as e:
            raise e
    
    def generate_oracle_insight(self, birth_data, ashtakvarga_data, date):
        """Returns complete oracle data for frontend caching"""
        return self.generate_complete_oracle(birth_data, ashtakvarga_data, date)