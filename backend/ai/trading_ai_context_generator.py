from datetime import datetime
from types import SimpleNamespace
from typing import Dict, Any
from .base_ai_context_generator import BaseAIContextGenerator
from calculators.trading_luck_calculator import TradingLuckCalculator
from calculators.chart_calculator import ChartCalculator
from calculators.ashtakavarga import AshtakavargaCalculator

class TradingAIContextGenerator(BaseAIContextGenerator):
    
    def build_trading_context(self, birth_data: Dict, target_date: datetime = None) -> Dict[str, Any]:
        if not target_date:
            target_date = datetime.now()
            
        # 1. Build Base Context (Natal)
        base_context = self.build_base_context(birth_data)
        birth_hash = self._create_birth_hash(birth_data)
        natal_chart = self.static_cache[birth_hash]['d1_chart']
        
        # 2. Inject SAV (Calculate if missing)
        av_calc = AshtakavargaCalculator(birth_data, natal_chart)
        sav_data = av_calc.calculate_sarvashtakavarga()
        natal_chart['ashtakavarga'] = {'d1_rashi': sav_data}
        
        # 3. Transit Chart (9:15 AM)
        transit_input = SimpleNamespace(
            date=target_date.strftime('%Y-%m-%d'),
            time="09:15",
            latitude=birth_data.get('latitude', 28.61),
            longitude=birth_data.get('longitude', 77.20),
            timezone=birth_data.get('timezone', 'UTC+5:30')
        )
        calc = ChartCalculator({})
        transit_chart = calc.calculate_chart(transit_input)
        
        # 4. Trading Forecast
        t_calc = TradingLuckCalculator(
            natal_chart, transit_chart, birth_data, target_date, natal_chart['ashtakavarga']
        )
        forecast = t_calc.calculate_trading_forecast()
        
        return {
            "trading_forecast": forecast,
            "user_name": birth_data.get('name'),
            "target_date": target_date.strftime('%Y-%m-%d')
        }