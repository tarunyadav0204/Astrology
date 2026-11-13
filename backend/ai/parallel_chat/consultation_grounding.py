"""Deterministic subject and evidence provenance for specialist and merge calls."""

CONSULTATION_GROUNDING_RULES = '''
CONSULTATION GROUNDING (takes precedence over voice/template examples):
- consultation_subject identifies the selected chart, not necessarily the person asking.
  Follow its address_mode throughout analysis, bullets, final verdict and NEXT_ACTION_META.
  named_chart means use the supplied name or "the native"; never attribute that chart's
  relationships, actions, dates or remedies to "you/your". A router's generic subject=self
  on an elliptical follow-up is not proof that the selected chart belongs to the user.
- Question premises, saved user reports, earlier assistant answers and specialist prose
  are NOT independently verified events. Astrology cannot establish whether someone had
  affairs, concealed something, betrayed a partner, or suffered public exposure. Do not
  explain why an unverified event happened as if it is established; do not add a current
  crisis, scandal, exposure, motives or moral character from chart symbolism/history.
- Answer the requested chart question substantively: distinguish calculated placements
  from conditional traditional interpretations. State once that the chart cannot verify
  the alleged behavior when that premise is material. Sustain that distinction throughout;
  an opening caveat does not license later factual accusations, inevitability, or proof.
  Dated dashas are calculated periods, not evidence that a claimed event occurred.
- chart_role_authority is chart-specific: lord_of_houses differs from occupied_house.
  Copy lordships for the explicitly named D1/D9/etc.; never transfer a divisional role
  into D1. Discard interpretations resting on incorrect roles or unverified behavior.
'''


def consultation_subject(context):
    birth = context.get('birth_details') or context.get('birth_data') or {}
    name = str(birth.get('name') or '').strip()
    # A named saved chart may belong to another person. Missing identity binding
    # must not be filled using the intent router's default "self" label.
    is_self = str(birth.get('relation') or '').strip().lower() == 'self'
    return {'chart_name': name or 'the selected native',
            'address_mode': 'self' if is_self else 'named_chart',
            'identity_basis': 'saved_chart_relation' if is_self else 'selected_chart_name',
            'verified_real_world_events': [],
            'history_evidence_status': 'conversation only; claims are not verified events'}


def chart_role_authority(calculated_facts):
    """Small reverse join of already-calculated houses; no new astrology math."""
    result = {}
    for code, chart in (calculated_facts.get('charts') or {}).items():
        houses = chart.get('houses') or {}
        planets = chart.get('planets') or {}
        result[code] = {
            'ascendant_sign': (houses.get('1') or {}).get('sign'),
            'planets': {
                planet: {'lord_of_houses': sorted(int(h) for h, row in houses.items() if row.get('lord') == planet),
                         'occupied_house': row.get('house'), 'sign': row.get('sign_name'),
                         'dignity': row.get('dignity'), 'neecha_bhanga': row.get('neecha_bhanga')}
                for planet, row in planets.items()
                if planet in {'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'}
            },
        }
    return result


def final_grounding_instruction(subject):
    """Last-position instruction; scope applies after templates and copied history."""
    import json
    return '\n\nFINAL SUBJECT AND EVIDENCE CHECK:\n' + json.dumps(subject, ensure_ascii=False) + '''
Before emitting this SAME answer (no tool/review call), check these requirements:
1. Use the selected chart subject and address_mode above, including metadata.
   For named_chart, NEXT_ACTION_META must be type=none (no personal remedy offer).
   Never use "you", "your" or "Show my remedies" for the chart subject.
2. The supplied calculations verify ZERO real-world private events. Earlier answers,
   questions and branch analyses do not change that. If this is a question about alleged
   conduct, explicitly say the chart cannot establish whether that conduct occurred.
3. Do not claim "exposure", "secrets", "crisis", "scandal", "other interests", wrongdoing
   or their timing as an actual or inevitable event. Explain neutral relationship themes
   conditionally instead. Do not claim moral character or deficient commitment from dignity.
   Reject branch interpretations that smuggle the allegation back in through those synonyms.
   Do not state that the native currently faces relationship problems or needs to correct
   private conduct: no such event/state is verified. Do not attribute a predisposition
   toward infidelity, clandestine relationships, romantic variety, seeking other partners,
   deficient commitment or sexual motives to a real person from placements. Calling such
   claims "potential" or "symbolic" does not make them supported. Discuss neutral themes
   such as communication, emotional needs, responsibilities and privacy without using
   those themes as a disguised explanation for the allegation. The final verdict must
   say whether the allegation is supported: it is NOT established by this chart.
   Use "traditionally may symbolize"
   for interpretations, rather than "confirms", "forces", "demands" or "is undergoing".
4. Any cited planet's lordships must match chart_role_authority for THAT chart; name the
   chart when switching D1/D9. When discussing a planet across both charts, explicitly
   contrast its D1 and D9 lordships from the table. Occupying house 1 does not make
   a planet the 1st lord. A7/UL natal-house rows refer to D1; do not invent D9 arudhas.
   Dasha-lord Tara is natal star compatibility, NOT a current transit.
5. Keep the answer useful and chart-specific. Separate exact placements from interpretations;
   do not replace the reading with a refusal. These rules also govern every bullet and verdict.
'''


def focused_branch_instruction(branch, chart_code, *, death_analysis_unlocked=False):
    """A chart-specific follow-up must not inherit a generic all-topic reading task."""
    from chat.system_instruction_config import death_ethics_block
    from utils.admin_settings import get_parallel_branch_word_limit
    school = {
        'parashari': 'Use calculated chart placements, dignity, house lords and the relevant supplied dasha. Read fact_reading_basis and chart_role_authority first.',
        'jaimini': 'Use frame_authority. Its A7/UL/Argala/natal-house rows are D1 unless explicitly labeled otherwise. KL is the AK sign in D9, not the AK placement in D1. Keep projections into another chart explicitly labeled; never recalculate arudhas.',
        'nakshatra': 'Use joined planet_facts and DT. Distinguish D1 natal stars from D9 stars and dasha-lord Tara from transits. Never infer a star from its sign alone.',
    }[branch]
    return death_ethics_block(death_analysis_unlocked) + f'''
You are the {branch} specialist for a chart-specific follow-up about {chart_code}.
Answer the CURRENT QUESTION in the context of the user's preceding question.
Stay within {chart_code}; D1 is a labeled comparison only. Do not start unrelated
career or other-topic sections merely because extra charts/calculations are supplied.
{school}
Concrete placements and lordships must be copied from the supplied authorities.
For a planet discussed across charts, name each chart's lordships independently.
Do not turn an occupied house into a lordship or a symbol into an observed event.
Neecha-bhanga is cancellation of debilitation, not own-sign dignity. Copy each chart's dignity.
For the natural significator central to the question, explicitly state its D1 and
requested-chart lordships from chart_role_authority before interpreting its placement.
A yogi/avayogi natal policy applies to its stated natal chart, not a divisional placement.
You may omit irrelevant facts. If evidence is absent, do not invent it.
Return only JSON: {{"branch":"{branch}","analysis":"...","bullets":["..."]}}.
Keep analysis within about {get_parallel_branch_word_limit(branch)} words.
''' + CONSULTATION_GROUNDING_RULES


NAMED_CHART_NEXT_ACTION = """
Selected chart is not identified as the user's own. Do not offer a personal remedy
CTA. Append NEXT_ACTION_META with type="none", empty title/reason, and empty
follow_up_questions. This does not request a remedy reading or alter the question.
""".strip()
