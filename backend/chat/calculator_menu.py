"""Shared, parameter-aware deterministic menu for Verified and conflict chat."""
from datetime import date, datetime, time, timezone
from typing import Optional, Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Each entry describes both its scope and required inputs to the model.
EXTRA_CALCULATORS = {
 'parashari.double_transit': 'Exact Jupiter–Saturn overlaps. Requires houses, start_date, end_date (UTC end exclusive).',
 'dasha.kalachakra_bphs': 'BPHS Kalachakra sign periods, Deha/Jeeva and gati transitions. Requires start_date, end_date; current periods evaluated at start_date. Distinct from Jaimini Kalachakra.',
 'dasha.kalachakra_jaimini': 'Jaimini Kalachakra sign-period variant. Requires start_date, end_date; current periods evaluated at start_date. Not BPHS Kalachakra.',
 'dasha.sudarshana': 'Sudarshana annual progression triggers from Lagna, Moon and Sun. Requires year. Returns yearly triggers, not a complete nested dasha-period schedule.',
 'dasha.yogini': 'Yogini MD/AD planetary periods with exact instants and declared year length. Requires start_date and end_date (UTC end exclusive).',
 'dasha.shoola': 'Standard nine-year forward Shoola periods (not Niryana Shoola; simplified starting-sign strength is disclosed), not a general career timer. Requires start_date, end_date; optional reference_house for a relative.',
 'annual.varshphal': 'Solar return chart, Muntha and Mudda periods. Requires year; optional location overrides birth location.',
 'annual.tajika': 'Tajika configurations on the annual chart. Requires year, exactly two planets, one matter house; optional location.',
 'annual.nakshatra': 'Annual nakshatra periods. Requires year and location.',
 'jaimini.argala': 'Argala and obstruction evidence. Optional houses selects target houses.',
 'jaimini.rashi_strength': 'Jaimini sign strength with components. Requires signs (1=Aries through 12=Pisces).',
 'jaimini.points': 'Jaimini points, arudhas and reference points from D1/D9.',
 'jaimini.full_analysis': 'Structured Jaimini relationships, aspects and yoga evidence, not a prewritten answer.',
 'yogas.general': 'Same general yoga source as mobile Yogas screen; formation rules and chart evidence.',
 'yogas.career': 'Career-specific yoga checks.',
 'yogas.pancha_mahapurusha': 'Pancha Mahapurusha formation checks.',
 'yogas.neecha_bhanga': 'Debilitation cancellation conditions.',
 'yogas.classical_core': 'Named classical core yoga rules, using the mobile yoga source.',
 'conditions.badhaka': 'Badhaka lord and obstruction connections; optional houses.',
 'conditions.gandanta': 'Gandanta junction conditions.',
 'conditions.mrityu_bhaga': 'Critical-degree rule checks; not a prediction of death.',
 'conditions.planetary_war': 'Planetary war geometry and participants.',
 'conditions.pushkara': 'Pushkara placements.',
 'conditions.vargottama': 'D1/D9 vargottama placements.',
 'conditions.nodal_enclosure': 'Exact Rahu–Ketu enclosure geometry, with boundary cases.',
 'points.indu_lagna': 'Indu Lagna calculation and connected planets.',
 'points.mudakku': 'Tamil Siddhar Mudakku rule; specialist system.',
 'points.sniper': 'Natal Kharesh (22nd Drekkana), Moon/Lagna 64th Navamsa with separate mapped-varga signs and physical D1 sectors, Bhrigu Bindu and critical degrees. No transit timing or standalone event guarantee.',
 'points.kota_chakra': 'Kota Chakra structure and planetary connections.',
 'strength.house': 'House strength breakdown. Requires houses.',
 'strength.bhava_bala': 'Classical Bhava Bala components. Optional houses.',
 'parashari.planet_delivery': 'Planet delivery conditions, cancellation and lordship.',
 'election.panchang': 'Panchang for a local date/time. Requires start_date, location; time defaults to noon explicitly.',
 'election.muhurat': 'Suitable local slots. Requires start_date, end_date, location, event_type: vehicle/home/gold/business/childbirth.',
 'election.navatara': 'Transit nakshatra relationship to natal Moon. Requires start_date; optional location/time sets the local snapshot (default noon at saved birth location).',
 'location.analysis': 'Relocation evidence for specified destinations. Requires topic and cities with coordinates/timezones.',
}

