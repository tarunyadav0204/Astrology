"""Opt-in sidereal, minute-grid elections. Legacy planner/API contracts stay unchanged."""
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import swisseph as swe
from calculators.chart_calculator import _SWISSEPH_CHART_LOCK
from calculators.muhurat_calculator import MuhuratCalculator, RAHU_SEGMENTS, YAMAGANDA_SEGMENTS, GULIKA_SEGMENTS

SUPPORTED_EVENTS = {'vehicle', 'home', 'gold', 'business'}
POLICIES = {
    'vehicle': ('VEHICLE_NAKSHATRAS', [0,3,6,9], [1], 'Vehicle Purchase', True, swe.VENUS),
    'home': ('HOME_NAKSHATRAS', [1,4,7,10], [1,6], 'Griha Pravesh', True, swe.MARS),
    'gold': ('GOLD_NAKSHATRAS', [1,2,3,4,5,6,8,11], [1], 'Gold Purchase', False, None),
    'business': ('BUSINESS_NAKSHATRAS', [1,4,7,10], [1,6], 'Business Opening', False, None),
}


def julian(dt):
    utc = dt.astimezone(timezone.utc)
    return swe.julday(utc.year, utc.month, utc.day, utc.hour+utc.minute/60+utc.second/3600)


def sidereal_ascendant(jd, latitude, longitude):
    return float(swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)[1][0]) % 360


