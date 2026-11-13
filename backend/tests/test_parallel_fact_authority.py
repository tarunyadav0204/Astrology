from ai.parallel_chat.fact_authority import jaimini_frame_authority, divisional_lord_authority, clarify_jaimini_payload


def test_model_projection_removes_ambiguous_direction_keys_without_losing_argala():
    payload = {'jaimini': {'AG': {'10': {'n': 168.49, 'g': 1, 'ap': [], 'vp': []}}},
               'jx': {'rf': {'AL': {'md': 7, 'ad': 8}}}}
    clarify_jaimini_payload(payload)
    assert 'AG' not in payload['jaimini']
    assert payload['frame_authority']['argala_by_natal_target_house']['10']['net_strength'] == 168.49
    assert 'rf' not in payload['jx']
    assert 'Natal target house 10: Argala net support (168.49)' in payload['reading_basis'][0]


def test_reading_basis_disambiguates_al_direction_and_argala_balance():
    payload = {'jaimini': {'PS': {'Asc': {'s': 5}}, 'JP': {'AL': {'s': 7}},
                          'AG': {'10': {'n': 168.49, 'g': 1, 'ap': [], 'vp': [
                              {'p': 'Mercury', 'k': 10, 'rs': 83.9},
                              {'p': 'Rahu', 'k': 3, 'rs': 0}]}}},
               'chara_dasha': {'P': [{'s': 1, 'ic': True, 'ad': [{'s': 2, 'ic': True}]}]}}
    clarify_jaimini_payload(payload)
    assert payload['reading_basis'][0] == 'AL is in Libra: natal house 3; house 7 from Chara MD; house 6 from Chara AD.'
    assert 'net support (168.49)' in payload['reading_basis'][1]
    assert 'positive-strength obstruction contributors: Mercury' in payload['reading_basis'][1]
    assert 'zero-strength obstruction contributors: Rahu' in payload['reading_basis'][1]


def test_jaimini_prompt_uses_actual_argala_schema_without_legacy_example():
    from ai.parallel_chat.prompt_blocks import build_jaimini_branch_static_agent
    prompt = build_jaimini_branch_static_agent()
    assert 'relationships.argala_analysis' not in prompt
    assert 'promising easy gains' not in prompt
    assert 'reading_basis' in prompt


def test_natal_sign_and_both_chara_frames_are_distinct():
    payload = {'jaimini': {'CK': {'AmK': {'p': 'Saturn', 's': 6, 'h': 2}},
                           'PS': {'Asc': {'s': 5}}, 'JP': {'AL': {'s': 7}}},
               'chara_dasha': {'P': [{'s': 1, 'nm': 'Aries', 'ic': True, 'y': 11,
                                     'ds': '2026-03-22', 'ad': [{'s': 2, 'ic': True}]}]}}
    result = jaimini_frame_authority(payload)
    assert result['karakas']['AmK'] == {
        'planet': 'Saturn', 'sign': 6, 'natal_house': 2,
        'house_from_chara_md': 6, 'house_from_chara_ad': 5}
    assert result['chara_md']['ds'] == '2026-03-22'
    assert result['chara_md']['y'] == 11
    assert result['chara_md']['natal_house'] == 9
    assert result['chara_ad']['natal_house'] == 10
    assert result['chara_ad']['house_from_chara_md'] == 2
    assert result['special_lagnas']['AL'] == {'sign': 7, 'natal_house': 3}
    assert result['sign_frames']['Capricorn']['natal_house'] == 6
    assert result['sign_frames']['Capricorn']['house_from_chara_md'] == 10


def test_argala_preserves_target_and_zero_strength_obstruction():
    result = jaimini_frame_authority({'jaimini': {'AG': {'1': {
        'n': 232.34, 'g': 1, 'ap': [{'p': 'Saturn', 'k': 2, 'rs': 62.64}],
        'vp': [{'p': 'Rahu', 'k': 12, 'rs': 0.0}]}}}})
    target = result['argala_by_natal_target_house']['1']
    assert target['support'][0]['house_from_target'] == 2
    assert target['obstruction'] == []
    assert target['zero_strength_obstruction'] == [{'planet': 'Rahu', 'house_from_target': 12, 'strength': 0.0}]
    assert target['net_strength'] == 232.34


