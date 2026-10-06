from classical_rules.contextual import ContextualRuleSpec
from classical_rules.deva_keralam.chapter_01 import PILOT_SPEC, evaluate_book_01
import pytest


def _facts(**overrides):
    facts = {
        "deva_keralam.ascendant.nadiamsa.sign_name": "Capricorn",
        "deva_keralam.ascendant.nadiamsa.ordinal": 32,
        "deva_keralam.ascendant.nadiamsa.name": "Kaalaa",
        "deva_keralam.ascendant.nadiamsa.half": "former",
        "deva_keralam.ascendant.nadiamsa.birth_time_precision_warning": False,
    }
    facts.update(overrides)
    return {"classical_facts": facts}


def _result(chart):
    return evaluate_book_01(chart)["results"][0]


def test_exact_pilot_match_returns_source_outcome_and_every_premise():
    row = _result(_facts())
    assert row["applicability"] == "matched"
    assert row["source"]["reference"] == "Deva Keralam, Book 1, verses 2497–2498"
    assert row["source"]["pdf_pages"] == [240]
    assert row["source"]["printed_pages"] == [225]
    assert row["source"]["editorial_status"] == "reviewed_clear"
    assert row["evidence"]["match_kind"] == "exact"
    assert len(row["evidence"]["premises"]) == 4
    assert row["evidence"]["inherited_context"]["ascendant_nadiamsa_ordinal"] == 32
    assert row["evidence"]["inherited_context"]["movable_sign_degree_range"] == "6°12′–6°24′"
    assert all("Jupiter" not in premise["key"] for premise in row["evidence"]["premises"])
    assert row["evidence"]["outcome"]["topic"] == "physical_description"
    assert row["evidence"]["outcome"]["traditional_results"] == [
        "The native is described as having a blood-red complexion.",
        "The native is described as having a medium build.",
        "The native is described as having a weak body.",
    ]
    assert row["evidence"]["outcome"]["timing"] is None


def test_known_anchor_mismatch_is_not_a_partial_prediction():
    row = _result(_facts(**{"deva_keralam.ascendant.nadiamsa.sign_name": "Aquarius"}))
    assert row["applicability"] == "not_matched"
    assert row["evidence"]["prefiltered"] is True
    assert "outcome" not in row["evidence"]


def test_non_anchor_premise_mismatch_is_not_matched():
    row = _result(_facts(**{"deva_keralam.ascendant.nadiamsa.half": "latter"}))
    assert row["applicability"] == "not_matched"
    assert "outcome" not in row["evidence"]
    assert any("deva_keralam.ascendant.nadiamsa.half" in reason for reason in row["evidence"]["failed_premises"])


@pytest.mark.parametrize("reliability", [False, None])
def test_unreliable_or_missing_precision_is_unavailable(reliability):
    chart = _facts()
    if reliability is None:
        chart["classical_facts"].pop("deva_keralam.ascendant.nadiamsa.birth_time_precision_warning")
    else:
        chart["classical_facts"]["deva_keralam.ascendant.nadiamsa.birth_time_precision_warning"] = not reliability
    row = _result(chart)
    assert row["applicability"] == "unavailable"
    assert "does not establish" in row["evidence"]["reason"]
    assert "outcome" not in row["evidence"]


def test_missing_required_chart_fact_is_unavailable_not_negative():
    chart = _facts()
    chart["classical_facts"].pop("deva_keralam.ascendant.nadiamsa.name")
    row = _result(chart)
    assert row["applicability"] == "unavailable"
    assert "outcome" not in row["evidence"]


def test_pilot_stays_out_of_global_registry_until_book_release_is_complete():
    # The pilot uses the production engine contract but is not surfaced as a
    # certified whole-book pack while coverage is knowingly incomplete.
    from classical_rules.registry import list_packs

    assert all(row["work_key"] != "deva_keralam" for row in list_packs())


def test_published_rule_cannot_use_unreviewed_or_defective_text():
    with pytest.raises(ValueError, match="non-executable editorial status"):
        ContextualRuleSpec(
            key="DK.TEST.BAD_TEXT",
            title="Bad text",
            source=PILOT_SPEC.source,
            expression={"op": "fact", "key": "x", "comparator": "equals", "value": 1},
            outcome={"topic": "test"},
            editorial_status="editor_says_ignore",
        )
