from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / "backend"))

from ai.intent_router import apply_foreign_routing_guards, apply_home_routing_guards  # noqa:E402
from chat.instant_chat_pipeline import (  # noqa:E402
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _build_instant_context,
    _mode_selection_from_intent,
    _requested_charts_from_intent,
    _validate_foreign_technical_explanation,
)
from instant_chat_v2.foreign import BOUNDARY_SUBTYPES, FOREIGN_PROFILES, TIMING_SUBTYPES  # noqa:E402
from instant_chat_v2.foreign_graph_policy import ForeignGraphPolicyStore  # noqa:E402
from instant_chat_v2.foreign_graph_runtime import compare_foreign_graph_policy  # noqa:E402
from instant_chat_v2.graph_live import apply_live_graph_policy, enforce_live_graph_answer  # noqa:E402
from instant_chat_v2.orchestrator import build_instant_v2_packet  # noqa:E402
from instant_chat_v2.translated_astrology import build_translated_astrology_contract, validate_translated_astrology_answer  # noqa:E402


def _context(key:str,*,timing:bool=False)->dict:
    policy=ForeignGraphPolicyStore().resolve(key);assert policy
    boundary=key in BOUNDARY_SUBTYPES
    availability={code.lower():not boundary and f"foreign:{code}" in policy.required_factors for code in ("D1","D3","D4","D9","D10","D12")}
    availability.update({"kp_fructification":timing,"scope_boundary":boundary,"pathway_evidence":key=="migration_pathway","option_evidence":key in {"stay_vs_relocate","temporary_vs_permanent","location_comparison"},"remedy_blueprint":key=="foreign_remedy"})
    return {"intent_summary":{"category":"foreign","foreign_subtype":key},"normalized_evidence":{"foreign_foundation":{"foreign_subtype":key,"houses_available":[int(x.split("H",1)[1]) for x in policy.required_factors if x.startswith("foreign:H")],"availability":availability,"route_synthesis":{"verdict":"qualified","evidence_complete":True},"timing_synthesis":{"dasha_evaluation_complete":timing,"transit_evaluation_complete":timing,"kp_fructification":{"complete":timing,"verdict":"supported"},"timing_windows":[{"start":"2027-01-01","end":"2027-02-01","transit_confirmed":True}] if timing else []}}}}


def test_foreign_ontology_compiles_and_covers_every_route()->None:
    result=subprocess.run([sys.executable,str(ROOT / "scripts" / "validate_foreign_life_ontology.py")],cwd=ROOT,capture_output=True,text=True,check=False)
    assert result.returncode==0,result.stderr
    assert "33 competency questions" in result.stdout
    assert set(ForeignGraphPolicyStore().runtime_keys())==set(FOREIGN_PROFILES)


def test_every_static_route_excludes_timing_and_every_timing_route_requires_triangulation()->None:
    store=ForeignGraphPolicyStore()
    for key in set(FOREIGN_PROFILES)-set(TIMING_SUBTYPES)-set(BOUNDARY_SUBTYPES):
        assert "foreign:DashaActivation" in store.resolve(key).default_exclusions,key
    for key in TIMING_SUBTYPES:
        policy=store.resolve(key);assert policy
        assert {"foreign:KPFructification","foreign:DashaActivation","foreign:TransitConfirmation"}.issubset(policy.required_factors)
        result=compare_foreign_graph_policy(category="foreign",query_plan={"category":"foreign","foreign_subtype":key,"answer_mode":"event_prediction"},observed_answer_mode="event_prediction",context=_context(key,timing=True))
        assert result and result["match"],(key,result)


def test_semantic_guards_keep_static_timing_and_boundaries_separate()->None:
    relocation={"category":"relocation","foreign_subtype":"domestic_relocation","answer_mode":"potential_capacity","needs_transits":True,"period_window":{"start":"2026-09-04"},"required_evidence":["transit_event_windows"]}
    apply_foreign_routing_guards(relocation)
    assert relocation["category"]=="relocation"
    assert relocation["answer_mode"]=="potential_capacity"
    assert relocation["needs_transits"] is False
    assert relocation["divisional_charts"]==["D1","D3","D4"]
    assert "period_window" not in relocation
    assert _requested_charts_from_intent(relocation,answer_mode="potential_capacity")==["D1","D3","D4"]

    timing={"category":"foreign","foreign_subtype":"foreign_residence","answer_mode":"event_prediction"}
    apply_foreign_routing_guards(timing)
    assert timing["foreign_subtype"]=="foreign_residence_timing"
    assert timing["divisional_charts"]==["D1","D4","D9","D12"]
    assert timing["needs_transits"] is True

    boundary={"category":"visa","foreign_subtype":"legal_immigration_handoff","answer_mode":"potential_capacity"}
    apply_foreign_routing_guards(boundary)
    assert boundary["route_action"]=="handoff"
    assert boundary["divisional_charts"]==[]


