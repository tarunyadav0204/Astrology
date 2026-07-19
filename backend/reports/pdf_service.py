from __future__ import annotations

import io
import os
import re
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils.env_json import parse_json_from_env

from .pdf_fonts import PdfFontSet, resolve_pdf_fonts, rich_text_for_fonts
from .assembly.janam_kundli_i18n import is_hindi
from .assembly.janam_kundli_labels import PLANET_ABBR_EN, PLANET_ABBR_HI, label_sign

_CLIENT = None
_PDF_FONTS: ContextVar[PdfFontSet] = ContextVar(
    "report_pdf_fonts",
    default=PdfFontSet(
        regular="Helvetica",
        bold="Helvetica-Bold",
        latin_regular="Helvetica",
        latin_bold="Helvetica-Bold",
        needs_latin_fallback=False,
    ),
)
_PDF_LANGUAGE: ContextVar[str] = ContextVar("report_pdf_language", default="english")
_PDF_REPORT_TYPE: ContextVar[str] = ContextVar("report_pdf_report_type", default="report")
_PDF_BRANDING: ContextVar[Dict[str, Any]] = ContextVar("report_pdf_branding", default={})

_DEFAULT_PDF_BUCKET_ENV_KEYS = (
    "REPORT_PDF_GCS_BUCKET",
    "REPORTS_PDF_GCS_BUCKET",
    "REPORT_PDF_BUCKET",
)

_DEFAULT_PDF_EXPIRY_SECONDS = int(os.getenv("REPORT_PDF_SIGNED_URL_TTL_S", "86400") or "86400")
_DEFAULT_PDF_FOLDER = "reports"

_ROOT_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_LOGO_PATH = _ROOT_DIR / "astroroshni_mobile" / "assets" / "logo.png"
_CONTENT_WIDTH = 178 * mm
_HALF_CONTENT_WIDTH = 86 * mm
_TABLE_GUTTER = 4 * mm

_ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

_SAFE_CHARS = re.compile(r"[^a-zA-Z0-9._-]+")


def _storage_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    from google.cloud import storage
    from google.oauth2 import service_account

    gcp_key = (os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or "").strip()
    if gcp_key:
        credentials_info = parse_json_from_env(gcp_key)
        if credentials_info:
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            _CLIENT = storage.Client(credentials=credentials)
        elif os.path.isfile(gcp_key):
            credentials = service_account.Credentials.from_service_account_file(gcp_key)
            _CLIENT = storage.Client(credentials=credentials)
        else:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_KEY is set but could not be parsed as JSON and is not a valid file path"
            )
    else:
        _CLIENT = storage.Client()
    return _CLIENT


def report_pdf_bucket_name() -> str:
    for key in _DEFAULT_PDF_BUCKET_ENV_KEYS:
        value = (os.getenv(key) or "").strip()
        if value:
            return value
    return ""


def _safe_filename(value: str) -> str:
    cleaned = _SAFE_CHARS.sub("_", (value or "").strip())
    return cleaned.strip("._-") or "report"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _escape_html(text: Any) -> str:
    value = _safe_text(text)
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _clean_markup(text: Any) -> str:
    value = _safe_text(text)
    value = re.sub(r"<term\b[^>]*>(.*?)</term>", r"\1", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("**", "").replace("*", "")
    return value.strip()


def _load_logo_bytes() -> Optional[bytes]:
    if _DEFAULT_LOGO_PATH.is_file():
        try:
            return _DEFAULT_LOGO_PATH.read_bytes()
        except Exception:
            return None
    return None


def _rounded_logo_bytes(raw: bytes, *, size_px: int = 256, radius_ratio: float = 0.22) -> bytes:
    """Return PNG bytes with soft rounded corners (avoids square black box edges)."""
    try:
        from PIL import Image as PILImage, ImageDraw

        src = PILImage.open(io.BytesIO(raw)).convert("RGBA")
        src = src.resize((size_px, size_px), PILImage.Resampling.LANCZOS)
        radius = max(8, int(size_px * radius_ratio))
        mask = PILImage.new("L", (size_px, size_px), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size_px - 1, size_px - 1), radius=radius, fill=255)
        out = PILImage.new("RGBA", (size_px, size_px), (255, 255, 255, 0))
        out.paste(src, (0, 0), mask=mask)
        buf = io.BytesIO()
        out.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return raw


def _logo_flowable(width_mm: float = 14, height_mm: float = 14) -> Optional[Image]:
    raw = _load_logo_bytes()
    if not raw:
        return None
    rounded = _rounded_logo_bytes(raw)
    return Image(io.BytesIO(rounded), width=width_mm * mm, height=height_mm * mm)


def _build_story_styles(fonts: PdfFontSet) -> Dict[str, ParagraphStyle]:
    # ReportLab defaults shaping=0; without this, Devanagari matras/conjuncts draw unshaped
    # even when uharfbuzz is installed and the TTFont is shapable.
    try:
        from reportlab.pdfbase.pdfmetrics import getFont

        shaping = 1 if bool(getattr(getFont(fonts.regular), "shapable", False)) else 0
    except Exception:
        shaping = 0

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ARCoverTitle",
        fontName=fonts.bold,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#7c2d12"),
        alignment=TA_CENTER,
        spaceAfter=4,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARCoverSubtitle",
        fontName=fonts.regular,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#8b5e34"),
        alignment=TA_CENTER,
        spaceAfter=10,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionTitle",
        fontName=fonts.bold,
        fontSize=16,
        leading=21,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=4,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionSubtitle",
        fontName=fonts.bold,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#ea580c"),
        spaceAfter=6,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARBody",
        fontName=fonts.regular,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#3f2a56"),
        spaceAfter=4,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARBodySmall",
        fontName=fonts.regular,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#5b4b6b"),
        spaceAfter=2,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARMetric",
        fontName=fonts.bold,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#9d174d"),
        alignment=TA_CENTER,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARMetricLabel",
        fontName=fonts.regular,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#831843"),
        alignment=TA_CENTER,
        shaping=shaping,
    ))
    styles.add(ParagraphStyle(
        name="ARHouseCell",
        fontName=fonts.regular,
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#2d1b4e"),
        alignment=TA_LEFT,
        shaping=shaping,
    ))
    return styles


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    fonts = _PDF_FONTS.get()
    cleaned = _clean_markup(text)
    is_bold = style.fontName == fonts.bold or str(style.fontName or "").endswith("-Bold")
    return Paragraph(rich_text_for_fonts(cleaned, fonts, bold=is_bold), style)


def _short_chip(text: Any, max_len: int = 32) -> str:
    value = _safe_text(text)
    if not value:
        return "--"
    value = value.replace("_", " ").strip()
    if value == value.lower() and " " in value:
        value = " ".join(part.capitalize() for part in value.split())
    if len(value) <= max_len:
        return value
    for sep in (". ", " — ", " – ", " - ", ": ", "; ", ", "):
        if sep in value:
            part = value.split(sep)[0].strip()
            if 3 < len(part) <= max_len:
                return part
    return value[: max_len - 1].rstrip() + "…"


