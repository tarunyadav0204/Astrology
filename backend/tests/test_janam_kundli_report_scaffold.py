"""Scaffold tests for Janam Kundli report registration and fact assembly."""

from reports.assembly.janam_kundli_page_assembler import (
    JANAM_KUNDLI_PAGE_BLUEPRINT,
    JANAM_KUNDLI_PAGE_COUNT,
    assemble_janam_kundli_pages,
    build_janam_kundli_chart_manifest,
)
from reports.assembly.shodashvarga import SHODASHVARGA_DIVISIONS
from reports.report_types import JANAM_KUNDLI_REPORT_CONFIG, REPORT_TYPE_CONFIGS
from reports.constants import SUPPORTED_REPORT_TYPES


def test_pdf_footer_brand_is_product_line():
    from reports.pdf_service import _footer_brand_line

    assert _footer_brand_line("english", "janam_kundli") == "AstroRoshni - Vedic Kundli"
    assert _footer_brand_line("hindi", "janam_kundli") == "AstroRoshni - Vedic Kundli"
    assert _footer_brand_line("hindi", "health") == "AstroRoshni - Vedic Kundli"


def test_pdf_chart_planet_labels_include_degree():
    from reports.pdf_service import _PDF_LANGUAGE, _chart_house_map, _planet_chart_label

    token = _PDF_LANGUAGE.set("english")
    try:
        assert _planet_chart_label("Sun", {"degree": 12.8}) == "Su12°"
        assert _planet_chart_label("Saturn", {"degree": 5.1, "retrograde": True}) == "Sa5°R"
        houses = [{"house_number": i, "sign": (i - 1) % 12} for i in range(1, 13)]
        house_map = _chart_house_map(
            {
                "houses": houses,
                "planets": {
                    "Sun": {"sign": 0, "degree": 10.2},
                    "Mars": {"sign": 0, "degree": 22.9, "retrograde": True},
                },
            }
        )
        assert "Su10°" in house_map[1]["planets"]
        assert "Ma22°R" in house_map[1]["planets"]
    finally:
        _PDF_LANGUAGE.reset(token)

    hi_token = _PDF_LANGUAGE.set("hindi")
    try:
        from reports.assembly.janam_kundli_labels import PLANET_ABBR_HI

        label = _planet_chart_label("Moon", {"degree": 3.4})
        assert label == f"{PLANET_ABBR_HI['Moon']}3°"
    finally:
        _PDF_LANGUAGE.reset(hi_token)


def test_hindi_janam_verdict_uses_hindi_sign_nakshatra():
    from reports.llm.janam_kundli_premium_report import build_static_janam_report

    fact_pack = _minimal_fact_pack()
    fact_pack["ascendant"]["sign_name"] = "Cancer"
    fact_pack["moon"]["sign_name"] = "Libra"
    fact_pack["moon"]["nakshatra"] = "Swati"
    report = build_static_janam_report(
        {"person": fact_pack["person"], "language": "hindi", "fact_pack": fact_pack}
    )
    assert report["janam_verdict"] == "लग्न कर्क; चंद्र तुला स्वाति"
    assert "Cancer" not in report["janam_verdict"]
    assert "Libra" not in report["janam_verdict"]
    assert "Swati" not in report["janam_verdict"]


def test_hindi_pdf_styles_enable_shaping():
    """ReportLab defaults shaping=0; Hindi needs shaping=1 + shapable Mukta."""
    from reportlab.pdfbase.pdfmetrics import getFont
    from reports.pdf_fonts import resolve_pdf_fonts
    from reports.pdf_service import _build_story_styles

    fonts = resolve_pdf_fonts("hindi")
    assert getFont(fonts.regular).shapable is True
    styles = _build_story_styles(fonts)
    assert styles["ARBody"].shaping == 1
    assert styles["ARBodySmall"].shaping == 1
    assert styles["ARSectionTitle"].shaping == 1


def test_label_gemstone_strips_suitability_english():
    from reports.assembly.janam_kundli_labels import label_gemstone, normalize_gemstone_name

    raw = "Blue Sapphire, only if suitability checks support it"
    assert normalize_gemstone_name(raw) == "Blue Sapphire"
    assert label_gemstone(raw, "hindi") == "नीलम"
    assert label_gemstone("Diamond or White Sapphire, only if suitability checks support it", "hindi") == "हीरा या सफेद पुखराज"
    assert label_gemstone(raw, "english") == "Blue Sapphire"


