import math
from typing import Dict, List, Any
from datetime import datetime
from .nakshatra_calculator import NakshatraCalculator
from .chara_karaka_calculator import CharaKarakaCalculator
from .chart_calculator import ChartCalculator

class BlankChartContextBuilder:
    """
    Blank Chart Context Builder - Creates stunning predictions without birth details
    Uses Fixed Structural Karma from classical texts for maximum impact
    """
    
    # Sign names for reference
    SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    def __init__(self):
        self.nakshatra_calc = NakshatraCalculator()
        
        # Nakshatra Fated Years from classical research
        self.nakshatra_fated_years = {
            "Ashwini": [20, 28, 40], "Bharani": [24, 33, 48], "Krittika": [21, 30, 42],
            "Rohini": [24, 36, 48], "Mrigashira": [28, 32, 45], "Ardra": [25, 33, 42],
            "Punarvasu": [24, 32, 50], "Pushya": [28, 36, 48], "Ashlesha": [30, 32, 42],
            "Magha": [25, 33, 44], "Purva Phalguni": [28, 38, 50], "Uttara Phalguni": [24, 32, 52],
            "Hasta": [30, 32, 45], "Chitra": [24, 32, 48], "Svati": [30, 33, 45],
            "Vishakha": [21, 28, 35], "Anuradha": [28, 35, 48], "Jyeshtha": [21, 27, 36],
            "Mula": [24, 33, 48], "Purva Ashadha": [24, 32, 45], "Uttara Ashadha": [28, 31, 38],
            "Shravana": [30, 32, 45], "Dhanishta": [24, 32, 48], "Shatabhisha": [28, 30, 42],
            "Purva Bhadrapada": [24, 33, 48], "Uttara Bhadrapada": [28, 35, 50], "Revati": [21, 24, 32]
        }
    
    def get_sign_name(self, sign_num):
        """Get sign name from number"""
        return self.SIGN_NAMES[sign_num] if 0 <= sign_num < 12 else 'Unknown'
    
    def calculate_age_from_birth_data(self, birth_data: Dict) -> int:
        """Calculate current age from birth data"""
        try:
            birth_date = datetime.strptime(birth_data['date'], '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
        except:
            return 25  # Default age if calculation fails
    
    def _calculate_bcp_activation(self, chart_data: Dict, age: int) -> Dict:
        """Bhrigu Chakra Paddhati: Age-based house activation"""
        active_house_idx = (age - 1) % 12
        active_house_num = active_house_idx + 1
        
        # Get planets in the activated house
        occupants = []
        for planet, data in chart_data.get('planets', {}).items():
            if data.get('house') == active_house_num:
                occupants.append(planet)
        
        # Get sign of activated house
        ascendant = chart_data.get('ascendant', 0)
        lagna_sign_num = int(ascendant / 30)
        active_sign_num = ((lagna_sign_num - 1 + active_house_idx) % 12) + 1
        active_sign = self.get_sign_name(active_sign_num - 1)  # Convert to 0-based index
        
        return {
            "current_age": age,
            "activated_house": active_house_num,
            "activated_sign": active_sign,
            "house_occupants": occupants,
            "cycle_number": math.ceil(age / 12),
            "house_meaning": self._get_house_meaning(active_house_num)
        }
    
    def _get_house_meaning(self, house_num: int) -> str:
        """Get house significance for BCP"""
        meanings = {
            1: "Self, personality, new beginnings",
            2: "Wealth, family, speech, values",
            3: "Courage, siblings, short travels",
            4: "Home, mother, property, emotions",
            5: "Children, creativity, intelligence",
            6: "Health, enemies, service, daily work",
            7: "Marriage, partnerships, business",
            8: "Transformation, occult, inheritance",
            9: "Fortune, father, higher learning",
            10: "Career, reputation, authority",
            11: "Gains, friends, aspirations",
            12: "Losses, spirituality, foreign lands"
        }
        return meanings.get(house_num, "Unknown")
    
    def _get_nadi_elemental_clusters(self, chart_data: Dict) -> Dict:
        """Bhrigu Nandi Nadi: Elemental 1-5-9 clustering"""
        clusters = {"Fire": [], "Earth": [], "Air": [], "Water": []}
        
        for planet, data in chart_data.get('planets', {}).items():
            sign_num = data.get('sign')
            if sign_num is not None:
                element = self._get_sign_element(sign_num)
                clusters[element].append(planet)
        
        return clusters
    
    def _get_sign_element(self, sign_num: int) -> str:
        """Get element of sign"""
        fire_signs = [0, 4, 8]  # Aries, Leo, Sagittarius (0-based)
        earth_signs = [1, 5, 9]  # Taurus, Virgo, Capricorn (0-based)
        air_signs = [2, 6, 10]  # Gemini, Libra, Aquarius (0-based)
        water_signs = [3, 7, 11]  # Cancer, Scorpio, Pisces (0-based)
        
        if sign_num in fire_signs:
            return "Fire"
        elif sign_num in earth_signs:
            return "Earth"
        elif sign_num in air_signs:
            return "Air"
        elif sign_num in water_signs:
            return "Water"
        return "Unknown"
    
    def _get_sudarshana_chakra(self, chart_data: Dict) -> Dict:
        """Triple perspective analysis"""
        planets = chart_data.get('planets', {})
        
        ascendant = chart_data.get('ascendant', 0)
        lagna_sign = int(ascendant / 30)
        
        return {
            "lagna_physical": self.get_sign_name(lagna_sign),
            "moon_mental": self.get_sign_name(planets.get('Moon', {}).get('sign', 0)),
            "sun_soul": self.get_sign_name(planets.get('Sun', {}).get('sign', 0))
        }
    
    def _detect_lal_kitab_debts(self, chart_data: Dict) -> List[str]:
        """Detect Lal Kitab ancestral debts"""
        debts = []
        planets = chart_data.get('planets', {})
        
        # Forefather's Debt: Jupiter afflicted by Rahu/Ketu/Saturn
        jup_house = planets.get('Jupiter', {}).get('house')
        if jup_house:
            afflicting_planets = []
            for planet in ['Rahu', 'Ketu', 'Saturn']:
                if planets.get(planet, {}).get('house') == jup_house:
                    afflicting_planets.append(planet)
            
            if afflicting_planets:
                debts.append(f"Forefather's Debt (Jupiter with {', '.join(afflicting_planets)})")
        
        # Mother's Debt: Ketu in 4th house
        if planets.get('Ketu', {}).get('house') == 4:
            debts.append("Mother's Debt (Ketu in 4th house)")
        
        # Brother's Debt: Mars in 3rd house with malefics
        mars_house = planets.get('Mars', {}).get('house')
        if mars_house == 3:
            malefics_in_3rd = [p for p in ['Saturn', 'Rahu', 'Ketu'] 
                              if planets.get(p, {}).get('house') == 3]
            if malefics_in_3rd:
                debts.append("Brother's Debt (Mars in 3rd with malefics)")
        
        # Wife's Debt: Venus afflicted in 7th
        if planets.get('Venus', {}).get('house') == 7:
            venus_afflicted = any(planets.get(p, {}).get('house') == 7 
                                for p in ['Saturn', 'Rahu', 'Ketu'])
            if venus_afflicted:
                debts.append("Wife's Debt (Venus afflicted in 7th)")
        
        return debts
    
    def _get_nakshatra_triggers(self, chart_data: Dict, age: int) -> Dict:
        """Check for Nakshatra fated years"""
        moon_data = chart_data.get('planets', {}).get('Moon', {})
        
        # Try to get nakshatra from moon data or calculate it
        moon_nakshatra = moon_data.get('nakshatra', 'Unknown')
        if moon_nakshatra == 'Unknown':
            # Calculate nakshatra from longitude if available
            moon_longitude = moon_data.get('longitude')
            if moon_longitude is not None:
                # Each nakshatra is 13.333... degrees
                nakshatra_index = int(moon_longitude / 13.333333333333334)
                nakshatra_names = [
                    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
                    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
                    "Hasta", "Chitra", "Svati", "Vishakha", "Anuradha", "Jyeshtha",
                    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
                ]
                if 0 <= nakshatra_index < len(nakshatra_names):
                    moon_nakshatra = nakshatra_names[nakshatra_index]
        
        fated_years = self.nakshatra_fated_years.get(moon_nakshatra, [])
        active_triggers = [year for year in fated_years if abs(age - year) <= 1]
        
        return {
            "birth_star": moon_nakshatra,
            "birth_star_pada": moon_data.get('nakshatra_pada', 1),
            "fated_years": fated_years,
            "active_fated_years": active_triggers,
            "is_fated_period": len(active_triggers) > 0
        }
    
    def _get_yogini_dasha_trigger(self, chart_data: Dict, age: int) -> Dict:
        """Check current Yogini Dasha for triggers"""
        try:
            from .yogini_dasha_calculator import YoginiDashaCalculator
            yogini_calc = YoginiDashaCalculator()
            
            # Calculate Yogini Dasha for current age
            moon_data = chart_data.get('planets', {}).get('Moon', {})
            moon_nakshatra = moon_data.get('nakshatra')
            
            if moon_nakshatra:
                current_dasha = yogini_calc.get_current_dasha_at_age(moon_nakshatra, age)
                return {
                    "current_yogini": current_dasha.get('yogini_name', 'Unknown'),
                    "dasha_years": current_dasha.get('duration', 0),
                    "remaining_years": current_dasha.get('remaining', 0)
                }
        except:
            pass
        
        return {"current_yogini": "Unknown", "dasha_years": 0, "remaining_years": 0}
    
    def build_context(self, birth_data: Dict) -> Dict:
        """
        Main method to build blank chart context for stunning predictions
        """
        try:
            # Calculate chart using ChartCalculator
            chart_calc = ChartCalculator({})
            
            # Convert dict to proper format for chart calculation
            from pydantic import BaseModel
            
            class BirthData(BaseModel):
                name: str = "User"
                date: str
                time: str
                latitude: float
                longitude: float
                timezone: str
                place: str = ""
                gender: str = ""
            
            # Create BirthData object
            birth_obj = BirthData(
                name=birth_data.get('name', 'User'),
                date=birth_data['date'],
                time=birth_data['time'],
                latitude=birth_data['latitude'],
                longitude=birth_data['longitude'],
                timezone=birth_data['timezone'],
                place=birth_data.get('place', ''),
                gender=birth_data.get('gender', '')
            )
            
            # Calculate chart
            chart_result = chart_calc.calculate_chart(birth_obj)
            chart_data = chart_result
            
            # Calculate age
            age = self.calculate_age_from_birth_data(birth_data)
            
            # Get Jaimini Karakas using chart data
            jaimini_karakas = {}
            arudha_data = {}
            
            try:
                karaka_calc = CharaKarakaCalculator(chart_data)
                jaimini_karakas = karaka_calc.calculate_chara_karakas()
            except Exception as e:
                print(f"Karaka calculation error: {e}")
            
            # Build all pillars
            context = {
                "metadata": {
                    "module_type": "BLANK_CHART_DESTINY_MAP",
                    "target_age": age,
                    "calculation_timestamp": datetime.now().isoformat()
                },
                "pillars": {
                    "bcp_activation": self._calculate_bcp_activation(chart_data, age),
                    "nadi_elemental_links": self._get_nadi_elemental_clusters(chart_data),
                    "sudarshana_chakra": self._get_sudarshana_chakra(chart_data),
                    "jaimini_markers": {
                        "atmakaraka": jaimini_karakas.get('Atmakaraka', {}).get('planet'),
                        "amatyakaraka": jaimini_karakas.get('Amatyakaraka', {}).get('planet'),
                        "arudha_lagna_sign": arudha_data.get('arudha_lagna_sign'),
                        "arudha_lagna_house": arudha_data.get('arudha_lagna_house')
                    },
                    "lal_kitab_layer": {
                        "ancestral_debts": self._detect_lal_kitab_debts(chart_data),
                        "planetary_houses": {p: d.get('house') for p, d in chart_data.get('planets', {}).items()}
                    },
                    "nakshatra_triggers": self._get_nakshatra_triggers(chart_data, age),
                    "yogini_dasha": self._get_yogini_dasha_trigger(chart_data, age)
                },
                "stun_factors": self._identify_stun_factors(chart_data, age)
            }
            
            return context
            
        except Exception as e:
            print(f"Error in BlankChartContextBuilder: {str(e)}")
            return {"error": str(e), "metadata": {"module_type": "BLANK_CHART_DESTINY_MAP"}}
    
    def _identify_stun_factors(self, chart_data: Dict, age: int) -> List[str]:
        """Identify the most stunning elements for immediate impact"""
        stun_factors = []
        
        # BCP House activation
        active_house = ((age - 1) % 12) + 1
        if active_house in [1, 7, 10]:  # Major life areas
            stun_factors.append(f"MAJOR_LIFE_ACTIVATION_HOUSE_{active_house}")
        
        # Nakshatra fated years
        moon_nak = chart_data.get('planets', {}).get('Moon', {}).get('nakshatra')
        if moon_nak and moon_nak in self.nakshatra_fated_years:
            fated_years = self.nakshatra_fated_years[moon_nak]
            if any(abs(age - year) <= 1 for year in fated_years):
                stun_factors.append("NAKSHATRA_FATED_PERIOD")
        
        # Lal Kitab debts
        debts = self._detect_lal_kitab_debts(chart_data)
        if debts:
            stun_factors.append("ANCESTRAL_KARMA_ACTIVE")
        
        # Atmakaraka in specific houses
        try:
            karakas = chart_data.get('jaimini_karakas', {})
            atmakaraka_planet = karakas.get('Atmakaraka', {}).get('planet')
            if atmakaraka_planet:
                ak_house = chart_data.get('planets', {}).get(atmakaraka_planet, {}).get('house_number')
                if ak_house in [8, 12]:  # Transformation houses
                    stun_factors.append("SOUL_TRANSFORMATION_ACTIVE")
        except:
            pass
        
        return stun_factors