def _humanize_token(text: Any) -> str:
    value = _safe_text(text)
    if not value:
        return "--"
    if "_" in value or value == value.lower():
        return " ".join(part.capitalize() for part in value.replace("_", " ").split())
    return value


def _metric_card(label: Any, value: Any, styles: Dict[str, ParagraphStyle], width: float = 42 * mm) -> Table:
    value_style = ParagraphStyle(
        "ARMetricWrap",
        parent=styles["ARMetric"],
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
    )
    card = Table(
        [
            [_p(_short_chip(value, 28), value_style)],
            [_p(label, styles["ARMetricLabel"])],
        ],
        colWidths=[width],
        rowHeights=[14 * mm, 7 * mm],
    )
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#f3d3c3")),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("VALIGN", (0, 1), (0, 1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return card


def _metric_row(metrics: Sequence[Dict[str, Any]], styles: Dict[str, ParagraphStyle], width: float = _CONTENT_WIDTH) -> Table:
    visible = [metric for metric in (metrics or [])[:4] if metric]
    cols = max(1, len(visible))
    gutter = _TABLE_GUTTER
    card_width = max(28 * mm, (width - (gutter * (cols - 1))) / cols)
    cards: List[Any] = []
    for metric in visible:
        cards.append(_metric_card(metric.get("label"), metric.get("value"), styles, width=card_width))
    if not cards:
        return Table([[]])
    table = Table([cards], colWidths=[card_width] * len(cards), hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), gutter),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return table


def _bullet_list(items: Sequence[Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    out: List[Any] = []
    for item in items or []:
        txt = _clean_markup(item)
        if not txt:
            continue
        out.append(_p(f"• {txt}", styles["ARBody"]))
    return out


def _normalize_table_rows(rows: Sequence[Any]) -> List[List[Any]]:
    normalized: List[List[Any]] = []
    headers: List[str] = []
    for row in rows or []:
        if isinstance(row, dict):
            if not headers:
                headers = [str(key) for key in row.keys()]
                normalized.append(headers)
            normalized.append([row.get(key) for key in headers])
        elif isinstance(row, (list, tuple)):
            normalized.append(list(row))
        else:
            normalized.append([row])
    return normalized


def _table_from_rows(
    rows: Sequence[Any],
    styles: Dict[str, ParagraphStyle],
    width: float = _CONTENT_WIDTH,
    *,
    compact: bool = False,
) -> Table:
    normalized_rows = _normalize_table_rows(rows)
    data = []
    for row in normalized_rows:
        data.append([_p(cell, styles["ARBodySmall"]) for cell in row])
    max_cols = max((len(row) for row in data), default=1)
    # Give the first column (planet/label) a bit more room in dense matrices.
    if compact and max_cols >= 10:
        label_w = width * 0.14
        rest = (width - label_w) / (max_cols - 1)
        col_widths = [label_w] + [rest] * (max_cols - 1)
    else:
        col_widths = [width / max_cols] * max_cols
    font_size = 6.5 if compact else 8
    leading = 8 if compact else 10
    pad = 2 if compact else 6
    vpad = 3 if compact else 5
    table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
        ("FONTNAME", (0, 0), (-1, 0), _PDF_FONTS.get().bold),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), leading),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#f3d3c3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), vpad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), vpad),
        ("SHAPING", (0, 0), (-1, -1), 1),
    ]))
    return table


def _planet_sign_index(planet_data: Any) -> Optional[int]:
    if not isinstance(planet_data, dict):
        return None
    if planet_data.get("sign") is not None:
        try:
            return int(planet_data.get("sign")) % 12
        except Exception:
            pass
    sign_name = _safe_text(planet_data.get("sign_name"))
    if sign_name in _ZODIAC_SIGNS:
        return _ZODIAC_SIGNS.index(sign_name)
    longitude = planet_data.get("longitude")
    if longitude is not None:
        try:
            return int(float(longitude) / 30.0) % 12
        except Exception:
            return None
    return None


def _planet_abbr(planet_name: str) -> str:
    language = _PDF_LANGUAGE.get()
    if is_hindi(language):
        return PLANET_ABBR_HI.get(planet_name) or planet_name[:2]
    return PLANET_ABBR_EN.get(planet_name) or planet_name[:2]


def _planet_degree_in_sign(planet_data: Dict[str, Any]) -> Optional[int]:
    """Whole degrees within the sign (0–29), from `degree` or longitude."""
    raw = planet_data.get("degree")
    if raw is None:
        longitude = planet_data.get("longitude")
        if longitude is None:
            return None
        try:
            raw = float(longitude) % 30.0
        except Exception:
            return None
    try:
        return int(float(raw)) % 30
    except Exception:
        return None


def _planet_chart_label(planet_name: str, planet_data: Dict[str, Any]) -> str:
    """Compact chart glyph: Su12° / सू12° (optional R for retrograde)."""
    abbr = _planet_abbr(planet_name)
    deg = _planet_degree_in_sign(planet_data)
    label = f"{abbr}{deg}°" if deg is not None else abbr
    if planet_data.get("retrograde") or planet_data.get("is_retrograde"):
        label = f"{label}R"
    return label