def test_typed_foreign_timing_cannot_fall_back_to_static_mode()->None:
    selection=_mode_selection_from_intent({"category":"foreign","foreign_subtype":"settlement_timing","answer_mode":"potential_capacity","route_action":"answer"})
    assert selection and selection["answer_mode"]=="event_prediction"


def test_cross_domain_ownership_and_legacy_home_transfer()->None:
    career={"category":"career","career_subtype":"foreign_career","answer_mode":"potential_capacity"}
    apply_foreign_routing_guards(career)
    assert "foreign_subtype" not in career
    assert career["category"]=="career"

    legacy={"category":"property","home_subtype":"foreign_handoff","answer_mode":"potential_capacity"}
    apply_home_routing_guards(legacy)
    assert legacy["category"]=="foreign"
    assert legacy["foreign_subtype"]=="foreign_residence"
    assert legacy["route_action"]=="answer"
    assert legacy["divisional_charts"]==["D1","D4","D9","D12"]


def test_travel_residence_and_settlement_are_distinct_compiled_routes()->None:
    store=ForeignGraphPolicyStore()
    travel=set(store.resolve("foreign_travel").required_factors)
    residence=set(store.resolve("foreign_residence").required_factors)
    settlement=set(store.resolve("permanent_settlement").required_factors)
    assert "foreign:D3" in travel and "foreign:D4" not in travel
    assert {"foreign:D4","foreign:D12"}.issubset(residence)
    assert {"foreign:D4","foreign:D12","foreign:H11"}.issubset(settlement)


def test_foreign_boundaries_are_deterministically_enforced()->None:
    expected={
        "location_recommendation_handoff":"best-country",
        "legal_immigration_handoff":"legal eligibility",
        "muhurat_handoff":"Muhurat",
        "travel_safety_handoff":"guarantee",
        "other_person_handoff":"another adult",
    }
    for key,phrase in expected.items():
        packet={"query_plan":{"category":"foreign","foreign_subtype":key,"answer_mode":"handoff"},"answer_spec":{},"verdict":{},"verification":{},"user_derivation":{}}
        result=apply_live_graph_policy(packet,intent={"category":"foreign","foreign_subtype":key},context=_context(key))
        answer=enforce_live_graph_answer("unsupported generated claim",result,language="english")
        assert phrase.lower() in answer.lower(),(key,answer)


def test_reference_relocation_question_has_complete_live_evidence()->None:
    birth={"name":"Tarun","date":"1980-04-02","time":"14:55:00","latitude":29.2396596,"longitude":75.8174505,"timezone":"UTC+5:30","place":"Hisar, Haryana, India"}
    intent={"category":"relocation","foreign_subtype":"domestic_relocation","answer_mode":"potential_capacity","query_context":{"as_of":"2026-09-04T10:00:00+05:30"}}
    apply_foreign_routing_guards(intent)
    context=_build_instant_context(birth,"Does my chart support relocation?",intent,[],answer_mode_override="potential_capacity",target_subject_override={"key":"self","label":"self","base_house":1})
    foundation=context["normalized_evidence"]["foreign_foundation"]
    assert foundation["availability"]["d1"] is True
    assert foundation["availability"]["d3"] is True
    assert foundation["availability"]["d4"] is True
    packet=build_instant_v2_packet(question="Does my chart support relocation?",intent=intent,answer_mode="potential_capacity",target_subject={"key":"self","label":"self","base_house":1},language="english",instant_context=context)
    result=apply_live_graph_policy(packet,intent=intent,context=context)
    policy=result["answer_spec"]["knowledge_graph_policy"]
    assert policy["domain"]=="foreign_life"
    assert policy["runtime_key"]=="domestic_relocation"
    assert policy["fallback_to_deeper_mode"] is False
    assert policy["missing_required_factors"]==[]


