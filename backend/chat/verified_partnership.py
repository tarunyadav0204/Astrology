"""Two-chart Verified evidence and calculator ownership; Luna supplies the reading."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

PARTNERSHIP_CAPABILITIES = {
    'parashari.vimshottari_periods': 'Exact Vimshottari MD/AD/PD periods for one or both people. Requires start_date and end_date, at most 20 years; dates use each person’s local birth timezone.',
    'parashari.dated_transits': 'Transit planetary positions and natal-house overlays at 12:00 UTC on start_date for one or both charts. A snapshot, not a continuous event window.',
    'relationship.synastry': 'Raw cross-chart planetary separations and whole-sign overlays in both directions for D1 and D9. Use alongside each person’s own chart; no compatibility verdict is imposed.',
}

PARTNERSHIP_CONTRACT = """
VERIFIED TWO-CHART READING:
The user deliberately supplied two independent birth charts. The baseline labels them native
and partner with their names and relationship. Use both actual charts; do not replace the
partner chart with houses derived from the native chart or treat partner as an unknown spouse.
Keep each placement, lordship, dasha and transit attached to its owning person and chart.
Core D1/D9, topic-relevant vargas, Jaimini points and Chara periods, Nadi linkages,
nakshatra/pada/lord positions, Vimshottari and transit facts plus raw mutual geometry
are supplied upfront for each person. Inspect this multi-system evidence before concluding.
You are the analyst: choose relevant methods, reconcile evidence and make a direct prediction
when supported. You may request any registered calculator for native, partner or both, with
independent date ranges, divisions, houses and locations. Request extra evidence whenever it
helps resolve the question; do not turn the baseline into a fixed checklist or imposed verdict.
For shared-event timing, inspect both people's periods and relevant dated activations before
identifying overlap. A current snapshot is not a future transit calculation. Cross-chart angular
separation is geometry, not automatically a Parashari graha aspect or a compatibility score.
Respect the stated relationship: business partners, friends and family are not spouses.
If the relationship is unspecified and changes the answer, ask one focused clarification.
Answer the actual question with a clear conclusion, chart-specific reasons, useful timing when
supported and practical implications. Explain meaningful uncertainty or conflicting indications
without letting them erase a supported prediction. Never invent missing placements, dates,
calculator results or certainty. Do not force single-person spouse-description or unrelated
single-chart presentation contracts onto this two-person question.

DIRECT CONSULTATION VOICE:
You are speaking directly with the user as their astrologer. Treat the calculated chart facts
as your own analysis: "Your Moon is...", "In [name]'s D9...", "Comparing your charts, I see...",
"The Jaimini indicators suggest...". Never narrate the evidence-delivery process or refer to
"supplied information", "provided information", "supplied package", "provided data", packets,
inputs, calculator branches or what was sent to you. Do not attribute your chart reading to
an unseen provider. Say "The charts suggest..." rather than "The supplied package indicates...".
Keep the distinction between chart-derived findings and facts the user actually told you:
"You mentioned..." is appropriate for their history, plans or relationship details. Own the
interpretation without overstating certainty: explain uncertainty in the conclusion itself,
not as missing supplied information. Do not claim to know or calculate facts you do not have.

OUTPUT DEPTH:
For a substantive compatibility or partnership analysis, provide a developed reading with these
clearly titled sections (translate naturally into the requested language):
1. Overall outlook — directly answer the question and strongest likely development.
2. The two individual charts — each person's relevant strengths, needs and vulnerabilities.
3. How the charts interact — mutual house overlays and meaningful planetary connections.
4. Divisional-chart confirmation — explicitly interpret both D9 charts and any topic-relevant
   divisions, citing owning person, division and placement. Request additional vargas when needed:
   D10 for business/career, D7 for children, D4 for home/property, D12 for family/parents.
5. Jaimini perspective — relevant AK/DK/AmK, arudhas/Upapada and sign relationships; request
   jaimini.full_analysis or other Jaimini tools for missing aspects and confirmation.
6. Nadi perspective — relevant planetary linkage/dispositor chains for both people and how
   they reinforce or contradict the interaction. Nadi linkages are distinct from Nadi koota.
7. Nakshatra perspective — compare Moon and relevant planet nakshatras, padas and lords,
   relating them to temperament, communication and the question. Never invent koota scores.
8. Timing and shared activation — both Vimshottari and Chara periods, with dated transits
   when timing is requested; distinguish natal compatibility from event timing.
