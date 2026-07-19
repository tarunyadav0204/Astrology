"""Scaffold tests for Janam Kundli report registration and fact assembly."""

from reports.assembly.janam_kundli_page_assembler import (
    JANAM_KUNDLI_PAGE_BLUEPRINT,
    assemble_janam_kundli_pages,
)
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


def test_hindi_latin_fallback_keeps_st_ligatures():
    """Mukta+HarfBuzz corrupts Latin 'st' (trust, AstroRoshni); Latin runs use Noto/Helvetica."""
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
    # Mixed line: Latin brand + Hindi label still split correctly.
    mixed = rich_text_for_fonts("AstroRoshni · जन्म कुंडली", fonts)
    assert "AstroRoshni" in mixed
    assert "जन्म" in mixed
    assert fonts.latin_regular in mixed
    assert fonts.regular in mixed


def test_janam_kundli_registered_and_enabled():
    assert "janam_kundli" in SUPPORTED_REPORT_TYPES
    assert "janam_kundli" in REPORT_TYPE_CONFIGS
    assert JANAM_KUNDLI_REPORT_CONFIG.enabled is True
    assert JANAM_KUNDLI_REPORT_CONFIG.page_count == 24


def test_janam_blueprint_has_24_pages_without_shadbala():
    keys = [p["key"] for p in JANAM_KUNDLI_PAGE_BLUEPRINT]
    assert len(keys) == 24
    assert "shadbala" not in keys
    assert keys[0] == "cover"
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[0]["charts"] == ["native_d1"]
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[1]["key"] == "birth_panchang"
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[1].get("skip_render") is True
    assert JANAM_KUNDLI_PAGE_BLUEPRINT[2]["charts"] == ["native_moon"]
    assert "present_phase" in keys
    assert "ashtakavarga" in keys


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
            "maha_dashas": [{"planet": "Rahu", "start": "2020-01-01", "end": "2038-01-01"}],
            "current_antardashas": [],
        },
        "sade_sati": {"periods": [], "current_period": None, "upcoming_period": None, "moon_sign_basis": "test"},
        "life_themes": {"sun": {"sign_name": "Taurus"}, "lords": {}, "placements": {}},
        "remedies": {
            "ascendant_sign_name": "Cancer",
            "functional_benefics": ["Mars", "Jupiter", "Moon"],
            "life_stone": {"planet": "Moon", "gemstone": "Pearl"},
            "lucky_stone": {"planet": "Mars", "gemstone": "Red Coral"},
            "bhagya_ratna": {"planet": "Jupiter", "gemstone": "Yellow Sapphire"},
            "avoid_stones": [],
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
                "wear_colors": "Smoke grey, dark blue, earthy tones",
                "support_colors": "Gold, saffron, orange",
                "avoid_colors": "White, silver, cream",
                "note": "Favor current Mahadasha lord colors.",
                "note_hi": "वर्तमान महादशा स्वामी के रंग अनुकूल रखें।",
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
    assert len(pages) == 24
    assert pages[0]["title"] == "Janam Kundli"
    assert pages[0]["chart_refs"] == ["native_d1"]
    cover_titles = [t.get("title") for t in pages[0]["tables"]]
    assert any("Panchang" in (title or "") for title in cover_titles)
    assert any("planet" in (title or "").lower() or "ग्रह" in (title or "") for title in cover_titles)
    assert pages[1]["skip_render"] is True
    assert pages[2]["chart_refs"] == ["native_moon"]
    assert pages[11]["title"]  # age-aware education title
    assert "Intellectual" in pages[11]["title"] or "Education" in pages[11]["title"]
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


def test_assemble_pages_hindi_titles():
    fact_pack = _minimal_fact_pack()
    pages = assemble_janam_kundli_pages(
        {"person": fact_pack["person"], "language": "hindi", "fact_pack": fact_pack},
        {"sections": [], "headline": "आशा की जन्म कुंडली"},
    )
    assert pages[0]["title"] == "जन्म कुंडली"
    assert "बौद्धिक" in pages[11]["title"] or "शिक्षा" in pages[11]["title"]
    assert pages[1]["tables"][0]["headers"][0] == "तथ्य"


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

    # planetary_positions keeps the same full D1 analysis tables
    planet_rows = pages[4]["tables"][0]["rows"]
    assert planet_rows[0][0] == "सूर्य"
    assert "वृषभ" in planet_rows[0][1]
    assert "कृत्तिका" in planet_rows[0][3]

    # D9 / D10 short matrices
    assert pages[3]["tables"][0]["title"] == "डी-९ ग्रह सारिणी"
    assert pages[3]["tables"][0]["rows"][0][2] == "स्वगृह"
    assert pages[6]["tables"][0]["title"] == "डी-१० ग्रह सारिणी"
    assert pages[6]["tables"][0]["rows"][0][2] == "उच्च"

    # emotional_blueprint / nakshatra deep-dive + Tara Bal
    emo = pages[10]
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
