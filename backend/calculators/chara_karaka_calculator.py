from .base_calculator import BaseCalculator

class CharaKarakaCalculator(BaseCalculator):
    """Extract Chara Karaka calculation from chara_karakas.py"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        self.KARAKA_DESCRIPTIONS = {
            "Atmakaraka": {
                "title": "Soul Significator",
                "description": "Represents the soul, self, and overall life purpose. Most important planet in the chart.",
                "areas": ["Self-realization", "Life purpose", "Spiritual growth", "Personal identity"]
            },
            "Amatyakaraka": {
                "title": "Career Significator", 
                "description": "Represents career, profession, and material achievements.",
                "areas": ["Career", "Profession", "Work environment", "Material success"]
            },
            "Bhratrukaraka": {
                "title": "Siblings Significator",
                "description": "Represents siblings, courage, and personal efforts.",
                "areas": ["Siblings", "Courage", "Personal efforts", "Initiative"]
            },
            "Matrukaraka": {
                "title": "Mother Significator",
                "description": "Represents mother, home, emotions, and nurturing.",
                "areas": ["Mother", "Home", "Emotions", "Nurturing", "Comfort"]
            },
            "Putrakaraka": {
                "title": "Children Significator", 
                "description": "Represents children, creativity, and intelligence.",
                "areas": ["Children", "Creativity", "Intelligence", "Learning", "Innovation"]
            },
            "Gnatikaraka": {
                "title": "Obstacles Significator",
                "description": "Represents obstacles, diseases, enemies, and challenges.",
                "areas": ["Obstacles", "Health issues", "Enemies", "Challenges", "Competition"]
            },
            "Darakaraka": {
                "title": "Spouse Significator",
                "description": "Represents spouse, partnerships, and relationships.",
                "areas": ["Spouse", "Marriage", "Partnerships", "Relationships", "Cooperation"]
            }
        }
    
    def calculate_chara_karakas(self):
        """Calculate Chara Karakas from chart data"""
        planets = self.chart_data.get('planets', {})
        
        # Get degrees for planets (excluding Rahu/Ketu/Gulika/Mandi)
        planet_degrees = {}
        for planet_name, planet_data in planets.items():
            if planet_name in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
                longitude = planet_data.get('longitude', 0)
                # Use degree within sign for Chara Karaka calculation (traditional method)
                degree_in_sign = longitude % 30
                planet_degrees[planet_name] = degree_in_sign
        
        # Sort planets by degrees (highest to lowest)
        sorted_planets = sorted(planet_degrees.items(), key=lambda x: x[1], reverse=True)
        
        # Assign Karaka roles
        karaka_names = ["Atmakaraka", "Amatyakaraka", "Bhratrukaraka", "Matrukaraka", 
                       "Putrakaraka", "Gnatikaraka", "Darakaraka"]
        
        chara_karakas = {}
        for i, (planet, degree_in_sign) in enumerate(sorted_planets[:7]):
            karaka_name = karaka_names[i] if i < len(karaka_names) else f"Karaka_{i+1}"
            
            planet_info = planets.get(planet, {})
            
            chara_karakas[karaka_name] = {
                'planet': planet,
                'degree_in_sign': round(degree_in_sign, 2),
                'sign': planet_info.get('sign', 0),
                'house': planet_info.get('house', 1),
                'longitude': planet_info.get('longitude', 0),
                'title': self.KARAKA_DESCRIPTIONS.get(karaka_name, {}).get('title', karaka_name),
                'description': self.KARAKA_DESCRIPTIONS.get(karaka_name, {}).get('description', ''),
                'life_areas': self.KARAKA_DESCRIPTIONS.get(karaka_name, {}).get('areas', [])
            }
        
        return {
            "chara_karakas": chara_karakas,
            "calculation_method": "Highest to lowest degrees in signs (excluding Rahu/Ketu)",
            "system": "Jaimini Chara Karaka System"
        }
    
    def get_atmakaraka(self):
        """Get Atmakaraka (soul significator)"""
        karakas = self.calculate_chara_karakas()
        return karakas['chara_karakas'].get('Atmakaraka')
    
    def get_amatyakaraka(self):
        """Get Amatyakaraka (career significator)"""
        karakas = self.calculate_chara_karakas()
        return karakas['chara_karakas'].get('Amatyakaraka')
    
    def get_darakaraka(self):
        """Get Darakaraka (spouse significator)"""
        karakas = self.calculate_chara_karakas()
        return karakas['chara_karakas'].get('Darakaraka')