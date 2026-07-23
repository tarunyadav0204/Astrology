from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Tuple

from .contracts import InterpretationAlternative, OutcomeAssessment, Polarity
from .subjects import SUBJECTS


HOUSE_SIGNIFICATION_REGISTRY_VERSION = "1.2.0"


@dataclass(frozen=True)
class HouseSignification:
    house: int
    label: str
    manifestations: Sequence[str]


@dataclass(frozen=True)
class HouseCombination:
    key: str
    relative_houses: Sequence[int]
    focus_relative_houses: Sequence[int]
    label: str
    manifestations: Sequence[str]


HOUSE_SIGNIFICATIONS: Dict[int, HouseSignification] = {
    1: HouseSignification(1, "identity, vitality and new direction", (
        "a personal beginning or change of direction", "attention to vitality or appearance",
        "greater independence or self-definition", "attention to the head, brain or overall physical constitution",
    )),
    2: HouseSignification(2, "savings, accumulated resources, family and speech", (
        "a savings or accumulated-resource matter", "a family responsibility or development",
        "an important conversation, food habit or question of values",
        "attention to the face, mouth, teeth, tongue, throat or food intake",
    )),
    3: HouseSignification(3, "effort, skills, communication and siblings", (
        "a communication, document or skills matter", "a new personal effort or initiative",
        "a sibling-related development or short journey", "attention to the shoulders, arms, hands, ears or breathing",
    )),
    4: HouseSignification(4, "home, property, education and inner stability", (
        "a home, residence or property matter", "education or foundational learning",
        "a matter involving mother, comfort or emotional security", "attention to the chest, breasts, lungs or emotional wellbeing",
    )),
    5: HouseSignification(5, "children, intelligence, creativity and learning", (
        "a child-related or creative development", "study, examination or application of intelligence",
        "a considered risk, counsel or speculative decision", "attention to the heart, upper abdomen, spine or digestion",
    )),
    6: HouseSignification(6, "health, service, workload, debt and disputes", (
        "a health, treatment or routine matter", "workload, service or employment pressure",
        "a debt, repayment, competition or dispute", "attention to the intestines, digestion, illness, treatment or recovery",
    )),
    7: HouseSignification(7, "partnerships, agreements and public dealings", (
        "a spouse or relationship development", "a contract, negotiation or business partnership",
        "an important one-to-one or public interaction", "attention to the kidneys, lower abdomen or reproductive balance",
    )),
    8: HouseSignification(8, "shared resources, vulnerability and consequential change", (
        "a joint-finance, tax, insurance or inheritance matter", "a private issue requiring adjustment",
        "a consequential change, research or deeper investigation", "attention to the reproductive organs, elimination or chronic vulnerability",
    )),
    9: HouseSignification(9, "father, guidance, fortune and long journeys", (
        "a matter involving father, mentor or adviser", "higher learning, belief or legal guidance",
        "a long-distance journey or expansion of opportunity", "attention to the hips, thighs or mobility",
    )),
    10: HouseSignification(10, "career, authority, status and responsibility", (
        "a professional responsibility or role change", "recognition, authority or public standing",
        "an important action with visible consequences", "attention to the knees, joints, bones or skeletal strain",
    )),
    11: HouseSignification(11, "gains, goals, recognition and networks", (
        "income or material gains", "an objective or desired result",
        "recognition, contacts, friends or network activity", "an elder-sibling matter",
        "attention to the calves, ankles or circulation",
    )),
    12: HouseSignification(12, "expenses, foreign connections, retreat and release", (
        "an expense or use of reserves", "foreign travel, distant residence or overseas connection",
        "rest, withdrawal, private work or spiritual practice", "attention to the feet, sleep, immunity or lymphatic drainage",
    )),
}