def test_lifestyle_colors_table_is_chart_based():
    """Assembler color table uses chart-based labels (not MD-as-favor)."""
    from reports.assembly.janam_kundli_page_assembler import _lifestyle_colors_table

    lifestyle = {
        "wear_colors": "Red, deep orange",
        "avoid_colors": "Blue, dark grey, black",
        "period_note": "Current Mahadasha (Saturn) is chart-challenging — do not treat its colors as lucky.",
        "period_note_hi": "वर्तमान महादशा (Saturn) चार्ट में चुनौतीपूर्ण है।",
        "note": "Colors are scored from lagna functional nature.",
        "note_hi": "रंग लग्न के कार्यात्मक स्वभाव से आँके गए हैं।",
        "favor_evidence": [
            {"color": "Red", "evidence": "Red ← Mars (functional benefic; yogakaraka)"},
        ],
        "avoid_evidence": [
            {"color": "Blue", "evidence": "Blue ← Saturn (functional malefic; current MD (caution))"},
        ],
    }
    table = _lifestyle_colors_table(lifestyle, "english")
    assert table["title"] == "Color therapy (chart-based)"
    labels = [row[0] for row in table["rows"]]
    assert "Favor (chart-supportive)" in labels
    assert "Avoid (chart-challenging)" in labels
    assert "Period note (MD/AD emphasis)" in labels
    favor_row = next(r for r in table["rows"] if r[0].startswith("Favor"))
    avoid_row = next(r for r in table["rows"] if r[0].startswith("Avoid"))
    assert "Mars" in favor_row[1]
    assert "Saturn" in avoid_row[1]


def test_hindi_latin_fallback_keeps_st_ligatures():
    """Mukta+HarfBuzz corrupts Latin 'st' (trust, AstroRoshni); Latin-only runs use Noto."""
    from reportlab.pdfbase.pdfmetrics import getFont
    from reports.pdf_fonts import resolve_pdf_fonts, rich_text_for_fonts

    fonts = resolve_pdf_fonts("hindi")
    assert fonts.needs_latin_fallback is True
    assert getFont(fonts.latin_regular).shapable is False
    trust = rich_text_for_fonts("Vedic guidance you can trust", fonts)
    assert "trust" in trust
    assert fonts.latin_regular in trust
    astro = rich_text_for_fonts("Prepared with AstroRoshni", fonts)
    assert "AstroRoshni" in astro
    assert fonts.latin_regular in astro
    # Mixed Indic lines must NOT mid-split fonts (breaks Paragraph shaping).
    mixed = rich_text_for_fonts("शनि (Saturn) 10वें भाव", fonts)
    assert "Saturn" in mixed
    assert "10वें" in mixed
    assert "<font" not in mixed
    assert fonts.latin_regular not in mixed


def test_hindi_mixed_narrative_pdf_keeps_english_parentheticals():
    """Regression: rich-font splits used to garble '(Saturn)' and tofu '10वें'."""
    from io import BytesIO

    from pypdf import PdfReader
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph

    from reports.pdf_fonts import resolve_pdf_fonts, rich_text_for_fonts

    fonts = resolve_pdf_fonts("hindi")
    style = ParagraphStyle(
        "ARBodyTest",
        fontName=fonts.regular,
        fontSize=11,
        leading=15,
        shaping=1,
    )
    sample = "10वें (कर्म) भाव का स्वामी मंगल (Mars) है और शनि (Saturn) 7वें भाव में है।"
    buf = BytesIO()
    c = canvas.Canvas(buf)
    para = Paragraph(rich_text_for_fonts(sample, fonts), style)
    para.wrap(480, 200)
    para.drawOn(c, 40, 700)
    c.save()
    extracted = PdfReader(BytesIO(buf.getvalue())).pages[0].extract_text() or ""
    assert "Saturn" in extracted
    assert "Mars" in extracted
    assert "\uffff" not in extracted
    assert "dm¡" not in extracted
    assert "^m~" not in extracted


def test_janam_kundli_registered_and_enabled():
    assert "janam_kundli" in SUPPORTED_REPORT_TYPES
    assert "janam_kundli" in REPORT_TYPE_CONFIGS
    assert JANAM_KUNDLI_REPORT_CONFIG.enabled is True
    assert JANAM_KUNDLI_REPORT_CONFIG.page_count == JANAM_KUNDLI_PAGE_COUNT
    assert JANAM_KUNDLI_REPORT_CONFIG.page_count == 26


def test_janam_blueprint_has_shodashvarga_atlas_without_shadbala():
    keys = [p["key"] for p in JANAM_KUNDLI_PAGE_BLUEPRINT]
    assert len(keys) == 26
    assert "shadbala" not in keys
    assert keys[0] == "cover"
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[0]["charts"] == ["native_d1"]
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[1]["key"] == "birth_panchang"
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[1].get("skip_render") is True
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[2]["charts"] == ["native_moon"]
    assert "present_phase" in keys
    assert "ashtakavarga" in keys
    shodash_pages = [p for p in JANAM_KUNDLI_PAGE_BLUEPRINT if str(p.get("key") or "").startswith("shodashvarga")]
    assert len(shodash_pages) == 2  # 16 charts packed 9 per page (3×3), then 7
    assert shodash_pages[0]["key"] == "shodashvarga_1"
    assert shodash_pages[0]["charts_per_row"] == 3
    assert shodash_pages[0]["chart_compact"] is True
    assert len(shodash_pages[0]["charts"]) == 9
    assert shodash_pages[0]["charts"][0] == "native_d1"
    assert len(shodash_pages[1]["charts"]) == 7
    assert shodash_pages[1]["charts"][-1] == "native_d60"
    # Continuous block sits immediately after dashamsha.
    dash_idx = keys.index("dashamsha")
    assert keys[dash_idx + 1: dash_idx + 3] == ["shodashvarga_1", "shodashvarga_2"]
    manifest_refs = [m["ref"] for m in build_janam_kundli_chart_manifest({"chart_style": "north"})]
    for division in SHODASHVARGA_DIVISIONS:
        assert f"native_d{division}" in manifest_refs


