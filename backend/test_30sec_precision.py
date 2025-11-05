#!/usr/bin/env python3
from calculators.annual_nakshatra_calculator import AnnualNakshatraCalculator
from datetime import datetime

calculator = AnnualNakshatraCalculator()
result = calculator.calculate_annual_nakshatra_periods('Revati', 2025)

for period in result['periods']:
    if period['start_datetime'].month == 1 and period['start_datetime'].day == 6:
        print(f"Drik: 07:06 PM - 05:50 PM")
        print(f"Ours: {period['start_time']} - {period['end_time']}")
        
        drik_start = datetime(2025, 1, 6, 19, 6)
        our_start = period['start_datetime'].replace(second=0, microsecond=0)
        diff = (our_start - drik_start).total_seconds() / 60
        print(f"Difference: {diff:+.1f} minutes")
        break