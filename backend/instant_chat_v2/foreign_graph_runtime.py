"""Resolve Travel, Relocation and Foreign Life requests against compiled policy."""
from __future__ import annotations
import re
from typing import Any, Mapping
from .foreign import BOUNDARY_SUBTYPES, TIMING_SUBTYPES, is_foreign_category, normalize_foreign_subtype
from .foreign_graph_policy import ForeignGraphPolicyStore, default_foreign_graph_policy_store

TIMING_MODES=frozenset({"event_prediction","event_timing","lifetime_event_timing","month_timing","timing_window","daily_forecast"})
_MODE={"foreign:ModeTopic":{"topic_reading","trait_nature","potential_capacity"},"foreign:ModeCapacity":{"potential_capacity","topic_reading"},"foreign:ModeDiagnosis":{"problem_diagnosis","topic_reading"},"foreign:ModeTiming":set(TIMING_MODES),"foreign:ModeComparison":{"comparison_choice","decision_support"},"foreign:ModeRemedy":{"remedy_action"},"foreign:ModeHandoff":{"handoff","dedicated_muhurat_flow","location_recommendation","topic_reading"}}

def foreign_graph_runtime_key(category: Any, plan: Mapping[str,Any]|None=None)->str|None:
    if not is_foreign_category(category): return None
    plan=plan if isinstance(plan,Mapping) else {}; subtype=normalize_foreign_subtype(plan.get("foreign_subtype")); mode=str(plan.get("answer_mode") or "").lower()
    if subtype in BOUNDARY_SUBTYPES: return subtype
    if mode in TIMING_MODES:
        return {"short_travel":"short_travel_timing","long_travel":"long_travel_timing","domestic_relocation":"domestic_relocation_timing","foreign_travel":"foreign_travel_timing","foreign_residence":"foreign_residence_timing","permanent_settlement":"settlement_timing","visa_support":"visa_timing","return_home":"return_home_timing"}.get(subtype,subtype)
    return subtype

def resolve_foreign_graph_inputs(*,intent:Mapping[str,Any]|None,context:Mapping[str,Any]|None,query_plan:Mapping[str,Any]|None=None)->dict[str,Any]:
    intent=intent if isinstance(intent,Mapping) else {}; context=context if isinstance(context,Mapping) else {}; summary=context.get("intent_summary") if isinstance(context.get("intent_summary"),Mapping) else {}; plan=dict(query_plan or {}); plan.setdefault("foreign_subtype",intent.get("foreign_subtype") or summary.get("foreign_subtype")); return {"category":plan.get("category") or summary.get("category") or intent.get("category"),"query_plan":plan,"observed_answer_mode":plan.get("answer_mode") or summary.get("answer_mode") or intent.get("answer_mode")}

def observed_foreign_factors(context:Mapping[str,Any],plan:Mapping[str,Any]|None=None)->set[str]:
    plan=plan if isinstance(plan,Mapping) else {}; key=foreign_graph_runtime_key(plan.get("category"),plan)
    if key in BOUNDARY_SUBTYPES:return {"foreign:ScopeBoundary"}
    n=context.get("normalized_evidence") if isinstance(context.get("normalized_evidence"),Mapping) else {}; f=n.get("foreign_foundation") if isinstance(n.get("foreign_foundation"),Mapping) else {}; a=f.get("availability") if isinstance(f.get("availability"),Mapping) else {}; out=set()
    for code in ("d1","d3","d4","d9","d10","d12"):
        if a.get(code):out.add(f"foreign:{code.upper()}")
    for h in f.get("houses_available") or []:
        try:out.add(f"foreign:H{int(h)}")
        except (TypeError,ValueError):pass
    if key in TIMING_SUBTYPES:
        timing=f.get("timing_synthesis") if isinstance(f.get("timing_synthesis"),Mapping) else {}
        if a.get("kp_fructification"):out.add("foreign:KPFructification")
        if timing.get("dasha_evaluation_complete"):out.add("foreign:DashaActivation")
        if timing.get("transit_evaluation_complete"):out.add("foreign:TransitConfirmation")
    if a.get("option_evidence") and (key != "location_comparison" or len(plan.get("comparison_options") or []) >= 2):out.add("foreign:OptionEvidence")
    if a.get("pathway_evidence"):out.add("foreign:PathwayEvidence")
    if a.get("remedy_blueprint"):out.add("foreign:RemedyBlueprint")
    return out

