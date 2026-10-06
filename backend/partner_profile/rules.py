"""Source-bound physical and temperament descriptors used by Partner Portrait.

These are descriptions of rashis and grahas from BPHS.  Applying a rashi or
graha description to the spouse requires that the factor actually represent
the spouse in the calculated evidence packet (seventh house, seventh lord,
seventh-house occupant, D9 confirmation, or Darakaraka).  The resolver weights
those channels separately; the source text itself is never presented as a
weighted scoring system.
"""

from __future__ import annotations

from typing import Any, Dict


SOURCES: Dict[str, Dict[str, Any]] = {
    "bphs.graha_forms": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 3,
        "verses": "16-17, 23-30",
        "title": "Descriptions of the grahas",
        "scope": "Classical complexion, physical form and disposition of the grahas",
        "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    },
    "bphs.rashi_forms": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 4,
        "verses": "6-24",
        "title": "Descriptions of the rashis",
        "scope": "Classical bodily form and disposition of the rashis",
        "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    },
    "bphs.seventh_house": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 18,
        "verses": "1-21",
        "title": "Effects of Yuvati Bhava",
        "scope": "The seventh house, its lord and karaka in matters of spouse and marriage",
        "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    },
    "bphs.navamsa_scope": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 7,
        "verses": "1-8",
        "title": "Use of the sixteen divisions",
        "scope": "Identifies Navamsha as the division used for spouse matters",
        "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    },
    "bphs.chara_karakas": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 32,
        "verses": "1-17",
        "title": "Chara Karakas",
        "scope": "Defines the longitude-ranked Chara Karakas, including Stri/Dara Karaka",
        "url": "https://vedic-astro.s3.amazonaws.com/books/bhrihat_parasara_hora_shastra.pdf",
    },
    "bphs.graha_states": {
        "work": "Brihat Parashara Hora Shastra",
        "chapter": 45,
        "verses": "5-6",
        "title": "Awakening, dreaming and sleeping states",
        "scope": "A debilitated graha is in the sleeping state and its capacity to deliver results is weakened",
        "url": "https://www.siva.sh/brihat-parashara-hora-shastra/45/5",
    },
    "phaladeepika.neecha_bhanga": {
        "work": "Phaladeepika",
        "chapter": 7,
        "verses": "26-30",
        "title": "Neecha Bhanga Raja Yoga",
        "scope": "The D1 cancellation rules shown on the chart; the portrait resolver mitigates debilitation when a rule matches without treating the graha as exalted.",
        "url": "https://vedpuran.net/wp-content/uploads/2021/04/mantreswara_s__phaladeeplka.pdf",
    },
}


def _signals(**values: str) -> Dict[str, str]:
    return dict(values)


