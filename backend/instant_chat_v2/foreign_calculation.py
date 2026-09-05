"""Deterministic evidence synthesis for Travel, Relocation and Foreign Life."""
from __future__ import annotations
from typing import Any, Mapping
from .foreign import BOUNDARY_SUBTYPES, TIMING_SUBTYPES, foreign_profile
from .home_calculation import _chart_for, _condition, _kp_adjudication, _timing_windows

_PRIMARY = {
    "short_travel":(3,), "long_travel":(9,12), "travel_tendency":(3,9,12),
    "foreign_overview":(3,4,9,11,12), "travel_purpose":(3,7,9,10,11,12),
    "travel_obstacles":(3,6,8,9,12), "retrospective_travel":(3,9,11,12),
    "domestic_relocation":(3,4,12), "stay_vs_relocate":(3,4,12),
    "temporary_vs_permanent":(4,9,11,12),
    "foreign_travel":(3,9,12), "foreign_residence":(4,9,12),
    "permanent_settlement":(4,11,12), "visa_support":(3,9,11),
    "migration_pathway":(7,9,10,11,12),
    "return_home":(3,4,11), "foreign_life_adjustment":(4,7,11,12),
    "foreign_obstacles":(4,6,8,11,12), "foreign_remedy":(4,6,8,11,12),
    "location_comparison":(4,9,10,11,12),
}

_HOUSE_MEANINGS={
    2:"resources and family roots",3:"movement, documents and initiative",4:"home, residence and rootedness",
    6:"obstacles, service and process",7:"partnerships, agreements and life away from the original base",
    8:"disruption and major transition",9:"long-distance movement and opportunity",10:"work and public role",
    11:"realization, continuity and gains",12:"foreign residence, separation and sustained distance",
}

