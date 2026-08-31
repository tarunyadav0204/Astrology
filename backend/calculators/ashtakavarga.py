import swisseph as swe


CLASSICAL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
KAKSHYA_RULERS = ['Saturn', 'Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Ascendant']
TRIKONA_GROUPS = ((0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11))
EKADHIPATYA_PAIRS = {
    'Mars': (0, 7), 'Venus': (1, 6), 'Mercury': (2, 5),
    'Jupiter': (8, 11), 'Saturn': (9, 10),
}
# Parashara convention used by P.V.R. Narasimha Rao/Jagannatha Hora.
RASHI_MULTIPLIERS = (7, 10, 8, 4, 10, 6, 7, 8, 9, 5, 11, 12)
GRAHA_MULTIPLIERS = {
    'Sun': 5, 'Moon': 5, 'Mars': 8, 'Mercury': 5,
    'Jupiter': 10, 'Venus': 7, 'Saturn': 5,
}
EKADHIPATYA_PROFILES = {
    'pvr_narasimha_rao': {
        'label': 'P.V.R. Narasimha Rao published convention',
        'mixed_higher_empty_rule': 'replace_with_occupied_value',
        'count_ascendant_as_occupant': False,
        'source': 'Vedic Astrology: An Integrated Approach, 12.7.2',
        'source_url': 'https://lakshminarayanlenasia.com/articles/vedic-astrology-an-integrated-approach2.pdf',
    },
    'parasharas_light_7': {
        'label': "Parashara's Light 7.0.3 worked-report convention (inferred from published tables)",
        'mixed_higher_empty_rule': 'subtract_occupied_value',
        'count_ascendant_as_occupant': True,
        'source': "Parashara's Light 7.0.3 Sample Report 5, pp. 14–18",
        'source_url': 'https://www.astrograha.com/Content/AstrologyReports/Circular-Astrology-Report.pdf',
    },
}
SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
              'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
NAKSHATRA_NAMES = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha',
    'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha',
    'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
    'Uttara Bhadrapada', 'Revati',
]


def _safe_gemini_response_text(response):
    """
    Read text from a google-generativeai GenerateContentResponse.
    Blocked or empty candidates often make .text raise ValueError.
    """
    if response is None:
        return None, "empty response"
    try:
        text = response.text
    except (ValueError, AttributeError) as e:
        detail = str(e)
        try:
            pf = getattr(response, "prompt_feedback", None)
            if pf is not None:
                detail = f"{detail} | prompt_feedback={pf}"
            cands = getattr(response, "candidates", None) or []
            for c in cands:
                fr = getattr(c, "finish_reason", None)
                if fr is not None:
                    detail = f"{detail} | finish_reason={fr}"
                    break
        except Exception:
            pass
        return None, detail
    if text is None or not str(text).strip():
        return None, "model returned empty text"
    return str(text).strip(), None