def _chart_house_map(chart_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    houses = chart_data.get("houses") or []
    planets = chart_data.get("planets") or {}
    # Chalit / Chandra: place strictly by house. Sign fallback would redraw whole-sign D1.
    force_house = bool(chart_data.get("_place_by_house") or chart_data.get("_reference") in {"chalit", "moon"})
    house_map: Dict[int, Dict[str, Any]] = {}
    for index, house in enumerate(houses, start=1):
        if not isinstance(house, dict):
            continue
        house_num = int(house.get("house_number") or index)
        try:
            sign_index = int(house.get("sign", index - 1) or 0) % 12
        except Exception:
            sign_index = (index - 1) % 12
        planet_labels = []
        for planet_name, planet_data in planets.items():
            if not isinstance(planet_data, dict):
                continue
            if planet_name in {"InduLagna", "Gulika", "Mandi"}:
                continue
            label = _planet_chart_label(planet_name, planet_data)
            planet_house = planet_data.get("house")
            place_by_house = force_house or bool(planet_data.get("_place_by_house")) or planet_house is not None
            if place_by_house:
                try:
                    if planet_house is not None and int(planet_house) == house_num:
                        planet_labels.append(label)
                except Exception:
                    pass
                continue
            planet_sign = _planet_sign_index(planet_data)
            if planet_sign == sign_index:
                planet_labels.append(label)
        house_map[house_num] = {
            "sign": _ZODIAC_SIGNS[sign_index % 12],
            "planets": planet_labels,
        }
    return house_map


def _chart_cell(house_num: int, house_info: Dict[str, Any], styles: Dict[str, ParagraphStyle], width: float) -> Table:
    planet_text = ", ".join(house_info.get("planets") or []) or "—"
    cell_style = ParagraphStyle(
        "ARHouseCellFixed",
        parent=styles["ARHouseCell"],
        fontSize=7,
        leading=8,
    )
    label_style = ParagraphStyle(
        "ARHouseLabelFixed",
        parent=styles["ARBodySmall"],
        fontSize=7,
        leading=8,
    )
    rows = [
        [_p(f"H{house_num}", label_style)],
        [_p(house_info.get("sign") or "", label_style)],
        [_p(planet_text, cell_style)],
    ]
    cell = Table(rows, colWidths=[width], rowHeights=[4.2 * mm, 4.2 * mm, 8.5 * mm])
    cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#f3d3c3")),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return cell


def _resolve_draw_style(report_document: Optional[Dict[str, Any]] = None) -> str:
    """Both partners must use the same chart geometry."""
    raw = ""
    if isinstance(report_document, dict):
        raw = _safe_text(report_document.get("chart_style") or "").lower()
    if raw == "south":
        return "south"
    return "north"


# SVG centers from mobile/web NorthIndianChart (400x400, y-down). ReportLab y is up.
_NORTH_HOUSE_CENTERS_SVG = {
    1: (200, 100),
    2: (100, 50),
    3: (50, 100),
    4: (100, 200),
    5: (50, 300),
    6: (100, 350),
    7: (200, 300),
    8: (300, 350),
    9: (350, 300),
    10: (300, 200),
    11: (350, 100),
    12: (300, 50),
}


def _sign_number_from_house_info(house_info: Dict[str, Any]) -> int:
    sign_name = _safe_text(house_info.get("sign"))
    if sign_name in _ZODIAC_SIGNS:
        return _ZODIAC_SIGNS.index(sign_name) + 1
    return 0


def _svg_to_rl(x: float, y: float, scale: float, size: float) -> tuple[float, float]:
    return x * scale, size - (y * scale)


def _chart_font_names() -> tuple[str, str]:
    fonts = _PDF_FONTS.get()
    return fonts.regular, fonts.bold


def _rashi_anchor(house_num: int, cx: float, cy: float, scale: float) -> tuple[float, float]:
    """Park rashi number away from planet cluster (matches mobile offsets, RL y-up)."""
    # SVG y offsets converted: +svg_y → -rl_y relative to center.
    offsets = {
        1: (-5, -55),
        2: (-10, -25),
        3: (10, -5),
        4: (40, -5),
        5: (10, -10),
        6: (-15, 10),
        7: (-5, 40),
        8: (-5, 10),
        9: (-20, -5),
        10: (-50, -5),
        11: (-25, -5),
        12: (-5, -20),
    }
    dx, dy = offsets.get(house_num, (0, 0))
    return cx + dx * scale, cy + dy * scale


def _planet_anchor(house_num: int, cx: float, cy: float, scale: float, count: int) -> tuple[float, float, float]:
    """Return base x, base y, and line step for planet labels (RL coords)."""
    step = max(7.0, 9.0 * scale)
    if house_num == 1:
        return cx, cy + 8 * scale, step
    if house_num in {2, 12}:
        return cx, cy + 6 * scale, step
    if house_num in {3, 4, 5}:
        return cx - 12 * scale, cy + 4 * scale, step
    if house_num in {6, 7, 8}:
        return cx, cy - 6 * scale, -step
    if house_num in {9, 10, 11}:
        return cx + 12 * scale, cy + 4 * scale, step
    return cx, cy - 8 * scale, -step


def _build_north_indian_diamond_drawing(
    house_map: Dict[int, Dict[str, Any]],
    *,
    size: float,
) -> Drawing:
    """Diamond North Indian kundli matching web/mobile ChartWidget geometry."""
    scale = size / 400.0
    drawing = Drawing(size, size)
    stroke = colors.HexColor("#e67e22")
    stroke_soft = colors.HexColor("#f0a36c")
    ink = colors.HexColor("#3d2a1f")
    accent = colors.HexColor("#d35400")
    font_reg, font_bold = _chart_font_names()
    asc_label = "लग्न" if is_hindi(_PDF_LANGUAGE.get()) else "ASC"

    pad = 2.0 * scale
    drawing.add(
        Rect(
            pad,
            pad,
            size - 2 * pad,
            size - 2 * pad,
            strokeColor=stroke,
            fillColor=colors.white,
            strokeWidth=1.4,
        )
    )

    diamond_svg = [(200, 2), (398, 200), (200, 398), (2, 200)]
    diamond_pts: List[float] = []
    for sx, sy in diamond_svg:
        rx, ry = _svg_to_rl(sx, sy, scale, size)
        diamond_pts.extend([rx, ry])
    drawing.add(
        Polygon(
            diamond_pts,
            strokeColor=stroke,
            fillColor=None,
            strokeWidth=1.3,
        )
    )

    x1, y1 = _svg_to_rl(2, 2, scale, size)
    x2, y2 = _svg_to_rl(398, 398, scale, size)
    drawing.add(Line(x1, y1, x2, y2, strokeColor=stroke_soft, strokeWidth=1.0))
    x3, y3 = _svg_to_rl(398, 2, scale, size)
    x4, y4 = _svg_to_rl(2, 398, scale, size)
    drawing.add(Line(x3, y3, x4, y4, strokeColor=stroke_soft, strokeWidth=1.0))

    for house_num in range(1, 13):
        cx_svg, cy_svg = _NORTH_HOUSE_CENTERS_SVG[house_num]
        cx, cy = _svg_to_rl(cx_svg, cy_svg, scale, size)
        info = house_map.get(house_num) or {}
        sign_num = _sign_number_from_house_info(info)
        planets = list(info.get("planets") or [])

        # Rashi number parked toward house corner; planets occupy the center cluster.
        rashi_label = str(sign_num) if sign_num else "—"
        rashi_size = max(6.5, min(9.0, 8.0 * scale * 1.15))
        rx, ry = _rashi_anchor(house_num, cx, cy, scale)
        drawing.add(
            String(
                rx,
                ry,
                rashi_label,
                fontSize=rashi_size,
                fillColor=accent if house_num == 1 else ink,
                textAnchor="middle",
                fontName=font_bold,
            )
        )
        if house_num == 1:
            drawing.add(
                String(
                    cx + 22 * scale,
                    cy - 18 * scale,
                    asc_label,
                    fontSize=max(5.5, 6.5 * scale),
                    fillColor=accent,
                    textAnchor="middle",
                    fontName=font_bold,
                )
            )

        if not planets:
            continue
        # Degree suffixes lengthen labels — prefer slightly smaller type and earlier wrapping.
        planet_font = max(4.5, min(6.5, 7.0 - max(0, len(planets) - 1) * 0.4))
        # One planet per line when crowded to avoid horizontal collisions.
        if len(planets) == 1:
            lines = [planets[0]]
        elif len(planets) == 2:
            lines = [" ".join(planets)]
        else:
            lines = [planets[i] for i in range(min(len(planets), 6))]

        base_x, base_y, step = _planet_anchor(house_num, cx, cy, scale, len(planets))
        # Center multi-line block around the planet anchor.
        start_y = base_y + ((len(lines) - 1) * abs(step) / 2.0) * (1 if step < 0 else -1)
        for idx, line in enumerate(lines):
            drawing.add(
                String(
                    base_x,
                    start_y + idx * step,
                    line,
                    fontSize=planet_font,
                    fillColor=ink,
                    textAnchor="middle",
                    fontName=font_reg,
                )
            )

    return drawing


def _render_north_indian_diamond_chart(
    chart_data: Dict[str, Any],
    house_map: Dict[int, Dict[str, Any]],
    title: str,
    styles: Dict[str, ParagraphStyle],
    width: float,
    *,
    compact: bool = False,
) -> Table:
    # Cover side-by-side uses ~100mm column; allow a larger compact diamond there.
    max_diamond = 86 * mm if compact else 78 * mm
    min_diamond = 52 * mm if compact else 52 * mm
    chart_size = max(min_diamond, min(width - 6 * mm, max_diamond))
    drawing = _build_north_indian_diamond_drawing(house_map, size=chart_size)
    asc_name = label_sign(
        _ZODIAC_SIGNS[int((chart_data.get("ascendant", 0) or 0) / 30) % 12],
        _PDF_LANGUAGE.get(),
    )
    caption = Paragraph(
        f"<b>{_escape_html(title)}</b> · <font size='8'>{_escape_html(asc_name)}</font>"
        if compact
        else f"<b>{_escape_html(title)}</b><br/><font size='8'>{_escape_html(asc_name)}</font>",
        styles["ARBodySmall"],
    )
    pad = 3 if compact else 6
    inner = Table([[drawing]], colWidths=[chart_size])
    inner.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1 if compact else 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 if compact else 2),
    ]))
    table = Table([[caption], [inner]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8f5")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#f3d3c3")),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _render_chart_grid(
    chart_data: Optional[Dict[str, Any]],
    style: str,
    title: str,
    styles: Dict[str, ParagraphStyle],
    width: float = _HALF_CONTENT_WIDTH,
    *,
    compact: bool = False,
) -> Table:
    if not chart_data:
        return Table([[ _p("Chart data unavailable", styles["ARBodySmall"]) ]], colWidths=[width])

    house_map = _chart_house_map(chart_data)
    # Always use the same structure for every native in a report.
    draw_style = "south" if style == "south" else "north"
    if draw_style == "north":
        return _render_north_indian_diamond_chart(
            chart_data, house_map, title, styles, width, compact=compact
        )

    ordered_houses = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
    ]

    inner_width = max(36 * mm, width - 8 * mm)
    cell_width = inner_width / 4
    grid_rows: List[List[Any]] = []
    for row in ordered_houses:
        rendered_row = []
        for house_num in row:
            if not house_num:
                rendered_row.append("")
                continue
            rendered_row.append(_chart_cell(house_num, house_map.get(house_num, {}), styles, width=cell_width))
        grid_rows.append(rendered_row)

    asc_name = label_sign(
        _ZODIAC_SIGNS[int((chart_data.get("ascendant", 0) or 0) / 30) % 12],
        _PDF_LANGUAGE.get(),
    )
    south_label = "दक्षिण भारतीय · लग्न" if is_hindi(_PDF_LANGUAGE.get()) else "South Indian · Ascendant"
    caption = Paragraph(
        f"<b>{_escape_html(title)}</b><br/><font size='8'>{_escape_html(south_label)}: {_escape_html(asc_name)}</font>",
        styles["ARBodySmall"],
    )
    inner = Table(grid_rows, colWidths=[cell_width] * 4)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]
    inner.setStyle(TableStyle(style_cmds))

    table = Table([[caption], [inner]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8f5")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#f3d3c3")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return table


def _chart_payload(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("divisional_chart"), dict):
        payload = value.get("divisional_chart")
        if isinstance(payload, dict) and (payload.get("houses") or payload.get("planets")):
            # Preserve native identity stamped on the wrapper.
            if value.get("_native_name") and not payload.get("_native_name"):
                payload = dict(payload)
                for key in ("_native_name", "_native_date", "_native_time", "_native_place"):
                    if value.get(key) is not None:
                        payload[key] = value.get(key)
            return payload
    if value.get("houses") or value.get("planets"):
        return value
    return None


def _chart_title(chart: Optional[Dict[str, Any]], fallback_name: str, chart_label: str) -> str:
    native = _safe_text((chart or {}).get("_native_name") or fallback_name)
    return f"{native} · {chart_label}"


def _person_label(report_document: Dict[str, Any], key: str, fallback: str) -> str:
    pair = report_document.get("pair") or {}
    person = pair.get(key) or {}
    return _safe_text(person.get("name") or fallback)


def _chart_block(
    report_document: Dict[str, Any],
    ref: str,
    styles: Dict[str, ParagraphStyle],
    width: float = _HALF_CONTENT_WIDTH,
    *,
    compact: bool = False,
) -> Optional[Table]:
    chart_data = report_document.get("chart_data") or {}
    boy_name = _person_label(report_document, "boy", "Person A")
    girl_name = _person_label(report_document, "girl", "Person B")
    native_name = _person_label(report_document, "native", boy_name)
    # Critical: never mix north for one partner and south for the other.
    style = _resolve_draw_style(report_document)

    boy_d1 = _chart_payload(chart_data.get("boy") or chart_data.get("native"))
    girl_d1 = _chart_payload(chart_data.get("girl"))
    boy_d9 = _chart_payload(chart_data.get("boy_d9") or chart_data.get("native_d9"))
    girl_d9 = _chart_payload(chart_data.get("girl_d9"))
    boy_d2 = _chart_payload(chart_data.get("boy_d2") or chart_data.get("native_d2"))
    girl_d2 = _chart_payload(chart_data.get("girl_d2"))
    boy_d7 = _chart_payload(chart_data.get("boy_d7"))
    girl_d7 = _chart_payload(chart_data.get("girl_d7"))
    native_d10 = _chart_payload(chart_data.get("native_d10") or chart_data.get("boy_d10"))
    native_d30 = _chart_payload(chart_data.get("native_d30") or chart_data.get("boy_d30"))
    native_moon = _chart_payload(chart_data.get("native_moon") or chart_data.get("boy_moon"))
    native_chalit = _chart_payload(chart_data.get("native_chalit") or chart_data.get("boy_chalit"))

    hi = is_hindi(_PDF_LANGUAGE.get())
    labels = {
        "d1": "डी-१ राशि" if hi else "D1 Rashi",
        "d2": "डी-२ होरा" if hi else "D2 Hora",
        "d7": "डी-७ सप्तमांश" if hi else "D7 Saptamsha",
        "d9": "डी-९ नवांश" if hi else "D9 Navamsa",
        "d10": "डी-१० दशमांश" if hi else "D10 Dasamsa",
        "d30": "डी-३० त्रिंशांश" if hi else "D30 Trimsamsa",
        "moon": "चंद्र कुंडली" if hi else "Chandra Kundli",
        "chalit": "भाव चलित" if hi else "Bhava Chalit",
    }
    ref_map = {
        "d1_north": (boy_d1, _chart_title(boy_d1, boy_name, labels["d1"]), style),
        "d1_south": (girl_d1, _chart_title(girl_d1, girl_name, labels["d1"]), style),
        "d9_north": (boy_d9, _chart_title(boy_d9, boy_name, labels["d9"]), style),
        "d9_south": (girl_d9, _chart_title(girl_d9, girl_name, labels["d9"]), style),
        "boy_d1": (boy_d1, _chart_title(boy_d1, boy_name, labels["d1"]), style),
        "girl_d1": (girl_d1, _chart_title(girl_d1, girl_name, labels["d1"]), style),
        "boy_d9": (boy_d9, _chart_title(boy_d9, boy_name, labels["d9"]), style),
        "girl_d9": (girl_d9, _chart_title(girl_d9, girl_name, labels["d9"]), style),
        "boy_d2": (boy_d2, _chart_title(boy_d2, boy_name, labels["d2"]), style),
        "girl_d2": (girl_d2, _chart_title(girl_d2, girl_name, labels["d2"]), style),
        "boy_d7": (boy_d7, _chart_title(boy_d7, boy_name, labels["d7"]), style),
        "girl_d7": (girl_d7, _chart_title(girl_d7, girl_name, labels["d7"]), style),
        "native_d1": (boy_d1, _chart_title(boy_d1, native_name, labels["d1"]), style),
        "native_d2": (boy_d2, _chart_title(boy_d2, native_name, labels["d2"]), style),
        "native_d9": (boy_d9, _chart_title(boy_d9, native_name, labels["d9"]), style),
        "native_d10": (native_d10, _chart_title(native_d10, native_name, labels["d10"]), style),
        "native_d30": (native_d30, _chart_title(native_d30, native_name, labels["d30"]), style),
        "boy_d30": (native_d30, _chart_title(native_d30, native_name, labels["d30"]), style),
        "native_moon": (native_moon, _chart_title(native_moon, native_name, labels["moon"]), style),
        "boy_moon": (native_moon, _chart_title(native_moon, native_name, labels["moon"]), style),
        "native_chalit": (native_chalit, _chart_title(native_chalit, native_name, labels["chalit"]), style),
        "boy_chalit": (native_chalit, _chart_title(native_chalit, native_name, labels["chalit"]), style),
    }
    chart_info = ref_map.get(ref)
    if not chart_info:
        return None
    chart, title, draw_style = chart_info
    if not chart:
        return None
    grid = _render_chart_grid(
        chart, style=draw_style, title=title, styles=styles, width=width, compact=compact
    )
    return Table([[grid]], colWidths=[width])


def _chart_table(report_document: Dict[str, Any], refs: Sequence[str], styles: Dict[str, ParagraphStyle]) -> Optional[Table]:
    blocks: List[Any] = []
    for ref in refs or []:
        block = _chart_block(report_document, ref, styles, width=_HALF_CONTENT_WIDTH)
        if block is not None:
            blocks.append((ref, block))
    if not blocks:
        return None

    rows: List[List[Any]] = []
    col_width = (_CONTENT_WIDTH - _TABLE_GUTTER) / 2
    for index in range(0, len(blocks), 2):
        pair = blocks[index:index + 2]
        if len(pair) == 1:
            full = _chart_block(report_document, pair[0][0], styles, width=_CONTENT_WIDTH)
            rows.append([full or pair[0][1]])
        else:
            rows.append([pair[0][1], pair[1][1]])
    table = Table(rows, colWidths=[col_width, col_width] if len(rows[0]) > 1 else [_CONTENT_WIDTH], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def _format_generated_at(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return _safe_text(value)
    else:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d %b %Y")


def _guna_score(score: Dict[str, Any]) -> str:
    for key in ("guna_milan", "ashtakoota"):
        block = score.get(key) or {}
        if isinstance(block, dict) and block.get("effective_total_score") is not None:
            return f"{_safe_text(block.get('effective_total_score'))}/36"
    if score.get("effective_total_score") is not None:
        return f"{_safe_text(score.get('effective_total_score'))}/36"
    return "--/36"


def _cover_verdict_chip(report_document: Dict[str, Any], premium: Dict[str, Any], score: Dict[str, Any]) -> str:
    recommendation = score.get("recommendation") or {}
    for candidate in (
        recommendation.get("verdict"),
        premium.get("headline"),
        score.get("grade"),
    ):
        text = _safe_text(candidate)
        if text:
            return _short_chip(text, 22)
    return "See summary"


def _timing_climate_chip(timing: Dict[str, Any]) -> str:
    raw = (
        (timing.get("current_window") or {}).get("climate")
        or timing.get("joint_readiness_label")
        or ""
    )
    text = _humanize_token(raw)
    return _short_chip(text, 22) if text and text != "--" else "See timing"


def _person_birth_card(
    person: Dict[str, Any],
    styles: Dict[str, ParagraphStyle],
    width: float,
    *,
    include_name: bool = True,
) -> Table:
    name_style = ParagraphStyle(
        "ARCoverPersonName",
        parent=styles["ARSectionTitle"],
        fontSize=12,
        leading=14,
        spaceAfter=1,
        spaceBefore=0,
    )
    label_style = ParagraphStyle(
        "ARCoverBirthLabel",
        parent=styles["ARSectionSubtitle"],
        fontSize=9,
        leading=11,
        spaceAfter=2,
        spaceBefore=0,
    )
    body_style = ParagraphStyle(
        "ARCoverBirthBody",
        parent=styles["ARBodySmall"],
        fontSize=8,
        leading=10,
        spaceAfter=1,
        spaceBefore=0,
    )
    language = _PDF_LANGUAGE.get()
    birth_label = "जन्म विवरण" if is_hindi(language) else "Birth details"
    native_fallback = "जातक" if is_hindi(language) else "Native"
    rows: List[List[Any]] = []
    if include_name:
        rows.append([_p(_safe_text(person.get("name") or native_fallback), name_style)])
    rows.extend([
        [_p(birth_label, label_style)],
        [_p(_safe_text(person.get("date")) or "—", body_style)],
        [_p(_safe_text(person.get("time")) or "—", body_style)],
        [_p(_safe_text(person.get("place")) or "—", body_style)],
    ])
    column = Table(rows, colWidths=[max(40 * mm, width - 6 * mm)])
    column.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return column


def _render_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    report_type = str(report_document.get("report_type") or "").lower()
    if report_type == "wealth":
        return _render_wealth_cover(report_document, page, styles)
    if report_type == "health":
        return _render_health_cover(report_document, page, styles)
    if report_type == "janam_kundli":
        return _render_janam_kundli_cover(report_document, page, styles)

    pair = report_document.get("pair") or {}
    boy = pair.get("boy") or {}
    girl = pair.get("girl") or {}
    score = report_document.get("score_summary") or {}
    premium = report_document.get("premium_report") or {}
    recommendation = score.get("recommendation") or {}
    timing = ((score.get("timing_overlay") or {}).get("shared") or {})
    verdict = (
        premium.get("compatibility_verdict")
        or page.get("summary")
        or recommendation.get("verdict")
        or "This report studies the relationship through classical Vedic layers, not a single calculator score."
    )
    generated_label = _format_generated_at(report_document.get("generated_at"))

    story: List[Any] = []
    logo = _logo_flowable(14, 14)
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 3 * mm))

    story.append(_p("Partnership Compatibility Report", styles["ARCoverTitle"]))
    story.append(_p(f"{_safe_text(boy.get('name') or 'Person A')} & {_safe_text(girl.get('name') or 'Person B')}", styles["ARCoverSubtitle"]))
    story.append(_p(f"Generated on {generated_label}", styles["ARCoverSubtitle"]))
    story.append(Spacer(1, 3 * mm))

    # Birth cards only — embedding charts in these cells caused overflow/overlap.
    col_width = (_CONTENT_WIDTH - _TABLE_GUTTER) / 2
    pair_table = Table(
        [[
            _person_birth_card(boy, styles, col_width),
            _person_birth_card(girl, styles, col_width),
        ]],
        colWidths=[col_width, col_width],
    )
    pair_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8f5")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#f3d3c3")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#f7cdb4")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(pair_table)
    story.append(Spacer(1, 4 * mm))

    metrics = [
        {"label": "Overall reading", "value": _short_chip(score.get("grade") or "See summary", 18)},
        {"label": "Match tone", "value": _cover_verdict_chip(report_document, premium, score)},
        {"label": "Guna Milan", "value": _guna_score(score)},
        {"label": "Timing climate", "value": _timing_climate_chip(timing)},
    ]
    story.append(_metric_row(metrics, styles))
    story.append(Spacer(1, 4 * mm))

    story.append(_p("How to read this report", styles["ARSectionSubtitle"]))
    story.append(_p(
        "Numbers are supporting context only. The chapters below explain Moon comfort, Venus-Mars chemistry, "
        "D1/D9 marriage promise, doshas, and timing in plain language so the couple can understand the relationship pattern.",
        styles["ARBody"],
    ))
    verdict_text = _safe_text(verdict)
    chip = _safe_text(_cover_verdict_chip(report_document, premium, score))
    if verdict_text and verdict_text != chip and not (chip and verdict_text.startswith(chip)):
        story.append(_p(verdict_text, styles["ARBody"]))

    boy_chart = _chart_block(report_document, "boy_d1", styles, width=col_width)
    girl_chart = _chart_block(report_document, "girl_d1", styles, width=col_width)
    if boy_chart is not None or girl_chart is not None:
        story.append(Spacer(1, 3 * mm))
        chart_table = Table(
            [[boy_chart or "", girl_chart or ""]],
            colWidths=[col_width, col_width],
        )
        chart_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(chart_table)

    return story


