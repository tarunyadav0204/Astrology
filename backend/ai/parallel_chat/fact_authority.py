"""Small, calculated facts carried past specialist prose into synthesis."""

SIGN_NAMES = ('Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
              'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces')


def divisional_lord_authority(payload):
    """Project existing calculated divisional rows, never borrow D1 lordships."""
    result = {}
    dx = (payload.get('px') or {}).get('dx') or {}
    for section in dx.values():
        if not isinstance(section, dict):
            continue
        for code, chart in (section.get('charts') or {}).items():
            for row in chart.get('rows', []):
                if not row.get('h') or not row.get('lord'):
                    continue
                result.setdefault(code, {})[str(row['h'])] = {
                    'house': row['h'], 'sign': SIGN_NAMES[row['s'] - 1],
                    'house_lord': row['lord'], 'lord_house_in_this_chart': row['lord_h'],
                    'lord_sign_in_this_chart': (
                        SIGN_NAMES[(row['s'] - row['h'] + row['lord_h'] - 1) % 12]
                        if isinstance(row.get('lord_h'), int) and 1 <= row['lord_h'] <= 12 else None
                    ),
                    'occupants': row.get('occ', []),
                }
    return result


def clarify_jaimini_payload(payload, sign_aspects=None):
    """Replace terse, competing representations after derived payload creation."""
    payload['frame_authority'] = jaimini_frame_authority(payload)
    authority = payload['frame_authority']
    # The calculator uses zero-based signs; the compact agent schema uses one-based.
    # Join the existing map, rather than asking the writer to calculate aspects.
    for index, (name, frame) in enumerate(authority['sign_frames'].items()):
        targets = (sign_aspects or {}).get(str(index), (sign_aspects or {}).get(index))
        if targets is not None:
            frame['rashi_aspects_to_signs'] = [SIGN_NAMES[i] for i in targets]
        frame['houses_from_special_lagnas'] = {
            key: (index + 1 - row['sign']) % 12 + 1
            for key, row in authority['special_lagnas'].items()
            if isinstance(row.get('sign'), int) and 1 <= row['sign'] <= 12
        }
    # Precompute the relations the writer used to invert. These are calculator
    # facts, not an LLM-generated interpretation or a second model pass.
    facts = []
    for key, row in authority['special_lagnas'].items():
        sign = row.get('sign')
        if not isinstance(sign, int) or not 1 <= sign <= 12:
            continue
        name = SIGN_NAMES[sign - 1]
        frame = authority['sign_frames'][name]
        facts.append(f"{key} is in {name}: natal house {frame['natal_house']}; "
                     f"house {frame['house_from_chara_md']} from Chara MD; "
                     f"house {frame['house_from_chara_ad']} from Chara AD.")
    for target, row in authority['argala_by_natal_target_house'].items():
        net = row.get('net_strength')
        if not isinstance(net, (float, int)):
            continue
        balance = 'net support' if net > 0 else 'net obstruction' if net < 0 else 'neutral balance'
        active = [r['planet'] for r in row['obstruction'] if isinstance(r['strength'], (int, float)) and r['strength'] > 0]
        zero = [r['planet'] for r in row['zero_strength_obstruction']]
        facts.append(f"Natal target house {target}: Argala {balance} ({net}); "
                     f"positive-strength obstruction contributors: {', '.join(active) or 'none'}; "
                     f"zero-strength obstruction contributors: {', '.join(zero) or 'none'}.")
    payload['reading_basis'] = facts
    for level in ('md', 'ad'):
        period = authority['chara_' + level]
        sign = period.get('s')
        if not isinstance(sign, int) or not 1 <= sign <= 12:
            continue
        name = SIGN_NAMES[sign - 1]
        tenth = SIGN_NAMES[(sign + 8) % 12]
        facts.append(f"Chara {level.upper()} {name}: 10th from this period is {tenth}; "
                     f"occupants: {', '.join(authority['sign_frames'][tenth]['occupants']) or 'none'}.")
    for name, frame in authority['sign_frames'].items():
        if 'rashi_aspects_to_signs' in frame:
            facts.append(f"{name} rashi aspects ONLY {', '.join(frame['rashi_aspects_to_signs'])}; "
                         f"planets occupying {name}: {', '.join(frame['occupants']) or 'none'}.")
    # The same facts are now named in argala_by_natal_target_house.
    payload['jaimini'].pop('AG', None)
    jx = payload.get('jx') or {}
    # Inverse house counts duplicated the same sign geometry, but repeatedly
    # leaked into forward-frame claims. Keep one orientation for the writer;
    # the original agent/calculator data and derived support bands stay intact.
    jx.pop('rf', None)
    jx.pop('kr', None)
    for topic in ('career', 'relationship'):
        (jx.get(topic) or {}).pop('rf', None)


