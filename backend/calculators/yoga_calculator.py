from .base_calculator import BaseCalculator
from .aspect_calculator import AspectCalculator
from .classical_mangal_dosha import calculate_classical_mangal_dosha
from .classical_neecha_bhanga import calculate_classical_neecha_bhanga
from .classical_pitri_shapa import calculate_classical_pitri_shapa
from .classical_matri_shapa import calculate_classical_matri_shapa
from .nodal_enclosure_calculator import calculate_nodal_enclosure
from .planet_result_delivery import calculate_planet_result_delivery
from .classical_core_yogas import (
    amala as calculate_classical_amala,
    chandra_yogas as calculate_classical_chandra_yogas,
    dhana_yogas as calculate_classical_dhana_yogas,
    dharma_karma_yoga as calculate_classical_dharma_karma_yoga,
    gaja_kesari as calculate_classical_gaja_kesari,
    nabhasa_yogas as calculate_classical_nabhasa_yogas,
    pancha_mahapurusha as calculate_classical_pancha_mahapurusha,
    raj_yogas as calculate_classical_raj_yogas,
    saraswati as calculate_classical_saraswati,
    surya_yogas as calculate_classical_surya_yogas,
    viparita_yogas as calculate_classical_viparita_yogas,
)

class YogaCalculator(BaseCalculator):
    """Calculate various Vedic yogas and combinations"""
    
    def __init__(self, birth_data=None, chart_data=None):
        super().__init__(chart_data)
        
        self.SIGN_LORDS = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        # Initialize ascendant sign for dosha calculations
        self.ascendant_sign = int(chart_data.get('ascendant', 0) / 30) if chart_data else 0
        
        # Initialize aspect calculator
        self.aspect_calc = AspectCalculator(chart_data)
    
    def calculate_raj_yogas(self):
        """BPHS 34.11–15 Kendra–Trikona lord relationships."""
        return calculate_classical_raj_yogas(
            self.chart_data,
            self._get_house_lord,
            self.aspect_calc.get_aspecting_planets,
        )
    
    def calculate_dhana_yogas(self):
        """BPHS 41.2–15 special Dhana combinations."""
        return calculate_classical_dhana_yogas(
            self.chart_data,
            self.aspect_calc.get_aspecting_planets,
        )
    
    def calculate_panch_mahapurusha_yogas(self):
        """Phaladeepika 6.1 Pancha Mahapurusha formations."""
        return calculate_classical_pancha_mahapurusha(self.chart_data)
    
    def calculate_neecha_bhanga_yogas(self):
        """Calculate only Phaladeepika 7.26-30 Neecha Bhanga Raja Yogas."""
        yogas = []
        classical_results = calculate_classical_neecha_bhanga(self.chart_data)
        delivery_planets = (self.chart_data.get("planet_result_delivery") or {}).get("planets")
        if not isinstance(delivery_planets, dict):
            delivery_chart = dict(self.chart_data)
            delivery_chart["neecha_bhanga"] = classical_results
            delivery_planets = calculate_planet_result_delivery(delivery_chart)["planets"]
        for planet, result in classical_results.items():
            if not result["neecha_bhanga_present"]:
                continue
            conditions = result["conditions_met"]
            references = sorted({row["reference"] for row in conditions})
            yogas.append({
                # Existing client fields are retained.
                "name": "Neecha Bhanga Raja Yoga",
                "planet": planet,
                "planets": [planet],
                "house": self.chart_data["planets"][planet].get("house"),
                "houses": [self.chart_data["planets"][planet].get("house")],
                "strength": "Established",
                "description": (
                    f"{planet} is debilitated in {result['debilitation_sign']} and meets "
                    f"{len(conditions)} condition(s) stated in Phaladeepika 7.26-30."
                ),
                "reason": " ".join(row["description"] for row in conditions),
                # Additive structured fields for the new UI and downstream clients.
                "raja_yoga_present": True,
                "condition_count": len(conditions),
                "classical_conditions": conditions,
                "matched_rule_ids": result["matched_rule_ids"],
                "references": references,
                "classical_result": result["classical_result"],
                "source": result["source"],
                "result_delivery": delivery_planets.get(planet),
            })
        return yogas
    
    def calculate_gaja_kesari_yoga(self):
        """BPHS 36.3–4 Gaja Kesari, including its stated qualifiers."""
        return calculate_classical_gaja_kesari(
            self.chart_data,
            self.aspect_calc.get_aspecting_planets,
        )
    
    def calculate_amala_yoga(self):
        """BPHS 36.5–6 Amala, enforcing the text's exclusive benefic condition."""
        return calculate_classical_amala(self.chart_data)
    
    def calculate_viparita_raja_yogas(self):
        """Phaladeepika 6.57, including both stated formation branches."""
        return calculate_classical_viparita_yogas(
            self.chart_data,
            self._get_house_lord,
            self.aspect_calc.get_aspecting_planets,
        )
    
    def calculate_dharma_karma_yogas(self):
        """Phaladeepika 6.37 with its distinct two-lord conjunction."""
        return calculate_classical_dharma_karma_yoga(
            self.chart_data,
            self._get_house_lord,
        )
    
    def calculate_nabhasa_yogas(self):
        """BPHS 35 complete 32-name Nabhasa formation scheme."""
        return calculate_classical_nabhasa_yogas(self.chart_data)

    def _calculate_ashraya_yogas(self):
        """Calculate Ashraya Yogas (dependency-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        movable_signs = [0, 3, 6, 9]  # Aries, Cancer, Libra, Capricorn
        fixed_signs = [1, 4, 7, 10]  # Taurus, Leo, Scorpio, Aquarius
        dual_signs = [2, 5, 8, 11]  # Gemini, Virgo, Sagittarius, Pisces
        
        planet_signs = []
        for planet_name in classical_planets:
            if planet_name in planets:
                planet_signs.append(planets[planet_name].get('sign'))

        yogas = []
        
        if len(planet_signs) == 7:
            if all(s in movable_signs for s in planet_signs):
                yogas.append({
                    'name': 'Rajju Yoga',
                    'strength': 'Low',
                    'description': 'All planets in movable signs. Indicates a person who is fond of traveling and is of a jealous disposition.'
                })
            elif all(s in fixed_signs for s in planet_signs):
                yogas.append({
                    'name': 'Musala Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in fixed signs. Indicates a person who is proud, wealthy, and attached to their homeland.'
                })
            elif all(s in dual_signs for s in planet_signs):
                yogas.append({
                    'name': 'Nalika Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in dual signs. Indicates a person who is intelligent, wealthy, and has a fluctuating mind.'
                })
                
        return yogas


    def _calculate_akriti_yogas(self):
        """Calculate Akriti Yogas (shape-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        occupied_houses = set()
        for planet_name in classical_planets:
            if planet_name in planets:
                occupied_houses.add(planets[planet_name].get('house'))

        yogas = []

        # 1. Gada Yoga: All planets in two adjacent kendras.
        if len(occupied_houses) > 1 and all(h in [1,4] for h in occupied_houses) or \
           all(h in [4,7] for h in occupied_houses) or \
           all(h in [7,10] for h in occupied_houses) or \
           all(h in [10,1] for h in occupied_houses):
            yogas.append({
                'name': 'Gada Yoga',
                'strength': 'Medium',
                'description': 'All planets in two adjacent kendras. Indicates wealth and property.'
            })

        # 2. Sakata Yoga: All planets in the 1st and 7th houses.
        if len(occupied_houses) > 1 and all(h in [1, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Sakata Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 1st and 7th houses. Indicates a life of struggle with occasional bursts of fortune.'
            })

        # 3. Vihaga Yoga: All planets in the 4th and 10th houses.
        if len(occupied_houses) > 1 and all(h in [4, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Vihaga Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 4th and 10th houses. Indicates a person who is a wanderer.'
            })

        # 4. Shringataka Yoga: All planets in the 1st, 5th, and 9th houses.
        if len(occupied_houses) > 1 and all(h in [1, 5, 9] for h in occupied_houses):
            yogas.append({
                'name': 'Shringataka Yoga',
                'strength': 'High',
                'description': 'All planets in trikonas. Indicates a life of ease and comfort.'
            })

        # 5. Hala Yoga: All planets in the 2nd, 6th, and 10th; or 3rd, 7th, and 11th; or 4th, 8th, and 12th.
        if len(occupied_houses) > 1 and all(h in [2, 6, 10] for h in occupied_houses) or \
           all(h in [3, 7, 11] for h in occupied_houses) or \
           all(h in [4, 8, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Hala Yoga',
                'strength': 'Medium',
                'description': 'All planets in 2nd, 6th, 10th or 3rd, 7th, 11th or 4th, 8th, 12th. Indicates a person who is a farmer or works with the land.'
            })
            
        # 6. Vajra Yoga: Benefics in the 1st and 7th, malefics in the 4th and 10th.
        benefics = ['Venus', 'Jupiter', 'Mercury', 'Moon']
        malefics = ['Saturn', 'Mars', 'Sun']
        
        benefic_houses = set()
        malefic_houses = set()
        
        for planet in benefics:
            if planet in planets:
                benefic_houses.add(planets[planet].get('house'))
        
        for planet in malefics:
            if planet in planets:
                malefic_houses.add(planets[planet].get('house'))
                
        if all(h in [1, 7] for h in benefic_houses) and all(h in [4, 10] for h in malefic_houses):
            yogas.append({
                'name': 'Vajra Yoga',
                'strength': 'High',
                'description': 'Benefics in 1st and 7th, malefics in 4th and 10th. Indicates a powerful and influential person.'
            })
            
        # 7. Yava Yoga: Benefics in the 4th and 10th, malefics in the 1st and 7th.
        if all(h in [4, 10] for h in benefic_houses) and all(h in [1, 7] for h in malefic_houses):
            yogas.append({
                'name': 'Yava Yoga',
                'strength': 'High',
                'description': 'Benefics in 4th and 10th, malefics in 1st and 7th. Indicates a person with a difficult early life but success later.'
            })
            
        # 8. Kamala Yoga: All planets in the 1st, 4th, 7th, and 10th houses.
        if len(occupied_houses) > 1 and all(h in [1, 4, 7, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Kamala Yoga',
                'strength': 'High',
                'description': 'All planets in kendras. Indicates a person who is famous and wealthy.'
            })

        # 9. Vapi Yoga: All planets in Panapara houses (2, 5, 8, 11) or Apoklima houses (3, 6, 9, 12).
        if len(occupied_houses) > 1 and all(h in [2, 5, 8, 11] for h in occupied_houses) or \
           all(h in [3, 6, 9, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Vapi Yoga',
                'strength': 'Medium',
                'description': 'All planets in Panapara or Apoklima houses. Indicates a person who is secretive and may have hidden wealth.'
            })
            
        # 10. Yoopa Yoga: All planets in the 1st, 2nd, 3rd, and 4th houses.
        if len(occupied_houses) > 1 and all(h in [1, 2, 3, 4] for h in occupied_houses):
            yogas.append({
                'name': 'Yoopa Yoga',
                'strength': 'Medium',
                'description': 'All planets in the first four houses. Indicates a person who is religious and performs sacrifices.'
            })

        # 11. Sara Yoga: All planets in the 4th, 5th, 6th, and 7th houses.
        if len(occupied_houses) > 1 and all(h in [4, 5, 6, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Sara Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 4th, 5th, 6th, and 7th houses. Indicates a person who is strong and powerful.'
            })

        # 12. Sakti Yoga: All planets in the 7th, 8th, 9th, and 10th houses.
        if len(occupied_houses) > 1 and all(h in [7, 8, 9, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Sakti Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7th, 8th, 9th, and 10th houses. Indicates a person who is lazy and unhappy.'
            })
            
        # 13. Danda Yoga: All planets in the 10th, 11th, 12th, and 1st houses.
        if len(occupied_houses) > 1 and all(h in [10, 11, 12, 1] for h in occupied_houses):
            yogas.append({
                'name': 'Danda Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 10th, 11th, 12th, and 1st houses. Indicates a person who is poor and unfortunate.'
            })

        # 14. Nauka Yoga: All planets in the 7 houses from the 1st to the 7th.
        if len(occupied_houses) > 1 and all(h in [1, 2, 3, 4, 5, 6, 7] for h in occupied_houses):
            yogas.append({
                'name': 'Nauka Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 1st to the 7th. Indicates a person who is famous and wealthy.'
            })
            
        # 15. Koota Yoga: All planets in the 7 houses from the 4th to the 10th.
        if len(occupied_houses) > 1 and all(h in [4, 5, 6, 7, 8, 9, 10] for h in occupied_houses):
            yogas.append({
                'name': 'Koota Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 4th to the 10th. Indicates a person who is a liar and a cheat.'
            })
            
        # 16. Chatra Yoga: All planets in the 7 houses from the 7th to the 1st.
        if len(occupied_houses) > 1 and all(h in [7, 8, 9, 10, 11, 12, 1] for h in occupied_houses):
            yogas.append({
                'name': 'Chatra Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 7th to the 1st. Indicates a person who is a king or a minister.'
            })
            
        # 17. Chapa Yoga: All planets in the 7 houses from the 10th to the 4th.
        if len(occupied_houses) > 1 and all(h in [10, 11, 12, 1, 2, 3, 4] for h in occupied_houses):
            yogas.append({
                'name': 'Chapa Yoga',
                'strength': 'Medium',
                'description': 'All planets in the 7 houses from the 10th to the 4th. Indicates a person who is a hunter or a warrior.'
            })
            
        # 18. Ardha Chandra Yoga: All planets in the 7 houses starting from a house other than a Kendra.
        panapara_start = [2, 5, 8, 11]
        apoklima_start = [3, 6, 9, 12]
        
        for start_house in panapara_start + apoklima_start:
            house_range = [(start_house + i -1) % 12 + 1 for i in range(7)]
            if len(occupied_houses) > 1 and all(h in house_range for h in occupied_houses):
                 yogas.append({
                    'name': 'Ardha Chandra Yoga',
                    'strength': 'Medium',
                    'description': 'All planets in 7 consecutive houses starting from a non-kendra house. Indicates a person who is a commander or a leader.'
                })
                 break

        # 19. Samudra Yoga: All planets in the even houses (2, 4, 6, 8, 10, 12).
        if len(occupied_houses) > 1 and all(h in [2, 4, 6, 8, 10, 12] for h in occupied_houses):
            yogas.append({
                'name': 'Samudra Yoga',
                'strength': 'High',
                'description': 'All planets in even houses. Indicates a person who is wealthy and prosperous.'
            })

        # 20. Chakra Yoga: All planets in the odd houses (1, 3, 5, 7, 9, 11).
        if len(occupied_houses) > 1 and all(h in [1, 3, 5, 7, 9, 11] for h in occupied_houses):
            yogas.append({
                'name': 'Chakra Yoga',
                'strength': 'High',
                'description': 'All planets in odd houses. Indicates a person who is a king or a ruler.'
            })

        return yogas


    def _calculate_sankhya_yogas(self):
        """Calculate Sankhya Yogas (number-based)"""
        planets = self.chart_data.get('planets', {})
        classical_planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        occupied_signs = set()
        for planet_name in classical_planets:
            if planet_name in planets:
                occupied_signs.add(planets[planet_name].get('sign'))
                
        num_occupied_signs = len(occupied_signs)
        sankhya_yoga_name = ""
        description = ""
        
        if num_occupied_signs == 1:
            sankhya_yoga_name = "Gola Yoga"
            description = "All planets in one sign - focused, but can be narrow-minded."
        elif num_occupied_signs == 2:
            sankhya_yoga_name = "Yuga Yoga"
            description = "All planets in two signs - can be pulled in two directions."
        elif num_occupied_signs == 3:
            sankhya_yoga_name = "Shula Yoga"
            description = "All planets in three signs - can indicate sharp or painful experiences."
        elif num_occupied_signs == 4:
            sankhya_yoga_name = "Kedara Yoga"
            description = "All planets in four signs - resourceful and helpful."
        elif num_occupied_signs == 5:
            sankhya_yoga_name = "Pasha Yoga"
            description = "All planets in five signs - can be bound by obligations."
        elif num_occupied_signs == 6:
            sankhya_yoga_name = "Dama Yoga"
            description = "All planets in six signs - generous and skillful."
        elif num_occupied_signs == 7:
            sankhya_yoga_name = "Veena Yoga"
            description = "All planets in seven signs - talented, enjoys arts and music."
            
        if sankhya_yoga_name:
            return [{
                'name': sankhya_yoga_name,
                'strength': 'Medium',
                'description': description
            }]
        return []
    
    def calculate_all_yogas(self):
        """Calculate all major yogas"""
        parivartana_yogas = self.calculate_parivartana_yogas()
        # Separate parivartana yogas into their respective categories
        maha_yogas = [y for y in parivartana_yogas if y['name'] == 'Maha Yoga']
        dainya_yogas = [y for y in parivartana_yogas if y['name'] == 'Dainya Yoga']
        khala_yogas = [y for y in parivartana_yogas if y['name'] == 'Khala Yoga']
        other_parivartana_yogas = [y for y in parivartana_yogas if y['name'] == 'Parivartana Yoga']
        
        return {
            'raj_yogas': self.calculate_raj_yogas(),
            'dhana_yogas': self.calculate_dhana_yogas(),
            'mahapurusha_yogas': self.calculate_panch_mahapurusha_yogas(),
            'neecha_bhanga_yogas': self.calculate_neecha_bhanga_yogas(),
            'gaja_kesari_yogas': self.calculate_gaja_kesari_yoga(),
            'amala_yogas': self.calculate_amala_yoga(),
            'viparita_raja_yogas': self.calculate_viparita_raja_yogas(),
            'dharma_karma_yogas': self.calculate_dharma_karma_yogas(),
            'nabhasa_yogas': self.calculate_nabhasa_yogas(),
            'chandra_yogas': self.calculate_chandra_yogas(),
            'surya_yogas': self.calculate_surya_yogas(),
            'parivartana_yogas': {
                'maha_yogas': maha_yogas,
                'dainya_yogas': dainya_yogas,
                'khala_yogas': khala_yogas,
                'other_parivartana_yogas': other_parivartana_yogas
            },
            # These legacy keys remain in the contract.  The former entries
            # were product interpretations (for example "Career Discipline
            # Yoga" and "Hormonal Balance Yoga"), not sourced named yogas.
            # Keep them empty here instead of presenting invented formations
            # on the classical Yogas screen.  Dedicated career and health
            # analyzers remain separate clients and can be migrated rule by
            # rule without changing this response contract.
            'career_specific_yogas': [],
            'health_yogas': [],
            'education_yogas': self.calculate_education_yogas(),
            'marriage_yogas': [],
            'major_doshas': self.calculate_major_doshas()
        }

    def calculate_other_yogas(self):
        """Calculate Lakshmi, Sakata, Shubha/Papa Kartari and Chamara Yogas"""
        planets = self.chart_data.get('planets', {})
        if not planets:
            return []

        yogas = []

        # Lakshmi Yoga
        ninth_lord = self._get_house_lord(9)
        lagna_lord = self._get_house_lord(1)
        if ninth_lord and lagna_lord and ninth_lord in planets and lagna_lord in planets:
            ninth_lord_house = planets[ninth_lord].get('house')
            # A simplified check for strong lagna lord.
            if ninth_lord_house in [1, 4, 5, 7, 9, 10] and planets[lagna_lord].get('strength') == 'High':
                yogas.append({
                    'name': 'Lakshmi Yoga',
                    'strength': 'High',
                    'description': 'Lord of the 9th house is in a Kendra or Trikona and the Lagna lord is strong. Indicates wealth and prosperity.'
                })

        # Sakata Yoga
        if 'Jupiter' in planets and 'Moon' in planets:
            jupiter_house = planets['Jupiter'].get('house')
            moon_house = planets['Moon'].get('house')
            
            house_diff = (jupiter_house - moon_house + 12) % 12
            if house_diff == 5 or house_diff == 7: # 6th or 8th from Moon
                yogas.append({
                    'name': 'Sakata Yoga',
                    'strength': 'Low',
                    'description': 'Jupiter in the 6th or 8th house from the Moon. Indicates a life of struggle with occasional bursts of fortune.'
                })

        # Shubha/Papa Kartari Yoga
        benefics = ['Venus', 'Jupiter', 'Mercury']
        malefics = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        
        # Shubha Kartari Yoga
        planets_in_second = [p for p,d in planets.items() if d.get('house') == 2]
        planets_in_twelfth = [p for p,d in planets.items() if d.get('house') == 12]
        
        if any(p in benefics for p in planets_in_second) and any(p in benefics for p in planets_in_twelfth):
            yogas.append({
                'name': 'Shubha Kartari Yoga',
                'strength': 'Medium',
                'description': 'Benefic planets in the 2nd and 12th houses from the Lagna. Indicates a protected and easy life.'
            })
        # Papa Kartari Yoga
        if any(p in malefics for p in planets_in_second) and any(p in malefics for p in planets_in_twelfth):
            yogas.append({
                'name': 'Papa Kartari Yoga',
                'strength': 'Low',
                'description': 'Malefic planets in the 2nd and 12th houses from the Lagna. Indicates a life of struggle and hardship.'
            })
            
        # Chamara Yoga
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_data = planets[lagna_lord]
            # Lagna lord exalted and aspected by Jupiter
            if 'is_exalted' in lagna_lord_data and lagna_lord_data.get('is_exalted') and 'Jupiter' in self.aspect_calc.get_aspecting_planets(lagna_lord_data.get('house')):
                yogas.append({
                    'name': 'Chamara Yoga',
                    'strength': 'High',
                    'description': 'Lagna lord is exalted and aspected by Jupiter. Indicates a long, prosperous, and reputable life.'
                })
        
        # Two benefics in Lagna, 7th, 9th, or 10th
        for h in [1, 7, 9, 10]:
            benefics_in_house = [p for p in benefics if p in planets and planets[p].get('house') == h]
            if len(benefics_in_house) >= 2:
                yogas.append({
                    'name': 'Chamara Yoga',
                    'strength': 'High',
                    'description': f'Two or more benefic planets in the {h}th house. Indicates a long, prosperous, and reputable life.'
                })

        return yogas
        
    def calculate_parivartana_yogas(self):
        """Phaladeepika 6.32 classification of the 66 house-lord exchanges."""
        planets = self.chart_data.get('planets', {})
        if not planets:
            return []

        yogas = []
        house_lords = {i: self._get_house_lord(i) for i in range(1, 13)}
        
        # Get planet positions
        planet_houses = {p: d.get('house') for p, d in planets.items()}

        # Check for exchanges
        exchanged_lords = set()
        for h1 in range(1, 13):
            for h2 in range(h1 + 1, 13):
                l1 = house_lords.get(h1)
                l2 = house_lords.get(h2)

                if l1 and l2 and l1 != l2 and l1 in planet_houses and l2 in planet_houses:
                    # Check if l1 is in h2 and l2 is in h1
                    if planet_houses.get(l1) == h2 and planet_houses.get(l2) == h1:
                        
                        # Avoid duplicates
                        pair = tuple(sorted((l1, l2)))
                        if pair in exchanged_lords:
                            continue
                        exchanged_lords.add(pair)

                        # Classify the yoga
                        yoga_type = ''
                        description = ''
                        dusthana_houses = [6, 8, 12]
                        is_h1_dusthana = h1 in dusthana_houses
                        is_h2_dusthana = h2 in dusthana_houses

                        if is_h1_dusthana or is_h2_dusthana:
                            yoga_type = 'Dainya Yoga'
                            description = f"House-lord exchange between Houses {h1} and {h2}; one of the houses is 6, 8 or 12, so Phaladeepika classifies it as Dainya."
                            classical_result = "Phaladeepika 6.34 gives misery from this exchange: dependence, want and humiliation."
                        elif h1 == 3 or h2 == 3:
                            yoga_type = 'Khala Yoga'
                            description = f"House-lord exchange between Houses {h1} and {h2}; House 3 is involved without a dusthana, so Phaladeepika classifies it as Khala."
                            classical_result = "Phaladeepika 6.35 gives a changing result from this exchange: quarrel, meanness and fortune that does not stay."
                        else:
                            yoga_type = 'Maha Yoga'
                            description = f"House-lord exchange between Houses {h1} and {h2}; it is neither Dainya nor Khala, so Phaladeepika classifies it among the remaining Maha exchanges."
                            classical_result = "Phaladeepika 6.33 gives a ruler's result from this exchange: wealth, happiness and fame."

                        yogas.append({
                            'name': yoga_type,
                            'planets': [l1, l2],
                            'houses': [h1, h2],
                            'strength': None,
                            'description': description,
                            'classical_result': classical_result,
                            'classical_conditions': [{
                                'rule_id': f'PD-6.32-{yoga_type.split()[0].upper()}',
                                'description': f'{l1}, lord of House {h1}, occupies House {h2}; {l2}, lord of House {h2}, occupies House {h1}',
                                'matched': True,
                            }],
                            'source': {
                                'work': 'Phaladeepika',
                                'reference_label': 'Phaladeepika 6.32',
                                'url': 'https://sanskritdocuments.org/doc_z_misc_sociology_astrology/phaladIpika.html',
                            },
                        })

        return yogas

    def calculate_surya_yogas(self):
        """BPHS 38.1–4 Sun-based yogas and their natural composition."""
        return calculate_classical_surya_yogas(self.chart_data)
    
    def calculate_chandra_yogas(self):
        """BPHS 37.5–13 Moon-based yogas under one documented reading."""
        return calculate_classical_chandra_yogas(self.chart_data)
    
    def calculate_career_specific_yogas(self):
        """Calculate career-specific yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Get 9th and 10th house lords
        ninth_lord = self._get_house_lord(9)
        tenth_lord = self._get_house_lord(10)
        
        if not ninth_lord or not tenth_lord:
            return yogas
        
        # 10th lord in Lagna (1st house)
        if tenth_lord in planets:
            tenth_lord_house = planets[tenth_lord].get('house', 1)
            if tenth_lord_house == 1:
                yogas.append({
                    'name': 'Daśama-pati Lagna Yoga',
                    'planet': tenth_lord,
                    'house': 1,
                    'strength': 'High',
                    'description': f'10th lord {tenth_lord} in Lagna - career-centric personality, leadership',
                    'classical_reference': 'Phaladīpikā Ch. 6 § 14',
                    'sanskrit_verse': 'Daśama-patiḥ lagnage karmavān'
                })
        
        # 9th lord in 10th house (Bhagya-Karma Yoga)
        if ninth_lord in planets:
            ninth_lord_house = planets[ninth_lord].get('house', 1)
            if ninth_lord_house == 10:
                yogas.append({
                    'name': 'Bhāgya-Karma Yoga',
                    'planet': ninth_lord,
                    'house': 10,
                    'strength': 'High',
                    'description': f'9th lord {ninth_lord} in 10th house - fortune supports profession',
                    'classical_reference': 'BPHS Ch. 14 on 9th-lord results',
                    'sanskrit_verse': 'Navama-patiḥ daśame kīrti-vān'
                })
        
        # 10th lord with Saturn (Career Discipline Yoga)
        if tenth_lord in planets and 'Saturn' in planets:
            tenth_lord_house = planets[tenth_lord].get('house', 1)
            saturn_house = planets['Saturn'].get('house', 1)
            
            if tenth_lord_house == saturn_house and tenth_lord != 'Saturn':
                yogas.append({
                    'name': 'Śani-Karma Yoga',
                    'planets': [tenth_lord, 'Saturn'],
                    'houses': [tenth_lord_house, saturn_house],
                    'strength': 'High',
                    'description': f'10th lord {tenth_lord} with Saturn - structured, responsible work style',
                    'classical_reference': 'Phaladīpikā 6.16; Hora Sara 10.2',
                    'sanskrit_verse': 'Daśama-patiḥ śanisaṃyuktaḥ karma-niṣṭhaḥ'
                })
        
        return yogas
    
    def calculate_health_yogas(self):
        """Calculate health-related yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Aristha Yogas (health affliction yogas)
        yogas.extend(self._calculate_aristha_yogas())
        
        # Ayur Yogas (longevity yogas)
        yogas.extend(self._calculate_ayur_yogas())
        
        # Healing yogas
        yogas.extend(self._calculate_healing_yogas())
        
        return yogas
    
    def _calculate_aristha_yogas(self):
        """Calculate Aristha (health affliction) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Lagna lord in 6th/8th/12th house
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_house = planets[lagna_lord].get('house', 1)
            if lagna_lord_house in [6, 8, 12]:
                yogas.append({
                    'name': 'Lagna Lord Aristha Yoga',
                    'planet': lagna_lord,
                    'house': lagna_lord_house,
                    'strength': 'High',
                    'type': 'affliction',
                    'description': f'Lagna lord {lagna_lord} in {lagna_lord_house}th house - health challenges'
                })
        
        # 6th lord in Lagna
        sixth_lord = self._get_house_lord(6)
        if sixth_lord and sixth_lord in planets:
            sixth_lord_house = planets[sixth_lord].get('house', 1)
            if sixth_lord_house == 1:
                yogas.append({
                    'name': 'Sixth Lord in Lagna',
                    'planet': sixth_lord,
                    'house': 1,
                    'strength': 'Medium',
                    'type': 'affliction',
                    'description': f'6th lord {sixth_lord} in Lagna - disease proneness'
                })
        
        # 8th lord in Lagna
        eighth_lord = self._get_house_lord(8)
        if eighth_lord and eighth_lord in planets:
            eighth_lord_house = planets[eighth_lord].get('house', 1)
            if eighth_lord_house == 1:
                yogas.append({
                    'name': 'Eighth Lord in Lagna',
                    'planet': eighth_lord,
                    'house': 1,
                    'strength': 'High',
                    'type': 'affliction',
                    'description': f'8th lord {eighth_lord} in Lagna - chronic health issues'
                })
        
        # Health-specific Viparita Raja Yogas (dusthana cancellation for health)
        yogas.extend(self._calculate_health_viparita_yogas())
        
        return yogas
    
    def _calculate_ayur_yogas(self):
        """Calculate Ayur (longevity) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Lagna lord in Kendra/Trikona
        lagna_lord = self._get_house_lord(1)
        if lagna_lord and lagna_lord in planets:
            lagna_lord_house = planets[lagna_lord].get('house', 1)
            if lagna_lord_house in [1, 4, 5, 7, 9, 10]:
                yogas.append({
                    'name': 'Ayur Yoga',
                    'planet': lagna_lord,
                    'house': lagna_lord_house,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': f'Lagna lord {lagna_lord} in favorable house - good longevity'
                })
        
        # Jupiter in Lagna (natural healing)
        if 'Jupiter' in planets:
            jupiter_house = planets['Jupiter'].get('house', 1)
            if jupiter_house == 1:
                yogas.append({
                    'name': 'Guru Lagna Yoga',
                    'planet': 'Jupiter',
                    'house': 1,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': 'Jupiter in Lagna - natural healing ability, strong immunity'
                })
        
        return yogas
    
    def _calculate_healing_yogas(self):
        """Calculate healing and recovery yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Sun in 10th house (vitality)
        if 'Sun' in planets:
            sun_house = planets['Sun'].get('house', 1)
            if sun_house == 10:
                yogas.append({
                    'name': 'Surya Karma Yoga',
                    'planet': 'Sun',
                    'house': 10,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Sun in 10th house - strong vitality and leadership in health'
                })
        
        # Moon in 4th house (emotional stability)
        if 'Moon' in planets:
            moon_house = planets['Moon'].get('house', 1)
            if moon_house == 4:
                yogas.append({
                    'name': 'Chandra Sukha Yoga',
                    'planet': 'Moon',
                    'house': 4,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Moon in 4th house - emotional stability, good digestive health'
                })
        
        # Venus in 7th house (hormonal balance)
        if 'Venus' in planets:
            venus_house = planets['Venus'].get('house', 1)
            if venus_house == 7:
                yogas.append({
                    'name': 'Shukra Kalatra Yoga',
                    'planet': 'Venus',
                    'house': 7,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': 'Venus in 7th house - hormonal balance, reproductive health'
                })
        
        return yogas
    
    def _calculate_health_viparita_yogas(self):
        """Calculate health-specific Viparita Raja Yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # 6th lord in 8th/12th house (disease lord in other dusthana)
        sixth_lord = self._get_house_lord(6)
        if sixth_lord and sixth_lord in planets:
            sixth_lord_house = planets[sixth_lord].get('house', 1)
            if sixth_lord_house in [8, 12]:
                yogas.append({
                    'name': 'Sarala Yoga (Health)',
                    'planet': sixth_lord,
                    'house': sixth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'6th lord {sixth_lord} in {sixth_lord_house}th house - victory over diseases'
                })
        
        # 8th lord in 6th/12th house (chronic illness lord in other dusthana)
        eighth_lord = self._get_house_lord(8)
        if eighth_lord and eighth_lord in planets:
            eighth_lord_house = planets[eighth_lord].get('house', 1)
            if eighth_lord_house in [6, 12]:
                yogas.append({
                    'name': 'Vimala Yoga (Health)',
                    'planet': eighth_lord,
                    'house': eighth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'8th lord {eighth_lord} in {eighth_lord_house}th house - reduces chronic health issues'
                })
        
        # 12th lord in 6th/8th house (hospitalization lord in other dusthana)
        twelfth_lord = self._get_house_lord(12)
        if twelfth_lord and twelfth_lord in planets:
            twelfth_lord_house = planets[twelfth_lord].get('house', 1)
            if twelfth_lord_house in [6, 8]:
                yogas.append({
                    'name': 'Vipareeta Raja Yoga (Health)',
                    'planet': twelfth_lord,
                    'house': twelfth_lord_house,
                    'strength': 'Medium',
                    'type': 'beneficial',
                    'description': f'12th lord {twelfth_lord} in {twelfth_lord_house}th house - reduces hospitalization and mental health issues'
                })
        
        return yogas
    
    def calculate_education_yogas(self):
        """Return only the sourced Phaladeepika Saraswati formation."""
        return calculate_classical_saraswati(self.chart_data)

    def _get_saraswati_house_significance(self, house: int) -> str:
        """Get house-specific significance for Saraswati Yoga"""
        significances = {
            1: "exceptional learning ability and academic leadership",
            2: "wealth through education and eloquent speech", 
            3: "creative writing and communication skills",
            4: "strong foundation in traditional learning",
            5: "brilliant intelligence and academic excellence",
            6: "victory in competitive exams and debates",
            7: "success in collaborative learning and partnerships",
            8: "deep research abilities and occult knowledge",
            9: "higher education success and teaching abilities",
            10: "career success through education and reputation",
            11: "gains and recognition through academic achievements",
            12: "foreign education and spiritual learning"
        }
        return significances.get(house, "general learning enhancement")
    
    def _get_budh_aditya_house_significance(self, house: int) -> str:
        """Get house-specific significance for Budh-Aditya Yoga"""
        significances = {
            1: "sharp analytical mind and leadership in academics",
            2: "intelligent speech and financial acumen",
            3: "excellent communication and writing skills", 
            4: "strong logical foundation and practical learning",
            5: "brilliant intelligence and academic success",
            6: "analytical problem-solving in competitive fields",
            7: "diplomatic intelligence and partnership success",
            8: "research excellence but challenges in formal education",
            9: "philosophical intelligence and higher learning",
            10: "career success through intellectual abilities",
            11: "networking skills and gains through intelligence",
            12: "intuitive intelligence but may face educational obstacles"
        }
        return significances.get(house, "enhanced intellectual abilities")
    
    def _planets_in_mutual_aspect(self, planet_names, planets):
        """Check if planets are in mutual aspect using AspectCalculator"""
        if len(planet_names) < 2:
            return False
        
        # Check if any two planets aspect each other using proper aspect calculation
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                planet1 = planet_names[i]
                planet2 = planet_names[j]
                
                if planet1 not in planets or planet2 not in planets:
                    continue
                
                planet1_data = planets[planet1].copy()
                planet1_data['name'] = planet1
                planet2_data = planets[planet2].copy()
                planet2_data['name'] = planet2
                
                if self._are_planets_connected(planet1_data, planet2_data):
                    return True
        return False
    
    def _are_planets_connected(self, planet1_data, planet2_data):
        """Check if two planets are connected by conjunction or aspect using AspectCalculator"""
        house1 = planet1_data.get('house', 1)
        house2 = planet2_data.get('house', 1)
        planet1_name = planet1_data.get('name', '')
        planet2_name = planet2_data.get('name', '')
        
        # 1. Conjunction (same house)
        if house1 == house2:
            return True
        
        # 2. Use AspectCalculator to check if planet1 aspects house2
        aspecting_planets_house2 = self.aspect_calc.get_aspecting_planets(house2)
        if planet1_name in aspecting_planets_house2:
            return True
        
        # 3. Use AspectCalculator to check if planet2 aspects house1
        aspecting_planets_house1 = self.aspect_calc.get_aspecting_planets(house1)
        if planet2_name in aspecting_planets_house1:
            return True
        
        return False
    
    def _get_house_lord(self, house_number):
        """Get the lord of a house"""
        houses = self.chart_data.get('houses', [])
        if house_number <= len(houses):
            house_sign = houses[house_number - 1].get('sign', 0)
            return self.SIGN_LORDS.get(house_sign)
    
    def _ordinal(self, n):
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    
    def get_marriage_yogas_only(self):
        """Get only marriage-related yogas from all yogas"""
        all_yogas = self.calculate_all_yogas()
        marriage_yogas = []
        
        # Add specific marriage yogas
        marriage_yogas.extend(all_yogas.get('marriage_yogas', []))
        
        # Filter other yogas for marriage relevance
        marriage_keywords = ['kalatra', 'marriage', 'spouse', 'venus', 'shukra', 'seventh', 'saptama', 'mangal', 'guru']
        
        for category_yogas in all_yogas.values():
            if isinstance(category_yogas, list):
                for yoga in category_yogas:
                    yoga_name = yoga.get('name', '').lower()
                    if any(keyword in yoga_name for keyword in marriage_keywords):
                        if yoga not in marriage_yogas:
                            marriage_yogas.append(yoga)
        
        return marriage_yogas
    
    def get_education_yogas_only(self):
        """Get only education-related yogas from all yogas"""
        all_yogas = self.calculate_all_yogas()
        education_yogas = []
        
        # Add specific education yogas
        education_yogas.extend(all_yogas.get('education_yogas', []))
        
        # Add relevant yogas from other categories
        for yoga in all_yogas.get('gaja_kesari_yogas', []):
            education_yogas.append(yoga)
        
        # Filter other yogas for education relevance
        education_keywords = ['saraswati', 'budh', 'mercury', 'jupiter', 'guru', 'education', 'learning', 'gaja', 'kesari']
        
        for category_yogas in all_yogas.values():
            if isinstance(category_yogas, list):
                for yoga in category_yogas:
                    yoga_name = yoga.get('name', '').lower()
                    if any(keyword in yoga_name for keyword in education_keywords):
                        if yoga not in education_yogas:
                            education_yogas.append(yoga)
        
        return education_yogas
    
    def calculate_marriage_yogas(self):
        """Calculate marriage-specific yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Mangal Dosha (Kuja Dosha)
        yogas.extend(self._calculate_mangal_dosha())
        
        # Kalatra Yogas (marriage combinations)
        yogas.extend(self._calculate_kalatra_yogas())
        
        # Venus-Jupiter marriage yogas
        yogas.extend(self._calculate_venus_jupiter_yogas())
        
        # 7th house marriage yogas
        yogas.extend(self._calculate_seventh_house_yogas())
        
        return yogas
    
    def _calculate_mangal_dosha(self):
        """Compatibility yoga-card view of the canonical Mangal Dosha result."""
        result = calculate_classical_mangal_dosha(self.chart_data)
        if not result["present"]:
            return []
        return [{
            'name': 'Mangal Dosha',
            'planet': 'Mars',
            'planets': ['Mars'],
            'house': result['mars_house'],
            'houses': [result['mars_house']],
            'strength': None,
            'type': 'affliction',
            'description': result['summary'],
            'classical_status': result['status'],
            'classical_conditions': [{
                'rule_id': row['rule_id'],
                'description': row['fact'],
                'matched': row['matched'],
            } for row in result['evidence']],
            'source': result['source'],
            'textual_variants': result['textual_variants'],
        }]
    
    def _calculate_kalatra_yogas(self):
        """Calculate Kalatra (marriage) yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # 7th lord in Kendra
        seventh_lord = self._get_house_lord(7)
        if seventh_lord and seventh_lord in planets:
            seventh_lord_house = planets[seventh_lord].get('house', 1)
            if seventh_lord_house in [1, 4, 7, 10]:
                yogas.append({
                    'name': 'Kalatra Yoga',
                    'planet': seventh_lord,
                    'house': seventh_lord_house,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': f'7th lord {seventh_lord} in Kendra - strong marriage'
                })
        
        # Venus in 7th house
        if 'Venus' in planets:
            venus_house = planets['Venus'].get('house', 1)
            if venus_house == 7:
                yogas.append({
                    'name': 'Shukra Kalatra Yoga',
                    'planet': 'Venus',
                    'house': 7,
                    'strength': 'High',
                    'type': 'beneficial',
                    'description': 'Venus in 7th house - beautiful spouse, happy marriage'
                })
        
        return yogas
    
    def _calculate_venus_jupiter_yogas(self):
        """Calculate Venus-Jupiter marriage combinations"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        if 'Venus' not in planets or 'Jupiter' not in planets:
            return yogas
        
        venus_house = planets['Venus'].get('house', 1)
        jupiter_house = planets['Jupiter'].get('house', 1)
        
        # Venus-Jupiter conjunction
        if venus_house == jupiter_house:
            yogas.append({
                'name': 'Guru-Shukra Yoga',
                'planets': ['Venus', 'Jupiter'],
                'houses': [venus_house],
                'strength': 'High',
                'type': 'beneficial',
                'description': 'Venus-Jupiter conjunction - harmonious marriage, spiritual spouse'
            })
        
        # Venus-Jupiter mutual aspect
        elif self._are_planets_connected(planets['Venus'], planets['Jupiter']):
            yogas.append({
                'name': 'Guru-Shukra Drishti Yoga',
                'planets': ['Venus', 'Jupiter'],
                'houses': [venus_house, jupiter_house],
                'strength': 'Medium',
                'type': 'beneficial',
                'description': 'Venus-Jupiter aspect - balanced marriage, good values'
            })
        
        return yogas
    
    def _calculate_seventh_house_yogas(self):
        """Calculate 7th house specific marriage yogas"""
        yogas = []
        planets = self.chart_data.get('planets', {})
        
        # Benefics in 7th house
        benefics_in_seventh = []
        for planet in ['Jupiter', 'Venus', 'Mercury']:
            if planet in planets and planets[planet].get('house', 1) == 7:
                benefics_in_seventh.append(planet)
        
        if benefics_in_seventh:
            yogas.append({
                'name': 'Saptama Shubha Yoga',
                'planets': benefics_in_seventh,
                'houses': [7],
                'strength': 'High',
                'type': 'beneficial',
                'description': f'Benefic planets {", ".join(benefics_in_seventh)} in 7th house - good marriage'
            })
        
        # Malefics in 7th house
        malefics_in_seventh = []
        for planet in ['Mars', 'Saturn', 'Rahu', 'Ketu']:
            if planet in planets and planets[planet].get('house', 1) == 7:
                malefics_in_seventh.append(planet)
        
        if malefics_in_seventh:
            yogas.append({
                'name': 'Saptama Krura Yoga',
                'planets': malefics_in_seventh,
                'houses': [7],
                'strength': 'High',
                'type': 'affliction',
                'description': f'Malefic planets {", ".join(malefics_in_seventh)} in 7th house - marriage challenges'
            })
        
        return yogas
    
    def calculate_major_doshas(self):
        """Calculate major negative yogas (Doshas)"""
        return {
            "mangal_dosha": self._check_mangal_dosha(),
            "kaal_sarp_dosha": self._check_kaal_sarp(),
            "pitra_dosha": self._check_pitra_dosha(),
            "matru_dosha": self._check_matru_dosha(),
        }
    
    def _check_mangal_dosha(self):
        """Canonical result with all legacy keys preserved additively."""
        return calculate_classical_mangal_dosha(self.chart_data)
    
    def _check_kaal_sarp(self):
        """Exact geometry for the explicitly modern nodal-enclosure convention."""
        return calculate_nodal_enclosure(self.chart_data)
    
    def _check_pitra_dosha(self):
        """Legacy method name; result now follows BPHS 83.20-30 only."""
        return calculate_classical_pitri_shapa(self.chart_data)

    def _check_matru_dosha(self):
        """Legacy-friendly key; result follows BPHS 83.34-46 only."""
        return calculate_classical_matri_shapa(self.chart_data)
