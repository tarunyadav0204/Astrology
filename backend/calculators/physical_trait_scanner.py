from typing import Dict, List, Any
import math
import logging

class PhysicalTraitScanner:
    """
    Analyzes physical appearance using a 3-Layer Priority System.
    UPDATED: Includes granular details (Body hair, Weight, Humps, etc.)
    """
    
    def __init__(self, chart_calculator):
        self.chart_calc = chart_calculator
        
    def scan_physical_features(self, birth_data: Dict) -> List[Dict]:
        try:
            # 1. Calculate Chart
            from types import SimpleNamespace
            birth_obj = SimpleNamespace(**birth_data)
            
            # DEBUG: Log birth data
            logging.info(f"🔍 Birth Data: {birth_data}")
            
            chart = self.chart_calc.calculate_chart(birth_obj)
            
            logging.info(f"Chart data keys: {list(chart.keys())}")
            
            traits = []
            asc_degree = chart['ascendant']
            asc_sign = int(asc_degree / 30)
            asc_exact_deg = asc_degree % 30
            
            # DEBUG: More detailed logging
            logging.info(f"🎯 Ascendant: {asc_degree}° -> Sign: {asc_sign} ({self._get_sign_name(asc_sign)}), Exact degree: {asc_exact_deg}°")
            planet_positions = [(p, f"{data['longitude']:.2f}°") for p, data in chart['planets'].items()]
            logging.info(f"🌟 All planets: {planet_positions}")
            
            # --- FEATURE 1: COMPLEXION (Primary) ---
            occupants = self._get_occupants_detailed(chart, asc_sign)
            logging.info(f"1st house occupants: {[f"{p['name']} at {p['degree']:.1f}°" for p in occupants]}")
            occupants.sort(key=lambda x: abs(x['degree'] - asc_exact_deg))
            
            complexion = self._analyze_complexion(asc_sign, occupants)
            logging.info(f"Complexion trait: {complexion['label']}")
            traits.append(complexion)
            
            # --- FEATURE 2: PLANETARY MARKERS (The "Deep Scan") ---
            # Planets in 1st house are the strongest physical modifiers
            for planet_data in occupants:
                p_name = planet_data['name']
                p_trait = self._get_planet_traits(p_name)
                
                # If planet is dominant (< 8 deg from Lagna), it's a defining feature
                degree_diff = abs(planet_data['degree'] - asc_exact_deg)
                logging.info(f"{p_name}: {degree_diff:.1f}° from ASC -> {'Dominant' if degree_diff < 8 else 'Normal'}")
                
                if degree_diff < 8:
                    p_trait['label'] = f"Dominant Feature: {p_trait['label']}"
                    p_trait['confidence'] = "High"
                    traits.insert(1, p_trait) 
                else:
                    traits.append(p_trait)
            
            # --- FEATURE 3: NAKSHATRA (The Nuance) ---
            nak_index = int(asc_degree / 13.333333)
            logging.info(f"🌙 Nakshatra calculation: {asc_degree}° / 13.333 = {nak_index}")
            nak_trait = self._get_nakshatra_traits(nak_index)
            if nak_trait:
                logging.info(f"Nakshatra trait: {nak_trait['label']}")
                traits.append(nak_trait)
            
            # Fallback: If no planets, use Sign Build
            if not occupants and len(traits) < 2:
                sign_trait = self._get_sign_traits(asc_sign)
                logging.info(f"Sign trait fallback: {sign_trait['label']}")
                traits.append(sign_trait)

            logging.info(f"Final traits count: {len(traits)}")
            return traits

        except Exception as e:
            logging.error(f"❌ Physical Scan Error: {e}")
            return []

    def _get_planet_traits(self, planet: str) -> Dict:
        """
        Detailed Physical Markers for Planets in 1st House.
        Includes specific classical indicators (Hair, Weight, Humps, etc.)
        """
        pt = {
            'Sun': (
                "High forehead, sparse hair/early balding, or commanding vitality", 
                "forehead"
            ),
            'Moon': (
                "Round face, fleshy body, expressive eyes, or fluctuating weight", 
                "face_shape"
            ),
            'Mars': (
                "Reddish eyes, distinct scar/mark on face, or athletic build", 
                "facial_mark"
            ),
            'Mercury': (
                "Youthful/Boyish look, quick mannerisms, or articulate speech", 
                "vibe"
            ),
            'Jupiter': (
                "Tendency to be overweight/stout, large forehead, or golden glow", 
                "build"
            ),
            'Venus': (
                "Charming features, curly/wavy hair, dimples, or attractive eyes", 
                "hair"
            ),
            'Saturn': (
                "Excess body hair, prominent veins/teeth, or tall/lean frame", 
                "body_hair"
            ),
            'Rahu': (
                "Distinctive gaze, glasses/weak eyesight, or unconventional appearance", 
                "eyes"
            ),
            'Ketu': (
                "Slight hunch/hump on upper back, mysterious look, or scar near eye", 
                "posture"
            )
        }
        
        desc, feat = pt.get(planet, ("Distinctive energy", "vibe"))
        return {
            "feature": feat,
            "label": desc,
            "confidence": "High", 
            "source": f"{planet} in 1st House"
        }

    def _analyze_complexion(self, sign_idx: int, occupants: List[Dict]) -> Dict:
        # 1. Check Dominant Planet
        if occupants:
            dom_planet = occupants[0]['name']
            planet_colors = {
                'Sun': "Reddish or Copper-toned complexion",
                'Moon': "Fair, pale, or luminous complexion",
                'Mars': "Reddish, flushed, or warm complexion",
                'Mercury': "Wheatish or Olive skin tone",
                'Jupiter': "Golden, bright, or fair complexion",
                'Venus': "Fair, glowing, or clear complexion",
                'Saturn': "Tanned, earthy, or darker complexion",
                'Rahu': "Smoky, shadowed, or unconventional tone",
                'Ketu': "Pallid, matte, or unique complexion"
            }
            return {
                "feature": "complexion",
                "label": planet_colors.get(dom_planet, "Distinctive complexion"),
                "confidence": "High",
                "source": f"{dom_planet} in 1st House"
            }
            
        # 2. Fallback to Sign
        sign_colors = {
            0: "Reddish or fair complexion", 1: "Wheatish or earthy complexion",
            2: "Fair to wheatish complexion", 3: "Pale or fair complexion",
            4: "Reddish or glowing complexion", 5: "Wheatish or pale complexion",
            6: "Fair or balanced skin tone", 7: "Darker or intense complexion",
            8: "Golden or reddish complexion", 9: "Wheatish or tanned complexion",
            10: "Tan or unique complexion", 11: "Fair or smooth complexion"
        }
        return {
            "feature": "complexion",
            "label": sign_colors.get(sign_idx, "Normal complexion"),
            "confidence": "Medium",
            "source": "Ascendant Sign"
        }

    def _get_occupants_detailed(self, chart: Dict, asc_sign: int) -> List[Dict]:
        occupants = []
        logging.info(f"Checking planets for 1st house (sign {asc_sign}):")
        for planet, data in chart['planets'].items():
            if planet in ['Uranus', 'Neptune', 'Pluto', 'Gulika', 'Mandi']: continue
            planet_sign = int(data['longitude'] / 30)
            logging.info(f"  {planet}: {data['longitude']:.2f}° -> Sign {planet_sign}")
            if planet_sign == asc_sign:
                occupants.append({
                    'name': planet,
                    'degree': data['longitude'] % 30
                })
        return occupants

    def _get_sign_traits(self, sign_idx: int) -> Dict:
        traits = {
            0: ("Aries", "Athletic build, prominent eyebrows, or quick movements"),
            1: ("Taurus", "Solid/Sturdy build, thick neck, or attractive face"),
            2: ("Gemini", "Tall/Slender frame, expressive hands, or youthful look"),
            3: ("Cancer", "Round face, soft features, or expressive eyes"),
            4: ("Leo", "Broad shoulders, thick hair (mane-like), or commanding presence"),
            5: ("Virgo", "Youthful appearance, clear skin, or bright eyes"),
            6: ("Libra", "Symmetrical features, charming smile, or dimples"),
            7: ("Scorpio", "Intense gaze, deep-set eyes, or strong physique"),
            8: ("Sagittarius", "Tall frame, high forehead, or open/friendly face"),
            9: ("Capricorn", "Lean/Bony structure, prominent knees/teeth, or serious look"),
            10: ("Aquarius", "Unconventional looks, tall, or distinct side profile"),
            11: ("Pisces", "Dreamy/Watery eyes, soft physique, or shorter height")
        }
        name, desc = traits.get(sign_idx, ("Unknown", "Distinctive features"))
        return {
            "feature": "overall_build",
            "label": desc,
            "confidence": "Medium",
            "source": f"{name} Ascendant"
        }

    def _get_nakshatra_traits(self, nak_index: int) -> Dict:
        nak_map = {
            0: ("Ashwini", "Youthful appearance, large eyes, or broad forehead"),
            1: ("Bharani", "Medium build, prominent forehead, or nice teeth"),
            2: ("Krittika", "Commanding presence, prominent nose, or strong appetite"),
            3: ("Rohini", "Beautiful/Magnetic eyes, slim build, or attractive smile"),
            4: ("Mrigashira", "Wandering/Restless eyes, thin limbs, or sharp features"),
            5: ("Ardra", "Strong structure, distinct nose, or curly hair"),
            6: ("Punarvasu", "Long fingers/nose, contented look, or curly hair"),
            7: ("Pushya", "Square face, serious/calm demeanor, or strong chest"),
            8: ("Ashlesha", "Penetrating/Hypnotic gaze, square face, or gap in teeth"),
            9: ("Magha", "Prominent nose, lion-like chin/jaw, or confident walk"),
            10: ("Purva Phalguni", "Attractive features, soft speech, or prominent neck"),
            11: ("Uttara Phalguni", "Large/Bright eyes, prominent nose, or tall build"),
            12: ("Hasta", "Active hands/gestures, charming smile, or smaller build"),
            13: ("Chitra", "Beautiful eyes, charismatic body language, or well-proportioned"),
            14: ("Swati", "Gentle appearance, compassionate eyes, or flexible body"),
            15: ("Vishakha", "Round face, distinct speech style, or intense focus"),
            16: ("Anuradha", "Attractive chest/shoulders, soft eyes, or friendly look"),
            17: ("Jyeshtha", "Serious gaze, muscular or wiry build, or prominent ears"),
            18: ("Mula", "Firm jaw, expressive eyes, or distinct walk"),
            19: ("Purva Ashadha", "Tall stature, bright teeth, or graceful movements"),
            20: ("Uttara Ashadha", "Broad forehead, long nose, or fair/clear complexion"),
            21: ("Shravana", "Distinct gait/walk, wide chest, or listening posture"),
            22: ("Dhanishta", "Radiant smile, energetic vibe, or fleshy lips"),
            23: ("Shatabhisha", "Wide forehead, bright/sharp eyes, or prominent cheekbones"),
            24: ("Purva Bhadrapada", "Medium height, uplifted ankles, or serious face"),
            25: ("Uttara Bhadrapada", "Attractive appearance, calm eyes, or balanced body"),
            26: ("Revati", "Perfectly proportioned body, beautiful feet, or sweet smile")
        }
        
        data = nak_map.get(nak_index)
        if data:
            return {
                "feature": "nakshatra_trait",
                "label": data[1],
                "confidence": "High",
                "source": f"{data[0]} Nakshatra"
            }
        return None
    
    def _get_sign_name(self, sign_idx: int) -> str:
        names = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        return names[sign_idx] if 0 <= sign_idx < 12 else "Unknown"