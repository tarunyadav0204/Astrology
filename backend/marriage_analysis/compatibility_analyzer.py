"""
Compatibility Analyzer for Marriage Analysis
Integrates Guna Milan and basic compatibility scoring
"""
from typing import Dict, Any
from .guna_milan import GunaMilanCalculator

class CompatibilityAnalyzer:
    def __init__(self):
        self.guna_calculator = GunaMilanCalculator()
    
    def analyze_compatibility(self, boy_chart: Dict, girl_chart: Dict, boy_birth: Dict, girl_birth: Dict) -> Dict[str, Any]:
        """Complete compatibility analysis between two charts"""
        
        # Get Moon nakshatras for Guna Milan
        boy_moon_nak = self._get_moon_nakshatra(boy_chart)
        girl_moon_nak = self._get_moon_nakshatra(girl_chart)
        
        # Calculate Guna Milan
        guna_milan = self.guna_calculator.calculate_ashtakoot(boy_moon_nak, girl_moon_nak)
        
        # Basic Manglik analysis
        boy_manglik = self._check_manglik(boy_chart)
        girl_manglik = self._check_manglik(girl_chart)
        manglik_compatibility = self._analyze_manglik_compatibility(boy_manglik, girl_manglik)
        
        # Overall compatibility score
        overall_score = self._calculate_overall_score(guna_milan, manglik_compatibility)
        
        return {
            "guna_milan": guna_milan,
            "manglik_analysis": {
                "boy_manglik": boy_manglik,
                "girl_manglik": girl_manglik,
                "compatibility": manglik_compatibility
            },
            "overall_score": overall_score,
            "recommendation": self._get_recommendation(overall_score, guna_milan, manglik_compatibility)
        }
    
    def _get_moon_nakshatra(self, chart_data: Dict) -> str:
        """Get Moon's nakshatra from chart data"""
        moon_data = chart_data.get('planets', {}).get('Moon', {})
        moon_longitude = moon_data.get('longitude', 0)
        
        # Calculate nakshatra (each nakshatra is 13.333... degrees)
        nakshatra_num = int(moon_longitude / 13.333333) + 1
        
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
            'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        return nakshatras[min(nakshatra_num - 1, 26)]
    
    def _check_manglik(self, chart_data: Dict) -> Dict[str, Any]:
        """Check Manglik dosha in chart"""
        mars_data = chart_data.get('planets', {}).get('Mars', {})
        mars_house = mars_data.get('house', 0)
        
        # Manglik houses: 1, 2, 4, 7, 8, 12
        manglik_houses = [1, 2, 4, 7, 8, 12]
        is_manglik = mars_house in manglik_houses
        
        severity = 'None'
        if is_manglik:
            if mars_house in [1, 7, 8]:
                severity = 'High'
            elif mars_house in [2, 12]:
                severity = 'Medium'
            else:
                severity = 'Low'
        
        return {
            "is_manglik": is_manglik,
            "mars_house": mars_house,
            "severity": severity
        }
    
    def _analyze_manglik_compatibility(self, boy_manglik: Dict, girl_manglik: Dict) -> Dict[str, Any]:
        """Analyze Manglik compatibility between partners"""
        boy_is_manglik = boy_manglik['is_manglik']
        girl_is_manglik = girl_manglik['is_manglik']
        
        if not boy_is_manglik and not girl_is_manglik:
            return {
                "status": "Compatible",
                "description": "Neither partner is Manglik",
                "score": 10
            }
        elif boy_is_manglik and girl_is_manglik:
            return {
                "status": "Compatible",
                "description": "Both partners are Manglik - doshas cancel out (Compatible)",
                "score": 8
            }
        else:
            manglik_partner = "Boy" if boy_is_manglik else "Girl"
            severity = boy_manglik['severity'] if boy_is_manglik else girl_manglik['severity']
            
            score = 3 if severity == 'High' else 5 if severity == 'Medium' else 7
            
            return {
                "status": "Incompatible",
                "description": f"{manglik_partner} is Manglik ({severity} severity)",
                "score": score,
                "remedies_needed": True
            }
    
    def _calculate_overall_score(self, guna_milan: Dict, manglik_compatibility: Dict) -> Dict[str, Any]:
        """Calculate overall compatibility score"""
        guna_score = guna_milan['total_score']
        guna_percentage = guna_milan['percentage']
        manglik_score = manglik_compatibility['score']
        
        # Weighted scoring: Guna Milan 70%, Manglik 30%
        overall_percentage = (guna_percentage * 0.7) + (manglik_score * 10 * 0.3)
        
        if overall_percentage >= 80:
            grade = 'Excellent'
        elif overall_percentage >= 65:
            grade = 'Good'
        elif overall_percentage >= 50:
            grade = 'Average'
        else:
            grade = 'Poor'
        
        return {
            "percentage": round(overall_percentage, 1),
            "grade": grade,
            "guna_contribution": round(guna_percentage * 0.7, 1),
            "manglik_contribution": round(manglik_score * 10 * 0.3, 1)
        }
    
    def _get_recommendation(self, overall_score: Dict, guna_milan: Dict, manglik_compatibility: Dict) -> Dict[str, Any]:
        """Generate compatibility recommendation"""
        grade = overall_score['grade']
        critical_issues = guna_milan.get('critical_issues', [])
        
        if grade == 'Excellent':
            recommendation = "Highly compatible match with excellent prospects"
            proceed = True
        elif grade == 'Good':
            recommendation = "Good compatibility with minor considerations"
            proceed = True
        elif grade == 'Average':
            recommendation = "Average compatibility - consider remedies if needed"
            proceed = True
        else:
            recommendation = "Poor compatibility - significant challenges expected"
            proceed = False
        
        remedies = []
        if critical_issues:
            remedies.extend([f"Address {issue}" for issue in critical_issues])
        
        if manglik_compatibility.get('remedies_needed'):
            remedies.append("Perform Manglik dosha remedies")
        
        return {
            "recommendation": recommendation,
            "proceed": proceed,
            "remedies": remedies,
            "critical_issues": critical_issues
        }