"""Plain-language rendering of deterministic Prashna evidence."""
from __future__ import annotations

from typing import Dict


HEADINGS = {
    "favorable": "The chart supports this outcome",
    "unfavorable": "The chart shows serious obstacles",
    "mixed": "The chart gives a mixed answer",
    "cannot_judge": "The chart does not give a dependable answer",
}

OUTCOME_LABELS = {
    ("relationship", "contact"): "renewed contact",
    ("relationship", "unblock"): "contact being reopened",
    ("relationship", "reconcile"): "reconciliation after the conflict",
    ("relationship", "return"): "a return to the relationship",
    ("marriage", "marriage"): "marriage with this person",
    ("marriage", "proposal"): "this marriage proposal",
}


def build_presentation(classical: Dict) -> Dict:
    result = classical["result"]
    outcome = OUTCOME_LABELS.get((classical.get("topic"), classical.get("intent")), "this outcome")
    matched = [row for row in classical["rules"] if row["matched"]]
    helps = [row["plain"] for row in matched if row["polarity"] == "support"]
    blocks = [row["plain"] for row in matched if row["polarity"] == "obstruction"]
    if result == "favorable":
        summary = "The applicable rules support the matter, and no decisive obstruction was found in this topic module."
        decision = "You may treat this as traditional support for proceeding, while still checking the real-world facts."
    elif result == "unfavorable":
        summary = "The applicable rules show obstruction, and no supporting rule resolved it."
        decision = "Do not treat the hoped-for outcome as secure. Address the practical obstacle or keep another option ready."
    elif result == "mixed":
        summary = "Some applicable rules support the matter and others obstruct it. The selected text supplies no precedence that resolves this conflict."
        decision = "Proceed only if the practical facts are acceptable. This chart does not justify a confident yes or no."
    else:
        summary = "None of the implemented rules for this question produces a decisive indication. The system will not manufacture an answer."
        decision = "Decide from practical evidence or ask a qualified practitioner to examine the preserved chart. Do not recast the same question for a different answer."
    heading = HEADINGS[result]
    if (classical.get("topic"), classical.get("intent")) in OUTCOME_LABELS:
        heading = {
            "favorable": f"The chart supports {outcome}",
            "unfavorable": f"The chart shows serious obstacles to {outcome}",
            "mixed": f"The chart is mixed about {outcome}",
            "cannot_judge": f"The chart does not give a dependable answer about {outcome}",
        }[result]
    return {"heading": heading, "summary": summary.replace("the matter", outcome),
            "supporting_points": helps[:3], "blocking_points": blocks[:3],
            "decision_guidance": decision,
            "tradition_label": "Traditional Praśnatantra–Tājika indication",
            "limits": "Use this traditional reading together with the facts of your situation. It cannot guarantee what will happen."}