CALCULATOR_EVIDENCE_INTEGRITY = """
Respect each calculator's method, reference, coordinate_frame, boundary_type and limitations.
Standard Shoola is not Niryana Shoola. Its disclosed simplified starting-sign strength is not a
fully audited Ayur strength method. Never substitute it when Niryana Shoola is requested.
Treat simplified Rudra/Maheshwara outputs as partial evidence, not verified full classical identities.
D3/D9 mapped signs are not physical D1 transit signs. Physical contacts require d1_sector or natal
D1 longitudes AND a separately calculated dated transit result. The natal points tool supplies no timing.
A current transit snapshot cannot establish arbitrary future contacts. No requested but unsupported
method may be invented. Do not count Chara and Jaimini as independent dashas, or double-count
Kharesh under both maraka and sensitive-point categories. A calculator error or unavailable status
is missing evidence, not absence of an astrological condition. These astrological combinations do
not establish medical or mortality risk; do not turn them into a probability, risk score or diagnosis.
"""

class Location(BaseModel):
 model_config = ConfigDict(extra='forbid')
 name: str
 latitude: float = Field(ge=-90, le=90)
 longitude: float = Field(ge=-180, le=180)
 timezone: str = Field(min_length=1)

class CalculatorParameters(BaseModel):
 model_config = ConfigDict(extra='forbid')
 divisions: Optional[list[int]] = None
 houses: Optional[list[Annotated[int, Field(strict=True, ge=1, le=12)]]] = None
 signs: Optional[list[Annotated[int, Field(strict=True, ge=1, le=12)]]] = None
 planets: Optional[list[str]] = None
 start_date: Optional[date] = None
 end_date: Optional[date] = None
 year: Optional[int] = Field(default=None, ge=1800, le=2399)
 reference_house: Optional[int] = Field(default=None, ge=1, le=12)
 location: Optional[Location] = None
 cities: Optional[list[Location]] = None
 topic: Optional[str] = None
 event_type: Optional[str] = None
 time: Optional[str] = None

 @model_validator(mode='after')
 def validate_values(self):
  if self.divisions is not None and (not self.divisions or any(n not in {1,2,3,4,5,6,7,8,9,10,11,12,16,20,24,27,30,40,45,60} for n in self.divisions)):
   raise ValueError("Unsupported divisional chart")
  for values in (self.houses, self.signs):
   if values is not None and (not values or len(values) != len(set(values))): raise ValueError('Supply distinct house/sign numbers')
  if self.start_date and self.end_date and self.end_date <= self.start_date: raise ValueError('End date must follow start date')
  if self.start_date and self.end_date and (self.end_date-self.start_date).days > 366*120: raise ValueError('Range exceeds calculator coverage')
  if self.planets and any(p not in {'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'} for p in self.planets): raise ValueError('Unknown planet')
  return self

def validate_parameters(capability, raw):
 p = CalculatorParameters.model_validate(raw or {})
 required = {
  'parashari.double_transit': ('houses','start_date','end_date'), 'dasha.yogini': ('start_date','end_date'),
  'dasha.kalachakra_bphs': ('start_date','end_date'), 'dasha.kalachakra_jaimini': ('start_date','end_date'), 'dasha.sudarshana': ('year',),
  'dasha.shoola': ('start_date','end_date'), 'annual.varshphal': ('year',), 'annual.tajika': ('year','planets','houses'),
  'annual.nakshatra': ('year','location'), 'jaimini.rashi_strength': ('signs',), 'strength.house': ('houses',),
  'election.panchang': ('start_date','location'), 'election.muhurat': ('start_date','end_date','location','event_type'),
  'election.navatara': ('start_date',), 'location.analysis': ('topic','cities'),
 }.get(capability, ())
 if any(getattr(p,k) is None for k in required): raise ValueError(f'{capability} requires {", ".join(required)}')
 if capability == 'annual.tajika' and (len(p.planets)!=2 or len(set(p.planets))!=2 or len(p.houses)!=1): raise ValueError('Tajika requires two distinct planets and one house')
 if capability == 'election.muhurat' and p.event_type not in {'vehicle','home','gold','business','childbirth'}: raise ValueError('Unsupported Muhurat event')
 if p.cities is not None and not p.cities: raise ValueError('Supply destination cities')
 if p.time: time.fromisoformat(p.time)
 return p

