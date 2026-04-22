from .ashtakavarga import AshtakavargaCalculator
from datetime import datetime, timedelta
import swisseph as swe
from datetime import datetime, timedelta

class AshtakavargaTransitCalculator(AshtakavargaCalculator):
    """Enhanced Ashtakavarga calculator with transit integration"""
    
    def __init__(self, birth_data, chart_data):
        super().__init__(birth_data, chart_data)
        
    def calculate_transit_ashtakavarga(self, transit_date):
        """Calculate Ashtakavarga for transit positions"""
        # Parse transit date
        if isinstance(transit_date, str):
            transit_date = datetime.strptime(transit_date, '%Y-%m-%d')
        
        jd = swe.julday(transit_date.year, transit_date.month, transit_date.day, 12.0)
        
        # Calculate transit planetary positions
        transit_planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            # Set Lahiri Ayanamsa for accurate Vedic calculations

            swe.set_sid_mode(swe.SIDM_LAHIRI)

            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
            transit_planets[planet_names[i]] = {
                'sign': int(pos[0] / 30),
                'longitude': pos[0]
            }
        
        # Calculate Ashtakavarga using transit positions
        return self._calculate_sarva_with_positions(transit_planets)
    
    def get_transit_recommendations(self, transit_date, duration_days=30):
        """Get personalized recommendations based on transit Ashtakavarga analysis"""
        transit_av = self.calculate_transit_ashtakavarga(transit_date)
        birth_av = self.calculate_sarvashtakavarga()
        
        # Calculate current planetary positions for transit date
        if isinstance(transit_date, str):
            transit_date = datetime.strptime(transit_date, '%Y-%m-%d')
        
        jd = swe.julday(transit_date.year, transit_date.month, transit_date.day, 12.0)
        
        # Get current transit positions
        transit_planets = {}
        planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6]):
            pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
            transit_planets[planet_names[i]] = {
                'sign': int(pos[0] / 30),
                'longitude': pos[0]
            }
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Transit AV strength should be computed via local usability (SAV + transit planet BAV),
        # not total bindu ratios (SAV totals are structurally redistributed).
        def _sav_band(points):
            if points >= 30:
                return 'strong'
            if points >= 25:
                return 'workable'
            return 'weak'

        def _bav_band(points):
            if points >= 5:
                return 'supportive'
            if points >= 3:
                return 'mixed'
            return 'blocked'

        planet_usability_rows = []
        supportive_hits = 0
        obstructed_hits = 0
        for planet, data in transit_planets.items():
            planet_sign = data['sign']
            sav_points = int(transit_av['sarvashtakavarga'].get(str(planet_sign), 0) or 0)
            pchart = ((transit_av.get('individual_charts') or {}).get(planet) or {})
            bindu_map = pchart.get('bindus') or {}
            bav_points = int(bindu_map.get(planet_sign, bindu_map.get(str(planet_sign), 0)) or 0)
            sav_band = _sav_band(sav_points)
            bav_band = _bav_band(bav_points)
            if sav_band == 'strong' and bav_band == 'supportive':
                verdict = 'supportive'
                supportive_hits += 1
            elif sav_band == 'weak' or bav_band == 'blocked':
                verdict = 'obstructed'
                obstructed_hits += 1
            else:
                verdict = 'mixed'
            planet_usability_rows.append(
                {
                    'planet': planet,
                    'sign': planet_sign,
                    'sign_name': sign_names[planet_sign],
                    'sav': sav_points,
                    'sav_band': sav_band,
                    'bav': bav_points,
                    'bav_band': bav_band,
                    'verdict': verdict,
                }
            )

        if supportive_hits > obstructed_hits:
            transit_strength = 'strong'
        elif obstructed_hits > supportive_hits:
            transit_strength = 'weak'
        else:
            transit_strength = 'moderate'
        
        # Find signs with significant changes
        enhanced_signs = []
        reduced_signs = []
        strong_signs = []
        weak_signs = []
        
        for sign in range(12):
            transit_points = transit_av['sarvashtakavarga'].get(str(sign), 0)
            birth_points = birth_av['sarvashtakavarga'].get(str(sign), 0)
            
            # Track changes from birth chart
            if transit_points > birth_points + 2:
                enhanced_signs.append(sign)
            elif transit_points < birth_points - 2:
                reduced_signs.append(sign)
            
            # Track absolute strength
            if transit_points >= 30:
                strong_signs.append(sign)
            elif transit_points <= 25:
                weak_signs.append(sign)
        
        # Analyze which planets are in strong/weak positions
        planets_in_strong_signs = []
        planets_in_weak_signs = []
        
        for planet, data in transit_planets.items():
            planet_sign = data['sign']
            transit_bindus = transit_av['sarvashtakavarga'].get(str(planet_sign), 0)
            
            if transit_bindus >= 30:
                planets_in_strong_signs.append(planet)
            elif transit_bindus <= 25:
                planets_in_weak_signs.append(planet)
        
        # Generate personalized recommendations
        recommendations = {
            'favorable_activities': [],
            'avoid_activities': [],
            'best_timing': [],
            'transit_strength': transit_strength,
            'planet_usability': planet_usability_rows,
        }
        
        # Favorable activities based on analysis
        if enhanced_signs or strong_signs:
            if 'Jupiter' in planets_in_strong_signs:
                recommendations['favorable_activities'].append("Excellent time for education, spiritual practices, and long-term investments")
            if 'Venus' in planets_in_strong_signs:
                recommendations['favorable_activities'].append("Favorable for relationships, creative projects, and luxury purchases")
            if 'Mercury' in planets_in_strong_signs:
                recommendations['favorable_activities'].append("Good for communication, business deals, and intellectual pursuits")
            if 'Sun' in planets_in_strong_signs:
                recommendations['favorable_activities'].append("Ideal for leadership roles, government work, and public recognition")
            if 'Moon' in planets_in_strong_signs:
                recommendations['favorable_activities'].append("Beneficial for emotional decisions, family matters, and intuitive work")
            
            if enhanced_signs:
                enhanced_sign_names = [sign_names[s] for s in enhanced_signs[:3]]
                recommendations['favorable_activities'].append(f"Enhanced energy in {', '.join(enhanced_sign_names)} - good for activities related to these areas")
        
        # Activities to avoid based on analysis
        if reduced_signs or weak_signs:
            if 'Saturn' in planets_in_weak_signs:
                recommendations['avoid_activities'].append("Avoid major commitments or long-term decisions - Saturn's influence is weakened")
            if 'Mars' in planets_in_weak_signs:
                recommendations['avoid_activities'].append("Postpone aggressive actions, competitions, or risky ventures")
            if 'Sun' in planets_in_weak_signs:
                recommendations['avoid_activities'].append("Not ideal for seeking authority positions or public recognition")
            
            if reduced_signs:
                reduced_sign_names = [sign_names[s] for s in reduced_signs[:3]]
                recommendations['avoid_activities'].append(f"Reduced energy in {', '.join(reduced_sign_names)} - avoid major decisions in these life areas")
        
        # Add general recommendations based on overall strength
        if transit_strength == 'strong':
            recommendations['favorable_activities'].append("Overall strong period - good time for new initiatives and important decisions")
            recommendations['best_timing'] = ["Morning hours", "Waxing moon periods", "Thursday and Friday"]
        elif transit_strength == 'weak':
            recommendations['avoid_activities'].append("Overall weak period - focus on routine work and avoid major changes")
            recommendations['best_timing'] = ["Evening hours", "Waning moon periods", "Saturday for important tasks"]
        else:
            if enhanced_signs:
                recommendations['favorable_activities'].append("Moderate period with some enhanced areas - proceed with caution and proper planning")
            else:
                recommendations['favorable_activities'].append("Moderate period - proceed with caution and proper planning")
            recommendations['best_timing'] = ["Mid-day hours", "Full moon and new moon days"]
        
        # Ensure we have at least some recommendations
        if not recommendations['favorable_activities']:
            recommendations['favorable_activities'] = ["Focus on routine activities and gradual progress"]
        
        if not recommendations['avoid_activities']:
            recommendations['avoid_activities'] = ["Avoid hasty decisions without proper analysis"]
        
        return recommendations
    
    def compare_birth_transit_strength(self, transit_date):
        """Compare birth chart Ashtakavarga with transit Ashtakavarga with detailed analysis"""
        birth_av = self.calculate_sarvashtakavarga()
        transit_av = self.calculate_transit_ashtakavarga(transit_date)
        
        comparison = {}
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Total SAV bindus are structurally invariant for a fixed rule matrix,
        # so the useful comparison is redistribution across signs, not total delta.
        total_bindus = sum(birth_av['sarvashtakavarga'].values())
        
        # Calculate distribution variance to show how much the energy has shifted
        total_absolute_change = sum(abs(transit_av['sarvashtakavarga'].get(str(i), 0) - birth_av['sarvashtakavarga'].get(str(i), 0)) for i in range(12))
        distribution_shift = total_absolute_change / 2  # Divide by 2 since each change is counted twice
        
        significant_changes = 0
        enhanced_count = 0
        reduced_count = 0
        
        for sign in range(12):
            birth_points = birth_av['sarvashtakavarga'].get(str(sign), 0)
            transit_points = transit_av['sarvashtakavarga'].get(str(sign), 0)
            difference = transit_points - birth_points
            
            # Determine status with more nuanced categories
            if difference > 2:
                status = 'significantly_enhanced'
                enhanced_count += 1
                significant_changes += 1
            elif difference > 0:
                status = 'enhanced'
                enhanced_count += 1
            elif difference < -2:
                status = 'significantly_reduced'
                reduced_count += 1
                significant_changes += 1
            elif difference < 0:
                status = 'reduced'
                reduced_count += 1
            else:
                status = 'stable'
            
            # Calculate percentage change
            percentage_change = (difference / birth_points * 100) if birth_points > 0 else 0
            
            comparison[sign_names[sign]] = {
                'birth_points': birth_points,
                'transit_points': transit_points,
                'difference': difference,
                'percentage_change': round(percentage_change, 1),
                'status': status,
                'strength_category': self._get_strength_category(transit_points)
            }
        
        # Add summary statistics
        comparison['summary'] = {
            'distribution_shift': int(distribution_shift),
            'distribution_percentage': round((distribution_shift / total_bindus * 100), 1) if total_bindus > 0 else 0,
            'significant_changes': significant_changes,
            'enhanced_signs': enhanced_count,
            'reduced_signs': reduced_count,
            'stability_index': round((12 - significant_changes) / 12 * 100, 1),
            'comparison_basis': 'redistribution_only',
        }
        
        return comparison
    
    def _get_strength_category(self, bindus):
        """Categorize sign strength based on bindu count"""
        if bindus >= 35:
            return 'excellent'
        elif bindus >= 30:
            return 'strong'
        elif bindus >= 25:
            return 'average'
        elif bindus >= 20:
            return 'weak'
        else:
            return 'very_weak'
    
    def _calculate_sarva_with_positions(self, planet_positions):
        """Calculate Sarvashtakavarga with custom planet positions"""
        sarva = {i: 0 for i in range(12)}
        individual_charts = {}
        
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for planet in planets:
            chart = self._calculate_individual_av_with_positions(planet, planet_positions)
            individual_charts[planet] = chart
            
            for sign, bindus in chart['bindus'].items():
                sarva[sign] += bindus
        
        # Convert keys to strings for consistent API response
        sarva_str_keys = {str(k): v for k, v in sarva.items()}
        
        return {
            'sarvashtakavarga': sarva_str_keys,
            'total_bindus': sum(sarva.values()),
            'individual_charts': individual_charts
        }
    
    def _calculate_individual_av_with_positions(self, target_planet, planet_positions):
        """Calculate individual Ashtakavarga with custom positions"""
        if target_planet not in self.contribution_rules:
            return {}
        
        bindus = [0] * 12
        rules = self.contribution_rules[target_planet]
        
        for contributor, beneficial_houses in rules.items():
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30)
            elif contributor in planet_positions:
                contributor_sign = planet_positions[contributor]['sign']
            else:
                continue
            
            for house_num in beneficial_houses:
                target_sign = (contributor_sign + house_num - 1) % 12
                bindus[target_sign] += 1
        
        return {
            'planet': target_planet,
            'bindus': {i: bindus[i] for i in range(12)},
            'total': sum(bindus)
        }
