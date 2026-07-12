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

_PLANET_ABBREVIATIONS = {
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
}

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


def _build_story_styles(fonts: PdfFontSet) -> Dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ARCoverTitle",
        fontName=fonts.bold,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#7c2d12"),
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARCoverSubtitle",
        fontName=fonts.regular,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#8b5e34"),
        alignment=TA_CENTER,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionTitle",
        fontName=fonts.bold,
        fontSize=16,
        leading=21,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionSubtitle",
        fontName=fonts.bold,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#ea580c"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ARBody",
        fontName=fonts.regular,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#3f2a56"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARBodySmall",
        fontName=fonts.regular,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#5b4b6b"),
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="ARMetric",
        fontName=fonts.bold,
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#9d174d"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="ARMetricLabel",
        fontName=fonts.regular,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#831843"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="ARHouseCell",
        fontName=fonts.regular,
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#2d1b4e"),
        alignment=TA_LEFT,
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


def _table_from_rows(rows: Sequence[Any], styles: Dict[str, ParagraphStyle], width: float = _CONTENT_WIDTH) -> Table:
    normalized_rows = _normalize_table_rows(rows)
    data = []
    for row in normalized_rows:
        data.append([_p(cell, styles["ARBodySmall"]) for cell in row])
    max_cols = max((len(row) for row in data), default=1)
    col_widths = [width / max_cols] * max_cols
    table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
        ("FONTNAME", (0, 0), (-1, 0), _PDF_FONTS.get().bold),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#f3d3c3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
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


