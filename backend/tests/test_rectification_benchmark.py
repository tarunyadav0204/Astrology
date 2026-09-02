from __future__ import annotations

import json

import pytest

from rectification.benchmark import (
    BLINDED_DATASET_SCHEMA_VERSION,
    TRUTH_VAULT_SCHEMA_VERSION,
    analyze_candidate_boundaries,
    build_cross_chart_event_control,
    build_date_jitter_cases,
    build_same_type_date_rotation_control,
    load_blinded_cases,
    render_markdown,
    run_benchmark,
)
from rectification.engine import CandidateEvaluation
from rectification.event_audit import (
    AUDITED_COHORT_STATUS,
    EVENT_AUDIT_SCHEMA_VERSION,
    apply_event_audit,
)
from rectification.public_benchmark_seed import build_seed_cohort
from rectification.cohort_freeze import (
    COHORT_FREEZE_SCHEMA_VERSION,
    create_frozen_manifest,
)


def _case():
    return {
        "id": "blind-001",
        "split": "development",
        "window_strategy": "pre_recorded_uncertainty",
        "chart": {
            "name": "Hidden truth fixture",
            "date": "1980-04-02",
            "latitude": 29.1492,
            "longitude": 75.7217,
            "timezone": "Asia/Kolkata",
            "place": "Hisar",
        },
        "window_start_local": "12:00:00",
        "window_end_local": "12:05:00",
        "events": [
            {"id": 1, "event_type": "marriage", "date_start": "2005-11-18", "precision": "exact_day", "source_reliability": "documented"},
            {"id": 2, "event_type": "career_change", "date_start": "2008-06-01", "precision": "month", "source_reliability": "confident_memory"},
            {"id": 3, "event_type": "childbirth", "date_start": "2010-07-10", "precision": "exact_day", "source_reliability": "documented"},
            {"id": 4, "event_type": "relocation", "date_start": "2014-01-01", "precision": "year", "source_reliability": "approximate_memory"},
        ],
    }


def _write_inputs(tmp_path, case=None):
    cases_path = tmp_path / "cases.json"
    truth_path = tmp_path / "truth.json"
    cases_path.write_text(json.dumps({
        "schema_version": BLINDED_DATASET_SCHEMA_VERSION,
        "dataset_id": "test-cohort-v1",
        "cases": [case or _case()],
    }))
    truth_path.write_text(json.dumps({
        "schema_version": TRUTH_VAULT_SCHEMA_VERSION,
        "dataset_id": "test-cohort-v1",
        "truth": [{
            "id": "blind-001",
            "verified_local_time": "12:03:00",
            "verification_source": "contemporaneous hospital record",
            "verification_rating": "documented",
        }],
    }))
    return cases_path, truth_path


class BlindSpyEvaluator:
    seen_chart_inputs = []

    def evaluate(self, *, chart_input, candidate_time, events):
        assert "verified_local_time" not in chart_input
        assert "verified_time" not in chart_input
        self.__class__.seen_chart_inputs.append(dict(chart_input))
        minute = int(candidate_time.split(":")[1])
        full_signal = minute == 3
        kp_signal = minute == 0
        event_rows = []
        for event in events:
            event_rows.append({
                "event_id": event["id"],
                "score": 85.0 if full_signal else (15.0 if kp_signal else 0.0),
                "reliability_weight": 1.0,
                "structural_promise": {"score": 10.0 if full_signal else 0.0, "maximum": 10.0},
                "dasha_delivery": {"score": 40.0 if full_signal else 0.0, "maximum": 40.0},
                "varga_confirmation": {"score": 20.0 if full_signal else 0.0, "maximum": 20.0},
                "transit_confirmation": {"score": 15.0 if full_signal else 0.0, "maximum": 15.0},
                "kp_confirmation": {"score": 15.0 if kp_signal else 0.0, "maximum": 15.0},
            })
        score = 85.0 if full_signal else (15.0 if kp_signal else 0.0)
        return CandidateEvaluation(
            local_time=candidate_time,
            score=score,
            weighted_score=score * len(events),
            event_weight_total=float(len(events)),
            fingerprint=candidate_time,
            details={
                "candidate_local_time": candidate_time,
                "relative_fit": score,
                "events": event_rows,
            },
        )


