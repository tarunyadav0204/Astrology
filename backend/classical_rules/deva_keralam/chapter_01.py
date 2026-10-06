"""Deva Keralam Book 1 pilot: verses 2497-2498.

This is intentionally a narrow, fully explicit pilot.  It proves the matching
contract without pretending that unreviewed parts of the scanned volume are
executable.  The caller supplies canonical Nadiamsa facts; calculation belongs
to the separate astronomical fact layer.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple

from ..contextual import (
    ContextualRuleSpec,
    PrecisionRequirement,
    RuleAnchor,
    build_contextual_rule,
)
from ..engine import ClassicalRuleEngine
from ..models import ClassicalRule, PassageGroup, SourceProfile


WORK = "Deva Keralam (Chandra Kala Nadi)"
WORK_KEY = "deva_keralam"
BOOK = 1
TITLE = "Book 1 pilot: Capricorn Ascendant in Kaalaa Nadiamsa"
EDITION_KEY = "deva_keralam_volume_1_scan"
WITNESS_URL = "local-source://Deva-Keralam-1-Chandrakala-Nadi.pdf/pdf-page/240"
SOURCE_PROFILE = "deva-keralam-book-1-pdf-page-240"


def _source() -> SourceProfile:
    return SourceProfile(
        key=SOURCE_PROFILE,
        work=WORK,
        chapter=BOOK,
        chapter_title=TITLE,
        verse_start=2497,
        verse_end=2498,
        witness_url=WITNESS_URL,
        witness_policy="private_source_reference",
        numbering_note=(
            "Verse numbering, printed page 225 and PDF page 240 follow the supplied Book 1 scan. "
            "The heading and translation explicitly state Capricorn ascendant and the former half "
            "of Kaalaa Nadiamsa. Table 1 fixes Kaalaa as canonical ordinal 32; the page note gives "
            "its movable-sign span as 6°12′–6°24′."
        ),
        reference_label="Deva Keralam, Book 1, verses 2497–2498",
        edition_key=EDITION_KEY,
        pdf_pages=(240,),
        printed_pages=(225,),
        editorial_status="reviewed_clear",
    )


PILOT_SPEC = ContextualRuleSpec(
    key="DK.1.2497-2498.CAPRICORN_KAALAA_FORMER_PHYSIQUE",
    title="Physical description for Capricorn Ascendant in former-half Kaalaa Nadiamsa",
    source=_source(),
    expression={
        "op": "all",
        "children": [
            {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.sign_name", "comparator": "equals", "value": "Capricorn"},
            {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.ordinal", "comparator": "equals", "value": 32},
            {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.name", "comparator": "equals", "value": "Kaalaa"},
            {"op": "fact", "key": "deva_keralam.ascendant.nadiamsa.half", "comparator": "equals", "value": "former"},
        ],
    },
    outcome={
        "topic": "physical_description",
        "prediction_kind": "natal_promise",
        "traditional_results": [
            "The native is described as having a blood-red complexion.",
            "The native is described as having a medium build.",
            "The native is described as having a weak body.",
        ],
        "user_reading": (
            "The text associates this exact degree pattern with a warm or reddish complexion, "
            "a medium build and comparatively delicate physical strength."
        ),
        "timing": None,
        "certainty_note": "This is a source match, not a guarantee that every stated event must occur literally.",
    },
    anchors=(
        RuleAnchor("deva_keralam.ascendant.nadiamsa.sign_name", ("Capricorn",)),
        RuleAnchor("deva_keralam.ascendant.nadiamsa.ordinal", (32,)),
        RuleAnchor("deva_keralam.ascendant.nadiamsa.name", ("Kaalaa",)),
    ),
    precision_requirements=(
        PrecisionRequirement(
            "deva_keralam.ascendant.nadiamsa.birth_time_precision_warning",
            "equals",
            False,
            "The recorded birth time does not establish the Ascendant's Nadiamsa half reliably.",
        ),
    ),
    inherited_context={
        "ascendant_sign": "Capricorn",
        "ascendant_nadiamsa_ordinal": 32,
        "ascendant_nadiamsa": "Kaalaa",
        "ascendant_nadiamsa_half": "former",
        "movable_sign_degree_range": "6°12′–6°24′",
        "context_authority": "heading_translation_and_note_on_printed_page_225",
    },
    editorial_status="reviewed_clear",
    topics=("appearance", "constitution", "nadiamsa", "natal_promise"),
    scope="D1 exact Nadiamsa context",
    notes=(
        "No result is emitted for a partial match.",
        "Jupiter's Trimsamsa from verses 2494-2495 is not inherited into verses 2497-2498.",
    ),
)

PILOT_SPECS = (PILOT_SPEC,)
RULES: Tuple[ClassicalRule, ...] = tuple(build_contextual_rule(spec) for spec in PILOT_SPECS)

PASSAGE_GROUPS = (
    PassageGroup(
        key="DK.1.2497-2498.PHYSICAL_DESCRIPTION",
        verse_start=2497,
        verse_end=2498,
        title="Physical description",
        classification="exact_nadiamsa_natal_judgment",
        operational_summary=(
            "Physical-description results requiring Capricorn Ascendant in the former half of "
            "Kaalaa Nadiamsa (canonical Table 1 ordinal 32)."
        ),
        executable=True,
        review_status="published_pilot",
        rule_keys=tuple(rule.key for rule in RULES),
    ),
)


def coverage() -> Dict[str, Any]:
    return {
        "book": BOOK,
        "pilot": True,
        "catalogued_verses": 2,
        "executable_verses": 2,
        "published_rules": len(RULES),
        "source_profile": SOURCE_PROFILE,
        "book_wide_coverage_complete": False,
    }


def evaluate_book_01(
    chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    result = ClassicalRuleEngine(RULES).evaluate(chart, birth_data)
    result.update({"work": WORK, "chapter": BOOK, "coverage": coverage()})
    return result


BOOK_01 = {
    "work_key": WORK_KEY,
    "work": WORK,
    "chapter": BOOK,
    "title": TITLE,
    "source_profile": SOURCE_PROFILE,
    "witness_url": WITNESS_URL,
    "passage_groups": PASSAGE_GROUPS,
    "rules": RULES,
    "coverage_provider": coverage,
    "evaluator": evaluate_book_01,
    "contributes_reading_insights": False,
}

# Registry discovery uses a common CHAPTER_* symbol convention even when the
# source itself calls the unit a book.
CHAPTER_01 = BOOK_01
