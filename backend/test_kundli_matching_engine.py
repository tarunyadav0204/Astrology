from marriage_analysis.compatibility_analyzer import CompatibilityAnalyzer
from marriage_matching.ashtakoota import AshtakootaCalculator
from marriage_matching.benchmarks import run_benchmark_suite
from marriage_matching.engine import KundliMatchingEngine
from datetime import date


def _chart(ascendant, moon_long, mars_long=180.0, venus_long=45.0, jupiter_long=120.0):
    def _planet(longitude, house=None):
        sign_zero = int((longitude % 360.0) / 30.0)
        return {
            "longitude": longitude % 360.0,
            "sign": sign_zero,
            "degree": longitude % 30.0,
            "house": house,
        }

    return {
        "ascendant": ascendant,
        "ayanamsa": 24.0,
        "planets": {
            "Moon": _planet(moon_long),
            "Mars": _planet(mars_long),
            "Venus": _planet(venus_long),
            "Jupiter": _planet(jupiter_long),
        },
        "houses": [{"sign": int(((ascendant / 30.0) + i) % 12)} for i in range(12)],
    }


def _birth(name):
    return {
        "name": name,
        "date": "1990-01-01",
        "time": "10:30",
        "latitude": 17.385,
        "longitude": 78.4867,
        "place": "Hyderabad",
    }


class MockDashaProvider:
    def get_periods(self, birth_data, start_date, end_date):
        name = birth_data["name"]
        if name == "Boy":
            return [
                {
                    "start_date": "2026-04-01",
                    "end_date": "2026-09-30",
                    "mahadasha": "Venus",
                    "antardasha": "Jupiter",
                    "pratyantardasha": "Moon",
                },
                {
                    "start_date": "2026-10-01",
                    "end_date": "2027-03-31",
                    "mahadasha": "Saturn",
                    "antardasha": "Mars",
                    "pratyantardasha": "Rahu",
                },
            ]
        return [
            {
                "start_date": "2026-04-15",
                "end_date": "2026-12-31",
                "mahadasha": "Venus",
                "antardasha": "Moon",
                "pratyantardasha": "Jupiter",
            },
            {
                "start_date": "2027-01-01",
                "end_date": "2027-06-30",
                "mahadasha": "Saturn",
                "antardasha": "Ketu",
                "pratyantardasha": "Mars",
            },
        ]


def test_moon_profile_uses_exact_longitude_not_nakshatra_only():
    calc = AshtakootaCalculator()
    boy_chart = _chart(0.0, 29.9)
    girl_chart = _chart(0.0, 31.0)

    boy_profile = calc.calculate(boy_chart, girl_chart)["boy_moon_profile"]
    girl_profile = calc.calculate(girl_chart, boy_chart)["boy_moon_profile"]

    assert boy_profile["nakshatra_name"] == "Krittika"
    assert girl_profile["nakshatra_name"] == "Krittika"
    assert boy_profile["sign_name"] == "Aries"
    assert girl_profile["sign_name"] == "Taurus"


def test_bhakoot_issue_reports_the_actual_pair():
    calc = AshtakootaCalculator()
    boy_chart = _chart(0.0, 1.0)
    girl_chart = _chart(0.0, 31.0)

    result = calc.calculate(boy_chart, girl_chart)

    assert result["koots"]["bhakoot"]["issue"] == "2/12 Bhakoot Dosha"
    assert "2/12 Bhakoot Dosha" in result["critical_issues"]


def test_compatibility_analyzer_returns_legacy_and_engine_payloads():
    analyzer = CompatibilityAnalyzer()
    boy_chart = _chart(0.0, 45.0, mars_long=180.0)
    girl_chart = _chart(30.0, 75.0, mars_long=210.0)

    result = analyzer.analyze_compatibility(boy_chart, girl_chart, _birth("Boy"), _birth("Girl"))

    assert "guna_milan" in result
    assert "manglik_analysis" in result
    assert "overall_score" in result
    assert "engine" in result
    assert result["engine"]["engine_version"] == "kundli_matching_v2"
    assert result["engine"]["legacy"]["overall_score"] == result["overall_score"]


def test_engine_exposes_structured_evidence_summary():
    engine = KundliMatchingEngine()
    boy_chart = _chart(0.0, 90.0, mars_long=180.0)
    girl_chart = _chart(60.0, 120.0, mars_long=210.0)

    result = engine.analyze(boy_chart, girl_chart, _birth("Boy"), _birth("Girl"))

    assert "positive_factors" in result["evidence_summary"]
    assert "caution_factors" in result["evidence_summary"]
    assert "contradictions" in result["evidence_summary"]
    assert "cross_chart" in result["relationship_indicators"]


