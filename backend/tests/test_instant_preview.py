import json
import pytest
from instant_chat_v2.preview import _CONTEXT_LABELS, _SCRIPTS, build_instant_preview, read_instant_preview


def packet():
    return {
        "query_plan": {"route_action": "answer", "category": "career", "answer_mode": "event_prediction",
                       "target_subject": {"key": "self"}, "time_scope": {"as_of": "2026-10-01"}},
        "evidence_ledger": {"records": [{"evidence_id": "ev-001", "kind": "current_dasha",
            "value": {"as_of": "2026-10-01", "levels": {
                "md": {"planet": "Saturn", "natal_house": 10},
                "ad": {"planet": "Ketu", "natal_house": 5},
                "pd": {"planet": "Saturn", "natal_house": 10}}}}]},
    }


def routed(language="english"):
    return {"response_language": language, "response_script": _SCRIPTS.get(language, "latn")}


@pytest.mark.parametrize("language", list(_CONTEXT_LABELS))
def test_production_dictionary_shape_localizes_only_calculated_inputs(language):
    preview = build_instant_preview(packet(), routed(language))
    assert preview["language"] == language
    assert len(preview["rows"]) == 3
    assert preview["source"] == "calculation"
    assert all(row["evidence_id"] == "ev-001" for row in preview["rows"])
    assert "{" not in preview["content"]
    assert preview["title"] != preview["answer_label"]


def test_legacy_list_shape_is_supported_too():
    p = packet()
    p["evidence_ledger"]["records"][0]["value"]["levels"] = [{"level":"mahadasha", "planet":"Saturn"}]
    preview = build_instant_preview(p, routed())
    assert preview["rows"][0]["text"] == "Major period: Saturn"


@pytest.mark.parametrize("change", [
    {"response_language":"swahili"}, {"response_language":""},
    {"response_language":"tamil", "response_script":"latn"},
    {"response_language":"chinese", "response_script":"hant"},
    {"response_script":""}, {"target_subject_keys":["self","partner"]},
])
def test_no_guessed_language_or_multi_subject_facts(change):
    assert build_instant_preview(packet(), {**routed(), **change}) is None


def test_roman_hindi_preserves_latin_script():
    preview = build_instant_preview(packet(), {"response_language":"hindi", "response_script":"latn"})
    assert preview["language"] == "hinglish"
    assert "Shani" in preview["content"]


@pytest.mark.parametrize("field,value", [
    ("route_action","clarify"), ("target_subject", {"key":"spouse"}),
    ("interpretation_frame","native_chart_derived_house"),
    ("answer_mode","topic_reading"), ("time_scope", {"retrospective":True}),
])
def test_no_wrong_subject_or_irrelevant_timing(field, value):
    p=packet(); p["query_plan"][field]=value
    assert build_instant_preview(p,routed()) is None


def test_dates_are_explicit_and_facts_never_become_predictions():
    p=packet()
    p["verdict"]={"direction":"supported_natal_promise"}
    p["evidence_ledger"]["records"][0]["value"]["as_of"]="2028-01-01"
    preview=build_instant_preview(p,routed())
    assert preview["as_of"] == "2028-01-01"
    assert "currently" not in preview["content"]
    assert "supports" not in preview["content"]
    assert read_instant_preview(json.dumps([preview])) == preview
    assert read_instant_preview('bad json') is None


def test_stream_transport_hides_metadata_at_every_chunk_boundary():
    from utils.response_transport import visible_instant_stream_text
    body="A calculated explanation."
    for sentinel in ("NEXT_ACTION_META:","PREDICTION_ANCHOR_META:"):
        for length in range(1,len(sentinel)+1):
            assert visible_instant_stream_text(body+'\n'+sentinel[:length]) == body
        assert visible_instant_stream_text(body+'\n'+sentinel+'{"internal":true}') == body
    assert visible_instant_stream_text(body+' [[HOME_FACT') == body