def test_divisional_lords_do_not_inherit_d1_or_ascendant_lord():
    result = divisional_lord_authority({'px': {'dx': {'career': {'charts': {'D10': {'rows': [
        {'h': 1, 's': 7, 'lord': 'Venus', 'lord_h': 3, 'occ': []},
        {'h': 10, 's': 4, 'lord': 'Moon', 'lord_h': 5, 'occ': ['Rahu']},
    ]}}}}}})
    assert result['D10']['10'] == {'house': 10, 'sign': 'Cancer', 'house_lord': 'Moon',
                                    'lord_house_in_this_chart': 5, 'lord_sign_in_this_chart': 'Aquarius',
                                    'occupants': ['Rahu']}
    assert result['D10']['1']['house_lord'] == 'Venus'
    assert divisional_lord_authority({}) == {}


def test_missing_active_period_does_not_invent_relative_houses():
    result = jaimini_frame_authority({'jaimini': {'CK': {'AK': {'p': 'Moon', 's': 6, 'h': 2}}}})
    assert result['chara_md'] == {}
    assert result['karakas']['AK']['house_from_chara_md'] is None
    assert result['karakas']['AK']['house_from_chara_ad'] is None


def test_jaimini_aspects_and_tenth_occupants_are_not_inferred_from_support_bands():
    payload = {'jaimini': {'PS': {'Asc': {'s': 3}, 'Venus': {'s': 4}, 'Mars': {'s': 8}},
                          'JP': {'A7': {'s': 5}}},
               'chara_dasha': {'P': [{'s': 5, 'ic': True, 'ad': [{'s': 9, 'ic': True}]}]}}
    clarify_jaimini_payload(payload, {'7': [0, 3, 9], '2': [5, 8, 11]})
    frames = payload['frame_authority']['sign_frames']
    assert frames['Scorpio']['rashi_aspects_to_signs'] == ['Aries', 'Cancer', 'Capricorn']
    assert frames['Gemini']['rashi_aspects_to_signs'] == ['Virgo', 'Sagittarius', 'Pisces']
    assert frames['Sagittarius']['houses_from_special_lagnas']['A7'] == 5
    assert 'Chara MD Leo: 10th from this period is Taurus; occupants: none.' in payload['reading_basis']
    assert 'Chara AD Sagittarius: 10th from this period is Virgo; occupants: none.' in payload['reading_basis']


def test_calculated_lookup_preserves_chart_house_sign_scores_and_period_levels():
    from ai.parallel_chat.fact_authority import calculated_fact_authority
    context = {
        'd1_chart': {'houses': [{'sign': 1}], 'planets': {'Saturn': {'sign_name': 'Taurus', 'house': 1}},
                     'graha_drishti_by_house': {'1': [{'planet': 'Mars'}]}},
        'divisional_charts': {'d9_navamsa': {'division_number': 9, 'divisional_chart': {
            'houses': [{'sign': 4, 'house_number': 7}, {'sign': 8, 'house_number': 11}],
            'planets': {'Jupiter': {'sign_name': 'Pisces', 'house': 2, 'dignity': 'own_sign'}}}}},
        'ashtakavarga': {'d9_navamsa': {'sarvashtakavarga': {'sarvashtakavarga': {'4': 28, '8': 37}}}},
        'current_dashas': {'mahadasha': {'planet': 'Saturn'},
                          'antardasha': {'planet': 'Venus', 'start': '2024-08-30'},
                          'maha_dashas': [{'planet': 'Mercury', 'start': '2036-11-09'}]},
        'special_points': {'gandanta_analysis': {'planets_in_gandanta': []}},
        'kp_analysis': {'planet_lords': {'Mercury': {'star_lord': 'Jupiter', 'sub_lord': 'Venus'}},
                        'planet_significators': {'Jupiter': [2, 7, 8, 9, 12]}},
        'macro_transits_timeline': {'Jupiter': [{'sign': 'Leo', 'house': 4, 'start_date': '2026-11-11'}]},
    }
    facts = calculated_fact_authority(context)
    assert facts['charts']['D9']['houses']['7']['SAV'] == 28
    assert facts['charts']['D9']['houses']['11']['SAV'] == 37
    assert facts['charts']['D9']['planets']['Jupiter']['sign_name'] == 'Pisces'
    assert facts['charts']['D1']['houses']['1']['graha_aspects_received'] == [{'planet': 'Mars'}]
    assert facts['charts']['D1']['planets']['Saturn']['gandanta'] is False
    assert facts['vimshottari']['antardasha']['planet'] == 'Venus'
    assert facts['vimshottari']['mahadasha_sequence'][0]['planet'] == 'Mercury'
    assert facts['kp']['planet_significators']['Jupiter'] == [2, 7, 8, 9, 12]
    assert facts['transit_segments']['Jupiter'][0]['sign'] == 'Leo'