def test_nadi_exception_softens_same_nakshatra_different_pada():
    calc = AshtakootaCalculator()
    boy_chart = _chart(0.0, 0.5)
    girl_chart = _chart(0.0, 4.0)

    result = calc.calculate(boy_chart, girl_chart)

    assert result["koots"]["nadi"]["score"] == 0
    assert result["exceptions"]["nadi"]["applies"] is True
    assert result["effective_total_score"] > result["total_score"]
    assert "Nadi Dosha - same Nadi" not in result["effective_critical_issues"]


def test_bhakoot_exception_softens_friendly_or_same_ruler_case():
    calc = AshtakootaCalculator()
    boy_chart = _chart(0.0, 5.0)      # Aries Moon
    girl_chart = _chart(0.0, 335.0)   # Pisces Moon -> 2/12, Mars/Jupiter are mutual friends

    result = calc.calculate(boy_chart, girl_chart)

    assert result["koots"]["bhakoot"]["score"] == 0
    assert result["exceptions"]["bhakoot"]["applies"] is True
    assert result["exceptions"]["bhakoot"]["adjusted_score"] == 7
    assert "2/12 Bhakoot Dosha" not in result["effective_critical_issues"]


def test_rule_profiles_change_exception_behavior():
    strict_calc = AshtakootaCalculator("classical_strict")
    balanced_calc = AshtakootaCalculator("balanced_modern")
    boy_chart = _chart(0.0, 0.5)
    girl_chart = _chart(0.0, 4.0)

    strict_result = strict_calc.calculate(boy_chart, girl_chart)
    balanced_result = balanced_calc.calculate(boy_chart, girl_chart)

    assert strict_result["exceptions"]["nadi"]["applies"] is False
    assert balanced_result["exceptions"]["nadi"]["applies"] is True


def test_engine_exposes_deterministic_evidence_objects():
    engine = KundliMatchingEngine(current_date=date(2026, 4, 29), dasha_provider=MockDashaProvider())
    result = engine.analyze(_chart(0.0, 90.0), _chart(60.0, 120.0), _birth("Boy"), _birth("Girl"))

    assert "evidence_objects" in result
    assert "items" in result["evidence_objects"]
    assert any(item["code"] == "ASHTAKOOTA_EFFECTIVE_SCORE" for item in result["evidence_objects"]["items"])
    assert any(item["category"] == "navamsa" for item in result["evidence_objects"]["items"])
    assert any(item["category"] == "timing" for item in result["evidence_objects"]["items"])


def test_engine_exposes_timing_overlay_and_joint_windows():
    engine = KundliMatchingEngine(current_date=date(2026, 4, 29), dasha_provider=MockDashaProvider())
    result = engine.analyze(_chart(0.0, 90.0), _chart(60.0, 120.0), _birth("Boy"), _birth("Girl"))

    assert "timing_overlay" in result
    assert result["timing_overlay"]["shared"]["joint_readiness_score"] >= 65
    assert result["timing_overlay"]["shared"]["current_window"]["climate"] in {"favorable", "highly_favorable"}
    assert result["recommendation"]["timing_note"]


def test_benchmark_suite_runs_and_matches_expectations():
    suite = run_benchmark_suite()

    assert len(suite) >= 4
    for case in suite:
        result = case["result"]
        expects = case["expects"]
        if "nadi_exception" in expects:
            assert result["ashtakoota"]["exceptions"]["nadi"]["applies"] is expects["nadi_exception"]
        if "effective_score_gt_raw" in expects and expects["effective_score_gt_raw"]:
            assert result["ashtakoota"]["effective_total_score"] > result["ashtakoota"]["total_score"]
        if "bhakoot_exception" in expects:
            assert result["ashtakoota"]["exceptions"]["bhakoot"]["applies"] is expects["bhakoot_exception"]
        if "critical_issue_removed" in expects:
            assert expects["critical_issue_removed"] not in result["ashtakoota"]["effective_critical_issues"]
        if "manglik_status" in expects:
            assert result["manglik"]["compatibility"]["status"] == expects["manglik_status"]
        if "pair_cancellation" in expects:
            assert result["manglik"]["compatibility"]["pair_cancellation"] is expects["pair_cancellation"]
