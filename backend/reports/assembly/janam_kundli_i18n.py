"""Hindi/English copy for Janam Kundli deterministic pages (non-LLM chrome)."""

from __future__ import annotations

from typing import Any, Dict


def is_hindi(language: Any) -> bool:
    return str(language or "").strip().lower() in {"hindi", "hi", "hin"}


PAGE_META = {
    "cover": {
        "en": ("Janam Kundli", "Personalized Vedic birth chart report"),
        "hi": ("जन्म कुंडली", "व्यक्तिगत वैदिक जन्म कुंडली रिपोर्ट"),
    },
    "birth_panchang": {
        "en": ("Avakahada Chakra & Birth Panchang", "Birth moment foundations"),
        "hi": ("अवकाहद चक्र और जन्म पंचांग", "जन्म क्षण की आधारभूत जानकारी"),
    },
    "primary_charts": {
        "en": ("Chandra Kundli & Planet Analysis", "Moon chart with planetary detail"),
        "hi": ("चंद्र कुंडली और ग्रह विश्लेषण", "चंद्र कुंडली तथा ग्रह विवरण"),
    },
    "navamsha": {
        "en": ("Navamsha Kundli (D-9)", "Hidden strengths and marriage/mid-life trajectory"),
        "hi": ("नवांश कुंडली (डी-९)", "छिपी शक्तियाँ तथा विवाह/मध्यायु प्रवृत्ति"),
    },
    "planetary_positions": {
        "en": ("Planetary Degrees, Dignities & Relations", "Degree, nakshatra, dignity, retrograde, combustion"),
        "hi": ("ग्रह अंश, दशा और संबंध", "अंश, नक्षत्र, बल, वक्री, अस्त"),
    },
    "chalit_chart": {
        "en": ("Chalit Chart & Bhava Sphuta", "House boundary shifts from D1"),
        "hi": ("चलित कुंडली और भाव स्फुट", "डी-१ से भाव परिवर्तन"),
    },
    "dashamsha": {
        "en": ("Dashamsha Kundli (D-10)", "Authority and professional success map"),
        "hi": ("दशांश कुंडली (डी-१०)", "करियर और अधिकार का मानचित्र"),
    },
    "ashtakavarga": {
        "en": ("Ashtakavarga Power Zones", "Sarvashtakavarga and Bhinnashtakavarga"),
        "hi": ("अष्टकवर्ग शक्ति क्षेत्र", "सर्वाष्टकवर्ग और भिन्नाष्टकवर्ग"),
    },
    "past_life_blueprint": {
        "en": ("Past Life Blueprint", "Karma, debts, and blessings"),
        "hi": ("पूर्व जन्म रूपरेखा", "कर्म, ऋण और आशीर्वाद"),
    },
    "personality": {
        "en": ("Your Cosmic Persona", "Ascendant temperament"),
        "hi": ("आपका व्यक्तित्व", "लग्न स्वभाव"),
    },
    "emotional_blueprint": {
        "en": ("Nakshatra Deep-Dive & Emotional Blueprint", "Moon nakshatra and pada"),
        "hi": ("नक्षत्र गहराई और भावनात्मक रूपरेखा", "चंद्र नक्षत्र और पद"),
    },
    "education_intellect": {
        "en": ("Education & Intellect", "Age-aware learning themes"),
        "hi": ("शिक्षा और बुद्धि", "आयु-अनुसार शिक्षा विषय"),
    },
    "career_profession": {
        "en": ("Career & Profession", "Age-aware career themes"),
        "hi": ("करियर और व्यवसाय", "आयु-अनुसार करियर विषय"),
    },
    "wealth_finances": {
        "en": ("Wealth & Finances", "Age-aware money themes"),
        "hi": ("धन और वित्त", "आयु-अनुसार धन विषय"),
    },
    "love_relationships": {
        "en": ("Love & Relationships", "Age-aware relationship themes"),
        "hi": ("प्रेम और संबंध", "आयु-अनुसार संबंध विषय"),
    },
    "health_profiles": {
        "en": ("Health Profiles", "Energetic vulnerabilities from 1st and 6th"),
        "hi": ("स्वास्थ्य प्रोफ़ाइल", "प्रथम और षष्ठ भाव से स्वास्थ्य संकेत"),
    },
    "major_yogas": {
        "en": ("Yogas Catalog", "All yogas from the same engine as the Yogas screen"),
        "hi": ("योग सूची", "योग स्क्रीन वाले इंजन से सभी योग"),
    },
    "dosha_checks": {
        "en": ("Dosha Checks", "Manglik, Kaal Sarp, and related checks"),
        "hi": ("दोष जाँच", "मांगलिक, काल सर्प और संबंधित जाँच"),
    },
    "sade_sati": {
        "en": ("Shani Sade Sati", "Timelines from Moon-based Saturn transit"),
        "hi": ("शनि साढ़े साती", "चंद्र राशि के सापेक्ष शनि गोचर काल"),
    },
    "dasha_tree": {
        "en": ("Vimshottari Dasha Tree", "Master life cycles"),
        "hi": ("विंशोत्तरी दशा वृक्ष", "मुख्य जीवन चक्र"),
    },
    "present_phase": {
        "en": ("The Present Phase", "Current Mahadasha and Antardasha"),
        "hi": ("वर्तमान चरण", "वर्तमान महादशा और अन्तर्दशा"),
    },
    "gemstones": {
        "en": ("Gemstone Recommendations", "Functional-benefic candidates"),
        "hi": ("रत्न सुझाव", "कार्यात्मक शुभ ग्रहों के आधार पर"),
    },
    "practical_remedies": {
        "en": ("Practical Daily Remedies", "Day, time, mantra counts, charity, and colors"),
        "hi": ("व्यावहारिक उपाय", "दिन, समय, मंत्र संख्या, दान और रंग"),
    },
    "closing_guidance": {
        "en": ("Cosmic Outlook & Closing Words", "Guidance and disclaimer"),
        "hi": ("ब्रह्मांडीय दृष्टि और समापन", "मार्गदर्शन और अस्वीकरण"),
    },
}

