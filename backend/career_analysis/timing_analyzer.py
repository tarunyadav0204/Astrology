from datetime import datetime, timedelta
from typing import Dict, List

class CareerTimingAnalyzer:
    def __init__(self, birth_data):
        self.birth_data = birth_data
        self.chart_data = None
        
        # Dasha periods (in years) for timing analysis
        self.dasha_periods = {
            'Sun': 6, 'Moon': 10, 'Mars': 7, 'Rahu': 18,
            'Jupiter': 16, 'Saturn': 19, 'Mercury': 17,
            'Ketu': 7, 'Venus': 20
        }
        
        # Career impact of different planets
        self.career_impact = {
            'Sun': {'impact': 'High', 'areas': ['Leadership', 'Government', 'Authority']},
            'Moon': {'impact': 'Medium', 'areas': ['Public relations', 'Healthcare', 'Hospitality']},
            'Mars': {'impact': 'High', 'areas': ['Engineering', 'Sports', 'Military']},
            'Mercury': {'impact': 'High', 'areas': ['Business', 'Communication', 'IT']},
            'Jupiter': {'impact': 'High', 'areas': ['Education', 'Finance', 'Law']},
            'Venus': {'impact': 'Medium', 'areas': ['Arts', 'Entertainment', 'Luxury']},
            'Saturn': {'impact': 'Medium', 'areas': ['Service', 'Manufacturing', 'Hard work']},
            'Rahu': {'impact': 'High', 'areas': ['Innovation', 'Foreign', 'Technology']},
            'Ketu': {'impact': 'Low', 'areas': ['Spirituality', 'Research', 'Occult']}
        }
    
    async def analyze(self):
        """Analyze career timing and favorable periods"""
        # Calculate chart data
        self.chart_data = await self._calculate_chart()
        
        # Get current dasha period
        current_period = await self._get_current_dasha_period()
        
        # Get upcoming favorable periods
        upcoming_periods = await self._get_upcoming_periods()
        
        # Analyze major transits
        major_transits = await self._analyze_major_transits()
        
        # Identify career peaks
        career_peaks = await self._identify_career_peaks()
        
        # Generate recommendations
        recommendations = self._generate_timing_recommendations(current_period, upcoming_periods)
        
        return {
            "current_period": current_period,
            "upcoming_periods": upcoming_periods,
            "major_transits": major_transits,
            "career_peaks": career_peaks,
            "recommendations": recommendations
        }
    
    async def analyze_challenges_remedies(self):
        """Analyze career challenges and suggest remedies"""
        challenges = await self._identify_career_challenges()
        remedies = self._suggest_remedies(challenges)
        
        return {
            "challenges": challenges,
            "remedies": remedies,
            "favorable_periods_for_remedies": self._get_remedy_timing(),
            "preventive_measures": self._get_preventive_measures()
        }
    
    async def _get_current_dasha_period(self):
        """Get current Mahadasha period"""
        # This would use the existing dasha calculation API
        # For now, return placeholder data
        current_year = datetime.now().year
        
        return {
            "dasha_lord": "Jupiter",
            "start_date": f"{current_year - 2}-01-01",
            "end_date": f"{current_year + 14}-01-01",
            "career_impact": "High",
            "interpretation": "Jupiter Mahadasha brings opportunities in education, finance, and advisory roles. Excellent time for career growth and recognition."
        }
    
    async def _get_upcoming_periods(self):
        """Get upcoming favorable career periods"""
        current_year = datetime.now().year
        periods = []
        
        # Next 3 major periods
        periods.append({
            "dasha_lord": "Saturn",
            "start_date": f"{current_year + 14}-01-01",
            "end_date": f"{current_year + 33}-01-01",
            "career_impact": "Medium",
            "interpretation": "Saturn period emphasizes hard work, discipline, and service-oriented careers. Slow but steady progress.",
            "key_opportunities": [
                "Government positions",
                "Manufacturing sector",
                "Long-term projects"
            ]
        })
        
        periods.append({
            "dasha_lord": "Mercury",
            "start_date": f"{current_year + 33}-01-01",
            "end_date": f"{current_year + 50}-01-01",
            "career_impact": "High",
            "interpretation": "Mercury period excellent for business, communication, and technology careers. Peak earning potential.",
            "key_opportunities": [
                "Business expansion",
                "IT and communication roles",
                "Writing and media"
            ]
        })
        
        return periods
    
    async def _analyze_major_transits(self):
        """Analyze major planetary transits affecting career"""
        current_year = datetime.now().year
        transits = []
        
        # Jupiter transits (every 12 years through each house)
        transits.append({
            "planet": "Jupiter",
            "date": f"{current_year + 1}-06-15",
            "through_house": "10th House",
            "impact": "High",
            "interpretation": "Jupiter transit through 10th house brings career advancement, recognition, and new opportunities."
        })
        
        # Saturn transits (every 2.5 years through each house)
        transits.append({
            "planet": "Saturn",
            "date": f"{current_year + 2}-03-20",
            "through_house": "11th House",
            "impact": "Medium",
            "interpretation": "Saturn transit through 11th house brings steady income growth and achievement of long-term goals."
        })
        
        return transits
    
    async def _identify_career_peaks(self):
        """Identify career peak periods based on age and planetary cycles"""
        birth_year = int(self.birth_data.date.split('-')[0])
        current_year = datetime.now().year
        current_age = current_year - birth_year
        
        peaks = []
        
        # Standard career peak ages
        peak_ages = [28, 35, 42, 49, 56]
        
        for age in peak_ages:
            if age > current_age:
                year = birth_year + age
                strength = self._calculate_peak_strength(age)
                
                peaks.append({
                    "age": age,
                    "year": year,
                    "strength": strength,
                    "description": self._get_peak_description(age, strength)
                })
        
        return peaks[:3]  # Return next 3 peaks
    
    async def _identify_career_challenges(self):
        """Identify potential career challenges"""
        challenges = []
        
        # Based on planetary positions and aspects
        challenges.append({
            "type": "Competition",
            "severity": "Medium",
            "period": "Next 2-3 years",
            "description": "Increased competition in chosen field may require additional skills and networking.",
            "planetary_cause": "Mars-Saturn aspect"
        })
        
        challenges.append({
            "type": "Career Change",
            "severity": "Low",
            "period": "Age 35-40",
            "description": "Potential career transition period requiring careful planning and preparation.",
            "planetary_cause": "Rahu-Ketu axis shift"
        })
        
        return challenges
    
    def _suggest_remedies(self, challenges):
        """Suggest remedies for career challenges"""
        remedies = []
        
        for challenge in challenges:
            if challenge['type'] == 'Competition':
                remedies.append({
                    "for_challenge": challenge['type'],
                    "remedy_type": "Skill Development",
                    "actions": [
                        "Enhance technical skills through certification",
                        "Build professional network",
                        "Focus on unique value proposition"
                    ],
                    "gemstone": "Red Coral (for Mars energy)",
                    "mantra": "Om Angarakaya Namaha",
                    "timing": "Tuesday mornings"
                })
            
            elif challenge['type'] == 'Career Change':
                remedies.append({
                    "for_challenge": challenge['type'],
                    "remedy_type": "Preparation",
                    "actions": [
                        "Start exploring new opportunities gradually",
                        "Build financial reserves",
                        "Develop transferable skills"
                    ],
                    "gemstone": "Yellow Sapphire (for Jupiter guidance)",
                    "mantra": "Om Brihaspataye Namaha",
                    "timing": "Thursday mornings"
                })
        
        return remedies
    
    async def _calculate_chart(self):
        """Calculate basic chart data"""
        return {
            'ascendant_sign': 0,
            'planets': {}
        }
    
    def _calculate_peak_strength(self, age):
        """Calculate strength of career peak at given age"""
        # Simplified calculation based on age and planetary cycles
        if age in [28, 42]:
            return 85  # Strong peaks
        elif age in [35, 49]:
            return 75  # Medium peaks
        else:
            return 65  # Moderate peaks
    
    def _get_peak_description(self, age, strength):
        """Get description for career peak"""
        descriptions = {
            28: "First major career breakthrough with recognition and advancement opportunities.",
            35: "Mid-career peak with leadership roles and increased responsibilities.",
            42: "Professional mastery period with expertise recognition and mentoring opportunities.",
            49: "Senior leadership phase with strategic roles and industry influence.",
            56: "Wisdom and experience culmination with advisory and consultancy opportunities."
        }
        
        return descriptions.get(age, f"Significant career milestone at age {age}.")
    
    def _generate_timing_recommendations(self, current_period, upcoming_periods):
        """Generate timing-based career recommendations"""
        recommendations = []
        
        # Current period recommendations
        if current_period['career_impact'] == 'High':
            recommendations.append({
                "type": "Immediate Action",
                "timing": "Next 6-12 months",
                "description": "Excellent time for career moves, job changes, or business expansion. Take advantage of favorable planetary support."
            })
        
        # Upcoming period preparations
        if upcoming_periods and upcoming_periods[0]['career_impact'] == 'High':
            recommendations.append({
                "type": "Future Preparation",
                "timing": f"Prepare for {upcoming_periods[0]['start_date'][:4]}",
                "description": f"Start preparing for {upcoming_periods[0]['dasha_lord']} period opportunities in {', '.join(upcoming_periods[0]['key_opportunities'])}."
            })
        
        # General timing advice
        recommendations.append({
            "type": "Optimal Timing",
            "timing": "Thursday and Sunday",
            "description": "Best days for career-related decisions and important meetings based on planetary influences."
        })
        
        return recommendations
    
    def _get_remedy_timing(self):
        """Get favorable periods for implementing remedies"""
        return [
            "Waxing Moon periods (Shukla Paksha)",
            "Thursday mornings for Jupiter-related remedies",
            "Tuesday mornings for Mars-related remedies"
        ]
    
    def _get_preventive_measures(self):
        """Get preventive measures for career challenges"""
        return [
            "Regular skill updates and learning",
            "Maintain professional relationships",
            "Build emergency fund for career transitions",
            "Stay updated with industry trends",
            "Practice stress management techniques"
        ]