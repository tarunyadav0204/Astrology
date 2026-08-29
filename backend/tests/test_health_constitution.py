from calculators.constitution_calculator import (
    GRAHA_DOSHA,
    compute_constitution_profile,
    constitution_profile_from_doshas,
    mercury_dosha,
    nakshatra_dosha,
    nakshatra_from_longitude,
    rashi_dosha,
)


def test_fire_water_air_earth_rashi_vectors():
    assert rashi_dosha(0)["Pitta"] == 1.0  # Aries
    assert rashi_dosha("Cancer")["Kapha"] == 1.0
    assert rashi_dosha(2)["Vata"] == 1.0  # Gemini
    earth = rashi_dosha("Taurus")
    assert earth["Vata"] == 0.5
    assert earth["Kapha"] == 0.5
    assert earth["Pitta"] == 0.0


def test_nakshatra_cycle_lists():
    assert nakshatra_dosha("Ashwini")["Vata"] == 1.0
    assert nakshatra_dosha("Bharani")["Pitta"] == 1.0
    assert nakshatra_dosha("Rohini")["Kapha"] == 1.0
    assert nakshatra_from_longitude(0) == "ashwini"
    assert nakshatra_dosha(nakshatra_from_longitude(20))["Pitta"] == 1.0  # Bharani


def test_venus_and_moon_are_kapha_predominant_vata():
    assert GRAHA_DOSHA["Venus"] == {"Vata": 0.3, "Pitta": 0.0, "Kapha": 0.7}
    assert GRAHA_DOSHA["Moon"] == {"Vata": 0.3, "Pitta": 0.0, "Kapha": 0.7}
    assert GRAHA_DOSHA["Ketu"]["Pitta"] == 1.0
    assert GRAHA_DOSHA["Ketu"]["Vata"] == 0.0


def test_isolated_mercury_is_tridoshic():
    isolated = mercury_dosha({"Mercury": {"sign": 2, "longitude": 65}})
    assert isolated == GRAHA_DOSHA["Mercury"]


def test_mercury_inherits_closest_same_sign_planet():
    inherited = mercury_dosha({
        "Mercury": {"sign": 2, "longitude": 65},
        "Saturn": {"sign": 2, "longitude": 68},
        "Jupiter": {"sign": 5, "longitude": 160},
    })
    assert inherited == GRAHA_DOSHA["Saturn"]


def test_pure_when_any_dosha_is_at_least_50():
    profile = constitution_profile_from_doshas({"Pitta": 52, "Vata": 28, "Kapha": 20})
    assert profile["kind"] == "primary"
    assert profile["display"] == "Pure Pitta"
    assert profile["primary"] == "Pitta"


def test_dual_when_top_two_are_close_and_both_above_35():
    profile = constitution_profile_from_doshas({"Vata": 42, "Pitta": 38, "Kapha": 20})
    assert profile["kind"] == "dual"
    assert profile["display"] == "Vata-Pitta"
    assert profile["primary"] == "Vata"
    assert profile["secondary"] == "Pitta"


def test_tridoshic_when_all_three_sit_in_the_sama_band():
    profile = constitution_profile_from_doshas({"Pitta": 34, "Vata": 33, "Kapha": 33})
    assert profile["kind"] == "tridoshic"
    assert profile["label"] == "Tridoshic"


def test_fallback_primary_when_leader_is_clear_but_under_50():
    profile = constitution_profile_from_doshas({"Pitta": 48, "Vata": 30, "Kapha": 22})
    assert profile["kind"] == "primary"
    assert profile["display"] == "Pitta"


def test_aries_lagna_without_planets_is_pure_pitta():
    profile = compute_constitution_profile({"ascendant": 5.0, "planets": {}})
    assert profile["method"] == "prakriti_v1"
    assert profile["display"] == "Pure Pitta"
    assert profile["dosha_balance"]["Pitta"] == 66.7
    assert profile["dosha_balance"]["Vata"] == 16.7
    assert profile["dosha_balance"]["Kapha"] == 16.7


def test_focal_weights_are_applied_on_a_full_synthetic_chart():
    chart = {
        "ascendant": 5.0,
        "houses": [{"house": i + 1, "sign": i} for i in range(12)],
        "planets": {
            "Sun": {"sign": 4, "longitude": 125},
            "Moon": {"sign": 3, "longitude": 95},
            "Mars": {"sign": 0, "longitude": 12},
            "Mercury": {"sign": 2, "longitude": 65},
            "Jupiter": {"sign": 8, "longitude": 250},
            "Venus": {"sign": 1, "longitude": 40},
            "Saturn": {"sign": 10, "longitude": 310},
        },
    }
    profile = compute_constitution_profile(chart)
    total = sum(profile["dosha_balance"].values())
    assert abs(total - 100) < 0.2
    applied = [row["id"] for row in profile["components"] if row["applied"]]
    assert applied[0] == "lagna_sign"
    assert "lagna_lord" in applied
    assert "moon" in applied
    assert "sun" in applied
    assert "sixth" in applied
    assert set(applied).issuperset({"mars", "mercury", "jupiter", "venus", "saturn"})
