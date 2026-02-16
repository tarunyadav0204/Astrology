
import swisseph as swe
from backend.app.kp.services.chart_service import KPChartService
from backend.app.kp.utils.kp_calculations import KPCalculations

def test_kp_calculation():
    # Birth details
    birth_date = "1980-04-02"
    birth_time = "14:55:00"
    latitude = 29.1492  # Hisar, Haryana
    longitude = 75.7217 # Hisar, Haryana
    timezone = "Asia/Kolkata"

    print(f"Testing KP for: {birth_date} {birth_time} at {latitude}, {longitude}")
    
    try:
        # Re-initialize swisseph to ensure clean state
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)
        
        result = KPChartService.calculate_kp_chart(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            timezone=timezone
        )
        
        moon_lords = result['planet_lords']['Moon']
        moon_pos_dms = result['planet_positions_dms']['Moon']
        
        print(f"\nMoon Position: {moon_pos_dms}")
        print(f"Moon Lords:")
        print(f"  Sign Lord: {moon_lords['sign_lord']}")
        print(f"  Star Lord: {moon_lords['star_lord']}")
        print(f"  Sub Lord:  {moon_lords['sub_lord']}")
        print(f"  Sub-Sub Lord: {moon_lords['sub_sub_lord']}")
        
        # Check other planets mentioned as wrong
        for p in ['Jupiter', 'Saturn', 'Rahu', 'Ketu']:
            lords = result['planet_lords'][p]
            pos = result['planet_positions_dms'][p]
            print(f"\n{p} Position: {pos}")
            print(f"  Lords: {lords['sign_lord']} - {lords['star_lord']} - {lords['sub_lord']} - {lords['sub_sub_lord']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_kp_calculation()
