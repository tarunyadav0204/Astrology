import swisseph as swe
from datetime import datetime, timedelta
import math
from utils.timezone_service import parse_timezone_offset


class PanchangCalculator:
    def __init__(self):
        # Initialize Swiss Ephemeris with Lahiri Ayanamsa for accurate Vedic calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self._tz_offset_hours = 0.0

    def calculate_panchang(self, date_str, latitude, longitude, timezone, time_str=None, reference="sunrise"):
        """
        Calculate complete Panchang for given date and location.

        reference:
          - "sunrise" (default): Hindu day elements at local sunrise (daily panchang)
          - "noon": civil noon local (legacy / approximate)
          - explicit time_str "HH:MM[:SS]": evaluate at that local civil time
        """
        self._tz_offset_hours = parse_timezone_offset(timezone, latitude, longitude, for_date=date_str)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        if time_str:
            parts = str(time_str).split(':')
            local_hour = int(parts[0]) + int(parts[1]) / 60.0
            if len(parts) > 2:
                local_hour += int(float(parts[2])) / 3600.0
            utc_hour = local_hour - self._tz_offset_hours
            jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, utc_hour)
        elif reference == "noon":
            utc_hour = 12.0 - self._tz_offset_hours
            jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, utc_hour)
        else:
            # Default: evaluate at local sunrise (Hindu day start)
            jd0 = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
            geopos = [float(longitude), float(latitude), 0.0]
            rise = swe.rise_trans(jd0, swe.SUN, swe.CALC_RISE, geopos)
            if rise[0] == 0:
                jd = rise[1][0]
            else:
                utc_hour = 6.0 - self._tz_offset_hours
                jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, utc_hour)

        # Calculate Sun and Moon positions
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]

        # Calculate Tithi
        tithi_data = self._calculate_tithi(sun_pos, moon_pos, jd)

        # Calculate Vara (weekday) from local sunrise civil date when possible
        vara_data = self._calculate_vara(jd)

        # Calculate Nakshatra
        nakshatra_data = self._calculate_nakshatra(moon_pos, jd)

        # Calculate Yoga
        yoga_data = self._calculate_yoga(sun_pos, moon_pos, jd)

        # Calculate Karana
        karana_data = self._calculate_karana(sun_pos, moon_pos, jd)

        return {
            'tithi': tithi_data,
            'vara': vara_data,
            'nakshatra': nakshatra_data,
            'yoga': yoga_data,
            'karana': karana_data,
            'ayanamsa': swe.get_ayanamsa_ut(jd),
            'reference_jd': jd,
            'timezone_offset_hours': self._tz_offset_hours,
        }
    
    def _calculate_tithi(self, sun_pos, moon_pos, jd):
        """Calculate Tithi details with precise timing"""
        tithi_deg = (moon_pos - sun_pos) % 360
        tithi_num = int(tithi_deg / 12) + 1
        
        # Calculate precise start and end times using iterative method
        current_tithi_start_deg = (tithi_num - 1) * 12
        current_tithi_end_deg = tithi_num * 12
        
        # Handle Amavasya (30th Tithi) - it ends at 0 degrees (360)
        if tithi_num == 30:
            current_tithi_end_deg = 360
        
        # Find start time by going backwards
        start_jd = self._find_tithi_moment(jd, current_tithi_start_deg, backwards=True)
        # Find end time by going forwards  
        end_jd = self._find_tithi_moment(jd, current_tithi_end_deg, backwards=False)
        
        # Convert to local time
        start_time = self._jd_to_local_time(start_jd)
        end_time = self._jd_to_local_time(end_jd)
        
        # Calculate elapsed percentage
        elapsed_deg = tithi_deg - current_tithi_start_deg
        elapsed_percent = (elapsed_deg / 12) * 100
        
        # Tithi lord calculation
        tithi_lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        lord = tithi_lords[(tithi_num - 1) % 7]
        
        return {
            'number': tithi_num,
            'name': self._get_tithi_name(tithi_num),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'elapsed': elapsed_percent,
            'duration': 12,
            'lord': lord,
            'significance': self._get_tithi_significance(tithi_num)
        }
    
    def _calculate_vara(self, jd):
        """Calculate Vara (weekday) details"""
        weekday = int((jd + 1.5) % 7)
        
        vara_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        vara_lords = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
        vara_deities = ['Surya', 'Chandra', 'Mangal', 'Budh', 'Guru', 'Shukra', 'Shani']
        vara_colors = ['#FFD700', '#C0C0C0', '#FF4500', '#32CD32', '#FFD700', '#FF69B4', '#000080']
        
        favorable_activities = {
            0: ['Spiritual practices', 'Government work', 'Leadership activities'],
            1: ['Travel', 'Water-related activities', 'Emotional matters'],
            2: ['Physical activities', 'Sports', 'Competitive work'],
            3: ['Education', 'Communication', 'Business'],
            4: ['Religious ceremonies', 'Teaching', 'Wisdom-seeking'],
            5: ['Arts', 'Beauty', 'Relationships', 'Luxury'],
            6: ['Hard work', 'Construction', 'Discipline']
        }
        
        return {
            'number': weekday + 1,
            'name': vara_names[weekday],
            'lord': vara_lords[weekday],
            'deity': vara_deities[weekday],
            'lucky_color': vara_colors[weekday],
            'favorable_activities': favorable_activities[weekday]
        }
    
    def _calculate_nakshatra(self, moon_pos, jd):
        """Calculate Nakshatra details with precise angular transition times"""
        nak_slice = 360.0 / 27.0
        nakshatra_deg = moon_pos % 360
        nakshatra_num = int(nakshatra_deg / nak_slice) + 1
        pada_deg = nakshatra_deg % nak_slice
        pada_num = int(pada_deg / (nak_slice / 4.0)) + 1

        start_boundary = (nakshatra_num - 1) * nak_slice
        end_boundary = nakshatra_num * nak_slice
        if end_boundary >= 360:
            end_boundary = 360.0

        start_jd = self._find_longitude_moment(jd, swe.MOON, start_boundary, backwards=True)
        end_jd = self._find_longitude_moment(jd, swe.MOON, end_boundary % 360 if end_boundary == 360 else end_boundary, backwards=False)
        start_time = self._jd_to_local_time(start_jd)
        end_time = self._jd_to_local_time(end_jd)

        nakshatra_names = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira',
            'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha',
            'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
            'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]

        nakshatra_lords = [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars',
            'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu',
            'Venus', 'Sun', 'Moon', 'Mars', 'Rahu',
            'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus',
            'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
            'Saturn', 'Mercury'
        ]

        nakshatra_deities = [
            'Ashwini Kumaras', 'Yama', 'Agni', 'Brahma', 'Soma',
            'Rudra', 'Aditi', 'Brihaspati', 'Nagas', 'Pitrs',
            'Bhaga', 'Aryaman', 'Savitar', 'Tvashtar', 'Vayu',
            'Indra-Agni', 'Mitra', 'Indra', 'Nirrti', 'Apas',
            'Vishve Devas', 'Vishnu', 'Vasus', 'Varuna', 'Aja Ekapada',
            'Ahir Budhnya', 'Pushan'
        ]

        career_focus = {
            1: 'Healing, Medicine', 2: 'Arts, Creativity', 3: 'Leadership, Fire-related',
            4: 'Agriculture, Beauty', 5: 'Research, Investigation', 6: 'Technology, Innovation',
            7: 'Travel, Trade', 8: 'Nurturing, Care', 9: 'Mysticism, Occult',
            10: 'Ancestry, Tradition', 11: 'Entertainment, Luxury', 12: 'Service, Healing',
            13: 'Crafts, Skills', 14: 'Arts, Architecture', 15: 'Independence, Trade',
            16: 'Friendship, Cooperation', 17: 'Devotion, Spirituality', 18: 'Wisdom, Knowledge',
            19: 'Destruction, Transformation', 20: 'Water, Liquids', 21: 'Victory, Achievement',
            22: 'Learning, Communication', 23: 'Music, Rhythm', 24: 'Healing, Medicine',
            25: 'Mysticism, Spirituality', 26: 'Compassion, Service', 27: 'Nourishment, Prosperity'
        }

        return {
            'number': nakshatra_num,
            'name': nakshatra_names[nakshatra_num - 1],
            'lord': nakshatra_lords[nakshatra_num - 1],
            'deity': nakshatra_deities[nakshatra_num - 1],
            'pada': pada_num,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'nature': self._get_nakshatra_nature(nakshatra_num),
            'career_focus': career_focus.get(nakshatra_num, 'General'),
            'compatible_nakshatras': self._get_compatible_nakshatras(nakshatra_num)
        }

    def _calculate_yoga(self, sun_pos, moon_pos, jd):
        """Calculate Yoga details with precise transition times"""
        yoga_slice = 360.0 / 27.0
        yoga_deg = (sun_pos + moon_pos) % 360
        yoga_num = int(yoga_deg / yoga_slice) + 1

        start_boundary = (yoga_num - 1) * yoga_slice
        end_boundary = yoga_num * yoga_slice
        start_jd = self._find_sum_longitude_moment(jd, start_boundary, backwards=True)
        end_jd = self._find_sum_longitude_moment(jd, end_boundary % 360 if end_boundary >= 360 else end_boundary, backwards=False)
        start_time = self._jd_to_local_time(start_jd)
        end_time = self._jd_to_local_time(end_jd)

        yoga_names = [
            'Vishkambha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana',
            'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
            'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra',
            'Siddhi', 'Vyatipata', 'Variyan', 'Parigha', 'Shiva',
            'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma',
            'Indra', 'Vaidhriti'
        ]

        yoga_qualities = [
            'Inauspicious', 'Auspicious', 'Auspicious', 'Auspicious', 'Auspicious',
            'Inauspicious', 'Auspicious', 'Auspicious', 'Inauspicious', 'Inauspicious',
            'Auspicious', 'Auspicious', 'Inauspicious', 'Auspicious', 'Inauspicious',
            'Auspicious', 'Inauspicious', 'Auspicious', 'Inauspicious', 'Auspicious',
            'Auspicious', 'Auspicious', 'Auspicious', 'Auspicious', 'Auspicious',
            'Auspicious', 'Inauspicious'
        ]

        recommended_activities = {
            'Auspicious': ['New ventures', 'Ceremonies', 'Important meetings', 'Travel'],
            'Inauspicious': ['Routine work', 'Spiritual practices', 'Meditation', 'Rest']
        }

        quality = yoga_qualities[yoga_num - 1]

        return {
            'number': yoga_num,
            'name': yoga_names[yoga_num - 1],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'quality': quality,
            'effect': self._get_yoga_effect(yoga_num),
            'recommended_activities': recommended_activities[quality],
            'spiritual_practice': self._get_yoga_spiritual_practice(yoga_num)
        }

    def _calculate_karana(self, sun_pos, moon_pos, jd):
        """Calculate Karana using the classical 60 half-tithi sequence."""
        tithi_deg = (moon_pos - sun_pos) % 360
        k_num = int(tithi_deg / 6) + 1  # 1..60

        movable = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara', 'Vanija', 'Vishti']
        if k_num == 1:
            karana_name = 'Kimstughna'
            nature = 'Fixed'
        elif k_num >= 58:
            fixed_map = {58: 'Shakuni', 59: 'Chatushpada', 60: 'Naga'}
            karana_name = fixed_map.get(k_num, 'Naga')
            nature = 'Fixed'
        else:
            karana_name = movable[(k_num - 2) % 7]
            nature = 'Movable'

        suitable_activities = {
            'Movable': ['Travel', 'Movement', 'Change', 'New beginnings'],
            'Fixed': ['Stable work', 'Meditation', 'Study', 'Planning']
        }
        business_suitable = karana_name not in ['Vishti', 'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna']

        return {
            'number': k_num,
            'name': karana_name,
            'nature': nature,
            'duration': 6,  # degrees of elongation (half-tithi)
            'effect': self._get_karana_effect(((k_num - 1) % 11) + 1),
            'suitable_activities': suitable_activities[nature],
            'business_suitable': business_suitable
        }
    
    def _get_tithi_name(self, tithi_num):
        """Get Tithi name"""
        names = [
            'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
            'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
            'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima',
            'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
            'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
            'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Amavasya'
        ]
        return names[tithi_num - 1]
    
    def _get_tithi_significance(self, tithi_num):
        """Get Tithi significance"""
        significances = {
            1: 'New beginnings, starting projects',
            2: 'Stability, building foundations',
            3: 'Growth, expansion',
            4: 'Obstacles, challenges',
            5: 'Knowledge, learning',
            6: 'Harmony, balance',
            7: 'Friendship, relationships',
            8: 'Transformation, change',
            9: 'Completion, fulfillment',
            10: 'Success, achievement',
            11: 'Spiritual practices, fasting',
            12: 'Joy, celebration',
            13: 'Auspicious activities',
            14: 'Preparation, planning',
            15: 'Full Moon - completion, fulfillment',
            30: 'New Moon - new beginnings, introspection'
        }
        return significances.get(tithi_num, 'General activities')
    
    def _get_nakshatra_nature(self, nakshatra_num):
        """Get Nakshatra nature"""
        natures = [
            'Swift', 'Fierce', 'Mixed', 'Gentle', 'Gentle',
            'Fierce', 'Movable', 'Swift', 'Fierce', 'Fierce',
            'Fierce', 'Gentle', 'Swift', 'Gentle', 'Movable',
            'Mixed', 'Gentle', 'Fierce', 'Fierce', 'Fierce',
            'Gentle', 'Gentle', 'Movable', 'Movable', 'Fierce',
            'Gentle', 'Gentle'
        ]
        return natures[nakshatra_num - 1]
    
    def _get_compatible_nakshatras(self, nakshatra_num):
        """Get compatible nakshatras (simplified)"""
        # This is a simplified compatibility - in reality it's much more complex
        compatible_groups = {
            1: ['Bharani', 'Krittika'], 2: ['Ashwini', 'Rohini'], 3: ['Bharani', 'Mrigashira'],
            4: ['Krittika', 'Ardra'], 5: ['Rohini', 'Punarvasu'], 6: ['Mrigashira', 'Pushya'],
        }
        return compatible_groups.get(nakshatra_num, ['General compatibility'])
    
    def _get_yoga_effect(self, yoga_num):
        """Get Yoga effect"""
        effects = [
            'Obstacles in work', 'Love and affection', 'Long life', 'Good fortune', 'Beauty and prosperity',
            'Extreme difficulties', 'Good deeds', 'Patience and stability', 'Pain and troubles', 'Obstacles',
            'Growth and prosperity', 'Stability', 'Calamities', 'Joy and happiness', 'Strength like diamond',
            'Success in endeavors', 'Calamities', 'Prosperity', 'Obstacles', 'Auspiciousness',
            'Success', 'Achievement', 'Auspiciousness', 'Purity', 'Knowledge',
            'Power and authority', 'Widowhood and troubles'
        ]
        return effects[yoga_num - 1]
    
    def _get_yoga_spiritual_practice(self, yoga_num):
        """Get recommended spiritual practice for Yoga"""
        practices = [
            'Ganesha worship', 'Lakshmi worship', 'Vishnu worship', 'Lakshmi worship', 'Saraswati worship',
            'Hanuman worship', 'Vishnu worship', 'Durga worship', 'Shiva worship', 'Hanuman worship',
            'Lakshmi worship', 'Vishnu worship', 'Kali worship', 'Krishna worship', 'Indra worship',
            'Ganesha worship', 'Kali worship', 'Kubera worship', 'Hanuman worship', 'Shiva worship',
            'Ganesha worship', 'Sadhya worship', 'Lakshmi worship', 'Saraswati worship', 'Brahma worship',
            'Indra worship', 'Vishnu worship'
        ]
        return practices[yoga_num - 1]
    
    def _get_karana_effect(self, karana_num):
        """Get Karana effect"""
        effects = [
            'Good for all activities', 'Strength and power', 'Family happiness', 'Friendship',
            'Illness and troubles', 'Trade and business', 'Obstacles and delays', 'Deception',
            'Quadruped related', 'Serpent related', 'Extreme difficulties'
        ]
        return effects[karana_num - 1]
    
    def calculate_choghadiya(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> dict:
        """
        Delegate to the shared calculators.PanchangCalculator (single source of truth).
        Keeps ISO timestamps expected by trading + web clients.
        """
        from utils.timezone_service import get_timezone_from_coordinates
        from calculators.panchang_calculator import PanchangCalculator as SharedPanchang

        tz = timezone or get_timezone_from_coordinates(latitude, longitude, for_date=date_str)
        self._tz_offset_hours = parse_timezone_offset(tz, latitude, longitude, for_date=date_str)
        shared = SharedPanchang()
        result = shared.calculate_choghadiya(date_str, latitude, longitude, tz)
        return {
            'date': date_str,
            'location': {'latitude': latitude, 'longitude': longitude},
            'timezone': tz,
            'day_choghadiya': result.get('day_choghadiya', []),
            'night_choghadiya': result.get('night_choghadiya', []),
        }

    def calculate_hora(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> dict:
        """Delegate planetary hours to shared calculator."""
        from utils.timezone_service import get_timezone_from_coordinates
        from calculators.panchang_calculator import PanchangCalculator as SharedPanchang

        tz = timezone or get_timezone_from_coordinates(latitude, longitude, for_date=date_str)
        self._tz_offset_hours = parse_timezone_offset(tz, latitude, longitude, for_date=date_str)
        shared = SharedPanchang()
        result = shared.calculate_hora(date_str, latitude, longitude, tz)
        if isinstance(result, dict) and 'error' in result:
            raise ValueError(result['error'])
        return {
            'date': date_str,
            'location': {'latitude': latitude, 'longitude': longitude},
            'timezone': tz,
            **result,
        }

    def calculate_special_muhurtas(self, date_str: str, latitude: float, longitude: float, timezone: str = None) -> dict:
        """Delegate Brahma/Abhijit muhurtas to shared calculator."""
        from utils.timezone_service import get_timezone_from_coordinates
        from calculators.panchang_calculator import PanchangCalculator as SharedPanchang

        tz = timezone or get_timezone_from_coordinates(latitude, longitude, for_date=date_str)
        self._tz_offset_hours = parse_timezone_offset(tz, latitude, longitude, for_date=date_str)
        shared = SharedPanchang()
        result = shared.calculate_special_muhurtas(date_str, latitude, longitude, tz)
        if isinstance(result, dict) and 'error' in result:
            raise ValueError(result['error'])
        return {
            'date': date_str,
            'location': {'latitude': latitude, 'longitude': longitude},
            'timezone': tz,
            **result,
        }

    def _find_tithi_moment(self, jd, target_deg, backwards=False):
        """Find the exact moment when tithi degree is reached"""
        # Search range: 2 days before/after
        start_jd = jd - 2 if backwards else jd
        end_jd = jd if backwards else jd + 2
        
        # Binary search for precision
        for _ in range(30):  # Max 30 iterations for binary search
            mid_jd = (start_jd + end_jd) / 2
            
            sun_pos = swe.calc_ut(mid_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(mid_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            current_deg = (moon_pos - sun_pos) % 360
            
            # Handle 360-degree wrap for target comparison
            if target_deg == 0 and current_deg > 180:
                current_deg -= 360
            elif target_deg == 360 and current_deg < 180:
                current_deg += 360
                
            diff = current_deg - target_deg
            
            if abs(diff) < 0.001:  # Within 0.001 degrees (about 3.6 seconds)
                return mid_jd
                
            if backwards:
                if diff > 0:
                    end_jd = mid_jd
                else:
                    start_jd = mid_jd
            else:
                if diff < 0:
                    start_jd = mid_jd
                else:
                    end_jd = mid_jd
                    
        return (start_jd + end_jd) / 2

    def _ang_diff(self, current, target):
        """Signed shortest difference current-target on a circle."""
        return (current - target + 180.0) % 360.0 - 180.0

    def _find_longitude_moment(self, jd, body, target_deg, backwards=False):
        """Binary-search when a body's sidereal longitude reaches target_deg."""
        start_jd = jd - 2 if backwards else jd
        end_jd = jd if backwards else jd + 2
        target = target_deg % 360.0

        for _ in range(40):
            mid_jd = (start_jd + end_jd) / 2.0
            current = swe.calc_ut(mid_jd, body, swe.FLG_SIDEREAL)[0][0] % 360.0
            diff = self._ang_diff(current, target)
            if abs(diff) < 0.0005:
                return mid_jd
            if backwards:
                if diff > 0:
                    end_jd = mid_jd
                else:
                    start_jd = mid_jd
            else:
                if diff < 0:
                    start_jd = mid_jd
                else:
                    end_jd = mid_jd
        return (start_jd + end_jd) / 2.0

    def _find_sum_longitude_moment(self, jd, target_deg, backwards=False):
        """Binary-search when (sun + moon) sidereal longitude reaches target_deg."""
        start_jd = jd - 2 if backwards else jd
        end_jd = jd if backwards else jd + 2
        target = target_deg % 360.0

        for _ in range(40):
            mid_jd = (start_jd + end_jd) / 2.0
            sun_pos = swe.calc_ut(mid_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(mid_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            current = (sun_pos + moon_pos) % 360.0
            diff = self._ang_diff(current, target)
            if abs(diff) < 0.0005:
                return mid_jd
            if backwards:
                if diff > 0:
                    end_jd = mid_jd
                else:
                    start_jd = mid_jd
            else:
                if diff < 0:
                    start_jd = mid_jd
                else:
                    end_jd = mid_jd
        return (start_jd + end_jd) / 2.0

    def _jd_to_local_time(self, jd):
        """Convert Julian Day (UT) to local datetime using active timezone offset."""
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        return dt_utc + timedelta(hours=float(self._tz_offset_hours or 0.0))

    def _jd_to_iso(self, jd):
        """Convert Julian Day to local time ISO format datetime string"""
        return self._jd_to_local_time(jd).isoformat()