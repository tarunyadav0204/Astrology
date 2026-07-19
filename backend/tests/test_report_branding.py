from reports.branding import (
    branding_contact_line,
    has_custom_branding,
    normalize_report_branding,
)
from reports.pdf_service import _footer_brand_line, _rounded_logo_bytes, _load_logo_bytes


def test_normalize_trims_and_always_powered_by():
    out = normalize_report_branding({
        "business_name": "  Pandit Sharma  ",
        "phone": " 999 ",
        "show_powered_by": False,
    })
    assert out["business_name"] == "Pandit Sharma"
    assert out["phone"] == "999"
    assert out["show_powered_by"] is True
    assert has_custom_branding(out) is True


def test_empty_business_name_is_default_branding():
    out = normalize_report_branding({"tagline": "Hello", "phone": "1"})
    assert has_custom_branding(out) is False
    assert _footer_brand_line("english", "janam_kundli", out) == "AstroRoshni - Vedic Kundli"


def test_contact_line_joins_nonempty():
    line = branding_contact_line({
        "business_name": "X",
        "phone": "111",
        "email": "a@b.com",
        "website": "",
    })
    assert line == "111 · a@b.com"


def test_footer_always_astroroshni_vedic_kundli():
    assert _footer_brand_line("english", "janam_kundli", {"business_name": "Pandit Sharma"}) == (
        "AstroRoshni - Vedic Kundli"
    )
    assert _footer_brand_line("hindi", "janam_kundli", {}) == "AstroRoshni - Vedic Kundli"


def test_rounded_logo_returns_png_when_source_exists():
    raw = _load_logo_bytes()
    if not raw:
        return
    rounded = _rounded_logo_bytes(raw)
    assert rounded[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(rounded) > 100
