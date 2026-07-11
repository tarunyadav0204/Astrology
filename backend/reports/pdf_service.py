from __future__ import annotations

import io
import os
import re
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

_CLIENT = None

_DEFAULT_PDF_BUCKET_ENV_KEYS = (
    "REPORT_PDF_GCS_BUCKET",
    "REPORTS_PDF_GCS_BUCKET",
    "REPORT_PDF_BUCKET",
)

_DEFAULT_PDF_EXPIRY_SECONDS = int(os.getenv("REPORT_PDF_SIGNED_URL_TTL_S", "86400") or "86400")
_DEFAULT_PDF_FOLDER = "reports"

_ROOT_DIR = Path(__file__).resolve().parents[2]
_DEFAULT_LOGO_PATH = _ROOT_DIR / "astroroshni_mobile" / "assets" / "logo.png"

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


def _build_story_styles() -> Dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ARCoverTitle",
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#7c2d12"),
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARCoverSubtitle",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#8b5e34"),
        alignment=TA_CENTER,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=colors.HexColor("#7c2d12"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARSectionSubtitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#ea580c"),
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ARBody",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#3f2a56"),
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ARBodySmall",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#5b4b6b"),
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="ARMetric",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#9d174d"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="ARMetricLabel",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#831843"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="ARHouseCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#2d1b4e"),
        alignment=TA_LEFT,
    ))
    return styles


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_escape_html(_clean_markup(text)), style)


def _metric_card(label: Any, value: Any, styles: Dict[str, ParagraphStyle]) -> Table:
    return Table(
        [[_p(value, styles["ARMetric"]), _p(label, styles["ARMetricLabel"])]],
        colWidths=[45 * mm],
        rowHeights=[18 * mm],
    )


def _metric_row(metrics: Sequence[Dict[str, Any]], styles: Dict[str, ParagraphStyle]) -> Table:
    cards: List[Any] = []
    for metric in metrics[:4]:
        cards.append([
            _metric_card(metric.get("label"), metric.get("value"), styles),
        ])
    if not cards:
        return Table([[]])
    row = [item[0] for item in cards]
    table = Table([row], colWidths=[46 * mm] * len(row))
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
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
        out.append(Paragraph(f"• {_escape_html(txt)}", styles["ARBody"]))
    return out


def _table_from_rows(rows: Sequence[Sequence[Any]], styles: Dict[str, ParagraphStyle]) -> Table:
    data = []
    for row in rows:
        data.append([_p(cell, styles["ARBodySmall"]) for cell in row])
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#7c2d12")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
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