HOUSE_COMBINATIONS: Tuple[HouseCombination, ...] = (
    HouseCombination("income_accumulation", (2, 11), (2, 11), "income and resource accumulation", (
        "income, savings or collection of money", "a financial gain becoming available for use",
    )),
    HouseCombination("career_recognition", (10, 11), (10,), "career recognition or professional gains", (
        "recognition, promotion or gain through work", "progress toward a professional objective",
    )),
    HouseCombination("service_income", (2, 6, 10, 11), (10,), "income through work or service", (
        "employment-related income or responsibility", "workload tied to compensation or gains",
    )),
    HouseCombination("financial_obligation", (2, 6), (6,), "financial obligation or repayment", (
        "a debt, repayment or recurring family expense", "resources being directed toward an obligation",
    )),
    HouseCombination("shared_finances", (2, 8), (8,), "shared finances and consequential obligations", (
        "joint money, tax, insurance or inheritance", "a financial adjustment involving another person",
    )),
    HouseCombination("partnership_result", (7, 11), (7,), "partnership result or agreement", (
        "a relationship or business agreement reaching a result", "gain through collaboration",
    )),
    HouseCombination("property_result", (4, 11), (4,), "home or property fulfilment", (
        "progress in a property or residence objective", "gain connected with home or fixed assets",
    )),
    HouseCombination("education_creative_result", (5, 11), (5,), "education, child or creative fulfilment", (
        "achievement in study or a creative objective", "a child-related development reaching fruition",
    )),
    HouseCombination("long_distance_opportunity", (9, 11), (9,), "long-distance or guidance-related opportunity", (
        "gain through travel, education, mentor or guidance", "progress toward a long-term aspiration",
    )),
    HouseCombination("health_and_recovery", (1, 6), (1, 6), "health, routine and recovery", (
        "attention to health and daily routine", "effort directed toward overcoming a difficulty",
    )),
    HouseCombination("home_change_or_relocation", (4, 12), (4,), "home change or relocation", (
        "change of residence or time away from home", "expense or release connected with property",
    )),
    HouseCombination("travel_or_foreign_stay", (3, 9, 12), (9, 12), "travel or foreign stay", (
        "a significant journey or distant connection", "planning or documentation for travel",
    )),
)


HOUSE_TONE_READINGS: Dict[int, Dict[Polarity, str]] = {
    1: {
        Polarity.SUPPORTIVE: "Personal initiative, vitality or a new direction receives support.",
        Polarity.MIXED: "A personal change or vitality matter can progress, but requires adjustment and sustained effort.",
        Polarity.CHALLENGING: "Pressure may affect vitality, confidence or personal direction and calls for measured action.",
        Polarity.NEUTRAL: "Attention shifts toward identity, vitality or a new personal direction.",
    },
    2: {
        Polarity.SUPPORTIVE: "Resources, family support or communication can develop constructively.",
        Polarity.MIXED: "Resources or family matters may improve in part while also creating expense, pressure or difficult conversations.",
        Polarity.CHALLENGING: "Savings, family responsibilities, speech or values may come under pressure.",
        Polarity.NEUTRAL: "A development concerns resources, family, speech, food habits or values.",
    },
    3: {
        Polarity.SUPPORTIVE: "Effort, communication, skills or sibling matters receive useful momentum.",
        Polarity.MIXED: "An initiative or communication can advance, but may involve revisions, friction or repeated effort.",
        Polarity.CHALLENGING: "Communication, documents, siblings or personal efforts may encounter conflict or delay.",
        Polarity.NEUTRAL: "Attention turns to effort, skills, communication, siblings or a short journey.",
    },
    4: {
        Polarity.SUPPORTIVE: "Home, property, education or emotional stability can develop favourably.",
        Polarity.MIXED: "A home, property or foundational matter may progress with expense, uncertainty or emotional strain.",
        Polarity.CHALLENGING: "Home, property, education or inner stability may require difficult adjustment.",
        Polarity.NEUTRAL: "A development concerns home, property, education or emotional foundations.",
    },
    5: {
        Polarity.SUPPORTIVE: "Learning, children, creativity or a considered decision receives constructive support.",
        Polarity.MIXED: "A child, education or creative matter can develop but may bring uncertainty or added responsibility.",
        Polarity.CHALLENGING: "Children, study, judgment or speculative decisions may involve pressure or setbacks.",
        Polarity.NEUTRAL: "Attention turns to children, learning, creativity, counsel or speculation.",
    },
    6: {
        Polarity.SUPPORTIVE: "Obstacles can be managed through disciplined routines, service or corrective action.",
        Polarity.MIXED: "Workload, health, debt or disputes may demand effort while remaining manageable.",
        Polarity.CHALLENGING: "Health, workload, debt, competition or disputes may intensify and need careful handling.",
        Polarity.NEUTRAL: "A matter involves health, service, workload, debt, competition or disputes.",
    },
    7: {
        Polarity.SUPPORTIVE: "A relationship, agreement or public interaction can move constructively.",
        Polarity.MIXED: "A partnership or agreement may progress while requiring negotiation and compromise.",
        Polarity.CHALLENGING: "Partnerships, contracts or public dealings may face conflict, delay or imbalance.",
        Polarity.NEUTRAL: "Attention turns to a spouse, partnership, agreement or public dealing.",
    },
    8: {
        Polarity.SUPPORTIVE: "A shared-resource or consequential matter can be reorganized constructively.",
        Polarity.MIXED: "Shared finances or a consequential change may bring both opportunity and vulnerability.",
        Polarity.CHALLENGING: "Shared resources, obligations or a private consequential matter may create pressure or uncertainty.",
        Polarity.NEUTRAL: "A development concerns shared resources, vulnerability, investigation or consequential change.",
    },
    9: {
        Polarity.SUPPORTIVE: "Guidance, higher learning, travel or long-term opportunity receives support.",
        Polarity.MIXED: "A matter involving guidance, father, learning or travel can progress after delay or reconsideration.",
        Polarity.CHALLENGING: "Guidance, father-related matters, higher learning or travel may encounter obstacles.",
        Polarity.NEUTRAL: "Attention turns to father, guidance, higher learning, belief or a long journey.",
    },
    10: {
        Polarity.SUPPORTIVE: "Career, authority or public responsibility can produce constructive progress or recognition.",
        Polarity.MIXED: "Professional responsibility may increase, bringing progress together with pressure or scrutiny.",
        Polarity.CHALLENGING: "Career, authority or public standing may face pressure, delay or conflict.",
        Polarity.NEUTRAL: "A development concerns career, authority, status or visible responsibility.",
    },
    11: {
        Polarity.SUPPORTIVE: "Income, recognition, objectives or helpful networks can produce a favourable result.",
        Polarity.MIXED: "An income, objective or network matter may bring progress, but with delay, pressure or complications.",
        Polarity.CHALLENGING: "Income, recognition, objectives, networks or an elder-sibling matter may face obstruction or strain.",
        Polarity.NEUTRAL: "A development concerns income, objectives, recognition, networks or an elder sibling.",
    },
    12: {
        Polarity.SUPPORTIVE: "Expense, retreat, foreign connections or release can serve a constructive purpose.",
        Polarity.MIXED: "An expense, distant connection or period of withdrawal may be useful but also draining.",
        Polarity.CHALLENGING: "Expenses, isolation, foreign matters or loss of energy may require careful management.",
        Polarity.NEUTRAL: "A development concerns expenses, foreign connections, retreat, rest or release.",
    },
}