def jaimini_frame_authority(payload):
    jaimini = payload.get('jaimini') or {}
    periods = (payload.get('chara_dasha') or {}).get('P') or []
    md = next((p for p in periods if p.get('ic')), {})
    ad = next((p for p in md.get('ad', []) if p.get('ic')), {})
    asc = ((jaimini.get('PS') or {}).get('Asc') or {}).get('s')

    def house(sign, origin):
        if isinstance(sign, int) and isinstance(origin, int) and 1 <= sign <= 12 and 1 <= origin <= 12:
            return (sign - origin) % 12 + 1
        return None

    return {
        'sign_numbering': '1=Aries through 12=Pisces; sign numbers are not houses',
        'sign_frames': {
            name: {'natal_house': house(i, asc), 'house_from_chara_md': house(i, md.get('s')),
                   'house_from_chara_ad': house(i, ad.get('s')),
                   'occupants': [p for p, row in (jaimini.get('PS') or {}).items()
                                 if p != 'Asc' and row.get('s') == i]}
            for i, name in enumerate(SIGN_NAMES, 1)
        },
        'argala_by_natal_target_house': {
            target: {
                'net_strength': row.get('n'), 'grade_code': row.get('g'),
                'support': [{'planet': r['p'], 'house_from_target': r['k'], 'strength': r['rs']}
                            for r in row.get('ap', [])],
                'obstruction': [{'planet': r['p'], 'house_from_target': r['k'], 'strength': r['rs']}
                                for r in row.get('vp', []) if r['rs'] != 0],
                'zero_strength_obstruction': [
                    {'planet': r['p'], 'house_from_target': r['k'], 'strength': r['rs']}
                    for r in row.get('vp', []) if r['rs'] == 0],
            } for target, row in (jaimini.get('AG') or {}).items()
        },
        'chara_md': {**{k: md[k] for k in ('s', 'nm', 'ds', 'de', 'y') if k in md},
                     **({'natal_house': house(md.get('s'), asc)} if md else {})},
        'chara_ad': {**{k: ad[k] for k in ('s', 'nm', 'ds', 'de') if k in ad},
                     **({'natal_house': house(ad.get('s'), asc),
                         'house_from_chara_md': house(ad.get('s'), md.get('s'))} if ad else {})},
        'special_lagnas': {
            key: {'sign': row.get('s'), 'natal_house': house(row.get('s'), asc)}
            for key, row in (jaimini.get('JP') or {}).items()
        },
        'karakas': {
            key: {'planet': row.get('p'), 'sign': row.get('s'),
                  'natal_house': row.get('h'),
                  'house_from_chara_md': house(row.get('s'), md.get('s')),
                  'house_from_chara_ad': house(row.get('s'), ad.get('s'))}
            for key, row in (jaimini.get('CK') or {}).items()
        },
    }


