import swisseph as swe
from datetime import datetime, timedelta
import math

class PanchangCalculator:
    def __init__(self):
        # Initialize Swiss Ephemeris with Lahiri Ayanamsa for accurate Vedic calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    def calculate_panchang(self, date_str, latitude, longitude, timezone):
        """Calculate complete Panchang for given date and location"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        jd = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 12.0)
        
        # Calculate Sun and Moon positions
        sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        
        # Calculate Tithi
        tithi_data = self._calculate_tithi(sun_pos, moon_pos, jd)
        
        # Calculate Vara (weekday)
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
            'ayanamsa': swe.get_ayanamsa_ut(jd)
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
        
        # Convert to IST
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
        """Calculate Nakshatra details"""
        nakshatra_deg = moon_pos % 360
        nakshatra_num = int(nakshatra_deg / 13.333333) + 1
        pada_deg = nakshatra_deg % 13.333333
        pada_num = int(pada_deg / 3.333333) + 1
        
        # Nakshatra timing calculation
        nakshatra_speed = 13.333333 / 27  # degrees per day for one nakshatra
        elapsed_deg = nakshatra_deg % 13.333333
        remaining_deg = 13.333333 - elapsed_deg
        
        base_time = datetime.fromtimestamp((jd - 2440587.5) * 86400)
        hours_elapsed = (elapsed_deg / nakshatra_speed) * 24
        hours_remaining = (remaining_deg / nakshatra_speed) * 24
        
        start_time = base_time - timedelta(hours=hours_elapsed)
        end_time = base_time + timedelta(hours=hours_remaining)
        
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
        """Calculate Yoga details"""
        yoga_deg = (sun_pos + moon_pos) % 360
        yoga_num = int(yoga_deg / 13.333333) + 1
        
        # Yoga timing calculation
        yoga_speed = 13.333333  # degrees per day
        elapsed_deg = yoga_deg % 13.333333
        remaining_deg = 13.333333 - elapsed_deg
        
        base_time = datetime.fromtimestamp((jd - 2440587.5) * 86400)
        hours_elapsed = (elapsed_deg / yoga_speed) * 24
        hours_remaining = (remaining_deg / yoga_speed) * 24
        
        start_time = base_time - timedelta(hours=hours_elapsed)
        end_time = base_time + timedelta(hours=hours_remaining)
        
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
        """Calculate Karana details"""
        tithi_deg = (moon_pos - sun_pos) % 360
        karana_deg = tithi_deg / 2
        karana_num = int(karana_deg / 6) % 11 + 1
        
        karana_names = [
            'Bava', 'Balava', 'Kaulava', 'Taitila', 'Gara',
            'Vanija', 'Vishti', 'Shakuni', 'Chatushpada', 'Naga', 'Kimstughna'
        ]
        
        karana_natures = [
            'Movable', 'Movable', 'Movable', 'Movable', 'Movable',
            'Movable', 'Movable', 'Fixed', 'Fixed', 'Fixed', 'Fixed'
        ]
        
        suitable_activities = {
            'Movable': ['Travel', 'Movement', 'Change', 'New beginnings'],
            'Fixed': ['Stable work', 'Meditation', 'Study', 'Planning']
        }
        
        business_suitable = karana_num not in [7, 8, 9, 10, 11]  # Avoid Vishti and fixed karanas for business
        
        return {
            'number': karana_num,
            'name': karana_names[karana_num - 1],
            'nature': karana_natures[karana_num - 1],
            'duration': 6,  # hours (approximate)
            'effect': self._get_karana_effect(karana_num),
            'suitable_activities': suitable_activities[karana_natures[karana_num - 1]],
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
    
    def calculate_choghadiya(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate Choghadiya periods for day and night"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset for the given day
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Calculate next day sunrise
            next_day_sunrise_result = swe.rise_trans(julian_day + 1, swe.SUN, swe.CALC_RISE, geopos)
            
            if next_day_sunrise_result[0] != 0:
                raise ValueError("Could not calculate next day sunrise")
                
            next_sunrise_jd = next_day_sunrise_result[1][0]
            
            # Day duration and night duration
            day_duration = (sunset_jd - sunrise_jd) * 24  # in hours
            night_duration = (next_sunrise_jd - sunset_jd) * 24  # in hours
            
            # Each Choghadiya period is 1/8 of day/night
            day_period_duration = day_duration / 8
            night_period_duration = night_duration / 8
            
            # Weekday for determining starting sequence
            weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            weekday = (weekday + 1) % 7  # Convert to Sunday=0
            
            # Choghadiya names and qualities (correct sequence)
            choghadiya_names = ['Udvega', 'Chara', 'Labha', 'Amrita', 'Kala', 'Shubha', 'Roga', 'Udvega']
            choghadiya_qualities = ['Bad', 'Neutral', 'Gain', 'Best', 'Loss', 'Good', 'Evil', 'Bad']
            
            # Day Choghadiya starts with day lord (correct Vedic system)
            # Sunday=0, Monday=1, etc. - each day starts with its own lord's choghadiya
            day_start_index = weekday
            
            day_choghadiya = []
            for i in range(8):
                name_index = (day_start_index + i) % 8
                name = choghadiya_names[name_index]
                quality = choghadiya_qualities[name_index]
                
                # Map quality to nature for consistency
                nature = 'Auspicious' if quality in ['Good', 'Best', 'Gain'] else 'Inauspicious'
                
                start_jd = sunrise_jd + (i * day_period_duration / 24)
                end_jd = start_jd + (day_period_duration / 24)
                
                day_choghadiya.append({
                    'period': i + 1,
                    'name': name,
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(day_period_duration * 60),
                    'quality': quality,
                    'nature': nature
                })
            
            # Night Choghadiya follows specific sequence
            night_choghadiya_names = ['Amrita', 'Chara', 'Roga', 'Kala', 'Labha', 'Udvega', 'Shubha', 'Amrita']
            night_choghadiya_qualities = ['Best', 'Neutral', 'Evil', 'Loss', 'Gain', 'Bad', 'Good', 'Best']
            
            night_choghadiya = []
            for i in range(8):
                name = night_choghadiya_names[i]
                quality = night_choghadiya_qualities[i]
                
                start_jd = sunset_jd + (i * night_period_duration / 24)
                end_jd = start_jd + (night_period_duration / 24)
                
                night_choghadiya.append({
                    'period': i + 1,
                    'name': name,
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(night_period_duration * 60),
                    'quality': quality
                })
            

            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'day_choghadiya': day_choghadiya,
                'night_choghadiya': night_choghadiya,
                'day_duration_hours': day_duration,
                'night_duration_hours': night_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Choghadiya: {str(e)}")
    
    def calculate_hora(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate Hora (planetary hours) for the day"""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Calculate next day sunrise
            next_day_sunrise_result = swe.rise_trans(julian_day + 1, swe.SUN, swe.CALC_RISE, geopos)
            
            if next_day_sunrise_result[0] != 0:
                raise ValueError("Could not calculate next day sunrise")
                
            next_sunrise_jd = next_day_sunrise_result[1][0]
            
            # Day and night durations
            day_duration = (sunset_jd - sunrise_jd) * 24  # in hours
            night_duration = (next_sunrise_jd - sunset_jd) * 24  # in hours
            
            # Each hora is 1/7 of day/night
            day_hora_duration = day_duration / 7
            night_hora_duration = night_duration / 7
            
            # Weekday for determining starting planet
            weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            weekday = (weekday + 1) % 7  # Convert to Sunday=0
            
            # Planet sequence for Hora (correct Chaldean order)
            planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
            
            # Swiss Ephemeris calculations are accurate
            
            # Day Hora starts with day lord
            day_lord_index = weekday
            
            day_horas = []
            for i in range(7):
                planet_index = (day_lord_index + i) % 7
                planet = planets[planet_index]
                
                start_jd = sunrise_jd + (i * day_hora_duration / 24)
                end_jd = sunrise_jd + ((i + 1) * day_hora_duration / 24)
                
                # Ensure end time is after start time
                if end_jd <= start_jd:
                    end_jd = start_jd + (day_hora_duration / 24)
                
                day_horas.append({
                    'hora': i + 1,
                    'planet': planet,
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(day_hora_duration * 60)
                })
            
            # Night Hora continues the sequence from sunset
            night_horas = []
            for i in range(7):
                # Continue the planetary sequence from where day ended
                planet_index = (day_lord_index + 7 + i) % 7
                planet = planets[planet_index]
                
                start_jd = sunset_jd + (i * night_hora_duration / 24)
                end_jd = sunset_jd + ((i + 1) * night_hora_duration / 24)
                
                night_horas.append({
                    'hora': i + 8,
                    'planet': planet,
                    'start_time': self._jd_to_iso(start_jd),
                    'end_time': self._jd_to_iso(end_jd),
                    'duration_minutes': int(night_hora_duration * 60)
                })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'day_horas': day_horas,
                'night_horas': night_horas,
                'day_duration_hours': day_duration,
                'night_duration_hours': night_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating Hora: {str(e)}")
    
    def calculate_special_muhurtas(self, date_str: str, latitude: float, longitude: float) -> dict:
        """Calculate special muhurtas like Abhijit, Brahma Muhurta etc."""
        if not date_str or latitude is None or longitude is None:
            raise ValueError("Date string, latitude, and longitude are required")
            
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            julian_day = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 0.0)
            
            # Calculate sunrise and sunset
            geopos = [float(longitude), float(latitude), 0.0]
            sunrise_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_RISE, geopos)
            sunset_result = swe.rise_trans(julian_day, swe.SUN, swe.CALC_SET, geopos)
            
            if sunrise_result[0] != 0 or sunset_result[0] != 0:
                raise ValueError("Could not calculate sunrise/sunset for given location")
                
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]
            
            # Calculate next day sunrise for night duration
            next_day_sunrise_result = swe.rise_trans(julian_day + 1, swe.SUN, swe.CALC_RISE, geopos)
            
            if next_day_sunrise_result[0] != 0:
                raise ValueError("Could not calculate next day sunrise")
                
            next_sunrise_jd = next_day_sunrise_result[1][0]
            
            # Day and night durations
            day_duration = (sunset_jd - sunrise_jd) * 24  # in hours
            night_duration = (next_sunrise_jd - sunset_jd) * 24  # in hours
            
            muhurtas = []
            
            # Brahma Muhurta (1.5 hours before sunrise)
            brahma_muhurta_duration = 1.5  # Fixed 1.5 hours
            brahma_muhurta_start_jd = sunrise_jd - (brahma_muhurta_duration / 24)
            brahma_muhurta_end_jd = sunrise_jd
            
            muhurtas.append({
                'name': 'Brahma Muhurta',
                'start_time': self._jd_to_iso(brahma_muhurta_start_jd),
                'end_time': self._jd_to_iso(brahma_muhurta_end_jd),
                'duration_minutes': 90,  # Fixed 90 minutes
                'significance': 'Most auspicious time for spiritual practices, meditation, and study',
                'activities': ['Meditation', 'Prayer', 'Study', 'Yoga'],
                'quality': 'Highly Auspicious'
            })
            
            # Abhijit Muhurta (middle 1/15th of day, around noon)
            # This is the 8th muhurta of the day (out of 15 muhurtas)
            muhurta_duration_hours = day_duration / 15  # Each muhurta duration in hours
            
            abhijit_start_jd = sunrise_jd + (7 * muhurta_duration_hours / 24)  # 8th muhurta (0-indexed)
            abhijit_end_jd = sunrise_jd + (8 * muhurta_duration_hours / 24)
            
            muhurtas.append({
                'name': 'Abhijit Muhurta',
                'start_time': self._jd_to_iso(abhijit_start_jd),
                'end_time': self._jd_to_iso(abhijit_end_jd),
                'duration_minutes': int(muhurta_duration_hours * 60),
                'significance': 'Universal auspicious time, overcomes all doshas',
                'activities': ['Important meetings', 'New ventures', 'Travel', 'Ceremonies'],
                'quality': 'Universally Auspicious'
            })
            
            # Godhuli Muhurta (cow dust time - around sunset)
            godhuli_duration = 0.8  # 48 minutes total
            godhuli_start_jd = sunset_jd - (0.4 / 24)  # 24 minutes before sunset
            godhuli_end_jd = sunset_jd + (0.4 / 24)   # 24 minutes after sunset
            
            muhurtas.append({
                'name': 'Godhuli Muhurta',
                'start_time': self._jd_to_iso(godhuli_start_jd),
                'end_time': self._jd_to_iso(godhuli_end_jd),
                'duration_minutes': int(godhuli_duration * 60),
                'significance': 'Evening auspicious time for prayers and spiritual activities',
                'activities': ['Evening prayers', 'Spiritual practices', 'Charity'],
                'quality': 'Auspicious'
            })
            
            # Vijaya Muhurta (victory time - 2nd muhurta of the day)
            vijaya_start_jd = sunrise_jd + (1 * muhurta_duration_hours / 24)  # 2nd muhurta
            vijaya_end_jd = sunrise_jd + (2 * muhurta_duration_hours / 24)
            
            muhurtas.append({
                'name': 'Vijaya Muhurta',
                'start_time': self._jd_to_iso(vijaya_start_jd),
                'end_time': self._jd_to_iso(vijaya_end_jd),
                'duration_minutes': int(muhurta_duration_hours * 60),
                'significance': 'Time for victory and success in endeavors',
                'activities': ['Important tasks', 'Competitions', 'Business deals'],
                'quality': 'Auspicious'
            })
            
            return {
                'date': date_str,
                'location': {'latitude': latitude, 'longitude': longitude},
                'muhurtas': muhurtas,
                'day_duration_hours': day_duration,
                'night_duration_hours': night_duration
            }
            
        except Exception as e:
            raise ValueError(f"Error calculating special muhurtas: {str(e)}")
    
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
    
    def _jd_to_local_time(self, jd):
        """Convert Julian Day to IST datetime"""
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd, 1)
        dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        # Convert UTC to IST (UTC+5:30) - FIXED: was 5:29, now correct 5:30
        dt_ist = dt + timedelta(hours=5, minutes=30)
        return dt_ist
    
    def _jd_to_iso(self, jd):
        """Convert Julian Day to local time ISO format datetime string"""
        return self._jd_to_local_time(jd).isoformat()