def test_reference_foreign_overview_preserves_cancer_chart_facts_in_composer()->None:
    birth={"name":"Tarun","date":"1980-04-02","time":"14:55:00","latitude":29.2396596,"longitude":75.8174505,"timezone":"UTC+5:30","place":"Hisar, Haryana, India"}
    question="What does my chart show about travel and foreign life?"
    intent={"category":"foreign","foreign_subtype":"foreign_overview","answer_mode":"topic_reading","query_context":{"as_of":"2026-09-04T20:16:00+05:30"}}
    apply_foreign_routing_guards(intent)
    context=_build_instant_context(birth,question,intent,[],answer_mode_override="topic_reading",target_subject_override={"key":"self","label":"self","base_house":1})
    packet=build_instant_v2_packet(question=question,intent=intent,answer_mode="topic_reading",target_subject={"key":"self","label":"self","base_house":1},language="english",instant_context=context)
    result=apply_live_graph_policy(packet,intent=intent,context=context)
    composer=_build_instant_composer_context(context,result)

    assert composer["native"]["ascendant"]["sign"]=="Cancer"
    assert composer["intent"]["foreign_subtype"]=="foreign_overview"
    foundation=composer["evidence"]["foreign_foundation"]
    assert foundation["charts"]["D1"]
    third_house=next(row for row in foundation["charts"]["D1"] if row["house"]==3)
    assert third_house["lord"]=="Mercury"
    assert third_house["lord_house"]==8
    assert composer["evidence"].get("current_timing") is None
    rules=composer["answer_contract"]["foreign_answer_rules"]
    assert rules["native_ascendant"]=="Cancer"
    assert rules["timing_route"] is False

    visible=build_translated_astrology_contract(composer,question=question,language="english",response_style="technical")
    assert visible["response_style"]=="technical"
    assert visible["technical_evidence_available"] is True
    assert visible["minimum_technical_references"]>=2
    composer["answer_contract"]["visible_astrology"]=visible
    prompt=_build_instant_composer_prompt_v3(question,composer,"english")
    assert "Technical mode must not collapse into a purely emotional or psychological narrative" in prompt

    nontechnical=(
        "Your chart supports foreign life because Rahu creates a hunger for unfamiliar places. "
        "You may feel more yourself abroad and carry two homes emotionally."
    )
    errors=validate_translated_astrology_answer(nontechnical,visible)
    assert any("technical style missing" in error for error in errors)


def test_static_foreign_answer_drops_wrong_identity_special_facts_and_timing()->None:
    context=_context("foreign_overview")
    context["birth_summary"]={"ascendant":{"sign":"Cancer"}}
    packet={"query_plan":{"category":"foreign","foreign_subtype":"foreign_overview","answer_mode":"topic_reading"},"answer_spec":{},"verdict":{},"verification":{},"user_derivation":{}}
    result=apply_live_graph_policy(packet,intent={"category":"foreign","foreign_subtype":"foreign_overview"},context=context)
    bad=(
        "Your chart does show real promise for travel and foreign life, but with conditions. "
        "Mercury, as the Yogi lord for your Virgo ascendant, supports short journeys. "
        "Mars sits in the Ashlesha-Magha Gandanta zone and affects long travel. "
        "Your current Saturn-Rahu-Saturn period reinforces this through sudden ambition. "
        "Foreign life may involve adjustment, so leave room for transition."
    )
    clean=enforce_live_graph_answer(bad,result,language="english")
    for forbidden in ("Virgo", "Yogi", "Gandanta", "Saturn-Rahu-Saturn", "current"):
        assert forbidden.lower() not in clean.lower()
    assert "real promise" in clean
    assert "leave room for transition" in clean