def _render_wealth_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    pair = report_document.get("pair") or {}
    native = pair.get("native") or pair.get("boy") or {}
    score = report_document.get("score_summary") or {}
    premium = report_document.get("premium_report") or {}
    dashas = score.get("current_dashas") or {}
    px = score.get("px_wealth") or {}
    verdict = (
        premium.get("wealth_verdict")
        or page.get("summary")
        or premium.get("headline")
        or "This report studies earning, saving, and growth through classical Vedic wealth layers."
    )
    generated_label = _format_generated_at(report_document.get("generated_at"))

    story: List[Any] = []
    logo = _logo_flowable(14, 14)
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 3 * mm))

    story.append(_p("Wealth Report", styles["ARCoverTitle"]))
    story.append(_p(_safe_text(native.get("name") or "Native"), styles["ARCoverSubtitle"]))
    story.append(_p(f"Generated on {generated_label}", styles["ARCoverSubtitle"]))
    story.append(Spacer(1, 3 * mm))

    col_width = _CONTENT_WIDTH
    story.append(_person_birth_card(native, styles, col_width))
    story.append(Spacer(1, 4 * mm))

    metrics = [
        {"label": "Wealth score", "value": _short_chip(score.get("wealth_score") or score.get("grade") or "See summary", 18)},
        {"label": "Income mode", "value": _short_chip(px.get("mode") or "--", 18)},
        {"label": "Current MD", "value": _short_chip(dashas.get("mahadasha") or "--", 18)},
        {"label": "Current AD", "value": _short_chip(dashas.get("antardasha") or "--", 18)},
    ]
    story.append(_metric_row(metrics, styles))
    story.append(Spacer(1, 4 * mm))

    story.append(_p("How to read this report", styles["ARSectionSubtitle"]))
    story.append(_p(
        "Start with the foundation and yogas, then D2/D10 manifestation, then the 12-month dasha plan. "
        "Numbers support the reading — the chapters explain how money tends to arrive, stick, or leak.",
        styles["ARBody"],
    ))
    if _safe_text(verdict):
        story.append(_p(_safe_text(verdict), styles["ARBody"]))

    native_chart = _chart_block(report_document, "native_d1", styles, width=_CONTENT_WIDTH)
    if native_chart is not None:
        story.append(Spacer(1, 3 * mm))
        story.append(native_chart)

    return story