def compare_foreign_graph_policy(*,category:Any,query_plan:Mapping[str,Any]|None,observed_answer_mode:Any,context:Mapping[str,Any],store:ForeignGraphPolicyStore|None=None)->dict[str,Any]|None:
    if not is_foreign_category(category):return None
    plan=dict(query_plan or {});plan.setdefault("category",category);key=foreign_graph_runtime_key(category,plan);s=store or default_foreign_graph_policy_store();p=s.resolve(str(key or ""))
    if not p:return {"ontology_version":s.ontology_version,"runtime_key":key,"match":False,"mismatches":[{"kind":"missing_compiled_policy"}]}
    actual=observed_foreign_factors(context,plan);required=set(p.required_factors);excluded=set(p.default_exclusions);mode=str(observed_answer_mode or "");mode_match=mode in _MODE.get(p.answer_mode,set());missing=sorted(required-actual);unexpected=sorted(excluded&actual);mismatches=[] if mode_match else [{"kind":"answer_mode","expected":p.answer_mode,"observed":mode}]
    if missing:mismatches.append({"kind":"missing_required_factors","factors":missing})
    if unexpected:mismatches.append({"kind":"unexpected_default_exclusions","factors":unexpected})
    return {"ontology_version":s.ontology_version,"runtime_key":key,"ontology_resource":p.ontology_resource,"question_label":p.question_label,"graph_tree":p.graph_tree,"expected_answer_mode":p.answer_mode,"observed_answer_mode":mode,"mode_match":mode_match,"required_factors":sorted(required),"observed_factors":sorted(actual),"default_exclusions":sorted(excluded),"missing_required_factors":missing,"unexpected_default_exclusions":unexpected,"required_capabilities":sorted(p.required_capabilities),"decision_rules":sorted(p.decision_rules),"guardrails":sorted(p.guardrails),"answer_contract":p.answer_contract,"evidence_policy":p.evidence_policy,"match":not mismatches,"mismatches":mismatches}

def _label(value:Any)->str:
    text=str(value or "").split(":")[-1];return " ".join(re.sub(r"(?<!^)(?=[A-Z])"," ",text).split()).capitalize()
def build_foreign_graph_route(comparison:Mapping[str,Any]|None)->dict[str,Any]|None:
    if not isinstance(comparison,Mapping):return None
    required=[str(v) for v in comparison.get("required_factors",())];observed={str(v) for v in comparison.get("observed_factors",())}
    return {"status":"matched" if comparison.get("match") else "review_needed","ontology_version":comparison.get("ontology_version"),"runtime_key":comparison.get("runtime_key"),"question_type":comparison.get("question_label") or _label(comparison.get("runtime_key")),"graph_tree":comparison.get("graph_tree"),"expected_approach":_label(comparison.get("expected_answer_mode")),"selected_approach":_label(comparison.get("observed_answer_mode")),"mode_match":bool(comparison.get("mode_match")),"required_nodes":[{"id":x,"label":_label(x),"selected":x in observed} for x in required],"missing_nodes":[{"id":x,"label":_label(x)} for x in required if x not in observed],"decision_rules":[{"id":str(x),"label":_label(x)} for x in comparison.get("decision_rules",())],"guardrails":[{"id":str(x),"label":_label(x)} for x in comparison.get("guardrails",())],"required_capabilities":[{"id":str(x),"label":_label(x)} for x in comparison.get("required_capabilities",())],"answer_contract":_label(comparison.get("answer_contract")),"evidence_policy":_label(comparison.get("evidence_policy"))}
