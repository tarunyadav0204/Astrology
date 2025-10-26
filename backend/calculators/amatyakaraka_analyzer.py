from .planet_analyzer import PlanetAnalyzer
from .divisional_chart_calculator import DivisionalChartCalculator
from .chara_karaka_calculator import CharaKarakaCalculator
from .aspect_calculator import AspectCalculator
from .profession_calculator import ProfessionCalculator
from .house_relationship_calculator import HouseRelationshipCalculator

class AmatyakarakaAnalyzer:
    """Jaimini Amatyakaraka analysis for profession"""
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planet_analyzer = PlanetAnalyzer(chart_data)
        self.divisional_calc = DivisionalChartCalculator(chart_data)
        self.chara_karaka_calc = CharaKarakaCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
        self.profession_calc = ProfessionCalculator(chart_data)
        self.house_rel_calc = HouseRelationshipCalculator(chart_data)
    
    def analyze_amatyakaraka(self):
        """Complete Amatyakaraka analysis using Jaimini method"""
        # Step 1: Calculate Amatyakaraka
        amatyakaraka = self._calculate_amatyakaraka()
        
        # Step 2: Analyze AmK planet, house & sign
        amk_analysis = self._analyze_amk_planet(amatyakaraka)
        
        # Step 3: Check AK-AmK relationship
        ak_amk_relationship = self._analyze_ak_amk_relationship(amatyakaraka)
        
        # Step 4: Analyze AmK in Navamsa
        navamsa_analysis = self._analyze_amk_navamsa(amatyakaraka)
        
        # Step 5: Analyze 10th from AmK
        tenth_from_amk = self._analyze_tenth_from_amk(amatyakaraka)
        
        # Step 6: AmK in D10 chart
        d10_analysis = self._analyze_amk_d10(amatyakaraka)
        
        return {
            'amatyakaraka_planet': amatyakaraka,
            'amk_analysis': amk_analysis,
            'ak_amk_relationship': ak_amk_relationship,
            'navamsa_analysis': navamsa_analysis,
            'tenth_from_amk': tenth_from_amk,
            'd10_analysis': d10_analysis,
            'profession_summary': self._get_profession_summary(amatyakaraka, amk_analysis)
        }
    
    def _calculate_amatyakaraka(self):
        """Calculate Amatyakaraka using proper Chara Karaka calculator"""
        chara_karakas = self.chara_karaka_calc.calculate_chara_karakas()
        return chara_karakas['chara_karakas']['Amatyakaraka']['planet']
    
    def _analyze_amk_planet(self, amatyakaraka):
        """Analyze Amatyakaraka planet characteristics"""
        amk_data = self.chart_data['planets'][amatyakaraka]
        amk_house = amk_data['house']
        amk_sign = amk_data['sign']
        
        # Get comprehensive planet analysis
        planet_analysis = self.planet_analyzer.analyze_planet(amatyakaraka)
        
        # Get real profession analysis
        profession_data = self.profession_calc.calculate_professional_analysis()
        planetary_strengths = profession_data['planetary_career_strengths']
        
        # Get real house analysis
        house_analysis = self.house_rel_calc.analyze_house_lord(amk_house)
        
        return {
            'planet': amatyakaraka,
            'house': amk_house,
            'sign': amk_sign,
            'sign_name': self._get_sign_name(amk_sign),
            'profession_indications': self._get_real_profession_indications(amatyakaraka, planetary_strengths),
            'house_significance': self._get_house_career_significance(amk_house),
            'sign_style': self._get_real_sign_career_style(amk_sign, planet_analysis),
            'planet_analysis': planet_analysis,
            'dignity': planet_analysis['dignity_analysis']['dignity'],
            'strength': planet_analysis['strength_analysis']['shadbala_rupas']
        }
    
    def _analyze_ak_amk_relationship(self, amatyakaraka):
        """Analyze relationship between Atmakaraka and Amatyakaraka"""
        atmakaraka = self._calculate_atmakaraka()
        
        ak_data = self.chart_data['planets'][atmakaraka]
        amk_data = self.chart_data['planets'][amatyakaraka]
        
        ak_house = ak_data['house']
        amk_house = amk_data['house']
        
        # Calculate house relationship
        house_diff = abs(ak_house - amk_house)
        if house_diff > 6:
            house_diff = 12 - house_diff
        
        relationship_type = self._get_ak_amk_relationship_type(house_diff)
        
        return {
            'atmakaraka': atmakaraka,
            'atmakaraka_house': ak_house,
            'amatyakaraka_house': amk_house,
            'house_difference': house_diff,
            'relationship_type': relationship_type,
            'career_impact': self._interpret_ak_amk_relationship(relationship_type),
            'conjunction': ak_house == amk_house,
            'mutual_aspect': self._check_mutual_aspect(atmakaraka, amatyakaraka)
        }
    
    def _analyze_amk_navamsa(self, amatyakaraka):
        """Analyze Amatyakaraka in Navamsa (D9)"""
        amk_data = self.chart_data['planets'][amatyakaraka]
        longitude = amk_data['longitude']
        
        navamsa_sign = self._calculate_navamsa_sign(longitude)
        navamsa_lord = self._get_sign_lord(navamsa_sign)
        
        return {
            'navamsa_sign': navamsa_sign,
            'navamsa_sign_name': self._get_sign_name(navamsa_sign),
            'navamsa_lord': navamsa_lord,
            'work_environment': self._get_navamsa_work_environment(navamsa_sign),
            'inner_drive': self._get_navamsa_inner_drive(navamsa_sign),
            'growth_potential': self._assess_navamsa_growth_potential(navamsa_lord)
        }
    
    def _analyze_tenth_from_amk(self, amatyakaraka):
        """Analyze 10th house from Amatyakaraka (Karma Bhava)"""
        amk_data = self.chart_data['planets'][amatyakaraka]
        amk_house = amk_data['house']
        
        karma_bhava = ((amk_house - 1 + 9) % 12) + 1
        house_info = self._get_house_info(karma_bhava)
        planets_in_karma = self._get_planets_in_house(karma_bhava)
        aspects_on_karma = self._get_aspects_on_house(karma_bhava)
        
        return {
            'karma_bhava_house': karma_bhava,
            'karma_bhava_sign': house_info['sign'],
            'karma_bhava_lord': house_info['lord'],
            'planets_in_karma': planets_in_karma,
            'aspects_on_karma': aspects_on_karma,
            'career_refinement': self._interpret_karma_bhava(house_info, planets_in_karma),
            'lord_analysis': self.planet_analyzer.analyze_planet(house_info['lord'])
        }
    
    def _analyze_amk_d10(self, amatyakaraka):
        """Analyze Amatyakaraka in D10 chart using proper divisional calculator"""
        d10_result = self.divisional_calc.calculate_divisional_chart(10)
        d10_chart = d10_result['divisional_chart']
        amk_d10_data = d10_chart['planets'][amatyakaraka]
        
        # Calculate house position in D10
        d10_asc_sign = int(d10_chart['ascendant'] / 30)
        amk_d10_house = ((amk_d10_data['sign'] - d10_asc_sign) % 12) + 1
        
        return {
            'amk_position_d10': {
                'house': amk_d10_house,
                'sign': amk_d10_data['sign'],
                'sign_name': self._get_sign_name(amk_d10_data['sign'])
            },
            'aspects_in_d10': self._get_d10_aspects(amatyakaraka, d10_chart),
            'real_world_expression': self._interpret_amk_d10_position({'house': amk_d10_house}),
            'career_manifestation': self._get_d10_career_manifestation(amatyakaraka, {'house': amk_d10_house})
        }
    
    def _get_profession_summary(self, amatyakaraka, amk_analysis):
        """Generate comprehensive profession summary"""
        planet_indications = amk_analysis['profession_indications']
        house_significance = amk_analysis['house_significance']
        sign_style = amk_analysis['sign_style']
        
        return {
            'primary_field': planet_indications['primary_field'],
            'career_style': sign_style,
            'work_area': house_significance,
            'key_strengths': self._get_amk_key_strengths(amatyakaraka, amk_analysis),
            'recommended_paths': self._get_recommended_career_paths(amatyakaraka, amk_analysis),
            'success_factors': self._get_success_factors(amatyakaraka, amk_analysis)
        }
    
    def _calculate_atmakaraka(self):
        """Calculate Atmakaraka using proper Chara Karaka calculator"""
        chara_karakas = self.chara_karaka_calc.calculate_chara_karakas()
        return chara_karakas['chara_karakas']['Atmakaraka']['planet']
    
    def _get_real_profession_indications(self, planet, planetary_strengths):
        """Get real profession indications using ProfessionCalculator"""
        planet_data = planetary_strengths[planet]
        
        return {
            'primary_field': planet_data['classical_profession'],
            'secondary_fields': self._get_secondary_fields_from_strength(planet, planet_data),
            'work_style': self._get_work_style_from_analysis(planet, planet_data),
            'career_suitability': planet_data['career_suitability'],
            'strength_score': planet_data['shadbala_rupas']
        }
    
    def _get_secondary_fields_from_strength(self, planet, planet_data):
        """Get secondary fields based on real planetary strength"""
        strength = planet_data['shadbala_rupas']
        dignity = planet_data['dignity']
        
        base_fields = {
            'Sun': ['Government service', 'Medical practice', 'Authority positions'],
            'Moon': ['Public service', 'Healthcare', 'Psychology', 'Travel industry'],
            'Mars': ['Engineering', 'Defense', 'Sports', 'Surgery'],
            'Mercury': ['Business', 'Education', 'Communication', 'Technology'],
            'Jupiter': ['Law', 'Finance', 'Teaching', 'Advisory roles'],
            'Venus': ['Arts', 'Entertainment', 'Luxury goods', 'Design'],
            'Saturn': ['Industry', 'Construction', 'Mining', 'Service sector']
        }
        
        fields = base_fields.get(planet, ['General professional work'])
        
        if strength >= 6 and dignity in ['exalted', 'own_sign']:
            fields = [f'High-level {field.lower()}' for field in fields]
        elif strength < 3 or dignity == 'debilitated':
            fields = [f'Support roles in {field.lower()}' for field in fields]
            
        return fields
    
    def _get_work_style_from_analysis(self, planet, planet_data):
        """Get work style from real planetary analysis"""
        strength = planet_data['shadbala_rupas']
        dignity = planet_data['dignity']
        
        base_styles = {
            'Sun': 'Authoritative and leadership-oriented',
            'Moon': 'Intuitive and people-focused', 
            'Mars': 'Action-oriented and competitive',
            'Mercury': 'Analytical and communicative',
            'Jupiter': 'Wise and advisory',
            'Venus': 'Creative and harmonious',
            'Saturn': 'Disciplined and systematic'
        }
        
        base_style = base_styles.get(planet, 'Balanced approach')
        
        if strength >= 6 and dignity in ['exalted', 'own_sign']:
            return f"Highly effective {base_style.lower()} with exceptional results"
        elif strength < 3 or dignity == 'debilitated':
            return f"Challenged {base_style.lower()} requiring development"
        else:
            return base_style
    
    def _get_real_sign_career_style(self, sign, planet_analysis):
        """Get career style based on real planetary analysis in sign"""
        dignity = planet_analysis['dignity_analysis']['dignity']
        strength = planet_analysis['strength_analysis']['shadbala_rupas']
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        sign_name = sign_names[sign] if 0 <= sign < 12 else 'Unknown'
        
        if dignity == 'exalted' and strength >= 6:
            return f'Highly effective {sign_name} approach with exceptional results'
        elif dignity == 'debilitated' or strength < 3:
            return f'Challenged {sign_name} approach requiring support'
        elif dignity in ['own_sign', 'moolatrikona']:
            return f'Natural {sign_name} approach with good results'
        else:
            return f'Moderate {sign_name} approach with steady progress'
    
    def _get_ak_amk_relationship_type(self, house_diff):
        """Determine AK-AmK relationship using proper Vedic principles"""
        if house_diff == 0:
            return 'Conjunction (Perfect alignment)'
        elif house_diff in [4, 8]:  # 5th and 9th from each other
            return 'Trine (Highly harmonious)'
        elif house_diff in [3, 9]:  # 4th and 10th from each other  
            return 'Kendra (Strong support)'
        elif house_diff in [2, 10]:  # 3rd and 11th from each other
            return 'Upachaya (Growth through effort)'
        elif house_diff in [1, 11]:  # 2nd and 12th from each other
            return 'Dhana-Vyaya (Financial fluctuation)'
        elif house_diff in [5, 7]:  # 6th and 8th from each other
            return 'Dusthana (Obstacles and transformation)'
        else:
            return 'Neutral relationship'
    
    def _interpret_ak_amk_relationship(self, relationship_type):
        """Interpret AK-AmK relationship impact on career"""
        interpretations = {
            'Conjunction (Perfect alignment)': 'Perfect alignment between soul purpose and profession - high success potential',
            'Trine (Highly harmonious)': 'Natural flow between life purpose and career - satisfaction and growth',
            'Kendra (Strong support)': 'Strong foundation for career development with steady progress',
            'Upachaya (Growth through effort)': 'Career grows through effort - gradual but steady professional development',
            'Dhana-Vyaya (Financial fluctuation)': 'Financial ups and downs in career - need for careful planning',
            'Dusthana (Obstacles and transformation)': 'Challenges lead to career transformation and eventual success',
            'Neutral relationship': 'Moderate relationship - career develops through balanced approach'
        }
        return interpretations.get(relationship_type, 'Balanced career development')
    
    def _calculate_navamsa_sign(self, longitude):
        """Calculate Navamsa sign using proper divisional calculator"""
        d9_result = self.divisional_calc.calculate_divisional_chart(9)
        d9_chart = d9_result['divisional_chart']
        
        for planet, data in d9_chart['planets'].items():
            if abs(data['longitude'] - longitude) < 1:
                return data['sign']
        
        # If exact match not found, calculate manually
        sign = int(longitude / 30)
        degree = longitude % 30
        navamsa_part = int(degree / 3.333333)
        
        if sign in [0, 3, 6, 9]:
            return (sign + navamsa_part) % 12
        elif sign in [1, 4, 7, 10]:
            return ((sign + 8) + navamsa_part) % 12
        else:
            return ((sign + 4) + navamsa_part) % 12
    
    def _get_navamsa_inner_drive(self, navamsa_sign):
        """Get inner drive from real D9 planetary analysis"""
        d9_result = self.divisional_calc.calculate_divisional_chart(9)
        d9_chart = d9_result['divisional_chart']
        strongest_planet = None
        max_strength = 0
        
        for planet, data in d9_chart['planets'].items():
            if planet in self.profession_calc.shadbala_data:
                strength = self.profession_calc.shadbala_data[planet]['total_rupas']
                if strength > max_strength:
                    max_strength = strength
                    strongest_planet = planet
        
        drive_map = {
            'Sun': 'Drive for leadership and recognition',
            'Moon': 'Drive for emotional fulfillment and public service',
            'Mars': 'Drive for achievement and competition',
            'Mercury': 'Drive for knowledge and communication',
            'Jupiter': 'Drive for wisdom and teaching',
            'Venus': 'Drive for creativity and harmony',
            'Saturn': 'Drive for discipline and long-term success'
        }
        return drive_map.get(strongest_planet, 'Drive for balanced professional growth')
    
    def _get_navamsa_work_environment(self, navamsa_sign):
        """Get work environment from real D9 analysis"""
        d9_result = self.divisional_calc.calculate_divisional_chart(9)
        d9_chart = d9_result['divisional_chart']
        environment_factors = []
        
        for planet, data in d9_chart['planets'].items():
            if data['sign'] == navamsa_sign:
                if planet in ['Sun', 'Mars']:
                    environment_factors.append('authoritative')
                elif planet in ['Moon', 'Venus']:
                    environment_factors.append('harmonious')
                elif planet == 'Mercury':
                    environment_factors.append('communicative')
                elif planet == 'Jupiter':
                    environment_factors.append('educational')
                elif planet == 'Saturn':
                    environment_factors.append('structured')
        
        if environment_factors:
            return f"Work environment tends to be {', '.join(environment_factors)}"
        else:
            return "Balanced work environment with moderate influences"
    
    def _check_mutual_aspect(self, planet1, planet2):
        """Check mutual aspect between two planets"""
        p1_data = self.chart_data['planets'][planet1]
        p2_data = self.chart_data['planets'][planet2]
        
        p1_house = p1_data['house']
        p2_house = p2_data['house']
        
        # Check if planet1 aspects planet2's house
        p1_aspects_p2 = p2_house in self._get_aspect_houses(planet1, p1_house)
        # Check if planet2 aspects planet1's house  
        p2_aspects_p1 = p1_house in self._get_aspect_houses(planet2, p2_house)
        
        return p1_aspects_p2 and p2_aspects_p1
    
    def _get_d10_career_manifestation(self, amatyakaraka, amk_d10_data):
        """Get career manifestation using real D10 analysis"""
        d10_house = amk_d10_data['house']
        base_profession = self.profession_calc.CLASSICAL_PROFESSIONS[amatyakaraka]
        
        if d10_house == 10:
            return f"Exceptional manifestation in {base_profession} with high recognition"
        elif d10_house in [1, 4, 7]:
            return f"Strong manifestation in {base_profession} with good stability"
        elif d10_house in [5, 9]:
            return f"Fortunate manifestation in {base_profession} with growth"
        else:
            return f"Moderate manifestation in {base_profession} requiring effort"
    
    # Helper methods remain the same
    def _assess_navamsa_growth_potential(self, navamsa_lord):
        return f"Growth potential depends on {navamsa_lord}'s strength and placement"
    
    def _get_house_info(self, house_number):
        ascendant_longitude = self.chart_data['ascendant']
        ascendant_sign = int(ascendant_longitude / 30)
        house_sign_num = (ascendant_sign + house_number - 1) % 12
        
        return {
            'sign': self._get_sign_name(house_sign_num),
            'lord': self._get_sign_lord(house_sign_num),
            'sign_number': house_sign_num
        }
    
    def _get_planets_in_house(self, house_number):
        planets = []
        for planet, data in self.chart_data['planets'].items():
            if data['house'] == house_number:
                planets.append(planet)
        return planets
    
    def _get_aspects_on_house(self, house_number):
        aspects = []
        for planet, data in self.chart_data['planets'].items():
            planet_house = data['house']
            aspected_houses = self.planet_analyzer._get_aspect_houses(planet, planet_house)
            if house_number in aspected_houses:
                aspects.append(planet)
        return aspects
    
    def _interpret_karma_bhava(self, house_info, planets):
        interpretation = f"Career theme refined by {house_info['sign']} qualities"
        if planets:
            interpretation += f" with {', '.join(planets)} influence"
        return interpretation
    
    def _get_amk_key_strengths(self, amatyakaraka, amk_analysis):
        planet_strengths = {
            'Sun': ['Leadership', 'Authority', 'Administration'],
            'Moon': ['Public relations', 'Emotional intelligence', 'Adaptability'],
            'Mars': ['Technical skills', 'Action orientation', 'Competitive spirit'],
            'Mercury': ['Communication', 'Analytical thinking', 'Versatility'],
            'Jupiter': ['Wisdom', 'Teaching ability', 'Strategic thinking'],
            'Venus': ['Creativity', 'Aesthetic sense', 'Relationship building'],
            'Saturn': ['Discipline', 'Systematic approach', 'Persistence']
        }
        return planet_strengths.get(amatyakaraka, ['General professional skills'])
    
    def _get_recommended_career_paths(self, amatyakaraka, amk_analysis):
        house = amk_analysis['house']
        planet_field = amk_analysis['profession_indications']['primary_field']
        
        paths = [
            f"Primary: {planet_field}",
            f"House influence: {amk_analysis['house_significance']}",
            f"Style: {amk_analysis['sign_style']}"
        ]
        return paths
    
    def _get_success_factors(self, amatyakaraka, amk_analysis):
        factors = [
            f"Leverage {amatyakaraka} qualities in profession",
            f"Work in {amk_analysis['profession_indications']['work_style']} manner",
            f"Focus on {amk_analysis['house_significance']} area"
        ]
        
        if amk_analysis['dignity'] in ['exalted', 'own_sign']:
            factors.append("Strong planetary dignity supports career success")
        
        return factors
    
    def _get_sign_name(self, sign_number):
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_number % 12]
    
    def _get_sign_lord(self, sign_number):
        lords = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
                'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter']
        return lords[sign_number % 12]
    
    def _get_house_career_significance(self, house_number):
        """Get career significance of house placement for Amatyakaraka"""
        house_meanings = {
            1: 'Personal brand and leadership in career - direct authority and recognition',
            2: 'Wealth creation and resource management - finance and value-based work',
            3: 'Communication and skill-based career - media, writing, and technical expertise',
            4: 'Stable foundation career - real estate, education, and emotional satisfaction',
            5: 'Creative and speculative career - innovation, entertainment, and advisory roles',
            6: 'Service-oriented career with competitive advantage - healthcare, law, problem-solving',
            7: 'Partnership-based career and public relations - business partnerships and client work',
            8: 'Transformative and research-oriented - deep analysis, crisis management, hidden systems',
            9: 'Teaching, publishing, and wisdom-based career - higher learning and spiritual guidance',
            10: 'Exceptional career recognition and authority - leadership and public prominence',
            11: 'Network-based career with large-scale impact - social influence and group leadership',
            12: 'Behind-the-scenes or foreign-based career - international work and spiritual service'
        }
        return house_meanings.get(house_number, 'Career development through focused effort')
    
    def _get_d10_aspects(self, amatyakaraka, d10_chart):
        amk_d10_data = d10_chart['planets'][amatyakaraka]
        d10_asc_sign = int(d10_chart['ascendant'] / 30)
        amk_house = ((amk_d10_data['sign'] - d10_asc_sign) % 12) + 1
        aspects = []
        
        for planet, data in d10_chart['planets'].items():
            if planet != amatyakaraka:
                planet_house = ((data['sign'] - d10_asc_sign) % 12) + 1
                aspected_houses = self._get_aspect_houses(planet, planet_house)
                if amk_house in aspected_houses:
                    aspects.append(planet)
        
        return aspects
    
    def _interpret_amk_d10_position(self, amk_d10_data):
        house = amk_d10_data['house']
        
        house_meanings = {
            1: 'Strong personal brand and leadership in career',
            2: 'Career through resources, finance, and value creation',
            3: 'Communication, media, and skill-based career success',
            4: 'Stable, secure career with emotional satisfaction',
            5: 'Creative, speculative, and innovative career expression',
            6: 'Service-oriented career with competitive advantage',
            7: 'Partnership-based career and public relations',
            8: 'Transformative career involving research or hidden knowledge',
            9: 'Teaching, publishing, and wisdom-based career',
            10: 'Exceptional career recognition and authority',
            11: 'Network-based career with large-scale impact',
            12: 'Behind-the-scenes or foreign-based career success'
        }
        
        return house_meanings.get(house, 'Career development through focused effort')
    
    def _get_aspect_houses(self, planet, planet_house):
        """Get houses aspected by a planet from its position"""
        aspected = []
        
        # 7th aspect (all planets)
        seventh_house = ((planet_house - 1 + 6) % 12) + 1
        aspected.append(seventh_house)
        
        # Special aspects
        if planet == 'Mars':
            # Mars aspects 4th and 8th houses from its position
            fourth_house = ((planet_house - 1 + 3) % 12) + 1
            eighth_house = ((planet_house - 1 + 7) % 12) + 1
            aspected.extend([fourth_house, eighth_house])
        elif planet == 'Jupiter':
            # Jupiter aspects 5th and 9th houses from its position
            fifth_house = ((planet_house - 1 + 4) % 12) + 1
            ninth_house = ((planet_house - 1 + 8) % 12) + 1
            aspected.extend([fifth_house, ninth_house])
        elif planet == 'Saturn':
            # Saturn aspects 3rd and 10th houses from its position
            third_house = ((planet_house - 1 + 2) % 12) + 1
            tenth_house = ((planet_house - 1 + 9) % 12) + 1
            aspected.extend([third_house, tenth_house])
        
        return aspected