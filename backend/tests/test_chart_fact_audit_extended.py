import pytest
from chat.chart_fact_audit_extended import audit_extended, Unverified


@pytest.fixture
def cache():
    return {'charts': {'D1': {'ascendant':120, 'planets': {'Saturn':{'longitude':324}, 'Jupiter':{'longitude':237}, 'Sun':{'longitude':221}, 'Mercury':{'longitude':223}}},
                       'D9': {'ascendant':0,'planets':{'Jupiter':{'longitude':340}}},
                       'D10': {'ascendant':150,'planets':{'Saturn':{'longitude':190}}}},
            'jaimini_points': {'karkamsa_lagna':{'sign_id':11}},
            'karakas': {'Amatyakaraka':{'planet':'Saturn'}},
            'nakshatras': {'Venus':{'nakshatra_name':'Mula','pada':2}},
            'av': {'sarvashtakavarga':{'1':26}, 'individual_charts':{'Jupiter':{'bindus':{1:5}}}},
            'kp': {'cusp_lords':{10:{'sign_lord':'Venus','star_lord':'Sun','sub_lord':'Saturn'}},
                   'planet_significators':{'Mercury':[2,4,6,7,11]},
                   'four_step_theory':{'Mercury':{'planet':{'name':'Mercury','houses':[2,4,6,7,11]},'star_lord':{'name':'Saturn','houses':[4,5,6,7,8]},'sub_lord':{'name':'Rahu','houses':[2,4,9]},'sub_sub_lord':{'name':'Mercury','houses':[2,4,6,7,11]}}}},
            'dashas': {'mahadasha':{'planet':'Jupiter','start':'2021-12-28','end':'2037-12-28'},'antardasha':{'planet':'Mercury','start':'2026-08-28','end':'2028-12-03'}}}


def check(cache, kind, value, **kwargs):
    c={'claim_type':kind,'asserted_value':value,'chart':'D1','chart_scope':'natal','reference_frame':'ascendant',**kwargs}
    return audit_extended(c,{'birth':{},'settings':{'ayanamsha':'lahiri','node_type':'mean'}},cache,'2026-11-13T04:19:40Z')


@pytest.mark.parametrize('kind,value,kwargs', [
    ('dignity','own sign',{'planet':'Saturn'}),
    ('dignity','exalted',{'planet':'Saturn','chart':'D10'}),
    ('nakshatra',{'nakshatra':'Mula','pada':2},{'planet':'Venus'}),
    ('jaimini_role','Amatyakaraka',{'planet':'Saturn'}),
    ('karakamsha_sign','Pisces',{}), ('karakamsha_house',8,{}),
    ('house_sign','Sagittarius',{'house':10,'reference_frame':'Karakamsha'}),
    ('house_occupants',['Sun','Mercury','Jupiter'],{'house':9,'reference_frame':'Karakamsha','comparison':'contains'}),
    ('kp_cusp_lords',{'sign_lord':'Venus','star_lord':'Sun','sub_lord':'Saturn'},{'house':10,'chart':None}),
    ('kp_cusp_sub_lord','Saturn',{'house':10,'chart':None}),
    ('kp_significator_chain',['Saturn','Rahu','Mercury'],{'planet':'Mercury','chart':None}),
    ('kp_significator_houses',[2,6,11],{'planet':'Mercury','comparison':'contains','significator_basis':'planet_significators'}),
    ('kp_significator_houses',[2,4,5,6,7,8,9,11],{'planet':'Mercury','comparison':'equals','significator_basis':'four_step_union'}),
    ('sav',{'sign':'Taurus','points':26},{'house':10}), ('bav',5,{'planet':'Jupiter','house':10}),
    ('dasha_period',{'period':'Mahadasha','start':'2021','end':'2037'},{'planet':'Jupiter','temporal_scope':'current'}),
    ('dasha_period',{'period':'Antardasha','start':'August 28, 2026','end':'December 3, 2028'},{'planet':'Mercury','temporal_scope':'current'}),
])
def test_matching_calculator_evidence(cache,kind,value,kwargs):
    assert check(cache,kind,value,**kwargs)[2] is True


def test_wrong_karakamsha_house_not_confused_with_d1_house(cache):
    actual,path,match=check(cache,'house_sign','Scorpio',house=10,reference_frame='Karakamsha')
    assert actual=='Sagittarius' and not match
    actual,path,match=check(cache,'house_occupants',['Sun','Mercury','Jupiter'],house=10,reference_frame='Karakamsha',comparison='contains')
    assert actual==[] and not match


def test_wrong_kp_and_bindu_numbers_are_mismatches(cache):
    assert check(cache,'kp_cusp_sub_lord','Venus',house=10)[2] is False
    assert check(cache,'sav',25,house=10)[2] is False
    assert check(cache,'bav',2,house=10,planet='Jupiter')[2] is False


def test_ambiguous_kp_basis_and_future_transit_do_not_get_guessed(cache):
    with pytest.raises(Unverified):check(cache,'kp_significator_houses',[5,8,9],planet='Mercury',comparison='contains')
    assert check(cache,'kp_significator_houses',[2,6,11],planet='Mercury',comparison='contains')[2]
    with pytest.raises(Unverified):check(cache,'planet_house',9,planet='Saturn',chart_scope='transit',temporal_scope='future')
    with pytest.raises(Unverified):check(cache,'dasha_period',{'period':'Mahadasha','start':'2021'},planet='Jupiter')


def test_explicit_aquarius_origin_is_not_karakamsha(cache):
    assert check(cache,'house_sign','Scorpio',house=10,reference_frame='sign',origin_sign='Aquarius')[2]
    assert check(cache,'house_occupants',['Sun','Mercury','Jupiter'],house=10,reference_frame='sign',origin_sign='Aquarius',comparison='contains')[2]


def test_current_transit_sign_does_not_require_natal_house_frame(cache,monkeypatch):
    from calculators.real_transit_calculator import RealTransitCalculator
    monkeypatch.setattr(RealTransitCalculator,'get_planet_position',lambda *args: 345.)
    assert check(cache,'planet_sign','Pisces',planet='Saturn',chart_scope='transit',temporal_scope='current',chart=None,reference_frame=None)[2]
    with pytest.raises(Unverified):check(cache,'planet_house',8,planet='Saturn',chart_scope='transit',temporal_scope='current',chart=None,reference_frame=None)


def test_transit_exit_compares_month_without_claiming_exact_ingress(cache,monkeypatch):
    from calculators.real_transit_calculator import RealTransitCalculator
    def position(self,date,planet): return 345. if date.month != 6 else 5.
    monkeypatch.setattr(RealTransitCalculator,'get_planet_position',position)
    assert check(cache,'transit_end_date','June 2027',planet='Saturn',chart_scope='transit',temporal_scope='future')[2]
    assert cache['transit_exits']['Saturn']['precision']=='daily sampling; month comparison only'
