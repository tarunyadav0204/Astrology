"""Machine-readable source boundary for the production Prashna lineage.

Rules outside this ledger cannot participate in a verdict.  The English text is a
compact implementation gloss, not a replacement for the cited edition.
"""
from __future__ import annotations

HAYANARATNA_BASE = "https://www.wisdomlib.org/hinduism/book/hayanaratna-the-jewel-of-annual-astrology/d/"
PRASHNA_TANTRA = "https://www.shanti-ganesha.com/classic/prashna-tantra.pdf"


def source(rule_id, work, section, url, gloss, *, variant=None):
    return {
        "id": rule_id,
        "work": work,
        "section": section,
        "url": url,
        "implementation_gloss": gloss,
        "variant": variant,
    }


TAJIKA_SOURCES = {
    "ikkavala": source("HR-3.2-ikkavala", "Hayanaratna", "3.2; Samjnatantra 2.17",
        HAYANARATNA_BASE + "doc1500904.html", "All seven planets occupy angles or succedents.",
        variant="Yadava gives a two-planet alternative; production follows Samjnatantra as preferred by Balabhadra."),
    "induvara": source("HR-3.2-induvara", "Hayanaratna", "3.2; Samjnatantra 2.17",
        HAYANARATNA_BASE + "doc1500904.html", "All seven planets occupy cadent houses.",
        variant="Yadava gives an angle/cadent two-planet alternative; production follows Samjnatantra."),
    "itthasala": source("HR-3.3-itthasala", "Hayanaratna", "3.3",
        HAYANARATNA_BASE + "doc1500905.html", "The swifter planet applies to the slower within the swifter planet's orb of light."),
    "isarapha": source("HR-3.4-isarapha", "Hayanaratna", "3.4; Tajikabhushana 4.10",
        HAYANARATNA_BASE + "doc1500906.html", "The swifter planet has separated by at least one degree."),
    "nakta": source("HR-3.5-nakta", "Hayanaratna", "3.5; Samjnatantra 2.25-27",
        HAYANARATNA_BASE + "doc1500907.html", "A swifter intermediary transfers light between unconnected significators."),
    "yamaya": source("HR-3.6-yamaya", "Hayanaratna", "3.6; Samjnatantra 2.29-30",
        HAYANARATNA_BASE + "doc1500908.html", "A slower intermediary collects the two significators' light."),
    "manau": source("HR-3.7-manau", "Hayanaratna", "3.7; Tajikayogasudhanidhi 6.19",
        HAYANARATNA_BASE + "doc1500909.html", "Mars or Saturn takes the swifter significator's light by an inimical contact or relevant-place occupation."),
    "kambula": source("HR-3.8-kambula", "Hayanaratna", "3.8; Samjnatantra 2.36",
        HAYANARATNA_BASE + "doc1500910.html", "The Moon applies to either or both significators already in itthasala; quality follows dignity."),
    "gairikambula": source("HR-3.9-gairikambula", "Hayanaratna", "3.9; Tajikayogasudhanidhi 6.25-26",
        HAYANARATNA_BASE + "doc1500911.html", "An otherwise disconnected Moon enters the next sign and applies to a dignified planet."),
    "khallasara": source("HR-3.10-khallasara", "Hayanaratna", "3.10; Balabhadra's preferred reading",
        HAYANARATNA_BASE + "doc1500912.html", "The significators apply, but the Moon has neither application nor joining with either."),
    "radda": source("HR-3.11-radda", "Hayanaratna", "3.11; Tajikayogasudhanidhi 6.28",
        HAYANARATNA_BASE + "doc1500913.html", "Application to a receiver that is retrograde, approaching the Sun's rays, set, cadent in 6/8/12, or overcome by a malefic."),
    "duhphalikutta": source("HR-3.12-duhphalikutta", "Hayanaratna", "3.12; Tajikabhushana 4.27",
        HAYANARATNA_BASE + "doc1500914.html", "A dignified slower planet receives application from an undignified swifter planet."),
    "dutthotthadabira": source("HR-3.13-dutthotthadabira", "Hayanaratna", "3.13; Jirnatajika",
        HAYANARATNA_BASE + "doc1500915.html", "Weak significators receive help through another dignified planet."),
    "tambira": source("HR-3.14-tambira", "Hayanaratna", "3.14; Hayanasindhu",
        HAYANARATNA_BASE + "doc1500916.html", "Without direct contact, a strong significator at a sign end applies to a strong planet in the next sign."),
    "kuttha": source("HR-3.15-kuttha", "Hayanaratna", "3.15; Tajikabhushana 4.29a",
        HAYANARATNA_BASE + "doc1500917.html", "A dignified, angular, benefic-supported, direct and visible planet is fully strong."),
    "duruhpha": source("HR-3.16-duruhpha", "Hayanaratna", "3.16; Tajikabhushana 4.30",
        HAYANARATNA_BASE + "doc1500918.html", "A planet has one or more enumerated severe weaknesses."),
}

