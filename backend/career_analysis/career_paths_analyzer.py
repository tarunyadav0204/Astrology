from calculators.planet_analyzer import PlanetAnalyzer
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from .conjunction_analyzer import ConjunctionAnalyzer

class CareerPathsAnalyzer:
    def __init__(self, chart_data):
        self.chart_data = chart_data
        self.planet_analyzer = PlanetAnalyzer(chart_data)
        self.yogi_calculator = YogiCalculator(chart_data)
        self.badhaka_calculator = BadhakaCalculator(chart_data)
        self.conjunction_analyzer = ConjunctionAnalyzer(chart_data)
        
        # Get D10 chart for career analysis
        self.d10_chart = chart_data['divisional_charts']['D10']
        
        # Include Rahu and Ketu in analysis
        self.all_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
    def analyze_career_fields(self):
        """Analyze top 3 career fields based on planetary positions"""
        fields = []
        
        # Get 10th house lord and planets
        tenth_house = self.chart_data['houses'][9]  # 10th house (0-indexed)
        tenth_lord = self.chart_data['house_lords'][9]
        
        # Analyze Sun for authority/leadership fields
        sun_analysis = self.planet_analyzer.analyze_planet('Sun')
        if sun_analysis['dignity'] in ['exalted', 'own_sign'] or sun_analysis['house'] in [1, 10]:
            fields.append({
                'field': 'Leadership & Administration',
                'reason': f"Sun in {sun_analysis['sign']} in {self._get_house_ordinal(sun_analysis['house'])} house shows natural authority and leadership abilities"
            })
        
        # Analyze Moon for caring/service fields
        moon_analysis = self.planet_analyzer.analyze_planet('Moon')
        if moon_analysis['dignity'] in ['exalted', 'own_sign'] or moon_analysis['house'] in [4, 12]:
            fields.append({
                'field': 'Healthcare & Counseling',
                'reason': f"Moon in {moon_analysis['sign']} in {self._get_house_ordinal(moon_analysis['house'])} house indicates nurturing nature and ability to care for others"
            })
        
        # Analyze Mercury for communication/education fields
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        if mercury_analysis['dignity'] in ['exalted', 'own_sign'] or mercury_analysis['house'] in [3, 5, 9]:
            fields.append({
                'field': 'Education & Communication',
                'reason': f"Mercury in {mercury_analysis['sign']} in {self._get_house_ordinal(mercury_analysis['house'])} house shows strong communication and teaching abilities"
            })
        
        # Analyze Venus for creative/artistic fields
        venus_analysis = self.planet_analyzer.analyze_planet('Venus')
        if venus_analysis['dignity'] in ['exalted', 'own_sign'] or venus_analysis['house'] in [2, 5, 7]:
            fields.append({
                'field': 'Creative Arts & Design',
                'reason': f"Venus in {venus_analysis['sign']} in {self._get_house_ordinal(venus_analysis['house'])} house indicates artistic talents and aesthetic sense"
            })
        
        # Analyze Ketu for spiritual/AI/research fields
        ketu_house = chart_data['planets']['Ketu']['house']
        ketu_sign = int(chart_data['planets']['Ketu']['longitude'] / 30)
        if ketu_house in [8, 9, 12] or ketu_sign in [7, 8, 11]:  # Scorpio, Sagittarius, Pisces
            fields.append({
                'field': 'AI & Spiritual Technology',
                'reason': f"Ketu in {self._get_house_ordinal(ketu_house)} house indicates past-life expertise in mystical sciences, now manifesting as AI and advanced technology"
            })
        
        # Analyze Rahu for innovative/foreign fields
        rahu_house = chart_data['planets']['Rahu']['house']
        rahu_sign = int(chart_data['planets']['Rahu']['longitude'] / 30)
        if rahu_house in [3, 6, 10, 11] or rahu_sign in [2, 5, 10]:  # Gemini, Virgo, Aquarius
            fields.append({
                'field': 'Innovation & Global Technology',
                'reason': f"Rahu in {self._get_house_ordinal(rahu_house)} house drives towards cutting-edge technology and international business"
            })
        
        # Analyze planetary conjunctions for specialized fields
        conjunctions = self.conjunction_analyzer.analyze_career_conjunctions()
        for conjunction in conjunctions:
            if conjunction['house'] in [1, 10, 11]:  # Career-relevant houses
                fields.append({
                    'field': conjunction['career_impact'],
                    'reason': conjunction['description']
                })
        
        # Analyze Mars for technical/engineering fields
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        if mars_analysis['dignity'] in ['exalted', 'own_sign'] or mars_analysis['house'] in [3, 6, 10]:
            fields.append({
                'field': 'Engineering & Technology',
                'reason': f"Mars in {mars_analysis['sign']} in {self._get_house_ordinal(mars_analysis['house'])} house shows technical aptitude and problem-solving skills"
            })
        
        # Analyze Jupiter for wisdom/advisory fields
        jupiter_analysis = self.planet_analyzer.analyze_planet('Jupiter')
        if jupiter_analysis['dignity'] in ['exalted', 'own_sign'] or jupiter_analysis['house'] in [5, 9, 11]:
            fields.append({
                'field': 'Finance & Advisory',
                'reason': f"Jupiter in {jupiter_analysis['sign']} in {self._get_house_ordinal(jupiter_analysis['house'])} house indicates wisdom and ability to guide others financially"
            })
        
        return fields[:3]  # Return top 3 fields
    
    def analyze_job_roles(self):
        """Analyze specific job roles based on planetary combinations"""
        roles = []
        
        # Get Atmakaraka for soul purpose
        atmakaraka = self._get_atmakaraka()
        
        if atmakaraka == 'Sun':
            roles.extend(['CEO/Director', 'Government Officer', 'Team Leader'])
        elif atmakaraka == 'Moon':
            roles.extend(['Therapist', 'Nurse', 'Social Worker'])
        elif atmakaraka == 'Mercury':
            roles.extend(['Teacher', 'Writer', 'Consultant'])
        elif atmakaraka == 'Venus':
            roles.extend(['Designer', 'Artist', 'Fashion Consultant'])
        elif atmakaraka == 'Mars':
            roles.extend(['Engineer', 'Surgeon', 'Project Manager'])
        elif atmakaraka == 'Jupiter':
            roles.extend(['Financial Advisor', 'Counselor', 'Judge'])
        elif atmakaraka == 'Saturn':
            roles.extend(['Researcher', 'Administrator', 'Quality Analyst'])
        elif atmakaraka == 'Rahu':
            roles.extend(['AI Engineer', 'International Business', 'Innovation Manager'])
        elif atmakaraka == 'Ketu':
            roles.extend(['AI Researcher', 'Spiritual Counselor', 'Data Scientist'])
        
        return roles[:3]  # Return top 3 roles
    
    def analyze_work_mode(self):
        """Analyze whether person should be employee or entrepreneur"""
        # Check Sun strength for leadership
        sun_analysis = self.planet_analyzer.analyze_planet('Sun')
        sun_score = self._calculate_planet_strength(sun_analysis)
        
        # Check Mars for initiative
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        mars_score = self._calculate_planet_strength(mars_analysis)
        
        # Check Saturn for discipline/structure
        saturn_analysis = self.planet_analyzer.analyze_planet('Saturn')
        saturn_score = self._calculate_planet_strength(saturn_analysis)
        
        # Check 10th house strength
        tenth_house_planets = [p for p in self.chart_data['planets'] if self.chart_data['planets'][p]['house'] == 10]
        tenth_house_strength = len(tenth_house_planets) * 10
        
        entrepreneur_score = sun_score + mars_score + tenth_house_strength
        employee_score = saturn_score + (100 - sun_score)
        
        if entrepreneur_score > employee_score:
            return {
                'mode': 'Entrepreneur',
                'confidence': min(entrepreneur_score, 100),
                'reason': f"Strong Sun (score: {sun_score}) and Mars (score: {mars_score}) indicate natural leadership and initiative for entrepreneurship"
            }
        else:
            return {
                'mode': 'Employee',
                'confidence': min(employee_score, 100),
                'reason': f"Strong Saturn (score: {saturn_score}) indicates preference for structured environments and steady growth as an employee"
            }
    
    def analyze_industries(self):
        """Analyze suitable industries based on elemental and planetary influences"""
        industries = []
        
        # Analyze dominant elements in chart
        fire_planets = ['Sun', 'Mars']
        earth_planets = ['Mercury', 'Saturn']
        air_planets = ['Venus', 'Saturn']  # Saturn also rules air
        water_planets = ['Moon', 'Venus']  # Venus also rules water
        
        fire_strength = sum(self._calculate_planet_strength(self.planet_analyzer.analyze_planet(p)) for p in fire_planets)
        earth_strength = sum(self._calculate_planet_strength(self.planet_analyzer.analyze_planet(p)) for p in earth_planets)
        water_strength = sum(self._calculate_planet_strength(self.planet_analyzer.analyze_planet(p)) for p in water_planets)
        
        if fire_strength > 120:
            industries.append({
                'industry': 'Energy & Manufacturing',
                'reason': f"Strong fire element (strength: {fire_strength}) indicates success in dynamic, high-energy industries"
            })
        
        if earth_strength > 120:
            industries.append({
                'industry': 'Real Estate & Agriculture',
                'reason': f"Strong earth element (strength: {earth_strength}) shows affinity for tangible, grounded industries"
            })
        
        if water_strength > 120:
            industries.append({
                'industry': 'Healthcare & Hospitality',
                'reason': f"Strong water element (strength: {water_strength}) indicates success in caring, service-oriented industries"
            })
        
        # Default to service industry if no strong elemental dominance
        if not industries:
            industries.append({
                'industry': 'Service & Consulting',
                'reason': "Balanced planetary influences suggest success in service-oriented industries where you can help others"
            })
        
        return industries[:2]  # Return top 2 industries
    
    def analyze_work_type(self):
        """Analyze whether person is suited for creative, technical, or service work"""
        # Analyze Venus for creativity
        venus_analysis = self.planet_analyzer.analyze_planet('Venus')
        creative_score = self._calculate_planet_strength(venus_analysis)
        
        # Analyze Mercury and Mars for technical work
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        technical_score = (self._calculate_planet_strength(mercury_analysis) + self._calculate_planet_strength(mars_analysis)) / 2
        
        # Analyze Moon and Jupiter for service work
        moon_analysis = self.planet_analyzer.analyze_planet('Moon')
        jupiter_analysis = self.planet_analyzer.analyze_planet('Jupiter')
        service_score = (self._calculate_planet_strength(moon_analysis) + self._calculate_planet_strength(jupiter_analysis)) / 2
        
        scores = {
            'Creative': creative_score,
            'Technical': technical_score,
            'Service': service_score
        }
        
        primary_type = max(scores, key=scores.get)
        
        return {
            'primary_type': primary_type,
            'scores': scores,
            'reason': self._get_work_type_reason(primary_type, scores[primary_type])
        }
    
    def analyze_avoid_careers(self):
        """Analyze career fields to avoid based on planetary weaknesses"""
        avoid = []
        
        # Check for weak planets that might indicate unsuitable careers
        sun_analysis = self.planet_analyzer.analyze_planet('Sun')
        if sun_analysis['dignity'] in ['debilitated', 'enemy_sign']:
            avoid.append("High-pressure leadership roles requiring constant authority")
        
        mercury_analysis = self.planet_analyzer.analyze_planet('Mercury')
        if mercury_analysis['dignity'] in ['debilitated', 'enemy_sign']:
            avoid.append("Roles requiring extensive writing or complex communication")
        
        mars_analysis = self.planet_analyzer.analyze_planet('Mars')
        if mars_analysis['dignity'] in ['debilitated', 'enemy_sign']:
            avoid.append("High-stress technical roles or competitive environments")
        
        return avoid[:2]  # Return top 2 things to avoid
    
    def _get_atmakaraka(self):
        """Get the Atmakaraka (planet with highest degree)"""
        max_degree = 0
        atmakaraka = 'Sun'
        
        for planet, data in self.chart_data['planets'].items():
            if planet in ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu']:
                degree = data['degree']
                if degree > max_degree:
                    max_degree = degree
                    atmakaraka = planet
        
        return atmakaraka
    
    def _calculate_planet_strength(self, planet_analysis):
        """Calculate overall strength score for a planet"""
        score = 50  # Base score
        
        if planet_analysis['dignity'] == 'exalted':
            score += 30
        elif planet_analysis['dignity'] == 'own_sign':
            score += 20
        elif planet_analysis['dignity'] == 'friend_sign':
            score += 10
        elif planet_analysis['dignity'] == 'enemy_sign':
            score -= 10
        elif planet_analysis['dignity'] == 'debilitated':
            score -= 30
        
        # House placement bonus
        if planet_analysis['house'] in [1, 4, 7, 10]:  # Kendra houses
            score += 15
        elif planet_analysis['house'] in [5, 9]:  # Trikona houses
            score += 10
        
        return max(0, min(100, score))
    
    def _get_house_ordinal(self, house_num):
        """Convert house number to ordinal string"""
        ordinals = {
            1: '1st', 2: '2nd', 3: '3rd', 4: '4th', 5: '5th', 6: '6th',
            7: '7th', 8: '8th', 9: '9th', 10: '10th', 11: '11th', 12: '12th'
        }
        return ordinals.get(house_num, f'{house_num}th')
    
    def _get_work_type_reason(self, work_type, score):
        """Get reason for work type preference"""
        if work_type == 'Creative':
            return f"Strong Venus influence (score: {score:.0f}) indicates natural artistic abilities and aesthetic sense"
        elif work_type == 'Technical':
            return f"Strong Mercury-Mars combination (score: {score:.0f}) shows analytical thinking and problem-solving skills"
        else:  # Service
            return f"Strong Moon-Jupiter combination (score: {score:.0f}) indicates natural inclination to help and guide others"