def _chart_house_map(chart_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    houses = chart_data.get("houses") or []
    planets = chart_data.get("planets") or {}
    house_map: Dict[int, Dict[str, Any]] = {}
    for index, house in enumerate(houses, start=1):
        if not isinstance(house, dict):
            continue
        house_num = int(house.get("house_number") or index)
        try:
            sign_index = int(house.get("sign", index - 1) or 0) % 12
        except Exception:
            sign_index = (index - 1) % 12
        planet_names = []
        for planet_name, planet_data in planets.items():
            if not isinstance(planet_data, dict):
                continue
            planet_house = planet_data.get("house")
            if planet_house is not None:
                try:
                    if int(planet_house) == house_num:
                        planet_names.append(_PLANET_ABBREVIATIONS.get(planet_name, planet_name[:2]))
                        continue
                except Exception:
                    pass
            planet_sign = _planet_sign_index(planet_data)
            if planet_sign == sign_index:
                planet_names.append(_PLANET_ABBREVIATIONS.get(planet_name, planet_name[:2]))
        house_map[house_num] = {
            "sign": _ZODIAC_SIGNS[sign_index % 12],
            "planets": planet_names,
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


def _render_chart_grid(chart_data: Optional[Dict[str, Any]], style: str, title: str, styles: Dict[str, ParagraphStyle], width: float = _HALF_CONTENT_WIDTH) -> Table:
    if not chart_data:
        return Table([[ _p("Chart data unavailable", styles["ARBodySmall"]) ]], colWidths=[width])

    house_map = _chart_house_map(chart_data)
    # Always use the same structure for every native in a report.
    draw_style = "south" if style == "south" else "north"
    if draw_style == "south":
        ordered_houses = [
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
        ]
    else:
        ordered_houses = [
            [1, 2, 3, 4],
            [12, None, None, 5],
            [11, None, None, 6],
            [10, 9, 8, 7],
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

    caption = Paragraph(
        f"<b>{_escape_html(title)}</b><br/><font size='8'>Ascendant: {_escape_html(_ZODIAC_SIGNS[int((chart_data.get('ascendant', 0) or 0) / 30) % 12])}</font>",
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
    if draw_style == "north":
        # Keep the hollow center as one merged blank so both charts look identical.
        style_cmds.append(("SPAN", (1, 1), (2, 2)))
        style_cmds.append(("BACKGROUND", (1, 1), (2, 2), colors.HexColor("#fff8f5")))
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


def _chart_block(report_document: Dict[str, Any], ref: str, styles: Dict[str, ParagraphStyle], width: float = _HALF_CONTENT_WIDTH) -> Optional[Table]:
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

    ref_map = {
        "d1_north": (boy_d1, _chart_title(boy_d1, boy_name, "D1 Rashi"), style),
        "d1_south": (girl_d1, _chart_title(girl_d1, girl_name, "D1 Rashi"), style),
        "d9_north": (boy_d9, _chart_title(boy_d9, boy_name, "D9 Navamsa"), style),
        "d9_south": (girl_d9, _chart_title(girl_d9, girl_name, "D9 Navamsa"), style),
        "boy_d1": (boy_d1, _chart_title(boy_d1, boy_name, "D1 Rashi"), style),
        "girl_d1": (girl_d1, _chart_title(girl_d1, girl_name, "D1 Rashi"), style),
        "boy_d9": (boy_d9, _chart_title(boy_d9, boy_name, "D9 Navamsa"), style),
        "girl_d9": (girl_d9, _chart_title(girl_d9, girl_name, "D9 Navamsa"), style),
        "boy_d2": (boy_d2, _chart_title(boy_d2, boy_name, "D2 Hora"), style),
        "girl_d2": (girl_d2, _chart_title(girl_d2, girl_name, "D2 Hora"), style),
        "boy_d7": (boy_d7, _chart_title(boy_d7, boy_name, "D7 Saptamsha"), style),
        "girl_d7": (girl_d7, _chart_title(girl_d7, girl_name, "D7 Saptamsha"), style),
        "native_d1": (boy_d1, _chart_title(boy_d1, native_name, "D1 Rashi"), style),
        "native_d2": (boy_d2, _chart_title(boy_d2, native_name, "D2 Hora"), style),
        "native_d9": (boy_d9, _chart_title(boy_d9, native_name, "D9 Navamsa"), style),
        "native_d10": (native_d10, _chart_title(native_d10, native_name, "D10 Dasamsa"), style),
        "native_d30": (native_d30, _chart_title(native_d30, native_name, "D30 Trimsamsa"), style),
        "boy_d30": (native_d30, _chart_title(native_d30, native_name, "D30 Trimsamsa"), style),
    }
    chart_info = ref_map.get(ref)
    if not chart_info:
        return None
    chart, title, draw_style = chart_info
    if not chart:
        return None
    grid = _render_chart_grid(chart, style=draw_style, title=title, styles=styles, width=width)
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


def _person_birth_card(person: Dict[str, Any], styles: Dict[str, ParagraphStyle], width: float) -> Table:
    name_style = ParagraphStyle(
        "ARCoverPersonName",
        parent=styles["ARSectionTitle"],
        fontSize=13,
        leading=16,
        spaceAfter=2,
    )
    rows = [
        [_p(_safe_text(person.get("name") or "Native"), name_style)],
        [_p("Birth details", styles["ARSectionSubtitle"])],
        [_p(_safe_text(person.get("date")) or "—", styles["ARBodySmall"])],
        [_p(_safe_text(person.get("time")) or "—", styles["ARBodySmall"])],
        [_p(_safe_text(person.get("place")) or "—", styles["ARBodySmall"])],
    ]
    column = Table(rows, colWidths=[max(40 * mm, width - 6 * mm)])
    column.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return column


def _render_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    report_type = str(report_document.get("report_type") or "").lower()
    if report_type == "wealth":
        return _render_wealth_cover(report_document, page, styles)
    if report_type == "health":
        return _render_health_cover(report_document, page, styles)

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
    logo_bytes = _load_logo_bytes()
    if logo_bytes:
        story.append(Image(io.BytesIO(logo_bytes), width=14 * mm, height=14 * mm))
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
    logo_bytes = _load_logo_bytes()
    if logo_bytes:
        story.append(Image(io.BytesIO(logo_bytes), width=14 * mm, height=14 * mm))
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
    logo_bytes = _load_logo_bytes()
    if logo_bytes:
        story.append(Image(io.BytesIO(logo_bytes), width=14 * mm, height=14 * mm))
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
        story.append(_p("Key takeaways", styles["ARSectionSubtitle"]))
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
        if rows:
            story.append(Spacer(1, 3 * mm))
            story.append(_p(table_data.get("title") or "Supporting reference", styles["ARSectionSubtitle"]))
            story.append(_table_from_rows(rows, styles))

    cta = page.get("cta")
    if cta:
        story.append(Spacer(1, 2 * mm))
        story.append(Table([[_p(cta, styles["ARBodySmall"])]], colWidths=[_CONTENT_WIDTH]))

    return story


def _page_footer(canvas, doc):
    fonts = _PDF_FONTS.get()
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#f3d3c3"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 14 * mm, A4[0] - doc.rightMargin, 14 * mm)
    try:
        canvas.setFont(fonts.regular, 8)
    except Exception:
        canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#7c2d12"))
    canvas.drawString(doc.leftMargin, 8.5 * mm, "AstroRoshni AI + Vedic Calculators")
    canvas.drawRightString(A4[0] - doc.rightMargin, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def render_report_pdf_bytes(report_document: Dict[str, Any]) -> bytes:
    fonts = resolve_pdf_fonts(report_document.get("language"))
    token = _PDF_FONTS.set(fonts)
    try:
        styles = _build_story_styles(fonts)
        buffer = io.BytesIO()
        title = _safe_text((report_document.get("premium_report") or {}).get("headline") or report_document.get("report_type") or "AstroRoshni report")
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=16 * mm,
            rightMargin=16 * mm,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            title=title,
            author="AstroRoshni AI",
            subject="Premium Vedic report",
        )

        story: List[Any] = []
        pages = report_document.get("pages") or []
        if pages:
            story.extend(_render_cover(report_document, pages[0], styles))
            for page in pages[1:]:
                story.append(PageBreak())
                story.extend(_render_page(page, report_document, styles))
        else:
            story.append(_p(title, styles["ARCoverTitle"]))
            story.append(_p("Report data was available, but the page list was empty.", styles["ARBody"]))

        doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
        return buffer.getvalue()
    finally:
        _PDF_FONTS.reset(token)


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
