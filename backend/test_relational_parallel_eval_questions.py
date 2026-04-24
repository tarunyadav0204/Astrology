import json
from pathlib import Path

from ai.parallel_chat.relational_payloads import build_relationship_profile


def test_relational_eval_question_taxonomy_contract():
    path = Path(__file__).parent / "testdata" / "relational_parallel_eval_questions.json"
    cases = json.loads(path.read_text(encoding="utf-8"))

    assert len(cases) >= 30
    for case in cases:
        profile = build_relationship_profile(
            {"relationship": {"raw_label": case["relationship"]}},
            case["question"],
        )
        assert profile["event_topic"] == case["event_topic"], case
        assert profile["relation_family"] == case["relation_family"], case
        assert profile["answer_policy"]["do_not_force_compatibility_sections"] is True