def test_blinded_dataset_rejects_any_truth_field(tmp_path):
    leaked = _case()
    leaked["chart"]["verified_local_time"] = "12:03:00"
    cases_path, _ = _write_inputs(tmp_path, leaked)
    with pytest.raises(ValueError, match="leaks truth field"):
        load_blinded_cases(cases_path)


def test_benchmark_recovers_hidden_time_and_reports_layer_ablation(tmp_path):
    BlindSpyEvaluator.seen_chart_inputs = []
    cases_path, truth_path = _write_inputs(tmp_path)
    report = run_benchmark(
        cases_path=cases_path,
        truth_path=truth_path,
        evaluator_factory=BlindSpyEvaluator,
    )
    assert BlindSpyEvaluator.seen_chart_inputs
    assert report["blindness"]["predictions_completed_before_truth_loaded"] is True
    assert report["metrics"]["development"]["full"]["recovery"]["5"]["selected_rate"] == 1.0
    assert report["cases"][0]["profiles"]["full"]["selected_local_time"] == "12:03:00"
    assert report["cases"][0]["profiles"]["kp_only"]["selected_local_time"] == "12:00:00"
    assert report["cases"][0]["profiles"]["kp_only"]["selected_error_minutes"] == 3.0
    assert report["comparison_to_midpoint"]["development"]["full_beats_midpoint_mean_error"] is True
    assert "Birth-time rectification blind benchmark" in render_markdown(report)


def test_truth_vault_is_opened_only_after_all_candidate_predictions(tmp_path, monkeypatch):
    cases_path, truth_path = _write_inputs(tmp_path)
    import rectification.benchmark as benchmark

    original = benchmark.load_truth_vault

    def guarded_truth_load(path):
        assert BlindSpyEvaluator.seen_chart_inputs, "truth was loaded before prediction"
        return original(path)

    BlindSpyEvaluator.seen_chart_inputs = []
    monkeypatch.setattr(benchmark, "load_truth_vault", guarded_truth_load)
    run_benchmark(
        cases_path=cases_path,
        truth_path=truth_path,
        evaluator_factory=BlindSpyEvaluator,
    )


def test_robustness_controls_all_run_before_truth_is_opened(tmp_path, monkeypatch):
    cases_path, truth_path = _write_inputs(tmp_path)
    import rectification.benchmark as benchmark

    original = benchmark.load_truth_vault

    def guarded_truth_load(path):
        # Six candidate minutes × original plus two signed jitter controls.
        assert len(BlindSpyEvaluator.seen_chart_inputs) == 18
        return original(path)

    BlindSpyEvaluator.seen_chart_inputs = []
    monkeypatch.setattr(benchmark, "load_truth_vault", guarded_truth_load)
    report = run_benchmark(
        cases_path=cases_path,
        truth_path=truth_path,
        evaluator_factory=BlindSpyEvaluator,
        robustness_controls=True,
        jitter_days=(1,),
    )
    controls = report["robustness_controls"]
    assert controls["all_controls_predicted_before_truth_loaded"] is True
    assert sorted(controls["comparisons"]) == [
        "event_date_jitter_+1_days", "event_date_jitter_-1_days"
    ]
    assert report["release_gate"]["status"] == "blocked"
    assert report["release_gate"]["use_rectified_time_enabled"] is False


def test_control_case_builders_do_not_mutate_original_cases(tmp_path):
    cases_path, _ = _write_inputs(tmp_path)
    cases = load_blinded_cases(cases_path)
    original = json.dumps(cases, sort_keys=True)
    shifted = build_date_jitter_cases(cases, 7)
    assert shifted[0]["events"][0]["date_start"] == "2005-11-25"
    assert json.dumps(cases, sort_keys=True) == original

    second = json.loads(json.dumps(cases[0]))
    second["id"] = "blind-002"
    second["events"][0]["event_type"] = "education"
    rotated = build_cross_chart_event_control([cases[0], second])
    assert rotated[0]["events"][0]["event_type"] == "education"
    assert rotated[1]["events"][0]["event_type"] == "marriage"