def _render_janam_kundli_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    """Single-page opening: branding → metrics → birth line → panchang | D1."""
    from .assembly.janam_kundli_i18n import COVER_COPY, cover_copy, is_hindi
    from .assembly.janam_kundli_labels import label_planet, label_sign
    from .branding import branding_contact_line, has_custom_branding, normalize_report_branding

    pair = report_document.get("pair") or {}
    native = pair.get("native") or pair.get("boy") or {}
    score = report_document.get("score_summary") or {}
    dashas = score.get("current_dashas") or {}
    language = report_document.get("language") or "english"
    copy = cover_copy(language)
    generated_label = _format_generated_at(report_document.get("generated_at"))
    lang_chip = copy["lang_label_hindi"] if is_hindi(language) else copy["lang_label_english"]
    asc_chip = label_sign(score.get("grade") or score.get("ascendant_sign"), language) or "--"
    md_chip = label_planet(dashas.get("mahadasha"), language) or "--"
    ad_chip = label_planet(dashas.get("antardasha"), language) or "--"

    branding = normalize_report_branding(report_document.get("branding") or {})
    custom = has_custom_branding(branding)
    # Under English practice branding, keep cover chrome in English.
    cover_chrome = COVER_COPY["en"] if custom else copy

    # Tight styles — default ARCoverSubtitle spaceAfter=10 overflows custom branding covers.
    brand_title = ParagraphStyle(
        "ARJanamBrandTitle",
        parent=styles["ARCoverTitle"],
        fontSize=18 if custom else 20,
        leading=21 if custom else 24,
        spaceAfter=1,
        spaceBefore=0,
    )
    brand_line = ParagraphStyle(
        "ARJanamBrandLine",
        parent=styles["ARCoverSubtitle"],
        fontSize=8,
        leading=10,
        spaceAfter=1,
        spaceBefore=0,
    )
    meta_line = ParagraphStyle(
        "ARJanamMetaLine",
        parent=styles["ARCoverSubtitle"],
        fontSize=9,
        leading=11,
        spaceAfter=1,
        spaceBefore=0,
    )
    section_label = ParagraphStyle(
        "ARJanamCoverSection",
        parent=styles["ARSectionSubtitle"],
        fontSize=9,
        leading=11,
        spaceAfter=2,
        spaceBefore=0,
    )

    story: List[Any] = []
    # Always show AstroRoshni mark (including under custom practice branding).
    logo = _logo_flowable(10, 10)
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 1.5 * mm))

    if custom:
        story.append(_p(_safe_text(branding.get("business_name")), brand_title))
        if branding.get("tagline"):
            story.append(_p(_safe_text(branding.get("tagline")), brand_line))
        contact = branding_contact_line(branding)
        if contact:
            story.append(_p(contact, brand_line))
        if branding.get("address"):
            story.append(_p(_safe_text(branding.get("address")), brand_line))
    else:
        story.append(_p(copy["report_title"], brand_title))

    native_name = _safe_text(native.get("name") or copy["native_fallback"])
    meta_bits = [
        cover_chrome["report_title"] if custom else native_name,
        native_name if custom else None,
        cover_chrome["generated_on"].format(date=generated_label),
    ]
    if custom:
        meta_bits.append("Prepared with AstroRoshni")
    story.append(_p(" · ".join(bit for bit in meta_bits if bit), meta_line))
    story.append(Spacer(1, 1.5 * mm))

    # Metrics sit directly under branding so the main band can be panchang | D1.
    metrics = [
        {"label": copy["ascendant"], "value": _short_chip(asc_chip, 18)},
        {"label": copy["language"], "value": _short_chip(lang_chip, 18)},
        {"label": copy["current_md"], "value": _short_chip(md_chip, 18)},
        {"label": copy["current_ad"], "value": _short_chip(ad_chip, 18)},
    ]
    story.append(_metric_row(metrics, styles))
    story.append(Spacer(1, 1.5 * mm))

    # Compact birth line (date · time · place) above the two-column band.
    birth_bits = [
        _safe_text(native.get("date")),
        _safe_text(native.get("time")),
        _safe_text(native.get("place")),
    ]
    birth_line = " · ".join(bit for bit in birth_bits if bit)
    if birth_line:
        birth_label = "जन्म विवरण" if is_hindi(language) else "Birth details"
        story.append(_p(f"{birth_label}: {birth_line}", section_label))
        story.append(Spacer(1, 1 * mm))

    gutter = _TABLE_GUTTER
    # ~40% panchang | ~60% D1 chart
    pan_w = _CONTENT_WIDTH * 0.40
    chart_w = _CONTENT_WIDTH - pan_w - gutter

    panchang_flow: Any = Spacer(1, 1)
    cover_tables = page.get("tables") or []
    if cover_tables:
        pan = cover_tables[0]
        pan_rows = pan.get("rows") or []
        pan_headers = pan.get("headers") or []
        if pan_rows:
            render_rows: List[Any] = list(pan_rows)
            if pan_headers and isinstance(pan_rows[0], (list, tuple)):
                render_rows = [list(pan_headers)] + [list(r) for r in pan_rows]
            panchang_inner = [
                [_p(pan.get("title") or "Panchang", section_label)],
                [_table_from_rows(render_rows, styles, width=pan_w, compact=True)],
            ]
            panchang_flow = Table(panchang_inner, colWidths=[pan_w])
            panchang_flow.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))

    chart_flow: Any = Spacer(1, 1)
    native_chart = _chart_block(
        report_document, "native_d1", styles, width=chart_w, compact=True
    )
    if native_chart is not None:
        chart_flow = native_chart

    main_row = Table([[panchang_flow, chart_flow]], colWidths=[pan_w, chart_w], hAlign="LEFT")
    main_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), gutter),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))
    story.append(main_row)

    # Optional planet overview only (keeps cover to one page).
    for tbl in list(cover_tables[1:] if cover_tables else []):
        title = str(tbl.get("title") or "")
        if "ग्रह" not in title and "planet" not in title.lower():
            continue
        headers = tbl.get("headers") or []
        rows = tbl.get("rows") or []
        if not rows:
            continue
        render_rows = [list(headers)] + [list(r) for r in rows] if headers else list(rows)
        story.append(Spacer(1, 2 * mm))
        story.append(_p(title, section_label))
        story.append(_table_from_rows(render_rows, styles, compact=True))
        break

    return story