# Deliberately conservative. Only visual attributes stated by the source are
# encoded. BPHS 3.16-17 explicitly describes the grahas' complexions, so those
# are retained as complexion evidence. Caste descriptors remain excluded.
# The English phrases below translate the source into plausible human skin
# tones; they must not be replaced by a regional or ethnic default.
PLANET_RULES: Dict[str, Dict[str, Any]] = {
    "Sun": {
        "appearance": _signals(complexion="warm reddish-brown complexion", build="square and structured", face_shape="square", eyes="warm, honey-toned expression", head_hair="less abundant hair"),
        "appearance_verses": {"complexion": "3.16"},
        "personality": ["clean and orderly", "intelligent", "self-possessed"],
        "source_id": "bphs.graha_forms",
        "verse": "3.23",
    },
    "Moon": {
        "appearance": _signals(complexion="fair or light complexion", build="rounded and soft", face_shape="round", expression="pleasant and approachable"),
        "appearance_verses": {"complexion": "3.16"},
        "personality": ["receptive", "learned", "soft-spoken", "change-responsive"],
        "source_id": "bphs.graha_forms",
        "verse": "3.24",
    },
    "Mars": {
        "appearance": _signals(complexion="warm reddish complexion", build="lean and wiry", waist="slender", expression="direct and energetic"),
        "appearance_verses": {"complexion": "3.16"},
        "personality": ["active", "liberal", "decisive", "quick to react"],
        "source_id": "bphs.graha_forms",
        "verse": "3.25",
    },
    "Mercury": {
        # BPHS 3.16 gives Budha a harita (grass-green) tone. "Olive or wheatish"
        # keeps that green-olive quality without collapsing Mercury into Venus's
        # warm-fair śyāva phrasing.
        "appearance": _signals(complexion="olive or wheatish complexion", build="well-proportioned and youthful", presence="attractive and animated"),
        "appearance_verses": {"complexion": "3.16"},
        "personality": ["witty", "adaptable", "articulate", "playful"],
        "source_id": "bphs.graha_forms",
        "verse": "3.26",
    },
    "Jupiter": {
        "appearance": _signals(complexion="fair or light golden complexion", build="broad or substantial", presence="warm and dignified", head_hair="golden-brown hair"),
        "appearance_verses": {"complexion": "3.17"},
        "personality": ["learned", "principled", "wise", "protective"],
        "source_id": "bphs.graha_forms",
        "verse": "3.27",
    },
    "Venus": {
        # BPHS 3.17 calls Śukra śyāva (brown/tawny), not kṛṣṇa (Saturn's dark).
        # "Medium brown" was over-reading that word into a deep skin tone that
        # image models and users treat as dark. Render śyāva as a warm fair
        # base with soft brown undertone — lighter than Mercury's wheatish and
        # Saturn's dark, warmer than Moon/Jupiter's plain fair.
        # BPHS 3.28 vakramūrdhaja is curly/wavy hair; keep it soft so the
        # image model does not force tight curls on every Venus-led portrait.
        "appearance": _signals(
            complexion="warm fair complexion with soft brown undertone",
            build="graceful and well-proportioned",
            eyes="pleasing and expressive",
            head_hair="soft wavy or gently curled hair",
            presence="polished and attractive",
        ),
        "appearance_verses": {"complexion": "3.17", "head_hair": "3.28"},
        "personality": ["refined", "creative", "affectionate", "socially graceful"],
        "source_id": "bphs.graha_forms",
        "verse": "3.28",
    },
    "Saturn": {
        "appearance": _signals(complexion="dark complexion", build="lean and elongated", stature="taller or long-limbed", head_hair="coarse hair", presence="serious and restrained"),
        "appearance_verses": {"complexion": "3.17"},
        "personality": ["reserved", "patient", "deliberate", "enduring"],
        "source_id": "bphs.graha_forms",
        "verse": "3.29",
    },
    "Rahu": {
        "appearance": _signals(presence="unusual or immediately distinctive"),
        "personality": ["unconventional", "observant", "intense"],
        "source_id": "bphs.graha_forms",
        "verse": "3.30",
    },
    "Ketu": {
        "appearance": _signals(presence="unusual or difficult to place"),
        "personality": ["private", "detached", "perceptive"],
        "source_id": "bphs.graha_forms",
        "verse": "3.30",
    },
}


SIGN_RULES: Dict[str, Dict[str, Any]] = {
    "Aries": {"appearance": _signals(build="prominent and substantial", presence="active and forthright"), "temperament": ["active", "courageous"], "verse": "4.6-7"},
    "Taurus": {"appearance": _signals(stature="long or taller", build="solid and grounded"), "temperament": ["steady", "grounded"], "verse": "4.8"},
    "Gemini": {"appearance": _signals(build="even and well-proportioned", presence="lively and mobile"), "temperament": ["adaptable", "communicative"], "verse": "4.9"},
    "Cancer": {"appearance": _signals(build="rounded or substantial", presence="soft and receptive"), "temperament": ["receptive", "protective"], "verse": "4.10-11"},
    "Leo": {"appearance": _signals(build="large or commanding", presence="dignified and noticeable"), "temperament": ["dignified", "self-possessed"], "verse": "4.12"},
    "Virgo": {"appearance": _signals(build="medium and balanced", presence="neat and composed"), "temperament": ["practical", "observant"], "verse": "4.13-14"},
    "Libra": {"appearance": _signals(build="medium and balanced", presence="graceful and socially polished"), "temperament": ["relational", "refined"], "verse": "4.15-16"},
    "Scorpio": {"appearance": _signals(build="slender and compact", body_hair="noticeable body hair", presence="intense and private"), "temperament": ["intense", "private"], "verse": "4.17"},
    "Sagittarius": {"appearance": _signals(build="even and well-proportioned", presence="open and dignified"), "temperament": ["principled", "expansive"], "verse": "4.17-18"},
    "Capricorn": {"appearance": _signals(build="large or strongly framed", presence="restrained and grounded"), "temperament": ["patient", "practical"], "verse": "4.19-20"},
    "Aquarius": {"appearance": _signals(build="medium and balanced", presence="distinctive and self-contained"), "temperament": ["independent", "observant"], "verse": "4.21"},
    "Pisces": {"appearance": _signals(build="medium and soft", presence="gentle and composed"), "temperament": ["receptive", "resolute"], "verse": "4.22-24"},
}

for _rule in SIGN_RULES.values():
    _rule["source_id"] = "bphs.rashi_forms"