def _minimal_fact_pack():
    return {
        "person": {"name": "Asha", "date": "1990-05-15", "time": "10:30", "place": "Delhi"},
        "age_years": 36,
        "age_bracket": "29_50",
        "ascendant": {"sign": 3, "sign_name": "Cancer", "element": "Water", "lord": "Moon"},
        "moon": {"planet": "Moon", "sign_name": "Sagittarius", "nakshatra": "Uttara Ashadha", "pada": 1},
        "panchang": {"tithi": "Shukla Panchami", "yoga": "Siddha", "karana": "Bava"},
        "ayanamsa": 23.5,
        "planet_matrix": [
            {
                "planet": "Sun",
                "sign_name": "Taurus",
                "house": 11,
                "degree": 1.2,
                "nakshatra": "Krittika",
                "pada": 2,
                "dignity": "neutral",
                "retrograde": False,
                "is_combust": False,
                "combustion_status": "normal",
                "functional_nature": "malefic",
                "dispositor": "Venus",
                "houses_ruled": [2],
                "natural_friendship": "enemy",
                "temporal_friendship": "friend",
                "compound_friendship": "neutral",
                "aspects_received": "Jupiter, Saturn",
                "gandanta": False,
                "special_roles": "—",
                "avastha": "Bal",
            }
        ],
        "d9_planet_matrix": [
            {
                "planet": "Sun",
                "sign_name": "Leo",
                "house": 1,
                "dignity": "own_sign",
                "nakshatra": "Magha",
                "pada": 1,
            }
        ],
        "d10_planet_matrix": [
            {
                "planet": "Sun",
                "sign_name": "Aries",
                "house": 10,
                "dignity": "exalted",
                "nakshatra": "Ashwini",
                "pada": 3,
            }
        ],
        "friendship_matrices": {
            "planets": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
            "natural": {
                "Sun": {
                    "Sun": "self", "Moon": "friend", "Mars": "friend", "Mercury": "neutral",
                    "Jupiter": "friend", "Venus": "enemy", "Saturn": "enemy",
                },
                "Moon": {
                    "Sun": "friend", "Moon": "self", "Mars": "neutral", "Mercury": "friend",
                    "Jupiter": "neutral", "Venus": "neutral", "Saturn": "neutral",
                },
                "Mars": {
                    "Sun": "friend", "Moon": "neutral", "Mars": "self", "Mercury": "enemy",
                    "Jupiter": "friend", "Venus": "neutral", "Saturn": "enemy",
                },
                "Mercury": {
                    "Sun": "friend", "Moon": "enemy", "Mars": "neutral", "Mercury": "self",
                    "Jupiter": "neutral", "Venus": "friend", "Saturn": "neutral",
                },
                "Jupiter": {
                    "Sun": "friend", "Moon": "neutral", "Mars": "friend", "Mercury": "enemy",
                    "Jupiter": "self", "Venus": "enemy", "Saturn": "neutral",
                },
                "Venus": {
                    "Sun": "enemy", "Moon": "enemy", "Mars": "enemy", "Mercury": "friend",
                    "Jupiter": "neutral", "Venus": "self", "Saturn": "friend",
                },
                "Saturn": {
                    "Sun": "enemy", "Moon": "enemy", "Mars": "enemy", "Mercury": "friend",
                    "Jupiter": "enemy", "Venus": "friend", "Saturn": "self",
                },
            },
            "temporal": {
                "Sun": {
                    "Sun": "self", "Moon": "friend", "Mars": "enemy", "Mercury": "friend",
                    "Jupiter": "friend", "Venus": "enemy", "Saturn": "friend",
                },
                "Moon": {
                    "Sun": "friend", "Moon": "self", "Mars": "friend", "Mercury": "enemy",
                    "Jupiter": "friend", "Venus": "friend", "Saturn": "enemy",
                },
                "Mars": {
                    "Sun": "enemy", "Moon": "friend", "Mars": "self", "Mercury": "friend",
                    "Jupiter": "enemy", "Venus": "friend", "Saturn": "friend",
                },
                "Mercury": {
                    "Sun": "friend", "Moon": "enemy", "Mars": "friend", "Mercury": "self",
                    "Jupiter": "friend", "Venus": "enemy", "Saturn": "friend",
                },
                "Jupiter": {
                    "Sun": "friend", "Moon": "friend", "Mars": "enemy", "Mercury": "friend",
                    "Jupiter": "self", "Venus": "friend", "Saturn": "enemy",
                },
                "Venus": {
                    "Sun": "enemy", "Moon": "friend", "Mars": "friend", "Mercury": "enemy",
                    "Jupiter": "friend", "Venus": "self", "Saturn": "friend",
                },
                "Saturn": {
                    "Sun": "friend", "Moon": "enemy", "Mars": "friend", "Mercury": "friend",
                    "Jupiter": "enemy", "Venus": "friend", "Saturn": "self",
                },
            },
            "compound": {
                "Sun": {
                    "Sun": "self", "Moon": "great_friend", "Mars": "neutral", "Mercury": "friend",
                    "Jupiter": "great_friend", "Venus": "great_enemy", "Saturn": "neutral",
                },
                "Moon": {
                    "Sun": "great_friend", "Moon": "self", "Mars": "friend", "Mercury": "neutral",
                    "Jupiter": "friend", "Venus": "friend", "Saturn": "enemy",
                },
                "Mars": {
                    "Sun": "neutral", "Moon": "friend", "Mars": "self", "Mercury": "neutral",
                    "Jupiter": "neutral", "Venus": "friend", "Saturn": "neutral",
                },
                "Mercury": {
                    "Sun": "great_friend", "Moon": "great_enemy", "Mars": "friend", "Mercury": "self",
                    "Jupiter": "friend", "Venus": "neutral", "Saturn": "friend",
                },
                "Jupiter": {
                    "Sun": "great_friend", "Moon": "friend", "Mars": "neutral", "Mercury": "neutral",
                    "Jupiter": "self", "Venus": "neutral", "Saturn": "enemy",
                },
                "Venus": {
                    "Sun": "great_enemy", "Moon": "neutral", "Mars": "neutral", "Mercury": "neutral",
                    "Jupiter": "friend", "Venus": "self", "Saturn": "great_friend",
                },
                "Saturn": {
                    "Sun": "neutral", "Moon": "great_enemy", "Mars": "neutral", "Mercury": "great_friend",
                    "Jupiter": "great_enemy", "Venus": "great_friend", "Saturn": "self",
                },
            },
        },
        "special_points": {
            "yogi": {"lord": "Jupiter", "sign_name": "Sagittarius"},
            "avayogi": {"lord": "Mercury", "sign_name": "Gemini"},
            "tithi_shunya_rashi": {"lord": "Saturn", "sign_name": "Aquarius"},
            "dagdha_rashi": {"lord": "Mars", "sign_name": "Aries"},
            "avayogi_tithi_shunya_overlap": {"is_active": False},
        },
        "chalit_house_shifts": [],
        "ashtakavarga": {
            "house_scores": [{"sign": 0, "sign_name": "Aries", "house": 10, "bindus": 28}],
            "strongest": {"sign": 0, "sign_name": "Aries", "house": 10, "bindus": 28},
            "weakest": {"sign": 0, "sign_name": "Aries", "house": 10, "bindus": 28},
            "total_bindus": 28,
            "bhinnashtakavarga": [
                {
                    "planet": "Sun",
                    "houses": [4, 4, 3, 5, 4, 5, 4, 3, 4, 5, 4, 4],
                    "total": 49,
                },
                {
                    "planet": "Lagna",
                    "houses": [5, 3, 4, 4, 5, 4, 3, 5, 4, 4, 4, 4],
                    "total": 49,
                },
            ],
        },
        "yogas_catalog": [
            {
                "name": "Gaja Kesari Yoga",
                "category": "gaja_kesari_yogas",
                "polarity": "auspicious",
                "strength": "High",
                "description": "Moon-Jupiter yoga",
            },
            {
                "name": "Dainya Yoga",
                "category": "parivartana_yogas_dainya_yogas",
                "polarity": "challenging",
                "strength": "Medium",
                "description": "Dusthana lord exchange",
            },
        ],
        "yogas_top": [
            {
                "name": "Gaja Kesari Yoga",
                "category": "gaja_kesari_yogas",
                "polarity": "auspicious",
                "strength": "High",
                "description": "Moon-Jupiter yoga",
            }
        ],
        "yogas_challenging": [
            {
                "name": "Dainya Yoga",
                "category": "parivartana_yogas_dainya_yogas",
                "polarity": "challenging",
                "strength": "Medium",
                "description": "Dusthana lord exchange",
            }
        ],
        "doshas": {
            "mangal_dosha": {"present": False},
            "kaal_sarp_dosha": {"present": False},
            "pitra_dosha": {"present": False},
        },
        "dasha": {
            "current": {
                "mahadasha": {"planet": "Rahu", "start": "2020-01-01", "end": "2038-01-01"},
                "antardasha": {"planet": "Sun", "start": "2026-01-01", "end": "2026-07-01"},
            },
            "maha_dashas": [
                {
                    "planet": "Rahu",
                    "start": "2020-01-01",
                    "end": "2038-01-01",
                    "antardashas": [
                        {"planet": "Rahu", "start": "2020-01-01", "end": "2022-09-13"},
                        {"planet": "Jupiter", "start": "2022-09-13", "end": "2025-02-06"},
                        {"planet": "Saturn", "start": "2025-02-06", "end": "2027-12-13"},
                        {"planet": "Mercury", "start": "2027-12-13", "end": "2030-06-31"},
                        {"planet": "Ketu", "start": "2030-07-01", "end": "2031-07-20"},
                        {"planet": "Venus", "start": "2031-07-20", "end": "2034-07-20"},
                        {"planet": "Sun", "start": "2034-07-20", "end": "2035-06-14"},
                        {"planet": "Moon", "start": "2035-06-14", "end": "2036-12-13"},
                        {"planet": "Mars", "start": "2036-12-13", "end": "2038-01-01"},
                    ],
                },
                {
                    "planet": "Jupiter",
                    "start": "2038-01-01",
                    "end": "2054-01-01",
                    "antardashas": [
                        {"planet": "Jupiter", "start": "2038-01-01", "end": "2040-02-18"},
                        {"planet": "Saturn", "start": "2040-02-18", "end": "2042-09-01"},
                    ],
                },
            ],
            "current_antardashas": [
                {"planet": "Rahu", "start": "2020-01-01", "end": "2022-09-13"},
            ],
        },
        "sade_sati": {"periods": [], "current_period": None, "upcoming_period": None, "moon_sign_basis": "test"},
        "life_themes": {"sun": {"sign_name": "Taurus"}, "lords": {}, "placements": {}},
        "remedies": {
            "ascendant_sign_name": "Cancer",
            "functional_benefics": ["Mars", "Jupiter", "Moon"],
            "life_stone": {
                "planet": "Moon",
                "gemstone": "Pearl",
                "role_hi": "लग्न स्वामी — जीवन रत्न उम्मीदवार",
                "meaning_hi": "शरीर और जीवन दिशा का आधार।",
                "meaning": "Supports vitality and life direction.",
            },
            "lucky_stone": {
                "planet": "Mars",
                "gemstone": "Red Coral",
                "role_hi": "पंचमेश — भाग्य रत्न उम्मीदवार",
                "meaning_hi": "बुद्धि और सृजन से जुड़ा।",
                "meaning": "Linked with intelligence and creativity.",
            },
            "bhagya_ratna": {
                "planet": "Jupiter",
                "gemstone": "Yellow Sapphire",
                "role_hi": "नवमेश — भाग्यरत्न उम्मीदवार",
                "meaning_hi": "भाग्य और धर्म का सहारा।",
                "meaning": "Supports fortune and dharma.",
            },
            "avoid_stones": [
                {
                    "planet": "Saturn",
                    "gemstone": "Blue Sapphire, only if suitability checks support it",
                    "reason": "Functional malefic for this lagna",
                    "reason_hi": "इस लग्न के लिए कार्यात्मक पाप ग्रह — साधारणतः न पहनें",
                }
            ],
            "suitability_note": "Conditional",
            "remedy_blueprint": {"priority_order": ["Rahu", "Sun"], "mantras": [], "caution": "Be steady"},
            "actionable_remedies": [
                {
                    "planet": "Rahu",
                    "role": "Mahadasha lord",
                    "weekday": "Saturday",
                    "best_time": "Evening after sunset",
                    "best_time_hi": "शनिवार सूर्यास्त के बाद संध्या",
                    "mantra": "Om Rahave Namaha",
                    "mantra_count": 108,
                    "mala_note": "Use a Rudraksha mala; 108 repetitions.",
                    "mala_note_hi": "रुद्राक्ष माला से १०८ जाप करें।",
                    "charity": "Donate dark blankets on Saturdays.",
                    "charity_hi": "शनिवार को गहरे कंबल दान करें।",
                    "seva": "Serve quietly in crisis contexts.",
                    "seva_hi": "संकटपूर्ण सेवा में शांत सहयोग करें।",
                    "wear_colors": "Smoke grey, dark blue",
                    "avoid_colors": "White, silver, cream",
                    "direction": "South-West",
                },
                {
                    "planet": "Sun",
                    "role": "Antardasha lord",
                    "weekday": "Sunday",
                    "best_time": "Morning after sunrise, facing East",
                    "best_time_hi": "रविवार सूर्योदय के बाद, पूर्व मुख",
                    "mantra": "Om Suryaya Namaha",
                    "mantra_count": 108,
                    "mala_note": "Use a Rudraksha mala; 108 repetitions.",
                    "mala_note_hi": "रुद्राक्ष माला से १०८ जाप करें।",
                    "charity": "Donate wheat or copper on Sundays.",
                    "charity_hi": "रविवार को गेहूँ या ताँबा दान करें।",
                    "seva": "Serve elders with sincerity.",
                    "seva_hi": "बड़ों की ईमानदारी से सेवा करें।",
                    "wear_colors": "Gold, saffron, orange",
                    "avoid_colors": "Blue, dark grey, black",
                    "direction": "East",
                },
            ],
            "lifestyle_colors": {
                "current_md": "Rahu",
                "current_ad": "Sun",
                "wear_colors": "Gold, saffron, orange",
                "support_colors": "Gold, saffron, orange",
                "avoid_colors": "Blue, dark grey, black",
                "period_note": "Current Mahadasha (Rahu) is mixed/neutral for color.",
                "period_note_hi": "वर्तमान महादशा (Rahu) रंग दृष्टि से मिश्रित/सम है।",
                "favor_evidence": [
                    {"color": "Gold", "evidence": "Gold ← Sun (functional benefic)"},
                ],
                "avoid_evidence": [
                    {"color": "Blue", "evidence": "Blue ← Saturn (functional malefic)"},
                ],
                "note": "Colors are scored from lagna functional nature, yogakaraka/lordship, and dignity.",
                "note_hi": "रंग लग्न के कार्यात्मक स्वभाव, योगकारक/भावेश और दशा से आँके गए हैं।",
            },

        },
        "nakshatra_deep_dive": {
            "moon": {
                "nakshatra": "Uttara Ashadha",
                "nakshatra_number": 21,
                "pada": 1,
                "lord": "Sun",
                "deity": "Vishvedevas",
                "quality": "Universal",
                "degrees_in_nakshatra": 2.1,
                "sign_name": "Sagittarius",
                "house": 6,
                "pada_lord": "Jupiter",
                "pada_element": "Fire",
                "pada_nature": "Initiative, beginning, action",
                "pada_syllable": "Be",
                "element": "Air",
                "guna": "Sattva",
                "animal": "Mongoose",
                "symbol": "Elephant tusk",
                "nature": "Universal, righteous",
                "characteristics": ["Victory", "Leadership", "Righteousness"],
                "gana": "Manushya",
                "nadi": "Adya",
                "yoni": "Mongoose",
            },
            "ascendant": {
                "nakshatra": "Pushya",
                "pada": 2,
                "lord": "Saturn",
                "deity": "Brihaspati",
                "sign_name": "Cancer",
            },
            "yoga_flags": [
                {"name": "Ganda Mool", "description": "Moon in Ganda Mool nakshatra - requires special remedies"}
            ],
            "planet_matrix": [
                {
                    "planet": "Moon",
                    "nakshatra": "Uttara Ashadha",
                    "pada": 1,
                    "lord": "Sun",
                    "deity": "Vishvedevas",
                }
            ],
            "remedy": {
                "deity": "Vishvedevas",
                "shakti": "Apradhrishya Shakti",
                "vriksha": "Jackfruit",
                "mantra": "Om Be",
                "pada_syllable": "Be",
                "optimal_direction": "North",
                "aligned_activity": "Victory and righteous action",
                "sound": "Chant the Beej Mantra 'Om Be' 108 times.",
            },
            "tara_bal": {
                "birth_moon_nakshatra_number": 21,
                "levels": [
                    {
                        "level": "mahadasha",
                        "level_label": "Mahadasha",
                        "planet": "Rahu",
                        "nakshatra": "Ardra",
                        "tara_name": "Vipat",
                        "tara_quality": "challenging",
                        "tara_effect": "bad",
                    },
                    {
                        "level": "antardasha",
                        "level_label": "Antardasha",
                        "planet": "Sun",
                        "nakshatra": "Krittika",
                        "tara_name": "Sampat",
                        "tara_quality": "supportive",
                        "tara_effect": "good",
                    },
                ],
            },
        },
    }


