from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List

class SudarshanaDashaCalculator:
    """
    Calculates the Sudarshana Chakra Dasha 'Yearly Clock' 
    and identifies exact dates when the clock hits natal planets.
    1 degree per year progression from Lagna/Moon/Sun.
    """
    
    def __init__(self, chart_data: Dict[str, Any], birth_data: Dict[str, Any]):
        self.chart_data = chart_data
        self.lagna_degree = chart_data.get('ascendant', 0) % 360
        self.moon_degree = chart_data.get('planets', {}).get('Moon', {}).get('longitude', 0) % 360
        self.sun_degree = chart_data.get('planets', {}).get('Sun', {}).get('longitude', 0) % 360
        self.birth_date = datetime.strptime(birth_data['date'], '%Y-%m-%d')

    def calculate_precision_triggers(self, target_year: int) -> Dict[str, Any]:
        """Maps the 360-degree zodiac to a timeline for a specific year with triple perspective"""
        planets = self.chart_data.get('planets', {})
        current_age = target_year - self.birth_date.year
        
        # Active house (12-year cycle, age 0 = house 1)
        active_house = (current_age % 12) + 1
        
        # Calculate from all three perspectives
        lagna_triggers = self._calculate_triggers_from_point(self.lagna_degree, current_age, target_year, planets, 'Lagna')
        moon_triggers = self._calculate_triggers_from_point(self.moon_degree, current_age, target_year, planets, 'Moon')
        sun_triggers = self._calculate_triggers_from_point(self.sun_degree, current_age, target_year, planets, 'Sun')
        
        # Merge and identify double/triple confirmations
        all_triggers = self._merge_triggers(lagna_triggers, moon_triggers, sun_triggers)
        
        # If no triggers, add house entry date as fallback
        if not all_triggers:
            house_entry = self._calculate_house_entry_date(current_age, active_house)
            all_triggers = [house_entry]

        return {
            "current_age": current_age,
            "active_house": active_house,
            "year_focus": self._get_house_signification(active_house),
            "precision_triggers": all_triggers
        }
    
    def _calculate_triggers_from_point(self, start_degree: float, current_age: int, target_year: int, planets: Dict, perspective: str) -> List[Dict]:
        """Calculate triggers from a specific starting point (Lagna/Moon/Sun)"""
        triggers = []
        
        for planet_name, data in planets.items():
            if planet_name in ['Gulika', 'Mandi', 'InduLagna']:
                continue
            
            p_long = data.get('longitude', 0)
            distance = (p_long - start_degree) % 360
            age_at_hit = distance / 30
            
            # Find the correct cycle
            while age_at_hit < current_age:
                age_at_hit += 12
            
            # Check if hit falls in target year
            year_birthday = self.birth_date + relativedelta(years=int(age_at_hit))
            remaining_fraction = age_at_hit % 1
            days_in_year = 366 if (year_birthday.year % 4 == 0 and year_birthday.year % 100 != 0) or (year_birthday.year % 400 == 0) else 365
            extra_days = remaining_fraction * days_in_year
            hit_date = year_birthday + timedelta(days=extra_days)
            
            if hit_date.year == target_year:
                window_start = (hit_date - timedelta(days=1.5)).strftime('%Y-%m-%d')
                window_end = (hit_date + timedelta(days=1.5)).strftime('%Y-%m-%d')
                
                triggers.append({
                    "date": hit_date.strftime('%Y-%m-%d'),
                    "window_start": window_start,
                    "window_end": window_end,
                    "planet": planet_name,
                    "natal_degree": round(p_long % 30, 2),
                    "sign": self._get_sign_name(int(p_long / 30)),
                    "perspective": perspective,
                    "significance": self._get_significance(planet_name),
                    "intensity": self._get_intensity(planet_name)
                })
        
        return triggers
    
    def _merge_triggers(self, lagna: List, moon: List, sun: List) -> List[Dict]:
        """Merge triggers using proximity logic - same planet within 7 days = confirmation"""
        from datetime import datetime
        
        combined = lagna + moon + sun
        combined.sort(key=lambda x: (x['planet'], x['date']))
        
        merged = []
        i = 0
        while i < len(combined):
            current = combined[i]
            planet = current['planet']
            base_date = datetime.strptime(current['date'], '%Y-%m-%d')
            
            # Collect all triggers for same planet within 7 days
            group = [current]
            j = i + 1
            while j < len(combined) and combined[j]['planet'] == planet:
                next_date = datetime.strptime(combined[j]['date'], '%Y-%m-%d')
                if abs((next_date - base_date).days) <= 7:
                    group.append(combined[j])
                    j += 1
                else:
                    break
            
            # Build merged trigger
            perspectives = [t['perspective'] for t in group]
            count = len(set(perspectives))
            
            merged_trigger = group[0].copy()
            merged_trigger['perspectives'] = perspectives
            
            if count == 3:
                merged_trigger['confirmation'] = 'Triple - Guaranteed Event'
                merged_trigger['intensity'] = 'Maximum'
            elif count == 2:
                merged_trigger['confirmation'] = 'Double - High Probability'
            else:
                merged_trigger['confirmation'] = 'Single'
            
            merged.append(merged_trigger)
            i = j if j > i + 1 else i + 1
        
        merged.sort(key=lambda x: x['date'])
        return merged

    def _get_significance(self, planet: str) -> str:
        map = {
            "Mars": "Acute energy surge, potential inflammatory spike or decision day",
            "Jupiter": "Expansion milestone, a 'Day of Grace' or spiritual insight",
            "Saturn": "Structural pressure, a karmic deadline or physical exhaustion",
            "Sun": "Vitality peak or authority encounter",
            "Moon": "Emotional shift or focus on domestic security",
            "Mercury": "Commercial transaction or critical communication window",
            "Venus": "Financial gain or social celebration",
            "Rahu": "Mental confusion or unconventional opportunity",
            "Ketu": "Spiritual detachment or sudden loss"
        }
        return map.get(planet, "Karmic activation point")

    def _get_intensity(self, planet: str) -> str:
        return "Critical" if planet in ["Mars", "Saturn", "Rahu", "Ketu"] else "High"
    
    def _get_house_signification(self, house: int) -> str:
        significations = {
            1: "Self & Vitality", 2: "Wealth & Family", 3: "Efforts & Siblings",
            4: "Happiness & Home", 5: "Intelligence & Children", 6: "Health & Obstacles",
            7: "Partnerships", 8: "Transformation", 9: "Fortune & Travel",
            10: "Career & Status", 11: "Gains", 12: "Expenses & Solitude"
        }
        return significations.get(house, "General Karma")

    def _get_sign_name(self, sign_id: int) -> str:
        names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return names[sign_id % 12]
    
    def _calculate_house_entry_date(self, current_age: int, active_house: int) -> Dict:
        """Calculate the date when the clock entered the current house (last birthday)"""
        house_entry_age = ((active_house - 1) % 12)
        while house_entry_age < current_age:
            house_entry_age += 12
        
        entry_date = self.birth_date + relativedelta(years=house_entry_age)
        
        return {
            "date": entry_date.strftime('%Y-%m-%d'),
            "window_start": entry_date.strftime('%Y-%m-%d'),
            "window_end": entry_date.strftime('%Y-%m-%d'),
            "planet": "House Entry",
            "natal_degree": 0.0,
            "sign": self._get_sign_name((int(self.lagna_degree / 30) + active_house - 1) % 12),
            "perspective": "Lagna",
            "significance": f"Year-clock enters {active_house}th house of {self._get_house_signification(active_house)}",
            "intensity": "Moderate",
            "confirmation": "House Activation",
            "perspectives": ["Lagna"]
        }