def test_open_ended_foreign_travel_when_returns_the_calculated_conditional_window()->None:
    birth={"name":"ABC","date":"1980-04-02","time":"14:55:00","latitude":29.2396596,"longitude":75.8174505,"timezone":"UTC+5:30","place":"Hisar, Haryana, India"}
    question="When will I travel abroad?"
    intent={"category":"foreign","foreign_subtype":"foreign_travel_timing","answer_mode":"event_prediction","query_context":{"as_of":"2026-09-04T21:30:00+05:30"}}
    apply_foreign_routing_guards(intent)
    context=_build_instant_context(birth,question,intent,[],answer_mode_override="event_prediction",target_subject_override={"key":"self","label":"self","base_house":1})
    packet=build_instant_v2_packet(question=question,intent=intent,answer_mode="event_prediction",target_subject={"key":"self","label":"self","base_house":1},language="english",instant_context=context)
    result=apply_live_graph_policy(packet,intent=intent,context=context)

    assert result["query_plan"]["time_scope"]["horizon_end"] is None
    assert result["verdict"]["direction"]=="conditional_window_found"
    window=result["verdict"]["ranked_windows"][0]
    assert window["start"]=="2029-01-17"
    assert window["end"]=="2029-05-27"

    composer=_build_instant_composer_context(context,result)
    timing=composer["evidence"]["foreign_foundation"]["timing_synthesis"]
    assert timing["next_window"]["start"]=="2029-01-17"
    assert timing["next_window"]["transit_confirmation"][0]["start"]=="2029-03-22"
    assert len(str(composer))<25000

    result["answer_spec"]["visible_astrology"]={"technical_detail_allowed":True}
    evasive=(
        "Your current Saturn-Rahu-Saturn period supports preparation, but it doesn't yet show the clear, "
        "dated confirmation needed to give a specific departure window. What's creating the urgency?"
    )
    clean=enforce_live_graph_answer(evasive,result,language="english")
    assert "17 January 2029" in clean
    assert "27 May 2029" in clean
    assert "22 March 2029" in clean
    assert "conditional window" in clean
    assert "Saturn–Jupiter–Mercury" in clean


def test_permanent_settlement_rejects_generic_planet_meanings_but_preserves_calculated_activation()->None:
    birth={"name":"ABC","date":"1980-04-02","time":"14:55:00","latitude":29.2396596,"longitude":75.8174505,"timezone":"UTC+5:30","place":"Hisar, Haryana, India"}
    question="Can I settle abroad permanently?"
    intent={"category":"foreign","foreign_subtype":"permanent_settlement","answer_mode":"potential_capacity","query_context":{"as_of":"2026-09-04T21:50:00+05:30"}}
    apply_foreign_routing_guards(intent)
    context=_build_instant_context(birth,question,intent,[],answer_mode_override="potential_capacity",target_subject_override={"key":"self","label":"self","base_house":1})
    foundation=context["normalized_evidence"]["foreign_foundation"]
    route=foundation["route_synthesis"]
    assert route["primary_houses"]==[4,11,12]
    rahu=next(row for row in route["planet_contributions"] if row["planet"]=="Rahu")
    assert any(row["role"]=="aspector_to_house_lord" and row["source_house"]==2 for row in rahu["activations"])
    assert rahu["net_direction"] in {"challenging","mixed"}

    packet=build_instant_v2_packet(question=question,intent=intent,answer_mode="potential_capacity",target_subject={"key":"self","label":"self","base_house":1},language="english",instant_context=context)
    result=apply_live_graph_policy(packet,intent=intent,context=context)
    bad=(
        "Yes, your chart strongly promises permanent settlement abroad. "
        "The 4th house and 7th house connect residence with foreign life. "
        "Rahu in the 2nd house gives you a natural pull toward foreign lands. "
        "Sun supports this by giving confidence and recognition abroad."
    )
    clean=enforce_live_graph_answer(bad,result,language="english")
    for forbidden in ("natural pull","confidence","recognition","not H7","generic Rahu","these links show activation"):
        assert forbidden.lower() not in clean.lower()


def test_foreign_technical_contract_rejects_ledger_dump_and_accepts_explanation()->None:
    dumped=(
        "The chart is supportive. D1: H4 lord Venus is own sign. D1: H11 lord Venus is own sign. "
        "D4: H7 lord Venus is own sign. D9: Moon aspects H4. "
        "These links show activation and its direction."
    )
    errors=_validate_foreign_technical_explanation(dumped,technical=True)
    assert any("catalogue" in error for error in errors)
    assert any("dignity" in error for error in errors)

    explained=(
        "The settlement promise is supportive but qualified. In D1, Venus rules H4 and occupies its own sign in "
        "H11, which links residence with realization rather than showing travel alone. However, the H12 lord's "
        "placement adds transition pressure. D4 confirms residential capacity while D12 qualifies how steadily "
        "foreign roots are maintained."
    )
    assert _validate_foreign_technical_explanation(explained,technical=True)==[]