def build_foreign_foundation(*, chart_data: Mapping[str,Any], normalized_evidence: Mapping[str,Any], category: Any, answer_mode: Any, foreign_subtype: Any=None, kp_evidence: Mapping[str,Any]|None=None, period_window: Mapping[str,Any]|None=None) -> dict[str,Any]:
    profile=foreign_profile(category,foreign_subtype); subtype=profile["subtype"]
    if subtype in BOUNDARY_SUBTYPES:
        return {"foreign_subtype":subtype,"availability":{"scope_boundary":True},"houses_available":[]}
    charts={code:_chart_for(chart_data,code,normalized_evidence) for code in profile["charts"]}
    rows={code:[_condition(code,chart,h) for h in profile["houses"]] for code,chart in charts.items()}
    d1={r["house"]:r for r in rows.get("D1",[]) if r.get("available")}
    base_subtype={"settlement_timing":"permanent_settlement"}.get(subtype,subtype.removesuffix("_timing"))
    primary=_PRIMARY.get(base_subtype,tuple(profile["houses"][:2]))
    score=sum(float((d1.get(h) or {}).get("score") or 0) for h in primary)
    confirmations={code:sum(float(r.get("score") or 0) for r in values if r.get("house") in primary) for code,values in rows.items() if code!="D1"}
    complete=all(h in d1 for h in primary) and all(any(r.get("available") for r in rows.get(code,[])) for code in profile["charts"] if code!="D1")
    route_fact_rows={
        code:[r for r in values if r.get("available")]
        for code,values in rows.items()
    }
    route_fact_rows={code:values for code,values in route_fact_rows.items() if values}
    allowed_planet_roles=[]
    planet_activations: dict[str,list[dict[str,Any]]]={}
    known_planets=("Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu")

    def add_activation(planet: Any, activation: dict[str,Any]) -> None:
        name=str(planet or "")
        if name in known_planets:
            planet_activations.setdefault(name,[]).append(activation)

    for code,values in route_fact_rows.items():
        for row in values:
            house=row.get("house")
            if row.get("lord"):
                allowed_planet_roles.append({
                    "chart":code,"house":house,"planet":row.get("lord"),"role":"lord",
                    "placed_house":row.get("lord_house"),"dignity":row.get("lord_dignity"),
                })
            for planet in row.get("occupants") or []:
                allowed_planet_roles.append({"chart":code,"house":house,"planet":planet,"role":"occupant"})
            for aspect in row.get("house_aspects") or []:
                allowed_planet_roles.append({
                    "chart":code,"house":house,"planet":aspect.get("planet"),"role":"aspector",
                    "tone":aspect.get("tone"),
                })
            for direction,key in (("supportive","support"),("challenging","cautions")):
                for statement in row.get(key) or []:
                    planet=next((name for name in known_planets if name in str(statement)),None)
                    if planet:
                        add_activation(planet,{
                            "chart":code,"target_house":house,"direction":direction,
                            "role":"lord" if f"lord {planet}" in str(statement) else "occupant" if "occupies" in str(statement) else "aspector" if "aspect" in str(statement) else "linked",
                            "evidence":str(statement),
                        })
            for aspect in row.get("lord_aspects_received") or []:
                planet=aspect.get("planet")
                tone=str(aspect.get("aspect_tone") or aspect.get("nature") or "").lower()
                direction="supportive" if "benefic" in tone and "malefic" not in tone else "challenging" if "malefic" in tone else "mixed"
                add_activation(planet,{
                    "chart":code,"target_house":house,"source_house":aspect.get("from_house"),
                    "direction":direction,"role":"aspector_to_house_lord",
                    "evidence":f"{code}: {planet} from H{aspect.get('from_house')} aspects H{house} lord {row.get('lord')}",
                })
    planet_contributions=[]
    for planet,activations in planet_activations.items():
        directions={str(item.get("direction")) for item in activations}
        net=("mixed" if len(directions)>1 else next(iter(directions)) if directions else "unclassified")
        planet_contributions.append({"planet":planet,"net_direction":net,"activations":activations[:8]})
    controlling_rows=[]
    for house in primary:
        row=d1.get(house) or {}
        if not row:
            continue
        supports=list(row.get("support") or [])
        cautions=list(row.get("cautions") or [])
        supports.sort(key=lambda value:(0 if " is in H" in str(value) else 1 if "occupies" in str(value) else 2 if "aspect" in str(value) else 3))
        controlling_rows.append({
            "chart":"D1","house":house,"life_function":_HOUSE_MEANINGS.get(house,f"house {house}"),
            "score":row.get("score"),"strongest_support":supports[0] if supports else None,
            "strongest_caution":cautions[0] if cautions else None,
            "lord":row.get("lord"),"lord_house":row.get("lord_house"),
            "destination_function":_HOUSE_MEANINGS.get(row.get("lord_house"),f"house {row.get('lord_house')}") if row.get("lord_house") else None,
        })
    divisional_rows=[]
    for code,values in route_fact_rows.items():
        if code=="D1":
            continue
        relevant=[row for row in values if row.get("house") in primary]
        supports=[fact for row in relevant for fact in row.get("support") or []]
        cautions=[fact for row in relevant for fact in row.get("cautions") or []]
        supports.sort(key=lambda value:(0 if " is in H" in str(value) else 1 if "occupies" in str(value) else 2 if "aspect" in str(value) else 3))
        divisional_rows.append({
            "chart":code,"role":("movement confirmation" if code=="D3" else "residence confirmation" if code=="D4" else "long-distance maturation" if code=="D9" else "rootedness and separation confirmation" if code=="D12" else "route confirmation"),
            "score":confirmations.get(code),"strongest_support":supports[0] if supports else None,
            "strongest_caution":cautions[0] if cautions else None,
        })
    explanation_plan={
        "controlling_chain":controlling_rows,
        "divisional_synthesis":divisional_rows,
        "house_meanings":{str(house):_HOUSE_MEANINGS.get(house,f"house {house}") for house in profile["houses"]},
        "selection_rule":(
            "Explain the verdict as a connected argument. Select the smallest decisive set: normally one D1 "
            "house-lord relationship that links route functions, one materially different supporting or opposing "
            "condition, and one divisional confirmation or qualification. Do not enumerate every available row."
        ),
    }
    fact_contract={
        "route":base_subtype,
        "controlling_houses":list(primary),
        "allowed_houses":list(profile["houses"]),
        "rows":route_fact_rows,
        "allowed_planet_roles":allowed_planet_roles,
        "rule":(
            "A planet may be cited only with its supplied chart, house and exact role. "
            "Do not turn a placement or aspect into an unsupplied personality trait or life mechanism."
        ),
    }
    if base_subtype == "permanent_settlement":
        fact_contract["settlement_rule"]=(
            "Permanent settlement is adjudicated from D1 H4 residence, H11 realization and H12 "
            "foreign residence/separation, then qualified by D4 residence and D12 rootedness. "
            "H7 partnership/away-from-origin and H9 distance may contribute as secondary links "
            "when their actual calculated rows connect to the primary settlement chain."
        )
    route={"verdict":"not_established" if not complete else "supportive" if score+sum(confirmations.values())*.35>=1 else "qualified" if score>=-.5 else "pressured","evidence_complete":complete,"primary_houses":list(primary),"chart_confirmation_scores":confirmations,"explanation_plan":explanation_plan,"planet_contributions":planet_contributions,"fact_contract":fact_contract,"rule":"Use movement H3, residence H4, distance H9, realization H11 and separation/foreign residence H12 only in the route-specific combination; distinguish activation from supportive, challenging or mixed contribution, and never infer the result from H12 or Rahu alone."}
    timing={}
    if subtype in TIMING_SUBTYPES:
        success=set(profile["houses"]); required=set(primary); cusps=tuple(h for h in primary if h in {3,4,9,11,12})[:2] or (9,12)
        kp=_kp_adjudication(kp_evidence or {},primary_cusps=cusps,success_houses=success,pressure_houses={6,8})
        windows=_timing_windows(normalized_evidence,success_houses=success,required_event_houses=required,period_window=period_window,retrospective=subtype=="retrospective_travel")
        timing={"kp_fructification":kp,"timing_windows":windows,"next_window":sorted(windows,key=lambda r:str(r.get("start") or ""))[0] if windows else {},"verdict":"supported_windows_found" if kp.get("verdict")=="supported" and windows else "conditional_window_found" if windows else "no_window_in_horizon","dasha_evaluation_complete":bool((normalized_evidence.get("forward_event_dasha_scan") or {}).get("dasha_evaluation_complete")),"transit_evaluation_complete":bool((normalized_evidence.get("forward_event_dasha_scan") or {}).get("transit_evaluation_complete"))}
    comparison={}
    if subtype == "stay_vs_relocate":
        stay=sum(float((d1.get(h) or {}).get("score") or 0) for h in (4,11))
        move=sum(float((d1.get(h) or {}).get("score") or 0) for h in (3,9,12))
        comparison={"options":[{"key":"stay","score":round(stay,2)},{"key":"relocate","score":round(move,2)}],"verdict":"relocate" if move>stay else "stay" if stay>move else "balanced","rule":"Compare rootedness/realization against movement/distance/separation; do not infer either option from H12 alone."}
    elif subtype == "temporary_vs_permanent":
        temporary=sum(float((d1.get(h) or {}).get("score") or 0) for h in (3,9,12))
        permanent=sum(float((d1.get(h) or {}).get("score") or 0) for h in (4,11,12)) + .35*sum(confirmations.get(code,0) for code in ("D4","D12"))
        comparison={"options":[{"key":"temporary","score":round(temporary,2)},{"key":"permanent","score":round(permanent,2)}],"verdict":"permanent" if permanent>temporary else "temporary" if temporary>permanent else "mixed","rule":"Permanent settlement requires H4/H11 residence continuity confirmed by D4/D12, not travel evidence alone."}
    pathway={}
    if subtype == "migration_pathway":
        pathway_scores={"work":sum(float((d1.get(h) or {}).get("score") or 0) for h in (9,10,11,12)),"study":sum(float((d1.get(h) or {}).get("score") or 0) for h in (5,9,11,12)),"partnership":sum(float((d1.get(h) or {}).get("score") or 0) for h in (7,9,11,12)),"family":sum(float((d1.get(h) or {}).get("score") or 0) for h in (2,4,9,11,12))}
        ranked=sorted(pathway_scores.items(),key=lambda item:(-item[1],item[0]))
        pathway={"ranked_pathways":[{"key":key,"score":round(value,2)} for key,value in ranked],"strongest":ranked[0][0] if ranked else None,"rule":"These are routes into movement/residence only; specialist domains still own career, education and marriage outcomes."}
    remedy=normalized_evidence.get("remedy_blueprint") if subtype=="foreign_remedy" and isinstance(normalized_evidence.get("remedy_blueprint"),Mapping) else {}
    availability={**{code.lower():any(r.get("available") for r in values) for code,values in rows.items()},"kp_fructification":bool((timing.get("kp_fructification") or {}).get("complete")),"pathway_evidence":bool(pathway),"option_evidence":bool(comparison) or subtype=="location_comparison","remedy_blueprint":bool(remedy)}
    return {"foreign_subtype":subtype,"focus_houses":list(profile["houses"]),"houses_available":sorted(d1),"charts":rows,"route_synthesis":route,"comparison_synthesis":comparison,"pathway_synthesis":pathway,"remedy_blueprint":remedy,"timing_synthesis":timing,"availability":availability}
