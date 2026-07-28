from __future__ import annotations

from dataclasses import replace

import pytest

from prediction_engine.contracts import (
    ActivationBand,
    ChartManifestation,
    FomoPresentation,
    HouseActivationState,
    ManifestationHouseRole,
    Polarity,
    PredictionWindow,
)
from prediction_engine.errors import PredictionConfigurationError
from prediction_engine.fomo_presentation import (
    FomoPresentationAdapter,
    normalize_fomo_locale,
)


SUBJECTS = ("self", "mother", "father", "spouse")
TONES = (
    Polarity.SUPPORTIVE,
    Polarity.MIXED,
    Polarity.CHALLENGING,
    Polarity.NEUTRAL,
)
DOMAINS = (
    "career",
    "finance",
    "relationship",
    "property",
    "education",
    "travel",
    "health",
    "family",
    "decisions",
)


def _manifestation(
    *,
    domain: str = "career",
    subject: str = "self",
    tone: Polarity = Polarity.MIXED,
    manifestation_id: str = "manifestation-1",
    constituent_domains: tuple[str, ...] = (),
) -> ChartManifestation:
    themes = tuple(
        {
            "key": f"secret-theme-{index}",
            "label": "Secret exact theme",
            "domain": theme_domain,
        }
        for index, theme_domain in enumerate(constituent_domains)
    )
    return ChartManifestation(
        manifestation_id=manifestation_id,
        signature_key="secret_exact_signature",
        subject=subject,
        domain=domain,
        label="Secret exact manifestation",
        window=PredictionWindow(
            "2026-07-21", "2026-08-12", "Saturn", "Rahu", "Saturn", "sig"
        ),
        house_roles=(),
        subject_confirmation={},
        carrier_planets=("Saturn",),
        carrier_coherence="shared_direct_carrier",
        carrier_relationships=(),
        activation_band=ActivationBand.STRONG,
        outcome_tone=tone,
        synthesis_strength="high",
        summary="Secret exact synthesized outcome",
        possibilities=("Secret concrete event",),
        helpful_reasons=(),
        pressure_reasons=(),
        mixed_reasons=(),
        rationale=("Secret astrological trace",),
        rule_id="test",
        constituent_themes=themes,
    )


def _house_role(native_house: int, relative_house: int) -> ManifestationHouseRole:
    return ManifestationHouseRole(
        native_house=native_house,
        relative_house=relative_house,
        role="test role",
        activation_state=HouseActivationState.FULLY_REINFORCED,
        activation_band=ActivationBand.STRONG,
        outcome_tone=Polarity.CHALLENGING,
        direct_carriers=("Saturn",),
        dasha_connections=(),
        transit_connections=(),
    )


@pytest.mark.parametrize("locale", ("en", "hi"))
@pytest.mark.parametrize("tone", TONES)
@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("domain", DOMAINS)
def test_every_supported_combination_has_explicit_copy(
    locale,
    tone,
    subject,
    domain,
):
    presentation = FomoPresentationAdapter().present(
        (_manifestation(domain=domain, subject=subject, tone=tone),),
        locale=locale,
    )[0]

    assert isinstance(presentation, FomoPresentation)
    assert presentation.title.strip()
    assert presentation.teaser.strip()
    assert presentation.suggested_question.strip()
    assert presentation.tone == tone
    assert presentation.locale == locale


def test_copy_cannot_leak_manifestation_or_astrological_trace():
    manifestation = _manifestation()
    presentation = FomoPresentationAdapter().present(
        (manifestation,), locale="en"
    )[0]
    visible = " ".join((
        presentation.title,
        presentation.teaser,
        presentation.suggested_question,
    )).lower()

    for forbidden in (
        manifestation.label,
        manifestation.summary,
        *manifestation.possibilities,
        *manifestation.rationale,
        "saturn",
        "rahu",
        "house 10",
        "h10",
        "mahadasha",
        "antardasha",
        "2026-07-21",
        "2026-08-12",
    ):
        assert forbidden.lower() not in visible
    assert not hasattr(presentation, "date_band")


def test_tone_changes_wording_without_changing_the_concealed_area():
    adapter = FomoPresentationAdapter()
    presentations = [
        adapter.present((_manifestation(tone=tone),), locale="en")[0]
        for tone in TONES
    ]

    assert len({row.title for row in presentations}) == len(TONES)
    assert len({row.teaser for row in presentations}) == len(TONES)
    assert all("career direction" in row.title.lower() for row in presentations)


def test_combined_manifestation_uses_declared_constituent_domains():
    manifestation = _manifestation(
        domain="combined",
        constituent_domains=("finance", "property"),
    )
    presentation = FomoPresentationAdapter().present(
        (manifestation,), locale="en"
    )[0]

    assert "financial priorities and home and living situation" in (
        presentation.title.lower()
    )
    assert presentation.domain == "combined"


