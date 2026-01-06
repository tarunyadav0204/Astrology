from typing import Dict, Any, List

class JaiminiFullAnalyzer:
    """
    Jaimini Logic Engine. Translates planetary positions into Sutra-based predictions.
    """

    def __init__(self, chart_data: Dict[str, Any], karaka_data: Dict[str, Any], points: Dict[str, Any], chara_dasha_data: Dict[str, Any] = None):
        self.chart = chart_data
        self.points = points
        self.karakas = karaka_data.get('chara_karakas', {})
        self.planets = chart_data.get('planets', {})
        self.chara_dasha = chara_dasha_data
        self.asc_sign = int(chart_data.get('ascendant', 0) / 30)

        # Map Planet Name -> Sign Index
        self.planet_positions = {p: data['sign'] for p, data in self.planets.items()}
        
        # Map Karaka -> Planet Name (e.g., 'Atmakaraka': 'Sun')
        self.karaka_map = {k: v['planet'] for k, v in self.karakas.items()}
        
        # Create sign map for quick lookup
        self.sign_map = {i: [] for i in range(12)}
        for p, data in self.planets.items():
            self.sign_map[data['sign']].append(p)

    def get_jaimini_report(self) -> Dict[str, Any]:
        """Generates the comprehensive Jaimini analysis."""
        # Identify active dasha signs for relative analysis
        current_md_sign = None
        current_ad_sign = None
        if self.chara_dasha:
            periods = self.chara_dasha.get('periods', [])
            current_md = next((p for p in periods if p.get('is_current')), {})
            current_md_sign = current_md.get('sign_id')
            
            # Debug logging
            print(f"\n🔍 JAIMINI ANALYZER DEBUG:")
            print(f"   Current MD: {current_md.get('sign_name')} (ID: {current_md_sign})")
            
            # Get current antardasha
            antardashas = current_md.get('antardashas', [])
            current_ad = next((a for a in antardashas if a.get('is_current')), {})
            current_ad_sign = current_ad.get('sign_id')
            print(f"   Current AD: {current_ad.get('sign_name')} (ID: {current_ad_sign})")
            print(f"   Total ADs available: {len(antardashas)}")
        
        # Get Karaka signs from the karaka data structure
        ak_data = self.karakas.get('Atmakaraka', {})
        amk_data = self.karakas.get('Amatyakaraka', {})
        ak_sign = ak_data.get('sign')
        amk_sign = amk_data.get('sign')
        print(f"   AK Sign: {ak_sign}, AmK Sign: {amk_sign}")
        
        return {
            "relative_views": {
                "mahadasha_lagna": self._analyze_relative_lagna(current_md_sign, "Mahadasha Sign"),
                "antardasha_lagna": self._analyze_relative_lagna(current_ad_sign, "Antardasha Sign"),
                "atmakaraka_lagna": self._analyze_relative_lagna(ak_sign, "Atmakaraka (AK)"),
                "amatyakaraka_lagna": self._analyze_relative_lagna(amk_sign, "Amatyakaraka (AmK)")
            },
            "raj_yogas": self._check_jaimini_yogas(),
            "sutra_logic": {
                "wealth_from_al": self._analyze_arudha_wealth(),
                "marriage_from_ul": self._analyze_upapada_longevity(),
                "talent_from_kl": self._analyze_karkamsa_skills()
            },
            "sign_aspects": self._calculate_all_aspects(),
            "karaka_status": self._analyze_karaka_positions()
        }

    # -------------------------------------------------------------------------
    # RELATIVE LAGNA ENGINE
    # -------------------------------------------------------------------------
    def _analyze_relative_lagna(self, base_sign: int, label: str) -> Dict[str, Any]:
        """Creates a virtual chart perspective from a specific sign/karaka."""
        if base_sign is None:
            return {"perspective": label, "base_sign": None, "houses": {}}
        
        relative_houses = {}
        # Pre-calculate houses 1-12 from this base sign
        for h in range(1, 13):
            target_sign = (base_sign + (h - 1)) % 12
            relative_houses[f"house_{h}"] = {
                "sign_id": target_sign,
                "sign_name": self._get_sign_name(target_sign),
                "planets": self.sign_map[target_sign]
            }
            
        return {
            "perspective": label,
            "base_sign": base_sign,
            "base_sign_name": self._get_sign_name(base_sign),
            "houses": relative_houses
        }

    # -------------------------------------------------------------------------
    # SUTRA ANALYSIS METHODS
    # -------------------------------------------------------------------------
    def _analyze_arudha_wealth(self) -> Dict[str, Any]:
        """Sutras for 2nd and 11th from Arudha Lagna (AL)."""
        al_sign = self.points['arudha_lagna']['sign_id']
        second_sign = (al_sign + 1) % 12
        eleventh_sign = (al_sign + 10) % 12
        p_2nd = self.sign_map[second_sign]
        p_11th = self.sign_map[eleventh_sign]
        
        is_dhana = any(p in ['Jupiter', 'Venus', 'Moon'] for p in p_2nd + p_11th)
        return {
            "dhana_yoga_status": "Strong" if is_dhana else "Average",
            "source_planets": p_2nd + p_11th,
            "note": "Benefics in 2nd/11th from AL indicate natural flow of wealth."
        }

    def _analyze_upapada_longevity(self) -> Dict[str, Any]:
        """Longevity of marriage based on the 2nd from Upapada (UL)."""
        ul_sign = self.points['upapada_lagna']['sign_id']
        second_from_ul = (ul_sign + 1) % 12
        planets = self.sign_map[second_from_ul]
        malefics = [p for p in planets if p in ['Saturn', 'Mars', 'Rahu', 'Ketu']]
        return {
            "marriage_stability": "Challenged" if malefics else "High",
            "blocking_factors": malefics,
            "ul_sign": self.points['upapada_lagna']['sign_name']
        }

    def _analyze_karkamsa_skills(self) -> List[str]:
        """Interpretations for Atmakaraka's position in Navamsa."""
        kl_sign = self.points['karkamsa_lagna']['sign_id']
        planets = self.sign_map.get(kl_sign, [])
        results = []
        if 'Ketu' in planets: results.append("Natural affinity for Mathematics, Coding, or Astrology.")
        if 'Sun' in planets: results.append("Innate leadership and desire for public service.")
        if 'Mercury' in planets: results.append("Business acumen and commercial talent.")
        if 'Jupiter' in planets: results.append("Teaching, counseling, or spiritual guidance abilities.")
        if 'Venus' in planets: results.append("Artistic talents and creative expression.")
        return results

    # -------------------------------------------------------------------------
    # 1. RASHI DRISHTI (Sign Aspects)
    # -------------------------------------------------------------------------
    def _calculate_all_aspects(self) -> Dict[int, List[int]]:
        """
        Calculates which signs aspect which signs.
        Rule:
        - Moveable (1,4,7,10) aspects Fixed (2,5,8,11) EXCEPT adjacent.
        - Fixed (2,5,8,11) aspects Moveable (1,4,7,10) EXCEPT adjacent.
        - Dual (3,6,9,12) aspects other Duals.
        """
        aspect_map = {}
        for sign in range(12):
            aspect_map[sign] = self._get_rashi_drishti(sign)
        return aspect_map

    def _get_rashi_drishti(self, sign: int) -> List[int]:
        # Signs are 0-indexed (Aries=0)
        # Groups:
        # Moveable (Chara): 0, 3, 6, 9 (Aries, Cancer, Libra, Cap)
        # Fixed (Sthira): 1, 4, 7, 10 (Taurus, Leo, Scorpio, Aqu)
        # Dual (Dviswabhava): 2, 5, 8, 11 (Gemini, Virgo, Sag, Pis)
        
        aspects = []
        
        # Moveable aspects Fixed (except adjacent)
        if sign in [0, 3, 6, 9]: 
            # Aries(0) -> Leo(4), Scorp(7), Aqu(10). (Skip Tau(1))
            # Cancer(3) -> Scorp(7), Aqu(10), Tau(1). (Skip Leo(4))
            fixed = [1, 4, 7, 10]
            for f in fixed:
                if f != (sign + 1) % 12: # Check forward adjacent (e.g Aries->Taurus)
                     aspects.append(f)
                     
        # Fixed aspects Moveable (except adjacent)
        elif sign in [1, 4, 7, 10]:
            # Taurus(1) -> Cancer(3), Lib(6), Cap(9). (Skip Aries(0))
            moveable = [0, 3, 6, 9]
            for m in moveable:
                if m != (sign - 1 + 12) % 12: # Check backward adjacent (e.g Taurus->Aries)
                    aspects.append(m)
                    
        # Dual aspects other Duals
        elif sign in [2, 5, 8, 11]:
            dual = [2, 5, 8, 11]
            for d in dual:
                if d != sign:
                    aspects.append(d)
                    
        return aspects

    # -------------------------------------------------------------------------
    # 2. JAIMINI YOGAS (The Predictive Core)
    # -------------------------------------------------------------------------
    def _check_jaimini_yogas(self) -> List[Dict[str, str]]:
        """
        Checks for connection between specific Karakas.
        Connection = Conjunction OR Rashi Drishti.
        """
        yogas = []
        
        # Karaka Keys
        AK = self.karaka_map.get('Atmakaraka')
        AmK = self.karaka_map.get('Amatyakaraka')
        PK = self.karaka_map.get('Putrakaraka')
        DK = self.karaka_map.get('Darakaraka')
        MK = self.karaka_map.get('Matrukaraka')
        
        # 1. Jaimini Raj Yoga (AK + AmK) - The Highest Yoga
        if self._are_connected(AK, AmK):
            yogas.append({
                "name": "Jaimini Raj Yoga",
                "actors": f"{AK} (AK) + {AmK} (AmK)",
                "effect": "High status, career success, and authority.",
                "strength": "High"
            })
            
        # 2. Minister Yoga (AK + MK)
        if self._are_connected(AK, MK):
            yogas.append({
                "name": "Amatya-Matru Yoga",
                "actors": f"{AK} (AK) + {MK} (MK)",
                "effect": "Success through education, home, or mother.",
                "strength": "Medium"
            })
            
        # 3. Creator Yoga (AK + PK)
        if self._are_connected(AK, PK):
            yogas.append({
                "name": "Atma-Putra Yoga",
                "actors": f"{AK} (AK) + {PK} (PK)",
                "effect": "Creative genius, good children, and followers.",
                "strength": "High"
            })
            
        # 4. Wealth Yoga (AK + DK)
        if self._are_connected(AK, DK):
            yogas.append({
                "name": "Atma-Dara Yoga",
                "actors": f"{AK} (AK) + {DK} (DK)",
                "effect": "Wealth through partnerships and business.",
                "strength": "High"
            })

        return yogas

    def _are_connected(self, p1: str, p2: str) -> bool:
        """Checks if two planets are connected via Jaimini rules."""
        if not p1 or not p2: return False
        
        # Check if planets exist in chart data
        if p1 not in self.planet_positions or p2 not in self.planet_positions:
            return False
        
        s1 = self.planet_positions[p1]
        s2 = self.planet_positions[p2]
        
        # 1. Conjunction (Same Sign)
        if s1 == s2: return True
        
        # 2. Rashi Drishti (Mutual Aspect)
        # Check if s1 aspects s2 OR s2 aspects s1 (It is always mutual in Jaimini)
        aspects_of_s1 = self._get_rashi_drishti(s1)
        if s2 in aspects_of_s1: return True
        
        return False

    def _analyze_karaka_positions(self) -> Dict[str, Any]:
        """Provides context on where the Soul (AK) and Career (AmK) are placed."""
        ak = self.karaka_map.get('Atmakaraka')
        amk = self.karaka_map.get('Amatyakaraka')
        
        result = {}
        
        if ak and ak in self.planet_positions:
            result["atmakaraka_placement"] = {
                "planet": ak,
                "sign": self._get_sign_name(self.planet_positions[ak]),
                "description": "The King of the chart."
            }
        
        if amk and amk in self.planet_positions:
            result["amatyakaraka_placement"] = {
                "planet": amk,
                "sign": self._get_sign_name(self.planet_positions[amk]),
                "description": "The Minister/Executer of the chart."
            }
        
        return result

    def _get_sign_name(self, idx: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[idx]