AGE_HEADERS = {
    "education_intellect": {
        "en": {
            "0_17": "Early Education, Focus & Foundational Learning",
            "18_28": "Higher Education, Skill Acquisition & Competitive Edge",
            "29_50": "Intellectual Pursuits, Upskilling & Knowledge Application",
            "51_plus": "Wisdom, Creative Pursuits & Lifelong Learning",
        },
        "hi": {
            "0_17": "प्रारंभिक शिक्षा, एकाग्रता और आधारभूत अधिगम",
            "18_28": "उच्च शिक्षा, कौशल और प्रतिस्पर्धात्मक बढ़त",
            "29_50": "बौद्धिक विकास, अपस्किलिंग और ज्ञान अनुप्रयोग",
            "51_plus": "ज्ञान, रचनात्मकता और जीवनपर्यंत अधिगम",
        },
    },
    "career_profession": {
        "en": {
            "0_17": "Inherent Talents & Future Career Inclinations",
            "18_28": "Career Launchpad, Ambition & Professional Pathways",
            "29_50": "Peak Professional Trajectory, Leadership & Authority",
            "51_plus": "Late-Career Stability, Mentorship & Legacy",
        },
        "hi": {
            "0_17": "जन्मजात प्रतिभा और भविष्य की करियर प्रवृत्तियाँ",
            "18_28": "करियर शुरुआत, महत्वाकांक्षा और व्यावसायिक मार्ग",
            "29_50": "शीर्ष व्यावसायिक प्रक्षेपवक्र, नेतृत्व और अधिकार",
            "51_plus": "उत्तर-करियर स्थिरता, मार्गदर्शन और विरासत",
        },
    },
    "wealth_finances": {
        "en": {
            "0_17": "Inherent Dhan Yogas (Wealth Potential)",
            "18_28": "Wealth Building, First Incomes & Financial Habits",
            "29_50": "Asset Accumulation, Real Estate & Major Dhan Yogas",
            "51_plus": "Financial Legacy, Security & Wealth Preservation",
        },
        "hi": {
            "0_17": "जन्मजात धन योग (धन संभावना)",
            "18_28": "धन निर्माण, प्रथम आय और वित्तीय आदतें",
            "29_50": "संपत्ति संचय, अचल संपत्ति और प्रमुख धन योग",
            "51_plus": "वित्तीय विरासत, सुरक्षा और धन संरक्षण",
        },
    },
    "love_relationships": {
        "en": {
            "0_17": "Social Dynamics, Friendships & Peer Relations",
            "18_28": "Love, Courtship & Ideal Marital Partner Traits",
            "29_50": "Marital Harmony, Spousal Support & Long-Term Partnerships",
            "51_plus": "Family Bonds, Companionship & Domestic Peace",
        },
        "hi": {
            "0_17": "सामाजिक गतिशीलता, मित्रता और सहपाठी संबंध",
            "18_28": "प्रेम, संबंध और आदर्श जीवनसाथी लक्षण",
            "29_50": "वैवाहिक सामंजस्य, जीवनसाथी सहयोग और दीर्घकालिक साझेदारी",
            "51_plus": "पारिवारिक बंधन, साथ और घरेलू शांति",
        },
    },
}