class AshtakavargaCalculator:
    def __init__(self, birth_data, chart_data, reduction_profile='pvr_narasimha_rao'):
        self.birth_data = birth_data
        self.chart_data = chart_data
        self.planets = chart_data['planets']
        if reduction_profile not in EKADHIPATYA_PROFILES:
            raise ValueError(
                f"Unknown Ekadhipatya profile {reduction_profile!r}; "
                f"expected one of {sorted(EKADHIPATYA_PROFILES)}"
            )
        self.reduction_profile = reduction_profile
        self.ekadhipatya_profile = EKADHIPATYA_PROFILES[reduction_profile]
        
        # Classical Bhinnashtakavarga rules from Brihat Jataka, Chapter IX
        # (same fixed totals also summarized by B.V. Raman's Ashtakavarga tables).
        self.contribution_rules = {
            'Sun': {
                'Sun': [1, 2, 4, 7, 8, 9, 10, 11],
                'Moon': [3, 6, 10, 11],
                'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'Mercury': [3, 5, 6, 9, 10, 11, 12],
                'Jupiter': [5, 6, 9, 11],
                'Venus': [6, 7, 12],
                'Saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'Ascendant': [3, 4, 6, 10, 11, 12]
            },
            'Moon': {
                'Sun': [3, 6, 7, 8, 10, 11],
                'Moon': [1, 3, 6, 7, 10, 11],
                'Mars': [2, 3, 5, 6, 9, 10, 11],
                'Mercury': [1, 3, 4, 5, 7, 8, 10, 11],
                'Jupiter': [1, 4, 7, 8, 10, 11, 12],
                'Venus': [3, 4, 5, 7, 9, 10, 11],
                'Saturn': [3, 5, 6, 11],
                'Ascendant': [3, 6, 10, 11]
            },
            'Mars': {
                'Sun': [3, 5, 6, 10, 11],
                'Moon': [3, 6, 11],
                'Mars': [1, 2, 4, 7, 8, 10, 11],
                'Mercury': [3, 5, 6, 11],
                'Jupiter': [6, 10, 11, 12],
                'Venus': [6, 8, 11, 12],
                'Saturn': [1, 4, 7, 8, 9, 10, 11],
                'Ascendant': [1, 3, 6, 10, 11]
            },
            'Mercury': {
                'Sun': [5, 6, 9, 11, 12],
                'Moon': [2, 4, 6, 8, 10, 11],
                'Mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'Mercury': [1, 3, 5, 6, 9, 10, 11, 12],
                'Jupiter': [6, 8, 11, 12],
                'Venus': [1, 2, 3, 4, 5, 8, 9, 11],
                'Saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'Ascendant': [1, 2, 4, 6, 8, 10, 11]
            },
            'Jupiter': {
                'Sun': [1, 2, 3, 4, 7, 8, 9, 10, 11],
                'Moon': [2, 5, 7, 9, 11],
                'Mars': [1, 2, 4, 7, 8, 10, 11],
                'Mercury': [1, 2, 4, 5, 6, 9, 10, 11],
                'Jupiter': [1, 2, 3, 4, 7, 8, 10, 11],
                'Venus': [2, 5, 6, 9, 10, 11],
                'Saturn': [3, 5, 6, 12],
                'Ascendant': [1, 2, 4, 5, 6, 7, 9, 10, 11]
            },
            'Venus': {
                'Sun': [8, 11, 12],
                'Moon': [1, 2, 3, 4, 5, 8, 9, 11, 12],
                'Mars': [3, 5, 6, 9, 11, 12],
                'Mercury': [3, 5, 6, 9, 11],
                'Jupiter': [5, 8, 9, 10, 11],
                'Venus': [1, 2, 3, 4, 5, 8, 9, 10, 11],
                'Saturn': [3, 4, 5, 8, 9, 10, 11],
                'Ascendant': [1, 2, 3, 4, 5, 8, 9, 11]
            },
            'Saturn': {
                'Sun': [1, 2, 4, 7, 8, 10, 11],
                'Moon': [3, 6, 11],
                'Mars': [3, 5, 6, 10, 11, 12],
                'Mercury': [6, 8, 9, 10, 11, 12],
                'Jupiter': [5, 6, 11, 12],
                'Venus': [6, 11, 12],
                'Saturn': [3, 5, 6, 11],
                'Ascendant': [1, 3, 4, 6, 10, 11]
            }
        }

        # Classical Lagna Bhinnashtakavarga target (49 total bindus).
        # Source used for this helper: Parasara tradition as summarized in
        # "Secrets of Ashtakavarga" (and explicitly noted there as a Lagna-only
        # addition outside the standard 337-point 7-planet SAV scheme).
        self.lagna_contribution_rules = {
            'Sun': [3, 4, 6, 10, 11, 12],
            'Moon': [3, 6, 10, 11, 12],
            'Mars': [1, 3, 6, 10, 11],
            'Mercury': [1, 2, 4, 6, 8, 10, 11],
            'Jupiter': [1, 2, 4, 5, 6, 7, 9, 10, 11],
            'Venus': [1, 2, 3, 4, 5, 8, 9],
            'Saturn': [1, 3, 4, 6, 10, 11],
            'Ascendant': [3, 6, 10, 11]
        }
    
    def calculate_individual_ashtakavarga(self, target_planet):
        """Calculate individual Ashtakavarga for a specific planet using authentic Vedic rules"""
        if target_planet not in self.contribution_rules:
            return {}
        
        # Initialize bindu array for 12 signs
        bindus = [0] * 12
        
        # Get rules for this target planet
        rules = self.contribution_rules[target_planet]
        
        # Check each contributor (Sun, Moon, Mars, etc.)
        for contributor, beneficial_houses in rules.items():
            # Get contributor's position
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30)
            else:
                contributor_sign = self.planets[contributor]['sign']
            
            # Check each beneficial house from contributor
            for house_num in beneficial_houses:
                # Calculate which sign this house falls in
                target_sign = (contributor_sign + house_num - 1) % 12
                bindus[target_sign] += 1  # Add bindu (can be multiple from different contributors)
        
        return {
            'planet': target_planet,
            'bindus': {i: bindus[i] for i in range(12)},
            'total': sum(bindus)
        }

    def calculate_individual_ashtakavarga_trace(self, target_planet):
        """
        Contributor-level trace for a target planet's Bhinnashtakavarga.
        Useful for validating sign-wise differences against external references.
        """
        if target_planet not in self.contribution_rules:
            return {}

        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

        bindus = [0] * 12
        contributions = {i: [] for i in range(12)}
        rules = self.contribution_rules[target_planet]

        for contributor, beneficial_houses in rules.items():
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30)
            else:
                contributor_sign = self.planets[contributor]['sign']

            for house_num in beneficial_houses:
                target_sign = (contributor_sign + house_num - 1) % 12
                bindus[target_sign] += 1
                contributions[target_sign].append({
                    'contributor': contributor,
                    'house_from_contributor': house_num,
                    'contributor_sign': contributor_sign,
                    'contributor_sign_name': sign_names[contributor_sign],
                })

        return {
            'planet': target_planet,
            'bindus': {i: bindus[i] for i in range(12)},
            'total': sum(bindus),
            'contributions_by_sign': {
                str(i): {
                    'sign_name': sign_names[i],
                    'count': bindus[i],
                    'contributions': contributions[i],
                }
                for i in range(12)
            },
        }

    def calculate_prastara_ashtakavarga(self, target_planet):
        """Return the classical 8×12 contributor matrix behind one BAV.

        A value of one means the contributor (and therefore its Kakshya) gives
        a rekha/bindu to the target planet in that zodiac sign.
        """
        if target_planet not in self.contribution_rules:
            return {}
        matrix = {contributor: {str(sign): 0 for sign in range(12)} for contributor in KAKSHYA_RULERS}
        for contributor, beneficial_houses in self.contribution_rules[target_planet].items():
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30) % 12
            else:
                contributor_sign = int(self.planets[contributor]['sign']) % 12
            for house_num in beneficial_houses:
                sign = (contributor_sign + house_num - 1) % 12
                matrix[contributor][str(sign)] = 1
        sign_totals = {
            str(sign): sum(matrix[contributor][str(sign)] for contributor in KAKSHYA_RULERS)
            for sign in range(12)
        }
        return {
            'planet': target_planet,
            'contributors': KAKSHYA_RULERS,
            'matrix': matrix,
            'sign_totals': sign_totals,
        }

    def calculate_kakshya_activation(self, target_planet, longitude):
        """Resolve an exact longitude against a target planet's Prastara AV."""
        prastara = self.calculate_prastara_ashtakavarga(target_planet)
        if not prastara:
            return {}
        normalized = float(longitude) % 360.0
        sign = int(normalized // 30) % 12
        degree = normalized - sign * 30
        index = min(7, int(degree // 3.75))
        ruler = KAKSHYA_RULERS[index]
        start = index * 3.75
        end = (index + 1) * 3.75
        bindu = int(prastara['matrix'][ruler][str(sign)])
        return {
            'planet': target_planet,
            'longitude': round(normalized, 8),
            'sign_id': sign,
            'sign': SIGN_NAMES[sign],
            'degree_in_sign': round(degree, 8),
            'kakshya_number': index + 1,
            'kakshya_ruler': ruler,
            'start_degree': start,
            'end_degree': end,
            'interval': '[start, end)',
            'bindu': bindu,
            'active': bindu == 1,
            'sign_bav_total': int(prastara['sign_totals'][str(sign)]),
        }

    @staticmethod
    def apply_trikona_shodhana(values):
        """Apply Parashara's trinal reduction to a 12-sign BAV vector."""
        reduced = [int(values[i] if not isinstance(values, dict) else values.get(i, values.get(str(i), 0))) for i in range(12)]
        trace = []
        for signs in TRIKONA_GROUPS:
            before = [reduced[sign] for sign in signs]
            minimum = min(before)
            if minimum == 0:
                action = 'unchanged_zero_present'
                after = before[:]
            else:
                action = 'subtract_minimum'
                after = [value - minimum for value in before]
                for sign, value in zip(signs, after):
                    reduced[sign] = value
            trace.append({
                'sign_ids': list(signs),
                'signs': [SIGN_NAMES[sign] for sign in signs],
                'before': before,
                'minimum': minimum,
                'after': after,
                'action': action,
            })
        return reduced, trace

    def apply_ekadhipatya_shodhana(self, values):
        """Apply the selected co-lordship reduction after Trikona Shodhana.

        P.V.R. Narasimha Rao and Parashara's Light agree on most branches but
        differ when an empty sign has the larger value. The published
        Parashara's Light tables can only be reproduced when Lagna is also
        treated as occupancy. These are named profiles rather than silently
        blended rules. Nodes are excluded.
        """
        reduced = [int(values[i] if not isinstance(values, dict) else values.get(i, values.get(str(i), 0))) for i in range(12)]
        occupants = {sign: [] for sign in range(12)}
        for planet in CLASSICAL_PLANETS:
            occupants[int(self.planets[planet]['sign']) % 12].append(planet)
        if self.ekadhipatya_profile['count_ascendant_as_occupant']:
            ascendant_sign = int(float(self.chart_data['ascendant']) // 30) % 12
            occupants[ascendant_sign].append('Ascendant')
        trace = []
        for lord, signs in EKADHIPATYA_PAIRS.items():
            left, right = signs
            before = [reduced[left], reduced[right]]
            left_occupied = bool(occupants[left])
            right_occupied = bool(occupants[right])
            action = 'unchanged'
            if before[0] == 0 or before[1] == 0:
                action = 'unchanged_zero_present'
            elif left_occupied and right_occupied:
                action = 'unchanged_both_occupied'
            elif left_occupied != right_occupied:
                occupied = left if left_occupied else right
                empty = right if left_occupied else left
                if reduced[empty] > reduced[occupied]:
                    if self.ekadhipatya_profile['mixed_higher_empty_rule'] == 'subtract_occupied_value':
                        reduced[empty] -= reduced[occupied]
                        action = 'occupied_value_subtracted_from_empty'
                    else:
                        reduced[empty] = reduced[occupied]
                        action = 'empty_reduced_to_occupied_value'
                else:
                    reduced[empty] = 0
                    action = 'empty_reduced_to_zero'
            elif before[0] == before[1]:
                reduced[left] = reduced[right] = 0
                action = 'both_empty_equal_reduced_to_zero'
            elif before[0] > before[1]:
                reduced[left] = reduced[right]
                action = 'both_empty_higher_reduced_to_lower'
            else:
                reduced[right] = reduced[left]
                action = 'both_empty_higher_reduced_to_lower'
            trace.append({
                'lord': lord,
                'sign_ids': [left, right],
                'signs': [SIGN_NAMES[left], SIGN_NAMES[right]],
                'occupants': [occupants[left], occupants[right]],
                'before': before,
                'after': [reduced[left], reduced[right]],
                'action': action,
                'profile': self.reduction_profile,
            })
        return reduced, trace

    def calculate_shodhya_pinda(self, target_planet):
        """Calculate fully reduced BAV, Rashi/Graha Pinda and Shodhya Pinda."""
        bav = self.calculate_individual_ashtakavarga(target_planet)
        if not bav:
            return {}
        raw = [int(bav['bindus'][sign]) for sign in range(12)]
        trikona, trikona_trace = self.apply_trikona_shodhana(raw)
        shodhita, ekadhipatya_trace = self.apply_ekadhipatya_shodhana(trikona)
        rashi_products = [shodhita[sign] * RASHI_MULTIPLIERS[sign] for sign in range(12)]
        graha_products = []
        for planet in CLASSICAL_PLANETS:
            sign = int(self.planets[planet]['sign']) % 12
            graha_products.append({
                'planet': planet,
                'sign_id': sign,
                'sign': SIGN_NAMES[sign],
                'reduced_bindus': shodhita[sign],
                'multiplier': GRAHA_MULTIPLIERS[planet],
                'product': shodhita[sign] * GRAHA_MULTIPLIERS[planet],
            })
        rashi_pinda = sum(rashi_products)
        graha_pinda = sum(row['product'] for row in graha_products)
        return {
            'planet': target_planet,
            'reduction_profile': self.reduction_profile,
            'reduction_profile_details': self.ekadhipatya_profile,
            'raw_bav': {str(i): raw[i] for i in range(12)},
            'after_trikona': {str(i): trikona[i] for i in range(12)},
            'after_ekadhipatya': {str(i): shodhita[i] for i in range(12)},
            'trikona_trace': trikona_trace,
            'ekadhipatya_trace': ekadhipatya_trace,
            'rashi_multipliers': {str(i): RASHI_MULTIPLIERS[i] for i in range(12)},
            'rashi_products': {str(i): rashi_products[i] for i in range(12)},
            'graha_products': graha_products,
            'rashi_pinda': rashi_pinda,
            'graha_pinda': graha_pinda,
            'shodhya_pinda': rashi_pinda + graha_pinda,
        }

    def calculate_shodhya_timing(self, target_planet, house_from_planet):
        """Calculate Parashara's nakshatra/rashi transit trigger for one house."""
        pinda = self.calculate_shodhya_pinda(target_planet)
        if not pinda:
            return {}
        source_sign = int(self.planets[target_planet]['sign']) % 12
        target_sign = (source_sign + int(house_from_planet) - 1) % 12
        rekhas = int(pinda['raw_bav'][str(target_sign)])
        product = rekhas * int(pinda['shodhya_pinda'])
        nakshatra_number = product % 27 or 27
        rashi_number = product % 12 or 12
        vimshottari_group = [((nakshatra_number - 1 + offset) % 27) + 1 for offset in (0, 9, 18)]
        rashi_trines = [((rashi_number - 1 + offset) % 12) + 1 for offset in (0, 4, 8)]
        return {
            'planet': target_planet,
            'reduction_profile': pinda.get('reduction_profile', self.reduction_profile),
            'reduction_profile_details': pinda.get('reduction_profile_details', self.ekadhipatya_profile),
            'house_from_planet': int(house_from_planet),
            'source_sign_id': source_sign,
            'source_sign': SIGN_NAMES[source_sign],
            'target_sign_id': target_sign,
            'target_sign': SIGN_NAMES[target_sign],
            'raw_rekhas': rekhas,
            'shodhya_pinda': pinda['shodhya_pinda'],
            'product': product,
            'nakshatra_number': nakshatra_number,
            'nakshatra': NAKSHATRA_NAMES[nakshatra_number - 1],
            'vimshottari_group_numbers': vimshottari_group,
            'vimshottari_group': [NAKSHATRA_NAMES[number - 1] for number in vimshottari_group],
            'rashi_number': rashi_number,
            'rashi': SIGN_NAMES[rashi_number - 1],
            'rashi_trine_numbers': rashi_trines,
            'rashi_trines': [SIGN_NAMES[number - 1] for number in rashi_trines],
        }

    def calculate_advanced_ashtakavarga(self):
        """Return production-ready Prastara, Kakshya and Shodhya evidence."""
        pindas = {planet: self.calculate_shodhya_pinda(planet) for planet in CLASSICAL_PLANETS}
        return {
            'schema_version': 'ashtakavarga.advanced.v1',
            'convention': {
                'school': self.ekadhipatya_profile['label'],
                'reduction_profile': self.reduction_profile,
                'reduction_profile_source': self.ekadhipatya_profile['source'],
                'reduction_profile_source_url': self.ekadhipatya_profile['source_url'],
                'mixed_higher_empty_rule': self.ekadhipatya_profile['mixed_higher_empty_rule'],
                'count_ascendant_as_occupant': self.ekadhipatya_profile['count_ascendant_as_occupant'],
                'reduction_order': ['Trikona Shodhana', 'Ekadhipatya Shodhana'],
                'occupancy_points': CLASSICAL_PLANETS + (['Ascendant'] if self.ekadhipatya_profile['count_ascendant_as_occupant'] else []),
                'kakshya_interval': '[start, end)',
            },
            'prastara': {planet: self.calculate_prastara_ashtakavarga(planet) for planet in CLASSICAL_PLANETS},
            'natal_kakshya': {
                planet: self.calculate_kakshya_activation(planet, self.planets[planet]['longitude'])
                for planet in CLASSICAL_PLANETS
            },
            'shodhya_pinda': pindas,
            'classical_timing': {
                'father': self.calculate_shodhya_timing('Sun', 9),
                'mother': self.calculate_shodhya_timing('Moon', 4),
                'siblings': self.calculate_shodhya_timing('Mars', 3),
                'profession': self.calculate_shodhya_timing('Mercury', 10),
                'children': self.calculate_shodhya_timing('Jupiter', 5),
                'marriage': self.calculate_shodhya_timing('Venus', 7),
                'longevity': self.calculate_shodhya_timing('Saturn', 8),
            },
        }
    
    def calculate_sarvashtakavarga(self):
        """Calculate Sarvashtakavarga (combined chart)"""
        sarva = {i: 0 for i in range(12)}
        individual_charts = {}
        
        # Calculate for all planets
        planets = CLASSICAL_PLANETS
        
        for planet in planets:
            chart = self.calculate_individual_ashtakavarga(planet)
            individual_charts[planet] = chart
            
            # Add to Sarvashtakavarga
            for sign, bindus in chart['bindus'].items():
                sarva[sign] += bindus
        
        # Convert keys to strings for consistent API response
        sarva_str_keys = {str(k): v for k, v in sarva.items()}
        
        return {
            'sarvashtakavarga': sarva_str_keys,
            'total_bindus': sum(sarva.values()),
            'individual_charts': individual_charts,
            'lagna_chart': self.calculate_lagna_ashtakavarga()
        }

    def calculate_lagna_ashtakavarga(self):
        """Calculate classical Lagna Bhinnashtakavarga (target total = 49)."""
        bindus = [0] * 12
        for contributor, beneficial_houses in self.lagna_contribution_rules.items():
            if contributor == 'Ascendant':
                contributor_sign = int(self.chart_data['ascendant'] / 30)
            else:
                contributor_sign = self.planets[contributor]['sign']
            for house_num in beneficial_houses:
                target_sign = (contributor_sign + house_num - 1) % 12
                bindus[target_sign] += 1
        return {
            'planet': 'Lagna',
            'bindus': {i: bindus[i] for i in range(12)},
            'total': sum(bindus)
        }
    
    def get_ashtakavarga_analysis(self, chart_type='lagna'):
        """Get analysis based on chart type"""
        if chart_type == 'lagna':
            return self._analyze_lagna_ashtakavarga()
        elif chart_type == 'navamsa':
            return self._analyze_navamsa_ashtakavarga()
        elif chart_type == 'transit':
            return self._analyze_transit_ashtakavarga()
        else:
            return self._analyze_general_ashtakavarga()
    
    def _analyze_lagna_ashtakavarga(self):
        """Analyze Ashtakavarga for Lagna chart"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        strongest_sign = int(max(bindus, key=bindus.get))
        weakest_sign = int(min(bindus, key=bindus.get))
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Get ascendant sign for personalized analysis
        asc_sign = int(self.chart_data['ascendant'] / 30)
        
        # House meanings for life analysis
        house_meanings = {
            0: 'personality and health', 1: 'wealth and family', 2: 'communication and siblings',
            3: 'home and mother', 4: 'education and children', 5: 'health and enemies',
            6: 'marriage and partnerships', 7: 'longevity and transformation', 8: 'fortune and dharma',
            9: 'career and reputation', 10: 'gains and friendships', 11: 'expenses and spirituality'
        }
        
        recommendations = []
        
        # Analyze each sign relative to ascendant
        for sign, count in bindus.items():
            sign_num = int(sign) if isinstance(sign, str) else sign
            house_num = (sign_num - asc_sign) % 12
            house_meaning = house_meanings[house_num]
            
            if count >= 30:
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign_num]}) has {count} bindus - Strong vitality and confidence. Good health and leadership abilities.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign_num]}) has {count} bindus - Strong financial potential. Good for wealth accumulation and family harmony.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong marriage prospects. Harmonious partnerships and business relationships.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong career potential. Recognition, authority, and professional success.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Excellent for gains and friendships. Strong network and income potential.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong spiritual inclination. Good for charitable giving and letting go of attachments.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign_num]}) has {count} bindus - Excellent communication skills. Strong bonds with siblings.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong connection with home and mother. Good property prospects.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Excellent for education and children. Creative abilities.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Good health and ability to overcome obstacles.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong transformative abilities. Good longevity.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong fortune and dharmic path. Good for higher learning.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Strong support for {house_meaning}.")
            elif count <= 25:
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign_num]}) has {count} bindus - Focus on health and self-care. Build confidence gradually.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign_num]}) has {count} bindus - Be careful with finances. Plan investments wisely.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign_num]}) has {count} bindus - Work on communication skills. Strengthen sibling relationships.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Focus on home harmony. Be patient with mother's health.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Education may need extra effort. Be patient with children.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Focus on health maintenance. Avoid unnecessary conflicts.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Marriage may need extra effort. Work on relationship skills.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Be prepared for life changes. Focus on inner strength.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Develop spiritual practices. Be patient with fortune.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Career growth requires patience. Build skills steadily.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Focus on building genuine friendships. Be cautious with investments.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Control unnecessary expenses. Develop spiritual practices for inner peace.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - {house_meaning.title()} may need extra attention.")
            else:
                # Average strength houses (26-29 bindus)
                if house_num == 0:
                    recommendations.append(f"Your {house_num + 1}st house ({sign_names[sign_num]}) has {count} bindus - Moderate health and confidence. Maintain good habits.")
                elif house_num == 1:
                    recommendations.append(f"Your {house_num + 1}nd house ({sign_names[sign_num]}) has {count} bindus - Steady financial growth. Balance saving and spending.")
                elif house_num == 2:
                    recommendations.append(f"Your {house_num + 1}rd house ({sign_names[sign_num]}) has {count} bindus - Good communication abilities. Keep nurturing sibling bonds.")
                elif house_num == 3:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Stable home environment. Maintain family connections.")
                elif house_num == 4:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Steady progress in education. Good relationship with children.")
                elif house_num == 5:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Moderate health. Handle conflicts diplomatically.")
                elif house_num == 6:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Stable relationships. Work on deeper connections.")
                elif house_num == 7:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Gradual transformation. Embrace change positively.")
                elif house_num == 8:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Steady fortune. Continue dharmic practices.")
                elif house_num == 9:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Consistent career progress. Keep building reputation.")
                elif house_num == 10:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Moderate gains. Maintain good friendships.")
                elif house_num == 11:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Balanced expenses. Continue spiritual practices.")
                else:
                    recommendations.append(f"Your {house_num + 1}th house ({sign_names[sign_num]}) has {count} bindus - Moderate support for {house_meaning}.")
        
        return {
            'strongest_sign': {
                'sign': strongest_sign,
                'name': sign_names[strongest_sign],
                'bindus': bindus[str(strongest_sign)]
            },
            'weakest_sign': {
                'sign': weakest_sign,
                'name': sign_names[weakest_sign],
                'bindus': bindus[str(weakest_sign)]
            },
            'recommendations': recommendations
        }
    
    def _analyze_navamsa_ashtakavarga(self, d9_chart_data=None):
        """Analyze using Navamsa positions against Rashi SAV strength"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Get D9 positions if available, otherwise use D1 as fallback
        if d9_chart_data and 'planets' in d9_chart_data:
            venus_sign = d9_chart_data['planets']['Venus']['sign']
            jupiter_sign = d9_chart_data['planets']['Jupiter']['sign']
        else:
            # Fallback to D1 positions with note
            venus_sign = self.planets['Venus']['sign']
            jupiter_sign = self.planets['Jupiter']['sign']
        
        recommendations = []
        venus_bindus = bindus[str(venus_sign)]
        jupiter_bindus = bindus[str(jupiter_sign)]
        
        if venus_bindus >= 28:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {venus_bindus} bindus - Excellent marriage compatibility and romantic happiness.")
        elif venus_bindus >= 25:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {venus_bindus} bindus - Good marriage prospects with some adjustments needed.")
        else:
            recommendations.append(f"Venus in {sign_names[venus_sign]} has {venus_bindus} bindus - Marriage requires patience and understanding.")
            
        if jupiter_bindus >= 28:
            recommendations.append(f"Jupiter in {sign_names[jupiter_sign]} has {jupiter_bindus} bindus - Strong spiritual growth and wisdom development.")
        else:
            recommendations.append(f"Jupiter in {sign_names[jupiter_sign]} has {jupiter_bindus} bindus - Spiritual progress through dedicated practice.")
        
        return {
            'focus': 'Marriage and spiritual growth',
            'analysis': 'Navamsa Ashtakavarga reveals marriage compatibility and spiritual potential',
            'recommendations': recommendations
        }
    
    def _analyze_transit_ashtakavarga(self):
        """Analyze for transit context"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Find best timing signs
        best_signs = [int(sign) for sign, count in bindus.items() if count >= 30]
        avoid_signs = [int(sign) for sign, count in bindus.items() if count <= 25]
        
        recommendations = []
        if best_signs:
            recommendations.append(f"When planets transit through {', '.join([sign_names[s] for s in best_signs])}, you'll have strong support for new projects and important decisions.")
        if avoid_signs:
            recommendations.append(f"When planets transit through {', '.join([sign_names[s] for s in avoid_signs])}, be more cautious and avoid major life changes.")
        
        return {
            'focus': 'Timing for activities and decisions',
            'analysis': 'Transit Ashtakavarga shows when planetary energies are most supportive',
            'recommendations': recommendations
        }
    
    def _analyze_general_ashtakavarga(self):
        """General analysis for other charts"""
        sarva = self.calculate_sarvashtakavarga()
        bindus = sarva['sarvashtakavarga']
        
        strong_count = sum(1 for count in bindus.values() if count >= 30)
        weak_count = sum(1 for count in bindus.values() if count <= 25)
        
        return {
            'focus': 'Overall planetary strength distribution',
            'analysis': f'Your chart has {strong_count} areas of natural strength and {weak_count} areas needing attention',
            'recommendations': [f"Focus on developing your {strong_count} strong areas while gradually improving the {weak_count} weaker areas through conscious effort."]
        }
    
    def generate_life_predictions(self, dasha_data, transit_data):
        """Generate life predictions using Vinay Aditya's 'Dots of Destiny' methodology via Gemini AI"""
        try:
            import google.generativeai as genai
            import os
            import json

            from utils.admin_settings import CHAT_LLM_DEEPSEEK, GEMINI_MODEL_OPTIONS, get_analysis_llm_vendor, get_gemini_analysis_model

            # Prepare comprehensive data payload
            sarva = self.calculate_sarvashtakavarga()
            bindus = sarva['sarvashtakavarga']
            individual_charts = sarva['individual_charts']
            sav_house_reference = self._sav_reference_for_lagna_and_signs(bindus)
            
            # Build complete data package
            data_payload = {
                "birth_data": {
                    "name": self.birth_data.name,
                    "date": self.birth_data.date,
                    "time": self.birth_data.time,
                    "place": getattr(self.birth_data, 'place', '')
                },
                "natal_chart": {
                    "ascendant": self.chart_data['ascendant'],
                    "planets": self.chart_data['planets']
                },
                "sarvashtakavarga": bindus,
                "sarvashtakavarga_key_legend": (
                    "Each key is a ZODIAC SIGN index: 0=Aries, 1=Taurus, 2=Gemini, 3=Cancer, 4=Leo, 5=Virgo, "
                    "6=Libra, 7=Scorpio, 8=Sagittarius, 9=Capricorn, 10=Aquarius, 11=Pisces. "
                    "These are NOT house numbers from lagna."
                ),
                "sav_per_house_from_ascendant": sav_house_reference,
                "bhinnashtakavarga": individual_charts,
                "current_dashas": dasha_data,
                "current_transits": transit_data,
                "analysis_date": self._get_current_date()
            }
            
            # Create Vinay Aditya methodology prompt
            prompt = f"""
Role: You are an expert Vedic Astrologer specializing in the Ashtakavarga system, specifically applying the principles from Vinay Aditya's book "Dots of Destiny: Applications of Ashtakavarga" and the teachings of K.N. Rao.

Task: Analyze the provided JSON data to make predictions for the user's current life phase.

CRITICAL — SARVASHTAKAVARGA NUMBERS AND HOUSES:
- The object `sarvashtakavarga` uses keys "0" through "11" for the TWELVE ZODIAC SIGNS (fixed wheel), NOT for "House 1" through "House 12" from the ascendant.
- Whenever you mention a HOUSE NUMBER (1-12 counted from the ascendant / lagna) together with a bindu count, you MUST take `sarvashtakavarga_bindus` ONLY from `sav_per_house_from_ascendant.houses` for that exact `house_from_ascendant`. The `sign_occupied` field must match the same row.
- Never assign a bindu count from one house or sign to a different house. Never invent or round bindu values.
- For Saturn/Jupiter transit strength vs SAV, use `sav_per_zodiac_sign` inside `sav_per_house_from_ascendant` together with the transit sign (derive sign from transit longitude).

Methodology:

1. Sarvashtakavarga (SAV) Analysis: Using ONLY `sav_per_house_from_ascendant.houses`, list strong houses (typically >30 bindus) and weak houses (typically <25). In `strong_areas` / `challenging_areas`, each string MUST follow: "House H (X bindus, SignName) — …" where H, X, and SignName are copied exactly from one row.

2. Transit Logic (The Trigger):
   - Saturn: Analyze Saturn's current transit. If it is in a sign with low SAV points (<25), predict a period of struggle or karmic settlement. If >30, predict structural growth.
   - Jupiter: If Jupiter transits a high-point sign (>30), predict expansion and opportunity.

3. Dasha Synthesis: Weight the Dasha Lord's results based on the Ashtakavarga strength of its natal house and the house it rules; mention antardasha only if clearly supported by the payload.

4. Kakshya Analysis (Prastar): If precise planetary degrees are available, check which Kakshya (orbital zone) Saturn and Jupiter are transiting. If they transit a Kakshya with a Bindu, predict immediate results (as per Vinay Aditya's Prastar rules).

5. Bhinnashtakavarga (BAV): Use `bhinnashtakavarga` totals and bindu patterns for at least the ascendant lord, the Moon, and the 10th-house lord (from lagna). Explain how their personal Ashtakavarga modifies the raw SAV story (e.g. a weak house in SAV but strong in that graha's BAV suggests partial relief when that planet is active).

6. Rahu and Ketu: Comment briefly on nodes transiting high vs low SAV signs (psychological and event tone), without inventing degrees.

7. Depth and tone: Avoid generic horoscope filler. Every paragraph should tie to concrete houses/bindus or named grahas from the JSON. Prefer practical, specific guidance over vague encouragement.

8. `timing_highlights`: Give 3–5 forward-looking windows (e.g. "next ~3 months", "when Jupiter enters …") grounded in current transits + SAV of the sign being entered.

Data:
{json.dumps(data_payload, indent=2)}

Provide predictions in this JSON format (fill every top-level key; use substantial text, not one-liners):
{{
  "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings",
  "current_life_phase": "3–6 sentences: dasha + SAV + one transit hook",
  "sav_strength_analysis": {{
    "strong_areas": ["Example: House 12 (35 bindus, Gemini) — … (numbers and sign must match sav_per_house_from_ascendant.houses)"],
    "challenging_areas": ["Example: House 8 (22 bindus, Aquarius) — …"],
    "overall_pattern": "4–8 sentences weaving strong vs weak houses into a coherent life story"
  }},
  "life_domain_insights": {{
    "vitality_and_personality": "2–5 sentences (house 1; ascendant lord BAV if relevant)",
    "wealth_family_speech": "2–5 sentences (houses 2, 11 where applicable)",
    "courage_siblings_skills": "2–5 sentences (house 3)",
    "home_comfort_mother": "2–5 sentences (house 4)",
    "children_creativity_speculation": "2–5 sentences (house 5)",
    "health_service_obstacles": "2–5 sentences (house 6)",
    "partnerships_marriage": "2–5 sentences (house 7)",
    "longevity_shared_resources": "2–5 sentences (house 8)",
    "fortune_dharma_father": "2–5 sentences (house 9)",
    "career_reputation": "2–5 sentences (house 10; 10th lord BAV)",
    "gains_network_aspirations": "2–5 sentences (house 11)",
    "expenses_moksha_rest": "2–5 sentences (house 12)"
  }},
  "timing_highlights": [
    {{"window": "e.g. next 3–4 months", "focus": "what to push or avoid", "ashtakavarga_basis": "cite house/sign/bindu from data only"}}
  ],
  "transit_predictions": {{
    "saturn_influence": "4–8 sentences with sign + SAV bindus for Saturn's current sign",
    "jupiter_influence": "4–8 sentences with sign + SAV bindus for Jupiter's current sign",
    "rahu_ketu_influence": "2–4 sentences",
    "timing_recommendations": ["3–6 bullets, specific and tied to SAV/transits"]
  }},
  "dasha_analysis": {{
    "current_period_strength": "3–6 sentences",
    "expected_results": "4–8 sentences",
    "recommendations": ["3–6 specific recommendations"]
  }},
  "life_predictions": {{
    "next_6_months": "Substantial paragraph(s)",
    "next_year": "Substantial paragraph(s)",
    "major_themes": ["5–8 concrete themes tied to houses or grahas"]
  }},
  "remedial_measures": ["5–8 remedies: lifestyle, timing, or gentle practices tied to weak houses — avoid medical/legal claims"]
}}
"""
            
            # Generate predictions with error logging (try admin model, then stable fallbacks for Gemini)
            use_deepseek = get_analysis_llm_vendor() == CHAT_LLM_DEEPSEEK
            print(
                f"🔮 Calling {'DeepSeek' if use_deepseek else 'Gemini'} API for life predictions..."
            )
            print(f"📊 Prompt length: {len(prompt)} characters")
            print(f"📤 REQUEST PROMPT (preview):\n{prompt[:1000]}...")

            response_text = None
            last_model_error = None
            response = None
            model_names: list = []

            if use_deepseek:
                try:
                    from ai.analysis_llm_backend import build_analysis_llm_model

                    model, mn, _ = build_analysis_llm_model()
                    print(f"🎯 Trying model: {mn}")
                    response = model.generate_content(prompt)
                    response_text, extract_err = _safe_gemini_response_text(response)
                    if response_text:
                        print(f"✅ DeepSeek API call successful with {mn}")
                        print(f"📝 Response length: {len(response_text)} characters")
                        print(f"📥 RESPONSE TEXT (preview):\n{response_text[:1000]}...")
                    else:
                        last_model_error = extract_err or "no usable text"
                        print(f"⚠️ Model {mn}: {last_model_error}")
                except Exception as call_err:
                    last_model_error = f"{type(call_err).__name__}: {call_err}"
                    print(f"⚠️ DeepSeek call failed: {last_model_error}")
            else:
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    return {"error": "Gemini API key not configured"}

                genai.configure(api_key=api_key)
                preferred = get_gemini_analysis_model()
                model_names = [preferred] + [m[0] for m in GEMINI_MODEL_OPTIONS if m[0] != preferred]
                for model_name in model_names:
                    try:
                        print(f"🎯 Trying model: {model_name}")
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(prompt)
                        response_text, extract_err = _safe_gemini_response_text(response)
                        if response_text:
                            print(f"✅ Gemini API call successful with {model_name}")
                            print(f"📝 Response length: {len(response_text)} characters")
                            print(f"📥 RESPONSE TEXT (preview):\n{response_text[:1000]}...")
                            break
                        last_model_error = extract_err or "no usable text"
                        print(f"⚠️ Model {model_name}: {last_model_error}")
                    except Exception as call_err:
                        last_model_error = f"{type(call_err).__name__}: {call_err}"
                        print(f"⚠️ Model {model_name} failed: {last_model_error}")
                        continue

            if not response_text:
                tried = "DeepSeek" if use_deepseek else f"Gemini ({len(model_names)} model(s))"
                return {
                    "error": (
                        "Could not get a valid response from the configured analysis LLM "
                        f"({tried}). Last error: {last_model_error}"
                    ),
                    "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings",
                    "error_type": "LlmNoText",
                }

            # Parse JSON response
            try:
                # Find JSON block in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1

                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    predictions = json.loads(json_str)
                else:
                    print(f"⚠️ JSON parsing failed - no valid JSON block found")
                    print(f"📄 Full response: {response_text}")
                    predictions = {
                        "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings",
                        "raw_response": response_text,
                        "note": "AI response received but JSON parsing failed"
                    }
            except json.JSONDecodeError as je:
                print(f"⚠️ JSON decode error: {str(je)}")
                print(f"📄 JSON string attempted: {json_str[:500] if 'json_str' in locals() else 'N/A'}...")
                predictions = {
                    "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings",
                    "raw_response": response_text,
                    "note": "AI response received but JSON parsing failed"
                }
            
            return predictions
            
        except Exception as e:
            print(f"❌ Gemini API error: {type(e).__name__}: {str(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            
            # Specific error handling
            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                error_msg = "API quota exceeded. Please try again later."
            elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                error_msg = "API authentication failed. Please check configuration."
            elif "model" in str(e).lower() or "not found" in str(e).lower():
                error_msg = f"Gemini model not available: {str(e)}"
            else:
                error_msg = f"Gemini prediction generation failed: {str(e)}"
            
            return {
                "error": error_msg,
                "methodology": "Based on Vinay Aditya's 'Dots of Destiny: Applications of Ashtakavarga' and K.N. Rao's teachings",
                "error_type": type(e).__name__
            }

    def _sav_reference_for_lagna_and_signs(self, bindus_str_keyed):
        """
        SAV totals in this codebase are keyed by zodiac sign index 0=Aries ... 11=Pisces.
        The app UI shows houses 1-12 from the ascendant. The model must not confuse the two.
        """
        sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
        ]

        def pts(si):
            k = str(si)
            v = bindus_str_keyed.get(k)
            if v is None:
                v = bindus_str_keyed.get(si)
            return int(v) if v is not None else 0

        asc_deg = float(self.chart_data['ascendant'])
        asc_sign = int(asc_deg / 30) % 12

        houses = []
        for house in range(1, 13):
            sign_idx = (asc_sign + house - 1) % 12
            houses.append({
                "house_from_ascendant": house,
                "sign_occupied": sign_names[sign_idx],
                "sign_index_0_Aries_to_11_Pisces": sign_idx,
                "sarvashtakavarga_bindus": pts(sign_idx),
            })

        sav_per_zodiac_sign = {sign_names[i]: pts(i) for i in range(12)}

        return {
            "note": (
                "sarvashtakavarga keys 0-11 are ZODIAC SIGNS (not house numbers). "
                "For house-specific bindus, use only `houses` below."
            ),
            "ascendant_sign": sign_names[asc_sign],
            "ascendant_sign_index": asc_sign,
            "houses": houses,
            "sav_per_zodiac_sign": sav_per_zodiac_sign,
        }
    
    def _get_current_date(self):
        """Get current date for analysis"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d')
