"""Shared two-chart evidence and user-stated context, sent exactly once per call."""
from copy import deepcopy


RELATIONAL_FACT_RULES = """
SHARED CONTEXT: relationship, relational_evidence, user_facts and history are supplied
either in cached shared context or SHARED_RELATIONAL_CONTEXT_JSON. Consult them in
every branch and the merge. user_facts are user-reported statements, not calculated
chart facts or independently verified claims. Their owner is the chart on which
they were saved; named subjects within a statement retain their own identities.
Do not convert an earlier prediction or an allegation about someone into a fact.
Do not claim to know another person's private thoughts, future feelings or actions.
Keep native and partner chart identities, house reference frames and period levels
separate. If evidence is missing, describe the limitation without inventing it.
The question's premise and saved reports are not confirmation of wrongdoing, shame,
suffering or another person's motives. Acknowledge reported actions without
endorsing the interpretation. Do not give dates for private emotional reactions
or describe one person's alleged moral superiority as a calculated chart result.
For remarriage questions distinguish possible relationship themes from a guaranteed
event. Give only the timing resolution actually supported by dated evidence.
Practical advice should support clear communication, wellbeing and children's
stability, not using children or public displays to pressure another person.
"""


def build_relational_shared(context, profile, evidence, history):
    # The evidence builder embeds the same profile; store one canonical copy.
    spine = deepcopy(evidence)
    spine.pop('profile', None)
    facts = {}
    supplied = context.get('user_facts') or {}
    # Upstream already selects categories. Preserve every distinct supplied fact;
    # never silently truncate a long-running user's relationship history.
    for category, rows in supplied.items():
        if not isinstance(rows, list):
            continue
        seen = set()
        kept = []
        for row in rows:
            if not isinstance(row, str) or not row.strip():
                continue
            key = ' '.join(row.split())
            if key not in seen:
                kept.append(row)
                seen.add(key)
        if kept:
            facts[category] = kept
    owner = ((context.get('native') or {}).get('birth_details') or {}).get('name')
    return {
        'relationship': deepcopy(profile),
        'relational_evidence': spine,
        'user_facts': {'source': 'user_reported', 'saved_on_chart': owner,
                       'by_category': facts},
        'history': deepcopy(history or []),
    }


def relational_call_payload(payload, shared, *, cached):
    """Cache failure must preserve exactly the evidence that a cache hit supplies."""
    result = {k: v for k, v in payload.items() if k not in shared}
    if not cached:
        result.update(shared)
    return result
