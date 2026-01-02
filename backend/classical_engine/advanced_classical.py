"""
Advanced Classical Techniques Module
Implements sophisticated Vedic astrology techniques for enhanced predictions
"""

from typing import Dict, List, Any, Tuple
from utils.timezone_service import parse_timezone_offset
import math

class AdvancedClassicalTechniques:
    def __init__(self, birth_data: Dict, planet_positions: Dict = None):
        self.birth_data = birth_data
        self.planet_positions = planet_positions or self._get_planet_positions()
        self.debug_info = {}
    
    def calculate_ashtakavarga_strength(self) -> Dict[str, Any]:
        """Calculate Ashtakavarga strength for all planets and houses"""
        debug = {
            "technique": "Ashtakavarga Analysis",
            "description": "Calculating planetary strength through Ashtakavarga system",
            "calculations": []
        }
        
        ashtakavarga_data = {}
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            # Simplified Ashtakavarga calculation
            planet_av = self._calculate_planet_ashtakavarga(planet)
            ashtakavarga_data[planet] = planet_av
            
            debug["calculations"].append(
                f"{planet}: Total points = {planet_av['total_points']}, "
                f"Strength = {planet_av['strength_category']}"
            )
        
        # Calculate Sarvashtakavarga (combined)
        sarvashtakavarga = self._calculate_sarvashtakavarga(ashtakavarga_data)
        
        result = {
            "individual_ashtakavarga": ashtakavarga_data,
            "sarvashtakavarga": sarvashtakavarga,
            "strongest_houses": self._get_strongest_av_houses(sarvashtakavarga)
        }
        
        self.debug_info["ashtakavarga"] = debug
        return result
    
    def analyze_yogakaraka_planets(self) -> Dict[str, Any]:
        """Identify and analyze Yogakaraka planets"""
        debug = {
            "technique": "Yogakaraka Analysis",
            "description": "Identifying planets that are both Kendra and Trikona lords",
            "calculations": []
        }
        
        ascendant = self._get_ascendant_sign()
        yogakaraka_planets = []
        
        # Define Kendra (1,4,7,10) and Trikona (1,5,9) houses
        kendra_houses = [1, 4, 7, 10]
        trikona_houses = [1, 5, 9]
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            ruled_houses = self._get_planet_rulerships(planet, ascendant)
            
            kendra_ruler = any(house in kendra_houses for house in ruled_houses)
            trikona_ruler = any(house in trikona_houses for house in ruled_houses)
            
            if kendra_ruler and trikona_ruler:
                yogakaraka_data = {
                    "planet": planet,
                    "ruled_houses": ruled_houses,
                    "strength": self._calculate_yogakaraka_strength(planet),
                    "current_condition": self._analyze_planet_condition(planet)
                }
                yogakaraka_planets.append(yogakaraka_data)
                
                debug["calculations"].append(
                    f"{planet} is Yogakaraka (rules houses {ruled_houses}), "
                    f"strength = {yogakaraka_data['strength']:.2f}"
                )
        
        result = {
            "yogakaraka_planets": yogakaraka_planets,
            "primary_yogakaraka": yogakaraka_planets[0] if yogakaraka_planets else None
        }
        
        self.debug_info["yogakaraka"] = debug
        return result
    
    def analyze_planetary_war(self) -> Dict[str, Any]:
        """Analyze planetary war (Graha Yuddha) conditions"""
        debug = {
            "technique": "Planetary War Analysis",
            "description": "Checking for planets in close conjunction (within 1 degree)",
            "calculations": []
        }
        
        wars = []
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for i, planet1 in enumerate(planets):
            for planet2 in planets[i+1:]:
                if planet1 == 'Sun' or planet2 == 'Sun':  # Sun doesn't participate in war
                    continue
                
                pos1 = self.planet_positions.get(planet1, {}).get('longitude', 0)
                pos2 = self.planet_positions.get(planet2, {}).get('longitude', 0)
                
                # Calculate angular distance
                distance = abs(pos1 - pos2)
                if distance > 180:
                    distance = 360 - distance
                
                if distance <= 1.0:  # Within 1 degree
                    winner = self._determine_war_winner(planet1, planet2, pos1, pos2)
                    
                    war_data = {
                        "planet1": planet1,
                        "planet2": planet2,
                        "distance": distance,
                        "winner": winner,
                        "effect": self._get_war_effect(winner, planet1, planet2)
                    }
                    wars.append(war_data)
                    
                    debug["calculations"].append(
                        f"{planet1} vs {planet2}: distance = {distance:.2f}°, "
                        f"winner = {winner}"
                    )
        
        result = {"planetary_wars": wars}
        self.debug_info["planetary_war"] = debug
        return result
    
    def analyze_argala(self) -> Dict[str, Any]:
        """Analyze Argala (planetary intervention) effects"""
        debug = {
            "technique": "Argala Analysis",
            "description": "Analyzing planetary interventions and obstructions",
            "calculations": []
        }
        
        argala_effects = {}
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            planet_house = self.planet_positions.get(planet, {}).get('house', 1)
            
            # Check for Argala from 2nd, 4th, and 11th houses
            argala_sources = []
            for source_house in [planet_house + 1, planet_house + 3, planet_house + 10]:
                if source_house > 12:
                    source_house -= 12
                
                planets_in_house = self._get_planets_in_house(source_house)
                if planets_in_house:
                    argala_sources.extend(planets_in_house)
            
            # Check for Virodhargala (obstruction) from 12th, 10th, and 3rd
            virodhargala_sources = []
            for obstruct_house in [planet_house - 1, planet_house - 2, planet_house + 2]:
                if obstruct_house <= 0:
                    obstruct_house += 12
                if obstruct_house > 12:
                    obstruct_house -= 12
                
                planets_in_house = self._get_planets_in_house(obstruct_house)
                if planets_in_house:
                    virodhargala_sources.extend(planets_in_house)
            
            argala_effects[planet] = {
                "argala_from": argala_sources,
                "virodhargala_from": virodhargala_sources,
                "net_effect": self._calculate_argala_net_effect(argala_sources, virodhargala_sources)
            }
            
            debug["calculations"].append(
                f"{planet}: Argala from {argala_sources}, "
                f"Virodhargala from {virodhargala_sources}"
            )
        
        result = {"argala_effects": argala_effects}
        self.debug_info["argala"] = debug
        return result
    
    def analyze_temporal_friendship(self) -> Dict[str, Any]:
        """Analyze temporal (Tatkalika) friendship based on house positions"""
        debug = {
            "technique": "Temporal Friendship Analysis",
            "description": "Calculating temporary friendship based on current positions",
            "calculations": []
        }
        
        temporal_relations = {}
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        
        for planet1 in planets:
            temporal_relations[planet1] = {}
            planet1_house = self.planet_positions.get(planet1, {}).get('house', 1)
            
            for planet2 in planets:
                if planet1 == planet2:
                    continue
                
                planet2_house = self.planet_positions.get(planet2, {}).get('house', 1)
                
                # Calculate house distance
                distance = planet2_house - planet1_house
                if distance <= 0:
                    distance += 12
                
                # Temporal friendship rules
                if distance in [2, 3, 4, 10, 11, 12]:
                    relation = "friend"
                else:
                    relation = "enemy"
                
                temporal_relations[planet1][planet2] = {
                    "relation": relation,
                    "house_distance": distance
                }
                
                debug["calculations"].append(
                    f"{planet1} to {planet2}: distance = {distance}, "
                    f"relation = {relation}"
                )
        
        result = {"temporal_relations": temporal_relations}
        self.debug_info["temporal_friendship"] = debug
        return result
    
    def analyze_chara_karakas(self) -> Dict[str, Any]:
        """Analyze Chara Karakas (variable significators)"""
        debug = {
            "technique": "Chara Karaka Analysis",
            "description": "Determining variable significators based on planetary degrees",
            "calculations": []
        }
        
        # Get planetary degrees (excluding Rahu/Ketu for Chara Karakas)
        planet_degrees = {}
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            longitude = self.planet_positions.get(planet, {}).get('longitude', 0)
            # Convert to degrees within sign (0-30)
            degree_in_sign = longitude % 30
            planet_degrees[planet] = degree_in_sign
        
        # Sort by degrees (highest to lowest)
        sorted_planets = sorted(planet_degrees.items(), key=lambda x: x[1], reverse=True)
        
        # Assign Chara Karaka roles
        karaka_roles = [
            "Atmakaraka", "Amatyakaraka", "Bhratrukaraka", "Matrukaraka",
            "Putrakaraka", "Gnatikaraka", "Darakaraka"
        ]
        
        chara_karakas = {}
        for i, (planet, degree) in enumerate(sorted_planets):
            if i < len(karaka_roles):
                role = karaka_roles[i]
                chara_karakas[role] = {
                    "planet": planet,
                    "degree": degree,
                    "significance": self._get_karaka_significance(role)
                }
                
                debug["calculations"].append(
                    f"{role}: {planet} ({degree:.2f}°)"
                )
        
        result = {"chara_karakas": chara_karakas}
        self.debug_info["chara_karakas"] = debug
        return result
    
    def analyze_rashi_sandhi(self) -> Dict[str, Any]:
        """Analyze planets in Rashi Sandhi (sign junctions)"""
        debug = {
            "technique": "Rashi Sandhi Analysis",
            "description": "Checking planets near sign boundaries (within 1 degree)",
            "calculations": []
        }
        
        sandhi_planets = []
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            longitude = self.planet_positions.get(planet, {}).get('longitude', 0)
            degree_in_sign = longitude % 30
            
            # Check if within 1 degree of sign boundary
            if degree_in_sign <= 1.0 or degree_in_sign >= 29.0:
                sandhi_data = {
                    "planet": planet,
                    "degree_in_sign": degree_in_sign,
                    "position": "early" if degree_in_sign <= 1.0 else "late",
                    "effect": self._get_sandhi_effect(planet, degree_in_sign)
                }
                sandhi_planets.append(sandhi_data)
                
                debug["calculations"].append(
                    f"{planet}: {degree_in_sign:.2f}° in sign ({sandhi_data['position']} sandhi)"
                )
        
        result = {"sandhi_planets": sandhi_planets}
        self.debug_info["rashi_sandhi"] = debug
        return result
    
    def analyze_nakshatra_pada(self) -> Dict[str, Any]:
        """Analyze Nakshatra Pada positions and their effects"""
        debug = {
            "technique": "Nakshatra Pada Analysis",
            "description": "Analyzing planetary positions in Nakshatra Padas",
            "calculations": []
        }
        
        pada_analysis = {}
        
        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
            longitude = self.planet_positions.get(planet, {}).get('longitude', 0)
            
            # Calculate Nakshatra and Pada
            nakshatra_num = int(longitude / 13.333333) + 1  # 27 Nakshatras
            nakshatra_degree = longitude % 13.333333
            pada_num = int(nakshatra_degree / 3.333333) + 1  # 4 Padas per Nakshatra
            
            nakshatra_name = self._get_nakshatra_name(nakshatra_num)
            pada_lord = self._get_pada_lord(nakshatra_num, pada_num)
            
            pada_analysis[planet] = {
                "nakshatra": nakshatra_name,
                "nakshatra_num": nakshatra_num,
                "pada": pada_num,
                "pada_lord": pada_lord,
                "degree_in_nakshatra": nakshatra_degree,
                "significance": self._get_pada_significance(nakshatra_name, pada_num)
            }
            
            debug["calculations"].append(
                f"{planet}: {nakshatra_name} Pada {pada_num} (lord: {pada_lord})"
            )
        
        result = {"nakshatra_pada_analysis": pada_analysis}
        self.debug_info["nakshatra_pada"] = debug
        return result
    
    # Helper methods
    def _calculate_planet_ashtakavarga(self, planet: str) -> Dict:
        """Calculate Ashtakavarga for a planet"""
        # Simplified calculation - in real implementation, use proper Ashtakavarga rules
        total_points = 28 + hash(planet) % 10  # Mock calculation
        return {
            "total_points": total_points,
            "strength_category": "strong" if total_points > 30 else "moderate" if total_points > 25 else "weak"
        }
    
    def _calculate_sarvashtakavarga(self, individual_av: Dict) -> Dict:
        """Calculate combined Ashtakavarga"""
        house_totals = {i: 20 + i % 8 for i in range(1, 13)}  # Mock calculation
        return {"house_totals": house_totals}
    
    def _get_strongest_av_houses(self, sarvashtakavarga: Dict) -> List[int]:
        """Get strongest houses by Ashtakavarga"""
        house_totals = sarvashtakavarga["house_totals"]
        sorted_houses = sorted(house_totals.items(), key=lambda x: x[1], reverse=True)
        return [h[0] for h in sorted_houses[:3]]
    
    def _get_ascendant_sign(self) -> int:
        """Get ascendant sign number"""
        return 1  # Mock - would calculate from birth data
    
    def _get_planet_rulerships(self, planet: str, ascendant: int) -> List[int]:
        """Get houses ruled by planet for given ascendant"""
        # Simplified rulership calculation
        base_rulerships = {
            "Sun": [5], "Moon": [4], "Mars": [1, 8], "Mercury": [3, 6],
            "Jupiter": [9, 12], "Venus": [2, 7], "Saturn": [10, 11]
        }
        return base_rulerships.get(planet, [])
    
    def _calculate_yogakaraka_strength(self, planet: str) -> float:
        """Calculate Yogakaraka strength"""
        return 0.8  # Mock calculation
    
    def _analyze_planet_condition(self, planet: str) -> Dict:
        """Analyze current condition of planet"""
        return {"dignity": "own_sign", "strength": 0.8}
    
    def _determine_war_winner(self, planet1: str, planet2: str, pos1: float, pos2: float) -> str:
        """Determine winner in planetary war"""
        # Higher longitude wins (simplified rule)
        return planet1 if pos1 > pos2 else planet2
    
    def _get_war_effect(self, winner: str, planet1: str, planet2: str) -> str:
        """Get effect of planetary war"""
        loser = planet2 if winner == planet1 else planet1
        return f"{winner} gains strength, {loser} loses power"
    
    def _get_planets_in_house(self, house: int) -> List[str]:
        """Get planets in specified house"""
        planets_in_house = []
        for planet, data in self.planet_positions.items():
            if data.get('house') == house:
                planets_in_house.append(planet)
        return planets_in_house
    
    def _calculate_argala_net_effect(self, argala: List, virodhargala: List) -> str:
        """Calculate net Argala effect"""
        if len(argala) > len(virodhargala):
            return "positive"
        elif len(virodhargala) > len(argala):
            return "negative"
        else:
            return "neutral"
    
    def _get_karaka_significance(self, role: str) -> str:
        """Get significance of Chara Karaka role"""
        significances = {
            "Atmakaraka": "Soul, self, overall life purpose",
            "Amatyakaraka": "Career, profession, ministers",
            "Bhratrukaraka": "Siblings, courage, efforts",
            "Matrukaraka": "Mother, home, emotions",
            "Putrakaraka": "Children, creativity, intelligence",
            "Gnatikaraka": "Obstacles, diseases, enemies",
            "Darakaraka": "Spouse, partnerships"
        }
        return significances.get(role, "Unknown")
    
    def _get_sandhi_effect(self, planet: str, degree: float) -> str:
        """Get effect of Rashi Sandhi"""
        if degree <= 1.0:
            return "Weak start, gradual strengthening"
        else:
            return "Completion of cycle, transformation"
    
    def _get_nakshatra_name(self, num: int) -> str:
        """Get Nakshatra name by number"""
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        return nakshatras[num - 1] if 1 <= num <= 27 else "Unknown"
    
    def _get_pada_lord(self, nakshatra_num: int, pada_num: int) -> str:
        """Get Pada lord"""
        # Simplified pada lord calculation
        lords = ["Mars", "Venus", "Mercury", "Moon"]
        return lords[(pada_num - 1) % 4]
    
    def _get_pada_significance(self, nakshatra: str, pada: int) -> str:
        """Get significance of Nakshatra Pada"""
        return f"Pada {pada} of {nakshatra} - specific qualities and effects"
    
    def _get_planet_positions(self) -> Dict:
        """Get natal planet positions using direct calculation"""
        import swisseph as swe
        
        try:
            # Calculate directly without API call
            time_parts = self.birth_data['time'].split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60
            
            tz_offset = parse_timezone_offset(
                self.birth_data['timezone'],
                self.birth_data['latitude'],
                self.birth_data['longitude']
            )
            
            utc_hour = hour - tz_offset
            jd = swe.julday(
                int(self.birth_data['date'].split('-')[0]),
                int(self.birth_data['date'].split('-')[1]),
                int(self.birth_data['date'].split('-')[2]),
                utc_hour
            )
            
            result = {}
            planet_names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
            
            for i, planet in enumerate([0, 1, 4, 2, 5, 3, 6, 11, 12]):
                if planet <= 6:
                    # Set Lahiri Ayanamsa for accurate Vedic calculations

                    swe.set_sid_mode(swe.SIDM_LAHIRI)

                    pos = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0]
                else:
                    pos = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0]
                    if planet == 12:
                        pos = list(pos)
                        pos[0] = (pos[0] + 180) % 360
                
                longitude = pos[0]
                # Calculate proper house from ascendant
                sign_num = int(longitude / 30)
                ascendant_sign = int(self.birth_data.get('ascendant', 0) / 30)
                house_num = ((sign_num - ascendant_sign) % 12) + 1
                
                result[planet_names[i]] = {
                    "longitude": longitude,
                    "house": house_num,
                    "sign": sign_num
                }
            
            return result
            
            result = {}
            for planet, data in chart_data.get('planets', {}).items():
                if planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
                    result[planet] = {
                        "longitude": data.get('longitude', 0.0),
                        "house": data.get('house', 1),
                        "sign": data.get('sign', 0)
                    }
            
            return result
            
        except Exception as e:
            print(f"Error getting planet positions: {e}")
            return {}