#!/usr/bin/env python3
"""Initialize financial forecast database with 5-year data"""

from calculators.financial.financial_context_builder import FinancialContextBuilder

def main():
    print("🚀 Initializing Financial Market Forecast Database...")
    print("=" * 60)
    
    builder = FinancialContextBuilder()
    
    # Generate 5-year forecast starting from 2025
    print("\n📊 Generating 5-year forecast (2025-2030)...")
    data = builder.build_all_sectors_forecast(start_year=2025, years=5)
    
    print(f"\n✅ Generated forecast for {data['total_sectors']} sectors")
    print(f"📅 Period: {data['start_year']}-{data['start_year'] + data['years']}")
    
    # Save to database
    print("\n💾 Saving to database...")
    builder.save_to_database(data)
    
    print("\n✨ Database initialized successfully!")
    print("=" * 60)
    print("\n📱 Mobile app can now access:")
    print("   - GET /api/financial/sectors")
    print("   - GET /api/financial/forecast/all")
    print("   - GET /api/financial/hot-opportunities")
    print("   - GET /api/financial/current-trends")

if __name__ == "__main__":
    main()