def _render_health_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    pair = report_document.get("pair") or {}
    native = pair.get("native") or pair.get("boy") or {}
    score = report_document.get("score_summary") or {}
    premium = report_document.get("premium_report") or {}
    dashas = score.get("current_dashas") or {}
    verdict = (
        premium.get("health_verdict")
        or score.get("verdict")
        or page.get("summary")
        or premium.get("headline")
        or "This report studies vitality, constitution, and wellness timing through classical Vedic health layers."
    )
    disclaimer = _safe_text(
        score.get("medical_disclaimer")
        or (
            "This report is Vedic astrological wellness guidance only. It is not a medical diagnosis, "
            "prescription, or substitute for professional healthcare."
        )
    )
    generated_label = _format_generated_at(report_document.get("generated_at"))

    story: List[Any] = []
    logo = _logo_flowable(14, 14)
    if logo is not None:
        story.append(logo)
        story.append(Spacer(1, 3 * mm))

    story.append(_p("Health Report", styles["ARCoverTitle"]))
    story.append(_p(_safe_text(native.get("name") or "Native"), styles["ARCoverSubtitle"]))
    story.append(_p(f"Generated on {generated_label}", styles["ARCoverSubtitle"]))
    story.append(Spacer(1, 3 * mm))

    col_width = _CONTENT_WIDTH
    story.append(_person_birth_card(native, styles, col_width))
    story.append(Spacer(1, 4 * mm))

    metrics = [
        {"label": "Health score", "value": _short_chip(score.get("health_score") or score.get("grade") or "See summary", 18)},
        {"label": "Constitution", "value": _short_chip(score.get("constitution_type") or "--", 18)},
        {"label": "Current MD", "value": _short_chip(dashas.get("mahadasha") or "--", 18)},
        {"label": "Current AD", "value": _short_chip(dashas.get("antardasha") or "--", 18)},
    ]
    story.append(_metric_row(metrics, styles))
    story.append(Spacer(1, 4 * mm))

    story.append(_p("How to read this report", styles["ARSectionSubtitle"]))
    story.append(_p(
        "Start with constitution and vitality, then D1/D9/D30 confirmation, then the 12-month dasha wellness plan. "
        "This is astrological guidance for awareness and habits — not a medical diagnosis.",
        styles["ARBody"],
    ))
    if _safe_text(verdict):
        story.append(_p(_safe_text(verdict), styles["ARBody"]))
    if disclaimer:
        story.append(Spacer(1, 2 * mm))
        story.append(_p(disclaimer, styles["ARBodySmall"]))

    native_chart = _chart_block(report_document, "native_d1", styles, width=_CONTENT_WIDTH)
    if native_chart is not None:
        story.append(Spacer(1, 3 * mm))
        story.append(native_chart)

    return story