def calculated_fact_authority(context):
    """Carry compact, explicitly joined calculator rows into writers, without an LLM.

    Missing calculations stay missing. In particular an absent Gandanta analysis
    is not a negative result, and SAV sign keys must never be read as house keys.
    """
    from calculators.classical_jaimini import SIGN_LORDS

    charts = {'D1': context.get('d1_chart') or {}}
    av_keys = {'D1': 'd1_rashi'}
    for key, section in (context.get('divisional_charts') or {}).items():
        division = section.get('division_number')
        if division and section.get('divisional_chart'):
            code = f'D{division}'
            charts[code] = section['divisional_chart']
            av_keys[code] = key
    gandanta = (context.get('special_points') or {}).get('gandanta_analysis') or {}
    flagged = {r.get('planet') for r in gandanta.get('planets_in_gandanta', [])}
    result = {'charts': {}}
    for code, chart in charts.items():
        planets = chart.get('planets') or {}
        av = (context.get('ashtakavarga') or {}).get(av_keys.get(code), {})
        sav = (av.get('sarvashtakavarga') or {}).get('sarvashtakavarga') or {}
        rows = {}
        for index, row in enumerate(chart.get('houses') or []):
            sign = row.get('sign')
            if not isinstance(sign, int) or not 0 <= sign < 12:
                continue
            house = row.get('house_number', index + 1)
            lord = SIGN_LORDS[sign]
            record = {'sign': SIGN_NAMES[sign], 'lord': lord,
                      'lord_house': (planets.get(lord) or {}).get('house'),
                      'occupants': [p for p, v in planets.items() if v.get('house') == house]}
            if str(sign) in sav or sign in sav:
                record['SAV'] = sav.get(str(sign), sav.get(sign))
            record['BAV_by_planet'] = {
                p: values['bindus'].get(str(sign), values['bindus'].get(sign))
                for p, values in (av.get('bhinnashtakavarga') or {}).items()
                if str(sign) in (values.get('bindus') or {}) or sign in (values.get('bindus') or {})
            }
            if code == 'D1' and 'graha_drishti_by_house' in chart:
                record['graha_aspects_received'] = chart['graha_drishti_by_house'].get(str(house), [])
            rows[str(house)] = record
        result['charts'][code] = {
            'houses': rows,
            'planets': {
                p: {k: v[k] for k in ('sign_name', 'house', 'dignity', 'nakshatra', 'nakshatra_pada', 'nakshatra_lord', 'retrograde', 'vargottama', 'combust', 'neecha_bhanga') if k in v}
                for p, v in planets.items()
            },
        }
        if code == 'D1' and 'planets_in_gandanta' in gandanta:
            for p, row in result['charts'][code]['planets'].items():
                row['gandanta'] = p in flagged
    dashas = context.get('current_dashas') or {}
    result['vimshottari'] = {
        level: {k: row[k] for k in ('planet', 'start', 'end') if k in row}
        for level in ('mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana')
        if isinstance((row := dashas.get(level)), dict)
    }
    result['vimshottari']['mahadasha_sequence'] = [
        {k: row[k] for k in ('planet', 'start', 'end') if k in row}
        for row in dashas.get('maha_dashas', [])
    ]
    result['transit_segments'] = {
        planet: [{k: row[k] for k in ('sign', 'house', 'start_date', 'end_date') if k in row}
                 for row in rows]
        for planet, rows in (context.get('macro_transits_timeline') or {}).items()
        if isinstance(rows, list)
    }
    kp = context.get('kp_analysis') or {}
    result['kp'] = {key: kp[key] for key in ('cusp_lords', 'planet_lords', 'planet_significators') if key in kp}
    result['kp']['four_step_house_unions'] = {
        planet: sorted({h for row in chain.values() if isinstance(row, dict) for h in row.get('houses', [])})
        for planet, chain in (kp.get('four_step_theory') or {}).items()
    }
    sudarshana = context.get('sudarshana_chakra') or {}
    result['sudarshana'] = {key: sudarshana[key] for key in ('lagna_chart', 'chandra_lagna', 'surya_lagna') if key in sudarshana}
    result['sudarshana']['house_agreement'] = [
        {k: row[k] for k in ('h', 'agree', 'band') if k in row}
        for row in (sudarshana.get('synthesis') or {}).get('house_agreement', [])
    ]
    result['transit_tara'] = context.get('navatara_warnings') or {}
    result['compound_friendship'] = (context.get('friendship_analysis') or {}).get('friendship_matrix') or {}
    return result