COMBINATION_TONE_READINGS: Dict[str, Dict[Polarity, str]] = {
    "income_accumulation": {
        Polarity.SUPPORTIVE: "Income and accumulated resources can increase or become more accessible.",
        Polarity.MIXED: "Income or collections may arrive alongside expenses, delays or competing obligations.",
        Polarity.CHALLENGING: "Income, savings or collections may be delayed, reduced or absorbed by obligations.",
        Polarity.NEUTRAL: "Income and accumulated resources become an active matter.",
    },
    "career_recognition": {
        Polarity.SUPPORTIVE: "Professional effort can bring recognition, progress or gains.",
        Polarity.MIXED: "Career progress may come with heavier responsibility, scrutiny or delay.",
        Polarity.CHALLENGING: "Professional objectives or recognition may be obstructed or demand substantially more effort.",
        Polarity.NEUTRAL: "Career progress, recognition and professional objectives become active.",
    },
    "service_income": {
        Polarity.SUPPORTIVE: "Work or service can support income and professional progress.",
        Polarity.MIXED: "Compensation or gains may be tied to increased workload and obligations.",
        Polarity.CHALLENGING: "Work pressure, employment difficulty or obligations may strain income.",
        Polarity.NEUTRAL: "Income, employment and service responsibilities become connected.",
    },
    "financial_obligation": {
        Polarity.SUPPORTIVE: "A debt or financial obligation can be managed or resolved constructively.",
        Polarity.MIXED: "Resources may cover an obligation, though with pressure or reduced flexibility.",
        Polarity.CHALLENGING: "Debt, repayment or recurring expenses may place resources under strain.",
        Polarity.NEUTRAL: "Resources and a debt, repayment or service obligation become connected.",
    },
    "shared_finances": {
        Polarity.SUPPORTIVE: "Shared finances or joint obligations can be reorganized constructively.",
        Polarity.MIXED: "A joint-finance matter may offer support while also creating dependency or adjustment.",
        Polarity.CHALLENGING: "Joint money, tax, insurance or another shared obligation may create pressure.",
        Polarity.NEUTRAL: "Personal and shared resources become connected.",
    },
    "partnership_result": {
        Polarity.SUPPORTIVE: "A partnership or agreement can produce a useful result.",
        Polarity.MIXED: "A partnership result is possible after negotiation, compromise or delay.",
        Polarity.CHALLENGING: "A partnership objective or expected result may be obstructed or disputed.",
        Polarity.NEUTRAL: "A partnership, agreement and expected result become connected.",
    },
    "property_result": {
        Polarity.SUPPORTIVE: "A home or property objective can progress favourably.",
        Polarity.MIXED: "A property or residence objective may progress with expense or complications.",
        Polarity.CHALLENGING: "A home or property objective may face delay, disagreement or financial strain.",
        Polarity.NEUTRAL: "A home, property or residence objective becomes active.",
    },
    "education_creative_result": {
        Polarity.SUPPORTIVE: "Study, children or creative work can reach a constructive result.",
        Polarity.MIXED: "Progress in study, children or creative work may require extra effort or adjustment.",
        Polarity.CHALLENGING: "An education, child or creative objective may be delayed or complicated.",
        Polarity.NEUTRAL: "An education, child or creative objective becomes active.",
    },
    "long_distance_opportunity": {
        Polarity.SUPPORTIVE: "Travel, guidance or higher learning can open a useful opportunity.",
        Polarity.MIXED: "A distant or guidance-related opportunity may develop after delay or uncertainty.",
        Polarity.CHALLENGING: "Travel, guidance or a long-term objective may face obstruction or disappointment.",
        Polarity.NEUTRAL: "A long-distance, guidance or higher-learning opportunity becomes active.",
    },
    "health_and_recovery": {
        Polarity.SUPPORTIVE: "Disciplined routines can support recovery or successful management of an obstacle.",
        Polarity.MIXED: "Health or routine demands attention, with improvement possible through sustained effort.",
        Polarity.CHALLENGING: "Health, vitality or daily routines may come under pressure.",
        Polarity.NEUTRAL: "Health, vitality and daily routines become connected.",
    },
    "home_change_or_relocation": {
        Polarity.SUPPORTIVE: "A home change, relocation or release from an old arrangement can be constructive.",
        Polarity.MIXED: "A home change or relocation may be useful while also costly or unsettling.",
        Polarity.CHALLENGING: "Residence, property or relocation may bring expense, separation or instability.",
        Polarity.NEUTRAL: "Home, residence, expense and relocation become connected.",
    },
    "travel_or_foreign_stay": {
        Polarity.SUPPORTIVE: "Travel or a foreign connection can proceed constructively.",
        Polarity.MIXED: "Travel or a foreign stay may proceed with delay, expense or repeated planning.",
        Polarity.CHALLENGING: "Travel, documentation or a foreign stay may face obstruction or loss of resources.",
        Polarity.NEUTRAL: "Travel, planning and a foreign or distant connection become active.",
    },
}


