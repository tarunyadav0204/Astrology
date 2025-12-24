# calculators/financial/financial_context_builder.py
from typing import Dict, Any, List
from .market_scanner import MarketScanner
from .sector_mapper import SECTOR_RULES
import sqlite3
from datetime import datetime

class FinancialContextBuilder:
    """Orchestrates financial market analysis"""
    
    def __init__(self):
        self.scanner = MarketScanner()
    
    def build_sector_forecast(self, sector: str, start_year: int = 2025, years: int = 5) -> Dict[str, Any]:
        """
        Build forecast for a specific sector
        Returns: Sector timeline with trends
        """
        if sector not in SECTOR_RULES:
            raise ValueError(f"Unknown sector: {sector}. Available: {list(SECTOR_RULES.keys())}")
        
        print(f"🔮 Building forecast for {sector}...")
        
        # Generate full timeline
        timeline = self.scanner.generate_forecast(start_year, years)
        
        return {
            "sector": sector,
            "ruler": SECTOR_RULES[sector]['ruler'],
            "timeline": timeline[sector],
            "total_periods": len(timeline[sector]),
            "bullish_periods": len([p for p in timeline[sector] if p['trend'] == 'BULLISH']),
            "bearish_periods": len([p for p in timeline[sector] if p['trend'] == 'BEARISH'])
        }
    
    def build_all_sectors_forecast(self, start_year: int = 2025, years: int = 5) -> Dict[str, Any]:
        """
        Build forecast for all sectors
        Returns: Complete market outlook
        """
        print(f"🌍 Building complete market forecast...")
        
        timeline = self.scanner.generate_forecast(start_year, years)
        
        summary = {}
        for sector in SECTOR_RULES.keys():
            periods = timeline[sector]
            summary[sector] = {
                "ruler": SECTOR_RULES[sector]['ruler'],
                "total_periods": len(periods),
                "bullish_periods": len([p for p in periods if p['trend'] == 'BULLISH']),
                "bearish_periods": len([p for p in periods if p['trend'] == 'BEARISH']),
                "timeline": periods
            }
        
        return {
            "start_year": start_year,
            "years": years,
            "sectors": summary,
            "total_sectors": len(SECTOR_RULES)
        }
    
    def get_current_trends(self, reference_date: str = None) -> Dict[str, str]:
        """
        Get current trend for all sectors at a specific date
        reference_date: ISO format string or None for today
        Returns: dict with sector: trend
        """
        from datetime import datetime
        
        if reference_date is None:
            reference_date = datetime.now().isoformat()
        
        ref_dt = datetime.fromisoformat(reference_date.split('T')[0])
        
        timeline = self.scanner.generate_forecast(ref_dt.year, 1)
        
        current_trends = {}
        for sector, periods in timeline.items():
            # Find period containing reference date
            for period in periods:
                start = datetime.fromisoformat(period['start'].split('T')[0])
                end = datetime.fromisoformat(period['end'].split('T')[0])
                
                if start <= ref_dt <= end:
                    current_trends[sector] = {
                        "trend": period['trend'],
                        "intensity": period['intensity'],
                        "reason": period['reason'],
                        "valid_until": period['end']
                    }
                    break
            
            if sector not in current_trends:
                current_trends[sector] = {
                    "trend": "NEUTRAL",
                    "intensity": "Low",
                    "reason": "No significant transit",
                    "valid_until": None
                }
        
        return current_trends
    
    def get_hot_sectors(self, start_year: int = 2025, years: int = 5, min_intensity: str = "High") -> List[Dict]:
        """
        Get sectors with strong bullish periods
        Returns: List of hot opportunities sorted by strength
        """
        timeline = self.scanner.generate_forecast(start_year, years)
        
        hot_periods = []
        for sector, periods in timeline.items():
            for period in periods:
                if period['trend'] == 'BULLISH' and period['intensity'] == min_intensity:
                    hot_periods.append({
                        "sector": sector,
                        "start": period['start'],
                        "end": period['end'],
                        "intensity": period['intensity'],
                        "reason": period['reason']
                    })
        
        return sorted(hot_periods, key=lambda x: x['start'])
    
    def save_to_database(self, forecast_data: Dict[str, Any]):
        """Save forecast to SQLite database"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        # Create tables if not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_forecast_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sector TEXT NOT NULL,
                ruler TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                trend TEXT NOT NULL,
                intensity TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_forecast_metadata (
                id INTEGER PRIMARY KEY,
                start_year INTEGER,
                end_year INTEGER,
                generated_at TIMESTAMP,
                total_periods INTEGER
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sector_date ON market_forecast_periods(sector, start_date, end_date)')
        
        # Clear old data
        cursor.execute("DELETE FROM market_forecast_periods")
        cursor.execute("DELETE FROM market_forecast_metadata")
        
        # Save metadata
        total_periods = sum(len(s['timeline']) for s in forecast_data['sectors'].values())
        end_year = forecast_data['start_year'] + forecast_data['years'] - 1
        cursor.execute("""
            INSERT INTO market_forecast_metadata (id, start_year, end_year, generated_at, total_periods)
            VALUES (1, ?, ?, ?, ?)
        """, (
            forecast_data['start_year'],
            end_year,
            datetime.now().isoformat(),
            total_periods
        ))
        
        # Save all periods
        for sector, info in forecast_data['sectors'].items():
            for period in info['timeline']:
                cursor.execute("""
                    INSERT INTO market_forecast_periods 
                    (sector, ruler, start_date, end_date, trend, intensity, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sector,
                    info['ruler'],
                    period['start'][:10],
                    period['end'][:10],
                    period['trend'],
                    period['intensity'],
                    period['reason']
                ))
        
        conn.commit()
        conn.close()
        print(f"✅ Saved {total_periods} periods to database")
