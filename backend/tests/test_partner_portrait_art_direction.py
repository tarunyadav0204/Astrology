import pytest

from partner_profile.art_direction import partner_presentation, visual_context_for_country


@pytest.mark.parametrize(
    ("native_gender", "expected"),
    [("Male", "feminine"), ("M", "feminine"), ("Female", "masculine"), ("F", "masculine")],
)
def test_partner_gender_is_derived_from_saved_chart_gender(native_gender, expected):
    assert partner_presentation(native_gender) == expected


def test_missing_or_unsupported_gender_is_not_guessed():
    with pytest.raises(ValueError, match="Male or Female"):
        partner_presentation("")
    with pytest.raises(ValueError, match="Male or Female"):
        partner_presentation("other")


@pytest.mark.parametrize(
    ("country_code", "expected"),
    [
        ("IN", "south_asian"),
        ("GB", "european"),
        ("US", "north_american"),
        ("BR", "latin_american"),
        ("JP", "east_southeast_asian"),
        ("NG", "sub_saharan_african"),
        ("AE", "middle_eastern_north_african"),
        ("KZ", "central_asian"),
        ("AU", "oceania"),
    ],
)
def test_country_controls_regional_art_direction(country_code, expected):
    assert visual_context_for_country(country_code) == expected


def test_unmapped_country_uses_declared_global_context():
    assert visual_context_for_country("AQ") == "global_mixed"