class VerifiedMuhuratCalculator(MuhuratCalculator):
    def __init__(self):
        with _SWISSEPH_CHART_LOCK:
            super().__init__()

    def _build_natal_context(self, birth_data):
        if not birth_data: return None
        from utils.timezone_service import parse_timezone_offset
        try:
            date_value = str(birth_data.get('date') or birth_data.get('user_dob')).split('T')[0]
            time_value = birth_data.get('time') or birth_data.get('user_time')
            if not time_value: return None
            latitude = float(birth_data.get('latitude',birth_data.get('user_lat')))
            longitude = float(birth_data.get('longitude',birth_data.get('user_lon')))
            local = datetime.fromisoformat(date_value+'T'+str(time_value))
            offset = parse_timezone_offset(birth_data.get('timezone') or birth_data.get('user_timezone') or '',latitude,longitude,for_date=date_value)
            utc = (local.replace(tzinfo=None)-timedelta(hours=offset)).replace(tzinfo=timezone.utc)
            jd = julian(utc)
            positions = self._sidereal_positions(jd)
            asc_sign = int(sidereal_ascendant(jd,latitude,longitude)/30)
            return {'asc_sign':asc_sign,'fourth_sign':(asc_sign+3)%12,
                'fourth_lord':self._sign_lord((asc_sign+3)%12),'moon_sign':int(positions[swe.MOON]/30),
                'positions':positions,'birth_jd':jd}
        except (ValueError,TypeError,KeyError):
            return None

    def search(self, request, birth_data=None):
        with _SWISSEPH_CHART_LOCK:
            try:
                swe.set_sid_mode(swe.SIDM_LAHIRI)
                return self._search(request, birth_data)
            finally:
                swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _search(self, request, birth_data):
        event = request['event_type']
        if event not in SUPPORTED_EVENTS:
            return {'status':'unsupported', 'event_type':event, 'candidates':[],
                    'limitation':'A complete activity-specific rule engine is not available for this activity. Fixed daytime segments are not a complete Muhurat.'}
        start, end = date.fromisoformat(request['start_date']), date.fromisoformat(request['end_date'])
        if end < start or (end-start).days >= 60:
            raise ValueError('Select an inclusive search period of 1–60 days')
        place=request['location']; zone=ZoneInfo(place['timezone'])
        lat,lon=place['latitude'],place['longitude']
        minimum=int(request.get('minimum_duration_minutes',15))
        if not 5 <= minimum <= 120: raise ValueError('Minimum duration must be 5–120 minutes')
        nak_attr,lagnas,avoid_days,label,fourth,karaka=POLICIES[event]
        natal=self._build_natal_context(birth_data) if birth_data and request.get('personalized',True) else None
        user_nak=int(natal['positions'][swe.MOON]/(360/27))+1 if natal else None
        candidates=[]; rejected=Counter(); errors=[]; scanned=0; solar_days=[]
        allowed_start=time.fromisoformat(request.get('allowed_start') or '00:00')
        allowed_end=time.fromisoformat(request.get('allowed_end') or '23:59')
        if allowed_end <= allowed_start: raise ValueError('Available end time must follow start time on the same day')
        check_time=time.fromisoformat(request['check_time']) if request.get('check_time') else None
        cutoff=datetime.fromisoformat(request['not_before_utc']).astimezone(zone) if request.get('not_before_utc') else None
        day=start
        while day<=end:
            if cutoff and day<cutoff.date():
                rejected['elapsed_date']+=1; day+=timedelta(days=1); continue
            if request.get('weekdays') and day.weekday() not in request['weekdays'] or day.isoformat() in request.get('excluded_dates',[]):
                rejected['user_availability']+=1; day+=timedelta(days=1); continue
            if day.weekday() in avoid_days:
                rejected['activity_weekday_policy']+=1; day+=timedelta(days=1); continue
            try:
                solar=self.panchang_calc.get_local_sunrise_sunset(day.isoformat(),lat,lon,place['timezone'])
                sunrise=datetime.fromisoformat(solar['sunrise']).replace(tzinfo=zone)
                sunset=datetime.fromisoformat(solar['sunset']).replace(tzinfo=zone)
                if sunrise.date()!=day or sunset<=sunrise: raise ValueError('Invalid solar-day coverage')
                eight=(sunset-sunrise)/8
                weekday=day.weekday()
                forbidden=[(sunrise+idx*eight,sunrise+(idx+1)*eight) for idx in
                    (RAHU_SEGMENTS[weekday], YAMAGANDA_SEGMENTS[weekday], GULIKA_SEGMENTS[weekday])]
                chog=self.panchang_calc.calculate_choghadiya(day.isoformat(),lat,lon,place['timezone'])
                if not chog.get('day_choghadiya'): raise ValueError('Choghadiya coverage unavailable')
                solar_days.append({'date':day.isoformat(),'sunrise':sunrise.isoformat(),'sunset':sunset.isoformat(),
                    'excluded_periods':[{'name':name,'start_time':a.isoformat(),'end_time':b.isoformat()} for name,(a,b) in zip(('Rahu Kaal','Yamaganda','Gulika'),forbidden)],
                    'day_choghadiya':chog['day_choghadiya']})
                begin=max(sunrise,datetime.combine(day,allowed_start,zone))
                finish=min(sunset,datetime.combine(day,allowed_end,zone))
                if check_time:
                    begin=datetime.combine(day,check_time,zone); finish=begin+timedelta(minutes=minimum)
                    if begin<sunrise or finish>sunset or begin.time()<allowed_start or finish.time()>allowed_end:
                        rejected['outside_daylight_or_availability']+=1; day+=timedelta(days=1); continue
                if cutoff:
                    if check_time and begin<cutoff:
                        rejected['elapsed_fixed_time']+=1; day+=timedelta(days=1); continue
                    begin=max(begin,cutoff)
                # Conservative whole-minute cells; do not round a candidate across an exclusion boundary.
                cursor=begin.replace(second=0,microsecond=0)
                if cursor<begin: cursor+=timedelta(minutes=1)
                run=None
                while cursor+timedelta(minutes=1)<=finish:
                    endpoint=cursor+timedelta(minutes=1)
                    reason=None; evaluated=None
                    if any(cursor<e and endpoint>s for s,e in forbidden): reason='rahu_yamaganda_gulika'
                    for sample in (cursor, cursor+timedelta(seconds=30), endpoint):
                        if reason: break
                        jd=julian(sample); positions=self._sidereal_positions(jd)
                        sun,moon=positions[swe.SUN],positions[swe.MOON]
                        tithi=int(((moon-sun)%360)/12)+1; nak=int(moon/(360/27))+1
                        yoga=int(((moon+sun)%360)/(360/27))+1
                        half=int(((moon-sun)%360)/6)+1
                        vishti=2<=half<=57 and (half-2)%7==6
                        tara=((nak-user_nak)%27)%9+1 if user_nak else None
                        asc=int(sidereal_ascendant(jd,lat,lon)/30)
                        if moon>=300: reason='panchak_policy'
                        elif (tithi-1)%15+1 in {4,9,14} or tithi==30: reason='tithi_policy'
                        elif yoga in self.AVOID_YOGAS: reason='yoga_policy'
                        elif vishti: reason='vishti_karana'
                        elif nak not in getattr(self,nak_attr): reason='activity_nakshatra_policy'
                        elif tara in {1,3,5,7}: reason='tara_bala'
                        elif asc not in lagnas: reason='activity_lagna_policy'
                        elif not any(slot['name'] in self.GOOD_CHOGHADIYA
                            and datetime.fromisoformat(slot['start_time']).replace(tzinfo=zone)<=sample
                            <datetime.fromisoformat(slot['end_time']).replace(tzinfo=zone) for slot in chog['day_choghadiya']): reason='choghadiya_policy'
                        if reason: break
                        if event=='vehicle':
                            score,reasons,blocking,positives,cautions,breakdown=self._evaluate_vehicle_slot(jd,asc,natal,karaka)
                        else:
                            score,reasons,blocking,positives,cautions,breakdown=self._evaluate_generic_slot(jd,asc,label,fourth,karaka)
                        if blocking: reason='activity_chart_defect'; break
                        evaluated={'score':score,'reasons':reasons,'cautions':cautions,'lagna':self._sign_name(asc),
                                   'panchang':{'tithi_number':tithi,'nakshatra_number':nak,'yoga_number':yoga,'karana_half':half,'tara_number':tara}}
                    if reason:
                        rejected[reason]+=1
                        if run:
                            if (run['end_time']-run['start_time']).total_seconds()/60>=minimum: candidates.append(run)
                            run=None
                    elif run and run['lagna']==evaluated['lagna'] and run['panchang']==evaluated['panchang']:
                        run['end_time']=endpoint
                        run['cautions']=list(dict.fromkeys(run['cautions']+evaluated['cautions']))
                        if evaluated['score']<run['score']:
                            run['score']=evaluated['score']; run['reasons']=evaluated['reasons']
                    else:
                        if run and (run['end_time']-run['start_time']).total_seconds()/60>=minimum: candidates.append(run)
                        run={**evaluated,'date':day.isoformat(),'start_time':cursor,'end_time':endpoint}
                    cursor=endpoint
                if run and (run['end_time']-run['start_time']).total_seconds()/60>=minimum: candidates.append(run)
                scanned+=1
            except (ValueError,RuntimeError,swe.Error) as exc:
                errors.append({'date':day.isoformat(),'reason':str(exc)[:150]})
            day+=timedelta(days=1)
        candidates.sort(key=lambda row:(-row['score'],row['start_time']))
        total=len(candidates)
        for row in candidates:
            row['duration_minutes']=int((row['end_time']-row['start_time']).total_seconds()/60)
            row['start_time']=row['start_time'].isoformat(); row['end_time']=row['end_time'].isoformat()
        return {'status':'partial' if errors else 'completed',
            'result_meaning':'incomplete_date_coverage' if errors else 'matching_windows_found' if candidates else 'search_completed_no_matching_windows',
            'profile':'verified_muhurat_lahiri_minute_grid_v1',
            'search':request,'event_type':event,'location':place,'candidates':candidates[:8],
            'solar_days':solar_days,'requested_personalization':bool(request.get('personalized')),'personalization_available':bool(natal),
            'total_candidates':total,'candidate_limit':8,'days_evaluated':scanned,'rejection_counts':dict(rejected),'errors':errors,
            'personalization':'natal vehicle context and Tara Bala' if natal and event=='vehicle' else 'Tara Bala' if natal else 'general Panchang/activity rules',
            'limitations':['Daylight search only.', 'Conservative one-minute grid, with endpoint and midpoint checks; not an exact transition solver.',
                'Activity policies are the existing app rule set, not a complete certification of every classical Muhurat doctrine.',
                'Scores rank evaluated factors and are not success probabilities.']}
