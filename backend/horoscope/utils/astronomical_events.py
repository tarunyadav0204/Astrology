from datetime import datetime, timedelta
import swisseph as swe
from typing import Dict, List, Optional

class AstronomicalEvents:
    """Calculate real astronomical events affecting horoscopes"""
    
    @staticmethod
    def get_mercury_retrograde_periods(year: int) -> List[Dict]:
        """Get actual Mercury retrograde periods for the year"""
        periods = []
        
        # Check each month for Mercury retrograde
        for month in range(1, 13):
            date = datetime(year, month, 15)
            jd = swe.julday(date.year, date.month, date.day)
            
            # Get Mercury position and speed
            pos, speed = swe.calc_ut(jd, swe.MERCURY, swe.FLG_SPEED)
            
            if speed[0] < 0:  # Retrograde
                # Find start and end dates
                start_date = AstronomicalEvents._find_retrograde_start(year, month)
                end_date = AstronomicalEvents._find_retrograde_end(year, month)
                
                if start_date and end_date:
                    periods.append({
                        'start': start_date,
                        'end': end_date,
                        'sign': AstronomicalEvents._get_zodiac_sign(pos[0])
                    })
        
        return periods
    
    @staticmethod
    def get_current_lunar_phase(date: datetime) -> Dict:
        """Get exact lunar phase information"""
        jd = swe.julday(date.year, date.month, date.day, date.hour)
        
        # Get Sun and Moon positions
        sun_pos = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
        
        # Calculate phase angle
        phase_angle = (moon_pos - sun_pos) % 360
        
        # Determine phase
        if phase_angle < 1 or phase_angle > 359:
            phase = "New Moon"
            illumination = 0
        elif 1 <= phase_angle < 89:
            phase = "Waxing Crescent"
            illumination = phase_angle / 180 * 100
        elif 89 <= phase_angle < 91:
            phase = "First Quarter"
            illumination = 50
        elif 91 <= phase_angle < 179:
            phase = "Waxing Gibbous"
            illumination = phase_angle / 180 * 100
        elif 179 <= phase_angle < 181:
            phase = "Full Moon"
            illumination = 100
        elif 181 <= phase_angle < 269:
            phase = "Waning Gibbous"
            illumination = (360 - phase_angle) / 180 * 100
        elif 269 <= phase_angle < 271:
            phase = "Last Quarter"
            illumination = 50
        else:
            phase = "Waning Crescent"
            illumination = (360 - phase_angle) / 180 * 100
        
        return {
            'phase': phase,
            'illumination': round(illumination, 1),
            'angle': round(phase_angle, 2),
            'moon_sign': AstronomicalEvents._get_zodiac_sign(moon_pos)
        }
    
    @staticmethod
    def get_void_of_course_moon(date: datetime) -> Optional[Dict]:
        """Check if Moon is void of course"""
        jd = swe.julday(date.year, date.month, date.day, date.hour)
        
        # Get Moon position and speed
        moon_pos, moon_speed = swe.calc_ut(jd, swe.MOON, swe.FLG_SPEED)
        moon_longitude = moon_pos[0]
        
        # Check for upcoming aspects within next 24 hours
        planets = [swe.SUN, swe.MERCURY, swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN]
        
        next_aspect_time = None
        next_sign_change = AstronomicalEvents._calculate_next_sign_change(moon_longitude, moon_speed[0])
        
        for planet_id in planets:
            planet_pos = swe.calc_ut(jd, planet_id)[0][0]
            aspect_time = AstronomicalEvents._find_next_aspect(moon_longitude, moon_speed[0], planet_pos)
            
            if aspect_time and (not next_aspect_time or aspect_time < next_aspect_time):
                next_aspect_time = aspect_time
        
        # Moon is void if next sign change comes before next aspect
        if next_sign_change and (not next_aspect_time or next_sign_change < next_aspect_time):
            return {
                'is_void': True,
                'until': date + timedelta(hours=next_sign_change),
                'current_sign': AstronomicalEvents._get_zodiac_sign(moon_longitude)
            }
        
        return {'is_void': False}
    
    @staticmethod
    def get_planetary_hours(date: datetime, latitude: float, longitude: float) -> Dict:
        """Calculate traditional planetary hours"""
        # Get sunrise and sunset times
        jd = swe.julday(date.year, date.month, date.day)
        
        # Calculate sunrise/sunset (simplified)
        sunrise_jd = jd + 0.25  # 6 AM approximation
        sunset_jd = jd + 0.75   # 6 PM approximation
        
        # Traditional planetary hour sequence
        day_sequence = ['Sun', 'Venus', 'Mercury', 'Moon', 'Saturn', 'Jupiter', 'Mars']
        night_sequence = ['Jupiter', 'Mars', 'Sun', 'Venus', 'Mercury', 'Moon', 'Saturn']
        
        # Calculate current planetary hour
        current_hour = date.hour
        
        if 6 <= current_hour < 18:  # Daytime
            hour_index = ((current_hour - 6) + (date.weekday() * 12)) % 7
            current_ruler = day_sequence[hour_index]
        else:  # Nighttime
            hour_index = ((current_hour - 18) + (date.weekday() * 12)) % 7
            current_ruler = night_sequence[hour_index]
        
        return {
            'current_ruler': current_ruler,
            'is_day': 6 <= current_hour < 18,
            'hour_number': (current_hour - 6) % 12 + 1 if 6 <= current_hour < 18 else (current_hour - 18) % 12 + 1
        }
    
    @staticmethod
    def _get_zodiac_sign(longitude: float) -> str:
        """Convert longitude to zodiac sign"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[int(longitude // 30)]
    
    @staticmethod
    def _find_retrograde_start(year: int, month: int) -> Optional[datetime]:
        """Find when Mercury retrograde starts in given month"""
        # Simplified - would need more precise calculation
        for day in range(1, 32):
            try:
                date = datetime(year, month, day)
                jd = swe.julday(date.year, date.month, date.day)
                pos, speed = swe.calc_ut(jd, swe.MERCURY, swe.FLG_SPEED)
                
                if speed[0] < 0:  # First retrograde day
                    return date
            except ValueError:
                continue
        return None
    
    @staticmethod
    def _find_retrograde_end(year: int, month: int) -> Optional[datetime]:
        """Find when Mercury retrograde ends"""
        # Simplified - would need more precise calculation
        start_month = month
        for month_offset in range(2):  # Check current and next month
            check_month = start_month + month_offset
            if check_month > 12:
                check_month -= 12
                year += 1
            
            for day in range(1, 32):
                try:
                    date = datetime(year, check_month, day)
                    jd = swe.julday(date.year, date.month, date.day)
                    pos, speed = swe.calc_ut(jd, swe.MERCURY, swe.FLG_SPEED)
                    
                    if speed[0] > 0:  # First direct day after retrograde
                        return date
                except ValueError:
                    continue
        return None
    
    @staticmethod
    def _calculate_next_sign_change(moon_longitude: float, moon_speed: float) -> Optional[float]:
        """Calculate hours until Moon changes sign"""
        current_sign_end = ((int(moon_longitude // 30) + 1) * 30) % 360
        degrees_to_go = (current_sign_end - moon_longitude) % 360
        
        if degrees_to_go == 0:
            degrees_to_go = 30
        
        # Moon moves about 0.5 degrees per hour
        hours_to_change = degrees_to_go / (moon_speed / 24)
        
        return hours_to_change if hours_to_change <= 24 else None
    
    @staticmethod
    def _find_next_aspect(moon_longitude: float, moon_speed: float, planet_longitude: float) -> Optional[float]:
        """Find hours until next major aspect"""
        aspect_angles = [0, 60, 90, 120, 180]  # Conjunction, sextile, square, trine, opposition
        
        closest_aspect_time = None
        
        for angle in aspect_angles:
            # Calculate target longitude for this aspect
            target_longitude = (planet_longitude + angle) % 360
            
            # Calculate degrees Moon needs to travel
            degrees_to_aspect = (target_longitude - moon_longitude) % 360
            
            # Calculate time (Moon moves ~0.5 degrees per hour)
            hours_to_aspect = degrees_to_aspect / (moon_speed / 24)
            
            if hours_to_aspect <= 24 and (not closest_aspect_time or hours_to_aspect < closest_aspect_time):
                closest_aspect_time = hours_to_aspect
        
        return closest_aspect_time