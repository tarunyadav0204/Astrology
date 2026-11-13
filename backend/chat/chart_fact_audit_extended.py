"""Calculator adapters for typed natal, KP, Jaimini, AV and dated claims."""
from datetime import datetime, timezone
import re
from calculators.base_calculator import BaseCalculator as B

TYPES = {'dignity', 'nakshatra', 'jaimini_role', 'karakamsha_sign', 'karakamsha_house',
         'house_occupants', 'alignment', 'chara_dasha', 'transit_end_date', 'kp_cusp_lords', 'kp_cusp_sub_lord', 'kp_significator_houses',
         'kp_significator_chain', 'sav', 'bav', 'dasha_period'}
FRAMES = {'Karakamsha', 'Karkamsha', 'Karkamsa', 'karakamsha'}


def handles(c):
    return (c.get('claim_type') in TYPES or (c.get('reference_frame') in FRAMES or c.get('reference_frame') == 'sign')
            or c.get('chart_scope') == 'transit')


class Unverified(ValueError):
    pass


def audit_extended(c, subject, cache, as_of):
    """Returns calculated value, evidence path and equality for one typed claim."""
    from chat.chart_fact_audit import calculate_subject
    from calculators.chara_karaka_calculator import CharaKarakaCalculator
    from calculators.jaimini_point_calculator import JaiminiPointCalculator
    from calculators.divisional_chart_calculator import DivisionalChartCalculator
    kind, planet, house, value = (c.get(k) for k in ('claim_type','planet','house','asserted_value'))
    code, frame = c.get('chart'), c.get('reference_frame')
    if c.get('chart_scope') not in {'natal', 'transit'}:
        raise Unverified('Unresolved natal/transit scope')
    if frame in FRAMES and code != 'D1':
        raise Unverified('Karakamsha adapter requires explicit D1 positions')
    if c.get('chart_scope') == 'transit' and kind != 'transit_end_date' and (c.get('temporal_scope') != 'current' or kind not in {'planet_sign','planet_house'}):
        raise Unverified('Only explicit current transit position supported; future intervals require an ingress adapter')
    if kind == 'dasha_period' and c.get('temporal_scope') != 'current':
        raise Unverified('Current-period adapter requires explicit current dasha scope')
    def memo(key, fn):
        if key not in cache: cache[key] = fn()
        return cache[key]
    charts = memo('charts', lambda: calculate_subject(subject, {1,9,10}))
    d1 = charts['D1']; asc = int(d1['ascendant']/30)%12
    birth = subject['birth']
    def chart():
        if not isinstance(code,str) or not re.fullmatch(r'D\d+', code): raise Unverified('Chart unresolved')
        from chat.chart_fact_audit import DIVISIONS
        n=int(code[1:])
        if n not in DIVISIONS: raise Unverified('Divisional chart not supported')
        if code not in charts: charts.update(calculate_subject(subject,{n}))
        return charts[code]
    def h():
        if type(house) is not int or not 1 <= house <= 12: raise Unverified('House must be 1..12')
        return house
    def karakas():
        return memo('karakas',lambda:CharaKarakaCalculator(d1).calculate_chara_karakas()['chara_karakas'])
    def kl():
        points=memo('jaimini_points',lambda:JaiminiPointCalculator(d1,charts['D9'],karakas()['Atmakaraka']['planet']).calculate_jaimini_points())
        return points['karkamsa_lagna']['sign_id']
    def dt():
        if not as_of: raise Unverified('Original question timestamp unavailable')
        parsed=datetime.fromisoformat(as_of.replace('Z','+00:00'))
        return parsed.astimezone(timezone.utc).replace(tzinfo=None) if parsed.tzinfo else parsed
    def subset(actual):
        if not isinstance(value,list) or not value: raise Unverified('Nonempty asserted list required')
        if c.get('comparison') not in ('contains','equals'): raise Unverified('List completeness not specified')
        return set(value).issubset(actual) if c['comparison']=='contains' else set(value)==set(actual)
    path=kind
    if kind=='transit_end_date':
        from calculators.real_transit_calculator import RealTransitCalculator
        from datetime import timedelta
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z]+ \d{4}',value): raise Unverified('Transit exit adapter requires a month and year')
        rtc=RealTransitCalculator(**subject['settings']); start=dt()
        initial=int(rtc.get_planet_position(start,planet)/30)%12
        end=None
        for days in range(1,1101):
            date=start+timedelta(days=days)
            if int(rtc.get_planet_position(date,planet)/30)%12 != initial:
                end=date; break
        if end is None: raise Unverified('No sign exit in three-year search horizon')
        cache.setdefault('transit_exits',{})[planet]={'first_changed_day':end.isoformat(),'precision':'daily sampling; month comparison only'}
        actual=end.strftime('%B %Y'); path=f'transits.{planet}.next_sign_exit_month'
    elif c.get('chart_scope')=='transit':
        if c.get('temporal_scope')!='current' or (kind=='planet_house' and (frame!='ascendant' or code!='D1')):
            raise Unverified('Transit claim needs explicit current time and D1 ascendant frame; future intervals require an ingress adapter')
        if kind not in {'planet_sign','planet_house'}: raise Unverified('Transit claim type unsupported')
        from calculators.real_transit_calculator import RealTransitCalculator
        pos=RealTransitCalculator(**subject['settings']).get_planet_position(dt(),planet)
        if pos is None: raise Unverified('Transit planet unavailable')
        sign=int(pos/30)%12
        actual=B.SIGN_NAMES[sign] if kind=='planet_sign' else (sign-asc)%12+1
        path=f'transits.{as_of}.{planet}.{kind}'
    elif kind.startswith('kp_'):
        from app.kp.services.chart_service import KPChartService
        from calculators.chart_calculator import _SWISSEPH_CHART_LOCK
        def kp_calc():
            with _SWISSEPH_CHART_LOCK:
                return KPChartService.calculate_kp_chart(birth['date'],birth['time'],birth['latitude'],birth['longitude'],birth['timezone'])
        kp=memo('kp',kp_calc)
        path=f'kp.{kind}.{house or planet}'
        if kind in {'kp_cusp_lords','kp_cusp_sub_lord'}:
            row=kp['cusp_lords'].get(h()) or kp['cusp_lords'].get(str(h()))
            if kind=='kp_cusp_sub_lord': actual=row['sub_lord']
            else:
                if not isinstance(value,dict) or not value or not set(value)<=set(row): raise Unverified('Invalid cusp lord fields')
                actual={k:row[k] for k in value}
        elif kind=='kp_significator_chain':
            row=kp['four_step_theory'][planet]
            actual=[row[k]['name'] for k in ('star_lord','sub_lord','sub_sub_lord')]
        else:
            basis=c.get('significator_basis')
            if basis=='four_step_union':
                actual=sorted({h for row in kp['four_step_theory'][planet].values() for h in row['houses']})
            elif basis=='planet_significators': actual=kp['planet_significators'][planet]
            else:
                direct=kp['planet_significators'][planet]
                union=sorted({h for row in kp['four_step_theory'][planet].values() for h in row['houses']})
                if subset(direct) and subset(union):
                    return {'planet_significators':direct,'four_step_union':union},path+'.both_bases',True
                raise Unverified('KP significator basis unresolved; candidate bases do not both support the claim')
            return actual,path+'.'+basis,subset(actual)
    elif kind=='dignity':
        ch=chart(); sign=int(ch['planets'][planet]['longitude']/30)%12
        v=str(value).lower().replace(' ','_')
        actual=DivisionalChartCalculator(d1)._calculate_divisional_dignity(planet,sign)['dignity']
        # Own-sign is a property even when a calculator prioritizes moolatrikona.
        if v in {'own_sign','own'}:
            actual='own_sign' if B.SIGN_LORDS[sign]==planet else actual
            v='own_sign'
        return actual,f'{code}.planets.{planet}.dignity',actual==v
    elif kind=='nakshatra':
        if code!='D1': raise Unverified('Only natal D1 nakshatra supported')
        from calculators.nakshatra_calculator import NakshatraCalculator
        row= memo('nakshatras',lambda:NakshatraCalculator(chart_data=d1).calculate_nakshatra_positions())[planet]
        if isinstance(value,str): actual=row['nakshatra_name']
        elif isinstance(value,dict) and value and set(value)<={'nakshatra','pada'}:
            actual={k:row['nakshatra_name' if k=='nakshatra' else 'pada'] for k in value}
        else: raise Unverified('Invalid nakshatra claim fields')
        path=f'D1.planets.{planet}.nakshatra'
    elif kind=='alignment':
        if value!='Arudha Lagna' or code!='D1': raise Unverified('Only explicit natal Arudha same-sign alignment supported')
        kl()
        target=cache['jaimini_points']['arudha_lagna']['sign_id']
        actual=B.SIGN_NAMES[int(d1['planets'][planet]['longitude']/30)%12]
        return {'planet_sign':actual,'arudha_sign':B.SIGN_NAMES[target]},f'D1.{planet}.alignment.arudha_lagna',actual==B.SIGN_NAMES[target]
    elif kind=='chara_dasha':
        if c.get('temporal_scope')!='current' or not isinstance(value,dict): raise Unverified('Chara requires current period and structured fields')
        from calculators.chara_dasha_calculator import CharaDashaCalculator
        result=memo('chara_dasha',lambda:CharaDashaCalculator(d1).calculate_dasha(datetime.fromisoformat(birth['date']+'T'+birth['time']),dt()))
        md=next(p for p in result['periods'] if p['is_current'])
        if value.get('period')=='Antardasha': row=next(p for p in md['antardashas'] if p['is_current'])
        elif value.get('period')=='Mahadasha':row=md
        else: raise Unverified('Unknown Chara level')
        actual={'sign':row['sign_name']}
        if 'end' in value:
            if not re.fullmatch(r'[A-Za-z]+ \d{4}',str(value['end'])): raise Unverified('Chara end requires month year')
            actual['end']=datetime.fromisoformat(row['end_date']).strftime('%B %Y')
        return actual,'chara_dasha.'+value['period'],all(actual[k]==value[k] for k in actual)
    elif kind=='jaimini_role':
        role=str(value)
        if role not in karakas(): raise Unverified('Unknown Jaimini role')
        actual=karakas()[role]['planet']
        return actual,f'D1.chara_karakas.{role}.planet',actual==planet
    elif kind in {'karakamsha_sign','karakamsha_house'}:
        actual=B.SIGN_NAMES[kl()] if kind=='karakamsha_sign' else (kl()-asc)%12+1
        path='jaimini.karakamsha.'+('sign' if kind=='karakamsha_sign' else 'D1_house')
    elif frame in FRAMES or frame=='sign' or kind=='house_occupants':
        ch=chart()
        if frame in FRAMES:
            if code!='D1': raise Unverified('Karakamsha adapter uses D1 positions; D9/Swamsa must be explicit')
            origin=kl()
        elif frame=='sign':
            if c.get('origin_sign') not in B.SIGN_NAMES: raise Unverified('Explicit sign origin unavailable')
            origin=B.SIGN_NAMES.index(c['origin_sign'])
        elif frame=='ascendant': origin=int(ch['ascendant']/30)%12
        else: raise Unverified('Unresolved house origin')
        if kind=='ascendant_sign': actual=B.SIGN_NAMES[origin]
        elif kind=='house_sign': actual=B.SIGN_NAMES[(origin+h()-1)%12]
        elif kind=='house_occupants':
            actual=[p for p,r in ch['planets'].items() if p in {'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'} and (int(r['longitude']/30)-origin)%12+1==h()]
            return actual,f'{code}.{frame}.houses.{house}.occupants',subset(actual)
        elif kind=='planet_house' and planet: actual=(int(ch['planets'][planet]['longitude']/30)-origin)%12+1
        else: raise Unverified('Unsupported Karakamsha claim representation')
        path=f'{code}.{frame}.{kind}.{house or planet or "origin"}'
    elif kind in {'sav','bav'}:
        if code!='D1' or frame!='ascendant': raise Unverified('AV adapter requires natal D1 ascendant frame')
        from calculators.ashtakavarga import AshtakavargaCalculator
        av=memo('av',lambda:AshtakavargaCalculator(birth,d1).calculate_sarvashtakavarga())
        sign=(asc+h()-1)%12
        if kind=='sav': points=av['sarvashtakavarga'][str(sign)]
        else: points=av['individual_charts'][planet]['bindus'][sign]
        if isinstance(value,dict) and value and set(value)<={'sign','points'}:
            actual={k: B.SIGN_NAMES[sign] if k=='sign' else points for k in value}
        elif type(value) is int: actual=points
        else: raise Unverified('Invalid bindu claim')
        path=f'D1.{kind}.{planet or "all"}.house.{house}'
    elif kind=='dasha_period':
        if not isinstance(value,dict): raise Unverified('Dasha dates need structured fields')
        from shared.dasha_calculator import DashaCalculator
        ds=memo('dashas',lambda:DashaCalculator(subject['settings']['ayanamsha']).calculate_current_dashas(birth,dt(),strict=True))
        level=str(value.get('period','')).lower()
        if level not in {'mahadasha','antardasha'}: raise Unverified('Dasha level unsupported')
        row=ds[level]
        def precision(expected,claimed):
            if re.fullmatch(r'\d{4}',str(claimed)): return expected[:4]
            if re.fullmatch(r'[A-Za-z]+ \d{4}',str(claimed)): return datetime.fromisoformat(expected).strftime('%B %Y')
            if re.fullmatch(r'[A-Za-z]+ \d{1,2}, \d{4}',str(claimed)): return datetime.fromisoformat(expected).strftime('%B %d, %Y').replace(' 0',' ')
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}',str(claimed)): return expected
            raise Unverified('Date precision unresolved')
        actual={k:precision(row[k],value[k]) for k in ('start','end') if k in value}
        if not actual: raise Unverified('Dasha start/end unavailable')
        return {'planet':row['planet'],**actual},f'vimshottari.{level}.{as_of}',row['planet']==planet and all(actual[k]==value[k] for k in actual)
    else: raise Unverified('No adapter')
    return actual,path,actual==value
