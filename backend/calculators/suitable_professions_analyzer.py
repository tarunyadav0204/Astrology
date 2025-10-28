from .base_calculator import BaseCalculator
from .profession_config import *

class SuitableProfessionsAnalyzer(BaseCalculator):
    """Professional-grade career analysis using comprehensive Vedic principles"""
    
    def __init__(self, chart_data, birth_data):
        super().__init__(chart_data)
        if not birth_data:
            raise ValueError("Birth data required for professional career analysis")
        
        # Initialize calculators
        from .shadbala_calculator import ShadbalaCalculator
        from .planetary_dignities_calculator import PlanetaryDignitiesCalculator
        from .nakshatra_calculator import NakshatraCalculator
        
        self.shadbala_calc = ShadbalaCalculator(chart_data)
        self.dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        self.nakshatra_calc = NakshatraCalculator(None, chart_data)
        
        # Get real data - no fallbacks
        self.shadbala_data = self.shadbala_calc.calculate_shadbala()
        self.dignities_data = self.dignities_calc.calculate_planetary_dignities()
        self.nakshatra_data = self.nakshatra_calc.calculate_nakshatra_positions()
    
    def analyze_suitable_professions(self):
        """Professional comprehensive career analysis"""
        # 1. Planetary Situation Overview
        tenth_lord_analysis = self._analyze_tenth_lord_situation()
        
        # 2. Nature of Work Analysis
        nature_of_work = self._analyze_nature_of_work(tenth_lord_analysis)
        
        # 3. Domain of Work Analysis
        domain_of_work = self._analyze_domain_of_work(tenth_lord_analysis)
        
        return {
            'nature_of_work': nature_of_work,
            'domain_of_work': domain_of_work
        }
    
    def _analyze_nature_of_work(self, tenth_lord_analysis):
        """Generate meaningful career guidance"""
        tenth_lord = tenth_lord_analysis['tenth_lord']
        tenth_lord_sign = tenth_lord_analysis['sign_name']
        tenth_lord_house = tenth_lord_analysis['house_placement']
        tenth_lord_nakshatra = tenth_lord_analysis['nakshatra']
        
        # Get conjunct planets
        conjunct_planets = []
        for planet, data in self.chart_data['planets'].items():
            if planet != tenth_lord and data['house'] == tenth_lord_house:
                conjunct_planets.append(planet)
        
        # Generate human-readable career guidance
        career_summary = self._generate_career_summary(tenth_lord, tenth_lord_sign, conjunct_planets)
        specific_roles = self._get_specific_job_roles(tenth_lord, tenth_lord_sign, conjunct_planets)
        astrological_reasoning = self._explain_astrological_logic(tenth_lord, tenth_lord_sign, tenth_lord_house, tenth_lord_nakshatra, conjunct_planets)
        
        return {
            'career_summary': career_summary,
            'recommended_roles': specific_roles,
            'astrological_reasoning': astrological_reasoning,
            'key_strengths': self._identify_key_strengths(tenth_lord, tenth_lord_sign, conjunct_planets),
            'work_environment': self._describe_ideal_work_environment(tenth_lord, tenth_lord_sign, conjunct_planets)
        }
    
    def _generate_career_summary(self, tenth_lord, sign, conjunctions):
        """Generate clear career summary"""
        base_nature = PLANETARY_WORK_NATURE[tenth_lord][0]
        sign_element = SIGN_ELEMENTS[sign]
        sign_nature = ELEMENT_WORK_NATURES[sign_element]
        
        # Create meaningful combination
        if base_nature == sign_nature:
            primary_style = f"{base_nature} with {SIGN_WORK_INFLUENCE[sign]['modifies']}"
        else:
            primary_style = f"{base_nature} combined with {sign_nature} tendencies"
        
        # Add conjunction influence
        if conjunctions:
            conjunction_effects = []
            for planet in conjunctions:
                conjunction_effects.append(CONJUNCTION_WORK_EFFECTS[planet]['effect'])
            
            conjunction_summary = f" Your career is further influenced by {', '.join(conjunctions)} which {', '.join(conjunction_effects)}."
        else:
            conjunction_summary = ""
        
        return f"You are naturally suited for {primary_style}.{conjunction_summary}"
    
    def _get_specific_job_roles(self, tenth_lord, sign, conjunctions):
        """Get specific job recommendations"""
        # Base roles from planet
        base_roles = PLANETARY_DOMAINS[tenth_lord]['modern'][:3]
        traditional_roles = PLANETARY_DOMAINS[tenth_lord]['traditional'][:3]
        
        # Check for special combinations
        combination_roles = []
        for planet in conjunctions:
            combo_key = tuple(sorted([tenth_lord, planet]))
            if combo_key in AI_CS_COMBINATIONS:
                combination_roles.extend(AI_CS_COMBINATIONS[combo_key]['fields'][:2])
        
        # Sign-specific modifications
        sign_modifier = SIGN_WORK_INFLUENCE[sign]['modifies']
        
        return {
            'primary_recommendations': base_roles,
            'traditional_options': traditional_roles,
            'specialized_combinations': combination_roles if combination_roles else None,
            'approach_style': sign_modifier
        }
    
    def _explain_astrological_logic(self, tenth_lord, sign, house, nakshatra, conjunctions):
        """Explain the astrological reasoning"""
        explanations = []
        
        # 10th lord explanation
        explanations.append(f"Your 10th lord is {tenth_lord}, which governs {', '.join(PLANETARY_DOMAINS[tenth_lord]['traditional'][:2])} indicating natural aptitude for {PLANETARY_WORK_NATURE[tenth_lord][0]} roles.")
        
        # Sign placement
        explanations.append(f"{tenth_lord} in {sign} adds {SIGN_WORK_INFLUENCE[sign]['modifies']} to your professional approach.")
        
        # House placement
        house_context = HOUSE_WORK_INFLUENCE[house]['context']
        explanations.append(f"Placed in the {house}th house, your career becomes about {house_context}.")
        
        # Nakshatra influence
        nakshatra_nature = NAKSHATRA_WORK_NATURE[nakshatra]
        explanations.append(f"Your {nakshatra} nakshatra adds {nakshatra_nature} qualities to your work style.")
        
        # Conjunctions
        if conjunctions:
            for planet in conjunctions:
                effect = CONJUNCTION_WORK_EFFECTS[planet]['effect']
                explanations.append(f"{planet} conjunction {effect}.")
        
        return explanations
    
    def _identify_key_strengths(self, tenth_lord, sign, conjunctions):
        """Identify key professional strengths"""
        strengths = []
        
        # Planetary strengths
        if tenth_lord == 'Venus':
            strengths.extend(['Aesthetic sense', 'Creative vision', 'Harmony in teams'])
        elif tenth_lord == 'Mars':
            strengths.extend(['Problem-solving', 'Technical skills', 'Action-oriented approach'])
        elif tenth_lord == 'Mercury':
            strengths.extend(['Analytical thinking', 'Communication', 'Process optimization'])
        elif tenth_lord == 'Jupiter':
            strengths.extend(['Strategic thinking', 'Teaching ability', 'Ethical leadership'])
        elif tenth_lord == 'Saturn':
            strengths.extend(['Systematic approach', 'Long-term planning', 'Quality focus'])
        elif tenth_lord == 'Sun':
            strengths.extend(['Natural authority', 'Vision setting', 'Team leadership'])
        elif tenth_lord == 'Moon':
            strengths.extend(['Emotional intelligence', 'Public connection', 'Nurturing teams'])
        
        # Sign modifications
        if sign in ['Leo', 'Aries', 'Sagittarius']:
            strengths.append('Natural leadership presence')
        elif sign in ['Virgo', 'Capricorn', 'Taurus']:
            strengths.append('Attention to detail and quality')
        elif sign in ['Gemini', 'Libra', 'Aquarius']:
            strengths.append('Innovation and creative thinking')
        elif sign in ['Cancer', 'Scorpio', 'Pisces']:
            strengths.append('Intuitive understanding of people')
        
        return strengths[:5]  # Return top 5 strengths
    
    def _describe_ideal_work_environment(self, tenth_lord, sign, conjunctions):
        """Describe ideal work environment"""
        environment_factors = []
        
        # Based on planet
        if tenth_lord == 'Venus':
            environment_factors.append('aesthetically pleasing workspace')
        elif tenth_lord == 'Mars':
            environment_factors.append('dynamic, fast-paced environment')
        elif tenth_lord == 'Saturn':
            environment_factors.append('structured, organized workplace')
        elif tenth_lord == 'Jupiter':
            environment_factors.append('growth-oriented, learning environment')
        elif tenth_lord == 'Mercury':
            environment_factors.append('intellectually stimulating atmosphere')
        
        # Based on sign
        if sign in ['Leo', 'Aries']:
            environment_factors.append('where you can take initiative and lead')
        elif sign in ['Virgo', 'Capricorn']:
            environment_factors.append('with clear processes and quality standards')
        elif sign in ['Gemini', 'Aquarius']:
            environment_factors.append('with variety and intellectual challenges')
        elif sign in ['Cancer', 'Pisces']:
            environment_factors.append('with supportive team dynamics')
        
        return f"You thrive in {', '.join(environment_factors)}."
    
    def _analyze_domain_of_work(self, tenth_lord_analysis):
        """Analyze specific industry domains with actionable career guidance"""
        # Get 2nd lord for wealth source domain
        second_lord_analysis = self._analyze_second_lord_situation()
        
        # Primary domain analysis
        domain_analysis = self._get_comprehensive_domain_analysis(second_lord_analysis, tenth_lord_analysis)
        
        return domain_analysis
    
    def _analyze_second_lord_situation(self):
        """Analyze 2nd lord for wealth source domain"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        second_house_sign = (ascendant_sign + 1) % 12
        second_lord = self.get_sign_lord(second_house_sign)
        second_lord_house = self.chart_data['planets'][second_lord]['house']
        second_lord_sign = self.chart_data['planets'][second_lord]['sign']
        second_lord_nakshatra = self.nakshatra_data[second_lord]['nakshatra_name']
        
        return {
            'second_lord': second_lord,
            'house_placement': second_lord_house,
            'sign_name': self.SIGN_NAMES[second_lord_sign],
            'nakshatra': second_lord_nakshatra
        }
    
    def _analyze_eleventh_lord_situation(self):
        """Analyze 11th lord for gains domain"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        eleventh_house_sign = (ascendant_sign + 10) % 12
        eleventh_lord = self.get_sign_lord(eleventh_house_sign)
        eleventh_lord_house = self.chart_data['planets'][eleventh_lord]['house']
        eleventh_lord_sign = self.chart_data['planets'][eleventh_lord]['sign']
        eleventh_lord_nakshatra = self.nakshatra_data[eleventh_lord]['nakshatra_name']
        
        return {
            'eleventh_lord': eleventh_lord,
            'house_placement': eleventh_lord_house,
            'sign_name': self.SIGN_NAMES[eleventh_lord_sign],
            'nakshatra': eleventh_lord_nakshatra
        }
    
    def _get_comprehensive_domain_analysis(self, second_lord_analysis, tenth_lord_analysis):
        """Get actionable domain analysis with specific career guidance"""
        second_lord = second_lord_analysis['second_lord']
        house_placement = second_lord_analysis['house_placement']
        tenth_lord = tenth_lord_analysis['tenth_lord']
        
        # Comprehensive domain mapping with actionable details
        domain_details = {
            ('Mercury', 11): {
                'primary_domain': 'Technology & Communication',
                'industries': ['Software Development', 'Digital Marketing', 'EdTech', 'Fintech', 'Media Technology'],
                'specific_roles': ['Product Manager', 'Technical Writer', 'Developer Relations', 'Solutions Architect', 'Data Analyst'],
                'company_types': ['Tech Startups', 'Fortune 500 Tech', 'Government Contractors', 'Consulting Firms'],

                'growth_potential': 'High - 13% annual growth in tech sector',
                'key_skills': ['Technical Communication', 'Project Management', 'Data Analysis', 'Problem Solving'],
                'specialization': 'Technology Communication & Networks'
            },
            ('Mercury', 3): {
                'primary_domain': 'Media & Digital Communication',
                'industries': ['Digital Media', 'Content Marketing', 'Publishing', 'Broadcasting', 'Social Media'],
                'specific_roles': ['Content Strategist', 'Digital Marketing Manager', 'Technical Writer', 'Media Producer'],
                'company_types': ['Media Companies', 'Marketing Agencies', 'Publishing Houses', 'Tech Companies'],
                'salary_range': '$55,000 - $95,000',
                'growth_potential': 'Moderate - 8% growth in digital media',
                'key_skills': ['Content Creation', 'Digital Marketing', 'Analytics', 'Communication'],
                'specialization': 'Digital Content & Communication'
            },
            ('Venus', 5): {
                'primary_domain': 'Creative Arts & Entertainment',
                'industries': ['Entertainment', 'Design', 'Fashion', 'Gaming', 'Creative Technology'],
                'specific_roles': ['UX/UI Designer', 'Creative Director', 'Game Designer', 'Brand Manager'],
                'company_types': ['Creative Agencies', 'Entertainment Studios', 'Tech Companies', 'Fashion Brands'],

                'growth_potential': 'High - 10% growth in creative industries',
                'key_skills': ['Design Thinking', 'Creative Software', 'Brand Strategy', 'User Experience'],
                'specialization': 'Creative Design & Entertainment'
            },
            ('Mars', 6): {
                'primary_domain': 'Engineering & Healthcare Technology',
                'industries': ['Healthcare Technology', 'Biomedical Engineering', 'Medical Devices', 'Health IT'],
                'specific_roles': ['Biomedical Engineer', 'Health IT Specialist', 'Medical Device Developer', 'Healthcare Analyst'],
                'company_types': ['Healthcare Companies', 'Medical Device Manufacturers', 'Health Tech Startups'],

                'growth_potential': 'Very High - 15% growth in health tech',
                'key_skills': ['Technical Problem Solving', 'Healthcare Knowledge', 'Engineering Design', 'Regulatory Compliance'],
                'specialization': 'Healthcare Engineering & Technology'
            },
            ('Jupiter', 9): {
                'primary_domain': 'Education & Legal Technology',
                'industries': ['EdTech', 'Legal Technology', 'Corporate Training', 'Educational Services'],
                'specific_roles': ['Learning Experience Designer', 'Legal Tech Consultant', 'Training Manager', 'Educational Technologist'],
                'company_types': ['EdTech Companies', 'Law Firms', 'Corporate Training', 'Educational Institutions'],

                'growth_potential': 'High - 12% growth in EdTech',
                'key_skills': ['Instructional Design', 'Legal Knowledge', 'Technology Integration', 'Project Management'],
                'specialization': 'Educational & Legal Technology'
            },
            ('Saturn', 10): {
                'primary_domain': 'Government & Enterprise Technology',
                'industries': ['Government Technology', 'Enterprise Software', 'Cybersecurity', 'Infrastructure'],
                'specific_roles': ['Systems Administrator', 'Cybersecurity Analyst', 'Government IT Specialist', 'Enterprise Architect'],
                'company_types': ['Government Agencies', 'Defense Contractors', 'Enterprise Software Companies'],

                'growth_potential': 'Stable - 7% growth in government tech',
                'key_skills': ['Systems Management', 'Security Protocols', 'Compliance', 'Infrastructure Design'],
                'specialization': 'Government & Enterprise Systems'
            }
        }
        
        # Primary domain based on 10th lord (career), not 2nd lord (wealth)
        details = self._get_domain_by_signification(tenth_lord, tenth_lord_analysis['house_placement'], domain_details)
        
        # Add modern applications based on conjunctions
        modern_apps = self._get_modern_applications(tenth_lord_analysis)
        
        return {
            'primary_domain': details['primary_domain'],
            'industries': details['industries'],
            'specific_roles': details['specific_roles'],
            'company_types': details['company_types'],
            'key_skills': details['key_skills'],
            'specialization': details['specialization'],
            'modern_applications': modern_apps,
            'career_guidance': self._generate_career_guidance(details, second_lord_analysis),
            'astrological_analysis': self._generate_domain_analysis(tenth_lord_analysis, second_lord_analysis, details)
        }
    
    def _get_modern_applications(self, tenth_lord_analysis):
        """Get modern technology applications"""
        tenth_lord = tenth_lord_analysis['tenth_lord']
        conjunct_planets = []
        
        for planet, data in self.chart_data['planets'].items():
            if planet != tenth_lord and data['house'] == tenth_lord_analysis['house_placement']:
                conjunct_planets.append(planet)
        
        modern_apps = []
        
        # Technology combinations
        if 'Mercury' in [tenth_lord] + conjunct_planets:
            if 'Venus' in [tenth_lord] + conjunct_planets:
                modern_apps.append('Digital Design & UX')
            if 'Mars' in [tenth_lord] + conjunct_planets:
                modern_apps.append('Software Engineering')
            if 'Jupiter' in [tenth_lord] + conjunct_planets:
                modern_apps.append('EdTech & Legal Tech')
        
        return modern_apps[:2]
    
    def _generate_career_guidance(self, details, second_lord_analysis):
        """Generate enhanced actionable career guidance with astrological reasoning"""
        guidance = []
        
        # Industry focus with reasoning
        top_industries = details['industries'][:3]
        guidance.append(f"Prioritize {', '.join(top_industries)} industries as your planetary combination creates natural success in these sectors")
        
        # Role recommendations with approach
        top_roles = details['specific_roles'][:3]
        guidance.append(f"Target {', '.join(top_roles)} roles where your astrological strengths will be most valued")
        
        # Skills development with planetary backing
        key_skills = details['key_skills'][:3]
        guidance.append(f"Focus skill development on {', '.join(key_skills)} as these align with your natural planetary abilities")
        
        # Company targeting with cultural fit
        company_types = details['company_types'][:2]
        guidance.append(f"Seek opportunities in {', '.join(company_types)} where your planetary combination indicates best cultural and professional fit")
        
        # Add specific wealth strategy based on 2nd lord
        wealth_strategy = self._get_wealth_strategy(second_lord_analysis)
        guidance.append(wealth_strategy)
        
        return guidance
    
    def _get_wealth_strategy(self, second_lord_analysis):
        """Generate specific wealth strategy based on 2nd lord placement"""
        second_lord = second_lord_analysis['second_lord']
        second_house = second_lord_analysis['house_placement']
        
        # Wealth strategies based on 2nd lord and house
        wealth_strategies = {
            ('Sun', 9): 'Build wealth through government positions, higher education, or international business ventures',
            ('Sun', 10): 'Accumulate wealth through leadership roles, government service, or authoritative positions',
            ('Sun', 11): 'Generate income through large organizations, networking, or government connections',
            ('Moon', 4): 'Build wealth through real estate, property development, or homeland-based businesses',
            ('Moon', 6): 'Earn through healthcare services, hospitality, or public-facing service roles',
            ('Moon', 11): 'Generate income through public relations, networking, or community-based businesses',
            ('Mercury', 3): 'Build wealth through communication, media, writing, or short-distance business ventures',
            ('Mercury', 11): 'Accumulate wealth through technology networks, large-scale communication, or tech consulting',
            ('Mercury', 9): 'Generate income through publishing, education, or international communication business',
            ('Venus', 5): 'Build wealth through creative work, entertainment, speculation, or luxury goods',
            ('Venus', 7): 'Earn through partnerships, luxury services, or beauty/fashion businesses',
            ('Venus', 11): 'Generate income through creative networks, entertainment industry, or luxury markets',
            ('Mars', 2): 'Build wealth through family business, engineering ventures, or technical financial services',
            ('Mars', 6): 'Accumulate wealth through healthcare technology, service industries, or competitive fields',
            ('Mars', 11): 'Generate income through technology networks, engineering consulting, or large-scale projects',
            ('Jupiter', 9): 'Build wealth through education, legal services, publishing, or international consulting',
            ('Jupiter', 11): 'Earn through educational networks, financial consulting, or wisdom-based large organizations',
            ('Jupiter', 5): 'Generate income through teaching, creative education, or speculative wisdom-based ventures',
            ('Saturn', 10): 'Build wealth through systematic career progression, manufacturing, or structured organizations',
            ('Saturn', 11): 'Accumulate wealth through disciplined networking, organized systems, or long-term investments',
            ('Saturn', 4): 'Generate income through real estate, construction, or property-based systematic businesses'
        }
        
        # Get specific strategy or create general one
        key = (second_lord, second_house)
        if key in wealth_strategies:
            return wealth_strategies[key]
        else:
            # General strategy based on 2nd lord
            planet_wealth_focus = {
                'Sun': 'leadership and authoritative positions',
                'Moon': 'public-facing and nurturing services',
                'Mercury': 'communication and analytical work',
                'Venus': 'creative and luxury-oriented ventures',
                'Mars': 'technical and competitive fields',
                'Jupiter': 'educational and consulting services',
                'Saturn': 'systematic and long-term investments'
            }
            
            focus = planet_wealth_focus.get(second_lord, 'your natural talents')
            return f'Build wealth by focusing on {focus} and leveraging your {second_house}th house placement for income generation'
    
    def _generate_domain_analysis(self, tenth_lord_analysis, second_lord_analysis, details):
        """Generate comprehensive astrological reasoning with conjunctions and house flavors"""
        tenth_lord = tenth_lord_analysis['tenth_lord']
        tenth_house = tenth_lord_analysis['house_placement']
        
        # Get conjunct planets
        conjunct_planets = []
        for planet, data in self.chart_data['planets'].items():
            if planet != tenth_lord and data['house'] == tenth_house:
                conjunct_planets.append(planet)
        
        # Enhanced analysis with conjunctions and house flavors
        primary_domain_why = self._get_enhanced_domain_explanation(tenth_lord, tenth_house, conjunct_planets, details)
        conjunction_effects = self._get_conjunction_effects(tenth_lord, conjunct_planets)
        house_flavor = self._get_house_domain_flavor(tenth_house, details['primary_domain'])
        
        # Enhanced industries explanation
        industries_why = self._get_enhanced_industries_explanation(tenth_lord, tenth_house, conjunct_planets, details, house_flavor)
        
        # Enhanced roles explanation
        roles_why = self._get_enhanced_roles_explanation(tenth_lord, tenth_house, conjunct_planets, details)
        
        # Enhanced companies explanation
        companies_why = self._get_enhanced_companies_explanation(tenth_lord, tenth_house, conjunct_planets, details)
        
        # Enhanced skills explanation
        skills_why = self._get_enhanced_skills_explanation(tenth_lord, tenth_house, conjunct_planets, details)
        
        analysis = {
            'primary_domain_why': primary_domain_why,
            'industries_why': industries_why,
            'roles_why': roles_why,
            'companies_why': companies_why,
            'skills_why': skills_why
        }
        
        return analysis
    
    def _get_enhanced_domain_explanation(self, tenth_lord, tenth_house, conjunct_planets, details):
        """Generate enhanced domain explanation with conjunctions"""
        planet_significations = {
            'Sun': 'government, authority, leadership, public service',
            'Moon': 'public relations, hospitality, healthcare, nurturing services', 
            'Mercury': 'communication, technology, analysis, commerce',
            'Venus': 'arts, entertainment, luxury, beauty, design',
            'Mars': 'engineering, technology, sports, defense, surgery',
            'Jupiter': 'education, law, finance, consulting, wisdom',
            'Saturn': 'organization, structure, manufacturing, real estate',
            'Rahu': 'innovation, foreign technology, unconventional methods',
            'Ketu': 'research, spirituality, behind-the-scenes work'
        }
        
        house_significations = {
            1: 'personal efforts and self-employment',
            2: 'family business and accumulated wealth', 
            3: 'communication, media, and short travels',
            4: 'real estate, vehicles, and homeland',
            5: 'creativity, speculation, and entertainment',
            6: 'service, health sector, and daily work',
            7: 'partnerships and foreign connections',
            8: 'research, occult, and transformation',
            9: 'higher learning, publishing, and foreign lands',
            10: 'career reputation and government',
            11: 'networks, technology, and large organizations',
            12: 'foreign lands, spirituality, and behind-scenes work'
        }
        
        base_explanation = f"Your 10th lord {tenth_lord} governs {planet_significations[tenth_lord]}, placed in {tenth_house}th house ({house_significations[tenth_house]})"
        
        if conjunct_planets:
            conjunction_details = []
            for planet in conjunct_planets:
                if planet in planet_significations:
                    conjunction_details.append(f"{planet} adds {self._get_conjunction_flavor(planet, details['primary_domain'])}")
            
            if conjunction_details:
                base_explanation += f". {', '.join(conjunction_details)}."
        
        base_explanation += f" This combination indicates your primary career domain is {details['primary_domain']}."
        
        return base_explanation
    
    def _get_conjunction_flavor(self, planet, domain):
        """Get specific conjunction effects based on domain"""
        conjunction_flavors = {
            'Rahu': {
                'Engineering & Technology': 'technical innovation and cutting-edge solutions',
                'Government & Public Service': 'unconventional administrative approaches',
                'Technology & Communication': 'disruptive technology and digital innovation',
                'Creative Arts & Entertainment': 'unique creative expression and viral content',
                'Healthcare & Public Relations': 'innovative healthcare solutions',
                'Education & Legal Services': 'modern teaching methods and legal technology',
                'Organization & Structure': 'innovative organizational systems'
            },
            'Jupiter': {
                'Engineering & Technology': 'teaching and mentoring in technical fields',
                'Government & Public Service': 'ethical leadership and policy guidance',
                'Technology & Communication': 'educational technology and knowledge sharing',
                'Creative Arts & Entertainment': 'meaningful content and cultural impact',
                'Healthcare & Public Relations': 'holistic healthcare and wellness education',
                'Education & Legal Services': 'advanced education and legal wisdom',
                'Organization & Structure': 'strategic planning and organizational wisdom'
            },
            'Saturn': {
                'Engineering & Technology': 'systematic engineering and quality control',
                'Government & Public Service': 'structured administration and long-term planning',
                'Technology & Communication': 'reliable systems and enterprise solutions',
                'Creative Arts & Entertainment': 'disciplined creative work and lasting impact',
                'Healthcare & Public Relations': 'systematic healthcare delivery',
                'Education & Legal Services': 'traditional education and established legal practice',
                'Organization & Structure': 'enhanced organizational discipline'
            },
            'Mercury': {
                'Engineering & Technology': 'communication in technical fields',
                'Government & Public Service': 'policy communication and documentation',
                'Technology & Communication': 'enhanced technical communication',
                'Creative Arts & Entertainment': 'content creation and media production',
                'Healthcare & Public Relations': 'health communication and medical writing',
                'Education & Legal Services': 'educational content and legal documentation',
                'Organization & Structure': 'process documentation and communication'
            },
            'Venus': {
                'Engineering & Technology': 'aesthetic design in technology',
                'Government & Public Service': 'diplomatic and harmonious leadership',
                'Technology & Communication': 'user experience and design thinking',
                'Creative Arts & Entertainment': 'enhanced creative abilities',
                'Healthcare & Public Relations': 'compassionate care and beautiful environments',
                'Education & Legal Services': 'attractive presentation and harmonious teaching',
                'Organization & Structure': 'beautiful and harmonious work environments'
            },
            'Mars': {
                'Engineering & Technology': 'dynamic technical execution',
                'Government & Public Service': 'decisive leadership and action-oriented governance',
                'Technology & Communication': 'fast-paced technical development',
                'Creative Arts & Entertainment': 'energetic and competitive creative work',
                'Healthcare & Public Relations': 'emergency healthcare and crisis management',
                'Education & Legal Services': 'competitive education and aggressive legal practice',
                'Organization & Structure': 'dynamic organizational change'
            },
            'Sun': {
                'Engineering & Technology': 'leadership in technical teams',
                'Government & Public Service': 'enhanced governmental authority',
                'Technology & Communication': 'authoritative technical leadership',
                'Creative Arts & Entertainment': 'celebrity status and recognition',
                'Healthcare & Public Relations': 'leadership in healthcare organizations',
                'Education & Legal Services': 'authoritative teaching and legal leadership',
                'Organization & Structure': 'executive leadership and organizational authority'
            },
            'Moon': {
                'Engineering & Technology': 'intuitive technical solutions',
                'Government & Public Service': 'public-oriented governance and emotional intelligence',
                'Technology & Communication': 'user-centric technology and emotional design',
                'Creative Arts & Entertainment': 'emotionally resonant creative work',
                'Healthcare & Public Relations': 'nurturing healthcare and empathetic communication',
                'Education & Legal Services': 'nurturing education and compassionate legal practice',
                'Organization & Structure': 'caring organizational culture'
            }
        }
        
        return conjunction_flavors.get(planet, {}).get(domain, f'{planet.lower()} influence')
    
    def _get_conjunction_effects(self, tenth_lord, conjunct_planets):
        """Get conjunction effects for roles"""
        if not conjunct_planets:
            return ""
        
        effects = []
        for planet in conjunct_planets:
            if planet == 'Jupiter':
                effects.append("with teaching and mentoring capabilities")
            elif planet == 'Saturn':
                effects.append("with systematic and disciplined approach")
            elif planet == 'Rahu':
                effects.append("with innovative and unconventional methods")
            elif planet == 'Mercury':
                effects.append("with strong communication skills")
            elif planet == 'Venus':
                effects.append("with aesthetic and harmonious approach")
        
        return f" {', '.join(effects)}" if effects else ""
    
    def _get_house_domain_flavor(self, house, domain):
        """Get house-specific domain flavors"""
        house_flavors = {
            2: "with focus on financial applications and wealth generation",
            3: "with emphasis on communication and media aspects", 
            4: "with connection to real estate and homeland security",
            5: "with creative and speculative elements",
            6: "with service orientation and daily work applications",
            7: "with partnership and international business focus",
            8: "with research and transformation aspects",
            9: "with higher education and international elements",
            10: "with government and reputation building focus",
            11: "with networking and large organization emphasis",
            12: "with foreign connections and behind-the-scenes work"
        }
        
        return house_flavors.get(house, "")
    
    def _get_enhanced_industries_explanation(self, tenth_lord, tenth_house, conjunct_planets, details, house_flavor):
        """Generate detailed industries explanation similar to primary domain"""
        planet_significations = {
            'Sun': 'government, authority, leadership, public service',
            'Moon': 'public relations, hospitality, healthcare, nurturing services', 
            'Mercury': 'communication, technology, analysis, commerce',
            'Venus': 'arts, entertainment, luxury, beauty, design',
            'Mars': 'engineering, technology, sports, defense, surgery',
            'Jupiter': 'education, law, finance, consulting, wisdom',
            'Saturn': 'organization, structure, manufacturing, real estate',
            'Rahu': 'innovation, foreign technology, unconventional methods',
            'Ketu': 'research, spirituality, behind-the-scenes work'
        }
        
        house_significations = {
            1: 'personal efforts and self-employment',
            2: 'family business and accumulated wealth', 
            3: 'communication, media, and short travels',
            4: 'real estate, vehicles, and homeland',
            5: 'creativity, speculation, and entertainment',
            6: 'service, health sector, and daily work',
            7: 'partnerships and foreign connections',
            8: 'research, occult, and transformation',
            9: 'higher learning, publishing, and foreign lands',
            10: 'career reputation and government',
            11: 'networks, technology, and large organizations',
            12: 'foreign lands, spirituality, and behind-scenes work'
        }
        
        base_industries = ', '.join(details['industries'][:2])
        base_explanation = f"Your 10th lord {tenth_lord} ({planet_significations[tenth_lord]}) in {tenth_house}th house ({house_significations[tenth_house]}) creates natural affinity for {base_industries} industries"
        
        if conjunct_planets:
            conjunction_details = []
            for planet in conjunct_planets:
                if planet in planet_significations:
                    industry_effect = self._get_industry_conjunction_effect(planet, details['industries'])
                    if industry_effect:
                        conjunction_details.append(f"{planet} expands this into {industry_effect}")
            
            if conjunction_details:
                base_explanation += f". {', '.join(conjunction_details)}."
        
        if house_flavor:
            base_explanation += f" The {tenth_house}th house placement specifically emphasizes {house_flavor.replace('with ', '')}."
        
        return base_explanation
    
    def _get_industry_conjunction_effect(self, planet, industries):
        """Get how conjunctions affect specific industries"""
        industry_effects = {
            'Rahu': {
                'Engineering': 'cutting-edge engineering and robotics',
                'Technology': 'disruptive technology and AI',
                'Defense': 'advanced defense systems',
                'Fintech': 'cryptocurrency and blockchain',
                'Healthcare': 'medical technology innovation'
            },
            'Jupiter': {
                'Engineering': 'educational engineering and training',
                'Technology': 'EdTech and knowledge platforms',
                'Finance': 'ethical finance and consulting',
                'Legal Services': 'legal education and policy',
                'Healthcare': 'holistic healthcare and wellness'
            },
            'Saturn': {
                'Engineering': 'infrastructure and heavy engineering',
                'Technology': 'enterprise and legacy systems',
                'Manufacturing': 'quality manufacturing and production',
                'Real Estate': 'construction and property development',
                'Government Services': 'systematic administration'
            },
            'Mercury': {
                'Technology': 'communication technology and software',
                'Media': 'digital media and content platforms',
                'Education': 'online learning and documentation',
                'Finance': 'financial analysis and reporting'
            },
            'Venus': {
                'Technology': 'user experience and design technology',
                'Entertainment': 'luxury entertainment and media',
                'Fashion': 'fashion technology and e-commerce',
                'Healthcare': 'aesthetic healthcare and wellness'
            },
            'Mars': {
                'Technology': 'fast-paced tech development',
                'Defense': 'military technology and security',
                'Sports': 'sports technology and fitness',
                'Manufacturing': 'automated manufacturing'
            }
        }
        
        effects = []
        for industry in industries[:3]:  # Check first 3 industries
            if planet in industry_effects and industry in industry_effects[planet]:
                effects.append(industry_effects[planet][industry])
        
        return ', '.join(effects) if effects else None
    
    def _get_enhanced_roles_explanation(self, tenth_lord, tenth_house, conjunct_planets, details):
        """Generate detailed roles explanation with planetary and house influences"""
        planet_significations = {
            'Sun': 'government, authority, leadership, public service',
            'Moon': 'public relations, hospitality, healthcare, nurturing services', 
            'Mercury': 'communication, technology, analysis, commerce',
            'Venus': 'arts, entertainment, luxury, beauty, design',
            'Mars': 'engineering, technology, sports, defense, surgery',
            'Jupiter': 'education, law, finance, consulting, wisdom',
            'Saturn': 'organization, structure, manufacturing, real estate',
            'Rahu': 'innovation, foreign technology, unconventional methods',
            'Ketu': 'research, spirituality, behind-the-scenes work'
        }
        
        house_role_influence = {
            1: 'entrepreneurial and self-directed',
            2: 'wealth-focused and family business oriented',
            3: 'communication and media-focused',
            4: 'property and security-oriented',
            5: 'creative and speculative',
            6: 'service and health-oriented',
            7: 'partnership and client-facing',
            8: 'research and transformation-focused',
            9: 'educational and international',
            10: 'leadership and reputation-building',
            11: 'network and large-scale oriented',
            12: 'behind-the-scenes and foreign-focused'
        }
        
        base_roles = ', '.join(details['specific_roles'][:2])
        base_explanation = f"Your 10th lord {tenth_lord} ({planet_significations[tenth_lord]}) naturally creates aptitude for {base_roles} roles"
        
        # Add house influence
        house_influence = house_role_influence.get(tenth_house, 'professional')
        base_explanation += f", with {house_influence} approach due to {tenth_house}th house placement"
        
        # Add conjunction effects
        if conjunct_planets:
            conjunction_details = []
            for planet in conjunct_planets:
                if planet in planet_significations:
                    role_effect = self._get_role_conjunction_effect(planet, details['specific_roles'])
                    if role_effect:
                        conjunction_details.append(f"{planet} adds {role_effect}")
            
            if conjunction_details:
                base_explanation += f". {', '.join(conjunction_details)}."
        
        return base_explanation
    
    def _get_role_conjunction_effect(self, planet, roles):
        """Get how conjunctions affect specific roles"""
        role_effects = {
            'Rahu': {
                'Software Engineer': 'cutting-edge technology expertise and innovation',
                'Mechanical Engineer': 'advanced automation and robotics skills',
                'Project Manager': 'disruptive project methodologies and tech adoption',
                'Technical Lead': 'unconventional technical leadership and innovation',
                'Product Manager': 'breakthrough product vision and market disruption'
            },
            'Jupiter': {
                'Software Engineer': 'mentoring abilities and knowledge sharing',
                'Mechanical Engineer': 'teaching and training capabilities in engineering',
                'Project Manager': 'ethical leadership and team development',
                'Technical Lead': 'wisdom-based technical guidance and mentoring',
                'Teacher': 'enhanced educational abilities and curriculum development'
            },
            'Saturn': {
                'Software Engineer': 'systematic coding practices and quality focus',
                'Mechanical Engineer': 'precision engineering and long-term planning',
                'Project Manager': 'disciplined project execution and risk management',
                'Technical Lead': 'structured technical leadership and process improvement',
                'Operations Manager': 'enhanced organizational and quality control skills'
            },
            'Mercury': {
                'Software Engineer': 'excellent technical communication and documentation',
                'Technical Writer': 'enhanced writing and communication abilities',
                'Project Manager': 'superior communication and coordination skills',
                'Technical Lead': 'clear technical communication and team coordination',
                'Product Manager': 'analytical thinking and market communication'
            },
            'Venus': {
                'Software Engineer': 'user experience focus and aesthetic coding',
                'UX/UI Designer': 'enhanced design sensibilities and user empathy',
                'Project Manager': 'harmonious team management and stakeholder relations',
                'Technical Lead': 'collaborative leadership and team harmony',
                'Creative Director': 'enhanced creative vision and aesthetic judgment'
            },
            'Mars': {
                'Software Engineer': 'fast-paced development and problem-solving agility',
                'Mechanical Engineer': 'dynamic engineering solutions and hands-on approach',
                'Project Manager': 'decisive leadership and quick execution',
                'Technical Lead': 'action-oriented technical leadership and rapid delivery',
                'Operations Manager': 'efficient operations and quick decision-making'
            }
        }
        
        effects = []
        for role in roles[:3]:  # Check first 3 roles
            if planet in role_effects and role in role_effects[planet]:
                effects.append(role_effects[planet][role])
        
        return ', '.join(effects) if effects else f'{planet.lower()}-influenced capabilities'
    
    def _get_enhanced_companies_explanation(self, tenth_lord, tenth_house, conjunct_planets, details):
        """Generate detailed companies explanation with planetary and house influences"""
        planet_significations = {
            'Sun': 'government, authority, leadership, public service',
            'Moon': 'public relations, hospitality, healthcare, nurturing services', 
            'Mercury': 'communication, technology, analysis, commerce',
            'Venus': 'arts, entertainment, luxury, beauty, design',
            'Mars': 'engineering, technology, sports, defense, surgery',
            'Jupiter': 'education, law, finance, consulting, wisdom',
            'Saturn': 'organization, structure, manufacturing, real estate',
            'Rahu': 'innovation, foreign technology, unconventional methods',
            'Ketu': 'research, spirituality, behind-the-scenes work'
        }
        
        house_company_influence = {
            1: 'entrepreneurial startups and self-owned businesses',
            2: 'family businesses and wealth-focused companies',
            3: 'media companies and communication-based organizations',
            4: 'real estate firms and property-based companies',
            5: 'creative companies and entertainment organizations',
            6: 'service companies and healthcare organizations',
            7: 'partnership firms and international companies',
            8: 'research organizations and transformation-focused companies',
            9: 'educational institutions and international organizations',
            10: 'large corporations and government organizations',
            11: 'network companies and large-scale organizations',
            12: 'multinational companies and behind-the-scenes organizations'
        }
        
        base_companies = ', '.join(details['company_types'][:2])
        house_influence = house_company_influence.get(tenth_house, 'professional organizations')
        
        base_explanation = f"Your 10th lord {tenth_lord} ({planet_significations[tenth_lord]}) in {tenth_house}th house creates natural success in {base_companies}, particularly {house_influence}"
        
        # Add conjunction effects on company preferences
        if conjunct_planets:
            conjunction_details = []
            for planet in conjunct_planets:
                if planet in planet_significations:
                    company_effect = self._get_company_conjunction_effect(planet, details['company_types'])
                    if company_effect:
                        conjunction_details.append(f"{planet} adds affinity for {company_effect}")
            
            if conjunction_details:
                base_explanation += f". {', '.join(conjunction_details)}."
        
        return base_explanation
    
    def _get_company_conjunction_effect(self, planet, company_types):
        """Get how conjunctions affect company type preferences"""
        company_effects = {
            'Rahu': {
                'Tech Companies': 'innovative tech startups and disruptive companies',
                'Engineering Firms': 'cutting-edge engineering and automation companies',
                'Defense Contractors': 'advanced defense technology companies',
                'Government Agencies': 'modernizing government organizations',
                'Creative Agencies': 'viral marketing and digital-first agencies'
            },
            'Jupiter': {
                'Tech Companies': 'educational technology and knowledge-based companies',
                'Educational Institutions': 'prestigious universities and training organizations',
                'Law Firms': 'ethical law firms and policy organizations',
                'Financial Services': 'ethical finance and consulting firms',
                'Government Agencies': 'policy-making and advisory organizations'
            },
            'Saturn': {
                'Tech Companies': 'enterprise software and established tech companies',
                'Engineering Firms': 'infrastructure and heavy engineering companies',
                'Manufacturing Companies': 'quality-focused manufacturing organizations',
                'Government Agencies': 'systematic government departments',
                'Real Estate Firms': 'established property development companies'
            },
            'Mercury': {
                'Tech Companies': 'communication technology and software companies',
                'Media Companies': 'digital media and content organizations',
                'Consulting Firms': 'analytical and strategy consulting companies',
                'Government Contractors': 'communication and documentation services'
            },
            'Venus': {
                'Tech Companies': 'design-focused and user experience companies',
                'Creative Agencies': 'luxury brands and aesthetic-focused agencies',
                'Entertainment Studios': 'high-end entertainment and media companies',
                'Fashion Brands': 'luxury fashion and lifestyle companies'
            },
            'Mars': {
                'Tech Companies': 'fast-growing and competitive tech companies',
                'Engineering Firms': 'dynamic engineering and project-based companies',
                'Defense Contractors': 'military and security-focused organizations',
                'Manufacturing': 'automated and efficiency-focused manufacturers'
            }
        }
        
        effects = []
        for company_type in company_types[:3]:  # Check first 3 company types
            if planet in company_effects and company_type in company_effects[planet]:
                effects.append(company_effects[planet][company_type])
        
        return ', '.join(effects) if effects else f'{planet.lower()}-influenced organizations'
    
    def _get_enhanced_skills_explanation(self, tenth_lord, tenth_house, conjunct_planets, details):
        """Generate detailed skills explanation with planetary and house influences"""
        planet_significations = {
            'Sun': 'government, authority, leadership, public service',
            'Moon': 'public relations, hospitality, healthcare, nurturing services', 
            'Mercury': 'communication, technology, analysis, commerce',
            'Venus': 'arts, entertainment, luxury, beauty, design',
            'Mars': 'engineering, technology, sports, defense, surgery',
            'Jupiter': 'education, law, finance, consulting, wisdom',
            'Saturn': 'organization, structure, manufacturing, real estate',
            'Rahu': 'innovation, foreign technology, unconventional methods',
            'Ketu': 'research, spirituality, behind-the-scenes work'
        }
        
        house_skill_influence = {
            1: 'self-reliance and entrepreneurial abilities',
            2: 'wealth management and financial acumen',
            3: 'communication and networking skills',
            4: 'foundational knowledge and security-focused abilities',
            5: 'creative problem-solving and innovative thinking',
            6: 'service excellence and health-focused skills',
            7: 'partnership building and diplomatic abilities',
            8: 'research capabilities and transformational skills',
            9: 'higher learning and international perspective',
            10: 'leadership excellence and reputation management',
            11: 'large-scale thinking and network building',
            12: 'behind-the-scenes expertise and spiritual insight'
        }
        
        base_skills = ', '.join(details['key_skills'][:2])
        house_influence = house_skill_influence.get(tenth_house, 'professional capabilities')
        
        base_explanation = f"Your 10th lord {tenth_lord} ({planet_significations[tenth_lord]}) naturally develops {base_skills} abilities, enhanced by {tenth_house}th house placement which adds {house_influence}"
        
        # Add conjunction effects on skill development
        if conjunct_planets:
            conjunction_details = []
            for planet in conjunct_planets:
                if planet in planet_significations:
                    skill_effect = self._get_skill_conjunction_effect(planet, details['key_skills'])
                    if skill_effect:
                        conjunction_details.append(f"{planet} enhances {skill_effect}")
            
            if conjunction_details:
                base_explanation += f". {', '.join(conjunction_details)}."
        
        return base_explanation
    
    def _get_skill_conjunction_effect(self, planet, skills):
        """Get how conjunctions enhance specific skills"""
        skill_effects = {
            'Rahu': {
                'Technical Problem Solving': 'innovative and unconventional problem-solving approaches',
                'Engineering Design': 'cutting-edge design thinking and automation skills',
                'Project Management': 'disruptive project methodologies and tech adoption',
                'Innovation': 'breakthrough innovation and future-focused thinking',
                'Leadership': 'unconventional leadership styles and change management'
            },
            'Jupiter': {
                'Technical Problem Solving': 'systematic and wisdom-based problem analysis',
                'Teaching': 'advanced pedagogical skills and curriculum development',
                'Project Management': 'ethical project leadership and team development',
                'Legal Knowledge': 'comprehensive legal understanding and policy expertise',
                'Financial Analysis': 'strategic financial planning and ethical investing'
            },
            'Saturn': {
                'Technical Problem Solving': 'methodical and quality-focused problem resolution',
                'Engineering Design': 'precision engineering and long-term durability focus',
                'Project Management': 'disciplined execution and risk management expertise',
                'Organization': 'systematic organizational design and process improvement',
                'Quality Control': 'rigorous quality standards and continuous improvement'
            },
            'Mercury': {
                'Technical Communication': 'exceptional technical writing and documentation skills',
                'Data Analysis': 'advanced analytical thinking and pattern recognition',
                'Project Management': 'superior coordination and communication abilities',
                'Problem Solving': 'logical analysis and systematic solution development',
                'Communication': 'multi-channel communication and information synthesis'
            },
            'Venus': {
                'Design Thinking': 'aesthetic design sensibilities and user empathy',
                'User Experience': 'intuitive understanding of user needs and preferences',
                'Brand Strategy': 'creative brand development and market positioning',
                'Creative Software': 'mastery of design tools and creative technologies',
                'Team Management': 'harmonious team dynamics and collaborative leadership'
            },
            'Mars': {
                'Technical Problem Solving': 'rapid problem identification and decisive solutions',
                'Engineering Design': 'dynamic design approaches and hands-on implementation',
                'Project Management': 'fast-paced execution and deadline management',
                'Innovation': 'action-oriented innovation and rapid prototyping',
                'Leadership': 'decisive leadership and crisis management abilities'
            }
        }
        
        effects = []
        for skill in skills[:3]:  # Check first 3 skills
            if planet in skill_effects and skill in skill_effects[planet]:
                effects.append(skill_effects[planet][skill])
        
        return ', '.join(effects) if effects else f'{planet.lower()}-enhanced capabilities'
    
    def _get_domain_by_signification(self, planet, house_placement, domain_details):
        """Get domain based on actual planetary significations"""
        # Primary domain mapping based on planetary nature
        planet_domains = {
            'Sun': {
                'primary_domain': 'Government & Public Service',
                'industries': ['Government Services', 'Public Administration', 'Politics', 'Leadership Roles'],
                'specific_roles': ['Government Officer', 'Public Administrator', 'Policy Maker', 'Executive Leader'],
                'company_types': ['Government Agencies', 'Public Sector', 'Administrative Bodies'],
                'key_skills': ['Leadership', 'Public Administration', 'Policy Making', 'Team Management'],
                'specialization': 'Government & Authority'
            },
            'Moon': {
                'primary_domain': 'Healthcare & Public Relations',
                'industries': ['Healthcare', 'Hospitality', 'Public Relations', 'Nursing', 'Food Services'],
                'specific_roles': ['Healthcare Professional', 'PR Manager', 'Hospitality Manager', 'Counselor'],
                'company_types': ['Hospitals', 'Hotels', 'PR Agencies', 'Healthcare Organizations'],
                'key_skills': ['Empathy', 'Communication', 'Patient Care', 'Public Relations'],
                'specialization': 'Care & Public Relations'
            },
            'Mercury': {
                'primary_domain': 'Technology & Communication',
                'industries': ['Software Development', 'Digital Marketing', 'EdTech', 'Fintech', 'Media Technology'],
                'specific_roles': ['Product Manager', 'Technical Writer', 'Developer Relations', 'Solutions Architect'],
                'company_types': ['Tech Startups', 'Fortune 500 Tech', 'Government Contractors', 'Consulting Firms'],
                'key_skills': ['Technical Communication', 'Project Management', 'Data Analysis', 'Problem Solving'],
                'specialization': 'Technology Communication & Networks'
            },
            'Venus': {
                'primary_domain': 'Creative Arts & Entertainment',
                'industries': ['Entertainment', 'Design', 'Fashion', 'Gaming', 'Creative Technology'],
                'specific_roles': ['UX/UI Designer', 'Creative Director', 'Game Designer', 'Brand Manager'],
                'company_types': ['Creative Agencies', 'Entertainment Studios', 'Tech Companies', 'Fashion Brands'],
                'key_skills': ['Design Thinking', 'Creative Software', 'Brand Strategy', 'User Experience'],
                'specialization': 'Creative Design & Entertainment'
            },
            'Mars': {
                'primary_domain': 'Engineering & Technology',
                'industries': ['Engineering', 'Technology', 'Defense', 'Sports', 'Manufacturing'],
                'specific_roles': ['Software Engineer', 'Mechanical Engineer', 'Project Manager', 'Technical Lead'],
                'company_types': ['Tech Companies', 'Engineering Firms', 'Defense Contractors', 'Manufacturing'],
                'key_skills': ['Technical Problem Solving', 'Engineering Design', 'Project Management', 'Innovation'],
                'specialization': 'Engineering & Technical Innovation'
            },
            'Jupiter': {
                'primary_domain': 'Education & Legal Services',
                'industries': ['Education', 'Legal Services', 'Finance', 'Consulting', 'Publishing'],
                'specific_roles': ['Teacher', 'Lawyer', 'Financial Advisor', 'Consultant', 'Academic'],
                'company_types': ['Educational Institutions', 'Law Firms', 'Financial Services', 'Consulting'],
                'key_skills': ['Teaching', 'Legal Knowledge', 'Financial Analysis', 'Consulting'],
                'specialization': 'Education & Legal Wisdom'
            },
            'Saturn': {
                'primary_domain': 'Organization & Structure',
                'industries': ['Manufacturing', 'Real Estate', 'Construction', 'Mining', 'Agriculture'],
                'specific_roles': ['Operations Manager', 'Real Estate Developer', 'Construction Manager', 'Farmer'],
                'company_types': ['Manufacturing Companies', 'Real Estate Firms', 'Construction Companies'],
                'key_skills': ['Organization', 'Project Management', 'Quality Control', 'Long-term Planning'],
                'specialization': 'Structure & Organization'
            }
        }
        
        # Get base domain from planet
        if planet in planet_domains:
            base_domain = planet_domains[planet]
        else:
            base_domain = planet_domains['Mercury']  # Default
        
        # Modify based on house placement - add domain-specific flavors
        house_modifications = {
            2: ['Fintech', 'Financial Services', 'Wealth Management'],
            3: ['Media', 'Communication', 'Content Creation'],
            4: ['Real Estate Tech', 'Home Services', 'Security Systems'],
            5: ['Gaming', 'Entertainment Tech', 'Creative Platforms'],
            6: ['Healthcare Tech', 'Service Platforms', 'Daily Use Apps'],
            7: ['Partnership Platforms', 'International Business', 'Consulting'],
            8: ['Research & Development', 'Data Analytics', 'Transformation'],
            9: ['EdTech', 'Publishing', 'International Business'],
            10: ['Enterprise Solutions', 'Government Tech', 'Leadership Platforms'],
            11: ['Social Networks', 'Large Scale Systems', 'Community Platforms'],
            12: ['Backend Systems', 'Spiritual Tech', 'Remote Work Solutions']
        }
        
        if house_placement in house_modifications:
            for industry in house_modifications[house_placement]:
                if industry not in base_domain['industries']:
                    base_domain['industries'].append(industry)
        
        return base_domain
    
    def _get_nakshatra_specialization(self, nakshatra):
        """Get nakshatra-based specialization"""
        specialization_map = {
            'Ashwini': 'Healthcare & Emergency Services',
            'Bharani': 'Transformation Industries',
            'Krittika': 'Manufacturing & Production',
            'Rohini': 'Agriculture & Luxury',
            'Mrigashira': 'Research & Investigation',
            'Ardra': 'Technology & Innovation',
            'Punarvasu': 'Real Estate & Hospitality',
            'Pushya': 'Nutrition & Wellness',
            'Ashlesha': 'Psychology & Counseling',
            'Magha': 'Government & Authority',
            'Purva Phalguni': 'Entertainment & Arts',
            'Uttara Phalguni': 'Public Service',
            'Hasta': 'Crafts & Skills',
            'Chitra': 'Design & Architecture',
            'Swati': 'Trade & Commerce',
            'Vishakha': 'Goal-oriented Industries',
            'Anuradha': 'Networking & Relationships',
            'Jyeshtha': 'Leadership & Management',
            'Mula': 'Research & Foundations',
            'Purva Ashadha': 'Motivation & Inspiration',
            'Uttara Ashadha': 'Victory & Achievement',
            'Shravana': 'Communication & Learning',
            'Dhanishta': 'Music & Rhythm',
            'Shatabhisha': 'Healing & Medicine',
            'Purva Bhadrapada': 'Spirituality & Occult',
            'Uttara Bhadrapada': 'Deep Knowledge',
            'Revati': 'Completion & Guidance'
        }
        
        return specialization_map[nakshatra]
    
    def _analyze_tenth_lord_situation(self):
        """Analyze 10th lord planetary situation"""
        ascendant_sign = int(self.chart_data['ascendant'] / 30)
        tenth_house_sign = (ascendant_sign + 9) % 12
        tenth_lord = self.get_sign_lord(tenth_house_sign)
        
        tenth_lord_data = self.chart_data['planets'][tenth_lord]
        tenth_lord_house = tenth_lord_data['house']
        tenth_lord_sign = tenth_lord_data['sign']
        tenth_lord_nakshatra = self.nakshatra_data[tenth_lord]['nakshatra_name']
        
        # Get nakshatra ruler from config
        nakshatra_ruler = NAKSHATRA_RULERS[tenth_lord_nakshatra]
        
        return {
            'tenth_lord': tenth_lord,
            'house_placement': tenth_lord_house,
            'sign_placement': tenth_lord_sign,
            'sign_name': self.SIGN_NAMES[tenth_lord_sign],
            'sign_ruler': self.get_sign_lord(tenth_lord_sign),
            'nakshatra': tenth_lord_nakshatra,
            'nakshatra_ruler': nakshatra_ruler,
            'shadbala_strength': self.shadbala_data[tenth_lord]['total_rupas'],
            'dignity': self.dignities_data[tenth_lord]['dignity'],
            'house_context': HOUSE_WORK_INFLUENCE[tenth_lord_house]['context']
        }