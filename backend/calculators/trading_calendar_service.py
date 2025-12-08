from datetime import datetime, timedelta
from typing import List, Dict
from types import SimpleNamespace
from .chart_calculator import ChartCalculator
from .trading_luck_calculator import TradingLuckCalculator
from .ashtakavarga import AshtakavargaCalculator
from panchang.panchang_calculator import PanchangCalculator

class TradingCalendarService:
    
    def __init__(self, natal_chart, birth_data):
        self.natal_chart = natal_chart
        self.birth_data = birth_data
        
        # Pre-calc SAV once
        self.av_calc = AshtakavargaCalculator(birth_data, natal_chart)
        self.raw_sav = self.av_calc.calculate_sarvashtakavarga() 
        self.natal_chart['ashtakavarga'] = {'d1_rashi': self.raw_sav}

    def get_monthly_forecast(self, year: int, month: int) -> List[Dict]:
        """Generates Green/Red calendar for the whole month"""
        import calendar
        _, num_days = calendar.monthrange(year, month)
        
        results = []
        chart_calc = ChartCalculator({})
        
        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day)
            
            # Skip weekends (Saturday=5, Sunday=6) - no market trading
            if date_obj.weekday() in [5, 6]:
                results.append({
                    "date": date_obj.strftime('%Y-%m-%d'),
                    "day": date_obj.strftime('%A'),
                    "score": None,
                    "signal": "CLOSED",
                    "action": "Market Closed",
                    "reason": "Weekend - No Trading",
                    "strategy": "Rest"
                })
                continue
            
            # CRITICAL FIX: Ensure consistent 9:15 AM calculation with proper timezone
            transit_input = SimpleNamespace(
                date=date_obj.strftime('%Y-%m-%d'),
                time="09:15",  # Explicitly set Market Open Time
                latitude=self.birth_data.get('latitude', 28.61),
                longitude=self.birth_data.get('longitude', 77.20),
                timezone=self.birth_data.get('timezone', 'UTC+5:30')  # Ensure Timezone matches
            )
            transit_chart = chart_calc.calculate_chart(transit_input)
            
            # Run Trading Calc
            t_calc = TradingLuckCalculator(
                self.natal_chart, transit_chart, self.birth_data, 
                date_obj, self.natal_chart['ashtakavarga']
            )
            forecast = t_calc.calculate_trading_forecast()
            
            results.append({
                "date": date_obj.strftime('%Y-%m-%d'),
                "day": date_obj.strftime('%A'),
                "score": forecast['luck_score'],
                "signal": forecast['signal'],
                "action": forecast['action'],
                "reason": forecast['headline'],
                "strategy": forecast['market_mood']['strategy']
            })
            
        return results

    def get_intraday_timings(self, target_date: datetime) -> Dict:
        """Calculates Trading Windows using Choghadiya and Hora"""
        panchang_calc = PanchangCalculator()
        
        # Get Choghadiya
        lat = self.birth_data.get('latitude', 28.61)
        lon = self.birth_data.get('longitude', 77.20)
        date_str = target_date.strftime('%Y-%m-%d')
        
        choghadiya = panchang_calc.calculate_choghadiya(date_str, lat, lon)
        
        # Filter for Market Hours (9:15 AM to 3:30 PM)
        market_slots = []
        
        def parse_iso(iso_str):
            return datetime.fromisoformat(iso_str)

        market_open = datetime.strptime(f"{date_str} 09:15", "%Y-%m-%d %H:%M")
        market_close = datetime.strptime(f"{date_str} 15:30", "%Y-%m-%d %H:%M")
        
        # Analyze Day Choghadiya for Market Hours
        for slot in choghadiya['day_choghadiya']:
            start = parse_iso(slot['start_time'])
            end = parse_iso(slot['end_time'])
            
            # Calculate intersection with market hours
            effective_start = max(start, market_open)
            effective_end = min(end, market_close)
            
            if effective_start < effective_end:
                # Determine quality for Trading specifically
                trade_quality = "Neutral"
                color_code = "blue"
                
                # Labha (Gain), Shubha (Good), Amrita (Best), Chara (Neutral/Good for movement)
                if slot['name'] in ['Labha', 'Shubha', 'Amrita']:
                    trade_quality = "Good"
                    color_code = "green"
                elif slot['name'] == 'Chara':
                    trade_quality = "Neutral (Good for momentum)"
                    color_code = "yellow"
                elif slot['name'] in ['Udvega', 'Roga', 'Kala']:
                    trade_quality = "Bad"
                    color_code = "red"
                
                market_slots.append({
                    "start": effective_start.strftime('%H:%M'),
                    "end": effective_end.strftime('%H:%M'),
                    "name": slot['name'],
                    "quality": trade_quality,
                    "color": color_code,
                    "type": "Choghadiya"
                })
                
        # Sort by start time
        market_slots.sort(key=lambda x: x['start'])
                
        return {
            "date": date_str,
            "timings": market_slots,
            "note": "Trade primarily during Labha/Shubha/Amrita slots. Avoid Udvega/Roga/Kala for new entries."
        }