def _render_page(page: Dict[str, Any], report_document: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story: List[Any] = []
    title = page.get("title")
    subtitle = page.get("subtitle")
    summary = page.get("summary")

    # Footer already prints the page number — avoid a second "Page N" in the body.
    story.append(_p(title, styles["ARSectionTitle"]))
    if subtitle:
        story.append(_p(subtitle, styles["ARSectionSubtitle"]))
    if summary:
        story.append(_p(summary, styles["ARBody"]))

    notes = page.get("notes") or []
    if notes:
        story.append(Spacer(1, 2 * mm))
        for note in notes:
            story.append(_p(note, styles["ARBody"]))

    bullets = page.get("bullets") or []
    if bullets:
        story.append(Spacer(1, 2 * mm))
        takeaways_label = "मुख्य बिंदु" if is_hindi(_PDF_LANGUAGE.get()) else "Key takeaways"
        story.append(_p(takeaways_label, styles["ARSectionSubtitle"]))
        story.extend(_bullet_list(bullets, styles))

    metrics = page.get("metrics") or []
    if metrics:
        story.append(Spacer(1, 3 * mm))
        story.append(_metric_row(metrics, styles))

    chart_refs = page.get("chart_refs") or []
    if chart_refs:
        chart_table = _chart_table(report_document, chart_refs, styles)
        if chart_table:
            story.append(Spacer(1, 4 * mm))
            story.append(chart_table)

    tables = page.get("tables") or []
    for table_data in tables:
        rows = table_data.get("rows") or []
        if not rows:
            continue
        headers = table_data.get("headers") or []
        # List-rows often carry headers separately; dict-rows already expand keys as header.
        render_rows: List[Any] = list(rows)
        if headers and isinstance(rows[0], (list, tuple)):
            render_rows = [list(headers)] + [list(r) for r in rows]
        story.append(Spacer(1, 3 * mm))
        story.append(_p(table_data.get("title") or "Supporting reference", styles["ARSectionSubtitle"]))
        compact = bool(table_data.get("compact")) or len(headers) >= 12
        story.append(_table_from_rows(render_rows, styles, compact=compact))

    cta = page.get("cta")
    if cta:
        story.append(Spacer(1, 2 * mm))
        story.append(Table([[_p(cta, styles["ARBodySmall"])]], colWidths=[_CONTENT_WIDTH]))

    return story


def _footer_brand_line(language: Any = None, report_type: Any = None, branding: Any = None) -> str:
    """Left footer stays product-branded on every page."""
    return "AstroRoshni - Vedic Kundli"


def _page_footer(canvas, doc):
    fonts = _PDF_FONTS.get()
    language = _PDF_LANGUAGE.get()
    brand = _footer_brand_line()
    page_label = f"पृष्ठ {doc.page}" if is_hindi(language) else f"Page {doc.page}"
    # Brand line is always Latin — never draw it with the Indic shapable face.
    brand_font = fonts.latin_regular or fonts.regular or "Helvetica"
    page_font = fonts.regular or "Helvetica"
    use_shaping = is_hindi(language) or bool(getattr(fonts, "regular", "").startswith("ARLang_"))

    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#f3d3c3"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 14 * mm, A4[0] - doc.rightMargin, 14 * mm)
    canvas.setFillColor(colors.HexColor("#7c2d12"))
    try:
        canvas.setFont(brand_font, 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    canvas.drawString(doc.leftMargin, 8.5 * mm, brand, shaping=0)
    try:
        canvas.setFont(page_font, 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    canvas.drawRightString(A4[0] - doc.rightMargin, 8.5 * mm, page_label, shaping=use_shaping)
    canvas.restoreState()


def render_report_pdf_bytes(report_document: Dict[str, Any]) -> bytes:
    from .branding import normalize_report_branding

    language = report_document.get("language") or "english"
    report_type = report_document.get("report_type") or "report"
    branding = normalize_report_branding(report_document.get("branding") or {})
    fonts = resolve_pdf_fonts(language)
    font_token = _PDF_FONTS.set(fonts)
    lang_token = _PDF_LANGUAGE.set(str(language))
    type_token = _PDF_REPORT_TYPE.set(str(report_type))
    brand_token = _PDF_BRANDING.set(branding)
    try:
        styles = _build_story_styles(fonts)
        buffer = io.BytesIO()
        title = _safe_text((report_document.get("premium_report") or {}).get("headline") or report_document.get("report_type") or "AstroRoshni report")
        author = branding.get("business_name") or "AstroRoshni"
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            title=title,
            author=author,
            subject="Premium Vedic report",
        )

        story: List[Any] = []
        pages = report_document.get("pages") or []
        if pages:
            story.extend(_render_cover(report_document, pages[0], styles))
            for page in pages[1:]:
                if page.get("skip_render"):
                    continue
                story.append(PageBreak())
                story.extend(_render_page(page, report_document, styles))
        else:
            story.append(_p(title, styles["ARCoverTitle"]))
            story.append(_p("Report data was available, but the page list was empty.", styles["ARBody"]))

        doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
        return buffer.getvalue()
    finally:
        _PDF_BRANDING.reset(brand_token)
        _PDF_REPORT_TYPE.reset(type_token)
        _PDF_LANGUAGE.reset(lang_token)
        _PDF_FONTS.reset(font_token)


def build_report_pdf_object_name(report_document: Dict[str, Any]) -> str:
    report_type = _safe_filename(_safe_text(report_document.get("report_type") or "report"))
    report_id = _safe_filename(_safe_text(report_document.get("report_id") or "report"))
    generated_at = report_document.get("generated_at")
    if isinstance(generated_at, str):
        try:
            parsed = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
        except Exception:
            parsed = datetime.now(timezone.utc)
    elif isinstance(generated_at, datetime):
        parsed = generated_at
    else:
        parsed = datetime.now(timezone.utc)
    return f"{_DEFAULT_PDF_FOLDER}/{report_type}/{parsed.strftime('%Y/%m')}/{report_id}.pdf"


def _sign_gs_uri(gs_uri: str, *, expiration_seconds: int = _DEFAULT_PDF_EXPIRY_SECONDS) -> str:
    parsed = parse_gs_uri(gs_uri)
    if not parsed:
        raise ValueError("Invalid gs:// URI")
    bucket_name, object_name = parsed
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expiration_seconds),
        method="GET",
        response_type="application/pdf",
        response_disposition=f'inline; filename="{Path(object_name).name}"',
    )


