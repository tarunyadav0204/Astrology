"""Festival ritual windows, separate from generic purchase elections.

All intervals are half-open, timezone-aware and solved to one second. This module
never substitutes a civil-calendar date or a synthetic sunrise for ritual rules.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import re
import swisseph as swe
from calculators.chart_calculator import _SWISSEPH_CHART_LOCK
from calculators.verified_muhurat_calculator import julian, sidereal_ascendant, VerifiedMuhuratCalculator
from festivals.festival_data import HINDU_FESTIVALS
from festivals.festival_calculator import FestivalCalculator

ROOT = 'https://www.drikpanchang.com/'
# Deliberately explicit: a festival name alone does not implement all its rites.
PROFILES = {
    'dussehra': ('aparahna', 'Shami / Aparajita puja', 'festivals/vijayadashami/vijayadashami-date-time.html'),
    'ganesh_chaturthi': ('madhyahna', 'Ganesh sthapana and puja', 'festivals/ganesh-chaturthi/ganesh-chaturthi-date-time.html'),
    'ram_navami': ('madhyahna', 'Rama Navami puja', 'dashavatara/rama-navami/rama-navami-date-time.html'),
    'maha_shivratri': ('nishita', 'Nishita Shiva puja', 'festivals/maha-shivaratri/maha-shivaratri-date-time.html'),
    'diwali': ('pradosh_taurus', 'Household Lakshmi puja', 'festivals/lakshmipuja/festivals-lakshmipuja-timings.html'),
    'dhanteras': ('pradosh_taurus', 'Dhanteras puja (not shopping)', 'festivals/dhanteras/festivals-dhanteras-puja-timings.html'),
    'bhai_dooj': ('aparahna', 'Bhai Dooj tika', 'festivals/bhai-dooj/bhai-dooj-date-time.html'),
    'govardhan_puja': ('pratah', 'Govardhan puja', 'festivals/govardhan-puja/govardhan-puja-date-time.html'),
    'vasant_panchami': ('purvahna', 'Saraswati puja', 'festivals/vasant-panchami/vasant-panchami-puja-date-time.html'),
}
ALIASES = {
    'dussehra': ['dusehra', 'dusshera', 'dasara', 'dashera', 'vijayadashami', 'vijaya dashami', 'दशहरा', 'विजयादशमी'],
    'diwali': ['deepavali', 'dipavali', 'lakshmi puja', 'laxmi puja', 'दीवाली', 'दिवाली', 'दीपावली', 'लक्ष्मी पूजा'],
    'ram_navami': ['rama navami', 'ramnavami', 'राम नवमी'],
    'maha_shivratri': ['maha shivaratri', 'mahashivratri', 'shivratri', 'महाशिवरात्रि'],
    'ganesh_chaturthi': ['ganesha chaturthi', 'ganesh chauth', 'गणेश चतुर्थी'],
    'bhai_dooj': ['bhai dooj', 'bhaiya dooj', 'भाई दूज'],
    'govardhan_puja': ['annakut', 'गोवर्धन पूजा'],
    'vasant_panchami': ['basant panchami', 'वसंत पंचमी', 'बसंत पंचमी'],
    'janmashtami': ['krishna janmashtami', 'janmastami', 'जन्माष्टमी'],
    'navratri': ['shardiya navratri', 'नवरात्रि'],
    'dhanteras': ['धनतेरस'],
}
# Accepted names identify the SAME implemented rite. Exact normalized aliases
# avoid both false rejections (Aparajita versus the combined display label) and
# accidental substitution of immersion/parana/Tantrik rites.
RITUAL_ALIASES = {
    'dussehra': ('aparajita puja','aparajita','shami puja','shami','aparajita shami puja','shami aparajita puja','अपराजिता पूजा','शमी पूजा','अपराजिता पूजन','शमी पूजन'),
    'diwali': ('lakshmi puja','laxmi puja','diwali puja','lakshmi ganesh puja','लक्ष्मी पूजा','लक्ष्मी पूजन','दीवाली पूजा','दिवाली पूजा'),
    'dhanteras': ('dhanteras puja','dhantrayodashi puja','धनतेरस पूजा'),
    'ganesh_chaturthi': ('ganesh puja','ganesha puja','ganesh sthapana','ganapati sthapana','गणेश पूजा','गणेश स्थापना'),
    'ram_navami': ('ram navami puja','rama navami puja','ram janma puja','राम नवमी पूजा'),
    'maha_shivratri': ('nishita puja','nishita shiva puja','shivratri puja','maha shivratri puja','निशिता पूजा','महाशिवरात्रि पूजा'),
    'bhai_dooj': ('bhai dooj tika','bhai dooj tilak','bhai dooj puja','भाई दूज टीका','भाई दूज तिलक'),
    'govardhan_puja': ('govardhan puja','annakut puja','गोवर्धन पूजा','अन्नकूट पूजा'),
    'vasant_panchami': ('saraswati puja','vasant panchami puja','basant panchami puja','सरस्वती पूजा'),
}


def _ritual_name(value):
    name = str(value or '').casefold().replace('pooja','puja').replace('poojan','puja').replace('pujan','puja')
    return ' '.join(re.sub(r'[_/\-–—,]+', ' ', name).split())


def supported_ritual(festival, ritual):
    if _ritual_name(ritual) in {'','puja','main puja','पूजा'}: return True
    if festival not in PROFILES: return False
    return _ritual_name(ritual) in {_ritual_name(name) for name in (PROFILES[festival][1], *RITUAL_ALIASES.get(festival,()))}


TITHIS = {name: i + 1 for i, name in enumerate(('pratipada','dvitiya','tritiya','chaturthi','panchami','shashthi','saptami','ashtami','navami','dashami','ekadashi','dvadashi','trayodashi','chaturdashi','purnima'))}
TITHIS['amavasya'] = 15


def resolve_festival(value):
    text = re.sub(r'[_\-]+', ' ', str(value or '').lower()).strip()
    matches = []
    for key, item in HINDU_FESTIVALS.items():
        names = [key.replace('_', ' '), item['name'].lower(), *ALIASES.get(key, [])]
        for name in names:
            for match in re.finditer(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text):
                matches.append((key, match.start(), match.end()))
    # A specific name wins over its contained generic alias, but two separate
    # festivals require selection rather than arbitrary string-length priority.
    keys = {key for key, a, b in matches if not any(
        other != key and c <= a and d >= b and d-c > b-a for other, c, d in matches)}
    return next(iter(keys)) if len(keys) == 1 else None


def coverage_catalog():
    catalog = []
    for key, item in HINDU_FESTIVALS.items():
        options = []
        if key == 'dussehra':
            options = [
                {'value':'Aparajita puja','label':'Aparajita Puja','aliases':['Aparajita','अपराजिता पूजा','अपराजिता पूजन'],'supported':True},
                {'value':'Shami puja','label':'Shami Puja','aliases':['Shami','शमी पूजा','शमी पूजन'],'supported':True},
                {'value':PROFILES[key][1],'label':'Shami and Aparajita Puja','aliases':['Aparajita/Shami puja'],'supported':True},
                {'value':'Exact Vijaya Muhurat','label':'Exact Vijaya Muhurat','aliases':[],'supported':False},
                {'value':'Durga Visarjan','label':'Durga Visarjan','aliases':[],'supported':False},
            ]
        elif key in PROFILES:
            options = [{'value':PROFILES[key][1],'label':{'diwali':'Lakshmi Puja','dhanteras':'Dhanteras Puja','ganesh_chaturthi':'Ganesh Sthapana and Puja','ram_navami':'Ram Navami Puja','maha_shivratri':'Shivratri Nishita Puja','bhai_dooj':'Bhai Dooj Tilak','govardhan_puja':'Govardhan Puja','vasant_panchami':'Saraswati Puja'}.get(key,PROFILES[key][1]),
                'aliases':list(RITUAL_ALIASES.get(key, ())), 'supported':True}]
        catalog.append({'id':key, 'name':item['name'],
            'coverage':'ritual_window' if key in PROFILES else 'panchang_only',
            'ritual':PROFILES[key][1] if key in PROFILES else None,
            'source':ROOT+PROFILES[key][2] if key in PROFILES else None,
            'ritual_options':options})
    return catalog


def _dt(jd):
    return datetime.fromtimestamp((jd - 2440587.5) * 86400, timezone.utc)


def _state(jd):
    sun = swe.calc_ut(jd, swe.SUN)[0][0]
    moon = swe.calc_ut(jd, swe.MOON)[0][0]
    return int(((moon - sun) % 360) / 12) + 1


def _boundary(lo, hi, state, evaluate=_state):
    while (hi - lo) * 86400 > 0.25:
        mid = (lo + hi) / 2
        if evaluate(mid) == state: lo = mid
        else: hi = mid
    return hi


def _runs(start, end, evaluate, step=1/24):
    """Find state runs; step must be shorter than any possible state duration."""
    left = cursor = start
    state = evaluate(cursor)
    while cursor < end:
        nxt = min(cursor + step, end)
        new = evaluate(nxt)
        if new != state:
            edge = _boundary(cursor, nxt, state, evaluate)
            yield left, edge, state
            left, state = edge, new
        cursor = nxt
    if end > left: yield left, end, state


def _solar(day, place, zone, setting=False):
    midnight = datetime.combine(day, time(), zone)
    result, values = swe.rise_trans(julian(midnight), swe.SUN,
        (swe.CALC_SET if setting else swe.CALC_RISE),
        (float(place['longitude']), float(place['latitude']), 0))
    if result != 0: raise ValueError('Sunrise/sunset is unavailable at this location')
    moment = _dt(values[0])
    if moment.astimezone(zone).date() != day: raise ValueError('Solar event outside local civil date')
    return values[0]


def _ritual_period(kind, day, place, zone):
    rise = _solar(day, place, zone)
    setting = _solar(day, place, zone, True)
    daylight = setting - rise
    if kind == 'madhyahna': return rise + daylight*2/5, rise + daylight*3/5
    if kind == 'aparahna': return rise + daylight*3/5, rise + daylight*4/5
    if kind == 'pratah': return rise, rise + daylight/5
    if kind == 'purvahna': return rise, rise + daylight/2
    next_rise = _solar(day + timedelta(days=1), place, zone)
    night = next_rise - setting
    if kind == 'nishita': return setting + night*7/15, setting + night*8/15
    if kind == 'pradosh_taurus': return setting, setting + night/5
    raise ValueError('Unknown ritual period')


def rahu_kaal_overlay(start, end, place, zone):
    """Preserve the festival rule window; separately calculate Rahu-avoiding portions.

    This is an explicit daytime avoidance convention, not a claim that every
    tradition cancels a festival's prescribed period when Rahu Kaal overlaps.
    """
    from calculators.muhurat_calculator import RAHU_SEGMENTS
    intervals = []; overlaps = []; outside = [(start, end)]
    day = start.date()
    while day <= end.date():
        rise = _solar(day, place, zone)
        setting = _solar(day, place, zone, True)
        eighth = (setting - rise) / 8
        index = RAHU_SEGMENTS[day.weekday()]
        a = _dt(rise + index*eighth).astimezone(zone)
        b = _dt(rise + (index+1)*eighth).astimezone(zone)
        intervals.append({'start':a.isoformat(timespec='seconds'), 'end':b.isoformat(timespec='seconds')})
        lo, hi = max(start, a), min(end, b)
        if hi > lo:
            overlaps.append({'start':lo.isoformat(timespec='seconds'), 'end':hi.isoformat(timespec='seconds')})
            remainder = []
            for x, y in outside:
                if b <= x or a >= y: remainder.append((x,y)); continue
                if x < a: remainder.append((x,min(a,y)))
                if b < y: remainder.append((max(b,x),y))
            outside = remainder
        day += timedelta(days=1)
    practical = []
    for a, b in outside:
        # User-facing minutes must stay inside the calculated portion, never
        # round a start earlier or an end later across an exclusion boundary.
        first = a.replace(second=0, microsecond=0)
        if first < a: first += timedelta(minutes=1)
        last = b.replace(second=0, microsecond=0)
        if last > first:
            practical.append({'start':first.isoformat(timespec='minutes'),
                'end':last.isoformat(timespec='minutes'), 'timezone':str(zone)})
    return {'status':'calculated', 'convention':'Daytime Rahu Kaal; sunrise-to-sunset weekday eighth',
        'practical_windows':practical, 'practical_precision':'Whole minutes rounded inward',
        'intervals':intervals, 'overlaps_ritual_window':bool(overlaps), 'overlaps':overlaps,
        'windows_outside_rahu_kaal':[{'start':a.isoformat(timespec='seconds'), 'end':b.isoformat(timespec='seconds'),
            'timezone':str(zone)} for a,b in outside if b > a],
        'guidance':'For Rahu Kaal avoidance, prefer the listed non-overlapping portions and allow time for the ritual. These are not a complete kundli election or a universal override of festival-specific tradition.'}


class VerifiedFestivalCalculator:
    def search(self, request, birth=None):
        with _SWISSEPH_CHART_LOCK:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            return self._search(request, birth)

    def _search(self, request, birth):
        festival = request.get('festival_id') or resolve_festival(request.get('event_type'))
        if festival not in HINDU_FESTIVALS: raise ValueError('Select a known festival')
        spec = HINDU_FESTIVALS[festival]
        start, end = date.fromisoformat(request['start_date']), date.fromisoformat(request['end_date'])
        if end < start or (end - start).days > 365: raise ValueError('Select at most one year')
        place = request['location']; zone = ZoneInfo(place['timezone'])
        profile = PROFILES.get(festival)
        coverage_reason = None if profile else 'No implemented ritual profile for this festival.'
        tradition = _ritual_name(request.get('tradition'))
        if tradition and tradition not in ('general household', 'household', 'smarta'):
            profile = None
            coverage_reason = 'The explicitly requested tradition has no implemented rule profile.'
        requested_ritual = request.get('ritual')
        if not supported_ritual(festival, requested_ritual):
            profile = None
            coverage_reason = 'The explicitly requested ritual has no implemented rule profile; the main puja is not substituted.'
        target = TITHIS.get(spec.get('lunar_day'))
        if target and spec.get('paksha') == 'krishna': target += 15
        if festival == 'sankashti_chaturthi': target = 19
        # Do not infer lunar dates for solar, regional, multi-day or nakshatra festivals.
        result = {'status': 'partial', 'workflow': 'festival_puja', 'festival_id': festival, 'festival': spec['name'],
            'rule_version': 'festival-puja-v2', 'solar_convention': 'Apparent upper limb, standard refraction, sea-level horizon', 'search': request, 'candidates': [], 'tithi_intervals': [],
            'coverage': 'ritual_window' if profile else 'panchang_only',
            'coverage_reason':coverage_reason, 'requested_ritual':requested_ritual,
            'ritual': profile[1] if profile else requested_ritual, 'tradition': request.get('tradition') or 'General household ritual profile',
            'sources': [ROOT + profile[2]] if profile else [], 'errors': [],
            'limitations': ['Not a complete religious calendar: local traditions and temple observances can differ.',
                'Fasting, parana, immersion and other rites are not inferred from the main puja window.']}
        if not target:
            result['limitation'] = 'This regional, solar or multi-day observance requires a specific ritual/date rule. No verified date or puja window is claimed.'
            return result
        left = julian(datetime.combine(start - timedelta(days=2), time(), zone))
        right = julian(datetime.combine(end + timedelta(days=3), time(), zone))
        calendar = FestivalCalculator()
        matched = []
        for a, b, state in _runs(left, right, _state, step=0.25):
            if state != target: continue
            month, adhika = calendar.get_lunar_month_with_adhika((a+b)/2)
            if spec.get('month') != 'all' and (month != spec.get('month') or adhika): continue
            if _dt(b).astimezone(zone).date() < start or _dt(a).astimezone(zone).date() > end: continue
            result['tithi_intervals'].append({'start': _dt(a).astimezone(zone).isoformat(timespec='seconds'),
                'end': _dt(b).astimezone(zone).isoformat(timespec='seconds'), 'tithi': target, 'month': month,
                'meaning': 'Astronomical tithi interval, not an established observance date or ritual window'})
            if not profile: continue
            possibilities = []
            day = _dt(a).astimezone(zone).date() - timedelta(days=1)
            while day <= _dt(b).astimezone(zone).date():
                try:
                    p, q = _ritual_period(profile[0], day, place, zone)
                    lo, hi = max(a, p), min(b, q)
                    if hi > lo: possibilities.append((day, lo, hi))
                except (ValueError, swe.Error):
                    result['errors'].append({'date': day.isoformat(), 'reason': 'Local solar timing unavailable'})
                day += timedelta(days=1)
            if len(possibilities) > 1 and festival == 'dussehra':
                # Resolve only the strong, sourced case: Dashami covers the entire
                # Aparahna and Shravana also prevails there on exactly one day.
                preferred = []
                for candidate in possibilities:
                    day, lo, hi = candidate
                    p, q = _ritual_period(profile[0], day, place, zone)
                    nakshatras = [state for _, _, state in _runs(p, q,
                        lambda jd: int(swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]/(360/27)), step=1/24)]
                    if a <= p and b >= q and 21 in nakshatras:
                        preferred.append(candidate)
                if len(preferred) == 1:
                    possibilities = preferred
                    result['date_rule'] = 'Full Aparahna Dashami with Shravana; other two-day combinations require confirmation'
                    result['sources'].append('https://news.drikpanchang.com/2013/10/vijayadashami-on-october-13th-or-14th.html')
            if len(possibilities) > 1:
                result['limitations'].append('Tithi overlaps the ritual period on two dates; observance-date priority needs tradition-specific confirmation. Neither date is recommended automatically.')
                continue
            matched.extend(possibilities)
        cutoff = datetime.fromisoformat(request['not_before_utc']) if request.get('not_before_utc') else None
        natal = VerifiedMuhuratCalculator()._build_natal_context(birth) if request.get('personalized') else None
        for day, a, b in matched:
            if not start <= day <= end: continue
            intervals = [(a, b)]
            if profile[0] == 'pradosh_taurus':
                try:
                    intervals = [(lo, hi) for lo, hi, sign in _runs(a, b,
                        lambda jd: int(sidereal_ascendant(jd, place['latitude'], place['longitude']) / 30), step=1/1440) if sign == 1]
                except (ValueError, swe.Error):
                    result['errors'].append({'date':day.isoformat(), 'reason':'Lagna calculation unavailable'})
                    continue
            for lo, hi in intervals:
                local_start, local_end = _dt(lo).astimezone(zone), _dt(hi).astimezone(zone)
                if cutoff and local_end <= cutoff: continue
                if cutoff and local_start < cutoff: local_start = cutoff.astimezone(zone)
                # Availability may restrict a ritual, but can never move it to another time/date.
                if request.get('weekdays') and day.weekday() not in request['weekdays']: continue
                if day.isoformat() in request.get('excluded_dates', []): continue
                available_start = datetime.combine(local_start.date(), time.fromisoformat(request.get('allowed_start', '00:00')), zone)
                available_end = datetime.combine(local_start.date(), time.fromisoformat(request.get('allowed_end', '23:59')), zone)
                if available_end.time() == time(23,59): available_end += timedelta(minutes=1)
                if (request.get('allowed_start', '00:00'), request.get('allowed_end', '23:59')) != ('00:00', '23:59'):
                    local_start, local_end = max(local_start, available_start), min(local_end, available_end)
                if (local_end-local_start).total_seconds() < request.get('minimum_duration_minutes', 15)*60: continue
                if request.get('check_time'):
                    check = datetime.combine(day, time.fromisoformat(request['check_time']), zone)
                    if not local_start <= check < local_end: continue
                evidence = []
                if natal:
                    moon = swe.calc_ut(julian(local_start + (local_end-local_start)/2), swe.MOON, swe.FLG_SIDEREAL)[0][0]
                    natal_moon = natal['positions'][swe.MOON]
                    tara = (int(moon/(360/27))-int(natal_moon/(360/27)))%27%9+1
                    chandra = (int(moon/30)-int(natal_moon/30))%12+1
                    evidence = [{'method': 'Midpoint Moon comparison only', 'at': (local_start+(local_end-local_start)/2).isoformat(),
                        'tara_number': tara, 'tara_supportive': tara in (2,4,6,8,9),
                        'moon_house_from_natal_moon': chandra, 'chandra_supportive': chandra in (1,3,6,7,10,11),
                        'limitation': 'A snapshot, not continuous suitability across the interval or a complete kundli election.'}]
                try:
                    rahu = rahu_kaal_overlay(local_start, local_end, place, zone)
                    if request.get('check_time'):
                        rahu['checked_time'] = {'at':check.isoformat(timespec='seconds'),
                            'within_rahu_kaal':any(datetime.fromisoformat(i['start']) <= check < datetime.fromisoformat(i['end']) for i in rahu['intervals'])}
                except (ValueError, swe.Error):
                    rahu = {'status':'unavailable', 'windows_outside_rahu_kaal':[],
                        'guidance':'Rahu Kaal could not be assessed. Do not claim avoidance or invent an alternative time.'}
                    result['limitations'].append('Daytime Rahu Kaal coverage is unavailable for a ritual window.')
                result['candidates'].append({'date': day.isoformat(), 'start': local_start.isoformat(timespec='seconds'),
                    'end': local_end.isoformat(timespec='seconds'), 'timezone': place['timezone'], 'ritual': profile[1],
                    'basis': profile[0] + ' intersected with required tithi' + (' and Taurus Lagna' if profile[0]=='pradosh_taurus' else ''),
                    'personal_checks': evidence, 'rahu_kaal':rahu})
        if request.get('personalized') and not natal: result['limitations'].append('Natal Moon comparison unavailable; these are general ritual windows.')
        result['status'] = 'completed' if profile and not result['errors'] and not any('two dates' in x for x in result['limitations']) else 'partial'
        if any(w.get('rahu_kaal',{}).get('status') == 'calculated' for w in result['candidates']):
            result['sources'].append('https://www.drikpanchang.com/panchang/rahu-kaal.html')
        result['total_candidates'] = len(result['candidates'])
        result['result_meaning'] = 'Calculated ritual windows' if result['candidates'] else 'No recommendable ritual window in the selected period; inspect coverage and tithi information. This is not proof that no festival is observed.'
        if not profile: result['limitation'] = str(coverage_reason or '') + ' Only lunar tithi information is calculated. Ritual-specific exclusions, date priority and tradition rules are not yet verified; do not turn these intervals into a puja recommendation.'
        return result