def test_same_type_date_rotation_preserves_event_types_and_case_shape(tmp_path):
    cases_path, _ = _write_inputs(tmp_path)
    cases = load_blinded_cases(cases_path)
    second = json.loads(json.dumps(cases[0]))
    second["id"] = "blind-002"
    second["events"][0]["date_start"] = "1999-01-02"
    second["events"][0]["date_end"] = "1999-01-02"
    control = build_same_type_date_rotation_control([cases[0], second])
    assert [event["event_type"] for event in control[0]["events"]] == [
        event["event_type"] for event in cases[0]["events"]
    ]
    assert control[0]["events"][0]["date_start"] == "1999-01-02"
    assert control[1]["events"][0]["date_start"] == "2005-11-18"


def test_benchmark_requires_four_events_and_no_birth_time_in_chart(tmp_path):
    too_few = _case()
    too_few["events"] = too_few["events"][:3]
    cases_path, _ = _write_inputs(tmp_path, too_few)
    with pytest.raises(ValueError, match="at least four"):
        load_blinded_cases(cases_path)

    unblinded = _case()
    unblinded["chart"]["time"] = "12:03:00"
    cases_path, _ = _write_inputs(tmp_path, unblinded)
    with pytest.raises(ValueError, match="must not contain a birth time"):
        load_blinded_cases(cases_path)


def test_benchmark_refuses_a_truth_vault_from_another_cohort(tmp_path):
    cases_path, truth_path = _write_inputs(tmp_path)
    payload = json.loads(truth_path.read_text())
    payload["dataset_id"] = "different-cohort"
    truth_path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="Dataset id mismatch"):
        run_benchmark(
            cases_path=cases_path,
            truth_path=truth_path,
            evaluator_factory=BlindSpyEvaluator,
        )


def test_holdout_is_locked_until_explicitly_revealed(tmp_path):
    development = _case()
    development["id"] = "development-001"
    holdout = _case()
    holdout["id"] = "holdout-001"
    holdout["split"] = "holdout"
    cases_path = tmp_path / "cases.json"
    truth_path = tmp_path / "truth.json"
    cases_path.write_text(json.dumps({
        "schema_version": BLINDED_DATASET_SCHEMA_VERSION,
        "dataset_id": "preassigned-v1",
        "cohort_status": "preassigned_development_holdout_event_sources_audited",
        "cases": [development, holdout],
    }))
    truth_path.write_text(json.dumps({
        "schema_version": TRUTH_VAULT_SCHEMA_VERSION,
        "dataset_id": "preassigned-v1",
        "cohort_status": "preassigned_development_holdout_event_sources_audited",
        "truth": [
            {"id": "development-001", "verified_local_time": "12:03:00", "verification_source": "record"},
            {"id": "holdout-001", "verified_local_time": "12:03:00", "verification_source": "record"},
        ],
    }))
    with pytest.raises(ValueError, match="Holdout scoring is locked"):
        run_benchmark(cases_path=cases_path, truth_path=truth_path, evaluator_factory=BlindSpyEvaluator)
    development_report = run_benchmark(
        cases_path=cases_path,
        truth_path=truth_path,
        split="development",
        evaluator_factory=BlindSpyEvaluator,
    )
    assert development_report["holdout_revealed"] is False
    manifest_path = tmp_path / "preassigned.freeze.private.json"
    manifest = create_frozen_manifest(
        cases_path=cases_path,
        truth_path=truth_path,
        minimum_total=2,
        minimum_holdout=1,
    )
    manifest_path.write_text(json.dumps(manifest))
    assert manifest["schema_version"] == COHORT_FREEZE_SCHEMA_VERSION
    full_report = run_benchmark(
        cases_path=cases_path,
        truth_path=truth_path,
        evaluator_factory=BlindSpyEvaluator,
        reveal_holdout=True,
        frozen_manifest_path=manifest_path,
    )
    assert full_report["holdout_revealed"] is True