def test_assemble_pages_from_minimal_facts():
    fact_pack = _minimal_fact_pack()
    pages = assemble_janam_kundli_pages(
        {"person": fact_pack["person"], "language": "english", "fact_pack": fact_pack},
        {"sections": [], "headline": "Janam Kundli for Asha"},
    )
    assert len(pages) == 26
    assert pages[0]["title"] == "Janam Kundli"
    assert pages[0]["chart_refs"] == ["native_d1"]
    cover_titles = [t.get("title") for t in pages[0]["tables"]]
    assert any("Panchang" in (title or "") for title in cover_titles)
    assert any("planet" in (title or "").lower() or "ग्रह" in (title or "") for title in cover_titles)
    assert pages[1]["skip_render"] is True
    assert pages[2]["chart_refs"] == ["native_moon"]
    edu = next(p for p in pages if p.get("section_key") == "education_intellect")
    assert "Intellectual" in edu["title"] or "Education" in edu["title"]
    yoga_page = next(p for p in pages if p["title"] == "Yogas Catalog")
    assert len(yoga_page["tables"]) == 2
    assert "Auspicious yogas (1)" in yoga_page["tables"][0]["title"]
    assert "Challenging yogas (1)" in yoga_page["tables"][1]["title"]
    assert yoga_page["tables"][0]["rows"][0][1] == "Gaja Kesari Yoga"
    ashta = next(p for p in pages if p.get("section_key") == "ashtakavarga")
    assert len(ashta["tables"]) == 2
    assert "Bhinnashtakavarga" in ashta["tables"][1]["title"]
    assert ashta["tables"][1]["rows"][0][0] == "Sun"
    assert ashta["tables"][1]["rows"][0][-1] == "49"

    planet_page = next(p for p in pages if p.get("section_key") == "planetary_positions")
    assert len(planet_page["tables"]) >= 5  # placement + relations + 3 friendship matrices
    friend_titles = [t.get("title") for t in planet_page["tables"][2:5]]
    assert "Natural friendship (Naisargika Maitri)" in friend_titles[0]
    assert "Temporal friendship (Tatkalika Maitri)" in friend_titles[1]
    assert "Compound friendship (Panchadha Maitri)" in friend_titles[2]
    natural = planet_page["tables"][2]
    assert natural["rows"][0][0] == "Su"  # Sun abbr
    assert natural["rows"][0][1] == "—"  # self
    assert natural["rows"][0][2] == "F"  # Sun→Moon friend

    shodash_pages = [p for p in pages if str(p.get("section_key") or "").startswith("shodashvarga")]
    assert len(shodash_pages) == 2
    assert shodash_pages[0]["title"].startswith("Shodashvarga Charts")
    assert shodash_pages[0]["charts_per_row"] == 3
    assert shodash_pages[0]["chart_compact"] is True
    assert shodash_pages[0]["chart_refs"][0] == "native_d1"
    assert len(shodash_pages[0]["chart_refs"]) == 9
    assert len(shodash_pages[1]["chart_refs"]) == 7
    assert shodash_pages[1]["chart_refs"][-1] == "native_d60"

    dasha_page = next(p for p in pages if p.get("section_key") == "dasha_tree")
    assert dasha_page["tables_per_row"] == 3
    assert len(dasha_page["tables"]) >= 3  # overview + one table per mahadasha
    assert dasha_page["tables"][0]["title"] == "Mahadasha timeline"
    assert dasha_page["tables"][0].get("full_width") is True
    assert dasha_page["tables"][0]["rows"][0][:3] == ["Rahu", "2020-01-01", "2038-01-01"]
    assert dasha_page["tables"][1]["title"].startswith("Rahu ·")
    assert "2020-01-01" in dasha_page["tables"][1]["title"]
    assert dasha_page["tables"][1]["headers"][0] == "AD"
    assert dasha_page["tables"][1]["rows"][0][0] == "Rahu"
    assert dasha_page["tables"][1]["rows"][6][0] == "Sun"
    assert dasha_page["tables"][2]["title"].startswith("Jupiter ·")