def relative_house_for_native(subject: str, native_house: int) -> int:
    anchor = SUBJECTS[subject].anchor_house
    return ((int(native_house) - anchor) % 12) + 1


def build_house_interpretations(
    native_houses: Iterable[int],
    subjects: Sequence[str],
    carrier_planets: Sequence[str],
    outcome: OutcomeAssessment,
) -> Tuple[InterpretationAlternative, ...]:
    native = tuple(sorted(set(int(house) for house in native_houses)))
    alternatives = []
    for subject in subjects:
        relative_by_native = {
            house: relative_house_for_native(subject, house) for house in native
        }
        relative_houses = tuple(sorted(set(relative_by_native.values())))
        matched_combinations = tuple(
            combination
            for combination in HOUSE_COMBINATIONS
            if set(combination.relative_houses).issubset(relative_houses)
        )
        standalone = tuple(HOUSE_SIGNIFICATIONS[house] for house in relative_houses)
        labels = [row.label for row in matched_combinations] or [row.label for row in standalone]
        meaning_rows = matched_combinations or standalone
        focus_relative_houses = tuple(sorted({
            house
            for row in meaning_rows
            for house in (
                row.focus_relative_houses
                if isinstance(row, HouseCombination)
                else (row.house,)
            )
        }))
        focus_native_houses = tuple(sorted({
            ((SUBJECTS[subject].anchor_house + house - 2) % 12) + 1
            for house in focus_relative_houses
        }))
        manifestations = tuple(dict.fromkeys(
            manifestation
            for row in meaning_rows
            for manifestation in row.manifestations
        ))
        tone_sources = matched_combinations or standalone
        tone_interpretation = " ".join(
            (
                COMBINATION_TONE_READINGS[row.key][outcome.tone]
                if isinstance(row, HouseCombination)
                else HOUSE_TONE_READINGS[row.house][outcome.tone]
            )
            for row in tone_sources
        )
        combination_keys = [row.key for row in matched_combinations]
        signature_key = (
            "+".join(combination_keys)
            if combination_keys
            else "+".join(f"house_{house}" for house in relative_houses)
        )
        alternatives.append(InterpretationAlternative(
            subject=subject,
            domain="house_significations",
            event_family="house_activation",
            signature_key=signature_key,
            label="; ".join(labels),
            native_houses=native,
            relative_houses=relative_houses,
            focus_native_houses=focus_native_houses,
            focus_relative_houses=focus_relative_houses,
            carrier_planets=tuple(carrier_planets),
            manifestations=manifestations,
            tone=outcome.tone,
            supportive_factors=outcome.supportive_factors,
            challenging_factors=outcome.challenging_factors,
            tone_interpretation=tone_interpretation,
            outcome_rule_id=outcome.rule_id,
        ))
    return tuple(alternatives)