def test_frozen_manifest_rejects_changed_blinded_cases(tmp_path):
    case = _case()
    case["split"] = "holdout"
    cases_path, truth_path = _write_inputs(tmp_path, case)
    payload = json.loads(cases_path.read_text())
    payload["cohort_status"] = "preassigned_development_holdout_event_sources_audited"
    cases_path.write_text(json.dumps(payload))
    truth_payload = json.loads(truth_path.read_text())
    truth_payload["cohort_status"] = "preassigned_development_holdout_event_sources_audited"
    truth_path.write_text(json.dumps(truth_payload))
    manifest = create_frozen_manifest(
        cases_path=cases_path,
        truth_path=truth_path,
        minimum_total=1,
        minimum_holdout=1,
    )
    manifest_path = tmp_path / "cohort.freeze.private.json"
    manifest_path.write_text(json.dumps(manifest))
    payload = json.loads(cases_path.read_text())
    payload["cases"][0]["window_end_local"] = "12:04:00"
    cases_path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="does not match the blinded cases"):
        run_benchmark(
            cases_path=cases_path,
            truth_path=truth_path,
            evaluator_factory=BlindSpyEvaluator,
            reveal_holdout=True,
            frozen_manifest_path=manifest_path,
        )


def test_public_seed_keeps_verified_time_out_of_blinded_case(tmp_path):
    events = "".join(
        f'''<event sevcode="{code}"><event_data><sbdate iyear="{year}" imonth="01" iday="02" /></event_data></event>'''
        for year, code in [
            (2001, "Social : End a program of study"),
            (2003, "Work : New Job"),
            (2008, "Relationship : Marriage"),
            (2012, "Family : Change residence"),
        ]
    )
    xml = tmp_path / "adb.xml"
    xml.write_text(f'''<astrodatabank_export><adb_entry adb_id="7"><public_data>
      <name>Public Person</name><roddenrating>AA</roddenrating>
      <bdata><sbdate iyear="1980" imonth="01" iday="01"/><sbtime>12:34</sbtime>
      <place slati="28n36" slong="77e12">New Delhi</place></bdata>
      <adb_link>https://example.test/public-person</adb_link></public_data>
      <research_data><events>{events}</events></research_data></adb_entry></astrodatabank_export>''')
    blinded, truth = build_seed_cohort(
        xml_path=xml,
        dataset_id="public-seed-test",
        count=1,
        random_seed=7,
        min_exact_events=0,
    )
    case = blinded["cases"][0]
    assert case["window_strategy"] == "blinded_uniform_truth_position"
    assert case["event_source_audit"].endswith("require_independent_verification")
    assert "time" not in case["chart"]
    assert "12:34" not in json.dumps(case)
    assert "public-person" not in json.dumps(case)
    assert case["window_start_local"].endswith(":00")
    assert case["window_end_local"].endswith(":00")
    assert truth["truth"][0]["verified_local_time"] == "12:34:00"


def _boundary_candidate(local_time, *, fingerprint, d9_sign, sub_lord, score):
    return CandidateEvaluation(
        local_time=local_time,
        score=score,
        weighted_score=score,
        event_weight_total=1.0,
        fingerprint=fingerprint,
        details={
            "d1_ascendant_sign": 3,
            "varga_ascendants": {"D9": {"longitude": d9_sign * 30.0, "sign": d9_sign}},
            "events": [{
                "event_id": "event-1",
                "event_type": "marriage",
                "dasha_delivery": {"active_lords": {"maha": "Jupiter"}, "score": 20},
                "kp_confirmation": {
                    "cusp_promise": [{"house": 7, "sub_lord": sub_lord, "supports": True}],
                    "score": 10,
                },
                "transit_confirmation": {"contacts": [], "score": 0},
                "structural_promise": {"score": 10},
                "varga_confirmation": {"score": 10 if d9_sign == 1 else 5},
            }],
        },
    )


def test_candidate_boundary_report_finds_exact_adjacent_varga_and_kp_change():
    candidates = [
        _boundary_candidate("12:00:00", fingerprint="same", d9_sign=0, sub_lord="Venus", score=50),
        _boundary_candidate("12:01:00", fingerprint="same", d9_sign=0, sub_lord="Venus", score=50),
        _boundary_candidate("12:02:00", fingerprint="changed", d9_sign=1, sub_lord="Saturn", score=45),
    ]
    result = analyze_candidate_boundaries(candidates)
    assert result["unique_evidence_profiles"] == 2
    assert result["longest_identical_plateau_candidates"] == 2
    transition = result["transitions"][0]
    assert transition["from_local_time"] == "12:01:00"
    assert transition["after_local_time"] == "12:02:00"
    assert "D9_ascendant_sign" in transition["changed_components"]
    assert "kp_cusps" in transition["changed_components"]


