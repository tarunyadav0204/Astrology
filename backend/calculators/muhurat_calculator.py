import swisseph as swe
from datetime import datetime, timedelta
import pytz
from panchang.panchang_calculator import PanchangCalculator
from utils.timezone_service import parse_timezone_offset


def _ordinal(number):
    """Return a grammatically correct ordinal for a positive integer."""
    try:
        value = int(number)
    except (TypeError, ValueError):
        return str(number)
    if 10 < value % 100 < 14:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return f'{value}{suffix}'


class MuhuratCalculator:
    PANCHAK_START_DEG = 300.0  # sidereal 20° Aquarius, start of Dhanishta pada 3
    KETU_KEY = -1  # Swiss Ephemeris exposes Rahu; Ketu is 180° opposite.
    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        self.panchang_calc = PanchangCalculator()
        
        self.CHILDBIRTH_NAKSHATRAS = [4, 5, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 24, 26, 27]
        self.VEHICLE_NAKSHATRAS = [1, 4, 5, 7, 8, 13, 14, 15, 17, 22, 23, 24, 27]
        self.HOME_NAKSHATRAS = [4, 5, 12, 14, 17, 21, 26, 27]
        self.GOLD_NAKSHATRAS = [1, 4, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 27]
        self.BUSINESS_NAKSHATRAS = [1, 4, 5, 8, 12, 13, 14, 17, 21, 26, 27]

        self.AVOID_TITHIS = [4, 9, 14, 30]
        self.AVOID_YOGAS = [1, 6, 9, 10, 13, 15, 17, 19, 27]
        
        # Must match panchang_calculator CHOG_NAMES (Amrita/Shubha/Labha/Chara).
        self.GOOD_CHOGHADIYA = ['Amrita', 'Shubha', 'Labha', 'Chara']

    def _is_panchak(self, jd_ut):
        moon = float(swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SIDEREAL)[0][0]) % 360.0
        return moon >= self.PANCHAK_START_DEG

    def _panchak_intervals(self, sunrise_jd, sunset_jd):
        step = 30.0 / 1440.0
        start, end = sunrise_jd - 1.5, sunset_jd + 1.5
        cursor, previous = start, self._is_panchak(start)
        active_start = start if previous else None
        intervals = []
        while cursor < end:
            nxt = min(cursor + step, end)
            current = self._is_panchak(nxt)
            if current != previous:
                lo, hi = cursor, nxt
                for _ in range(32):
                    mid = (lo + hi) / 2
                    if self._is_panchak(mid) == previous: lo = mid
                    else: hi = mid
                boundary = (lo + hi) / 2
                if current: active_start = boundary
                elif active_start is not None:
                    intervals.append((active_start, boundary)); active_start = None
            previous, cursor = current, nxt
        if active_start is not None: intervals.append((active_start, end))
        return intervals

    def _panchak_status(self, date_str, lat, lon, tz):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Anchor the rise/set search near the start of the civil date. A noon
        # reference can make Swiss Ephemeris return next sunrise/previous set.
        jd = swe.julday(date_obj.year, date_obj.month, date_obj.day, 0.0)
        geopos = (float(lon), float(lat), 0.0)
        rise = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        setting = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)[1][0]
        intervals = self._panchak_intervals(rise, setting)
        clipped = [(max(s, rise), min(e, setting)) for s, e in intervals if min(e, setting) > max(s, rise)]
        return {
            'is_panchak': bool(clipped),
            'name': 'Panchak',
            'reason': 'Moon is transiting Dhanishta pada 3/4, Shatabhisha, Purva Bhadrapada, Uttara Bhadrapada or Revati.',
            'intervals': [{'start': self._jd_to_local_time(s, tz), 'end': self._jd_to_local_time(e, tz)} for s, e in clipped],
        }
    
    def _parse_timezone(self, tz_str):
        """Helper to parse timezone string like 'UTC+5:30' into float offset"""
        offset = 0.0 # Default UTC
        if isinstance(tz_str, (int, float)):
            return float(tz_str)
        if isinstance(tz_str, str) and 'UTC' in tz_str:
            try:
                tz_part = tz_str.replace('UTC', '')
                sign = -1 if '-' in tz_part else 1
                tz_part = tz_part.replace('+', '').replace('-', '')
                
                if ':' in tz_part:
                    hours, minutes = tz_part.split(':')
                    offset = sign * (float(hours) + float(minutes)/60.0)
                else:
                    offset = sign * float(tz_part)
            except: pass
        return offset

    def _jd_to_local_time(self, jd_val, timezone_str):
        """Convert Julian Day to local time with proper timezone handling"""
        if not jd_val: return None
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
        
        # Parse timezone
        if timezone_str.startswith('UTC'):
            tz_offset = self._parse_timezone(timezone_str)
            dt_local = dt_utc + timedelta(hours=tz_offset)
        else:
            try:
                tz = pytz.timezone(timezone_str)
                dt_local = dt_utc.astimezone(tz)
            except:
                tz_offset = self._parse_timezone(timezone_str)
                dt_local = dt_utc + timedelta(hours=tz_offset)
        
        return dt_local.strftime('%I:%M %p')

    @staticmethod
    def _format_reason_interval(start_value, end_value):
        """Make Panchang ISO timestamps readable in rejection explanations."""
        try:
            start = datetime.fromisoformat(str(start_value).replace('Z', '+00:00'))
            end = datetime.fromisoformat(str(end_value).replace('Z', '+00:00'))
            return f"{start.strftime('%-d %b %Y, %I:%M %p')} – {end.strftime('%-d %b %Y, %I:%M %p')}"
        except (TypeError, ValueError):
            return f"{start_value} – {end_value}"

    def calculate_childbirth_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz_offset = parse_timezone_offset('', lat, lon)
            tz = f"UTC+{tz_offset}" if tz_offset >= 0 else f"UTC{tz_offset}"
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.CHILDBIRTH_NAKSHATRAS, [1, 2, 3, 4, 5, 6, 8, 11], [], "Childbirth")

    def calculate_vehicle_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None, birth_data=None,
                                  allow_caution_dates=False):
        # Auto-detect timezone if not provided
        if tz is None:
            tz_offset = parse_timezone_offset('', lat, lon)
            tz = f"UTC+{tz_offset}" if tz_offset >= 0 else f"UTC{tz_offset}"
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.VEHICLE_NAKSHATRAS, [0, 3, 6, 9], [1], "Vehicle Purchase",
            check_4th_house=True, karaka_planet=swe.VENUS, birth_data=birth_data,
            allow_caution_dates=allow_caution_dates)

    def calculate_griha_pravesh_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz_offset = parse_timezone_offset('', lat, lon)
            tz = f"UTC+{tz_offset}" if tz_offset >= 0 else f"UTC{tz_offset}"
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.HOME_NAKSHATRAS, [1, 4, 7, 10], [1, 6], "Griha Pravesh",
            check_4th_house=True, karaka_planet=swe.MARS)

    def calculate_gold_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz_offset = parse_timezone_offset('', lat, lon)
            tz = f"UTC+{tz_offset}" if tz_offset >= 0 else f"UTC{tz_offset}"
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.GOLD_NAKSHATRAS, [1, 2, 3, 4, 5, 6, 8, 11], [1], "Gold Purchase")

    def calculate_business_muhurat(self, start_date, end_date, lat, lon, user_nak, tz=None):
        if tz is None:
            tz_offset = parse_timezone_offset('', lat, lon)
            tz = f"UTC+{tz_offset}" if tz_offset >= 0 else f"UTC{tz_offset}"
        return self._generic_muhurat_search(start_date, end_date, lat, lon, user_nak, tz,
            self.BUSINESS_NAKSHATRAS, [1, 4, 7, 10], [1, 6], "Business Opening",
            check_4th_house=True)

    def _generic_muhurat_search(self, start_str, end_str, lat, lon, user_nak, tz_str, 
                              good_nakshatras, good_lagnas, avoid_weekdays, category,
                              check_4th_house=False, karaka_planet=None, birth_data=None,
                              allow_caution_dates=False):
        try:
            if 'T' in start_str: start_str = start_str.split('T')[0]
            if 'T' in end_str: end_str = end_str.split('T')[0]
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
        except ValueError:
            return {"error": "Invalid date format"}

        valid_slots = []
        rejected_dates = []
        natal_context = self._build_natal_context(birth_data) if birth_data else None
        current_date = start_date
        days_scanned = 0
        
        # Use timezone string directly for proper DST handling
        timezone_str = tz_str

        while current_date <= end_date and days_scanned < 60:
            date_str = current_date.strftime('%Y-%m-%d')
            date_warnings = []
            
            if current_date.weekday() in avoid_weekdays:
                warning = 'Tuesday is traditionally avoided for vehicle purchase.'
                if allow_caution_dates:
                    date_warnings.append(warning)
                else:
                    rejected_dates.append({'date': date_str, 'reasons': [warning]})
                    current_date += timedelta(days=1); days_scanned += 1; continue

            try:
                # 2. Panchang Check (Pass all args)
                panchang = self.panchang_calc.calculate_panchang(
                    date_str,
                    float(lat),
                    float(lon),
                    tz_str,
                    reference="sunrise",
                )
            except Exception as e:
                print(f"Panchang Error for {date_str}: {e}")
                rejected_dates.append({'date': date_str, 'reasons': ['Panchang could not be calculated for this date.']})
                current_date += timedelta(days=1); days_scanned += 1; continue

            panchak_status = self._panchak_status(date_str, lat, lon, tz_str)

            if panchak_status.get('is_panchak'):
                interval_text = ', '.join(
                    f"{item['start']}–{item['end']}" for item in panchak_status.get('intervals', [])
                )
                rejected_dates.append({
                    'date': date_str,
                    'reasons': [
                        f"Panchak is active during this date ({interval_text}).\n\nDecision: Not recommended for vehicle purchase."
                    ],
                    'panchak': panchak_status,
                })
                current_date += timedelta(days=1); days_scanned += 1; continue

            if panchang['tithi']['number'] in self.AVOID_TITHIS:
                warning = f"Tithi {panchang['tithi']['name']} is traditionally avoided for this purpose."
                if allow_caution_dates:
                    date_warnings.append(warning)
                else:
                    rejected_dates.append({'date': date_str, 'reasons': [warning]})
                    current_date += timedelta(days=1); days_scanned += 1; continue
            
            if panchang['yoga']['number'] in self.AVOID_YOGAS:
                yoga = panchang['yoga']
                interval = self._format_reason_interval(yoga['start_time'], yoga['end_time']) if yoga.get('start_time') and yoga.get('end_time') else 'the daily Panchang period'
                warning = f"{yoga['name']} Yoga — traditionally associated with {str(yoga.get('effect', 'obstacles')).lower()}. Active: {interval}."
                if allow_caution_dates:
                    date_warnings.append(warning)
                else:
                    rejected_dates.append({'date': date_str, 'reasons': [
                        f"{yoga['name']} Yoga\n\nTraditional effect: {str(yoga.get('effect', 'obstacles')).capitalize()}\nActive: {interval}\nDecision: Not recommended for vehicle purchase."
                    ]})
                    current_date += timedelta(days=1); days_scanned += 1; continue
            
            if panchang.get('karana', {}).get('name') == 'Vishti':
                warning = 'Vishti (Bhadra) Karana is active.'
                if allow_caution_dates:
                    date_warnings.append(warning)
                else:
                    rejected_dates.append({'date': date_str, 'reasons': [warning]})
                    current_date += timedelta(days=1); days_scanned += 1; continue

            daily_nak = panchang['nakshatra']['number']
            if daily_nak not in good_nakshatras:
                warning = f"Nakshatra {panchang['nakshatra']['name']} is outside the preferred vehicle-purpose set."
                if allow_caution_dates:
                    date_warnings.append(warning)
                else:
                    rejected_dates.append({'date': date_str, 'reasons': [warning]})
                    current_date += timedelta(days=1); days_scanned += 1; continue
                
            # The mobile flow always supplies the native's Janma Nakshatra.
            # Public PWA requests may not have birth details; in that case we
            # retain every other rule and explicitly omit the personalised
            # Tara Bala filter rather than inventing a birth star.
            tara_score = None
            if user_nak:
                dist = (daily_nak - user_nak)
                if dist < 0: dist += 27
                tara_score = (dist + 1) % 9
                if tara_score == 0: tara_score = 9
                if tara_score in [1, 3, 5, 7]:
                    warning = f"Tara Bala is unfavourable ({_ordinal(tara_score)} Tara from the natal Moon Nakshatra)."
                    if allow_caution_dates:
                        date_warnings.append(warning)
                    else:
                        rejected_dates.append({'date': date_str, 'reasons': [warning]})
                        current_date += timedelta(days=1); days_scanned += 1; continue

            # 4. Planetary Positions
            planet_positions = {}
            if check_4th_house or karaka_planet:
                # Calculate JD for noon in UTC (no timezone offset needed for planetary positions)
                jd_noon = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
                
                if karaka_planet:
                    karaka_pos = swe.calc_ut(jd_noon, karaka_planet, swe.FLG_SIDEREAL)[0][0]
                    sun_pos = swe.calc_ut(jd_noon, swe.SUN, swe.FLG_SIDEREAL)[0][0]
                    if self._angular_distance(sun_pos, karaka_pos) < 6:
                         warning = 'Venus is combust by the Sun.'
                         if allow_caution_dates:
                             date_warnings.append(warning)
                         else:
                             rejected_dates.append({'date': date_str, 'reasons': [warning]})
                             current_date += timedelta(days=1); days_scanned += 1; continue

                malefics = [0, 4, 6, 11, 12]
                occupied_signs = set()
                for p in malefics:
                    pos = swe.calc_ut(jd_noon, p, swe.FLG_SIDEREAL)[0][0]
                    sign = int(pos / 30)
                    occupied_signs.add(sign)
                planet_positions['malefics_in'] = occupied_signs

            # 5. Choghadiya (Pass TZ)
            try:
                choghadiya_data = self.panchang_calc.calculate_choghadiya(date_str, lat, lon, timezone=tz_str)
            except:
                choghadiya_data = None

            # 6. Fine-Grained Search with timezone
            day_slots = self._find_lagnas_detailed(
                current_date, float(lat), float(lon), timezone_str, 
                good_lagnas, planet_positions if check_4th_house else None,
                choghadiya_data, natal_context=natal_context,
                karaka_planet=karaka_planet,
            )
            
            if day_slots:
                if date_warnings:
                    for slot in day_slots:
                        slot['cautions'] = date_warnings + list(slot.get('cautions', []))
                        slot['rationale'] = f"This is a fallback date with cautions: {' '.join(date_warnings)} {slot.get('rationale') or ''}".strip()
                for slot in day_slots:
                    slot['panchak'] = bool(panchak_status.get('is_panchak'))
                    slot['panchak_warning'] = (
                        'Panchak is active during this slot; confirm with a qualified priest before using it.'
                        if panchak_status.get('is_panchak') else None
                    )
                    slot['panchak_intervals'] = panchak_status.get('intervals', [])
                    if panchak_status.get('is_panchak'):
                        slot['cautions'].insert(0, slot['panchak_warning'])
                        slot['rationale'] += ' Panchak is active, so priest confirmation is required.'
                valid_slots.append({
                    'date': date_str,
                    'weekday': panchang['vara']['name'],
                    'nakshatra': panchang['nakshatra']['name'],
                    'tara_quality': ('Excellent' if tara_score in [2,4,6,8,9] else 'Average') if tara_score else 'Not personalised',
                    'slots': day_slots,
                    'panchak': panchak_status,
                    'fallback': bool(allow_caution_dates and date_warnings),
                    'date_warnings': date_warnings,
                    'natal_vehicle_context': self._natal_vehicle_summary(natal_context) if natal_context else None,
                })
            else:
                rejected_dates.append({'date': date_str, 'reasons': ['No acceptable Lagna and Choghadiya slot remains after Rahu Kaal, Yamaganda and Gulika filtering.']})
            
            current_date += timedelta(days=1)
            days_scanned += 1
            
        return {
            "category": category,
            "period": f"{start_str} to {end_str}",
            "dates_found": len(valid_slots),
            "recommendations": valid_slots,
            "rejected_dates": rejected_dates,
            "mode": "best_available" if allow_caution_dates else "strict",
        }

    @staticmethod
    def _angular_distance(first, second):
        return abs((float(first) - float(second) + 180.0) % 360.0 - 180.0)

    @staticmethod
    def _sign_name(sign):
        return ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][int(sign) % 12]

    def _build_natal_context(self, birth_data):
        """Build only the natal facts needed for a vehicle election.

        This is deliberately small and auditable: Lagna/4th house, 4th lord,
        natal Moon and the D16 hook are not guessed when birth data is absent.
        """
        if not birth_data:
            return None
        try:
            date_value = str(birth_data.get('date') or birth_data.get('user_dob')).split('T')[0]
            time_value = str(birth_data.get('time') or birth_data.get('user_time') or '12:00')
            parts = time_value.split(':')
            local_hour = float(parts[0]) + float(parts[1] if len(parts) > 1 else 0) / 60.0
            lat = float(birth_data.get('latitude') if birth_data.get('latitude') is not None else birth_data.get('user_lat'))
            lon = float(birth_data.get('longitude') if birth_data.get('longitude') is not None else birth_data.get('user_lon'))
            tz = birth_data.get('timezone') or birth_data.get('user_timezone')
            offset = parse_timezone_offset(tz, lat, lon, for_date=date_value) if tz else parse_timezone_offset('', lat, lon, for_date=date_value)
            year, month, day = [int(x) for x in date_value.split('-')]
            jd = swe.julday(year, month, day, local_hour - offset)
            asc = swe.houses(jd, lat, lon, b'P')[1][0] % 360.0
            asc_sign = int(asc / 30)
            positions = self._sidereal_positions(jd)
            return {
                'asc_sign': asc_sign,
                'fourth_sign': (asc_sign + 3) % 12,
                'fourth_lord': self._sign_lord((asc_sign + 3) % 12),
                'moon_sign': int(positions[swe.MOON] / 30),
                'positions': positions,
                'birth_jd': jd,
            }
        except (TypeError, ValueError, KeyError):
            return None

    def _sidereal_positions(self, jd):
        positions = {
            planet: float(swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)[0][0]) % 360.0
            for planet in (swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
                           swe.JUPITER, swe.SATURN, swe.MEAN_NODE)
        }
        positions[self.KETU_KEY] = (positions[swe.MEAN_NODE] + 180.0) % 360.0
        return positions

    @staticmethod
    def _sign_lord(sign):
        return [swe.MARS, swe.VENUS, swe.MERCURY, swe.MOON, swe.SUN, swe.MERCURY,
                swe.VENUS, swe.MARS, swe.JUPITER, swe.SATURN, swe.SATURN, swe.JUPITER][int(sign) % 12]

    def _dignity_score(self, planet, sign):
        # Classical sign dignities used only as a transparent scoring input.
        exalted = {swe.SUN: 0, swe.MOON: 1, swe.MARS: 9, swe.MERCURY: 5,
                    swe.JUPITER: 3, swe.VENUS: 11, swe.SATURN: 6}
        debilitated = {swe.SUN: 6, swe.MOON: 7, swe.MARS: 3, swe.MERCURY: 11,
                       swe.JUPITER: 9, swe.VENUS: 5, swe.SATURN: 0}
        if exalted.get(planet) == sign:
            return 15, 'exalted'
        if debilitated.get(planet) == sign:
            return -15, 'debilitated'
        if self._sign_lord(sign) == planet:
            return 12, 'own sign'
        return 0, 'ordinary sign'

    def _evaluate_vehicle_slot(self, jd, lagna_sign, natal_context, karaka_planet):
        positions = self._sidereal_positions(jd)
        signs = {planet: int(value / 30) for planet, value in positions.items()}
        fourth_sign = (lagna_sign + 3) % 12
        eighth_sign = (lagna_sign + 7) % 12
        twelfth_sign = (lagna_sign + 11) % 12
        score = 50
        reasons = []
        positives = []
        cautions = []
        score_breakdown = [{'factor': 'Base election score', 'points': 50}]
        blocking = []
        malefics = (swe.SUN, swe.MARS, swe.SATURN, swe.MEAN_NODE, self.KETU_KEY)
        benefics = (swe.MOON, swe.MERCURY, swe.JUPITER, swe.VENUS)

        lagna_lord = self._sign_lord(lagna_sign)
        dignity, label = self._dignity_score(lagna_lord, signs[lagna_lord])
        score += dignity
        lagna_reason = f"Lagna lord {self._planet_name(lagna_lord)} is in {self._sign_name(signs[lagna_lord])} ({label})."
        reasons.append(lagna_reason)
        (positives if dignity >= 0 else cautions).append(lagna_reason)
        score_breakdown.append({'factor': 'Lagna lord dignity', 'points': dignity})

        fourth_lord = self._sign_lord(fourth_sign)
        dignity, label = self._dignity_score(fourth_lord, signs[fourth_lord])
        fourth_lord_points = round(dignity * 0.75)
        score += fourth_lord_points
        fourth_lord_reason = f"Election 4th lord {self._planet_name(fourth_lord)} is in {self._sign_name(signs[fourth_lord])} ({label})."
        reasons.append(fourth_lord_reason)
        (positives if dignity >= 0 else cautions).append(fourth_lord_reason)
        score_breakdown.append({'factor': 'Election 4th-lord dignity', 'points': fourth_lord_points})

        fourth_malefics = [p for p in malefics if signs[p] == fourth_sign]
        fourth_benefics = [p for p in benefics if signs[p] == fourth_sign]
        if fourth_malefics:
            score -= 18
            defect = 'A natural malefic occupies the election 4th house.'
            blocking.append(defect); cautions.append(defect)
        else:
            score += 8
            positive = 'The election 4th house is free from natural malefic occupation.'
            reasons.append(positive); positives.append(positive)
            score_breakdown.append({'factor': 'Unafflicted election 4th house', 'points': 8})
        if fourth_benefics:
            score += 8
            positive = 'A benefic occupies the election 4th house.'
            reasons.append(positive); positives.append(positive)
            score_breakdown.append({'factor': 'Benefic in election 4th house', 'points': 8})
        if any(signs[p] == eighth_sign for p in malefics):
            score -= 12
            caution = 'A natural malefic occupies the election 8th house; durability is reduced.'
            reasons.append(caution); cautions.append(caution)
            score_breakdown.append({'factor': 'Malefic in election 8th house', 'points': -12})
        if any(signs[p] == twelfth_sign for p in malefics):
            score -= 8
            caution = 'A natural malefic occupies the election 12th house; loss/expense is a caution.'
            reasons.append(caution); cautions.append(caution)
            score_breakdown.append({'factor': 'Malefic in election 12th house', 'points': -8})

        moon_sign = signs[swe.MOON]
        if natal_context:
            moon_distance = (moon_sign - natal_context['moon_sign']) % 12 + 1
            if moon_distance in (2, 4, 5, 8, 9, 12):
                score -= 10
                defect = f'Chandra Bala is unfavourable: Moon is {_ordinal(moon_distance)} from natal Moon.'
                # Chandra Bala is an important personal caution, but not an
                # absolute veto when the election chart otherwise has a
                # workable Lagna and no hard defect.
                cautions.append(defect)
                score_breakdown.append({'factor': 'Unfavourable Chandra Bala', 'points': -10})
            else:
                score += 10
                positive = f'Chandra Bala is favourable: Moon is {_ordinal(moon_distance)} from natal Moon.'
                reasons.append(positive); positives.append(positive)
                score_breakdown.append({'factor': 'Chandra Bala', 'points': 10})
        else:
            caution = 'Chandra Bala was not applied because birth details were unavailable.'
            reasons.append(caution); cautions.append(caution)

        venus_sign = signs[karaka_planet]
        venus_dignity, venus_label = self._dignity_score(karaka_planet, venus_sign)
        venus_points = round(venus_dignity * 0.5)
        score += venus_points
        venus_reason = f"Venus, the vehicle karaka, is in {self._sign_name(venus_sign)} ({venus_label})."
        reasons.append(venus_reason); (positives if venus_dignity >= 0 else cautions).append(venus_reason)
        score_breakdown.append({'factor': 'Vehicle karaka dignity', 'points': venus_points})
        sun_venus_gap = self._angular_distance(positions[swe.SUN], positions[karaka_planet])
        if sun_venus_gap < 6:
            defect = 'Venus is combust (within 6° of the Sun).'
            blocking.append(defect); cautions.append(defect)
        else:
            positive = f'Venus is clear of combustion ({sun_venus_gap:.1f}° from the Sun).'
            reasons.append(positive); positives.append(positive)
            score_breakdown.append({'factor': 'Venus free from combustion', 'points': 5})
            score += 5

        if natal_context:
            natal_fourth = natal_context['fourth_sign']
            natal_fourth_lord = natal_context['fourth_lord']
            natal_lord_sign = int(natal_context['positions'][natal_fourth_lord] / 30)
            natal_occupants = [self._planet_name(p) for p, pos in natal_context['positions'].items() if int(pos / 30) == natal_fourth]
            natal_score, natal_label = self._dignity_score(natal_fourth_lord, natal_lord_sign)
            natal_points = round(natal_score * 0.35)
            score += natal_points
            natal_reason = f"Natal 4th house is {self._sign_name(natal_fourth)}; its lord {self._planet_name(natal_fourth_lord)} is in {self._sign_name(natal_lord_sign)} ({natal_label})."
            reasons.append(natal_reason); (positives if natal_score >= 0 else cautions).append(natal_reason)
            score_breakdown.append({'factor': 'Natal 4th-house promise', 'points': natal_points})
            if natal_occupants:
                natal_occupant_reason = f"Natal 4th-house occupants: {', '.join(natal_occupants)}."
                reasons.append(natal_occupant_reason); positives.append(natal_occupant_reason)

        if not cautions:
            cautions.append('No major electional pressure factor was detected in the evaluated rules.')
        return max(0, min(100, int(score))), reasons, blocking, positives, cautions, score_breakdown

    @staticmethod
    def _planet_name(planet):
        return {swe.SUN: 'Sun', swe.MOON: 'Moon', swe.MERCURY: 'Mercury', swe.VENUS: 'Venus',
                swe.MARS: 'Mars', swe.JUPITER: 'Jupiter', swe.SATURN: 'Saturn',
                swe.MEAN_NODE: 'Rahu', MuhuratCalculator.KETU_KEY: 'Ketu'}.get(planet, str(planet))

    def _natal_vehicle_summary(self, context):
        if not context:
            return None
        return {
            'ascendant': self._sign_name(context['asc_sign']),
            'fourth_house': self._sign_name(context['fourth_sign']),
            'fourth_lord': self._planet_name(context['fourth_lord']),
            'natal_moon_sign': self._sign_name(context['moon_sign']),
        }

    def _find_lagnas_detailed(self, date_obj, lat, lon, timezone_str, good_lagnas, planet_positions, choghadiya_data, natal_context=None, karaka_planet=swe.VENUS):
        jd = swe.julday(int(date_obj.year), int(date_obj.month), int(date_obj.day), 12.0)
        geopos = (float(lon), float(lat), 0.0)
        
        rise = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)[1][0]
        setting = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)[1][0]
        
        sunrise_hour = self._jd_to_local_hour(rise, timezone_str)
        sunset_hour = self._jd_to_local_hour(setting, timezone_str)
        
        day_duration = sunset_hour - sunrise_hour
        if day_duration < 0: day_duration += 24 
        
        weekday = date_obj.weekday()
        rahu_map = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7} 
        yama_map = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 5, 6: 6}
        gulika_map = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

        def get_window(idx, is_day=True):
            duration = day_duration if is_day else (24-day_duration)
            start_base = sunrise_hour if is_day else sunset_hour
            one_part = duration / 8
            s = start_base + (idx * one_part)
            return (s, s + one_part)

        rahu = get_window(rahu_map[weekday])
        yama = get_window(yama_map[weekday])
        gulika = get_window(gulika_map[weekday])

        def is_forbidden(t):
            # Check range considering day wrap
            def in_range(val, r): return r[0] <= val < r[1]
            return in_range(t, rahu) or in_range(t, yama) or in_range(t, gulika)
        
        # Find good time slots
        slots = []
        for hour in range(int(sunrise_hour), int(sunset_hour) + 1):
            if is_forbidden(hour): continue
            
            # Calculate lagna for this hour
            tz_offset = parse_timezone_offset(timezone_str, lat, lon, for_date=date_obj.strftime('%Y-%m-%d'))
            jd_hour = swe.julday(date_obj.year, date_obj.month, date_obj.day, hour - tz_offset)
            asc = swe.houses(jd_hour, lat, lon, b'P')[1][0]  # Placidus houses
            lagna_sign = int(asc / 30)
            
            if lagna_sign not in good_lagnas: continue
            
            # Check choghadiya if available (names + clock windows from panchang)
            if choghadiya_data and not self._is_good_choghadiya_hour(float(hour), choghadiya_data):
                continue

            score, reasons, blocking, positives, cautions, score_breakdown = self._evaluate_vehicle_slot(
                jd_hour, lagna_sign, natal_context, karaka_planet
            )
            # Hard electional defects are not softened by a high score.
            if blocking:
                continue

            slots.append({
                'time': self._jd_to_local_time(jd_hour, timezone_str),
                'lagna': ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][lagna_sign],
                'quality': 'Excellent' if score >= 70 else ('Good' if score >= 55 else ('Usable with caution' if score >= 40 else 'Caution only')),
                'score': score,
                'reasons': reasons,
                'positives': positives,
                'cautions': cautions,
                'score_breakdown': score_breakdown,
                'rationale': f"Selected because this slot passed all hard vehicle-Muhurat rules and scored {score}/100 after balancing supportive and cautionary factors.",
            })
        
        return slots
    
    def _jd_to_local_hour(self, jd_val, timezone_str):
        """Convert JD to local hour with timezone handling"""
        if not jd_val: return 0
        year, month, day, hour, minute, second = swe.jdut1_to_utc(jd_val, 1)
        dt_utc = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.UTC)
        
        if timezone_str.startswith('UTC'):
            tz_offset = self._parse_timezone(timezone_str)
            dt_local = dt_utc + timedelta(hours=tz_offset)
        else:
            try:
                tz = pytz.timezone(timezone_str)
                dt_local = dt_utc.astimezone(tz)
            except:
                tz_offset = self._parse_timezone(timezone_str)
                dt_local = dt_utc + timedelta(hours=tz_offset)
        
        return dt_local.hour + dt_local.minute/60.0

    def _clock_to_hours(self, value):
        """Parse HH:MM, HH:MM:SS, or ISO datetime into local fractional hours."""
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        try:
            if 'T' in s:
                dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
                return dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            parts = s.split(':')
            h = float(parts[0])
            m = float(parts[1]) if len(parts) > 1 else 0.0
            sec = float(parts[2]) if len(parts) > 2 else 0.0
            return h + m / 60.0 + sec / 3600.0
        except Exception:
            return None

    def _is_good_choghadiya_hour(self, hour_val, choghadiya_data):
        """True when hour falls inside an auspicious daytime Choghadiya window."""
        if not choghadiya_data:
            return True
        for slot in choghadiya_data.get('day_choghadiya', []) or []:
            if slot.get('name') not in self.GOOD_CHOGHADIYA:
                continue
            start = self._clock_to_hours(slot.get('start_clock') or slot.get('start_time'))
            end = self._clock_to_hours(slot.get('end_clock') or slot.get('end_time'))
            if start is None or end is None:
                continue
            if end < start:
                end += 24.0
            if start <= hour_val < end:
                return True
        return False
