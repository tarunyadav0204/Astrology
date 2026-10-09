"""Question-scoped Prashna routing; persisted chart clocks are never client controlled."""
from datetime import datetime
from typing import Any, Dict


def apply_prashna_transition(intent: Dict[str, Any], question: str, context: Dict[str, Any]) -> Dict[str, Any]:
    from chat.verified_prashna import freeze_prashna
    qc = dict(context or {})
    previous = qc.get('_prashna_previous') or qc.get('prashna')
    transition = str(intent.get('reading_transition') or 'none')
    selected_method = qc.get('prashna_choice')
    # Explicit natal contracts and non-analysis routes cannot inherit question-chart evidence.
    if (selected_method == 'natal' or intent.get('reading_type') in {'chart_dasha_analysis', 'muhurat'} or intent.get('mode') == 'PREDICT_DAILY'
            or intent.get('route_action') in {'ack', 'handoff', 'out_of_scope'}):
        transition = 'natal'
    if transition == 'none' and qc.get('_prashna_previous') and not qc.get('prashna'):
        if selected_method == 'natal':
            transition = 'natal'
        elif qc.get('prashna_workflow_choice') == 'continue':
            transition = 'continue_prashna'
        elif qc.get('prashna_workflow_choice') == 'new':
            transition = 'natal'
            intent = {**intent, 'status': 'CLARIFY', 'route_action': 'clarify', 'prashna_intent': 'none',
                      'clarification_question': 'What would you like the new reading to address?'}
        else:
            transition = 'clarify_workflow'
    if transition == 'none' and qc.get('prashna'):
        # Compatibility for older router outputs: only a freshly selected method,
        # never a previous conversation's chart, can serve as the fallback.
        transition = 'new_prashna'
    if transition == 'continue_prashna' and not previous:
        transition = 'new_prashna'
    for key in ('prashna', 'prashna_requested', 'prashna_choice'):
        qc.pop(key, None)
    resolved = str(intent.get('resolved_question') or '').strip() or (qc.get('_clarification_context') if transition == 'none' else None) or question
    if transition == 'natal':
        qc.pop('prashna_location', None)
        # A new topic must not carry the old clarification chain into generation.
        resolved = question
    elif transition == 'clarify_workflow' and previous:
        intent = {**intent, 'status': 'CLARIFY', 'route_action': 'clarify',
                  'workflow_choice': True, 'prashna_intent': 'none',
                  'clarification_question': intent.get('clarification_question') or 'Select a card below to continue.'}
    elif transition in {'continue_prashna', 'new_prashna'}:
        if transition == 'continue_prashna':
            fixed = previous
            if not str(intent.get('resolved_question') or '').strip() and fixed.get('original_question') != question:
                resolved = f"{fixed.get('original_question') or ''}\nFollow-up: {question}"
        else:
            place = qc.get('prashna_location') or (previous or {}).get('location')
            if intent.get('requires_new_location') and not (selected_method == 'prashna' and qc.get('prashna_location')):
                place = None
            stamp = qc.get('_question_received_at')
            if not place or not stamp:
                # No confirmed current city: stop for the existing location-card flow.
                intent = {**intent, 'status': 'CLARIFY', 'route_action': 'clarify',
                          'prashna_intent': 'explicit',
                          'clarification_question': 'Select the Use Prashna card below to continue.'}
                fixed = None
            else:
                fixed = freeze_prashna(place, datetime.fromisoformat(stamp))
                fixed['original_question'] = resolved
        if fixed:
            qc.update(prashna=fixed, prashna_requested=True, prashna_choice='prashna')
            intent = {**intent, 'prashna_intent': 'none'}
    # Only pending workflow decisions carry the old chart as routing context.
    return {**intent, 'query_context': qc, 'reading_transition': transition, 'resolved_question': resolved}
