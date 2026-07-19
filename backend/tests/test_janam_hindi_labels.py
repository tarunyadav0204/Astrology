from reports.assembly.janam_kundli_labels import (
    label_deity,
    label_gemstone,
    label_nakshatra_quality,
    label_pada_nature,
    label_strength,
    label_yoga_name,
    localize_evidence_text,
)
from reports.assembly.janam_kundli_page_assembler import assemble_janam_kundli_pages
from reports.pdf_service import _person_birth_card, _PDF_LANGUAGE
from reportlab.lib.styles import getSampleStyleSheet


def test_core_hindi_fact_labels():
    assert label_strength("High", "hindi") == "उच्च"
    assert label_deity("Vayu", "hindi") == "वायु"
    assert label_nakshatra_quality("Movable", "hindi") == "चर"
    assert label_pada_nature("Initiative, beginning, action", "hindi") == "पहल, आरंभ, कर्म"
    assert label_gemstone("Blue Sapphire", "hindi") == "नीलम"
    assert label_yoga_name("Kendra-Trikona Raj Yoga", "hindi") == "केंद्र-त्रिकोण राज योग"
    assert localize_evidence_text(
        "Jupiter and Mars create dharmic career success", "hindi"
    ) == "गुरु और मंगल से धार्मिक/कर्म क्षेत्र में सफलता"
    assert localize_evidence_text(
        "7th lord Saturn and 1st lord Moon connected", "hindi"
    ) == "7वें भाव के स्वामी शनि और 1वें भाव के स्वामी चंद्र युक्त"
    assert localize_evidence_text(
        "Dusthana lord Mercury in dusthana house 8", "hindi"
    ) == "दुस्थान स्वामी बुध दुस्थान भाव 8 में"
    adhi = localize_evidence_text(
        "Benefics in the 6th, 7th, or 8th from the Moon. Indicates leadership, wealth, and a happy life.",
        "hindi",
    )
    assert "from the" not in adhi
    assert "Moon" not in adhi
    assert "शुभ ग्रह" in adhi
    vasi = localize_evidence_text(
        "Planets in the 12th house from the Sun. Makes the person charitable, and famous.",
        "hindi",
    )
    assert "Planets" not in vasi
    assert "Sun" not in vasi
    assert "परोपकारी" in vasi
    assert localize_evidence_text(
        "All planets in five signs - can be bound by obligations.", "hindi"
    ) == "पाँच राशियों में सभी ग्रह — दायित्वों में बाँध सकते हैं।"
    sani = localize_evidence_text(
        "10th lord Mars with Saturn - structured, responsible work style", "hindi"
    )
    assert sani == "10वें भाव के स्वामी मंगल के साथ शनि - अनुशासित, उत्तरदायी कार्य शैली"


def test_assemble_hindi_nakshatra_and_yoga_tables():
    from tests.test_janam_kundli_report_scaffold import _minimal_fact_pack

    fact = _minimal_fact_pack()
    pages = assemble_janam_kundli_pages(
        {"person": fact["person"], "language": "hindi", "fact_pack": fact},
        {"sections": [], "headline": "टेस्ट"},
    )
    emo = next(p for p in pages if "नक्षत्र" in (p.get("title") or ""))
    identity = next(t for t in emo["tables"] if t["title"] == "नक्षत्र पहचान")
    identity_blob = " ".join(str(c) for r in identity["rows"] for c in r)
    assert "विश्वेदेव" in identity_blob or "Vishvedevas" not in identity_blob
    pada = next(t for t in emo["tables"] if t["title"] == "पद विवरण")
    pada_map = {r[0]: r[1] for r in pada["rows"]}
    assert pada_map["पद स्वभाव"] == "पहल, आरंभ, कर्म"

    yoga = next(p for p in pages if p.get("title") == "योग सूची")
    assert yoga["tables"][0]["rows"][0][1] == "गज केसरी योग"
    assert yoga["tables"][0]["rows"][0][3] == "उच्च"

    gems = next(p for p in pages if "रत्न" in (p.get("title") or ""))
    life = next(m for m in gems["metrics"] if m["label"] == "जीवन रत्न")
    assert "मोती" in life["value"]


def test_practical_remedies_has_day_time_count_and_colors():
    from tests.test_janam_kundli_report_scaffold import _minimal_fact_pack

    fact = _minimal_fact_pack()
    pages = assemble_janam_kundli_pages(
        {"person": fact["person"], "language": "english", "fact_pack": fact},
        {"sections": [], "headline": "Test"},
    )
    page = next(p for p in pages if p.get("title") == "Practical Daily Remedies")
    titles = [t["title"] for t in page["tables"]]
    assert "Step-by-step planetary remedies" in titles
    assert "Mantra practice details" in titles
    assert "Color therapy (current dasha)" in titles
    step = next(t for t in page["tables"] if t["title"].startswith("Step-by-step"))
    assert step["rows"][0][2] == "Saturday"
    assert "108" in step["rows"][0][4]
    assert any(m["label"] == "Mantra count" for m in page["metrics"])

    hi_pages = assemble_janam_kundli_pages(
        {"person": fact["person"], "language": "hindi", "fact_pack": fact},
        {"sections": [], "headline": "टेस्ट"},
    )
    hi_page = next(p for p in hi_pages if "उपाय" in (p.get("title") or ""))
    hi_step = next(t for t in hi_page["tables"] if "चरणबद्ध" in t["title"])
    assert hi_step["rows"][0][2] == "शनिवार"
    assert "सूर्यास्त" in hi_step["rows"][0][3]


def test_birth_details_label_is_hindi():
    token = _PDF_LANGUAGE.set("hindi")
    try:
        styles = getSampleStyleSheet()
        # Minimal styles dict expected by helper
        from reports.pdf_service import _build_story_styles
        from reports.pdf_fonts import resolve_pdf_fonts

        fonts = resolve_pdf_fonts("hindi")
        styles = _build_story_styles(fonts)
        card = _person_birth_card({"name": "टेस्ट", "date": "1990-01-01", "time": "10:00", "place": "Delhi"}, styles, 100)
        # Flatten cell text
        blob = " ".join(str(c) for row in card._cellvalues for c in row)
        assert "जन्म विवरण" in blob
        assert "Birth details" not in blob
    finally:
        _PDF_LANGUAGE.reset(token)