def test_assemble_pages_hindi_titles():
    fact_pack = _minimal_fact_pack()
    pages = assemble_janam_kundli_pages(
        {"person": fact_pack["person"], "language": "hindi", "fact_pack": fact_pack},
        {"sections": [], "headline": "आशा की जन्म कुंडली"},
    )
    assert pages[0]["title"] == "जन्म कुंडली"
    edu = next(p for p in pages if p.get("section_key") == "education_intellect")
    assert "बौद्धिक" in edu["title"] or "शिक्षा" in edu["title"]
    assert pages[1]["tables"][0]["headers"][0] == "तथ्य"
    shodash = next(p for p in pages if p.get("section_key") == "shodashvarga_1")
    assert shodash["title"].startswith("षोडशवर्ग")
    assert shodash["charts_per_row"] == 3
    assert "native_d1" in shodash["chart_refs"]

    gem = next(p for p in pages if p.get("section_key") == "gemstones")
    assert gem["title"] == "रत्न सुझाव"
    assert "Blue Sapphire" not in (gem.get("summary") or "")
    assert all("only if suitability" not in b for b in (gem.get("bullets") or []))
    assert len(gem["tables"]) >= 2
    assert gem["tables"][0]["rows"][0][2] == "मोती"
    assert gem["tables"][1]["rows"][0][1] == "नीलम"
    assert "पाप" in gem["tables"][1]["rows"][0][2]