def test_missing_gandanta_and_sav_are_unknown_not_false_or_zero():
    from ai.parallel_chat.fact_authority import calculated_fact_authority
    facts = calculated_fact_authority({'d1_chart': {
        'houses': [{'sign': 0}], 'planets': {'Mars': {'house': 1}}}})
    assert 'gandanta' not in facts['charts']['D1']['planets']['Mars']
    assert 'SAV' not in facts['charts']['D1']['houses']['1']


def test_reading_basis_distinguishes_occupant_lord_and_natal_vs_aspect_reversal():
    from ai.parallel_chat.fact_authority import fact_reading_basis
    facts = {'charts': {'D7': {'houses': {'7': {'sign': 'Taurus', 'lord': 'Venus',
             'lord_house': 1, 'occupants': ['Mercury']}}}},
             'vimshottari': {'antardasha': {'planet': 'Venus', 'end': '2027-10-31'},
                            'pratyantardasha': {'planet': 'Saturn'}}}
    special = {'yogi_points': {'yogi': {'lord': 'Ketu'}, 'duplicate_yogi': {'lord': 'Mars'},
               'avayogi': {'lord': 'Rahu'}, 'avayogi_effect_policy': {
                   'placement_house': 2, 'reversal_houses': [3, 6, 8, 12], 'aspected_reversal_houses': [8],
                   'natal_effect': {'polarity': 'challenging', 'rule': 'ordinary_avayogi_obstruction'}}}}
    lines = fact_reading_basis(facts, special)
    assert 'lord is Venus in D7 house 1; occupants (not lords) = Mercury' in lines[0]
    assert 'pratyantardasha: Saturn; start = not supplied; end = not supplied' in lines[2]
    assert 'NATAL effect = challenging' in lines[-1]
    assert 'ONLY to target houses [8]' in lines[-1]


def test_nakshatra_join_retains_actual_d9_beside_natal_pada():
    from ai.parallel_chat.fact_authority import join_nakshatra_placements
    payload = {'nakshatra': {'P1': {'Mercury': {'nk': 'Punarvasu', 'pd': 3}},
                            'P9': {'Mercury': {'sn': 'Gemini', 'h': 7}}, 'DT': {'md': 'Moon'}}}
    join_nakshatra_placements(payload)
    assert payload['nakshatra']['planet_facts']['Mercury'] == {
        'D1': {'nk': 'Punarvasu', 'pd': 3}, 'D9': {'sn': 'Gemini', 'h': 7}}
    assert 'P1' not in payload['nakshatra'] and 'P9' not in payload['nakshatra']
    assert payload['nakshatra']['DT'] == {'md': 'Moon'}


def test_kp_chain_union_does_not_inherit_the_cusp_house_number():
    from ai.parallel_chat.fact_authority import calculated_fact_authority
    facts = calculated_fact_authority({'kp_analysis': {'cusp_lords': {'10': {'sub_lord': 'Jupiter'}},
        'four_step_theory': {'Jupiter': {'planet': {'houses': [2, 7, 8, 9, 12]},
          'star_lord': {'houses': [2, 3, 6, 7, 8]}, 'sub_lord': {'houses': [1, 2, 5]},
          'sub_sub_lord': {'houses': [2]}}}}})
    assert facts['kp']['four_step_house_unions']['Jupiter'] == [1, 2, 3, 5, 6, 7, 8, 9, 12]


def test_relative_house_basis_distinguishes_natal_number_from_distance():
    from ai.parallel_chat.fact_authority import role_relationship_basis
    rows = role_relationship_basis({'charts': {'D1': {
        'houses': {'7': {'lord': 'Jupiter', 'lord_house': 6}},
        'planets': {'Moon': {'sign_name': 'Sagittarius'}, 'Sun': {'sign_name': 'Cancer'}}}}})
    assert 'lord is 12th from its house; house is 2th from lord' in rows[0]
    assert 'Moon reference: H1=Sagittarius, H7=Gemini, H10=Virgo' in rows[1]
    assert 'Sun reference: H1=Cancer, H7=Capricorn, H10=Aries' in rows[2]