CALCULATION_SOURCES = {
    "houses": source("HR-1.9-houses", "Hayanaratna", "1.9", HAYANARATNA_BASE + "doc1500890.html",
        "Quadrants from ascendant and meridian are trisected into cusps; junctions are halfway between cusps and house strength is proportional."),
    "five_dignities": source("HR-2.5-dignities", "Hayanaratna", "2.5", HAYANARATNA_BASE + "doc1500896.html",
        "Domicile, exaltation, hadda, decan and ninth-part dignity tables."),
    "friendship": source("HR-2.4.1-friendship", "Hayanaratna", "2.4.1", HAYANARATNA_BASE + "doc1500895.html",
        "The production profile selects the constant twofold friend/enemy table; an enemy's domicile supplies the inferior dignity condition."),
    "time_strength": source("HR-2.6.3-time", "Hayanaratna", "2.6.3", HAYANARATNA_BASE + "doc1500897.html",
        "Male-planet strength grows and declines through the day half; the complementary arc supplies female-planet strength."),
    "planet_gender": source("HR-1.5-gender", "Hayanaratna", "1.5", HAYANARATNA_BASE + "doc1500886.html",
        "Jupiter, Mars and Sun are male; Moon, Mercury, Saturn and Venus are female."),
    "orbs": source("HR-3.1-orbs", "Hayanaratna", "3.1", HAYANARATNA_BASE + "doc1500903.html",
        "Sun 15°, Moon 12°, Mars 8°, Mercury/Venus 7°, Jupiter/Saturn 9°."),
}


TOPIC_SOURCES = {
    "general": [
        source("PT-II-1", "Prashna Tantra", "II.1", PRASHNA_TANTRA, "A house gains vitality from its lord or benefics and is harmed by malefics."),
        source("PT-II-2", "Prashna Tantra", "II.2", PRASHNA_TANTRA, "Ascendant conditions describe fulfillment, failure, or success after setbacks."),
        source("PT-II-3-13", "Prashna Tantra", "II.3-13", PRASHNA_TANTRA, "The ascendant, its lord, the matter significator and the Moon establish success or failure."),
    ],
    "wealth": [source("PT-II-6-12", "Prashna Tantra", "II.6-12", PRASHNA_TANTRA, "Complete second-house rules for a defined receipt or gain.")],
    "relationship": [
        source("PT-I-25", "Prashna Tantra", "I.25", PRASHNA_TANTRA, "The seventh house signifies disputes and wife or husband."),
        source("PT-II-1-4-9-13", "Prashna Tantra", "II.1, 3-4, 9, 13", PRASHNA_TANTRA, "House vitality and the ascendant, matter significator and Moon judge fulfilment or failure of a defined object."),
    ],
    "marriage": [source("PT-II-62-66", "Prashna Tantra", "II.62-66", PRASHNA_TANTRA, "Application, placement, affliction and eighth-lord obstruction for obtaining a spouse.")],
    "travel": [source("PT-II-95-104", "Prashna Tantra", "II.95-104", PRASHNA_TANTRA, "Journey occurrence, obstruction, danger, purpose, destination and outcome.")],
    "career": [
        source("PT-II-108-113", "Prashna Tantra", "II.108-113", PRASHNA_TANTRA, "Tenth-house attainment and obstruction rules."),
        source("PT-III-72-75", "Prashna Tantra", "III.72-75", PRASHNA_TANTRA, "Current versus new employer and improvement rules."),
    ],
    "lost": [source("PT-III-76-97", "Prashna Tantra", "III.76-97", PRASHNA_TANTRA, "Recovery, non-recovery, thief, location and authority rules for missing property.")],
    "property": [source("PT-III-183-185", "Prashna Tantra", "III.183-185", PRASHNA_TANTRA, "Purchase and sale roles and strength conditions.")],
}

SUPPORTED_TOPICS = frozenset(TOPIC_SOURCES)


def public_ledger():
    return {
        "lineage": "Praśnatantra–Tājika",
        "calculation": list(CALCULATION_SOURCES.values()),
        "tajika": list(TAJIKA_SOURCES.values()),
        "topics": {name: rows for name, rows in TOPIC_SOURCES.items()},
        "unsupported_topics": ["health", "children", "pregnancy", "death", "legal", "speculation"],
    }