def test_panchang_nested_dicts_and_hindi_labels():
    fact_pack = _minimal_fact_pack()
    fact_pack["panchang"] = {
        "tithi": {"number": 17, "name": "Dwitiya", "paksha": "Krishna", "degrees_traversed": 8.43},
        "vara": {"number": 4, "name": "Wednesday"},
        "nakshatra": {"number": 15, "name": "Swati", "degrees_traversed": 3.08},
        "yoga": {"number": 14, "name": "Harshana", "degrees_traversed": 5.73},
        "karana": {"number": 34, "name": "Gara"},
        "sunrise": "1990-05-15T05:42:11",
        "sunset": "1990-05-15T18:55:03",
    }
    fact_pack["moon"]["sign_name"] = "Libra"
    fact_pack["moon"]["nakshatra"] = "Swati"
    fact_pack["ascendant"]["sign_name"] = "Cancer"
    fact_pack["life_themes"]["sun"]["sign_name"] = "Pisces"

    pages = assemble_janam_kundli_pages(
        {"person": fact_pack["person"], "language": "hindi", "fact_pack": fact_pack},
        {"sections": [], "headline": "टेस्ट"},
    )
    # Compact panchang on cover; full panchang kept on skip_render birth_panchang page.
    rows = {r[0]: r[1] for r in pages[0]["tables"][0]["rows"]}
    assert "{" not in rows["तिथि"]
    assert rows["तिथि"] == "कृष्ण द्वितीया"
    assert rows["वार"] == "बुधवार"
    assert rows["नक्षत्र"] == "स्वाति"
    assert rows["योग"] == "हर्षण"
    assert rows["करण"] == "गर"
    assert rows["सूर्य राशि"] == "मीन"
    assert rows["चंद्र राशि"] == "तुला"
    assert rows["लग्न"] == "कर्क"
    assert "सूर्योदय" not in rows  # cover uses compact panchang
    full_rows = {r[0]: r[1] for r in pages[1]["tables"][0]["rows"]}
    assert full_rows["सूर्योदय"] == "05:42"
    assert full_rows["सूर्यास्त"] == "18:55"

    cover_metrics = {m["label"]: m["value"] for m in pages[0]["metrics"]}
    assert cover_metrics["लग्न"] == "कर्क"
    assert cover_metrics["चंद्र"] == "तुला"

    # primary_charts (page 3) carries Moon chart + planet analysis (D1 is on cover)
    assert pages[2]["chart_refs"] == ["native_moon"]
    primary_tables = pages[2]["tables"]
    assert len(primary_tables) >= 3
    assert primary_tables[0]["headers"][0] == "ग्रह"
    assert "वृषभ" in primary_tables[0]["rows"][0][1]
    assert "कृत्तिका" in primary_tables[0]["rows"][0][3]
    assert primary_tables[2]["title"] == "विशेष बिंदु"
    assert primary_tables[2]["rows"][0][1].startswith("गुरु")

    ashta = next(p for p in pages if p.get("section_key") == "ashtakavarga")
    assert "भिन्नाष्टकवर्ग" in ashta["tables"][1]["title"]
    assert ashta["tables"][1]["rows"][0][0] == "सूर्य"

    # planetary_positions keeps D1 analysis tables plus three friendship matrices
    planet_rows = pages[4]["tables"][0]["rows"]
    assert planet_rows[0][0] == "सूर्य"
    assert "वृषभ" in planet_rows[0][1]
    assert "कृत्तिका" in planet_rows[0][3]
    assert len(pages[4]["tables"]) >= 5
    assert "प्राकृतिक मित्रता" in pages[4]["tables"][2]["title"]
    assert "तात्कालिक मित्रता" in pages[4]["tables"][3]["title"]
    assert "संयुक्त मित्रता" in pages[4]["tables"][4]["title"]
    assert pages[4]["tables"][2]["rows"][0][2] == "मित्र"  # Sun→Moon

    # D9 / D10 short matrices
    navamsha = next(p for p in pages if p.get("section_key") == "navamsha")
    dashamsha = next(p for p in pages if p.get("section_key") == "dashamsha")
    assert navamsha["tables"][0]["title"] == "डी-९ ग्रह सारिणी"
    assert navamsha["tables"][0]["rows"][0][2] == "स्वगृह"
    assert dashamsha["tables"][0]["title"] == "डी-१० ग्रह सारिणी"
    assert dashamsha["tables"][0]["rows"][0][2] == "उच्च"

    # emotional_blueprint / nakshatra deep-dive + Tara Bal
    emo = next(p for p in pages if p.get("section_key") == "emotional_blueprint")
    assert "नक्षत्र" in emo["title"]
    emo_titles = [tbl["title"] for tbl in emo["tables"]]
    assert "नक्षत्र पहचान" in emo_titles
    assert "चंद्र नक्षत्र स्वभाव" in emo_titles
    assert any("तारा बल" in title for title in emo_titles)
    tara_tbl = next(tbl for tbl in emo["tables"] if "तारा बल" in tbl["title"])
    assert tara_tbl["rows"][0][0] == "महादशा"
    assert tara_tbl["rows"][0][3] == "विपत्"
    assert tara_tbl["rows"][1][3] == "संपत्"
    nature_tbl = next(tbl for tbl in emo["tables"] if "स्वभाव" in tbl["title"])
    nature_map = {r[0]: r[1] for r in nature_tbl["rows"]}
    assert nature_map["गण"] == "मनुष्य"
    assert nature_map["नाड़ी"] == "आद्य"
