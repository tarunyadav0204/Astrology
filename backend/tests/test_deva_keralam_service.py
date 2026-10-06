from classical_rules.deva_keralam.service import match_deva_keralam_chart


def _capricorn_kaalaa_chart(ascendant=276.25):
    # Capricorn is movable.  6°12′–6°24′ is physical division / ordinal 32;
    # 6°15′ lies in its former half.
    return {
        "ascendant": ascendant,
        "planets": {
            "Sun": {"longitude": 10.0},
            "Moon": {"longitude": 45.0},
        },
    }


def test_service_calculates_facts_and_matches_reviewed_pilot_end_to_end():
    result = match_deva_keralam_chart(
        _capricorn_kaalaa_chart(),
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 60},
    )

    assert result["contract_version"] == "deva-keralam-matcher/1.0.0"
    assert result["status"] == "matched"
    assert result["fallback_used"] is False
    assert result["precision_basis"]["status"] == "supplied_longitude_uncertainty"
    assert result["summary"]["counts"] == {
        "matched": 1,
        "not_matched": 0,
        "unavailable": 0,
    }

    facts = result["facts"]["facts"]
    assert facts["deva_keralam.ascendant.nadiamsa.sign_name"]["value"] == "Capricorn"
    assert facts["deva_keralam.ascendant.nadiamsa.ordinal"]["value"] == 32
    assert facts["deva_keralam.ascendant.nadiamsa.name"]["value"] == "Kaalaa"
    assert facts["deva_keralam.ascendant.nadiamsa.half"]["value"] == "former"
    assert facts["deva_keralam.ascendant.nadiamsa.birth_time_precision_warning"]["value"] is False

    row = result["results"][0]
    assert row["applicability"] == "matched"
    assert row["source"]["reference"] == "Deva Keralam, Book 1, verses 2497–2498"
    assert row["source"]["pdf_pages"] == [240]
    assert row["evidence"]["outcome"]["topic"] == "physical_description"
    assert len(row["evidence"]["premises"]) == 4


def test_service_returns_unavailable_at_exact_half_boundary():
    result = match_deva_keralam_chart(
        _capricorn_kaalaa_chart(276.3),
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 0},
    )

    assert result["status"] == "unavailable"
    assert result["summary"]["unavailable_rule_keys"] == [
        "DK.1.2497-2498.CAPRICORN_KAALAA_FORMER_PHYSIQUE"
    ]
    row = result["results"][0]
    assert row["applicability"] == "unavailable"
    assert "does not establish" in row["evidence"]["reason"]
    precision = result["facts"]["facts"][
        "deva_keralam.ascendant.nadiamsa.precision_status"
    ]
    assert precision["value"] == "boundary"


def test_service_does_not_assume_birth_time_precision_when_context_is_absent():
    result = match_deva_keralam_chart(_capricorn_kaalaa_chart())
    assert result["status"] == "unavailable"
    assert result["precision_basis"]["status"] == "unverified_not_supplied"
    assert result["results"][0]["applicability"] == "unavailable"


def test_service_returns_not_matched_for_a_secure_different_nadiamsa():
    result = match_deva_keralam_chart(
        _capricorn_kaalaa_chart(276.45),
        birth_context={"ascendant_longitude_uncertainty_arcseconds": 60},
    )
    assert result["status"] == "not_matched"
    assert result["summary"]["counts"]["not_matched"] == 1
    assert result["results"][0]["applicability"] == "not_matched"


def test_clock_time_precision_requires_local_rate_and_can_be_derived():
    without_rate = match_deva_keralam_chart(
        _capricorn_kaalaa_chart(),
        birth_context={"birth_time_uncertainty_seconds": 20},
    )
    assert without_rate["status"] == "unavailable"
    assert without_rate["precision_basis"]["status"] == "unverified_missing_local_ascensional_rate"

    with_rate = match_deva_keralam_chart(
        _capricorn_kaalaa_chart(),
        birth_context={
            "birth_time_uncertainty_seconds": 20,
            "ascendant_rate_degrees_per_second": 1 / 600,
        },
    )
    assert with_rate["status"] == "matched"
    assert with_rate["precision_basis"]["ascendant_longitude_uncertainty_arcseconds"] == 120.0