def _seed_payloads_for_audit():
    case = _case()
    case["id"] = "case-a"
    case["split"] = "development"
    blinded = {
        "schema_version": BLINDED_DATASET_SCHEMA_VERSION,
        "dataset_id": "seed-v1",
        "cohort_status": "development_seed_event_sources_unaudited",
        "cases": [case],
    }
    truth = {
        "schema_version": TRUTH_VAULT_SCHEMA_VERSION,
        "dataset_id": "seed-v1",
        "cohort_status": "development_seed_event_sources_unaudited",
        "truth": [{
            "id": "case-a",
            "verified_local_time": "12:03:00",
            "verification_source": "https://example.test/birth",
        }],
    }
    return blinded, truth


def _verified_audit_row(event_id, event_type, event_date):
    return {
        "case_id": "case-a",
        "event_id": event_id,
        "status": "verified_exact",
        "audited_event_type": event_type,
        "audited_date_start": event_date,
        "audited_precision": "exact_day",
        "sources": [{"publisher": "Official archive", "url": "https://example.test/event"}],
    }


def test_event_audit_retains_only_independently_verified_semantic_matches():
    blinded, truth = _seed_payloads_for_audit()
    rows = [
        _verified_audit_row("1", "marriage", "2005-11-18"),
        _verified_audit_row("2", "career_change", "2008-06-01"),
        _verified_audit_row("3", "childbirth", "2010-07-10"),
        _verified_audit_row("4", "relocation", "2014-01-01"),
    ]
    audited, audited_truth, report = apply_event_audit(
        blinded_payload=blinded,
        truth_payload=truth,
        audit_payload={
            "schema_version": EVENT_AUDIT_SCHEMA_VERSION,
            "dataset_id": "seed-v1",
            "audited_dataset_id": "seed-v1-audited",
            "events": rows,
        },
    )
    assert audited["cohort_status"] == AUDITED_COHORT_STATUS
    assert audited_truth["cohort_status"] == AUDITED_COHORT_STATUS
    assert audited["dataset_id"] == audited_truth["dataset_id"] == "seed-v1-audited"
    assert report["retained_cases"] == 1
    assert all(
        event["source_reliability"] == "documented"
        for event in audited["cases"][0]["events"]
    )
    assert "example.test/event" not in json.dumps(audited)


def test_event_audit_preserves_preassigned_holdout_split():
    blinded, truth = _seed_payloads_for_audit()
    blinded["cases"][0]["split"] = "holdout"
    rows = [
        _verified_audit_row("1", "marriage", "2005-11-18"),
        _verified_audit_row("2", "career_change", "2008-06-01"),
        _verified_audit_row("3", "childbirth", "2010-07-10"),
        _verified_audit_row("4", "relocation", "2014-01-01"),
    ]
    audited, audited_truth, _ = apply_event_audit(
        blinded_payload=blinded,
        truth_payload=truth,
        audit_payload={
            "schema_version": EVENT_AUDIT_SCHEMA_VERSION,
            "dataset_id": "seed-v1",
            "events": rows,
        },
    )
    assert audited["cases"][0]["split"] == "holdout"
    assert "preassigned_development_holdout" in audited["cohort_status"]
    assert audited_truth["cohort_status"] == audited["cohort_status"]


def test_event_audit_drops_semantic_mismatch_and_rejects_under_supported_case():
    blinded, truth = _seed_payloads_for_audit()
    rows = [
        _verified_audit_row("1", "marriage", "2005-11-18"),
        _verified_audit_row("2", "career_change", "2008-06-01"),
        _verified_audit_row("3", "childbirth", "2010-07-10"),
        {"case_id": "case-a", "event_id": "4", "status": "semantic_mismatch"},
    ]
    with pytest.raises(ValueError, match="No case retained"):
        apply_event_audit(
            blinded_payload=blinded,
            truth_payload=truth,
            audit_payload={
                "schema_version": EVENT_AUDIT_SCHEMA_VERSION,
                "dataset_id": "seed-v1",
                "events": rows,
            },
        )