9. Strengths, friction and practical guidance — actionable implications tied to chart evidence.
10. Synthesis and confidence — what agrees across methods, conflicts and final prediction.
These sections set depth and coverage, not a predetermined verdict or a closed list.
You have full freedom to add any other useful section supported by the question and calculated
evidence, and to split, combine, reorder or rename sections for clarity while retaining relevant
multi-system coverage. Examples include emotional intimacy, communication, shared finances,
business roles, family dynamics, children, conflict resolution or specific future scenarios.
Choose additions yourself; do not ask the user for permission to improve the reading structure.
Keep headings relevant to
the stated relationship; omit unrelated life topics. A narrow factual follow-up may be shorter.
For substantive readings, do not collapse this into only three generic sections or merely name
schools: show concrete calculated evidence and explain its implications. If a method failed,
say what could not be established instead of inventing findings. Simple style still gets the
same evidence depth with explained terminology; technical style may include more placements.
Birth-time-sensitive vargas need caution when birth time is uncertain. Do not multiply confidence
by counting D1, D9, Nadi and nakshatra views of the same planet as independent guarantees.
"""


def validate_partner_birth_data(data: dict[str, Any]) -> None:
    for field in ('name', 'date', 'time', 'latitude', 'longitude'):
        if data.get(field) is None or data.get(field) == '':
            raise ValueError(f'Partner {field} is required for Verified partnership analysis')
    if not -90 <= float(data['latitude']) <= 90 or not -180 <= float(data['longitude']) <= 180:
        raise ValueError('Partner coordinates are out of range')


def _chart(birth_data):
    from calculators.chart_calculator import ChartCalculator
    profile = birth_data.get('calculation_profile') or {}
    return ChartCalculator({}).calculate_chart(
        SimpleNamespace(**birth_data),
        ayanamsha=profile.get('ayanamsha', birth_data.get('ayanamsha') or 'lahiri'),
        node_type=profile.get('node_type', 'mean'),
    )


def cross_chart_geometry(native, partner):
    """Raw separations and whole-sign overlays, with no model-generated judgments."""
    contacts = []
    for a, ap in (native.get('planets') or {}).items():
        for b, bp in (partner.get('planets') or {}).items():
            if ap.get('longitude') is None or bp.get('longitude') is None:
                continue
            al, bl = float(ap['longitude']) % 360, float(bp['longitude']) % 360
            delta = abs(al - bl)
            contacts.append({'native_planet': a, 'partner_planet': b,
                'native_longitude': al, 'partner_longitude': bl,
                'separation_degrees': round(min(delta, 360 - delta), 4)})
    overlays = {}
    for owner, chart, reference, target in (
        ('native', native, 'partner', partner), ('partner', partner, 'native', native),
    ):
        asc = target.get('ascendant')
        if asc is None:
            continue
        asc_sign = int(float(asc) % 360 // 30)
        overlays[f'{owner}_planets_in_{reference}_houses'] = [
            {'planet': name, 'planet_owner': owner, 'house_owner': reference,
             'house': (int(float(p['longitude']) % 360 // 30) - asc_sign) % 12 + 1}
            for name, p in (chart.get('planets') or {}).items() if p.get('longitude') is not None
        ]
    return {'method': 'angular separation and whole-sign house overlay',
            'coordinate_frame': native.get('coordinate_frame') or 'sidereal D1',
            'contacts': contacts, 'overlays': overlays}


def build_partnership_context(*, birth_data, partner_birth_data, question, intent, history):
    from calculators.divisional_chart_calculator import DivisionalChartCalculator
    from calculators.base_calculator import BaseCalculator
    from calculators.transit_calculator import TransitCalculator
    from calculators.dasha_time import parse_birth_datetime
    from shared.dasha_calculator import DashaCalculator
    from utils.query_context import resolve_query_now
    validate_partner_birth_data(partner_birth_data)
    contexts, charts = {}, {}
    category = str((intent or {}).get('category') or '').lower()
    topic_divisions = {'business': 10, 'career': 10, 'job': 10, 'children': 7,
                       'property': 4, 'home': 4, 'family': 12, 'parents': 12}
    divisions = sorted({9, *([topic_divisions[category]] if category in topic_divisions else [])})
    query_context = (intent or {}).get('query_context') or {}
    now = resolve_query_now(query_context)
    for subject, data in (('native', birth_data), ('partner', partner_birth_data)):
        # Compute actual chart facts directly; no single-person composer verdicts
        # or derived-relative frames enter this two-person baseline.
        own_intent = {**(intent or {}), 'target_subject': 'self', 'target_subjects': []}
        d1 = _chart(data)
        asc_sign = int(float(d1['ascendant']) % 360 // 30)
        d1['house_lordships'] = {house: BaseCalculator.SIGN_LORDS[(asc_sign + house - 1) % 12]
                                  for house in range(1, 13)}
        d9_result = DivisionalChartCalculator(d1).calculate_divisional_chart(9)
        d9 = {**(d9_result.get('divisional_chart') or d9_result),
              'coordinate_frame': d9_result.get('coordinate_frame'), 'method': d9_result.get('method')}
        division_results = {'D9': d9_result}
        charts[subject] = {'D1': d1, 'D9': d9}
        for division in divisions:
            if division == 9:
                continue
            result = DivisionalChartCalculator(d1).calculate_divisional_chart(division)
            division_results[f'D{division}'] = result
            charts[subject][f'D{division}'] = result.get('divisional_chart') or result
        profile = data.get('calculation_profile') or {}
        ayanamsha = profile.get('ayanamsha', data.get('ayanamsha') or 'lahiri')
        dob = parse_birth_datetime(data)
        focus = now.astimezone(dob.tzinfo).replace(tzinfo=None) if dob.tzinfo else now.replace(tzinfo=None)
        dashas = DashaCalculator(ayanamsha).calculate_current_dashas(data, focus, strict=True)
        transits = TransitCalculator({}).calculate_transits(
            SimpleNamespace(**data), now.date().isoformat(), ayanamsha=ayanamsha,
            node_type=profile.get('node_type', 'mean'))
        contexts[subject] = {
            'intent_summary': own_intent, 'query_context': query_context,
            'natal_snapshot': d1, 'current_dashas': dashas,
            'current_transits': {'snapshot_at': now.date().isoformat() + 'T12:00:00Z', **transits},
            'instant_parashari': {'divisional_support': division_results},
        }
    pair = {'birth_data': {'native': birth_data, 'partner': partner_birth_data},
            'contexts': contexts, 'charts': charts, 'query_now': now.isoformat(),
            'relationship': partner_birth_data.get('partnership_relationship') or partner_birth_data.get('relationship') or '',
            'synastry': {division: cross_chart_geometry(charts['native'][division], charts['partner'][division])
                        for division in ('D1', 'D9')}}
    # Feed known multi-system foundations upfront; optional failures remain labelled
    # and do not suppress a usable two-chart reading or the model's extra tool requests.
    from calculators.nakshatra_calculator import NakshatraCalculator
    from chat.verified_chat_pipeline import _raw_calculations
    for subject in ('native', 'partner'):
        foundations = {}
        for capability in ('jaimini.significators_and_arudhas', 'jaimini.points',
                           'jaimini.chara_dasha', 'nadi.linkages'):
            parameters = {}
            if capability == 'jaimini.chara_dasha':
                from datetime import timedelta
                parameters = {'start_date': (now.date() - timedelta(days=366)).isoformat(),
                              'end_date': (now.date() + timedelta(days=366 * 3)).isoformat()}
            result = calculate_partnership_capability(pair, capability, subject, parameters)
            foundations[capability] = _raw_calculations(result['subjects'][subject])
            if capability == 'jaimini.chara_dasha':
                foundations[capability] = {**foundations[capability],
                                          'calculated_window': parameters,
                                          'additional_ranges_available': True}
        foundations['nakshatra.positions'] = NakshatraCalculator(
            chart_data=charts[subject]['D1']).calculate_nakshatra_positions()
        contexts[subject]['partnership_foundations'] = foundations
    return {**contexts['native'], 'verified_partnership': pair,
            'intent_summary': {**(intent or {}), 'mode': 'VERIFIED_PARTNERSHIP'}}


def build_partnership_baseline(pair):
    from chat.verified_chat_pipeline import build_verified_baseline, _historical_vimshottari_timeline
    subjects = {}
    for subject in ('native', 'partner'):
        data = pair['birth_data'][subject]
        subjects[subject] = {
            'chart_subject': subject, 'name': data.get('name'),
            'birth_chart_id': data.get('id') or data.get('birth_chart_id'),
            **build_verified_baseline(pair['contexts'][subject]),
            'core_charts': pair['charts'][subject],
            'multi_system_foundations': pair['contexts'][subject].get('partnership_foundations') or {},
            'historical_timing_evidence': {'vimshottari_md_ad_timeline': _historical_vimshottari_timeline(data)},
        }
    return {'calculation_packet_version': 'verified-two-chart-v2',
            'relationship': pair['relationship'], 'query_now': pair.get('query_now'),
            'subjects': subjects, 'synastry': pair['synastry']}


def calculate_partnership_capability(pair, capability, chart_subject, parameters):
    from chat.verified_chat_pipeline import _calculate_requested_capabilities, _capability_payloads
    if chart_subject not in ('native', 'partner', 'both'):
        raise ValueError('Choose native, partner or both')
    if capability == 'relationship.synastry':
        from chat.calculator_menu import CalculatorParameters
        args = CalculatorParameters.model_validate(parameters or {})
        divisions = args.divisions or [1, 9]
        if any(division not in (1, 9) for division in divisions):
            raise ValueError('Synastry supports D1 and D9; request other charts with divisional_confirmation')
        return {'chart_subject': 'both', 'result': {f'D{division}': pair['synastry'][f'D{division}'] for division in divisions}}
    results = {}
    for subject in ('native', 'partner') if chart_subject == 'both' else (chart_subject,):
        context = pair['contexts'][subject]
        try:
            if capability in {'parashari.vimshottari_periods', 'parashari.dated_transits'}:
                results[subject] = _calculate_dated_evidence(pair['birth_data'][subject], capability, parameters)
                continue
            results[subject] = _calculate_requested_capabilities(
                pair['birth_data'][subject], [capability], _capability_payloads(context), context, parameters,
            ).get(capability)
            if results[subject] in (None, {}, []):
                results[subject] = {'error': 'calculation_unavailable'}
        except Exception as exc:
            results[subject] = {'error': 'calculation_unavailable', 'detail': str(exc)[:200]}
    result = {'chart_subject': chart_subject, 'subjects': results}
    if all(isinstance(value, dict) and value.get('error') for value in results.values()):
        result['error'] = 'calculation_unavailable'
    return result


def _calculate_dated_evidence(birth_data, capability, parameters):
    from datetime import datetime, time
    from chat.calculator_menu import CalculatorParameters
    args = CalculatorParameters.model_validate(parameters or {})
    if args.start_date is None:
        raise ValueError('start_date is required')
    profile = birth_data.get('calculation_profile') or {}
    if capability == 'parashari.vimshottari_periods':
        from shared.dasha_calculator import DashaCalculator
        if args.end_date is None:
            raise ValueError('end_date is required')
        if (args.end_date - args.start_date).days > 366 * 20:
            raise ValueError('Request at most 20 years per calculation')
        rows = DashaCalculator(profile.get('ayanamsha', birth_data.get('ayanamsha') or 'lahiri')).get_dasha_periods_for_range(
            birth_data, datetime.combine(args.start_date, time.min),
            datetime.combine(args.end_date, time.min), strict=True,
        )
        return {'periods': rows, 'start_date': args.start_date.isoformat(),
                'end_date': args.end_date.isoformat(), 'timezone': birth_data.get('timezone'),
                'truncated': len(rows) >= 2000}
    if args.time is not None:
        raise ValueError('dated_transits supports the fixed 12:00 UTC snapshot only')
    from calculators.transit_calculator import TransitCalculator
    result = TransitCalculator({}).calculate_transits(
        SimpleNamespace(**birth_data), args.start_date.isoformat(),
        ayanamsha=profile.get('ayanamsha', birth_data.get('ayanamsha') or 'lahiri'),
        node_type=profile.get('node_type', 'mean'),
    )
    geometry = cross_chart_geometry(_chart(birth_data), result)
    contacts = [{'natal_planet': row['native_planet'], 'transit_planet': row['partner_planet'],
                 'natal_longitude': row['native_longitude'], 'transit_longitude': row['partner_longitude'],
                 'separation_degrees': row['separation_degrees']} for row in geometry['contacts']]
    return {'snapshot_at': args.start_date.isoformat() + 'T12:00:00Z',
            'transit_positions': result,
            'natal_contacts': contacts,
            'transit_planets_in_natal_houses': [
                {'planet': row['planet'], 'house': row['house']} for row in geometry['overlays'].get('partner_planets_in_native_houses', [])],
            'limitation': 'One 12:00 UTC snapshot, not a continuous transit window.'}


async def generate_verified_partnership_response(*, question, birth_data, partner_birth_data,
        intent, history, language, model_name, response_style='simple', stream_callback=None,
        calculation_callback=None):
    from chat.verified_chat_pipeline import run_verified_calculator_agent
    context = await asyncio.to_thread(build_partnership_context,
        birth_data=birth_data, partner_birth_data=partner_birth_data, question=question,
        intent=intent, history=history)
    result = await run_verified_calculator_agent(question=question, language=language,
        birth_data=birth_data, instant_context=context, history=history, model_name=model_name,
        timeout_s=180, response_style=response_style, stream_callback=stream_callback,
        calculation_callback=calculation_callback)
    result['verified_packet_validation'] = result.get('packet_validation') or {}
    result['follow_up_questions'] = []
    result['partnership_mode'] = True
    return result
