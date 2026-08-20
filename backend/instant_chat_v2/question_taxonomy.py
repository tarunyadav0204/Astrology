"""Coverage contract for real-user Instant Chat questions.

This module is deliberately declarative.  It does not inspect or classify user
text at runtime; semantic classification remains owned by the multilingual LLM
router.  The registry exists so planning, calculator coverage, answer shape and
evaluation cannot silently drift apart.
"""

from __future__ import annotations

from typing import Any, Dict


QUESTION_OPERATIONS: Dict[str, Dict[str, Any]] = {
    "chart_fact": {
        "answer_mode": "factual_chart_lookup",
        "purpose": "Return an exact calculated chart or dasha fact without turning it into a prediction.",
        "required_answer": ["direct fact", "chart/system reference when useful"],
        "forbidden": ["invented interpretation", "generic life reading", "unsupported date"],
        "examples": [
            "What is my Moon sign?",
            "When does my Mercury mahadasha start?",
            "Explain my D12 chart",
            "Read my Karkamsa",
            "Interpret my Swamsa chart",
            "मेरी कुंडली में गुरु किस भाव में है?",
        ],
    },
    "explanation": {
        "answer_mode": "explanation_mechanism",
        "purpose": "Explain or correct how an earlier astrological conclusion was reached.",
        "required_answer": ["direct explanation", "exact evidence chain", "correction if overstated"],
        "forbidden": ["fresh broad reading", "defending an unsupported earlier claim"],
        "examples": ["Why did you say October is stronger?", "Aapne promotion kaise predict ki?"],
    },
    "trait_or_nature": {
        "answer_mode": "trait_nature",
        "purpose": "Describe temperament, behavior, communication or pressure response.",
        "required_answer": ["core nature", "observable behavior", "strength", "caution"],
        "forbidden": ["current dasha dominating a natal trait answer", "flattery-only prose"],
        "examples": ["What kind of person am I?", "Mera gussa kaisa hai?"],
    },
    "person_profile": {
        "answer_mode": "relationship_person",
        "purpose": "Describe a spouse, child or relative through the correct derived frame.",
        "required_answer": ["named subject framing", "temperament", "relating style", "caution"],
        "forbidden": ["calling derived evidence the other person's own chart", "wrong relative house"],
        "examples": ["What will my spouse be like?", "Meri saas ka nature kaisa hai?"],
    },
    "topic_outlook": {
        "answer_mode": "topic_reading",
        "purpose": "Answer how a life area is functioning without a bounded calendar window.",
        "required_answer": ["plain verdict", "likely manifestations", "support", "friction", "practical direction"],
        "forbidden": ["house-number dump", "whole-life drift", "unasked exact timing"],
        "examples": ["How is my career?", "Meri wife ke saath relationship kaisa hai?"],
    },
    "period_outlook": {
        "answer_mode": "timing_window",
        "purpose": "Describe a named day, month, year or rolling period in one life area.",
        "required_answer": ["overall verdict", "phase changes", "real-life outcomes", "best use", "caution"],
        "forbidden": ["one static dasha summary for a long period", "dates without meaning"],
        "examples": ["How is my career this year?", "अगले 6 महीने मेरी सेहत कैसी रहेगी?"],
    },
    "event_likelihood_or_timing": {
        "answer_mode": "event_prediction",
        "purpose": "Assess whether/when a specific material event is supported.",
        "required_answer": ["natal promise", "dasha permission", "transit delivery", "ranked windows", "conditional verdict"],
        "forbidden": ["certainty from activation alone", "invented date", "current dasha only when a later window is stronger"],
        "examples": ["When will I get married?", "Will I get promoted this year?", "Naukri kab milegi?"],
    },
    "capacity_or_fit": {
        "answer_mode": "potential_capacity",
        "purpose": "Assess aptitude, promise, suitability or sustainable capacity.",
        "required_answer": ["core capacity", "best-fit expression", "limitation", "practical direction"],
        "forbidden": ["confusing ability with current timing", "generic encouragement"],
        "examples": ["Am I suited for business?", "Can I succeed as a lawyer?"],
    },
    "comparison_or_choice": {
        "answer_mode": "comparison_choice",
        "purpose": "Compare every named option using option-specific evidence.",
        "required_answer": ["each option", "relative support", "distinct risk", "recommendation or explicit close call"],
        "forbidden": ["soft winner without score separation", "shared evidence presented as option-specific"],
        "examples": ["Promotion or job change?", "Business karun ya naukri?"],
    },
    "problem_diagnosis": {
        "answer_mode": "problem_diagnosis",
        "purpose": "Explain why an area is blocked, delayed, unstable or repeatedly difficult.",
        "required_answer": ["real-life diagnosis", "current cause", "trigger if supported", "handling"],
        "forbidden": ["generic reassurance", "automatic remedy dump", "unsupported causal certainty"],
        "examples": ["Why is my career stuck?", "Paise tikte kyun nahi hain?"],
    },
    "action_guidance": {
        "answer_mode": "topic_reading",
        "purpose": "Give practical action within the supported chart/timing evidence.",
        "required_answer": ["what to do now", "what to avoid", "why it fits the present phase"],
        "forbidden": ["pretending every action request is a remedy request", "fatalistic instruction"],
        "examples": ["What should I focus on in my job now?", "Ab mujhe kya karna chahiye?"],
    },
    "remedy_follow_up": {
        "answer_mode": "remedy_action",
        "purpose": "Answer only an explicit Remedies CTA follow-up with a bounded remedy plan.",
        "required_answer": ["priority problem", "few relevant remedies", "one caution"],
        "forbidden": ["remedy mode inferred from wording alone", "large generic remedy list"],
        "examples": ["Show my remedies", "Open the remedy you suggested"],
    },
    "location_recommendation": {
        "answer_mode": "location_recommendation",
        "purpose": "Recommend relocation scope/place/direction for a stated goal.",
        "required_answer": ["scope", "ranked location qualities or places", "goal-specific rationale", "limitations"],
        "forbidden": ["inventing India/abroad scope", "confusing where with when"],
        "examples": ["Where should I move for my career?", "Which city abroad suits me for wealth?"],
    },
    "compatibility": {
        "answer_mode": "dedicated_partnership_flow",
        "purpose": "Evaluate two people only when both chart identities are resolved.",
        "required_answer": ["both charts", "bond strengths", "friction pattern", "practical relationship guidance"],
        "forbidden": ["calling a one-chart derived reading compatibility", "guessing the second person"],
        "examples": ["Are Deepika and I compatible?", "Hum dono ki marriage compatibility kaisi hai?"],
    },
    "muhurat_or_election": {
        "answer_mode": "dedicated_muhurat_flow",
        "purpose": "Find a suitable date/time for an action using the dedicated electional calculator.",
        "required_answer": ["event", "location/timezone", "ranked slots", "blocking and supportive factors"],
        "forbidden": ["using a personal event-prediction window as a muhurat", "exact slot without location"],
        "examples": ["Best date to register my company?", "Griha pravesh ka muhurat batao"],
    },
    "multi_part": {
        "answer_mode": "compound_plan",
        "purpose": "Detect materially different asks before calculation and ask the user to choose one question.",
        "required_answer": ["brief acknowledgement", "one-question-at-a-time request"],
        "forbidden": ["running calculators", "answering only the easiest part", "mixing evidence across parts"],
        "examples": ["When does Mercury dasha start and how will it affect my career?"],
    },
}


