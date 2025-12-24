#!/usr/bin/env python3
# generate_market_data.py
"""
Run this script to generate 5-year market forecast data.
Usage: python generate_market_data.py
Output: market_forecast_2025_2030.json
"""

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.financial.financial_context_builder import FinancialContextBuilder

if __name__ == "__main__":
    print("🚀 Starting Market Forecast Generation...")
    print("=" * 60)
    
    builder = FinancialContextBuilder()
    
    # Generate 5-year forecast
    data = builder.build_all_sectors_forecast(start_year=2025, years=5)
    
    # Save to JSON
    output_file = "market_forecast_2025_2030.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Market Data Generated Successfully!")
    print(f"📁 Output: {output_file}")
    print(f"📊 Total Sectors: {data['total_sectors']}")
    print(f"📅 Period: {data['start_year']} - {data['start_year'] + data['years']}")
    
    # Print summary
    print("\n📈 SECTOR SUMMARY:")
    for sector, info in data['sectors'].items():
        print(f"  • {sector}: {info['bullish_periods']} bullish, {info['bearish_periods']} bearish periods")
    
    print("\n🔥 HOT OPPORTUNITIES (High Intensity Bullish):")
    hot = builder.get_hot_sectors(2025, 5, "High")
    for i, opp in enumerate(hot[:5], 1):
        print(f"  {i}. {opp['sector']}: {opp['start'][:10]} to {opp['end'][:10]}")
        print(f"     Reason: {opp['reason']}")
