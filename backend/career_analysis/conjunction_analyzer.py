class ConjunctionAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planets = chart_data['planets']
        
    def analyze_career_conjunctions(self):
        """Analyze planetary conjunctions affecting career with modern interpretations"""
        conjunctions = []
        
        # Find conjunctions (planets within 8 degrees)
        for planet1 in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
            for planet2 in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                if planet1 != planet2:
                    degree_diff = abs(self.planets[planet1]['longitude'] - self.planets[planet2]['longitude'])
                    if degree_diff <= 8 or degree_diff >= 352:  # Account for 0-360 wrap
                        house = self.planets[planet1]['house']
                        conjunction = self._analyze_conjunction_career_impact(planet1, planet2, house)
                        if conjunction:
                            conjunctions.append(conjunction)
        
        return conjunctions
    
    def _analyze_conjunction_career_impact(self, planet1, planet2, house):
        """Analyze specific conjunction impact on career with modern interpretations"""
        # Saturn-Ketu conjunction - AI and spiritual technology
        if (planet1 == 'Saturn' and planet2 == 'Ketu') or (planet1 == 'Ketu' and planet2 == 'Saturn'):
            return {
                'planets': ['Saturn', 'Ketu'],
                'house': house,
                'career_impact': 'AI Engineering & Spiritual Technology',
                'description': f'Saturn-Ketu in H{house} combines disciplined structure with past-life mystical knowledge, creating expertise in AI, machine learning, and spiritual technology applications',
                'modern_fields': ['AI Engineering', 'Machine Learning', 'Spiritual Apps', 'Meditation Technology', 'Consciousness Research'],
                'karmic_pattern': 'Past-life expertise in mystical sciences now manifesting through advanced technology'
            }
        
        # Mars-Ketu conjunction - Technical research and innovation
        if (planet1 == 'Mars' and planet2 == 'Ketu') or (planet1 == 'Ketu' and planet2 == 'Mars'):
            return {
                'planets': ['Mars', 'Ketu'],
                'house': house,
                'career_impact': 'Technical Innovation & Research',
                'description': f'Mars-Ketu in H{house} creates technical expertise with detached precision, ideal for cutting-edge engineering and research',
                'modern_fields': ['Robotics Engineering', 'Space Technology', 'Defense Research', 'Biomedical Engineering', 'Quantum Computing'],
                'karmic_pattern': 'Past-life warrior knowledge applied to modern technical challenges'
            }
        
        # Mercury-Ketu conjunction - AI and data analysis
        if (planet1 == 'Mercury' and planet2 == 'Ketu') or (planet1 == 'Ketu' and planet2 == 'Mercury'):
            return {
                'planets': ['Mercury', 'Ketu'],
                'house': house,
                'career_impact': 'AI Communication & Data Science',
                'description': f'Mercury-Ketu in H{house} combines analytical intelligence with intuitive insights, perfect for AI and data science',
                'modern_fields': ['Data Science', 'Natural Language Processing', 'AI Communication', 'Algorithmic Trading', 'Predictive Analytics'],
                'karmic_pattern': 'Past-life scholarly knowledge manifesting through data and algorithms'
            }
        
        # Rahu-Mars conjunction - Innovative engineering
        if (planet1 == 'Rahu' and planet2 == 'Mars') or (planet1 == 'Mars' and planet2 == 'Rahu'):
            return {
                'planets': ['Rahu', 'Mars'],
                'house': house,
                'career_impact': 'Innovative Engineering & Technology',
                'description': f'Rahu-Mars in H{house} drives towards cutting-edge engineering and technological innovation',
                'modern_fields': ['Aerospace Engineering', 'Electric Vehicles', 'Renewable Energy', 'Biotechnology', 'Nanotechnology'],
                'karmic_pattern': 'Future-oriented technical ambitions with aggressive implementation'
            }
        
        # Rahu-Mercury conjunction - Digital innovation
        if (planet1 == 'Rahu' and planet2 == 'Mercury') or (planet1 == 'Mercury' and planet2 == 'Rahu'):
            return {
                'planets': ['Rahu', 'Mercury'],
                'house': house,
                'career_impact': 'Digital Innovation & Communication',
                'description': f'Rahu-Mercury in H{house} creates expertise in digital communication and innovative technology platforms',
                'modern_fields': ['Social Media Technology', 'Digital Marketing', 'Blockchain', 'Cryptocurrency', 'Virtual Reality'],
                'karmic_pattern': 'Obsessive drive towards digital communication and networking technologies'
            }
        
        # Jupiter-Ketu conjunction - Spiritual wisdom and teaching
        if (planet1 == 'Jupiter' and planet2 == 'Ketu') or (planet1 == 'Ketu' and planet2 == 'Jupiter'):
            return {
                'planets': ['Jupiter', 'Ketu'],
                'house': house,
                'career_impact': 'Spiritual Teaching & Wisdom Technology',
                'description': f'Jupiter-Ketu in H{house} combines higher wisdom with detached knowledge, ideal for spiritual teaching and wisdom-based technology',
                'modern_fields': ['Spiritual Counseling', 'Educational Technology', 'Wisdom Apps', 'Philosophical Research', 'Consciousness Studies'],
                'karmic_pattern': 'Past-life spiritual teacher knowledge applied to modern wisdom sharing'
            }
        
        return None
    
    def analyze_tenth_house_conjunctions(self):
        """Analyze conjunctions specifically in 10th house for career"""
        tenth_house_planets = []
        for planet, data in self.planets.items():
            if data['house'] == 10:
                tenth_house_planets.append(planet)
        
        if len(tenth_house_planets) < 2:
            return None
        
        # Analyze all combinations in 10th house
        career_combinations = []
        for i in range(len(tenth_house_planets)):
            for j in range(i + 1, len(tenth_house_planets)):
                planet1, planet2 = tenth_house_planets[i], tenth_house_planets[j]
                combination = self._analyze_conjunction_career_impact(planet1, planet2, 10)
                if combination:
                    career_combinations.append(combination)
        
        return career_combinations
    
    def analyze_karmic_career_patterns(self):
        """Analyze Rahu-Ketu axis for karmic career patterns"""
        rahu_house = self.planets['Rahu']['house']
        ketu_house = self.planets['Ketu']['house']
        rahu_sign = int(self.planets['Rahu']['longitude'] / 30)
        ketu_sign = int(self.planets['Ketu']['longitude'] / 30)
        
        patterns = {
            'rahu_career_drive': self._analyze_rahu_career_drive(rahu_house, rahu_sign),
            'ketu_past_expertise': self._analyze_ketu_past_expertise(ketu_house, ketu_sign),
            'karmic_balance': self._analyze_karmic_career_balance(rahu_house, ketu_house)
        }
        
        return patterns
    
    def _analyze_rahu_career_drive(self, house, sign):
        """Analyze Rahu's career obsessions and future-oriented drives"""
        house_meanings = {
            1: 'Personal branding and leadership innovation',
            2: 'Wealth through technology and foreign connections',
            3: 'Communication technology and media innovation',
            4: 'Real estate technology and home automation',
            5: 'Creative technology and entertainment innovation',
            6: 'Health technology and service innovation',
            7: 'Partnership in technology and international business',
            8: 'Research technology and transformation industries',
            9: 'Educational technology and philosophical innovation',
            10: 'Career in cutting-edge technology and innovation',
            11: 'Network technology and social innovation',
            12: 'Spiritual technology and behind-the-scenes innovation'
        }
        
        sign_meanings = {
            0: 'Pioneering technology leadership',  # Aries
            1: 'Luxury technology and material innovation',  # Taurus
            2: 'Communication and networking technology',  # Gemini
            3: 'Emotional technology and care innovation',  # Cancer
            4: 'Entertainment technology and creative innovation',  # Leo
            5: 'Analytical technology and precision innovation',  # Virgo
            6: 'Relationship technology and harmony innovation',  # Libra
            7: 'Transformation technology and deep innovation',  # Scorpio
            8: 'Wisdom technology and educational innovation',  # Sagittarius
            9: 'Structural technology and systematic innovation',  # Capricorn
            10: 'Social technology and humanitarian innovation',  # Aquarius
            11: 'Spiritual technology and transcendent innovation'  # Pisces
        }
        
        return {
            'house_drive': house_meanings[house],
            'sign_approach': sign_meanings[sign],
            'obsession_area': f'Future-oriented career in {house_meanings[house].lower()}'
        }
    
    def _analyze_ketu_past_expertise(self, house, sign):
        """Analyze Ketu's past-life expertise and natural talents"""
        house_meanings = {
            1: 'Natural leadership and personal mastery',
            2: 'Innate wealth consciousness and resource management',
            3: 'Intuitive communication and artistic expression',
            4: 'Deep emotional wisdom and nurturing abilities',
            5: 'Creative genius and spiritual knowledge',
            6: 'Natural healing abilities and service orientation',
            7: 'Relationship wisdom and partnership mastery',
            8: 'Mystical knowledge and transformation expertise',
            9: 'Spiritual teaching and philosophical wisdom',
            10: 'Natural authority and career mastery',
            11: 'Social wisdom and network mastery',
            12: 'Spiritual liberation and transcendent knowledge'
        }
        
        sign_meanings = {
            0: 'Warrior and leadership expertise',  # Aries
            1: 'Material mastery and stability expertise',  # Taurus
            2: 'Communication and intellectual expertise',  # Gemini
            3: 'Emotional and nurturing expertise',  # Cancer
            4: 'Creative and royal expertise',  # Leo
            5: 'Analytical and service expertise',  # Virgo
            6: 'Harmony and relationship expertise',  # Libra
            7: 'Mystical and transformation expertise',  # Scorpio
            8: 'Wisdom and teaching expertise',  # Sagittarius
            9: 'Structural and organizational expertise',  # Capricorn
            10: 'Innovation and humanitarian expertise',  # Aquarius
            11: 'Spiritual and transcendent expertise'  # Pisces
        }
        
        return {
            'natural_talent': house_meanings[house],
            'expertise_type': sign_meanings[sign],
            'past_life_skill': f'Mastery in {house_meanings[house].lower()}'
        }
    
    def _analyze_karmic_career_balance(self, rahu_house, ketu_house):
        """Analyze the karmic balance between Rahu desires and Ketu detachment"""
        axis_meanings = {
            (1, 7): 'Balance personal innovation with partnership wisdom',
            (2, 8): 'Balance material technology with mystical transformation',
            (3, 9): 'Balance communication innovation with spiritual teaching',
            (4, 10): 'Balance home technology with career mastery',
            (5, 11): 'Balance creative innovation with social wisdom',
            (6, 12): 'Balance service technology with spiritual liberation'
        }
        
        # Normalize the axis (smaller house first)
        axis = tuple(sorted([rahu_house, ketu_house]))
        
        return {
            'karmic_lesson': axis_meanings.get(axis, 'Balance innovation with wisdom'),
            'career_integration': f'Integrate future technology drives with past-life expertise'
        }