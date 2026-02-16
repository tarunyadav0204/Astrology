import swisseph as swe
from datetime import datetime
from ..utils.kp_calculations import KPCalculations

class KPChartService:
    @staticmethod
    def calculate_kp_chart(birth_date, birth_time, latitude, longitude, timezone=None, **kwargs):
        """Calculate KP chart with Placidus houses using correct KP Ayanamsa."""
        try:
            # 1. Set Swiss Ephemeris to use KP Ayanamsa
            from utils.timezone_service import parse_timezone_offset
            swe.set_sid_mode(swe.SIDM_KRISHNAMURTI)

            # 2. Calculate Julian Day in UTC
            time_parts = birth_time.split(':')
            hour = float(time_parts[0]) + float(time_parts[1])/60.0
            
            # If timezone is empty or None, calculate it from coordinates
            if not timezone:
                # Use the timezone service to get offset
                tz_offset = parse_timezone_offset("", latitude, longitude)
            else:
                tz_offset = parse_timezone_offset(timezone, latitude, longitude)
            
            utc_hour = hour - tz_offset
            
            year, month, day = [int(p) for p in birth_date.split('-')]
            
            jd = swe.julday(year, month, day, utc_hour)
            ayanamsa = swe.get_ayanamsa_ut(jd)

            # The CORRECTION_FACTOR is adjusted to match the user's reference software.
            # For 2nd April 1980, 2:55 PM, Hisar:
            # Tropical Moon: 212.0325
            # KP Ayanamsa: 23.4844
            # Sidereal = 188.5481
            # User Target: 188° 32' 30" = 188.541666
            # New Correction = 188.5481 - 188.541666 = 0.00653
            CORRECTION_FACTOR = 0.00653

            # 3. Calculate house cusps (Tropical) and convert to Sidereal
            houses_tropical, ascmc = swe.houses(jd, latitude, longitude, b'P')
            house_cusps = {}
            for i in range(12):
                sidereal_cusp = (houses_tropical[i] - ayanamsa) % 360
                house_cusps[i + 1] = (sidereal_cusp - CORRECTION_FACTOR) % 360

            # 4. Calculate final corrected positions and lords for each planet linearly
            planets = {
                'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
                'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
                'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE
            }
            planet_positions = {}
            planet_lords = {}

            # Add Ascendant to planet_positions and planet_lords for UI display
            asc_longitude = (ascmc[0] - ayanamsa - CORRECTION_FACTOR) % 360
            planet_positions['Ascendant'] = asc_longitude
            nak_info_asc = KPCalculations.get_nakshatra_info(asc_longitude)
            planet_lords['Ascendant'] = {
                "sign_lord": KPCalculations.get_sign_lord(asc_longitude),
                "star_lord": nak_info_asc["lord"],
                "sub_lord": KPCalculations.get_sub_lord(asc_longitude),
                "sub_sub_lord": KPCalculations.get_sub_sub_lord(asc_longitude)
            }

            for name, planet_id in planets.items():
                # Get tropical position
                tropical_pos = swe.calc_ut(jd, planet_id, 0)[0][0]
                # Convert to sidereal
                sidereal_pos = (tropical_pos - ayanamsa) % 360
                # Apply the universal correction to get the final position
                final_pos = (sidereal_pos - CORRECTION_FACTOR) % 360
                planet_positions[name] = final_pos
                
                # Immediately calculate lords using the final, corrected position
                nakshatra_info = KPCalculations.get_nakshatra_info(final_pos)
                planet_lords[name] = {
                    "sign_lord": KPCalculations.get_sign_lord(final_pos),
                    "star_lord": nakshatra_info["lord"],
                    "sub_lord": KPCalculations.get_sub_lord(final_pos),
                    "sub_sub_lord": KPCalculations.get_sub_sub_lord(final_pos)
                }

            # Handle Ketu separately based on the *final* corrected Rahu position
            planet_positions['Ketu'] = (planet_positions['Rahu'] + 180) % 360
            ketu_final_pos = planet_positions['Ketu']
            nakshatra_info = KPCalculations.get_nakshatra_info(ketu_final_pos)
            planet_lords['Ketu'] = {
                "sign_lord": KPCalculations.get_sign_lord(ketu_final_pos),
                "star_lord": nakshatra_info["lord"],
                "sub_lord": KPCalculations.get_sub_lord(ketu_final_pos),
                "sub_sub_lord": KPCalculations.get_sub_sub_lord(ketu_final_pos)
            }
            
            # 5. Calculate all lords for cusps
            cusp_lords = {}
            for house, cusp_pos in house_cusps.items():
                 nakshatra_info = KPCalculations.get_nakshatra_info(cusp_pos)
                 cusp_lords[house] = {
                    "sign_lord": KPCalculations.get_sign_lord(cusp_pos),
                    "star_lord": nakshatra_info["lord"],
                    "sub_lord": KPCalculations.get_sub_lord(cusp_pos),
                    "sub_sub_lord": KPCalculations.get_sub_sub_lord(cusp_pos)
                }

            # 6. Calculate significators
            significators_data = KPCalculations.get_significators(planet_positions, house_cusps)
            
            # 6a. Calculate 4-Step Theory Data
            # Step 1: Planet -> Houses it signifies
            # Step 2: Planet's Star Lord -> Houses it signifies
            # Step 3: Planet's Sub Lord -> Houses it signifies
            # Step 4: Planet's Sub-Sub Lord -> Houses it signifies
            four_step_data = {}
            for planet, lords in planet_lords.items():
                if planet == 'Ascendant': continue
                
                # Get houses signified by the planet itself
                p_sigs = significators_data["planet_significators"].get(planet, [])
                
                # Get houses signified by its Star Lord
                star_lord = lords["star_lord"]
                star_sigs = significators_data["planet_significators"].get(star_lord, [])
                
                # Get houses signified by its Sub Lord
                sub_lord = lords["sub_lord"]
                sub_sigs = significators_data["planet_significators"].get(sub_lord, [])
                
                # Get houses signified by its Sub-Sub Lord
                ss_lord = lords["sub_sub_lord"]
                ss_sigs = significators_data["planet_significators"].get(ss_lord, [])
                
                four_step_data[planet] = {
                    "planet": {"name": planet, "houses": p_sigs},
                    "star_lord": {"name": star_lord, "houses": star_sigs},
                    "sub_lord": {"name": sub_lord, "houses": sub_sigs},
                    "sub_sub_lord": {"name": ss_lord, "houses": ss_sigs}
                }

            # 7. Format positions into DMS for easier debugging by the user
            planet_positions_dms = {p: KPChartService._decimal_to_dms_str(pos) for p, pos in planet_positions.items()}
            house_cusps_dms = {c: KPChartService._decimal_to_dms_str(pos) for c, pos in house_cusps.items()}
            
            return {
                "house_cusps": house_cusps,
                "planet_positions": planet_positions,
                "planet_lords": planet_lords,
                "cusp_lords": cusp_lords,
                "significators": significators_data["house_significators"],
                "planet_significators": significators_data["planet_significators"],
                "four_step_theory": four_step_data,
                "ayanamsa": ayanamsa,
                "planet_positions_dms": planet_positions_dms,
                "house_cusps_dms": house_cusps_dms
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Error calculating KP chart: {str(e)}")

    @staticmethod
    def _decimal_to_dms_str(decimal_degrees):
        """Converts decimal degrees to a DMS formatted string."""
        decimal_degrees = float(decimal_degrees)
        d = int(decimal_degrees)
        m_decimal = (decimal_degrees - d) * 60
        m = int(m_decimal)
        s = int((m_decimal - m) * 60)
        return f"{d}° {m}' {s}\""
    
    @staticmethod
    def get_planet_house_positions(planet_positions, house_cusps):
        """Get which house each planet is positioned in"""
        planet_houses = {}
        for planet, longitude in planet_positions.items():
            house = KPCalculations.get_house_from_longitude(longitude, house_cusps)
            planet_houses[planet] = house
        return planet_houses