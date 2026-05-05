from datetime import datetime
import swisseph as swe
from shared.dasha_calculator import DashaCalculator

birth_data = {
    "date": "1980-04-02",
    "time": "14:55",
    "timezone": 5.5
}
calc = DashaCalculator()
# May 4, 2026 12:00
now = datetime(2026, 5, 4, 12, 0, 0)
dashas = calc.calculate_current_dashas(birth_data, now)
print(f"Dasha for May 4, 2026:")
print(f"MD: {dashas['mahadasha']['planet']}")
print(f"AD: {dashas['antardasha']['planet']}")
print(f"PD: {dashas['pratyantardasha']['planet']}")

# Check a few days around it
for day in range(1, 10):
    dt = datetime(2026, 5, day, 12, 0, 0)
    d = calc.calculate_current_dashas(birth_data, dt)
    print(f"May {day}: {d['pratyantardasha']['planet']}")