_GS_URI_RE = re.compile(r"^gs://([^/]+)/(.+)$")


def parse_gs_uri(uri: str) -> Optional[tuple[str, str]]:
    m = _GS_URI_RE.match((uri or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def store_report_pdf(report_document: Dict[str, Any]) -> Dict[str, Any]:
    bucket_name = report_pdf_bucket_name()
    if not bucket_name:
        raise RuntimeError("REPORT_PDF_GCS_BUCKET is not set")

    pdf_bytes = render_report_pdf_bytes(report_document)
    object_name = build_report_pdf_object_name(report_document)
    client = _storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.content_type = "application/pdf"
    blob.cache_control = "private, max-age=0, no-cache, no-store, must-revalidate"
    blob.upload_from_string(pdf_bytes, content_type="application/pdf")

    gs_uri = f"gs://{bucket_name}/{object_name}"
    signed_url = _sign_gs_uri(gs_uri)
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "pdf_gcs_path": gs_uri,
        "pdf_object_name": object_name,
        "pdf_content_type": "application/pdf",
        "pdf_generated_at": generated_at,
        "pdf_url": signed_url,
        "pdf_expires_in_s": _DEFAULT_PDF_EXPIRY_SECONDS,
    }


def sign_report_pdf_url(gs_uri: str, *, expiration_seconds: int = _DEFAULT_PDF_EXPIRY_SECONDS) -> str:
    return _sign_gs_uri(gs_uri, expiration_seconds=expiration_seconds)
