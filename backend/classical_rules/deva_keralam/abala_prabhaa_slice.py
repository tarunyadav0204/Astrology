"""Reviewed executable slice: Abala/Prabhaa Nadiamsa, verses 54-96.

The supplied edition spans PDF pages 32-36 (printed pages 7-11).  Every
candidate below is tied to the reviewed context reconstruction.  Only natal
conditions that the current fact contract can express without inference are
compiled.  The rest remain explicit rejections, rather than partial rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

from ..contextual import PrecisionRequirement
from ..engine import ClassicalRuleEngine
from ..models import ClassicalRule, SourceProfile
from .review_compiler import (
    CompilationResult,
    ReviewedRuleCandidate,
    compile_reviewed_batch,
)


WORK = "Deva Keralam (Chandra Kala Nadi)"
EDITION_KEY = "deva_keralam_volume_1_scan"
CONTEXT_BLOCK_KEY = "DK1.CTX.ABALA_PRABHA.V0054-0096"
WITNESS = "local-source://Deva-Keralam-1-Chandrakala-Nadi.pdf"


PRECISION = (
    PrecisionRequirement(
        "deva_keralam.precision.ascendant.reliable",
        "equals",
        True,
        "The recorded birth time does not establish the Ascendant Nadiamsa reliably.",
    ),
)


def _fact(key: str, value: Any, comparator: str = "equals") -> Dict[str, Any]:
    return {"op": "fact", "key": key, "comparator": comparator, "value": value}


def _all(*conditions: Mapping[str, Any]) -> Dict[str, Any]:
    return {"op": "all", "children": [dict(condition) for condition in conditions]}


def _base(*conditions: Mapping[str, Any], half: Optional[str] = None) -> Dict[str, Any]:
    rows = [
        _fact("deva_keralam.ascendant.nadiamsa.ordinal", 16),
        _fact("deva_keralam.ascendant.nadiamsa.name", "Prabhaa"),
        *conditions,
    ]
    if half:
        rows.append(_fact("deva_keralam.ascendant.nadiamsa.half", half))
    return _all(*rows)


def _fixed(*conditions: Mapping[str, Any], half: Optional[str] = None) -> Dict[str, Any]:
    return _base(
        _fact("deva_keralam.ascendant.nadiamsa.sign_modality", "fixed"),
        *conditions,
        half=half,
    )


def _taurus_aries(*conditions: Mapping[str, Any], half: Optional[str] = None) -> Dict[str, Any]:
    if half is not None:
        raise ValueError("The Taurus/Aries Navamsa branch is independent of the Abala half branches")
    return _all(
        _fact("deva_keralam.ascendant.rashi.name", "Taurus"),
        _fact("deva_keralam.ascendant.navamsa.name", "Aries"),
        *conditions,
    )


def _taurus_prabhaa(*conditions: Mapping[str, Any], half: Optional[str] = None) -> Dict[str, Any]:
    return _base(
        _fact("deva_keralam.ascendant.rashi.name", "Taurus"),
        *conditions,
        half=half,
    )


def _expression_uses_nadiamsa(expression: Mapping[str, Any]) -> bool:
    if str(expression.get("op") or "").lower() == "fact":
        return str(expression.get("key") or "").startswith("deva_keralam.ascendant.nadiamsa.")
    return any(_expression_uses_nadiamsa(child) for child in expression.get("children") or ())


def _source(start: int, end: int, pdf_pages: Tuple[int, ...], *, qualified: bool = False) -> SourceProfile:
    printed = tuple(page - 25 for page in pdf_pages)
    return SourceProfile(
        key=f"deva-keralam-book-1-v{start:04d}-{end:04d}",
        work=WORK,
        chapter=1,
        chapter_title="Abala (Prabhaa) Nadiamsa",
        verse_start=start,
        verse_end=end,
        witness_url=f"{WITNESS}/pdf-page/{pdf_pages[0]}",
        witness_policy="private_source_reference",
        numbering_note=(
            "Verse and page numbering follow the supplied Santhanam Book I scan. "
            "The edition identifies Abala with canonical Table 1 Prabhaa, ordinal 16."
        ),
        reference_label=f"Deva Keralam, Book 1, verses {start}" if start == end else f"Deva Keralam, Book 1, verses {start}-{end}",
        edition_key=EDITION_KEY,
        pdf_pages=pdf_pages,
        printed_pages=printed,
        editorial_status="reviewed_interpreted" if qualified else "reviewed_clear",
    )


def _outcome(topic: str, *results: str) -> Dict[str, Any]:
    return {
        "topic": topic,
        "prediction_kind": "natal_promise",
        "traditional_results": list(results),
        "timing": None,
        "certainty_note": "This is an exact source match, not a guarantee that every statement must occur literally.",
    }


def _candidate(
    key: str,
    title: str,
    start: int,
    end: int,
    pages: Tuple[int, ...],
    expression: Mapping[str, Any],
    outcome: Mapping[str, Any],
    *,
    context_status: str = "verified",
    qualified: bool = False,
    notes: Tuple[str, ...] = (),
    **kwargs: Any,
) -> ReviewedRuleCandidate:
    uses_nadiamsa = _expression_uses_nadiamsa(expression)
    return ReviewedRuleCandidate(
        key=key,
        title=title,
        passage_key=f"DK1.PASSAGE.V{start:04d}-{end:04d}",
        context_block_key=CONTEXT_BLOCK_KEY,
        source=_source(start, end, pages, qualified=qualified),
        expression=expression,
        outcome=outcome,
        precision_requirements=PRECISION if uses_nadiamsa else (),
        context_status=context_status,
        context_qualification_acknowledged=qualified,
        inherited_context=(
            {
                "canonical_nadiamsa": "Prabhaa",
                "source_section_name": "Abala",
                "canonical_ordinal": 16,
                "fixed_sign_span": "26°48′-27°00′",
            }
            if uses_nadiamsa else
            {
                "section": "Abala/Prabhaa",
                "independent_branch": "Taurus Ascendant with Aries Navamsa",
            }
        ),
        topics=(
            (str(outcome.get("topic") or "natal_promise"), "nadiamsa", "natal_promise")
            if uses_nadiamsa else
            (str(outcome.get("topic") or "natal_promise"), "navamsa", "natal_promise")
        ),
        notes=(
            (("Abala is resolved through the edition-reviewed alias to Table 1 Prabhaa.",) if uses_nadiamsa else (
                "The Taurus/Aries Navamsa statement is an independent branch; Abala Nadiamsa is not added cumulatively.",
            ))
            + notes
        ),
        **kwargs,
    )


# These twelve candidates have explicit scope, supported natal conditions and
# no unresolved textual alternative or unsupported timing dependency.
APPROVED_CANDIDATES: Tuple[ReviewedRuleCandidate, ...] = (
    _candidate(
        "DK.1.54-55.PRABHAA_FORMER_DESCRIPTION",
        "Description for former-half Prabhaa in a fixed Ascendant",
        54, 55, (32,), _fixed(half="former"),
        _outcome(
            "appearance_and_temperament",
            "The text describes a dark complexion and lean build.",
            "It describes happiness, gentleness in childhood and affection for an elder brother.",
            "It associates help from a brother-in-law with foreign residence and prosperity.",
            "The source also uses a historical Brahmin social classification.",
        ),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.56.PRABHAA_COBORNS_TAURUS_AQUARIUS",
        "After-born sibling indication with Mars in H1 and Jupiter in H5",
        56, 56, (33,),
        _fixed(
            _fact("deva_keralam.ascendant.rashi.name", ["Taurus", "Aquarius"], "in"),
            _fact("deva_keralam.planet.Mars.house", 1),
            _fact("deva_keralam.planet.Jupiter.house", 5),
        ),
        _outcome("siblings", "The text denies a surviving younger sibling under this configuration."),
        context_status="qualified", qualified=True,
        notes=(
            "The edition explicitly calls this application safe for Taurus and Aquarius; Leo and Scorpio are excluded pending the scrutiny required by its note.",
        ),
    ),
    _candidate(
        "DK.1.57.PRABHAA_FORMER_FAMILY",
        "Family indications for former-half Prabhaa",
        57, 57, (33,), _fixed(half="former"),
        _outcome(
            "family",
            "The text gives two sisters and one brother.",
            "It describes a passionate temperament and reduced happiness through father and mother.",
        ),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.58.PRABHAA_FORMER_ELDER_BROTHER",
        "Elder-brother indication for former-half Prabhaa",
        58, 58, (33,), _fixed(half="former"),
        _outcome("siblings", "The text gives longevity to the elder brother."),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.58.PRABHAA_LATTER_PARENTS",
        "Parent indication for latter-half Prabhaa",
        58, 58, (33,), _fixed(half="latter"),
        _outcome("parents", "The text gives long life to both parents."),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.59-60.PRABHAA_LATTER_HOME_PROSPERITY",
        "Home-country prosperity for latter-half Prabhaa",
        59, 60, (33,), _fixed(half="latter"),
        _outcome(
            "residence_and_prosperity",
            "The text associates the latter half with prosperity in the birth country.",
            "It also describes leaving during upheaval and later returning.",
        ),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.61-62.PRABHAA_TAURUS_ARIES_NAVAMSA_PROSPERITY",
        "Prosperity for Taurus Ascendant with Aries Navamsa",
        61, 62, (34,), _taurus_aries(),
        _outcome(
            "prosperity",
            "The text associates this pattern with prosperity in a pilgrimage centre and increasing prosperity in the Andhra region.",
        ),
    ),
    _candidate(
        "DK.1.66.PRABHAA_FORMER_SATURN_ASPECTS_H12",
        "Marriage indication when Saturn aspects H12",
        66, 66, (34,),
        _taurus_prabhaa(_fact("deva_keralam.planet.Saturn.aspected_houses", 12, "contains"), half="former"),
        _outcome(
            "marriage",
            "The text gives two marriages and describes financial hardship for the first spouse.",
        ),
    ),
    _candidate(
        "DK.1.67.PRABHAA_FORMER_PROGENY_OBSTACLE",
        "Progeny obstacles with fifth lord joined Rahu and Saturn in H11",
        67, 67, (34,),
        _taurus_prabhaa(
            _fact("deva_keralam.relationship.conjunction.Mercury.Rahu.present", True),
            _fact("deva_keralam.planet.Saturn.house", 11),
            half="former",
        ),
        _outcome("children", "The text describes obstacles in obtaining progeny."),
    ),
    _candidate(
        "DK.1.68.PRABHAA_LATTER_CHILDREN",
        "Children indication for latter-half Prabhaa",
        68, 68, (34,), _taurus_prabhaa(half="latter"),
        _outcome(
            "children",
            "The text describes considerable enjoyment, one child, and no later childbirth through the wife.",
        ),
    ),
    _candidate(
        "DK.1.78.PRABHAA_FORMER_RELATIVE_SUPPORT",
        "Relative support for former-half Prabhaa",
        78, 78, (35,), _fixed(half="former"),
        _outcome("family_support", "The text associates childhood wealth and happiness with paternal and maternal relatives."),
        context_status="qualified", qualified=True,
    ),
    _candidate(
        "DK.1.78.PRABHAA_LATTER_SISTERS",
        "Sister indications for latter-half Prabhaa",
        78, 78, (35,), _fixed(half="latter"),
        _outcome("siblings", "The text gives two sisters and describes their daughters as virtuous."),
        context_status="qualified", qualified=True,
    ),
)


def _rejected(
    key: str,
    start: int,
    end: int,
    pages: Tuple[int, ...],
    *,
    expression: Optional[Mapping[str, Any]] = None,
    timing_kind: str = "none",
    source_disputes: Tuple[str, ...] = (),
    inherited_ambiguities: Tuple[str, ...] = (),
) -> ReviewedRuleCandidate:
    return _candidate(
        key, f"Rejected reviewed passage {start}-{end}", start, end, pages,
        expression or _base(), _outcome("review_only", "Not executable."),
        timing_kind=timing_kind,
        source_disputes=source_disputes,
        inherited_ambiguities=inherited_ambiguities,
    )


# This audit covers every remaining premise family in verses 54-96.  Rejected
# records are useful: they prove why the compiler did not turn nearby prose
# into an executable rule.
REJECTED_CANDIDATES: Tuple[ReviewedRuleCandidate, ...] = (
    _rejected("DK.1.59-60.FORMER.TIMING", 59, 60, (33,), timing_kind="ordinal_dasha_and_childhood"),
    _rejected("DK.1.61-62.FATHER.THIRD", 61, 62, (34,), inherited_ambiguities=("The second one-third subdivision is not available in the canonical Nadiamsa fact contract.",)),
    _rejected("DK.1.63.SAMPATH_DASHA", 63, 63, (34,), timing_kind="ordinal_dasha"),
    _rejected("DK.1.64.MALEFIC_BHUKTI", 64, 64, (34,), timing_kind="relative_house_dasha_bhukti"),
    _rejected("DK.1.65.TEXTUAL_ALTERNATIVE", 65, 65, (34,), source_disputes=("The edition records Moon in Abala and Saturn in Abala as alternative readings.",)),
    _rejected(
        "DK.1.69-72.MALEFIC_ASPECT_COUNT", 69, 72, (34,),
        expression=_taurus_prabhaa(_fact("deva_keralam.planet.Jupiter.receives_malefic_aspect_count", 2), half="former"),
    ),
    _rejected("DK.1.73-75.BLEMISH", 73, 75, (34,), inherited_ambiguities=("The phrase 'blemish caused by the Sun' lacks a deterministic canonical condition.",)),
    _rejected(
        "DK.1.76.THIRD_LORD_NAVAMSA_DIGNITY", 76, 76, (34,),
        expression=_fixed(_fact("deva_keralam.house.3.lord_navamsa_dignity", "debilitated")),
    ),
    _rejected("DK.1.77.SISTER_CHILDREN", 77, 77, (34,), inherited_ambiguities=("It is unclear whether verse 77 inherits the planetary premise of verse 76.",)),
    _rejected(
        "DK.1.79-80.NIRMALA_ALIAS", 79, 80, (35,),
        expression=_fixed(_fact("deva_keralam.house.3.lord_nadiamsa_name", "Nirmala")),
    ),
    _rejected(
        "DK.1.81-84.MOTHER", 81, 84, (35,), timing_kind="dasha_and_age",
        source_disputes=("The source gives two alternative Saturn/malefic configurations and multiple alternative ages.",),
    ),
    _rejected("DK.1.85-87.THIRD_DASHA", 85, 87, (35,), timing_kind="ordinal_dasha"),
    _rejected(
        "DK.1.88-92.AQUARIUS_RUN", 88, 92, (36,), timing_kind="age_and_ordinal_dasha",
        inherited_ambiguities=("The Nirmala spelling and the combined Rasi/Navamsa dignity branch require separate reviewed canonical premises.",),
    ),
    _rejected(
        "DK.1.93.MISSING_LINE", 93, 93, (36,), timing_kind="ordinal_dasha_and_age",
        source_disputes=("The edition explicitly says the first line of verse 93 is missing in the original.",),
    ),
    _rejected("DK.1.94-96.TIMING", 94, 96, (36,), timing_kind="age_transit_dasha_and_death"),
)


ALL_CANDIDATES = (*APPROVED_CANDIDATES, *REJECTED_CANDIDATES)
COMPILATION_RESULTS: Tuple[CompilationResult, ...] = compile_reviewed_batch(ALL_CANDIDATES)
RULES: Tuple[ClassicalRule, ...] = tuple(row.rule for row in COMPILATION_RESULTS if row.rule is not None)
REJECTIONS: Tuple[CompilationResult, ...] = tuple(row for row in COMPILATION_RESULTS if not row.compiled)


@dataclass(frozen=True)
class RuleFixture:
    rule_key: str
    kind: str
    chart: Mapping[str, Any]
    expected_applicability: str


def _leaf_facts(expression: Mapping[str, Any]) -> Dict[str, Any]:
    facts: Dict[str, Any] = {}
    operator = str(expression.get("op") or "").lower()
    if operator == "fact":
        comparator = str(expression.get("comparator") or "equals")
        expected = expression.get("value")
        if comparator == "equals":
            facts[str(expression["key"])] = expected
        elif comparator == "in":
            facts[str(expression["key"])] = list(expected)[0]
        elif comparator == "contains":
            facts[str(expression["key"])] = [expected]
        return facts
    for child in expression.get("children") or ():
        facts.update(_leaf_facts(child))
    return facts


def _fixtures() -> Tuple[RuleFixture, ...]:
    rows = []
    specs = {row.rule.key: row.spec for row in COMPILATION_RESULTS if row.rule and row.spec}
    for rule in RULES:
        spec = specs[rule.key]
        facts = _leaf_facts(spec.expression)
        facts["deva_keralam.precision.ascendant.reliable"] = True
        rows.append(RuleFixture(rule.key, "positive", {"classical_facts": dict(facts)}, "matched"))
        negative = dict(facts)
        if "deva_keralam.ascendant.nadiamsa.name" in negative:
            negative["deva_keralam.ascendant.nadiamsa.name"] = "Kaalaa"
        elif "deva_keralam.ascendant.navamsa.name" in negative:
            negative["deva_keralam.ascendant.navamsa.name"] = "Pisces"
        else:
            negative["deva_keralam.ascendant.rashi.name"] = "Gemini"
        rows.append(RuleFixture(rule.key, "negative", {"classical_facts": negative}, "not_matched"))
    return tuple(rows)


FIXTURES = _fixtures()


def evaluate_slice(chart: Mapping[str, Any], birth_data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Evaluate only the reviewed slice; this is not a global registry hook."""
    result = ClassicalRuleEngine(RULES).evaluate(chart, birth_data)
    result["coverage"] = coverage()
    return result


def coverage() -> Dict[str, Any]:
    return {
        "context_block_key": CONTEXT_BLOCK_KEY,
        "verse_start": 54,
        "verse_end": 96,
        "reviewed_candidates": len(ALL_CANDIDATES),
        "compiled_rules": len(RULES),
        "rejected_candidates": len(REJECTIONS),
        "globally_registered": False,
    }