def page_title_subtitle(key: str, language: Any) -> tuple[str, str]:
    lang = "hi" if is_hindi(language) else "en"
    meta = PAGE_META.get(key) or {}
    pair = meta.get(lang) or meta.get("en") or (key, "")
    return pair[0], pair[1]


def age_title(key: str, bracket: str, language: Any, default: str) -> str:
    lang = "hi" if is_hindi(language) else "en"
    return ((AGE_HEADERS.get(key) or {}).get(lang) or {}).get(bracket) or default


def t(language: Any, en: str, hi: str) -> str:
    return hi if is_hindi(language) else en


def yes_no(language: Any, present: bool) -> str:
    if is_hindi(language):
        return "हाँ" if present else "नहीं"
    return "Yes" if present else "No"


COVER_COPY: Dict[str, Dict[str, str]] = {
    "en": {
        "report_title": "Janam Kundli Report",
        "generated_on": "Generated on {date}",
        "ascendant": "Ascendant",
        "language": "Language",
        "current_md": "Current MD",
        "current_ad": "Current AD",
        "how_to_read": "How to read this report",
        "how_to_read_body": (
            "Pages 1–8 and the dasha/dosha tables are calculator facts. Narrative pages synthesize only those facts "
            "into clear language — they do not invent placements, yogas, or dates."
        ),
        "native_fallback": "Native",
        "lang_label_hindi": "Hindi",
        "lang_label_english": "English",
    },
    "hi": {
        "report_title": "जन्म कुंडली रिपोर्ट",
        "generated_on": "निर्माण तिथि {date}",
        "ascendant": "लग्न",
        "language": "भाषा",
        "current_md": "वर्तमान महादशा",
        "current_ad": "वर्तमान अन्तर्दशा",
        "how_to_read": "इस रिपोर्ट को कैसे पढ़ें",
        "how_to_read_body": (
            "पृष्ठ १–८ तथा दशा/दोष तालिकाएँ गणना के तथ्य हैं। कथात्मक पृष्ठ केवल इन्हीं तथ्यों का स्पष्ट हिंदी "
            "संश्लेषण करते हैं — वे ग्रह स्थिति, योग या तिथियाँ गढ़ते नहीं।"
        ),
        "native_fallback": "जातक",
        "lang_label_hindi": "हिंदी",
        "lang_label_english": "अंग्रेज़ी",
    },
}


def cover_copy(language: Any) -> Dict[str, str]:
    return COVER_COPY["hi"] if is_hindi(language) else COVER_COPY["en"]
