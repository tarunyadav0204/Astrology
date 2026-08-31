from datetime import datetime, timedelta

import swisseph as swe

from .ashtakavarga import AshtakavargaCalculator, NAKSHATRA_NAMES, SIGN_NAMES


TRANSIT_PLANET_IDS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN,
}
KAKSHYA_SIZE = 30.0 / 8.0

class AshtakavargaTransitCalculator(AshtakavargaCalculator):
    """Enhanced Ashtakavarga calculator with transit integration"""
    
    def __init__(self, birth_data, chart_data, reduction_profile='pvr_narasimha_rao'):
        # Ashtakavarga transit judgment is always made against the fixed natal
        # BAV/SAV/Prastara. Transit positions are inputs to that natal ledger;
        # they do not generate a replacement "transit SAV".
        super().__init__(birth_data, chart_data, reduction_profile=reduction_profile)

    @staticmethod
    def _parse_moment(value):
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        text = str(value or '').strip()
        if 'T' in text:
            return datetime.fromisoformat(text.replace('Z', '+00:00')).replace(tzinfo=None)
        return datetime.strptime(text, '%Y-%m-%d').replace(hour=12)

    @staticmethod
    def _julian_day(moment):
        hour = moment.hour + moment.minute / 60.0 + moment.second / 3600.0
        return swe.julday(moment.year, moment.month, moment.day, hour)

    def _transit_position(self, planet, moment):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        values = swe.calc_ut(
            self._julian_day(moment),
            TRANSIT_PLANET_IDS[planet],
            swe.FLG_SIDEREAL | swe.FLG_SPEED,
        )[0]
        longitude = float(values[0]) % 360.0
        speed = float(values[3])
        sign_id = int(longitude // 30) % 12
        degree = longitude % 30.0
        nakshatra_number = int(longitude // (360.0 / 27.0)) + 1
        kakshya_number = min(8, int(degree // KAKSHYA_SIZE) + 1)
        return {
            'longitude': longitude,
            'speed_degrees_per_day': speed,
            'retrograde': speed < 0,
            'sign_id': sign_id,
            'sign': SIGN_NAMES[sign_id],
            'degree_in_sign': degree,
            'nakshatra_number': nakshatra_number,
            'nakshatra': NAKSHATRA_NAMES[nakshatra_number - 1],
            'kakshya_number': kakshya_number,
        }

    def _all_transit_positions(self, moment):
        return {planet: self._transit_position(planet, moment) for planet in TRANSIT_PLANET_IDS}

    @staticmethod
    def _sav_band(points):
        # Parashara's Light manual: <=24 weak, 25–30 medium, >30 strong.
        if points > 30:
            return 'strong'
        if points >= 25:
            return 'medium'
        return 'weak'

    @staticmethod
    def _bav_band(points):
        # A neutral display band only; no probability or invented composite score.
        if points >= 5:
            return 'bindu_rich'
        if points >= 3:
            return 'mixed'
        return 'bindu_poor'

    def _planet_transit_evidence(self, planet, position, natal_sav, advanced):
        sign_id = position['sign_id']
        bav = self.calculate_individual_ashtakavarga(planet)
        bindus = bav.get('bindus', {})
        bav_points = int(bindus.get(sign_id, bindus.get(str(sign_id), 0)) or 0)
        sav_points = int(natal_sav.get(str(sign_id), natal_sav.get(sign_id, 0)) or 0)
        kakshya = self.calculate_kakshya_activation(planet, position['longitude'])
        timing_key = {
            'Sun': 'father', 'Moon': 'mother', 'Mars': 'siblings',
            'Mercury': 'profession', 'Jupiter': 'children',
            'Venus': 'marriage', 'Saturn': 'longevity',
        }[planet]
        sensitive = (advanced.get('classical_timing') or {}).get(timing_key, {})
        rashi_match = (sign_id + 1) in (sensitive.get('rashi_trine_numbers') or [])
        nakshatra_match = position['nakshatra_number'] in (sensitive.get('vimshottari_group_numbers') or [])
        natal_asc_sign = int(float(self.chart_data.get('ascendant', 0)) // 30) % 12
        return {
            'planet': planet,
            **position,
            'natal_house': ((sign_id - natal_asc_sign) % 12) + 1,
            'natal_bav_bindus': bav_points,
            'natal_bav_band': self._bav_band(bav_points),
            'natal_sav_bindus': sav_points,
            'natal_sav_band': self._sav_band(sav_points),
            'kakshya': kakshya,
            'sensitive_timing': {
                'topic': timing_key,
                'reference_nakshatra': sensitive.get('nakshatra'),
                'reference_rashi': sensitive.get('rashi'),
                'nakshatra_group': sensitive.get('vimshottari_group', []),
                'rashi_trines': sensitive.get('rashi_trines', []),
                'nakshatra_match': nakshatra_match,
                'rashi_match': rashi_match,
                'double_match': nakshatra_match and rashi_match,
            },
            'evidence_flags': [
                flag for flag, present in (
                    ('kakshya_bindu', bool(kakshya.get('active'))),
                    ('sensitive_nakshatra', nakshatra_match),
                    ('sensitive_rashi', rashi_match),
                    ('natal_bav_bindus_5_plus', bav_points >= 5),
                    ('natal_sav_above_30', sav_points > 30),
                ) if present
            ],
        }

    @staticmethod
    def _state_key(position):
        return (
            position['sign_id'],
            position['nakshatra_number'],
            position['kakshya_number'],
            position['retrograde'],
        )

    def _refine_state_change(self, planet, left, right, field, old_value):
        # The three-hour scan interval is narrower than one lunar Kakshya, so each
        # interval contains at most one boundary for every tracked field.
        for _ in range(20):
            middle = left + (right - left) / 2
            if self._transit_position(planet, middle)[field] == old_value:
                left = middle
            else:
                right = middle
        return right

    def calculate_transit_calendar(self, start, days=30):
        start = self._parse_moment(start).replace(hour=0, minute=0, second=0, microsecond=0)
        days = max(1, min(int(days), 366))
        end = start + timedelta(days=days)
        natal_sav = self.calculate_sarvashtakavarga().get('sarvashtakavarga', {})
        advanced = self.calculate_advanced_ashtakavarga()
        events = []
        step = timedelta(hours=3)
        fields = (
            ('sign_id', 'rashi_ingress'),
            ('nakshatra_number', 'nakshatra_ingress'),
            ('kakshya_number', 'kakshya_ingress'),
            ('retrograde', 'direction_station'),
        )
        for planet in TRANSIT_PLANET_IDS:
            left = start
            left_position = self._transit_position(planet, left)
            while left < end:
                right = min(left + step, end)
                right_position = self._transit_position(planet, right)
                for field, event_type in fields:
                    if left_position[field] == right_position[field]:
                        continue
                    boundary = self._refine_state_change(planet, left, right, field, left_position[field])
                    after = self._transit_position(planet, boundary + timedelta(seconds=1))
                    evidence = self._planet_transit_evidence(planet, after, natal_sav, advanced)
                    events.append({
                        'type': event_type,
                        'timestamp_utc': boundary.isoformat(timespec='minutes') + 'Z',
                        'planet': planet,
                        'direction': 'retrograde' if after['retrograde'] else 'direct',
                        'from': left_position[field],
                        'to': after[field],
                        'sign': after['sign'],
                        'nakshatra': after['nakshatra'],
                        'kakshya_number': after['kakshya_number'],
                        'kakshya_ruler': evidence['kakshya'].get('kakshya_ruler'),
                        'kakshya_bindu': evidence['kakshya'].get('bindu'),
                        'natal_bav_bindus': evidence['natal_bav_bindus'],
                        'natal_sav_bindus': evidence['natal_sav_bindus'],
                        'sensitive_timing': evidence['sensitive_timing'],
                    })
                left = right
                left_position = right_position
        return sorted(events, key=lambda row: (row['timestamp_utc'], row['planet'], row['type']))

    def calculate_classical_transit_analysis(self, transit_date, window_days=30):
        moment = self._parse_moment(transit_date)
        natal_sarva = self.calculate_sarvashtakavarga()
        natal_sav = natal_sarva.get('sarvashtakavarga', {})
        advanced = self.calculate_advanced_ashtakavarga()
        rows = self.calculate_transit_snapshot(moment, natal_sav=natal_sav, advanced=advanced)
        return {
            'schema_version': 'ashtakavarga.transit.v2',
            'basis': 'fixed_natal_bav_sav_prastara',
            'snapshot_utc': moment.isoformat(timespec='minutes') + 'Z',
            'transit_date': moment.date().isoformat(),
            'convention': advanced.get('convention', {}),
            'natal_sav': natal_sav,
            'planet_transits': rows,
            'sensitive_hits': [
                row for row in rows
                if row['sensitive_timing']['rashi_match'] or row['sensitive_timing']['nakshatra_match']
            ],
            'kakshya_bindu_hits': [row for row in rows if row['kakshya'].get('active')],
            'calendar_window': {
                'start_date': moment.date().isoformat(),
                'days': max(1, min(int(window_days), 366)),
                'events': self.calculate_transit_calendar(moment, window_days),
            },
            'interpretation_guardrail': (
                'Rows expose classical bindu and sensitive-place evidence independently. '
                'No composite probability or guaranteed event result is calculated.'
            ),
        }

    def calculate_transit_snapshot(self, transit_date, natal_sav=None, advanced=None):
        """Return the seven grahas placed against one fixed natal AV ledger."""
        moment = self._parse_moment(transit_date)
        if natal_sav is None:
            natal_sav = self.calculate_sarvashtakavarga().get('sarvashtakavarga', {})
        if advanced is None:
            advanced = self.calculate_advanced_ashtakavarga()
        positions = self._all_transit_positions(moment)
        return [
            self._planet_transit_evidence(planet, positions[planet], natal_sav, advanced)
            for planet in TRANSIT_PLANET_IDS
        ]
        
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