def fact_reading_basis(facts, special_points=None):
    """Render role joins that prose writers repeatedly confused, for any chart.

    This is evidence presentation, not a post-generation rewrite or a second call.
    Keep it small: primary angles for each chart and paired D1/D9 placements.
    """
    lines = []
    charts = facts.get('charts') or {}
    for code, chart in charts.items():
        for house in ('1', '7', '10'):
            row = (chart.get('houses') or {}).get(house)
            if not row:
                continue
            lines.append(f"{code} house {house} = {row['sign']}; its lord is {row['lord']} "
                         f"in {code} house {row['lord_house']}; occupants (not lords) = "
                         f"{', '.join(row['occupants']) or 'none'}."
                         + (f" {code} house {house} SAV = {row['SAV']}." if 'SAV' in row else ''))
    d9 = (charts.get('D9') or {}).get('planets') or {}
    for planet, row in (charts.get('D1') or {}).get('planets', {}).items():
        if planet not in d9:
            continue
        other = d9[planet]
        d1_lords = sorted(int(h) for h, v in (charts['D1'].get('houses') or {}).items() if v['lord'] == planet)
        d9_lords = sorted(int(h) for h, v in (charts['D9'].get('houses') or {}).items() if v['lord'] == planet)
        lines.append(f"{planet}: D1 {row.get('sign_name')} house {row.get('house')}, dignity {row.get('dignity')}, "
                     f"nakshatra {row.get('nakshatra')} pada {row.get('nakshatra_pada')}; "
                     f"D9 {other.get('sign_name')} house {other.get('house')}, dignity {other.get('dignity')}. "
                     f"Lordships: D1 {d1_lords}; D9 {d9_lords}. Occupancy is not lordship."
                     + (f" Gandanta = {row['gandanta']}." if 'gandanta' in row else '')
                     + (f" Vargottama = {row['vargottama']}." if 'vargottama' in row else ''))
    for code, chart in charts.items():
        if code in ('D1', 'D9'):
            continue
        for planet, row in chart.get('planets', {}).items():
            lines.append(f"{code} {planet}: {row.get('sign_name')}, house {row.get('house')}, "
                         f"dignity {row.get('dignity')}. Never borrow D1 placement for {code}.")
    for level, row in facts.get('vimshottari', {}).items():
        if not isinstance(row, dict):
            continue
        lines.append(f"Vimshottari {level}: {row.get('planet')}; start = {row.get('start', 'not supplied')}; "
                     f"end = {row.get('end', 'not supplied')}. Never borrow dates from another level.")
    yogi = (special_points or {}).get('yogi_points') or {}
    if yogi:
        lines.append(f"Yogi = {(yogi.get('yogi') or {}).get('lord')}; "
                     f"Duplicate Yogi = {(yogi.get('duplicate_yogi') or {}).get('lord')}; "
                     f"Avayogi = {(yogi.get('avayogi') or {}).get('lord')}. These are roles, not house lordships.")
        policy = yogi.get('avayogi_effect_policy') or {}
        natal = policy.get('natal_effect') or {}
        if natal:
            lines.append(f"Avayogi NATAL effect = {natal.get('polarity')} under {natal.get('rule')}; "
                         f"placement house = {policy.get('placement_house')}; "
                         f"reversal houses = {policy.get('reversal_houses')}. "
                         f"Aspect reversal applies ONLY to target houses {policy.get('aspected_reversal_houses', [])}; "
                         "it does not change the natal effect. Cancellation is neutral, not supportive.")
    return lines


def join_nakshatra_placements(payload):
    """Keep each planet's natal star and calculated D9 in one evidence row."""
    nakshatra = payload.get('nakshatra')
    if not isinstance(nakshatra, dict):
        return
    d1, d9 = nakshatra.pop('P1', {}), nakshatra.pop('P9', {})
    nakshatra['planet_facts'] = {
        planet: {'D1': d1.get(planet, {}), 'D9': d9.get(planet, {})}
        for planet in dict.fromkeys([*d1, *d9])
    }


def role_relationship_basis(facts):
    """Resolve relative houses and Moon/Sun frames before interpretation."""
    chart = (facts.get('charts') or {}).get('D1') or {}
    planets = chart.get('planets') or {}
    result = []
    for house, row in (chart.get('houses') or {}).items():
        target, placement = int(house), row.get('lord_house')
        if isinstance(placement, int):
            result.append(f"D1 H{target} lord {row['lord']} in natal H{placement}: "
                          f"lord is {(placement-target)%12+1}th from its house; "
                          f"house is {(target-placement)%12+1}th from lord. "
                          "Natal house number is not this relative distance.")
    for origin in ('Moon', 'Sun'):
        sign = (planets.get(origin) or {}).get('sign_name')
        if sign in SIGN_NAMES:
            i = SIGN_NAMES.index(sign)
            result.append(f"{origin} reference: H1={sign}, H7={SIGN_NAMES[(i+6)%12]}, "
                          f"H10={SIGN_NAMES[(i+9)%12]}. These are reference houses, not exaltation.")
    return result


FACT_USE_CONTRACT = '''
FACT USE: Keep natal placement, house lordship, compound friendship, reference-frame
house, dasha-lord Tara, and dated transit as separate types. Never convert between
them. A BAV score does not assert a transit. A natal house number does not assert a
relative house distance. A sign number does not assert a house. Self means self,
not great_friend. Use the directional compound friendship matrix, not dignity.
Within this same response, check each factual clause against its exact source row
before writing the interpretation. Delete unsupported clauses and their conclusions.
Do not supply remembered facts to fill a section. Do not guarantee predicted events.
An undated PD has no supplied end date: never borrow the AD end for the MD-AD-PD
sequence. KP planet_significators and four_step_house_unions are different sets:
name the four-step chain explicitly when using its extra houses. Apply these checks
to bullets and final summaries as well as analysis.
'''


def normalize_sudarshana_summaries(payload):
    """Drop filtered static summaries which disagree with calculator agreement rows.

    The compact topic rows omit outer planets while the calculator's agreement
    includes them. Keep the calculator as the sole static count source; current
    dasha activation is a separate calculation and must remain intact.
    """
    sx = payload.get('sx') or {}
    for topic in ('topic', 'career', 'relationship', 'education', 'health'):
        if topic in sx:
            sx[topic] = {'hs': sx[topic].get('hs', [])}
    for key in ('dom', 'patterns'):
        sx.pop(key, None)


