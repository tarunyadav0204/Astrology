from datetime import datetime, timedelta
import math

class YoginiDashaCalculator:
    """
    Professional Grade Yogini Dasha Calculator.
    Based on the classical method: (Birth Nakshatra + 3) % 8.
    Cycle Length: 36 Years.
    """
    
    def __init__(self, use_360_days=False):
        # Option to use Savana Year (360 days) common in Yogini
        self.year_length = 360.0 if use_360_days else 365.25
        # The Fixed Cycle of 8 Yoginis
        self.YOGINIS = [
            {'id': 1, 'name': 'Mangala',  'lord': 'Moon',    'years': 1, 'vibe': 'Success, Auspiciousness, Prosperity'},
            {'id': 2, 'name': 'Pingala',  'lord': 'Sun',     'years': 2, 'vibe': 'Heart trouble, Fame, Aggression'},
            {'id': 3, 'name': 'Dhanya',   'lord': 'Jupiter', 'years': 3, 'vibe': 'Wealth, Prosperity, Wisdom'},
            {'id': 4, 'name': 'Bhramari', 'lord': 'Mars',    'years': 4, 'vibe': 'Travel, Confusion, Displacement'},
            {'id': 5, 'name': 'Bhadrika', 'lord': 'Mercury', 'years': 5, 'vibe': 'Career Growth, Friends, Social Status'},
            {'id': 6, 'name': 'Ulka',     'lord': 'Saturn',  'years': 6, 'vibe': 'Grief, Fear, Sudden Loss'},
            {'id': 7, 'name': 'Siddha',   'lord': 'Venus',   'years': 7, 'vibe': 'Success, Luxury, Romance, Knowledge'},
            {'id': 8, 'name': 'Sankata',  'lord': 'Rahu',    'years': 8, 'vibe': 'Crisis, Transformation, Danger'}
        ]

    def calculate_current_yogini(self, birth_data: dict, moon_longitude: float, target_date: datetime = None) -> dict:
        """Calculates the Yogini Dasha running on a specific date."""
        if target_date is None:
            target_date = datetime.now()

        # Parse birth date safely handling timezones
        birth_date_obj = self._parse_birth_date(birth_data)

        # Ensure target_date and birth_date are compatible (Timezone safe)
        if target_date.tzinfo is not None and birth_date_obj.tzinfo is None:
            birth_date_obj = birth_date_obj.replace(tzinfo=target_date.tzinfo)
        elif target_date.tzinfo is None and birth_date_obj.tzinfo is not None:
            target_date = target_date.replace(tzinfo=birth_date_obj.tzinfo)

        # 1. Calculate Birth Yogini & Balance
        start_dasha = self._calculate_birth_dasha_balance(moon_longitude, birth_date_obj)
        
        # 2. Iterate forward from birth to target date
        current_date = start_dasha['end_date']
        
        # If target is within the first dasha (balance period)
        if target_date <= current_date:
            return self._calculate_sub_periods(start_dasha, target_date, is_balance=True)

        # Loop through 36-year cycles until we reach target
        current_index = self._get_index_by_name(start_dasha['name'])
        
        while current_date < target_date:
            current_index = (current_index + 1) % 8
            yogini = self.YOGINIS[current_index]
            
            # Use configured year length
            duration_days = yogini['years'] * self.year_length
            start_date = current_date
            end_date = start_date + timedelta(days=duration_days)
            
            # Check if this is the one
            if start_date <= target_date < end_date:
                md_obj = {
                    'mahadasha': yogini,
                    'start_date': start_date,
                    'end_date': end_date
                }
                return self._calculate_sub_periods(md_obj, target_date)
            
            current_date = end_date

        return {}

    def _calculate_birth_dasha_balance(self, moon_lon: float, birth_date: datetime) -> dict:
        """Determines the starting Yogini and the remaining time (Balance) at birth."""
        moon_lon = moon_lon % 360
        nakshatra_span = 360 / 27 
        nakshatra_idx = int(moon_lon / nakshatra_span) 
        nakshatra_num = nakshatra_idx + 1 
        
        remainder = (nakshatra_num + 3) % 8
        if remainder == 0:
            remainder = 8
            
        yogini = next(y for y in self.YOGINIS if y['id'] == remainder)
        
        deg_in_nak = moon_lon % nakshatra_span
        fraction_passed = deg_in_nak / nakshatra_span
        fraction_remaining = 1.0 - fraction_passed
        
        years_remaining = yogini['years'] * fraction_remaining
        days_remaining = years_remaining * self.year_length
        
        end_date = birth_date + timedelta(days=days_remaining)
        
        return {
            'name': yogini['name'],
            'lord': yogini['lord'],
            'years_total': yogini['years'],
            'years_balance': years_remaining,
            'start_date': birth_date,
            'end_date': end_date,
            'vibe': yogini['vibe']
        }

    def _calculate_sub_periods(self, md_data: dict, target_date: datetime, is_balance=False) -> dict:
        """Calculates the Antardasha (Sub Period) within the Mahadasha."""
        md_name = md_data['name'] if is_balance else md_data['mahadasha']['name']
        md_years = md_data.get('years_total', 0) if is_balance else md_data['mahadasha']['years']
        
        current_date = md_data['start_date']
        start_index = self._get_index_by_name(md_name if is_balance else md_data['mahadasha']['name'])
        
        if is_balance:
            full_md_days = md_years * self.year_length
            theoretical_start = md_data['end_date'] - timedelta(days=full_md_days)
            current_date = theoretical_start
        
        sub_periods = []
        
        for i in range(8):
            idx = (start_index + i) % 8
            ad_yogini = self.YOGINIS[idx]
            
            ad_years = (md_years * ad_yogini['years']) / 36.0
            ad_days = ad_years * self.year_length
            
            start = current_date
            end = start + timedelta(days=ad_days)
            
            ad_obj = {
                'planet': ad_yogini['lord'],
                'dasha_name': ad_yogini['name'],
                'start_date': start,
                'end_date': end,
                'vibe': ad_yogini['vibe']
            }
            
            sub_periods.append(ad_obj)
            current_date = end

        active_ad = None
        for ad in sub_periods:
            if ad['start_date'] <= target_date < ad['end_date']:
                active_ad = ad
                break
        
        if not active_ad and sub_periods:
            active_ad = sub_periods[-1]
                
        return {
            "mahadasha": {
                "name": md_name,
                "lord": md_data['lord'] if is_balance else md_data['mahadasha']['lord'],
                "vibe": md_data['vibe'] if is_balance else md_data['mahadasha']['vibe'],
                "start": md_data['start_date'].strftime("%Y-%m-%d"),
                "end": md_data['end_date'].strftime("%Y-%m-%d")
            },
            "antardasha": {
                "name": active_ad['dasha_name'],
                "lord": active_ad['planet'],
                "start": active_ad['start_date'].strftime("%Y-%m-%d"),
                "end": active_ad['end_date'].strftime("%Y-%m-%d"),
                "vibe": active_ad['vibe']
            },
            "significance": self._get_combined_prediction(
                md_name if is_balance else md_data['mahadasha']['name'], 
                active_ad['dasha_name']
            )
        }

    def _get_index_by_name(self, name):
        for i, y in enumerate(self.YOGINIS):
            if y['name'] == name: return i
        return 0

    def _parse_birth_date(self, birth_data: dict) -> datetime:
        """Robust date parsing"""
        try:
            date_str = f"{birth_data['date']} {birth_data.get('time', '00:00')}"
            if len(birth_data.get('time', '').split(':')) == 3:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        except:
            return datetime.now()

    def _get_combined_prediction(self, md_name, ad_name):
        """Professional predictive tags"""
        if md_name == 'Sankata' or ad_name == 'Sankata':
            return "Challenging period requiring caution and remedies."
        
        if md_name == 'Siddha' and ad_name == 'Siddha':
            return "Excellent period for growth, luxury, and success."
            
        if md_name == 'Siddha':
            return "Period of general success and enjoyment."
            
        if md_name == 'Bhramari' or ad_name == 'Bhramari':
            return "Period of travel, displacement, or mental confusion."
            
        if md_name == 'Ulka' or ad_name == 'Ulka':
            return "Period of hard work, potential strain, or sudden changes."
            
        return "Mixed results based on house placement."

    def get_sub_periods_list(self, md_name: str, start_date: datetime, end_date: datetime) -> list:
        """Returns list of all 8 sub-periods for a specific Mahadasha timeframe."""
        md_yogini = next(y for y in self.YOGINIS if y['name'] == md_name)
        start_index = self._get_index_by_name(md_name)
        
        current_date = start_date
        subs = []
        
        for i in range(8):
            idx = (start_index + i) % 8
            ad_yogini = self.YOGINIS[idx]
            
            ad_years = (md_yogini['years'] * ad_yogini['years']) / 36.0
            ad_days = ad_years * self.year_length 
            
            end = current_date + timedelta(days=ad_days)
            
            subs.append({
                'name': ad_yogini['name'],
                'lord': ad_yogini['lord'],
                'start': current_date.strftime("%Y-%m-%d"),
                'end': end.strftime("%Y-%m-%d"),
                'vibe': ad_yogini['vibe']
            })
            
            current_date = end
            
        return subs

    def get_full_timeline(self, birth_data, moon_lon, years=120):
        """Generates full lifetime Dasha timeline (default 120 years)."""
        timeline = []
        birth_date_obj = self._parse_birth_date(birth_data)
        
        # Get birth dasha balance
        start_dasha = self._calculate_birth_dasha_balance(moon_lon, birth_date_obj)
        timeline.append({
            'name': start_dasha['name'],
            'lord': start_dasha['lord'],
            'start': start_dasha['start_date'].strftime("%Y-%m-%d"),
            'end': start_dasha['end_date'].strftime("%Y-%m-%d"),
            'vibe': start_dasha['vibe'],
            'is_balance': True
        })
        
        # Continue from end of balance period
        current_date = start_dasha['end_date']
        current_index = self._get_index_by_name(start_dasha['name'])
        end_target = birth_date_obj + timedelta(days=years * self.year_length)
        
        while current_date < end_target:
            current_index = (current_index + 1) % 8
            yogini = self.YOGINIS[current_index]
            
            duration_days = yogini['years'] * self.year_length
            start_date = current_date
            end_date = start_date + timedelta(days=duration_days)
            
            timeline.append({
                'name': yogini['name'],
                'lord': yogini['lord'],
                'start': start_date.strftime("%Y-%m-%d"),
                'end': end_date.strftime("%Y-%m-%d"),
                'vibe': yogini['vibe'],
                'is_balance': False
            })
            
            current_date = end_date
        
        return timeline