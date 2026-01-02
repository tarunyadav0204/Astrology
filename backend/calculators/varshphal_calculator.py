from datetime import datetime, timedelta
import math
from typing import Dict, Any, List

class VarshphalCalculator:
    """
    Calculates the Annual Solar Return Chart (Varshphal) based on Tajik Shastra.
    Features:
    1. Exact Solar Return Time Calculation (iterative).
    2. Muntha Calculation (The focal point of the year).
    3. Mudda Dasha Calculation (120 years compressed to 1 year).
    """
    
    def __init__(self, chart_calculator):
        self.chart_calc = chart_calculator

    def calculate_varshphal(self, birth_data: Dict, target_year: int) -> Dict[str, Any]:
        """
        Main entry point. Generates the Annual Chart for a specific year.
        """
        # 1. Get Natal Sun Longitude (The Target)
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        natal_chart = self.chart_calc.calculate_chart(birth_obj)
        natal_sun_lon = natal_chart['planets']['Sun']['longitude']
        natal_asc_degree = natal_chart['ascendant']
        
        # 2. Find Exact Solar Return Time
        birth_date = datetime.strptime(birth_data['date'], '%Y-%m-%d')
        try:
            target_start = datetime(target_year, birth_date.month, birth_date.day, 12, 0, 0)
        except ValueError:
             target_start = datetime(target_year, 3, 1, 12, 0, 0)
             
        return_time = self._find_solar_return_time(natal_sun_lon, target_start, birth_data)
        
        # 3. Cast the Annual Chart (Varshphal)
        varshphal_input = {
            'name': f"Varshphal {target_year}",
            'date': return_time.strftime('%Y-%m-%d'),
            'time': return_time.strftime('%H:%M:%S'),
            'latitude': birth_data['latitude'],
            'longitude': birth_data['longitude'],
            'timezone': birth_data.get('timezone', 'UTC+0') 
        }
        
        vp_obj = SimpleNamespace(**varshphal_input)
        annual_chart = self.chart_calc.calculate_chart(vp_obj)
        
        # 4. Calculate Muntha
        age = target_year - birth_date.year
        natal_asc_sign = int(natal_asc_degree / 30) + 1
        
        muntha_sign_num = (natal_asc_sign + age) % 12
        if muntha_sign_num == 0: muntha_sign_num = 12
        
        annual_asc_sign = int(annual_chart['ascendant'] / 30) + 1
        muntha_house = (muntha_sign_num - annual_asc_sign + 1)
        if muntha_house <= 0: muntha_house += 12

        # 5. Calculate Mudda Dasha
        annual_moon_lon = annual_chart['planets']['Moon']['longitude']
        mudda_dasha = self._calculate_mudda_dasha(annual_moon_lon, return_time)
        
        # 6. Identify Year Lord
        sign_lords = {
            1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
            7: 'Venus', 8: 'Mars', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
        }
        year_lord = sign_lords[muntha_sign_num]

        return {
            'year': target_year,
            'age': age,
            'return_time': varshphal_input,
            'chart': annual_chart,
            'muntha': {
                'sign': muntha_sign_num,
                'house': muntha_house,
                'prediction': self._get_muntha_prediction(muntha_house)
            },
            'year_lord': year_lord,
            'mudda_dasha': mudda_dasha
        }

    def _find_solar_return_time(self, target_lon: float, start_date: datetime, birth_data: Dict) -> datetime:
        """
        Iteratively finds the exact second when Sun returns to target_lon.
        """
        current_check_time = start_date
        
        for _ in range(5):
            check_input = {
                'date': current_check_time.strftime('%Y-%m-%d'),
                'time': current_check_time.strftime('%H:%M:%S'),
                'latitude': birth_data['latitude'],
                'longitude': birth_data['longitude'],
                'timezone': birth_data.get('timezone', 'UTC+0')
            }
            from types import SimpleNamespace
            check_obj = SimpleNamespace(name="Check", **check_input)
            
            chart = self.chart_calc.calculate_chart(check_obj)
            current_sun_lon = chart['planets']['Sun']['longitude']
            
            diff = target_lon - current_sun_lon
            
            if diff > 180: diff -= 360
            if diff < -180: diff += 360
            
            if abs(diff) < 0.0003:
                return current_check_time
            
            days_adjustment = diff / 0.9856
            current_check_time += timedelta(days=days_adjustment)
            
        return current_check_time

    def _calculate_mudda_dasha(self, moon_lon: float, start_date: datetime) -> List[Dict]:
        """
        Calculates Mudda Dasha (Vimshottari compressed to 1 year).
        """
        dasha_order = [
            {'planet': 'Ketu', 'years': 7}, {'planet': 'Venus', 'years': 20},
            {'planet': 'Sun', 'years': 6}, {'planet': 'Moon', 'years': 10},
            {'planet': 'Mars', 'years': 7}, {'planet': 'Rahu', 'years': 18},
            {'planet': 'Jupiter', 'years': 16}, {'planet': 'Saturn', 'years': 19},
            {'planet': 'Mercury', 'years': 17}
        ]
        
        nakshatra_span = 360 / 27
        nakshatra_idx = int(moon_lon / nakshatra_span)
        lord_idx = nakshatra_idx % 9
        
        degree_in_nak = moon_lon % nakshatra_span
        fraction_passed = degree_in_nak / nakshatra_span
        fraction_remaining = 1.0 - fraction_passed
        
        timeline = []
        current_date = start_date
        
        first_lord = dasha_order[lord_idx]
        factor = 3.04375
        
        days_total = first_lord['years'] * factor
        days_remaining = days_total * fraction_remaining
        
        end_date = current_date + timedelta(days=days_remaining)
        timeline.append({
            'planet': first_lord['planet'],
            'start': current_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'type': 'Balance'
        })
        current_date = end_date
        
        for i in range(1, 9):
            next_idx = (lord_idx + i) % 9
            lord = dasha_order[next_idx]
            duration = lord['years'] * factor
            end_date = current_date + timedelta(days=duration)
            
            timeline.append({
                'planet': lord['planet'],
                'start': current_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            })
            current_date = end_date
            
        return timeline

    def _get_muntha_prediction(self, house: int) -> str:
        preds = {
            1: "New beginnings, health focus, and vitality.",
            2: "Financial accumulation and family matters.",
            3: "Effort, courage, siblings, and short travel.",
            4: "Domestic happiness, mother, and property.",
            5: "Creative intelligence, children, and speculation.",
            6: "Challenges with enemies or health. Hard work.",
            7: "Partnerships, marriage, and public dealings.",
            8: "Transformation, obstacles, or chronic issues.",
            9: "Luck, father, and spiritual journey.",
            10: "Career peak, success, and leadership.",
            11: "Gains, rewards, and social network.",
            12: "Expenditure, travel, or spiritual isolation."
        }
        return preds.get(house, "General yearly focus.")