LIFE_DOMAINS: Dict[str, Dict[str, Any]] = {
    "general": {"aliases": ["timing"], "divisionals": ["D1", "D9"]},
    "career": {"aliases": ["job", "promotion"], "divisionals": ["D1", "D10"]},
    "business": {"aliases": [], "divisionals": ["D1", "D10"]},
    "marriage": {"aliases": ["spouse", "partner"], "divisionals": ["D1", "D9"]},
    "relationship": {"aliases": ["love"], "divisionals": ["D1", "D9"]},
    "wealth": {"aliases": ["money", "finance", "gain", "wish"], "divisionals": ["D1", "D2", "D11"]},
    "health": {"aliases": ["disease"], "divisionals": ["D1", "D3", "D30"]},
    "property": {"aliases": ["home"], "divisionals": ["D1", "D4"]},
    "progeny": {"aliases": ["child", "children", "pregnancy", "son", "daughter"], "divisionals": ["D1", "D7"]},
    "education": {"aliases": ["learning"], "divisionals": ["D1", "D24"]},
    "foreign": {"aliases": ["travel", "visa"], "divisionals": ["D1", "D4", "D12"]},
    "mother": {"aliases": [], "divisionals": ["D1", "D12"]},
    "father": {"aliases": [], "divisionals": ["D1", "D12"]},
    "siblings": {"aliases": [], "divisionals": ["D1", "D3"]},
    "family": {"aliases": [], "divisionals": ["D1", "D12"]},
    "spirituality": {"aliases": ["soul", "purpose", "dharma"], "divisionals": ["D1", "D9", "Karkamsa", "Swamsa"]},
    "vehicles": {"aliases": [], "divisionals": ["D1", "D4"]},
    "self": {"aliases": ["temperament", "personality"], "divisionals": ["D1", "D9"]},
    "life_purpose": {"aliases": ["calling"], "divisionals": ["D1", "D9", "Karkamsa", "Swamsa"]},
    "employment": {"aliases": ["job_search", "selection"], "divisionals": ["D1", "D10"]},
    "authority": {"aliases": ["promotion", "leadership"], "divisionals": ["D1", "D10"]},
    "job_change": {"aliases": ["resignation", "role_change"], "divisionals": ["D1", "D10"]},
    "project": {"aliases": ["launch", "execution"], "divisionals": ["D1", "D10"]},
    "income": {"aliases": ["salary", "compensation"], "divisionals": ["D1", "D2", "D10", "D11"]},
    "debt": {"aliases": ["loan", "repayment"], "divisionals": ["D1", "D2"]},
    "investment": {"aliases": ["trading", "speculation"], "divisionals": ["D1", "D2", "D5"]},
    "inheritance": {"aliases": ["insurance", "settlement"], "divisionals": ["D1", "D2", "D8"]},
    "separation": {"aliases": ["divorce", "reconciliation"], "divisionals": ["D1", "D9"]},
    "exams": {"aliases": ["competitive_exam"], "divisionals": ["D1", "D24"]},
    "immigration": {"aliases": ["relocation"], "divisionals": ["D1", "D4", "D12"]},
    "location": {"aliases": ["place_recommendation"], "divisionals": ["D1", "D4", "D10", "D12"]},
    "mental_wellbeing": {"aliases": ["emotional_wellbeing"], "divisionals": ["D1", "D9", "D30"]},
    "surgery": {"aliases": ["operation"], "divisionals": ["D1", "D6", "D8", "D30"]},
    "accident": {"aliases": ["injury"], "divisionals": ["D1", "D3", "D8", "D30"]},
    "recovery": {"aliases": ["rehabilitation", "rehab"], "divisionals": ["D1", "D6", "D30"]},
    "legal": {"aliases": ["litigation", "court"], "divisionals": ["D1", "D6", "D10"]},
    "competition": {"aliases": ["rivals", "enemies"], "divisionals": ["D1", "D6"]},
    "reputation": {"aliases": ["public_standing"], "divisionals": ["D1", "D10"]},
    "government": {"aliases": ["official", "authority"], "divisionals": ["D1", "D10"]},
    "friends": {"aliases": ["network", "community"], "divisionals": ["D1", "D11"]},
    "creativity": {"aliases": ["arts"], "divisionals": ["D1", "D5"]},
    "sports": {"aliases": ["athletics"], "divisionals": ["D1", "D3", "D10"]},
    "research": {"aliases": ["occult"], "divisionals": ["D1", "D8", "D9"]},
    "karma": {"aliases": ["repeating_patterns"], "divisionals": ["D1", "D9", "D60"]},
    "retirement": {"aliases": [], "divisionals": ["D1", "D10", "D12"]},
    "adoption": {"aliases": ["stepchildren"], "divisionals": ["D1", "D7"]},
    "muhurat": {"aliases": ["election"], "divisionals": ["D1"]},
}