def normalize_writer_frames(jaimini, av, facts):
    """Eliminate numeric sign/house aliases; join every AV chart to its own ascendant."""
    import copy
    authority = jaimini.get('frame_authority')
    if authority:
        # PS/JP/CK and jx numeric shortcuts duplicate the authoritative joins.
        jaimini['jaimini'] = {k: v for k, v in jaimini.get('jaimini', {}).items()
                              if k not in ('PS', 'JP', 'CK')}
        jx = jaimini.get('jx') or {}
        jaimini['jx'] = {k: v for k, v in jx.items() if k in ('dk_asp', 'amk_ak')}
        for topic in ('career', 'relationship'):
            if topic in jx:
                jaimini['jx'][topic] = {k: v for k, v in jx[topic].items()
                    if not isinstance(v, (int, float)) and k not in ('img', 'rf')}
        # Keep source authority intact for diagnostics; present named signs to writers.
        named = copy.deepcopy(authority)
        named['arudha_reference'] = {
            'calculation_chart': 'D1',
            'd9_arudhas_calculated': False,
            'rule': 'A7/UL signs and natal_house are D1 calculations. D9 occupants of these signs do not make them D9 arudhas or move their signs.'}
        for group in ('karakas', 'special_lagnas'):
            for row in named[group].values():
                sign = row.pop('sign', None)
                if isinstance(sign, int) and 1 <= sign <= 12:
                    row['sign_name'] = SIGN_NAMES[sign-1]
        for level in ('chara_md', 'chara_ad'):
            row = named[level]
            sign = row.pop('s', None)
            if isinstance(sign, int) and 1 <= sign <= 12:
                row['sign_name'] = SIGN_NAMES[sign-1]
            if 'y' in row:
                row['duration_years'] = row.pop('y')
        jaimini['frame_authority'] = named
    charts = {}
    for code, chart in facts.get('charts', {}).items():
        rows = {h: {'sign': row['sign'], 'SAV': row['SAV'], 'BAV': row.get('BAV_by_planet', {})}
                for h, row in chart.get('houses', {}).items() if 'SAV' in row}
        if rows:
            charts[code] = rows
    if charts:
        # Replaces duplicate raw sign-indexed arrays, not an additional copy.
        av['ashtakavarga'] = {'indexing': 'chart -> natal house within THAT chart -> sign/SAV/BAV',
                             'charts': charts}


def clarify_school_fact_types(nakshatra, kp, av, facts):
    """Name unlike fact types rather than asking the writer to decode aliases."""
    names = {'nk': 'nakshatra_name', 'ni': 'nakshatra_index', 'pd': 'nakshatra_pada',
             'h': 'house_in_this_chart', 'sn': 'sign_name', 'nl': 'nakshatra_lord'}
    nk = nakshatra.get('nakshatra') or {}
    for planet, charts in nk.get('planet_facts', {}).items():
        for code, row in list(charts.items()):
            named = {names.get(k, k): v for k, v in row.items()}
            source = facts.get('charts', {}).get(code, {})
            planet_row = source.get('planets', {}).get(planet, {})
            house = str(planet_row.get('house'))
            sign_lord = source.get('houses', {}).get(house, {}).get('lord')
            if sign_lord:
                named['sign_lord'] = sign_lord
            for key in ('dignity', 'gandanta', 'vargottama'):
                if key in planet_row:
                    named[key] = planet_row[key]
            charts[code] = named
    dt = nk.get('DT') or {}
    nk['DT'] = {'type': 'natal nakshatra of active dasha lord, NOT transit',
        'natal_moon_nakshatra': dt.get('mk'), 'periods': {
            level: {'planet': row.get('p'), 'natal_nakshatra': row.get('nk'),
                    'tara_number': row.get('tn'), 'tara_name': row.get('tl'), 'quality': row.get('q')}
            for level, row in dt.items() if isinstance(row, dict)}}
    kp['KP_significators_reading_basis'] = [
        f"{planet} KP significator houses = {houses}. This is NOT its D1 lordship."
        for planet, houses in facts.get('kp', {}).get('planet_significators', {}).items()]
    ax = av.get('ax') or {}
    if 'transit' in ax:
        ax['event_planet_house_scores'] = {'type': 'hypothetical house scoring, NOT a current transit position',
                                           **ax.pop('transit')}
    av['dated_transit_segments'] = facts.get('transit_segments', {})
