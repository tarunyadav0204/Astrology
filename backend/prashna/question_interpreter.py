"""Closed, structured question catalogue for the production Prashna flow."""
from __future__ import annotations

from typing import Dict, List

from prashna.source_ledger import SUPPORTED_TOPICS


TOPICS = {
    "relationship": {"label": "Love, contact & reconciliation", "matter_house": 7,
        "roles": {1: "You", 7: "The other person or relationship"}},
    "career": {"label": "Job or career outcome", "matter_house": 10,
        "roles": {1: "You", 10: "The job or professional outcome"}},
    "wealth": {"label": "Payment or gain", "matter_house": 2,
        "roles": {1: "You", 2: "The payment or gain"}},
    # Marriage remains a separate calculation module, but its questions are
    # grouped under Love & relationship in the public catalogue.
    "marriage": {"label": "Marriage proposal", "matter_house": 7, "public": False,
        "roles": {1: "You", 7: "The prospective spouse or proposal"}},
    "travel": {"label": "Planned journey", "matter_house": 9,
        "roles": {1: "You", 9: "The journey", 7: "The destination", 4: "How it concludes", 10: "Its purpose"}},
    "lost": {"label": "Missing possession", "matter_house": 4,
        "roles": {1: "You", 2: "Your possession", 4: "The missing item", 7: "Another party"}},
    "property": {"label": "Property transaction", "matter_house": 4,
        "roles": {1: "The buyer", 4: "The property", 7: "The seller", 11: "Profit from sale"}},
}


def question(group: str, topic: str, intent: str, text: str) -> Dict:
    return {"group": group, "topic": topic, "intent": intent, "text": text}


GUIDED_QUESTIONS = {
    "career_job_offer": question("career", "career", "outcome", "Will I receive the specific job offer I am considering?"),
    "career_promotion": question("career", "career", "outcome", "Will I receive the specific promotion I am asking about?"),
    "career_application": question("career", "career", "outcome", "Will my application for this specific position succeed?"),
    "career_employer_change": question("career", "career", "outcome", "Will changing to this specific employer work out?"),
    "wealth_overdue_payment": question("wealth", "wealth", "outcome", "Will this specific overdue payment be received?"),
    "wealth_money_owed": question("wealth", "wealth", "outcome", "Will the specific money owed to me be recovered?"),
    "wealth_expected_gain": question("wealth", "wealth", "outcome", "Will this defined expected financial gain be received?"),
    "relationship_contact": question("relationship", "relationship", "contact", "Will this specific person call or message me?"),
    "relationship_unblock": question("relationship", "relationship", "unblock", "Will this specific person unblock me?"),
    "relationship_reconcile": question("relationship", "relationship", "reconcile", "Will this specific person and I reconcile after our fight?"),
    "relationship_return": question("relationship", "relationship", "return", "Will this specific person return to our relationship?"),
    "relationship_marriage": question("relationship", "marriage", "marriage", "Will this specific person marry me?"),
    "marriage_proposal": question("relationship", "marriage", "proposal", "Will this specific marriage proposal proceed?"),
    "marriage_prospective_spouse": question("relationship", "marriage", "marriage", "Will marriage with this specific prospective spouse proceed?"),
    "travel_planned_journey": question("travel", "travel", "outcome", "Will this specific planned journey take place?"),
    "travel_visa_journey": question("travel", "travel", "outcome", "Will this specific visa-related journey take place?"),
    "lost_recovery": question("lost", "lost", "outcome", "Will this specific missing possession be recovered?"),
    "lost_find_item": question("lost", "lost", "outcome", "Will I find the specific item that is currently missing?"),
    "property_purchase": question("property", "property", "buy", "Will this specific property purchase complete?"),
    "property_sale": question("property", "property", "sell", "Will this specific property sale complete profitably?"),
}


def resolve_guided_question(question_id: str) -> Dict:
    """Resolve an immutable UI choice; no text classification is performed."""
    key = (question_id or "").strip()
    if key not in GUIDED_QUESTIONS:
        raise ValueError("Choose one of the supported Prashna questions before casting the chart.")
    selected = GUIDED_QUESTIONS[key]
    topic, intent, text = selected["topic"], selected["intent"], selected["text"]
    spec = TOPICS[topic]
    return {
        "status": "selected",
        "question_id": key,
        "original_question": text,
        "topic": topic,
        "topic_label": TOPICS[selected["group"]]["label"],
        "intent": intent,
        "roles": [{"house": house, "role": role} for house, role in spec["roles"].items()],
    }


def public_topics() -> List[Dict]:
    rows = []
    for topic, spec in TOPICS.items():
        if spec.get("public", True) is False:
            continue
        questions = [{"id": key, "text": item["text"]} for key, item in GUIDED_QUESTIONS.items()
                     if item["group"] == topic]
        if not questions:
            continue
        rows.append({"id": topic, "label": spec["label"], "matter_house": spec["matter_house"],
                     "questions": questions})
    return rows


assert set(TOPICS).issubset(SUPPORTED_TOPICS)