def test_three_domains_name_the_broad_areas_without_revealing_the_event():
    manifestation = _manifestation(
        domain="combined",
        constituent_domains=("finance", "property", "relationship"),
    )
    presentation = FomoPresentationAdapter().present(
        (manifestation,), locale="en"
    )[0]

    title = presentation.title.lower()
    assert "financial priorities" in title
    assert "home and living situation" in title
    assert "relationship direction" in title
    assert "secret exact" not in title


def test_many_domains_name_four_areas_then_use_a_compact_overflow_phrase():
    manifestation = _manifestation(
        domain="combined",
        constituent_domains=(
            "finance",
            "property",
            "relationship",
            "family",
            "career",
        ),
    )
    presentation = FomoPresentationAdapter().present(
        (manifestation,), locale="en"
    )[0]

    title = presentation.title.lower()
    assert "financial priorities" in title
    assert "home and living situation" in title
    assert "relationship direction" in title
    assert "family priorities" in title
    assert "other connected matters" in title
    assert "career direction" not in title


def test_hindi_combined_copy_names_the_activated_areas_for_a_relative():
    manifestation = _manifestation(
        domain="combined",
        subject="mother",
        constituent_domains=("finance", "property", "relationship"),
    )
    presentation = FomoPresentationAdapter().present(
        (manifestation,), locale="hi"
    )[0]

    assert "आपकी माता" in presentation.title
    assert "आर्थिक प्राथमिकताओं" in presentation.title
    assert "घर और रहने की स्थिति" in presentation.title
    assert "रिश्तों" in presentation.title


def test_relative_teaser_areas_come_from_relative_houses_not_generic_domains():
    spouse = replace(
        _manifestation(
            domain="combined",
            subject="spouse",
            constituent_domains=("finance", "education"),
            manifestation_id="spouse-manifestation",
        ),
        house_roles=(
            _house_role(8, 2),
            _house_role(11, 5),
        ),
        constituent_themes=(
            {"key": "finance", "domain": "finance", "required_native_houses": (8,)},
            {"key": "learning", "domain": "education", "required_native_houses": (11,)},
        ),
    )
    mother = replace(
        _manifestation(
            domain="combined",
            subject="mother",
            constituent_domains=("finance", "education"),
            manifestation_id="mother-manifestation",
        ),
        house_roles=(
            _house_role(8, 5),
            _house_role(11, 8),
        ),
        constituent_themes=(
            {"key": "learning", "domain": "education", "required_native_houses": (8,)},
            {"key": "shared", "domain": "finance", "required_native_houses": (11,)},
        ),
    )

    spouse_title = FomoPresentationAdapter().present(
        (spouse,), locale="en"
    )[0].title.lower()
    mother_title = FomoPresentationAdapter().present(
        (mother,), locale="en"
    )[0].title.lower()

    assert "family finances and speech" in spouse_title
    assert "learning, children, and creativity" in spouse_title
    assert "learning, children, and creativity" in mother_title
    assert "shared finances and major adjustments" in mother_title
    assert "family finances and speech" not in mother_title


def test_presentation_ids_and_copy_are_deterministic():
    adapter = FomoPresentationAdapter()
    manifestation = _manifestation()

    first = adapter.present((manifestation,), locale="english")[0]
    second = adapter.present((manifestation,), locale="en-IN")[0]

    assert first == second
    assert first.manifestation_id == manifestation.manifestation_id


def test_hindi_is_an_explicit_template_not_an_english_fallback():
    presentation = FomoPresentationAdapter().present(
        (_manifestation(subject="mother"),), locale="hindi"
    )[0]

    assert presentation.locale == "hi"
    assert any("\u0900" <= character <= "\u097f" for character in presentation.title)
    assert "मेरी माता" in presentation.suggested_question
    assert "अगले कुछ महीनों" in presentation.suggested_question


@pytest.mark.parametrize("tone", TONES)
def test_chat_question_asks_about_the_manifestation_window_not_a_general_reading(tone):
    presentation = FomoPresentationAdapter().present(
        (_manifestation(tone=tone),),
        locale="en",
    )[0]

    assert "over the next few months" in presentation.suggested_question
    assert "when is it most likely" in presentation.suggested_question
    assert "what is my chart asking me" not in presentation.suggested_question.lower()


def test_unsupported_locale_fails_instead_of_falling_back():
    with pytest.raises(PredictionConfigurationError):
        normalize_fomo_locale("fr")


def test_missing_domain_template_fails_instead_of_falling_back():
    manifestation = replace(_manifestation(), domain="unregistered_domain")

    with pytest.raises(PredictionConfigurationError):
        FomoPresentationAdapter().present((manifestation,), locale="en")


def test_invalid_combined_manifestation_fails_instead_of_falling_back():
    manifestation = _manifestation(
        domain="combined",
        constituent_domains=("finance",),
    )

    with pytest.raises(PredictionConfigurationError):
        FomoPresentationAdapter().present((manifestation,), locale="en")


def test_no_manifestation_produces_no_fallback_copy():
    assert FomoPresentationAdapter().present((), locale="en") == ()