CONVERSATION_STATES: Dict[str, Dict[str, Any]] = {
    "clear_first_turn": {
        "required": "Calculate immediately when subject, operation and material event/domain are clear.",
        "example": "How is my career this year?",
    },
    "ambiguous_reference": {
        "required": "Ask one natural clarification; never guess the person or event.",
        "example": "Will he come back?",
    },
    "clarification_reply": {
        "required": "Merge the short answer into dialogue state and never repeat the resolved question.",
        "example": "spouse",
    },
    "correction": {
        "required": "Replace the earlier assumption, retain the correction, then ask only the next material unknown.",
        "example": "Not my boyfriend—my husband.",
    },
    "contextual_follow_up": {
        "required": "Resolve ellipsis from recent dialogue and answer the new operation without restarting.",
        "example": "Why? And after that?",
    },
    "insufficient_chart_data": {
        "required": "State what cannot be calculated and request only the missing chart/person input.",
        "example": "Are we compatible? (only one chart selected)",
    },
    "high_stakes_or_blocked": {
        "required": "Apply the safety policy while preserving useful, non-diagnostic guidance.",
        "example": "Will this lump become cancer?",
    },
}


ROUTER_CATEGORY_LABELS = {
    label
    for canonical, contract in LIFE_DOMAINS.items()
    for label in (canonical, *contract.get("aliases", []))
}


def covered_domain_labels() -> set[str]:
    labels: set[str] = set()
    for canonical, contract in LIFE_DOMAINS.items():
        labels.add(canonical)
        labels.update(str(alias) for alias in contract.get("aliases", []))
    return labels
