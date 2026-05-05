from datetime import datetime
from shared.dasha_calculator import DashaCalculator

birth_data = {
    "date": "1980-04-02T14:55:00.000Z",
    "time": "14:55",
    "lat": 29.1492,
    "lon": 75.7217,
    "tzone": 5.5
}
calc = DashaCalculator()
now = datetime(2026, 5, 4, 12, 0, 0)
dashas = calc.calculate_current_dashas(birth_data, now)
print(f"Dasha as of {now}:")
print(f"MD: {dashas['mahadasha']['planet']} ({dashas['mahadasha']['start_date']} to {dashas['mahadasha']['end_date']})")
print(f"AD: {dashas['antardasha']['planet']} ({dashas['antardasha']['start_date']} to {dashas['antardasha']['end_date']})")
print(f"PD: {dashas['pratyantardasha']['planet']} ({dashas['pratyantardasha']['start_date']} to {dashas['pratyantardasha']['end_date']})")

print("\nScanning for PD changes in 2026:")
periods = calc.get_dasha_periods_for_range(birth_data, datetime(2026, 1, 1), datetime(2026, 12, 31))
for p in periods:
    print(f"{p['start_date']} to {p['end_date']}: {p['mahadasha']}-{p['antardasha']}-{p['pratyantardasha']}")