def test_writer_frames_use_named_jaimini_signs_and_chart_specific_av_houses():
    from ai.parallel_chat.fact_authority import normalize_writer_frames
    jm = {'jaimini': {'PS': {}, 'JP': {}, 'CK': {}, 'a': 'jaimini'},
          'jx': {'md': 7, 'ad': 8, 'ul2': {'s': 8}, 'relationship': {'dk': 4, 'md': 'obstructed'}},
          'frame_authority': {'special_lagnas': {'UL': {'sign': 7, 'natal_house': 8}},
              'karakas': {}, 'chara_md': {'s': 7, 'y': 9, 'natal_house': 8}, 'chara_ad': {}}}
    av = {'ashtakavarga': {'D9': {'S9': [1, 2, 3]}}}
    facts = {'charts': {'D9': {'houses': {'7': {'sign': 'Gemini', 'SAV': 23, 'BAV_by_planet': {'Moon': 4}}}}}}
    normalize_writer_frames(jm, av, facts)
    assert jm['frame_authority']['chara_md'] == {'sign_name': 'Libra', 'duration_years': 9, 'natal_house': 8}
    assert jm['jx'] == {'relationship': {'md': 'obstructed'}}
    assert 'PS' not in jm['jaimini']
    assert av['ashtakavarga']['charts']['D9']['7'] == {'sign': 'Gemini', 'SAV': 23, 'BAV': {'Moon': 4}}
    assert 'D9' not in av['ashtakavarga']


def test_school_fact_types_separate_star_lord_sign_lord_and_transit_scores():
    from ai.parallel_chat.fact_authority import clarify_school_fact_types
    nk = {'nakshatra': {'planet_facts': {'Venus': {'D9': {'sn': 'Capricorn', 'h': 1, 'nl': 'Sun'}}},
                       'DT': {'mk': 'Swati', 'md': {'p': 'Saturn', 'nk': 'Rohini', 'tn': 8, 'tl': 'Mitra', 'q': 'supportive'}}}}
    kp, av = {}, {'ax': {'transit': {'event_planet': 'Saturn', 'rows': [{'h': 7, 'b': 1}]}}}
    facts = {'charts': {'D9': {'planets': {'Venus': {'house': 1, 'dignity': 'neutral'}},
                              'houses': {'1': {'lord': 'Saturn'}}}},
             'kp': {'planet_significators': {'Jupiter': [2, 7, 8, 9, 12]}},
             'transit_segments': {'Saturn': [{'sign': 'Pisces', 'house': 1}]}}
    clarify_school_fact_types(nk, kp, av, facts)
    row = nk['nakshatra']['planet_facts']['Venus']['D9']
    assert row['nakshatra_lord'] == 'Sun' and row['sign_lord'] == 'Saturn'
    assert nk['nakshatra']['DT']['periods']['md']['tara_name'] == 'Mitra'
    assert 'transit' not in av['ax']
    assert av['dated_transit_segments']['Saturn'][0]['house'] == 1
    assert '[2, 7, 8, 9, 12]' in kp['KP_significators_reading_basis'][0]


def test_nakshatra_prompt_does_not_recalculate_tara_or_request_final_presentation():
    from ai.parallel_chat.prompt_blocks import build_nakshatra_branch_static_agent
    prompt = build_nakshatra_branch_static_agent('marriage')
    assert 'GRATITUDE_OPENING' not in prompt
    assert 'FOLLOW_UP_STRUCTURE' not in prompt
    assert '**Compute**' not in prompt
    assert 'Copy DT.periods Tara number/name/quality exactly' in prompt
    assert 'nakshatra_lord and sign_lord are separate' in prompt


def test_sudarshana_filtered_counts_cannot_compete_with_calculator_counts():
    from ai.parallel_chat.fact_authority import normalize_sudarshana_summaries
    current = {'career': {'rows': [{'p': 'Mercury', 'agree': 1}]}}
    payload = {'sx': {'career': {'hs': [6], 'rows': [{'h': 6, 'agree': 2}],
                                'support': 'mixed'}, 'current': current},
               'calculated_house_agreement': [{'h': 6, 'agree': 3}]}
    normalize_sudarshana_summaries(payload)
    assert payload['sx']['career'] == {'hs': [6]}
    assert payload['sx']['current'] == current
    assert payload['calculated_house_agreement'] == [{'h': 6, 'agree': 3}]
