from typing import Dict, List

class SuitableFieldsAnalyzer:
    def __init__(self, birth_data):
        self.birth_data = birth_data
        self.chart_data = None
        
        # Career field mappings
        self.field_mappings = {
            'Technology': {
                'planets': ['Mercury', 'Saturn'],
                'signs': [2, 5, 10],  # Gemini, Virgo, Aquarius
                'houses': [3, 6, 11],
                'description': 'Software development, IT services, digital innovation'
            },
            'Finance & Banking': {
                'planets': ['Jupiter', 'Mercury'],
                'signs': [1, 5, 9],  # Taurus, Virgo, Capricorn
                'houses': [2, 8, 11],
                'description': 'Banking, investment, financial planning, accounting'
            },
            'Healthcare': {
                'planets': ['Mars', 'Jupiter', 'Moon'],
                'signs': [3, 5, 7],  # Cancer, Virgo, Scorpio
                'houses': [6, 8, 12],
                'description': 'Medicine, nursing, healthcare administration'
            },
            'Education': {
                'planets': ['Jupiter', 'Mercury'],
                'signs': [2, 8, 11],  # Gemini, Sagittarius, Pisces
                'houses': [4, 5, 9],
                'description': 'Teaching, training, educational administration'
            },
            'Government': {
                'planets': ['Sun', 'Jupiter'],
                'signs': [4, 9],  # Leo, Capricorn
                'houses': [1, 10],
                'description': 'Civil services, public administration, politics'
            },
            'Business & Entrepreneurship': {
                'planets': ['Mercury', 'Venus', 'Mars'],
                'signs': [0, 2, 4],  # Aries, Gemini, Leo
                'houses': [1, 3, 7, 10],
                'description': 'Own business, trading, partnerships'
            },
            'Arts & Entertainment': {
                'planets': ['Venus', 'Moon'],
                'signs': [1, 4, 6],  # Taurus, Leo, Libra
                'houses': [3, 5, 12],
                'description': 'Creative arts, entertainment, media production'
            },
            'Engineering': {
                'planets': ['Mars', 'Saturn'],
                'signs': [0, 7, 9],  # Aries, Scorpio, Capricorn
                'houses': [3, 6, 10],
                'description': 'Technical engineering, construction, manufacturing'
            }
        }
    
    async def analyze(self):
        """Analyze suitable career fields"""
        # Calculate chart data
        self.chart_data = await self._calculate_chart()
        
        # Analyze each field
        field_scores = {}
        for field_name, field_data in self.field_mappings.items():
            score = self._calculate_field_compatibility(field_data)
            field_scores[field_name] = {
                'compatibility': score,
                'description': field_data['description'],
                'supporting_factors': self._get_supporting_factors(field_data, score)
            }
        
        # Sort fields by compatibility
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1]['compatibility'], reverse=True)
        
        # Separate primary and secondary recommendations
        primary_fields = [{'name': name, **data} for name, data in sorted_fields[:3] if data['compatibility'] >= 70]
        secondary_fields = [{'name': name, **data} for name, data in sorted_fields[3:6] if data['compatibility'] >= 50]
        
        # Business vs Job analysis
        business_vs_job = await self._analyze_business_vs_job()
        
        # Foreign opportunities
        foreign_opportunities = await self._analyze_foreign_opportunities()
        
        return {
            "primary_fields": primary_fields,
            "secondary_fields": secondary_fields,
            "business_vs_job": business_vs_job,
            "foreign_opportunities": foreign_opportunities
        }
    
    async def analyze_foreign_opportunities(self):
        """Analyze foreign career opportunities specifically"""
        return await self._analyze_foreign_opportunities()
    
    async def analyze_financial_prospects(self):
        """Analyze financial prospects and wealth indicators"""
        # Analyze 2nd house (earned wealth)
        second_house_analysis = self._analyze_wealth_house(2)
        
        # Analyze 11th house (gains)
        eleventh_house_analysis = self._analyze_wealth_house(11)
        
        # Multiple income sources
        multiple_income = self._analyze_multiple_income_sources()
        
        return {
            "earned_wealth": second_house_analysis,
            "gains_income": eleventh_house_analysis,
            "multiple_income_potential": multiple_income,
            "wealth_yogas": self._identify_wealth_yogas(),
            "financial_timing": self._analyze_financial_timing()
        }
    
    def _calculate_field_compatibility(self, field_data):
        """Calculate compatibility score for a career field"""
        score = 0
        
        # Planet strength in field (40% weight)
        planet_score = 0
        for planet in field_data['planets']:
            planet_strength = self._get_planet_strength_for_career(planet)
            planet_score += planet_strength
        
        if field_data['planets']:
            planet_score = (planet_score / len(field_data['planets'])) * 0.4
        
        # Sign compatibility (30% weight)
        sign_score = 0
        ascendant_sign = self.chart_data.get('ascendant_sign', 0)
        tenth_house_sign = (ascendant_sign + 9) % 12
        
        if ascendant_sign in field_data['signs'] or tenth_house_sign in field_data['signs']:
            sign_score = 30
        elif any(self._is_friendly_sign(ascendant_sign, sign) for sign in field_data['signs']):
            sign_score = 20
        else:
            sign_score = 10
        
        sign_score *= 0.3
        
        # House emphasis (30% weight)
        house_score = 0
        for house in field_data['houses']:
            if self._has_planets_in_house(house):
                house_score += 25
            elif self._is_house_strong(house):
                house_score += 15
        
        house_score = min(house_score, 30) * 0.3
        
        total_score = planet_score + sign_score + house_score
        return min(int(total_score), 100)
    
    async def _analyze_business_vs_job(self):
        """Analyze business vs job suitability"""
        business_score = 0
        job_score = 0
        
        # Business indicators
        # Strong 1st, 7th, 10th houses
        if self._is_house_strong(1):
            business_score += 20
        if self._is_house_strong(7):
            business_score += 15
        if self._is_house_strong(10):
            business_score += 15
        
        # Mars and Mercury strength
        mars_strength = self._get_planet_strength_for_career('Mars')
        mercury_strength = self._get_planet_strength_for_career('Mercury')
        business_score += (mars_strength + mercury_strength) / 4
        
        # Job indicators
        # Strong 6th house (service)
        if self._is_house_strong(6):
            job_score += 25
        
        # Saturn strength (discipline, service)
        saturn_strength = self._get_planet_strength_for_career('Saturn')
        job_score += saturn_strength / 2
        
        # Jupiter strength (advisory roles)
        jupiter_strength = self._get_planet_strength_for_career('Jupiter')
        job_score += jupiter_strength / 3
        
        # Normalize scores
        business_score = min(int(business_score), 100)
        job_score = min(int(job_score), 100)
        
        return {
            "business_score": business_score,
            "job_score": job_score,
            "business_analysis": self._get_business_analysis(business_score),
            "job_analysis": self._get_job_analysis(job_score)
        }
    
    async def _analyze_foreign_opportunities(self):
        """Analyze foreign career opportunities"""
        foreign_score = 0
        
        # 12th house (foreign lands)
        if self._is_house_strong(12):
            foreign_score += 25
        
        # 9th house (long distance travel)
        if self._is_house_strong(9):
            foreign_score += 20
        
        # Rahu strength (foreign influence)
        if self._has_planets_in_house(12) or self._has_planets_in_house(9):
            foreign_score += 15
        
        # Water signs emphasis
        water_signs = [3, 7, 11]  # Cancer, Scorpio, Pisces
        ascendant_sign = self.chart_data.get('ascendant_sign', 0)
        if ascendant_sign in water_signs:
            foreign_score += 10
        
        foreign_score = min(foreign_score, 100)
        
        # Favorable directions based on planetary positions
        favorable_directions = self._get_favorable_directions()
        
        return {
            "score": foreign_score,
            "analysis": self._get_foreign_analysis(foreign_score),
            "favorable_directions": favorable_directions
        }
    
    async def _calculate_chart(self):
        """Calculate basic chart data"""
        # Simplified chart calculation
        return {
            'ascendant_sign': 0,  # Placeholder - would use actual calculation
            'planets': {}
        }
    
    def _get_planet_strength_for_career(self, planet):
        """Get planet strength for career purposes"""
        # Simplified strength calculation
        return 60  # Placeholder
    
    def _has_planets_in_house(self, house):
        """Check if house has planets"""
        return house in [1, 10]  # Placeholder
    
    def _is_house_strong(self, house):
        """Check if house is strong"""
        return house in [1, 4, 7, 10]  # Placeholder
    
    def _is_friendly_sign(self, sign1, sign2):
        """Check if signs are friendly"""
        return abs(sign1 - sign2) in [4, 8]  # Trine relationship
    
    def _get_supporting_factors(self, field_data, score):
        """Get supporting factors for field compatibility"""
        factors = []
        if score >= 80:
            factors.append("Strong planetary support")
            factors.append("Favorable house positions")
        elif score >= 60:
            factors.append("Good planetary alignment")
            factors.append("Moderate house support")
        else:
            factors.append("Basic compatibility present")
        
        return factors
    
    def _get_business_analysis(self, score):
        """Get business suitability analysis"""
        if score >= 75:
            return "Excellent entrepreneurial potential with strong leadership and business acumen."
        elif score >= 55:
            return "Good business potential with proper planning and partnerships."
        else:
            return "Business ventures require careful consideration and strong partnerships."
    
    def _get_job_analysis(self, score):
        """Get job suitability analysis"""
        if score >= 75:
            return "Excellent for structured employment with growth opportunities in organizations."
        elif score >= 55:
            return "Good potential for stable employment with steady career progression."
        else:
            return "Job roles require focus on skill development and performance improvement."
    
    def _get_foreign_analysis(self, score):
        """Get foreign opportunities analysis"""
        if score >= 70:
            return "Strong potential for foreign assignments, international business, or overseas career."
        elif score >= 50:
            return "Moderate opportunities for foreign connections and international exposure."
        else:
            return "Foreign opportunities may require additional qualifications and networking."
    
    def _get_favorable_directions(self):
        """Get favorable directions for career"""
        return ["North", "East", "Northeast"]  # Placeholder
    
    def _analyze_wealth_house(self, house_num):
        """Analyze wealth-related house"""
        return {
            "strength": "Medium",
            "planets": ["Jupiter"],
            "analysis": f"{house_num}th house shows moderate wealth potential."
        }
    
    def _analyze_multiple_income_sources(self):
        """Analyze potential for multiple income sources"""
        return {
            "potential": "High",
            "sources": ["Primary career", "Investments", "Side business"],
            "analysis": "Good potential for diversified income streams."
        }
    
    def _identify_wealth_yogas(self):
        """Identify wealth-creating yogas"""
        return [
            {"name": "Dhana Yoga", "strength": "Medium", "description": "Moderate wealth accumulation potential"}
        ]
    
    def _analyze_financial_timing(self):
        """Analyze timing for financial growth"""
        return {
            "peak_periods": ["Age 28-35", "Age 42-49"],
            "growth_phases": ["Current period shows steady growth"],
            "recommendations": ["Focus on savings and investments"]
        }