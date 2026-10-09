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
        # Parse birth date safely handling timezones
        birth_date_obj = self._parse_birth_date(birth_data)

        from .dasha_time import normalize_focus
        target_date = normalize_focus(target_date, birth_date_obj)
        if target_date < birth_date_obj:
            raise ValueError('Yogini target date precedes birth')

        # 1. Calculate Birth Yogini & Balance
        start_dasha = self._calculate_birth_dasha_balance(moon_longitude, birth_date_obj)
        
        # 2. Iterate forward from birth to target date
        current_date = start_dasha['end_date']
        
        # If target is within the first dasha (balance period)
        if target_date < current_date:
            return self._calculate_sub_periods(start_dasha, target_date, is_balance=True)

        # Loop through 36-year cycles until we reach target
        current_index = self._get_index_by_name(start_dasha['name'])
        
        while current_date <= target_date:
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

    def get_periods_in_range(self, birth_data, moon_longitude, start, end):
        """Bounded MD/AD facts with exact instants; birth balance clips the full AD schedule."""
        from .dasha_time import normalize_focus
        birth = self._parse_birth_date(birth_data)
        start, end = normalize_focus(start, birth), normalize_focus(end, birth)
        if end <= start:
            raise ValueError('Yogini end must follow start')
        balance = self._calculate_birth_dasha_balance(moon_longitude, birth)
        idx = self._get_index_by_name(balance['name'])
        cursor, finish = birth, balance['end_date']
        rows = []
        while cursor < end:
            yogini = self.YOGINIS[idx]
            if finish > start:
                full_start = finish - timedelta(days=yogini['years'] * self.year_length)
                ad_cursor = full_start
                subs = []
                for i in range(8):
                    ad = self.YOGINIS[(idx + i) % 8]
                    ad_end = full_start + (finish - full_start) * sum(self.YOGINIS[(idx+j)%8]['years'] for j in range(i+1)) / 36
                    if ad_end > max(start, birth) and ad_cursor < end:
                        subs.append({'name': ad['name'], 'lord': ad['lord'],
                                     'start_iso': max(ad_cursor, birth).isoformat(), 'end_iso': ad_end.isoformat()})
                    ad_cursor = ad_end
                rows.append({'name': yogini['name'], 'lord': yogini['lord'],
                             'start_iso': cursor.isoformat(), 'end_iso': finish.isoformat(),
                             'antardashas': subs})
            cursor = finish
            idx = (idx + 1) % 8
            finish = cursor + timedelta(days=self.YOGINIS[idx]['years'] * self.year_length)
        return {'method': 'nakshatra_yogini_36_year_cycle', 'year_days': self.year_length,
                'boundary_type': 'start_inclusive_end_exclusive', 'periods': rows}

    def _calculate_birth_dasha_balance(self, moon_lon: float, birth_date: datetime) -> dict:
        """Determines the starting Yogini and the remaining time (Balance) at birth."""
        if not math.isfinite(moon_lon):
            raise ValueError('Moon longitude must be finite')
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
        
        full_start = current_date
        full_duration = timedelta(days=md_years * self.year_length)
        cumulative_years = 0
        sub_periods = []
        
        for i in range(8):
            idx = (start_index + i) % 8
            ad_yogini = self.YOGINIS[idx]
            
            ad_years = (md_years * ad_yogini['years']) / 36.0
            ad_days = ad_years * self.year_length
            
            start = current_date
            cumulative_years += ad_yogini['years']
            end = full_start + full_duration * cumulative_years / 36
            
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
        
        if not active_ad:
            raise ValueError('No Yogini antardasha covers the requested timestamp')
                
        return {
            "mahadasha": {
                "name": md_name,
                "lord": md_data['lord'] if is_balance else md_data['mahadasha']['lord'],
                "vibe": md_data['vibe'] if is_balance else md_data['mahadasha']['vibe'],
                "start": md_data['start_date'].strftime("%Y-%m-%d"),
                "start_iso": md_data['start_date'].isoformat(),
                "end_iso": md_data['end_date'].isoformat(),
                "end": md_data['end_date'].strftime("%Y-%m-%d")
            },
            "antardasha": {
                "name": active_ad['dasha_name'],
                "lord": active_ad['planet'],
                "start": active_ad['start_date'].strftime("%Y-%m-%d"),
                "start_iso": active_ad['start_date'].isoformat(),
                "end_iso": active_ad['end_date'].isoformat(),
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
        raise ValueError(f'Unknown Yogini: {name}')

    def _parse_birth_date(self, birth_data: dict) -> datetime:
        from .dasha_time import parse_birth_datetime
        return parse_birth_datetime(birth_data)

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
        
        # Reconstruct the full MD origin when start_date is birth balance.
        current_date = end_date - timedelta(days=md_yogini['years'] * self.year_length)
        subs = []
        
        for i in range(8):
            idx = (start_index + i) % 8
            ad_yogini = self.YOGINIS[idx]
            
            ad_years = (md_yogini['years'] * ad_yogini['years']) / 36.0
            ad_days = ad_years * self.year_length 
            
            end = current_date + timedelta(days=ad_days)
            
            if end <= start_date:
                current_date = end
                continue
            subs.append({
                'name': ad_yogini['name'],
                'lord': ad_yogini['lord'],
                'start': max(current_date, start_date).strftime("%Y-%m-%d"),
                'end': min(end, end_date).strftime("%Y-%m-%d"),
                'start_iso': max(current_date, start_date).isoformat(),
                'end_iso': min(end, end_date).isoformat(),
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
            'start_iso': start_dasha['start_date'].isoformat(),
            'end_iso': start_dasha['end_date'].isoformat(),
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
                'start_iso': start_date.isoformat(),
                'end_iso': end_date.isoformat(),
                'vibe': yogini['vibe'],
                'is_balance': False
            })
            
            current_date = end_date
        
        return timeline