def _chart_house_map(chart_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    houses = chart_data.get("houses") or []
    planets = chart_data.get("planets") or {}
    house_map: Dict[int, Dict[str, Any]] = {}
    for index, house in enumerate(houses, start=1):
        sign_index = int(house.get("sign", index - 1) or 0)
        planet_names = []
        for planet_name, planet_data in planets.items():
            planet_sign = planet_data.get("sign")
            if planet_sign == sign_index:
                planet_names.append(_PLANET_ABBREVIATIONS.get(planet_name, planet_name[:2]))
        house_map[index] = {
            "sign": _ZODIAC_SIGNS[sign_index % 12],
            "planets": planet_names,
        }
    return house_map


def _chart_cell(house_num: int, house_info: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> Table:
    planet_text = ", ".join(house_info.get("planets") or []) or "—"
    rows = [
        [_p(f"House {house_num}", styles["ARBodySmall"])],
        [_p(house_info.get("sign") or "", styles["ARBodySmall"])],
        [_p(planet_text, styles["ARHouseCell"])],
    ]
    cell = Table(rows, colWidths=[31 * mm])
    cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#f3d3c3")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return cell


def _render_chart_grid(chart_data: Optional[Dict[str, Any]], style: str, title: str, styles: Dict[str, ParagraphStyle]) -> Table:
    if not chart_data:
        return Table([[ _p("Chart data unavailable", styles["ARBodySmall"]) ]], colWidths=[90 * mm])

    house_map = _chart_house_map(chart_data)
    if style == "south":
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

    grid_rows: List[List[Any]] = []
    for row in ordered_houses:
        rendered_row = []
        for house_num in row:
            if not house_num:
                rendered_row.append("")
                continue
            rendered_row.append(_chart_cell(house_num, house_map.get(house_num, {}), styles))
        grid_rows.append(rendered_row)

    caption = Paragraph(
        f"<b>{_escape_html(title)}</b><br/><font size='8'>Ascendant: {_escape_html(_ZODIAC_SIGNS[int((chart_data.get('ascendant', 0) or 0) / 30) % 12])}</font>",
        styles["ARBodySmall"],
    )
    table = Table([[caption], [Table(grid_rows, colWidths=[22 * mm, 22 * mm, 22 * mm, 22 * mm])]], colWidths=[94 * mm])
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


def _chart_block(report_document: Dict[str, Any], ref: str, styles: Dict[str, ParagraphStyle]) -> Table:
    chart_data = report_document.get("chart_data") or {}
    report_type = _safe_text(report_document.get("report_type") or "report").title()

    ref_map = {
        "d1_north": (chart_data.get("boy"), "D1 North", "north"),
        "d1_south": (chart_data.get("girl"), "D1 South", "south"),
        "d9_north": (chart_data.get("boy_d9"), "D9 North", "north"),
        "d9_south": (chart_data.get("girl_d9"), "D9 South", "south"),
    }
    chart_info = ref_map.get(ref)
    if chart_info:
        chart, title, style = chart_info
        grid = _render_chart_grid(chart, style=style, title=title, styles=styles)
        return Table([[grid]], colWidths=[96 * mm])

    label = {
        "radar_chart": "Compatibility radar",
        "d1_cross_house_table": "House overlay table",
        "dasha_timeline": "Timing timeline",
        "dasha_overlap": "Joint windows",
        "d60_summary": "Karmic summary",
    }.get(ref, ref)
    return Table([[
        Paragraph(
            f"<b>{_escape_html(label)}</b><br/><font size='8'>Included in {report_type} analysis</font>",
            styles["ARBodySmall"],
        )
    ]], colWidths=[96 * mm])


def _render_cover(report_document: Dict[str, Any], page: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    chart_data = report_document.get("chart_data") or {}
    pair = report_document.get("pair") or {}
    boy = pair.get("boy") or {}
    girl = pair.get("girl") or {}
    score = report_document.get("score_summary") or {}
    premium = report_document.get("premium_report") or {}
    verdict = premium.get("compatibility_verdict") or page.get("summary") or "Relationship report ready."
    generated_at = report_document.get("generated_at")
    generated_label = _safe_text(generated_at)
    if not generated_label and report_document.get("generated_at"):
        generated_label = _safe_text(report_document.get("generated_at"))

    story: List[Any] = []
    logo_bytes = _load_logo_bytes()
    if logo_bytes:
        story.append(Image(io.BytesIO(logo_bytes), width=14 * mm, height=14 * mm))
        story.append(Spacer(1, 3 * mm))

    story.append(_p("Partnership Compatibility Report", styles["ARCoverTitle"]))
    story.append(_p(f"{_safe_text(boy.get('name') or 'Person A')} vs {_safe_text(girl.get('name') or 'Person B')}", styles["ARCoverSubtitle"]))
    story.append(_p(f"Generated on {_safe_text(generated_label or datetime.now(timezone.utc).strftime('%d %b %Y, %I:%M %p UTC'))}", styles["ARCoverSubtitle"]))
    story.append(Spacer(1, 4 * mm))

    pair_rows = [
        [
            Table([[
                _p(_safe_text(boy.get("name") or "Person A"), styles["ARSectionTitle"]),
                _p("Birth details", styles["ARSectionSubtitle"]),
                _p(" • ".join([_safe_text(boy.get("date")), _safe_text(boy.get("time")), _safe_text(boy.get("place"))]).strip(" •"), styles["ARBodySmall"]),
            ]], colWidths=[86 * mm]),
            Table([[
                _p(_safe_text(girl.get("name") or "Person B"), styles["ARSectionTitle"]),
                _p("Birth details", styles["ARSectionSubtitle"]),
                _p(" • ".join([_safe_text(girl.get("date")), _safe_text(girl.get("time")), _safe_text(girl.get("place"))]).strip(" •"), styles["ARBodySmall"]),
            ]], colWidths=[86 * mm]),
        ]
    ]
    pair_table = Table(pair_rows, colWidths=[88 * mm, 88 * mm])
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
    story.append(Spacer(1, 5 * mm))

    metrics = [
        {"label": "Overall score", "value": f"{round(float((score.get('percentage') or 0)))} / 100"},
        {"label": "Verdict", "value": _safe_text(report_document.get("premium_report", {}).get("headline") or premium.get("compatibility_verdict") or "Ready to open")},
        {"label": "Guna Milan", "value": f"{_safe_text((report_document.get('score_summary') or {}).get('guna_milan', {}).get('effective_total_score') or '--')}/36"},
        {"label": "Report type", "value": _safe_text(report_document.get("report_type") or "partnership").title()},
    ]
    story.append(_metric_row(metrics, styles))
    story.append(Spacer(1, 5 * mm))

    story.append(_p(verdict, styles["ARBody"]))

    if chart_data.get("boy") or chart_data.get("girl"):
        chart_row = Table([
            [
                _chart_block(report_document, "d1_north", styles),
                _chart_block(report_document, "d1_south", styles),
            ]
        ], colWidths=[96 * mm, 96 * mm])
        chart_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(Spacer(1, 4 * mm))
        story.append(chart_row)

    return story


def _render_page(page: Dict[str, Any], report_document: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> List[Any]:
    story: List[Any] = []
    page_num = page.get("page_number")
    title = page.get("title")
    subtitle = page.get("subtitle")
    summary = page.get("summary")

    story.append(_p(f"Page {page_num}", styles["ARSectionSubtitle"]))
    story.append(_p(title, styles["ARSectionTitle"]))
    if subtitle:
        story.append(_p(subtitle, styles["ARSectionSubtitle"]))
    if summary:
        story.append(_p(summary, styles["ARBody"]))

    metrics = page.get("metrics") or []
    if metrics:
        metric_cards = []
        for metric in metrics[:4]:
            metric_cards.append(_metric_card(metric.get("label"), metric.get("value"), styles))
        metric_row = Table([metric_cards], colWidths=[46 * mm] * len(metric_cards))
        metric_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(Spacer(1, 2 * mm))
        story.append(metric_row)

    chart_refs = page.get("chart_refs") or []
    if chart_refs:
        chart_cards = []
        for ref in chart_refs:
            chart_cards.append(_chart_block(report_document, ref, styles))
        if chart_cards:
            chart_table = Table([chart_cards], colWidths=[95 * mm] * len(chart_cards))
            chart_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story.append(Spacer(1, 4 * mm))
            story.append(chart_table)

    bullets = page.get("bullets") or []
    if bullets:
        story.append(Spacer(1, 2 * mm))
        story.extend(_bullet_list(bullets, styles))

    tables = page.get("tables") or []
    for table_data in tables:
        rows = table_data.get("rows") or []
        if rows:
            story.append(Spacer(1, 3 * mm))
            story.append(_p(table_data.get("title") or "Table", styles["ARSectionSubtitle"]))
            story.append(_table_from_rows(rows, styles))

    notes = page.get("notes") or []
    if notes:
        story.append(Spacer(1, 2 * mm))
        for note in notes:
            story.append(_p(note, styles["ARBodySmall"]))

    cta = page.get("cta")
    if cta:
        story.append(Spacer(1, 2 * mm))
        story.append(Table([[_p(cta, styles["ARBodySmall"])]], colWidths=[180 * mm]))

    return story


def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#f3d3c3"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 14 * mm, A4[0] - doc.rightMargin, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#7c2d12"))
    canvas.drawString(doc.leftMargin, 8.5 * mm, "AstroRoshni AI + Vedic Calculators")
    canvas.drawRightString(A4[0] - doc.rightMargin, 8.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def render_report_pdf_bytes(report_document: Dict[str, Any]) -> bytes:
    styles = _build_story_styles()
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
