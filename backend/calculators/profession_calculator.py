from .base_calculator import BaseCalculator

class ProfessionCalculator(BaseCalculator):
    """Calculate professional aptitude using real Vedic calculations"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        # Initialize real calculators
        from .shadbala_calculator import ShadbalaCalculator
        from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
        from .chara_karaka_calculator import CharaKarakaCalculator
        
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        self.chara_karaka_calc = CharaKarakaCalculator(chart_data)
        
        # Get real data
        self.shadbala_data = self.shadbala_calc.calculate_shadbala()
        self.dignities_data = self.dignities_calc.calculate_planetary_dignities()
        self.chara_karaka_data = self.chara_karaka_calc.calculate_chara_karakas()
        
        # Classical profession indicators from BPHS
        self.CLASSICAL_PROFESSIONS = {
            'Sun': 'Government service, medicine, authority positions, politics',
            'Moon': 'Public work, liquids, travel, nursing, psychology', 
            'Mars': 'Military, police, surgery, engineering, sports',
            'Mercury': 'Commerce, writing, teaching, mathematics, communication',
            'Jupiter': 'Education, law, finance, religion, counseling',
            'Venus': 'Arts, entertainment, luxury goods, beauty, vehicles',
            'Saturn': 'Labor, mining, agriculture, oil, iron, servants',
            'Rahu': 'Foreign work, technology, unconventional fields',
            'Ketu': 'Spirituality, research, occult, healing arts'
        }
    
    def calculate_professional_analysis(self):
        """Calculate professional analysis using real Vedic calculations"""
        planets = self.chart_data.get('planets', {})
        
        analysis = {
            'tenth_house_analysis': self._analyze_tenth_house_real(planets),
            'atmakaraka_amatyakaraka_analysis': self._get_real_ak_amk_analysis(),
            'planetary_career_strengths': self._get_real_planetary_strengths(),
            'professional_yogas': self._identify_career_yogas(),
            'career_obstacles': self._identify_real_obstacles(),
            'profession_recommendations': self._get_classical_recommendations()
        }
        
        return analysis
    
    def _analyze_tenth_house_real(self, planets):
        """Analyze 10th house using real planetary strengths"""
        tenth_house_sign = self.chart_data.get('houses', [])[9].get('sign', 0) if len(self.chart_data.get('houses', [])) > 9 else 0
        tenth_lord = self._get_sign_lord(tenth_house_sign)
        
        analysis = {
            'house_sign': tenth_house_sign,
            'house_lord': tenth_lord,
            'lord_shadbala_rupas': 0,
            'lord_dignity': 'neutral',
            'planets_in_house': [],
            'house_strength_grade': 'Average'
        }
        
        # Real 10th lord analysis
        if tenth_lord in self.shadbala_data:
            analysis['lord_shadbala_rupas'] = self.shadbala_data[tenth_lord]['total_rupas']
            analysis['lord_dignity'] = self.dignities_data.get(tenth_lord, {}).get('dignity', 'neutral')
        
        # Real planets in 10th house analysis
        for planet_name, planet_data in planets.items():
            if planet_data.get('house') == 10 and planet_name not in ['Gulika', 'Mandi']:
                planet_analysis = {
                    'planet': planet_name,
                    'shadbala_rupas': self.shadbala_data.get(planet_name, {}).get('total_rupas', 0),
                    'dignity': self.dignities_data.get(planet_name, {}).get('dignity', 'neutral'),
                    'strength_grade': self.shadbala_data.get(planet_name, {}).get('grade', 'Average'),
                    'classical_profession': self.CLASSICAL_PROFESSIONS.get(planet_name, 'General work')
                }
                analysis['planets_in_house'].append(planet_analysis)
        
        # Calculate overall house strength using real data
        lord_strength = analysis['lord_shadbala_rupas']
        planets_strength = sum(p['shadbala_rupas'] for p in analysis['planets_in_house'])
        total_strength = lord_strength + planets_strength
        
        if total_strength >= 12:
            analysis['house_strength_grade'] = 'Excellent'
        elif total_strength >= 8:
            analysis['house_strength_grade'] = 'Good'
        elif total_strength >= 5:
            analysis['house_strength_grade'] = 'Average'
        else:
            analysis['house_strength_grade'] = 'Weak'
        
        return analysis
    
    def _get_real_ak_amk_analysis(self):
        """Get real Atmakaraka-Amatyakaraka analysis from Chara Karaka calculator"""
        chara_karakas = self.chara_karaka_data.get('chara_karakas', {})
        
        ak_data = chara_karakas.get('Atmakaraka', {})
        amk_data = chara_karakas.get('Amatyakaraka', {})
        
        analysis = {
            'atmakaraka': {
                'planet': ak_data.get('planet', 'Unknown'),
                'house': ak_data.get('house', 1),
                'shadbala_rupas': self.shadbala_data.get(ak_data.get('planet', ''), {}).get('total_rupas', 0),
                'dignity': self.dignities_data.get(ak_data.get('planet', ''), {}).get('dignity', 'neutral'),
                'classical_profession': self.CLASSICAL_PROFESSIONS.get(ak_data.get('planet', ''), 'General work')
            },
            'amatyakaraka': {
                'planet': amk_data.get('planet', 'Unknown'),
                'house': amk_data.get('house', 1),
                'shadbala_rupas': self.shadbala_data.get(amk_data.get('planet', ''), {}).get('total_rupas', 0),
                'dignity': self.dignities_data.get(amk_data.get('planet', ''), {}).get('dignity', 'neutral'),
                'classical_profession': self.CLASSICAL_PROFESSIONS.get(amk_data.get('planet', ''), 'General work')
            }
        }
        
        # Classical combination analysis
        ak_planet = ak_data.get('planet', '')
        amk_planet = amk_data.get('planet', '')
        
        if ak_planet and amk_planet:
            analysis['combination_strength'] = (
                analysis['atmakaraka']['shadbala_rupas'] + 
                analysis['amatyakaraka']['shadbala_rupas']
            )
            analysis['career_focus'] = f"{self.CLASSICAL_PROFESSIONS.get(ak_planet, 'General')} with {self.CLASSICAL_PROFESSIONS.get(amk_planet, 'support')}"
        
        return analysis
    
    def _get_real_planetary_strengths(self):
        """Get real planetary strengths for career analysis"""
        career_planets = ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        strengths = {}
        
        for planet in career_planets:
            if planet in self.shadbala_data:
                planet_data = self.shadbala_data[planet]
                dignity_data = self.dignities_data.get(planet, {})
                
                strengths[planet] = {
                    'shadbala_rupas': planet_data['total_rupas'],
                    'shadbala_grade': planet_data['grade'],
                    'dignity': dignity_data.get('dignity', 'neutral'),
                    'strength_multiplier': dignity_data.get('strength_multiplier', 1.0),
                    'classical_profession': self.CLASSICAL_PROFESSIONS.get(planet, 'General work'),
                    'career_suitability': self._get_career_suitability(planet_data['total_rupas'], dignity_data.get('strength_multiplier', 1.0))
                }
        
        return strengths
    
    def _identify_career_yogas(self):
        """Identify career yogas using real planetary data"""
        yogas = []
        
        # Check for strong 10th lord
        tenth_house_sign = self.chart_data.get('houses', [])[9].get('sign', 0) if len(self.chart_data.get('houses', [])) > 9 else 0
        tenth_lord = self._get_sign_lord(tenth_house_sign)
        
        if tenth_lord in self.shadbala_data:
            lord_rupas = self.shadbala_data[tenth_lord]['total_rupas']
            lord_dignity = self.dignities_data.get(tenth_lord, {}).get('dignity', 'neutral')
            
            if lord_rupas >= 6 and lord_dignity in ['exalted', 'own_sign', 'moolatrikona']:
                yogas.append({
                    'name': 'Strong 10th Lord Yoga',
                    'description': f'{tenth_lord} as 10th lord is strong with {lord_rupas:.1f} rupas and {lord_dignity} dignity',
                    'strength': 'High'
                })
        
        # Check for exalted planets in 10th house
        planets = self.chart_data.get('planets', {})
        for planet_name, planet_data in planets.items():
            if planet_data.get('house') == 10 and planet_name not in ['Gulika', 'Mandi']:
                dignity = self.dignities_data.get(planet_name, {}).get('dignity', 'neutral')
                if dignity == 'exalted':
                    yogas.append({
                        'name': f'{planet_name} Exaltation in 10th House',
                        'description': f'Exalted {planet_name} in 10th house creates strong career yoga',
                        'strength': 'High'
                    })
        
        return yogas
    
    def _identify_real_obstacles(self):
        """Identify career obstacles using real planetary data"""
        obstacles = []
        
        # Check for debilitated 10th lord
        tenth_house_sign = self.chart_data.get('houses', [])[9].get('sign', 0) if len(self.chart_data.get('houses', [])) > 9 else 0
        tenth_lord = self._get_sign_lord(tenth_house_sign)
        
        if tenth_lord in self.dignities_data:
            dignity = self.dignities_data[tenth_lord].get('dignity', 'neutral')
            if dignity == 'debilitated':
                obstacles.append({
                    'type': 'Debilitated 10th Lord',
                    'description': f'{tenth_lord} as 10th lord is debilitated, causing career challenges',
                    'severity': 'High',
                    'remedy': f'Strengthen {tenth_lord} through appropriate remedies'
                })
        
        return obstacles
    
    def _get_classical_recommendations(self):
        """Get profession recommendations based on classical Vedic principles"""
        recommendations = []
        
        # Analyze strongest planets for career
        planet_strengths = []
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            if planet in self.shadbala_data:
                strength = self.shadbala_data[planet]['total_rupas']
                dignity_multiplier = self.dignities_data.get(planet, {}).get('strength_multiplier', 1.0)
                total_strength = strength * dignity_multiplier
                planet_strengths.append((planet, total_strength))
        
        # Sort by strength and recommend top professions
        planet_strengths.sort(key=lambda x: x[1], reverse=True)
        
        for i, (planet, strength) in enumerate(planet_strengths[:3]):
            if strength >= 4:  # Only recommend if reasonably strong
                recommendations.append({
                    'rank': i + 1,
                    'planet': planet,
                    'strength_score': round(strength, 1),
                    'profession_category': self.CLASSICAL_PROFESSIONS.get(planet, 'General work'),
                    'suitability': 'High' if strength >= 8 else 'Medium' if strength >= 6 else 'Moderate'
                })
        
        return recommendations
    
    def _get_career_suitability(self, shadbala_rupas, dignity_multiplier):
        """Calculate career suitability based on real strength"""
        total_strength = shadbala_rupas * dignity_multiplier
        
        if total_strength >= 8:
            return 'Excellent'
        elif total_strength >= 6:
            return 'Good'
        elif total_strength >= 4:
            return 'Moderate'
        else:
            return 'Weak'
    
    def _get_sign_lord(self, sign_num):
        """Get the lord of a zodiac sign"""
        lords = {
            1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
            7: 'Venus', 8: 'Mars', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
        }
        return lords.get(sign_num, 'Unknown')