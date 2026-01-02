from .ashtakavarga_transit import AshtakavargaTransitCalculator
from datetime import datetime, timedelta
import swisseph as swe

class AshtakavargaEventPredictor(AshtakavargaTransitCalculator):
    """Event prediction using Ashtakavarga as per Dots of Destiny principles"""
    
    def __init__(self, birth_data, chart_data):
        super().__init__(birth_data, chart_data)
        
    def predict_events_for_year(self, year):
        """Predict events for entire year using Ashtakavarga principles"""
        events = []
        
        # Check major transits through high/low bindu signs
        birth_av = self.calculate_sarvashtakavarga()
        
        # Identify critical signs (very high/low bindus)
        critical_signs = self._get_critical_signs(birth_av)
        
        # Track Jupiter and Saturn transits through critical signs
        jupiter_events = self._predict_jupiter_events(year, critical_signs)
        saturn_events = self._predict_saturn_events(year, critical_signs)
        
        events.extend(jupiter_events)
        events.extend(saturn_events)
        
        return sorted(events, key=lambda x: x['date'])
    
    def _get_critical_signs(self, birth_av):
        """Identify signs with very high (35+) or very low (20-) bindus"""
        critical = {
            'very_strong': [],  # 35+ bindus
            'strong': [],       # 30-34 bindus  
            'weak': [],         # 21-25 bindus
            'very_weak': []     # 20- bindus
        }
        
        for sign in range(12):
            bindus = birth_av['sarvashtakavarga'].get(str(sign), 0)
            if bindus >= 35:
                critical['very_strong'].append(sign)
            elif bindus >= 30:
                critical['strong'].append(sign)
            elif bindus <= 20:
                critical['very_weak'].append(sign)
            elif bindus <= 25:
                critical['weak'].append(sign)
                
        return critical
    
    def _predict_jupiter_events(self, year, critical_signs):
        """Predict events based on Jupiter transits through critical signs"""
        events = []
        
        # Jupiter takes ~12 years for full cycle, ~1 year per sign
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        # Check Jupiter position monthly
        for month in range(1, 13):
            check_date = datetime(year, month, 15)
            jd = swe.julday(year, month, 15, 12.0)
            
            # Set Lahiri Ayanamsa for accurate Vedic calculations

            
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            
            jupiter_pos = swe.calc_ut(jd, 5, swe.FLG_SIDEREAL)[0][0]
            jupiter_sign = int(jupiter_pos / 30)
            
            # Events when Jupiter transits critical signs
            if jupiter_sign in critical_signs['very_strong']:
                events.append({
                    'date': check_date,
                    'planet': 'Jupiter',
                    'event_type': 'major_positive',
                    'description': f'Jupiter in very strong sign - excellent for growth, education, spirituality',
                    'life_areas': ['education', 'spirituality', 'wealth', 'children'],
                    'strength': 90
                })
            elif jupiter_sign in critical_signs['strong']:
                events.append({
                    'date': check_date,
                    'planet': 'Jupiter',
                    'event_type': 'positive',
                    'description': f'Jupiter in strong sign - favorable for expansion and wisdom',
                    'life_areas': ['career', 'knowledge', 'relationships'],
                    'strength': 75
                })
            elif jupiter_sign in critical_signs['very_weak']:
                events.append({
                    'date': check_date,
                    'planet': 'Jupiter',
                    'event_type': 'challenging',
                    'description': f'Jupiter in very weak sign - obstacles in growth areas',
                    'life_areas': ['education', 'finances', 'health'],
                    'strength': 30
                })
                
        return events
    
    def _predict_saturn_events(self, year, critical_signs):
        """Predict events based on Saturn transits through critical signs"""
        events = []
        
        # Saturn takes ~30 years for full cycle, ~2.5 years per sign
        for month in range(1, 13):
            check_date = datetime(year, month, 15)
            jd = swe.julday(year, month, 15, 12.0)
            
            saturn_pos = swe.calc_ut(jd, 6, swe.FLG_SIDEREAL)[0][0]
            saturn_sign = int(saturn_pos / 30)
            
            # Events when Saturn transits critical signs
            if saturn_sign in critical_signs['very_strong']:
                events.append({
                    'date': check_date,
                    'planet': 'Saturn',
                    'event_type': 'structured_growth',
                    'description': f'Saturn in very strong sign - disciplined progress and achievements',
                    'life_areas': ['career', 'discipline', 'long_term_goals'],
                    'strength': 80
                })
            elif saturn_sign in critical_signs['very_weak']:
                events.append({
                    'date': check_date,
                    'planet': 'Saturn',
                    'event_type': 'major_challenges',
                    'description': f'Saturn in very weak sign - significant obstacles and delays',
                    'life_areas': ['career', 'health', 'relationships'],
                    'strength': 25
                })
                
        return events
    
    def predict_specific_event_timing(self, event_type, start_year, end_year):
        """Predict timing for specific events like marriage, career change, etc."""
        if event_type == 'marriage':
            return self.predict_marriage_timing_detailed(start_year, end_year)
        elif event_type == 'children':
            return self.predict_children_timing_detailed(start_year, end_year)
            
        predictions = []
        birth_av = self.calculate_sarvashtakavarga()
        
        # Event-specific sign analysis
        event_signs = self._get_event_relevant_signs(event_type)
        
        for year in range(start_year, end_year + 1):
            year_strength = 0
            monthly_analysis = []
            
            for month in range(1, 13):
                check_date = datetime(year, month, 15)
                
                # Get major planet positions
                jd = swe.julday(year, month, 15, 12.0)
                jupiter_sign = int(swe.calc_ut(jd, 5, swe.FLG_SIDEREAL)[0][0] / 30)
                saturn_sign = int(swe.calc_ut(jd, 6, swe.FLG_SIDEREAL)[0][0] / 30)
                
                month_strength = 0
                
                # Check if benefics are in strong signs for this event
                for sign in event_signs:
                    sign_bindus = birth_av['sarvashtakavarga'].get(str(sign), 0)
                    
                    if jupiter_sign == sign and sign_bindus >= 30:
                        month_strength += 40
                    if saturn_sign == sign and sign_bindus >= 30:
                        month_strength += 30
                        
                monthly_analysis.append({
                    'month': month,
                    'strength': month_strength,
                    'jupiter_sign': jupiter_sign,
                    'saturn_sign': saturn_sign
                })
                
                year_strength += month_strength
            
            # Determine probability based on year strength
            if year_strength >= 200:
                probability = 'Very High'
            elif year_strength >= 120:
                probability = 'High'  
            elif year_strength >= 60:
                probability = 'Medium'
            else:
                probability = 'Low'
                
            predictions.append({
                'year': year,
                'event_type': event_type,
                'probability': probability,
                'strength': year_strength,
                'best_months': [m['month'] for m in monthly_analysis if m['strength'] >= 40],
                'analysis': f'Annual strength: {year_strength}/360 points'
            })
            
        return predictions
    
    def predict_children_timing_detailed(self, start_year, end_year):
        """Detailed children timing prediction using Ashtakavarga principles"""
        birth_av = self.calculate_sarvashtakavarga()
        predictions = []
        
        # Get 5th house sign from birth chart (children) - 5th house is 120 degrees from ascendant
        ascendant_degrees = self.chart_data['ascendant']
        fifth_house_degrees = (ascendant_degrees + 120) % 360
        fifth_house_sign = int(fifth_house_degrees / 30)
        
        # Children-relevant signs: 5th house (children), 9th house (fortune), 11th house (gains)
        children_signs = {
            'primary': fifth_house_sign,  # 5th house - main children indicator
            'fortune': [(fifth_house_sign + 4) % 12],  # 9th from 5th (fortune in children)
            'gains': [(fifth_house_sign + 6) % 12]  # 11th from 5th (gains from children)
        }
        
        for year in range(start_year, end_year + 1):
            year_analysis = self._analyze_children_year(year, birth_av, children_signs)
            predictions.append(year_analysis)
            
        return predictions
    
    def _analyze_children_year(self, year, birth_av, children_signs):
        """Analyze specific year for children potential"""
        total_strength = 0
        monthly_details = []
        
        # Key factors for children timing:
        # 1. Jupiter transit through 5th house or strong children signs
        # 2. Moon transit support (fertility)
        # 3. 5th house bindus strength
        # 4. Avoid Saturn in 5th house (delays)
        
        primary_sign_bindus = birth_av['sarvashtakavarga'].get(str(children_signs['primary']), 0)
        
        for month in range(1, 13):
            jd = swe.julday(year, month, 15, 12.0)
            
            # Get Jupiter, Moon, and Saturn positions
            jupiter_pos = swe.calc_ut(jd, 5, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
            saturn_pos = swe.calc_ut(jd, 6, swe.FLG_SIDEREAL)[0][0]
            
            jupiter_sign = int(jupiter_pos / 30)
            moon_sign = int(moon_pos / 30)
            saturn_sign = int(saturn_pos / 30)
            
            month_strength = 0
            factors = []
            
            # Jupiter in 5th house or children signs (most important)
            if jupiter_sign == children_signs['primary']:
                jupiter_boost = primary_sign_bindus * 2.5  # Higher weight for children
                month_strength += jupiter_boost
                factors.append(f"Jupiter in 5th house ({primary_sign_bindus} bindus)")
            elif jupiter_sign in children_signs['fortune'] + children_signs['gains']:
                month_strength += birth_av['sarvashtakavarga'].get(str(jupiter_sign), 0) * 1.8
                factors.append(f"Jupiter in children-supportive sign")
            
            # Moon in strong signs (fertility support)
            moon_bindus = birth_av['sarvashtakavarga'].get(str(moon_sign), 0)
            if moon_bindus >= 28:  # Lower threshold for Moon
                month_strength += moon_bindus * 0.8
                factors.append(f"Moon in fertile sign ({moon_bindus} bindus)")
            
            # Saturn in 5th house reduces chances (delays)
            if saturn_sign == children_signs['primary']:
                month_strength -= 20  # Penalty for Saturn in 5th
                factors.append("Saturn in 5th house (delays)")
            
            # 5th house strength bonus
            if primary_sign_bindus >= 32:
                month_strength += 25  # Very strong 5th house
                factors.append("Very strong 5th house")
            elif primary_sign_bindus >= 28:
                month_strength += 15  # Strong 5th house
                factors.append("Strong 5th house")
            
            # Ensure minimum 0
            month_strength = max(0, month_strength)
            
            monthly_details.append({
                'month': month,
                'strength': month_strength,
                'factors': factors,
                'jupiter_sign': jupiter_sign,
                'moon_sign': moon_sign,
                'saturn_sign': saturn_sign
            })
            
            total_strength += month_strength
        
        # Determine probability based on total strength
        if total_strength >= 400:
            probability = 'Very High'
            description = 'Excellent year for children - very favorable planetary support'
        elif total_strength >= 250:
            probability = 'High'
            description = 'Very favorable year for children'
        elif total_strength >= 150:
            probability = 'Medium'
            description = 'Moderate chances for children'
        else:
            probability = 'Low'
            description = 'Less favorable year for children'
        
        # Find best months (strength >= 50)
        best_months = [detail['month'] for detail in monthly_details if detail['strength'] >= 50]
        
        return {
            'year': year,
            'event_type': 'children',
            'probability': probability,
            'strength': int(total_strength),
            'description': description,
            'best_months': best_months,
            'fifth_house_bindus': primary_sign_bindus,
            'analysis': f'Children strength: {int(total_strength)}/800 points. 5th house has {primary_sign_bindus} bindus.',
            'monthly_breakdown': sorted(monthly_details, key=lambda x: x['strength'], reverse=True)[:3]
        }
    
    def predict_marriage_timing_detailed(self, start_year, end_year):
        """Detailed marriage timing prediction using Ashtakavarga principles"""
        birth_av = self.calculate_sarvashtakavarga()
        predictions = []
        
        # Get 7th house sign from birth chart - 7th house is 180 degrees from ascendant
        ascendant_degrees = self.chart_data['ascendant']
        seventh_house_degrees = (ascendant_degrees + 180) % 360
        seventh_house_sign = int(seventh_house_degrees / 30)
        
        # Marriage-relevant signs: 7th house, 2nd house (family), 11th house (fulfillment)
        marriage_signs = {
            'primary': seventh_house_sign,  # 7th house - main marriage indicator
            'secondary': [(seventh_house_sign + 5) % 12],  # 2nd from 7th (family expansion)
            'fulfillment': [(seventh_house_sign + 4) % 12]  # 11th from 7th (gains from marriage)
        }
        
        for year in range(start_year, end_year + 1):
            year_analysis = self._analyze_marriage_year(year, birth_av, marriage_signs)
            predictions.append(year_analysis)
            
        return predictions
    
    def _analyze_marriage_year(self, year, birth_av, marriage_signs):
        """Analyze specific year for marriage potential"""
        total_strength = 0
        monthly_details = []
        
        # Key factors for marriage timing:
        # 1. Jupiter transit through 7th house or strong marriage signs
        # 2. Venus transit through beneficial signs
        # 3. 7th house bindus strength
        # 4. Dasha periods of 7th lord or Venus
        
        primary_sign_bindus = birth_av['sarvashtakavarga'].get(str(marriage_signs['primary']), 0)
        
        for month in range(1, 13):
            jd = swe.julday(year, month, 15, 12.0)
            
            # Get Jupiter and Venus positions
            jupiter_pos = swe.calc_ut(jd, 5, swe.FLG_SIDEREAL)[0][0]
            venus_pos = swe.calc_ut(jd, 3, swe.FLG_SIDEREAL)[0][0]
            jupiter_sign = int(jupiter_pos / 30)
            venus_sign = int(venus_pos / 30)
            
            month_strength = 0
            factors = []
            
            # Jupiter in 7th house or marriage signs (most important)
            if jupiter_sign == marriage_signs['primary']:
                jupiter_boost = primary_sign_bindus * 2  # Double weight for 7th house
                month_strength += jupiter_boost
                factors.append(f"Jupiter in 7th house ({primary_sign_bindus} bindus)")
            elif jupiter_sign in marriage_signs['secondary'] + marriage_signs['fulfillment']:
                month_strength += birth_av['sarvashtakavarga'].get(str(jupiter_sign), 0) * 1.5
                factors.append(f"Jupiter in marriage-supportive sign")
            
            # Venus in strong signs (secondary importance)
            venus_bindus = birth_av['sarvashtakavarga'].get(str(venus_sign), 0)
            if venus_bindus >= 30:
                month_strength += venus_bindus
                factors.append(f"Venus in strong sign ({venus_bindus} bindus)")
            
            # 7th house strength bonus
            if primary_sign_bindus >= 35:
                month_strength += 20  # Very strong 7th house
                factors.append("Very strong 7th house")
            elif primary_sign_bindus >= 30:
                month_strength += 10  # Strong 7th house
                factors.append("Strong 7th house")
            
            monthly_details.append({
                'month': month,
                'strength': month_strength,
                'factors': factors,
                'jupiter_sign': jupiter_sign,
                'venus_sign': venus_sign
            })
            
            total_strength += month_strength
        
        # Determine probability based on total strength
        if total_strength >= 300:
            probability = 'Very High'
            description = 'Excellent year for marriage - multiple favorable transits'
        elif total_strength >= 200:
            probability = 'High'
            description = 'Very favorable year for marriage'
        elif total_strength >= 120:
            probability = 'Medium'
            description = 'Moderate chances for marriage'
        else:
            probability = 'Low'
            description = 'Less favorable year for marriage'
        
        # Find best months (strength >= 40)
        best_months = [detail['month'] for detail in monthly_details if detail['strength'] >= 40]
        
        return {
            'year': year,
            'event_type': 'marriage',
            'probability': probability,
            'strength': total_strength,
            'description': description,
            'best_months': best_months,
            'seventh_house_bindus': primary_sign_bindus,
            'analysis': f'Marriage strength: {total_strength}/600 points. 7th house has {primary_sign_bindus} bindus.',
            'monthly_breakdown': monthly_details[:3]  # Show top 3 months
        }
    
    def _get_event_relevant_signs(self, event_type):
        """Get signs most relevant for specific event types"""
        if event_type == 'marriage':
            # Use detailed marriage analysis instead
            return self.predict_marriage_timing_detailed
            
        event_sign_map = {
            'career': [9, 10],       # 10th house, 11th house
            'property': [3, 7],      # 4th house, 8th house
            'education': [2, 4, 8],  # 3rd, 5th, 9th houses
            'health': [0, 5, 7],     # 1st, 6th, 8th houses
            'travel': [2, 8, 11],    # 3rd, 9th, 12th houses
            'spirituality': [4, 8, 11] # 5th, 9th, 12th houses
        }
        
        return event_sign_map.get(event_type, [6, 9])  # Default to 7th and 10th
    
    def get_daily_ashtakavarga_strength(self, date):
        """Get Ashtakavarga strength for specific date"""
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
            
        transit_av = self.calculate_transit_ashtakavarga(date)
        birth_av = self.calculate_sarvashtakavarga()
        
        # Calculate daily strength based on:
        # 1. Planets in strong signs
        # 2. Enhanced signs from birth chart
        # 3. Vedic day strength factors
        
        jd = swe.julday(date.year, date.month, date.day, 12.0)
        
        daily_strength = 0
        planet_strengths = {}
        
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        planet_indices = [0, 1, 4, 2, 5, 3, 6]
        
        for i, planet in enumerate(planets):
            pos = swe.calc_ut(jd, planet_indices[i], swe.FLG_SIDEREAL)[0][0]
            planet_sign = int(pos / 30)
            
            # Get bindu strength for this planet in this sign
            birth_bindus = birth_av['sarvashtakavarga'].get(str(planet_sign), 0)
            transit_bindus = transit_av['sarvashtakavarga'].get(str(planet_sign), 0)
            
            # Planet-specific strength calculation
            planet_strength = self._calculate_planet_daily_strength(
                planet, planet_sign, birth_bindus, transit_bindus
            )
            
            planet_strengths[planet] = planet_strength
            daily_strength += planet_strength
            
        # Normalize to 0-100 scale
        normalized_strength = min(100, (daily_strength / 7) * 100 / 50)  # 50 is average strength
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'overall_strength': round(normalized_strength, 1),
            'planet_strengths': planet_strengths,
            'strength_category': self._get_daily_strength_category(normalized_strength),
            'recommendations': self._get_daily_recommendations(normalized_strength, planet_strengths)
        }
    
    def _calculate_planet_daily_strength(self, planet, sign, birth_bindus, transit_bindus):
        """Calculate individual planet strength for the day"""
        base_strength = birth_bindus
        
        # Planet-specific multipliers based on Vedic principles
        multipliers = {
            'Sun': 1.2,      # Leadership, authority
            'Moon': 1.1,     # Emotions, mind
            'Mars': 1.0,     # Energy, action
            'Mercury': 1.1,  # Communication, intellect
            'Jupiter': 1.3,  # Wisdom, growth
            'Venus': 1.1,    # Relationships, creativity
            'Saturn': 0.9    # Discipline, obstacles
        }
        
        return base_strength * multipliers.get(planet, 1.0)
    
    def _get_daily_strength_category(self, strength):
        """Categorize daily strength"""
        if strength >= 80:
            return 'excellent'
        elif strength >= 65:
            return 'strong'
        elif strength >= 50:
            return 'moderate'
        elif strength >= 35:
            return 'weak'
        else:
            return 'challenging'
    
    def _get_daily_recommendations(self, strength, planet_strengths):
        """Get daily recommendations based on strength"""
        recommendations = []
        
        if strength >= 70:
            recommendations.append("Excellent day for important decisions and new initiatives")
            
        if planet_strengths.get('Jupiter', 0) >= 40:
            recommendations.append("Favorable for education, spiritual practices, and investments")
            
        if planet_strengths.get('Venus', 0) >= 40:
            recommendations.append("Good for relationships, creative work, and social activities")
            
        if planet_strengths.get('Mercury', 0) >= 40:
            recommendations.append("Ideal for communication, business deals, and learning")
            
        if strength < 40:
            recommendations.append("Focus on routine work and avoid major decisions")
            
        return recommendations