# Remove client prose/UI fields, preserving complete factual rows (never slice lists).
_PROSE = {'prediction','predictions','interpretation','interpretations','remedies','remedy','guidance','description','summary','vibe','combined_prediction','html','formatted_response','recommendations','warning','warnings'}
def compact_result(value):
 if isinstance(value, dict): return {k: compact_result(v) for k,v in value.items() if str(k).lower() not in _PROSE}
 if isinstance(value, (list,tuple)): return [compact_result(v) for v in value]
 if isinstance(value,(date,datetime)): return value.isoformat()
 return value

def run_calculator(capability, birth, raw=None):
 import importlib
 from types import SimpleNamespace
 from calculators.chart_calculator import ChartCalculator
 from calculators.divisional_chart_calculator import DivisionalChartCalculator
 p = validate_parameters(capability, raw)
 calc = ChartCalculator({})
 profile = birth.get('calculation_profile') or {}
 chart = calc.calculate_chart(SimpleNamespace(**birth), ayanamsha=profile.get('ayanamsha', birth.get('ayanamsha') or 'lahiri'), node_type=profile.get('node_type','mean'))
 divisions = DivisionalChartCalculator(chart)
 def instance(module, cls, *args): return getattr(importlib.import_module('calculators.'+module),cls)(*args)
 def instant(d): return datetime.combine(d,time.min,tzinfo=timezone.utc)
 if capability == 'parashari.double_transit':
  from charts.double_transit_service import calculate_double_transits
  result=calculate_double_transits(chart,instant(p.start_date),instant(p.end_date),ayanamsha=profile.get('ayanamsha',birth.get('ayanamsha') or 'lahiri'))
  result['windows']=[w for w in result['windows'] if w['house'] in p.houses]
  result.update(focus_houses=p.houses,window_count=len(result['windows']))
 elif capability.startswith('yogas.'):
  yoga=instance('yoga_calculator','YogaCalculator',SimpleNamespace(**birth),chart)
  methods={'general':'calculate_all_yogas','classical_core':'calculate_all_yogas','career':'calculate_career_specific_yogas','pancha_mahapurusha':'calculate_panch_mahapurusha_yogas','neecha_bhanga':'calculate_neecha_bhanga_yogas'}
  result=getattr(yoga,methods[capability.split('.')[1]])()
 elif capability in {'dasha.kalachakra_bphs','dasha.kalachakra_jaimini'}:
  from utils.timezone_service import parse_timezone_offset
  dasha_birth={**birth,'timezone_offset':parse_timezone_offset(birth.get('timezone',''),birth.get('latitude'),birth.get('longitude'),for_date=birth.get('date'))}
  if capability == 'dasha.kalachakra_bphs':
   obj=instance('bphs_kalachakra_calculator','BPHSKalachakraCalculator',profile.get('ayanamsha',birth.get('ayanamsha') or 'lahiri'))
   result=obj.calculate_kalchakra_dasha(dasha_birth,current_date=instant(p.start_date))
  else:
   result=instance('jaimini_kalachakra_calculator','JaiminiKalachakraCalculator',chart).calculate_jaimini_kalachakra_dasha(dasha_birth,current_date=instant(p.start_date))
  if result.get('error'): raise ValueError('Requested Kalachakra calculation unavailable')
  result={k:v for k,v in result.items() if k not in {'wheel_data','paramayus_note'}}
 elif capability == 'dasha.sudarshana':
  result=instance('sudarshana_dasha_calculator','SudarshanaDashaCalculator',chart,birth).calculate_precision_triggers(p.year)
 elif capability == 'dasha.yogini':
  result=instance('yogini_dasha_calculator','YoginiDashaCalculator').get_periods_in_range(birth,chart['planets']['Moon']['longitude'],instant(p.start_date),instant(p.end_date))
 elif capability == 'dasha.shoola':
  result=instance('shoola_dasha_calculator','ShoolaDashaCalculator',chart).calculate_shoola_dasha(birth,relative_house_idx=p.reference_house-1 if p.reference_house else None,focus_date=instant(p.start_date))
 elif capability.startswith('annual.'):
  annual_birth={**birth}
  if p.location: annual_birth.update(p.location.model_dump(exclude={'name'}))
  if capability == 'annual.nakshatra':
   result=instance('annual_nakshatra_calculator','AnnualNakshatraCalculator').calculate_annual_nakshatra_periods_all_continuous(p.year,p.location.latitude,p.location.longitude)
  else:
   annual=instance('varshphal_calculator','VarshphalCalculator',calc).calculate_varshphal(annual_birth,p.year)
   tajika_chart=annual['chart']
   annual['chart']={k:annual['chart'][k] for k in ('ascendant','planets') if k in annual['chart']}
   annual['chart']['planets']={k:{field:v[field] for field in ('longitude','sign','house','retrograde','speed') if field in v} for k,v in annual['chart']['planets'].items()}
   result=annual if capability=='annual.varshphal' else instance('tajika_classical_engine','TajikaClassicalEngine',tajika_chart).all_configurations(*p.planets,matter_house=p.houses[0])
 elif capability == 'jaimini.argala': result=instance('argala_calculator','ArgalaCalculator',chart,birth).calculate_argala_analysis()
 elif capability == 'jaimini.rashi_strength':
  obj=instance('jaimini_rashi_strength','JaiminiRashiStrength',chart)
  result={str(sign):{'score':obj.calculate_rashi_strength(sign-1), 'planetary':obj._calculate_planetary_strength(sign-1), 'aspects':obj._calculate_aspect_strength(sign-1), 'lord':obj._calculate_rashi_lord_strength(sign-1), 'combinations':obj._calculate_special_combinations(sign-1)} for sign in p.signs}
 elif capability in {'jaimini.points','jaimini.full_analysis'}:
  karakas=instance('chara_karaka_calculator','CharaKarakaCalculator',chart).calculate_chara_karakas()['chara_karakas']
  ak=karakas['Atmakaraka']['planet']
  points=instance('jaimini_point_calculator','JaiminiPointCalculator',chart,divisions.calculate_divisional_chart(9),ak,birth).calculate_jaimini_points()
  result=points if capability=='jaimini.points' else instance('jaimini_full_analyzer','JaiminiFullAnalyzer',chart,karakas,points).get_jaimini_report()
 elif capability == 'conditions.badhaka':
  obj=instance('badhaka_calculator','BadhakaCalculator',chart)
  result=obj.get_chart_badhaka_summary(int(chart['ascendant']/30))
  if p.houses: result['house_connections']={str(h):obj.analyze_badhaka_impact_on_house(h,int(chart['ascendant']/30)) for h in p.houses}
 elif capability == 'conditions.pushkara': result=instance('pushkara_calculator','PushkaraCalculator').analyze_chart(chart,int(chart['ascendant']/30))
 elif capability == 'conditions.vargottama': result=instance('vargottama_calculator','VargottamaCalculator',chart,{'D9':divisions.calculate_divisional_chart(9)}).calculate_vargottama_positions()
 elif capability == 'conditions.nodal_enclosure':
  from calculators.nodal_enclosure_calculator import calculate_nodal_enclosure
  result=calculate_nodal_enclosure(chart)
 elif capability == 'points.sniper': result=instance('sniper_points_calculator','SniperPointsCalculator',chart,divisions.calculate_divisional_chart(3),divisions.calculate_divisional_chart(9)).get_all_sniper_points(include_transits=False)
 elif capability == 'strength.house':
  obj=instance('house_strength_calculator','HouseStrengthCalculator',chart)
  result={str(h):obj.calculate_house_strength(h) for h in p.houses}
 elif capability == 'strength.bhava_bala':
  from calculators.classical_bhava_bala import calculate_classical_bhava_bala
  from calculators.classical_shadbala import calculate_classical_shadbala
  vargas={f'D{n}':divisions.calculate_divisional_chart(n)['divisional_chart']['planets'] for n in (1,2,3,7,9,12,30)}
  result=calculate_classical_bhava_bala(birth,chart,calculate_classical_shadbala(birth,{**chart, "divisions":vargas}))
 elif capability == 'parashari.planet_delivery':
  from calculators.planet_result_delivery import calculate_planet_result_delivery
  result=calculate_planet_result_delivery(chart)
 elif capability == 'election.panchang':
  result=instance('panchang_calculator','PanchangCalculator').calculate_panchang(str(p.start_date),p.time or '12:00:00',p.location.latitude,p.location.longitude,p.location.timezone)
 elif capability == 'election.navatara':
  from calculators.chart_calculator import ChartCalculator
  transit_birth={**birth,'date':str(p.start_date),'time':p.time or '12:00:00'}
  if p.location: transit_birth.update(p.location.model_dump(exclude={'name'}))
  transit=calc.calculate_chart(SimpleNamespace(**transit_birth),ayanamsha=profile.get('ayanamsha',birth.get('ayanamsha') or 'lahiri'),node_type=profile.get('node_type','mean'))
  obj=instance('navatara_calculator','NavataraCalculator',int(chart['planets']['Moon']['longitude']/(360/27)))
  result=obj.get_transit_tara_analysis({k:int(v['longitude']/(360/27)) for k,v in transit['planets'].items()})
  result={'snapshot_date':str(p.start_date),'snapshot_time':p.time or '12:00:00','timezone':transit_birth['timezone'],
          'birth_moon_nakshatra_index':int(chart['planets']['Moon']['longitude']/(360/27)), 'navatara':result,
          'transit_positions':{k:{'longitude':v['longitude'],'sign':int(v['longitude']/30),
            'natal_house':(int(v['longitude']/30)-int(chart['ascendant']/30))%12+1,
            'nakshatra_index':int(v['longitude']/(360/27))} for k,v in transit['planets'].items()},
          'snapshot_only':True,'intraday_transitions_calculated':False}
 elif capability == 'election.muhurat':
  obj=instance('muhurat_calculator','MuhuratCalculator')
  method={'vehicle':'vehicle','home':'griha_pravesh','gold':'gold','business':'business','childbirth':'childbirth'}[p.event_type]
  result=getattr(obj,'calculate_'+method+'_muhurat')(str(p.start_date),str(p.end_date),p.location.latitude,p.location.longitude,int(chart['planets']['Moon']['longitude']/(360/27))+1,tz=p.location.timezone)
  if isinstance(result,dict):
   result={**result,'candidate_samples':result.get('recommendations',[]),'coverage':'Legacy hourly samples; not validated whole-interval windows. Use dedicated Muhurat for interval elections.'}
 elif capability == 'location.analysis':
  result=instance('locational_calculator','LocationalCalculator').analyze(birth,category=p.topic,location_scope='both',natal_chart=chart,metros=[c.model_dump() for c in p.cities],top_n=len(p.cities))
 else:
  adapters={'conditions.gandanta':('gandanta_calculator','GandantaCalculator','calculate_gandanta_analysis'), 'conditions.mrityu_bhaga':('mrityu_bhaga_calculator','MrityuBhagaCalculator','analyze_chart_mrityu_bhaga'), 'conditions.planetary_war':('planetary_war_calculator','PlanetaryWarCalculator','calculate_planetary_wars'), 'points.indu_lagna':('indu_lagna_calculator','InduLagnaCalculator','get_indu_lagna_data'), 'points.mudakku':('mudakku_calculator','MudakkuCalculator','calculate'), 'points.kota_chakra':('kota_chakra_calculator','KotaChakraCalculator','calculate')}
  module,cls,method=adapters[capability]
  result=getattr(instance(module,cls,chart),method)()
 if capability == 'annual.nakshatra':
  if p.start_date and p.end_date:
   result=[row for row in result if row['start_datetime'].date() < p.end_date and row['end_datetime'].date() > p.start_date]
  result=[{k:row[k] for k in ('nakshatra','start_datetime','end_datetime','nakshatra_index') if k in row} for row in result]
 if capability in {'dasha.yogini','dasha.shoola','dasha.kalachakra_bphs','dasha.kalachakra_jaimini'}:
  def scope_periods(value):
   if isinstance(value,list):
    rows=[]
    for row in value:
     if isinstance(row,dict):
      left=row.get('start_iso',row.get('start',row.get('start_date')))
      right=row.get('end_iso',row.get('end',row.get('end_date')))
      if left and right:
       left=datetime.fromisoformat(str(left)); right=datetime.fromisoformat(str(right))
       if left.tzinfo is None: left=left.replace(tzinfo=timezone.utc)
       if right.tzinfo is None: right=right.replace(tzinfo=timezone.utc)
       if left >= instant(p.end_date) or right <= instant(p.start_date): continue
     rows.append(scope_periods(row))
    return rows
   if isinstance(value,dict): return {k:scope_periods(v) for k,v in value.items()}
   return value
  result=scope_periods(result)
 if p.houses and capability in {'jaimini.argala','strength.bhava_bala'}:
  result={k:v for k,v in result.items() if str(k) in {str(h) for h in p.houses}}
 return {'calculator':capability,'parameters':p.model_dump(mode='json',exclude_none=True),'facts':compact_result(result)}
