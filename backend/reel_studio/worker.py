"""Premium, chart-grounded Reel Studio renderer.

Each output intercuts an original AI astrologer speaking to camera, a
deterministic kundali, a deterministic dasha timeline, and generated
live-action b-roll. It never substitutes generic text cards for chart data.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import textwrap
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import imageio_ffmpeg
from google.cloud import texttospeech
from PIL import Image, ImageDraw, ImageFont

from db import execute, get_conn
from partner_profile.image_provider import OpenAIPartnerPortraitProvider
from tts.routes import _build_voice_and_config, _get_google_credentials, _segment_text_to_plain
from utils.admin_settings import get_podcast_tts_voices
from reel_studio.text import plain_text

logger = logging.getLogger(__name__)

ROOT = Path(os.getenv("REEL_LOCAL_OUTPUT_DIR", "storage/reels"))
VIDEO_MODEL = "gemini-omni-1.1-flash"
# Temporary cost-control mode.  Keep the Omni call below intact for later, but
# do not invoke it unless this is explicitly enabled in deployment.
OMNI_VIDEO_ENABLED = os.getenv("REEL_ENABLE_OMNI_VIDEO", "false").strip().lower() in {"1", "true", "yes", "on"}
WIDTH, HEIGHT = 1080, 1920
REEL_IMAGE_SIZE = "1024x1824"  # exact 9:16; both dimensions are valid GPT Image 2 multiples of 16
PLANET_ABBR = {"Jupiter": "Ju", "Mercury": "Me", "Saturn": "Sa", "Venus": "Ve", "Mars": "Ma", "Moon": "Mo", "Sun": "Su", "Rahu": "Ra", "Ketu": "Ke"}
SIGN_NAMES = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
# Standard North Indian kundali geometry: the four cardinal houses are
# diamonds around the chart's central junction; the other eight are perimeter
# wedges. This is deliberately not the generic "one central diamond + X" grid.
NORTH_INDIAN_HOUSE_SLOTS = (
    {"house": 1, "slot": "top central diamond"},
    {"house": 2, "slot": "upper-left top wedge"},
    {"house": 3, "slot": "upper-left side wedge"},
    {"house": 4, "slot": "left central diamond"},
    {"house": 5, "slot": "lower-left side wedge"},
    {"house": 6, "slot": "lower-left bottom wedge"},
    {"house": 7, "slot": "bottom central diamond"},
    {"house": 8, "slot": "lower-right bottom wedge"},
    {"house": 9, "slot": "lower-right side wedge"},
    {"house": 10, "slot": "right central diamond"},
    {"house": 11, "slot": "upper-right side wedge"},
    {"house": 12, "slot": "upper-right top wedge"},
)
USD_TO_INR = float(os.getenv("REEL_USD_TO_INR", "95"))
VIDEO_TOKEN_COST_INR = 17.50 * USD_TO_INR / 1_000_000
OMNI_INPUT_TOKEN_COST_INR = 1.50 * USD_TO_INR / 1_000_000
OMNI_TEXT_TOKEN_COST_INR = 9.00 * USD_TO_INR / 1_000_000
# GPT Image 2 output cost scales with output-image tokens. 1024x1824 is 19%
# larger than the published 1024x1536 reference price.
GPT_IMAGE_LOW_COST_INR = 0.005 * 1.1875 * USD_TO_INR
CHIRP_TTS_CHAR_COST_INR = 30.0 * USD_TO_INR / 1_000_000


def _update(job_id: str, status: str, *, output_url: str | None = None, error: str | None = None) -> None:
    with get_conn() as conn:
        execute(conn, """UPDATE reel_render_jobs SET status=%s, output_url=COALESCE(%s, output_url),
            error_message=%s,
            task_claim_id=CASE WHEN %s IN ('completed', 'failed') THEN NULL ELSE task_claim_id END,
            task_claimed_until=CASE WHEN %s IN ('completed', 'failed') THEN NULL ELSE task_claimed_until END,
            updated_at=CURRENT_TIMESTAMP WHERE id=%s""", (status, output_url, error, status, status, job_id))
        conn.commit()


def _fail_reel(job_id: str, error: str) -> None:
    from reel_studio.billing import refund_reel
    try:
        refund_reel(job_id)
    except Exception as exc:
        error += f" Credit refund could not be completed: {type(exc).__name__}: {exc}"
    _update(job_id, "failed", error=error[:1000])


def _record(user_id: int, run_id: str, stage: str, provider: str, units: float, metadata: dict, unit_cost_inr: float = 0.0) -> None:
    with get_conn() as conn:
        execute(conn, """INSERT INTO reel_generation_costs
          (user_id, run_id, stage, provider, units, unit_cost_inr, total_cost_inr, metadata_json)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (user_id, run_id, stage, provider, units, unit_cost_inr, units * unit_cost_inr, json.dumps(metadata)))
        conn.commit()


def _font(size: int, bold: bool = False):
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(candidate).is_file(): return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _display_font(size: int, bold: bool = False):
    """A restrained editorial serif for factual cards; never generated text."""
    for candidate in (
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ):
        if Path(candidate).is_file(): return ImageFont.truetype(candidate, size)
    return _font(size, bold)


def _base_canvas(*, transparent: bool = False) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    # The data cards use the same warm editorial language as the product, not
    # generic "AI astrology" gradients.
    image = Image.new("RGBA" if transparent else "RGB", (WIDTH, HEIGHT), (0, 0, 0, 0) if transparent else "#31040f")
    draw = ImageDraw.Draw(image)
    if transparent:
        return image, draw
    draw.ellipse((-620, -480, 800, 850), fill="#520c20")
    draw.ellipse((400, -240, 1420, 740), fill="#66172b")
    draw.ellipse((-380, 1260, 650, 2270), fill="#1d0610")
    draw.ellipse((610, 1160, 1460, 2070), fill="#672337")
    for x, y, radius in ((88, 370, 16), (944, 275, 10), (101, 1220, 12), (954, 1540, 18), (875, 92, 8)):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#d9a44d")
    draw.text((74, 66), "ASTROROSHNI", fill="#e9bd6a", font=_font(25, True))
    return image, draw


def _phone_shell(draw: ImageDraw.ImageDraw, title: str, selected_tab: str) -> tuple[int, int, int, int]:
    """Product-frame presentation for deterministic, privacy-safe content."""
    outer = (64, 350, 1016, 1775)
    screen = (88, 386, 992, 1740)
    draw.rounded_rectangle(outer, radius=96, fill="#09070a", outline="#d8ad62", width=7)
    draw.rounded_rectangle((78, 366, 1002, 1759), radius=82, outline="#61401e", width=3)
    draw.rounded_rectangle(screen, radius=66, fill="#fbf4e8")
    draw.rounded_rectangle((88, 386, 992, 532), radius=66, fill="#550b22")
    draw.rectangle((88, 470, 992, 532), fill="#550b22")
    draw.rounded_rectangle((430, 402, 650, 436), radius=18, fill="#09070a")
    draw.text((128, 407), "9:41", fill="#fff0d2", font=_font(17, True))
    draw.text((946, 407), "5G", anchor="ra", fill="#fff0d2", font=_font(17, True))
    draw.text((136, 416), "‹", fill="#f7e2b7", font=_display_font(46))
    draw.ellipse((875, 401, 923, 449), outline="#b78348", width=2)
    draw.line((890, 430, 910, 410), fill="#f7e2b7", width=3)
    draw.polygon([(910, 410), (899, 412), (908, 421)], fill="#f7e2b7")
    draw.text((540, 420), title, anchor="mm", fill="#fff0d2", font=_display_font(31, True))
    tabs = ("Chart", "Dasha", "SAV")
    for i, tab in enumerate(tabs):
        x1 = 120 + i * 285
        selected = tab == selected_tab
        if selected:
            draw.rounded_rectangle((x1, 480, x1 + 238, 524), radius=20, fill="#f5d98f")
        draw.text((x1 + 119, 502), tab, anchor="mm", fill="#580b22" if selected else "#f6e7ca", font=_font(20, True))
    return screen


def _wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int, size: int = 42) -> None:
    y = xy[1]
    for line in textwrap.wrap(text, width=width):
        draw.text((xy[0], y), line, fill="#fff9ef", font=_font(size))
        y += int(size * 1.32)


def _chart_visual(path: Path, snapshot: dict, *, focus_nodes: list[str] | None = None, draw_edges: list[str] | None = None, callout_text: str | None = None, transparent: bool = False) -> None:
    image, draw = _base_canvas(transparent=transparent)
    draw.text((540, 150), "Chart Clues", anchor="mm", fill="#ffe4a2", font=_display_font(68, True))
    draw.text((540, 224), "from your verified birth chart", anchor="mm", fill="#ebc985", font=_display_font(28))
    _phone_shell(draw, "D1 Lagna", "Chart")
    draw.text((140, 572), "VERIFIED NATAL MAP", fill="#6e1630", font=_font(18, True))
    draw.text((140, 610), "Highlighted links explain this part of your reading", fill="#514541", font=_font(20))
    left, top, size = 135, 680, 810
    # Same twelve-house North Indian geometry as the app chart and PDF report.
    # The previous renderer incorrectly folded twelve houses into nine cells.
    draw.rectangle((left, top, left + size, top + size), outline="#bd8629", width=5)
    diamond = [(left + size // 2, top), (left + size, top + size // 2), (left + size // 2, top + size), (left, top + size // 2)]
    draw.line(diamond + [diamond[0]], fill="#bd8629", width=5)
    draw.line((left, top, left + size, top + size), fill="#d9bea1", width=3)
    draw.line((left + size, top, left, top + size), fill="#d9bea1", width=3)
    centers_svg = {1: (200, 100), 2: (100, 50), 3: (50, 100), 4: (100, 200), 5: (50, 300), 6: (100, 350), 7: (200, 300), 8: (300, 350), 9: (350, 300), 10: (300, 200), 11: (350, 100), 12: (300, 50)}
    rashi_offsets = {1: (0, -70), 2: (-24, -38), 3: (-32, -5), 4: (50, -4), 5: (22, -18), 6: (-25, 22), 7: (0, 56), 8: (26, 22), 9: (28, -15), 10: (-55, -4), 11: (30, -5), 12: (25, -38)}
    by_house: dict[int, list[str]] = {i: [] for i in range(1, 13)}
    planet_houses: dict[str, int] = {}
    for placement in snapshot.get("placements") or []:
        planet = str(placement.get("planet") or "")
        house = int(placement.get("house") or 0)
        degree = placement.get("degree_in_sign")
        degree_label = f" {float(degree):.1f}°" if isinstance(degree, (int, float)) else ""
        by_house.get(house, []).append(f"{PLANET_ABBR.get(planet, '?')}{degree_label}"); planet_houses[planet.lower()] = house
    graph = snapshot.get("visual_graph") or {}
    graph_nodes = {str(row.get("id")): row for row in graph.get("nodes", [])}
    graph_edges = {str(row.get("id")): row for row in graph.get("edges", [])}
    focus_nodes = focus_nodes or []
    focus_houses = set()
    for node_id in focus_nodes:
        node = graph_nodes.get(node_id) or {}
        if node.get("house"): focus_houses.add(int(node["house"]))
        elif ".house." in node_id:
            try: focus_houses.add(int(node_id.rsplit(".", 1)[1]))
            except ValueError: pass
    def center_for(node_id: str):
        node = graph_nodes.get(node_id) or {}
        house = node.get("house")
        if not house and ".house." in node_id:
            try: house = int(node_id.rsplit(".", 1)[1])
            except ValueError: house = None
        if not house and ".planet." in node_id:
            house = planet_houses.get(node_id.rsplit(".", 1)[1])
        if not house or int(house) not in centers_svg: return None
        sx, sy = centers_svg[int(house)]
        return (left + (sx * size / 400), top + (sy * size / 400))
    # Draw only verified selected relationships before labels, one at a time.
    for edge_id in (draw_edges or [])[:3]:
        edge = graph_edges.get(edge_id) or {}; start, end = center_for(str(edge.get("from"))), center_for(str(edge.get("to")))
        if not start or not end or start == end: continue
        draw.line((start, end), fill="#faad4d", width=7)
        dx, dy = end[0] - start[0], end[1] - start[1]; length = max((dx * dx + dy * dy) ** .5, 1)
        ux, uy = dx / length, dy / length; px, py = -uy, ux
        tip = (end[0] - ux * 15, end[1] - uy * 15)
        draw.polygon([tip, (tip[0] - ux * 28 + px * 14, tip[1] - uy * 28 + py * 14), (tip[0] - ux * 28 - px * 14, tip[1] - uy * 28 - py * 14)], fill="#faad4d")
        target = graph_nodes.get(str(edge.get("to"))) or {}
        if target.get("house"): focus_houses.add(int(target["house"]))
    asc = int(snapshot.get("ascendant_sign") or 0)
    for house in range(1, 13):
        sx, sy = centers_svg[house]
        x, y = left + (sx * size / 400), top + (sy * size / 400)
        if focus_houses and house not in focus_houses:
            draw.ellipse((x - 72, y - 56, x + 72, y + 56), fill="#eee6dd")
        elif house in focus_houses:
            draw.ellipse((x - 84, y - 67, x + 84, y + 67), outline="#faad4d", width=6)
        ox, oy = rashi_offsets[house]
        draw.text((x + ox, y + oy), str(((asc + house - 1) % 12) + 1), anchor="mm", fill="#704625", font=_font(25, True))
        if house == 1:
            draw.text((x + 55, y - 64), "ASC", anchor="mm", fill="#8d1b38", font=_font(18, True))
        planets = by_house[house]
        lines = planets if planets else []
        for index, line in enumerate(lines):
            draw.text((x, y + 10 + index * 31 - (len(lines) - 1) * 15), line, anchor="mm", fill="#211713", font=_font(23 if len(lines) < 3 else 20, True))
    draw.rounded_rectangle((118, 1530, 962, 1690), radius=26, fill="#fffaf1", outline="#bd8629", width=3)
    draw.text((152, 1562), "READING RULE", fill="#8d1b38", font=_font(20, True))
    for line_index, line in enumerate(textwrap.wrap(callout_text or "Every highlighted placement and arrow is resolved from the saved chart.", width=54)[:2]):
        draw.text((152, 1600 + line_index * 31), line, fill="#33251f", font=_font(22))
    image.save(path, "PNG")


def _dasha_visual(path: Path, snapshot: dict, *, callout_text: str | None = None, transparent: bool = False) -> None:
    image, draw = _base_canvas(transparent=transparent)
    draw.text((540, 150), "Dasha Stack", anchor="mm", fill="#ffe4a2", font=_display_font(68, True))
    draw.text((540, 224), "the timing behind the reading", anchor="mm", fill="#ebc985", font=_display_font(28))
    _phone_shell(draw, "Dasha Browser", "Dasha")
    dashas = snapshot.get("current_dashas") or {}
    levels = (("mahadasha", "MAHA DASHA"), ("antardasha", "ANTAR DASHA"), ("pratyantardasha", "PRATYANTAR DASHA"), ("sookshma", "SOOKSHMA DASHA"), ("prana", "PRANA DASHA"))
    for index, (key, label) in enumerate(levels):
        y = 605 + index * 177; period = dashas.get(key) or {}
        draw.text((142, y), f"0{index + 1}", fill="#8d1b38", font=_font(20, True))
        draw.text((205, y), label, fill="#471421", font=_display_font(25, True))
        draw.rounded_rectangle((142, y + 38, 938, y + 152), radius=20, fill="#fffaf1", outline="#d5b37b", width=2)
        draw.rounded_rectangle((165, y + 52, 505, y + 139), radius=17, fill="#68142d", outline="#e5b855", width=4)
        draw.text((195, y + 72), str(period.get("planet") or "Unavailable"), fill="#fff0d0", font=_display_font(29, True))
        draw.text((195, y + 111), " → ".join(filter(None, (str(period.get("start") or ""), str(period.get("end") or "")))) or "No verified period", fill="#f3dcae", font=_font(14))
        if index < len(levels) - 1:
            draw.line((190, y + 155, 190, y + 170), fill="#bd8629", width=4)
            draw.polygon([(190, y + 174), (181, y + 160), (199, y + 160)], fill="#bd8629")
    draw.rounded_rectangle((140, 1518, 940, 1665), radius=25, fill="#fff9ef", outline="#bd8629", width=3)
    draw.text((175, 1553), "TIMING, NOT CERTAINTY", fill="#8d1b38", font=_font(19, True))
    for line_index, line in enumerate(textwrap.wrap(callout_text or "This is the verified active sequence used in this reading.", width=52)[:2]):
        draw.text((175, 1590 + line_index * 29), line, fill="#33251f", font=_font(22))
    image.save(path, "PNG")


def _ashtakavarga_visual(path: Path, snapshot: dict) -> None:
    image, draw = _base_canvas()
    draw.text((74, 180), "ASHTAKAVARGA", fill="#fff4df", font=_font(58, True))
    draw.text((74, 252), "Sarvashtakavarga strength by house", fill="#e6cbd2", font=_font(27))
    points = ((snapshot.get("ashtakavarga") or {}).get("sav_by_house") or {})
    for house in range(1, 13):
        x = 90 + ((house - 1) % 3) * 310; y = 450 + ((house - 1) // 3) * 210
        value = int(points.get(str(house), 0))
        draw.rounded_rectangle((x, y, x + 260, y + 155), radius=22, fill="#35204c", outline="#e2b86d", width=2)
        draw.text((x + 28, y + 24), f"HOUSE {house}", fill="#f8cb72", font=_font(20, True))
        draw.text((x + 130, y + 84), str(value), anchor="mm", fill="#fff9ef", font=_font(54, True))
    draw.rounded_rectangle((74, 1450, 1006, 1710), radius=28, fill="#1d1231", outline="#8c6c60", width=2)
    draw.text((108, 1495), "HOW TO READ THIS", fill="#f8c96e", font=_font(23, True))
    _wrapped(draw, "These are calculated house-strength points from your saved chart, not AI-generated astrology.", (108, 1540), 42, 34)
    image.save(path, "PNG")


def _brand_logo() -> bytes:
    default = Path(__file__).resolve().parents[2] / "astroroshni_mobile" / "assets" / "logo.png"
    path = Path(os.getenv("REEL_BRAND_LOGO_PATH") or default)
    if not path.is_file():
        raise RuntimeError("Official reel logo is missing. Configure REEL_BRAND_LOGO_PATH to the AstroRoshni PNG logo.")
    content = path.read_bytes()
    if not content:
        raise RuntimeError("Official reel logo is empty.")
    return content


async def _gpt_image(prompt: str, *, logo: bytes, quality: str = "low") -> bytes:
    # A single image request can occasionally hit a transient read/connect
    # timeout. Retrying that request is much safer than discarding a whole
    # 12–18 scene reel after the other parallel work has already started.
    for attempt in range(2):
        try:
            return (await OpenAIPartnerPortraitProvider().edit_image(
                prompt, logo, mime_type="image/png", quality=quality, size=REEL_IMAGE_SIZE,
            )).content
        except (httpx.TimeoutException, httpx.NetworkError, asyncio.TimeoutError) as exc:
            if attempt:
                raise RuntimeError(
                    f"GPT Image request timed out after {attempt + 1} attempts: {type(exc).__name__}"
                ) from exc
            await asyncio.sleep(1.0)


async def _gpt_image_edit(prompt: str, source: Path, *, quality: str = "low") -> bytes:
    return (await OpenAIPartnerPortraitProvider().edit_image(prompt, source.read_bytes(), quality=quality, size=REEL_IMAGE_SIZE)).content


def _premium_factual_edit_prompt(plan: dict, beat: dict, *, visual: str) -> str:
    question = re.sub(r"\s+", " ", str((plan.get("source") or {}).get("question") or "")).strip()[:280]
    claims = {str(item.get("id")): str(item.get("text") or "") for item in plan.get("claims") or []}
    evidence = "\n".join(f"- {claims[key][:220]}" for key in beat.get("evidence_ids") or [] if claims.get(str(key)))
    layout = "complete North Indian kundali with highlighted placements and arrows" if visual == "chart" else "five-level dasha stack with selected periods and dates"
    return f'''Create a finished, high-end 9:16 AstroRoshni editorial keyframe from the supplied factual source image.
Question: {question}
Verified supporting points only:\n{evidence or '- Use only the supplied source.'}

The supplied chart/dasha data is immutable: preserve every rashi, house, planet placement, degree, highlighted target, arrow, dasha level, planet, and date exactly. Do not omit, move, combine, alter, or invent any factual value. Redesign the presentation around the same data; do not merely upscale the source.

Visual target: an award-quality Indian luxury astrology product campaign. Full 9:16 composition; large elegant gold serif headline in the top safe area; a realistic premium black-and-champagne-gold phone centred in a burgundy, candlelit, marble-and-brass environment; rich app header/navigation; cream cards with sharp readable typography; luminous thin gold arrows connecting at most three concise factual callouts to the relevant source locations. The phone must contain a rich, legible app screen with {layout}. All callouts must sit completely within safe margins. Use the verified points above only; omit text rather than fabricate it. No generic poster, no empty UI, no cropped cards, no illegible text, no altered astrology.'''


def _ashtakavarga_prompt(plan: dict, beat: dict, snapshot: dict) -> str:
    question = re.sub(r"\s+", " ", str((plan.get("source") or {}).get("question") or "")).strip()[:280]
    narration = re.sub(r"\s+", " ", str(beat.get("narration") or "")).strip()[:480]
    claims = {str(item.get("id")): str(item.get("text") or "") for item in plan.get("claims") or []}
    evidence = "\n".join(f"- {claims[key][:240]}" for key in beat.get("evidence_ids") or [] if claims.get(str(key)))
    sav = (snapshot.get("ashtakavarga") or {}).get("sav_by_house") or {}
    return f'''Create a finished, high-end 9:16 AstroRoshni Ashtakavarga editorial keyframe.
Question: {question}
Narration: {narration}
Verified supporting points only:\n{evidence or '- Use the SAV data only.'}
Exact Sarvashtakavarga values by house: {json.dumps(sav, sort_keys=True)}

Design an award-quality Indian luxury astrology product campaign: deep burgundy, champagne-gold, refined cream panels, realistic black-and-gold phone, premium app navigation, clean infographic hierarchy, and a concise headline. Build a beautiful SAV screen with all twelve houses and their exact supplied values. Use highlighted rings, arrows, callout cards, or a bar/house-strength visual only where grounded in the values or verified points. Every visible house value must exactly match the supplied JSON. Do not invent any planet placement, dasha, date, yoga, house score, or prediction. No generic poster, no illegible microtext, no cropped content, no watermark.'''


def _scene_image_prompt(plan: dict, beat: dict, snapshot: dict) -> str:
    language = str((plan.get("settings") or {}).get("language") or "en").lower()
    language_instruction = (
        "Hindi (Devanagari). All editorial copy, headings, callouts, and app-interface labels in this image must be fluent Hindi. "
        "Keep the official brand name AstroRoshni unchanged, and retain numeric values and dates exactly."
        if language == "hi" else
        "English. All editorial copy, headings, callouts, and app-interface labels in this image must be fluent English."
    )
    claims = {str(item.get("id")): plain_text(item.get("text") or "") for item in plan.get("claims") or []}
    evidence = [claims.get(str(key), "") for key in beat.get("evidence_ids") or []]
    ascendant_sign = int(snapshot.get("ascendant_sign") or 0) % 12
    houses = [{"house": house, "rashi_number": ((ascendant_sign + house - 1) % 12) + 1,
               "rashi_name": SIGN_NAMES[(ascendant_sign + house - 1) % 12]} for house in range(1, 13)]

    # Resolve a planet's rashi from its verified house and ascendant. This is
    # deliberately independent of legacy raw-sign fields, which were stored as
    # zero-based indexes and could contradict the display rashi in image prompts.
    canonical_placements = []
    for placement in snapshot.get("placements") or []:
        house = int(placement.get("house") or 0)
        if house not in range(1, 13):
            continue
        rashi_number = ((ascendant_sign + house - 1) % 12) + 1
        canonical_placements.append({
            "planet": str(placement.get("planet") or ""),
            "house": house,
            "rashi_number": rashi_number,
            "rashi_name": SIGN_NAMES[rashi_number - 1],
            "degree_in_sign": placement.get("degree_in_sign"),
        })
    kind = str(beat.get("type") or "")
    original_visual_direction = plain_text(beat.get("visual_instruction") or "")
    visual_direction = original_visual_direction
    if kind == "chart_focus":
        chart_cells = [
            {"slot": item["slot"], "exact_cell_label": f"House {item['house']} — {houses[item['house'] - 1]['rashi_name']} ({houses[item['house'] - 1]['rashi_number']})"}
            for item in NORTH_INDIAN_HOUSE_SLOTS
        ]
        source = {
            "chart_type": "North Indian D1 natal chart",
            "ascendant": {"house": 1, "rashi_number": ascendant_sign + 1, "rashi_name": SIGN_NAMES[ascendant_sign]},
            "houses": houses,
            "fixed_counterclockwise_house_slots": list(NORTH_INDIAN_HOUSE_SLOTS),
            "copy_exactly_one_label_per_cell": chart_cells,
            "planet_placements": canonical_placements,
            "allowed_highlights": {"nodes": beat.get("focus_nodes") or [], "arrows": beat.get("draw_edges") or []},
        }
        rendering_rule = (
            "Render exactly ONE standard North Indian D1 natal chart in TEXT-ONLY ACCURACY MODE. Follow FIXED_COUNTERCLOCKWISE_HOUSE_SLOTS precisely: "
            "House 1 is the TOP CENTRAL DIAMOND, House 4 is the LEFT CENTRAL DIAMOND, House 7 is the BOTTOM CENTRAL DIAMOND, and House 10 is the RIGHT CENTRAL DIAMOND. "
            "Houses 2 through 12 proceed COUNTER-CLOCKWISE around the chart. Never run house order clockwise. HOUSE is its fixed chart position; "
            "RASHI NUMBER is the one zodiac sign inside that house. They are different concepts. Use COPY_EXACTLY_ONE_LABEL_PER_CELL as a twelve-cell proof sheet: "
            "each listed label occurs once, in its named slot, and no other sign or number may appear. The supplied ascendant is House 1. For every planet, "
            "copy its supplied house and rashi only. Do not add a planet, move a planet, change the ascendant, or turn rashi numbers into house numbers. "
            "Do not use planetary icons, zodiac glyphs, decorative duplicate labels, a planet legend, generic report, or unsupplied placement. "
            "If a cell cannot be made legible, leave that cell blank rather than inventing or duplicating any label."
        )
        visual_direction = (
            "LOCKED BASE COMPOSITION: render the complete standard North Indian D1 chart as the dominant, upright, unwarped visual. "
            "GEOMETRY BLUEPRINT — draw a square outer border containing FOUR cardinal diamond compartments around the centre: House 1 top, House 4 left, "
            "House 7 bottom, and House 10 right. Place the remaining eight houses as the triangular perimeter wedges specified in FIXED_COUNTERCLOCKWISE_HOUSE_SLOTS. "
            "This is the entire grid: exactly 12 compartments, no single central diamond, no full-corner X, no curved boundaries, no extra subdivisions, "
            "no missing boundary, and no alternate South Indian or wheel layout. "
            "Keep all boundaries thin, straight, continuous, and visible. The chart may be full-frame or a smaller composed element, "
            "but whenever it appears, show the complete unwarped 12-compartment grid rather than cropping or reshaping it. "
            "Do not turn the chart into an infographic, pathway diagram, dashboard, split screen, or a non-North-Indian grid. "
            "Use the planner direction only for a small external callout, gold highlight, arrow, or background atmosphere; it may never alter, crop, "
            f"replace, or obscure the twelve-cell chart. Planner direction to adapt safely: {original_visual_direction}"
        )
    elif kind == "ashtakavarga":
        source = {"metric": "Sarvashtakavarga (SAV)", "sav_by_house": ((snapshot.get("ashtakavarga") or {}).get("sav_by_house") or {})}
        rendering_rule = (
            "Render only the supplied Sarvashtakavarga values. Every key in SAV_BY_HOUSE is a HOUSE NUMBER 1 through 12, "
            "not a rashi/sign number and not a planet. Label any value visibly as ‘House N — value’. "
            "Do not render a natal chart, zodiac-rashi grid, planet placements, dashas, or a house interpretation that was not supplied."
        )
    elif kind == "dasha_stack":
        source = {"active_dasha_hierarchy": snapshot.get("current_dashas") or {}}
        rendering_rule = "Render only the supplied active dasha hierarchy. Copy each level, planet name, and date exactly. Do not render a natal chart, invent alternate periods, or infer timing beyond the supplied values."
    else:
        source = {}
        rendering_rule = "Do not render a natal chart, rashi grid, planetary placements, SAV table, or dasha stack in this scene. This is a focused editorial/narrative visual only."
        visual_direction = original_visual_direction
    return f'''Create a finished premium 9:16 AstroRoshni reel image.
BRAND REFERENCE: The attached image is the official AstroRoshni gold AR logo. Use it as a brand asset within the new scene. Preserve the AR monogram, its geometry, colours, and proportions. Place the actual logo beside the exact brand name 'AstroRoshni' in a tasteful header or footer inside safe margins. The reference is a small logo, not the full scene or layout: create the complete scene described below around it. Do not substitute a lotus, star, sun, zodiac symbol, invented emblem, or invented tagline for the supplied logo. Keep branding separate from the chart and its factual labels.
VISUAL MODULE: {kind}
NON-NEGOTIABLE FACTUAL RULE: {rendering_rule}
VISUAL DIRECTION: {visual_direction}
NARRATION: {plain_text(beat.get("narration") or "")}
APPROVED CLAIMS: {json.dumps([item for item in evidence if item], ensure_ascii=False)}
VERIFIED DATA FOR THIS MODULE ONLY: {json.dumps(source, ensure_ascii=False)}
FOCUS NODES: {json.dumps(beat.get("focus_nodes") or [])}; VERIFIED ARROWS: {json.dumps(beat.get("draw_edges") or [])}
STRICT RENDERING RULE: {rendering_rule}
VISIBLE TEXT: Use finished plain typography. Never print Markdown formatting markers (hashes, asterisks, backticks) in the image. Headings must read naturally, for example 'Key Insights'.
OUTPUT LANGUAGE: {language_instruction}
Create an award-quality Indian luxury editorial design: burgundy, champagne-gold, cream UI cards, phone/app screens where appropriate, clear arrows and pointed callout blocks. Use only the supplied claims and verified data. Do not invent astrology, dates, placements, scores, predictions, generic reports, or thank-you messages. Prefer a few short, large, readable labels over paragraphs of invented copy. All text and focal elements must remain inside 9:16 safe margins.'''


def _native_subject_direction(snapshot: dict) -> str:
    presentation = str(snapshot.get("native_presentation") or "unspecified").lower()
    if presentation in {"male", "female"}:
        return (
            f"The saved native is an adult {presentation}. When the scene depicts the native, make the primary subject an adult Indian {presentation}; "
            "never depict the native as another gender. If the scene includes another person, make their role visually distinct rather than presenting them as the native."
        )
    return "The saved native's gender is unspecified. Do not assign a gender to a central native; use an object, place, hands, silhouette, or a gender-neutral composition instead."


async def _podcast_audio(text: str, language: str, voice_name: str) -> tuple[bytes, str]:
    """Synthesize one Reel beat without an LLM rewrite or an SSML retry.

    A Reel already has approved, short narration for every beat.  Sending every
    beat through the general speech endpoint used to make a separate Gemini
    rewrite, then attempt an SSML request that Chirp rejected before retrying
    as plain text.  Those synchronous preparation calls stopped the event loop
    from even starting image generation.  Use the same Google voice and spoken
    text cleanup directly, with its blocking RPC isolated in the thread pool.
    """
    plain_text = _segment_text_to_plain(text)
    if not plain_text:
        raise RuntimeError("Reel narration is empty after speech preparation.")

    def synthesize_beat() -> bytes:
        credentials = _get_google_credentials()
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        voice, audio_config = _build_voice_and_config(
            language,
            voice_name,
            0.95 if language.startswith("hi") else 1.0,
        )
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=plain_text),
            voice=voice,
            audio_config=audio_config,
        )
        return response.audio_content

    return await asyncio.to_thread(synthesize_beat), voice_name


def _video_output_tokens(usage: dict) -> int:
    """Extract Omni video tokens without trusting a particular API response shape."""
    for row in (usage or {}).get("output_tokens_by_modality") or []:
        if str(row.get("modality") or "").lower() == "video":
            try: return int(row.get("tokens") or 0)
            except (TypeError, ValueError): pass
    for key in ("video_output_tokens", "output_video_tokens", "total_output_tokens", "output_tokens"):
        try:
            value = int((usage or {}).get(key) or 0)
            if value:
                return value
        except (TypeError, ValueError):
            pass
    details = (usage or {}).get("output_token_details") or {}
    try:
        return int(details.get("video_tokens") or 0)
    except (TypeError, ValueError):
        return 0


def _usage_tokens(usage: dict, key: str) -> int:
    try: return int((usage or {}).get(key) or 0)
    except (TypeError, ValueError): return 0


def _record_omni_usage(user_id: int, run_id: str, role: str, usage: dict) -> None:
    metadata = {"role": role, "usage": usage}
    video_tokens = _video_output_tokens(usage)
    _record(user_id, run_id, "video", "google:gemini-omni-1.1-flash", video_tokens, {**metadata, "unit": "video_output_tokens"}, VIDEO_TOKEN_COST_INR)
    input_tokens = _usage_tokens(usage, "total_input_tokens") or _usage_tokens(usage, "input_tokens")
    thought_tokens = _usage_tokens(usage, "total_thought_tokens") or _usage_tokens(usage, "thought_tokens")
    if input_tokens: _record(user_id, run_id, "video_input", "google:gemini-omni-1.1-flash", input_tokens, {**metadata, "unit": "input_tokens"}, OMNI_INPUT_TOKEN_COST_INR)
    if thought_tokens: _record(user_id, run_id, "video_thinking", "google:gemini-omni-1.1-flash", thought_tokens, {**metadata, "unit": "thought_tokens"}, OMNI_TEXT_TOKEN_COST_INR)


def _run_video(prompt: str, *, image: bytes | None = None) -> tuple[bytes, dict]:
    """Gemini Omni Flash direct call using its supported text/image inputs."""
    key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not key: raise RuntimeError("GEMINI_API_KEY is not configured")
    inputs: list[dict] = []
    if image: inputs.append({"type": "image", "data": base64.b64encode(image).decode(), "mime_type": "image/png"})
    inputs.append({"type": "text", "text": prompt})
    payload = {"model": VIDEO_MODEL, "input": inputs, "response_format": {"type": "video", "aspect_ratio": "9:16", "resolution": "720p"}, "generation_config": {"video_config": {"task": "image_to_video" if image else "text_to_video"}}}
    with httpx.Client(timeout=480, follow_redirects=True) as client:
        response = client.post("https://generativelanguage.googleapis.com/v1beta/interactions", headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=payload)
        if response.is_error: raise RuntimeError(f"Gemini Omni generation failed: {response.text[:800]}")
        result = response.json()
        for step in result.get("steps") or []:
            for part in step.get("content") or []:
                if part.get("type") == "video" and part.get("data"):
                    return base64.b64decode(part["data"]), result.get("usage") or {}
    raise RuntimeError("Gemini Omni returned no video output")


def _still_clip(ffmpeg: str, image: Path, output: Path, seconds: float) -> None:
    # GPT Image outputs finished 9:16 editorial compositions. Do not apply a
    # Ken-Burns zoom: it trims safe-edge headlines/callouts and makes detailed
    # chart boundaries appear to shake. Invalid source ratios are letterboxed,
    # never cropped, so the whole factual visual remains visible.
    # Generated images may be 2:3 despite the requested 9:16 frame. Use a
    # cover transform, not decrease+pad: black letterboxing makes a Reel look
    # unfinished. Cropping is centred and only removes the side excess.
    motion = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},fps=30,format=yuv420p"
    subprocess.run([ffmpeg, "-nostdin", "-y", "-loop", "1", "-i", str(image), "-t", str(seconds), "-vf", motion, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)], check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)


def _video_segment(ffmpeg: str, source: Path, output: Path, start: float) -> None:
    subprocess.run([ffmpeg, "-nostdin", "-y", "-ss", str(start), "-i", str(source), "-t", "5", "-c", "copy", str(output)], check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=120)


def _duration(ffmpeg: str, media: Path) -> float:
    # Background workers must never inherit an interactive stdin; that can make
    # FFmpeg hang even though the MP3 is already complete on disk.
    probe = subprocess.run([ffmpeg, "-nostdin", "-hide_banner", "-i", str(media)], capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL, timeout=10)
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", probe.stderr)
    if not match:
        raise RuntimeError(f"Could not determine duration of {media.name}")
    return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def _compose(ffmpeg: str, clips: list[Path], narration: list[Path | None], output: Path, *, source_audio: set[int]) -> None:
    """Normalise provider clips and lay the exact narration back in sequence.

    This avoids a fragile stream-copy concat when generated clips have different
    codecs/audio layouts, and guarantees silence during chart/dasha inserts.
    """
    if len(clips) != len(narration):
        raise RuntimeError("Video/audio timeline mismatch")
    # Never force podcast speech into a five-second scene; the measured audio
    # duration determines how long its visual remains on screen.
    durations = [_duration(ffmpeg, clip) for clip in clips]
    inputs: list[str] = []
    for clip in clips: inputs += ["-i", str(clip)]
    audio_indexes: dict[int, int] = {}
    for index, audio in enumerate(narration):
        if audio:
            audio_indexes[index] = len(clips) + len(audio_indexes)
            inputs += ["-i", str(audio)]
    filters: list[str] = []
    for index in range(len(clips)):
        filters.append(f"[{index}:v]trim=duration={durations[index]:.3f},setpts=PTS-STARTPTS,scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},fps=30,format=yuv420p[v{index}]")
        if index in source_audio:
            filters.append(f"[{index}:a]aresample=44100,apad,atrim=duration={durations[index]:.3f},asetpts=PTS-STARTPTS[a{index}]")
        elif index in audio_indexes:
            filters.append(f"[{audio_indexes[index]}:a]aresample=44100,apad,atrim=duration={durations[index]:.3f},asetpts=PTS-STARTPTS[a{index}]")
        else:
            filters.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={durations[index]:.3f}[a{index}]")
    filters.append("".join(f"[v{i}][a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=1:a=1[v][a]")
    subprocess.run([ffmpeg, "-nostdin", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(output)], check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=600)


def _claim_reel_job(job_id: str, claim_id: str, *, claim_minutes: int) -> str:
    """Atomically claim a durable job; Cloud Tasks delivery is at-least-once."""
    with get_conn() as conn:
        row = execute(
            conn,
            """
            UPDATE reel_render_jobs
            SET status = 'processing', task_claim_id = %s,
                task_claimed_until = CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND status NOT IN ('completed', 'failed')
              AND (task_claimed_until IS NULL OR task_claimed_until < CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (claim_id, max(1, int(claim_minutes)), job_id),
        ).fetchone()
        if row:
            conn.commit()
            return "claimed"
        existing = execute(conn, "SELECT status FROM reel_render_jobs WHERE id = %s", (job_id,)).fetchone()
        conn.commit()
    if not existing:
        return "missing"
    return "terminal" if str(existing[0]) in {"completed", "failed"} else "busy"


def process_reel_job(job_id: str, *, claim_id: str | None = None) -> str:
    claim_id = str(claim_id or uuid.uuid4())
    claim_state = _claim_reel_job(
        job_id,
        claim_id,
        # The Cloud Tasks request itself can run for 30 minutes. Leave a
        # recovery buffer beyond that deadline before a retry may take over.
        claim_minutes=int(os.getenv("REEL_TASK_CLAIM_MINUTES", "45") or "45"),
    )
    if claim_state != "claimed":
        return claim_state
    with get_conn() as conn:
        row = execute(conn, "SELECT user_id, plan_json FROM reel_render_jobs WHERE id=%s", (job_id,)).fetchone()
    if not row:
        return "missing"
    user_id, raw_plan = row; plan = json.loads(raw_plan); run_id = plan["run_id"]
    snapshot = plan.get("chart_snapshot")
    if not snapshot:
        _fail_reel(job_id, "Premium reels require the chat to be linked to a saved birth chart. No chart visual was generated.")
        return "failed"
    work = ROOT / str(user_id) / job_id
    try:
        work.mkdir(parents=True, exist_ok=True); ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        language = plan.get("settings", {}).get("language", "en")
        beats = plan.get("storyboard") or []
        duration_seconds = int((plan.get("settings") or {}).get("duration_seconds") or 180)
        min_beats, max_beats = (8, 10) if duration_seconds == 90 else (12, 18)
        if not min_beats <= len(beats) <= max_beats:
            raise RuntimeError(f"The approved {duration_seconds}-second reel plan must contain {min_beats} to {max_beats} directed beats.")
        # Validate the asset before starting any paid TTS/image requests.
        logo = _brand_logo()
        _update(job_id, "creating_planned_shots")

        async def limited(semaphore: asyncio.Semaphore, operation):
            async with semaphore:
                return await operation

        async def create_assets_and_clips() -> list[tuple[Path, Path, str, str, str]]:
            # Local performance experiment: launch one TTS and one image job
            # for every storyboard beat at once.  The providers are independent
            # and the environment values remain an immediate escape hatch if a
            # quota responds poorly under real load.
            scene_count = max(1, len(beats))
            tts_limit = int(os.getenv("REEL_TTS_CONCURRENCY", str(scene_count)))
            image_limit = int(os.getenv("REEL_IMAGE_CONCURRENCY", str(scene_count)))
            tts_semaphore = asyncio.Semaphore(tts_limit)
            image_semaphore = asyncio.Semaphore(image_limit)
            female_voice, _ = get_podcast_tts_voices(language)
            asset_started = time.perf_counter()
            audio_tasks = {
                index: asyncio.create_task(
                    limited(
                        tts_semaphore,
                        _podcast_audio(
                            str(beat.get("narration") or "").strip(),
                            language,
                            female_voice,
                        ),
                    )
                )
                for index, beat in enumerate(beats)
            }
            image_tasks: dict[str, asyncio.Task[bytes]] = {}
            async def generate_scene(index: int, beat: dict) -> bytes:
                kind = str(beat.get("type") or "unknown")
                try:
                    prompt = _scene_image_prompt(plan, beat, snapshot)
                    if kind == "lifestyle_image":
                        prompt += f"\n{_native_subject_direction(snapshot)}"
                    return await limited(image_semaphore, _gpt_image(prompt, logo=logo, quality="low"))
                except Exception as exc:
                    detail = str(exc).strip() or repr(exc)
                    raise RuntimeError(f"Image generation failed for beat {index + 1} ({kind}): {type(exc).__name__}: {detail}") from exc

            for index, beat in enumerate(beats):
                # Cost-control policy: every Reel Studio image uses GPT Image's
                # low-quality tier, including factual chart/SAV/dasha scenes.
                image_tasks[f"beat-{index}"] = asyncio.create_task(generate_scene(index, beat))
            # Give every task one event-loop turn now. The direct TTS call
            # immediately moves its blocking RPC to a thread, allowing image
            # HTTP requests to begin before any audio result is awaited.
            await asyncio.sleep(0)
            logger.info(
                "REEL_ASSET_FANOUT job_id=%s beats=%s tts_concurrency=%s image_concurrency=%s elapsed_ms=%.1f",
                job_id,
                scene_count,
                tts_limit,
                image_limit,
                (time.perf_counter() - asset_started) * 1000,
            )
            async def materialize(path: Path, task: asyncio.Task[bytes]) -> Path:
                path.write_bytes(await task)
                return path

            image_paths: dict[str, asyncio.Task[Path]] = {}
            for index, beat in enumerate(beats):
                image_paths[f"beat-{index}"] = asyncio.create_task(materialize(work / f"scene-{index}.png", image_tasks[f"beat-{index}"]))

            clip_semaphore = asyncio.Semaphore(int(os.getenv("REEL_CLIP_CONCURRENCY", "4")))

            async def prepare_beat(index: int, beat: dict) -> tuple[Path, Path, str, str, str]:
                kind = str(beat.get("type") or "")
                line = str(beat.get("narration") or "").strip()
                if not line:
                    raise RuntimeError(f"Beat {index + 1} has no narration.")
                audio, voice = await audio_tasks[index]
                audio_path = work / f"podcast-{index}.mp3"; audio_path.write_bytes(audio)
                image = await image_paths[f"beat-{index}"]
                clip = work / f"beat-{index}.mp4"
                def encode() -> None:
                    _still_clip(ffmpeg, image, clip, max(4.0, _duration(ffmpeg, audio_path) + 0.35))
                async with clip_semaphore:
                    await asyncio.to_thread(encode)
                return clip, audio_path, voice, kind, line

            async def indexed_prepare(index: int, beat: dict):
                return index, await prepare_beat(index, beat)

            prepared_by_index: dict[int, tuple[Path, Path, str, str, str]] = {}
            completed = 0
            for task in asyncio.as_completed([indexed_prepare(index, beat) for index, beat in enumerate(beats)]):
                index, prepared_beat = await task
                prepared_by_index[index] = prepared_beat
                completed += 1
                # This is a real completed scene, not a time-based estimate.
                # The client turns it into a branded progress experience.
                _update(job_id, f"creating_your_reel_{completed}_of_{len(beats)}")
            return [prepared_by_index[index] for index in range(len(beats))]

        prepared = asyncio.run(create_assets_and_clips())
        clips, timeline_audio = [], []
        for clip, audio_path, voice, kind, line in prepared:
            clips.append(clip); timeline_audio.append(audio_path)
            _record(user_id, run_id, "tts", f"google-tts:{voice}", len(line), {"role": kind, "unit": "characters"}, CHIRP_TTS_CHAR_COST_INR)
            _record(user_id, run_id, "image", "openai:gpt-image-2", 1, {"role": kind, "pricing": "gpt-image-2-1024x1824-low", "reference": "official_astroroshni_logo", "input_image_cost_included": False}, GPT_IMAGE_LOW_COST_INR)
        _update(job_id, "premium_compositing")
        output = work / "final-reel.mp4"; _compose(ffmpeg, clips, timeline_audio, output, source_audio=set())
        _record(user_id, run_id, "render", "ffmpeg", 1, {"composition": "gpt_image_edits+deterministic_astrology_visuals+podcast_tts", "omni_video_enabled": False})
        from reel_studio.storage import store_reel
        _update(job_id, "saving_reel")
        store_reel(user_id, job_id, output)
        _update(job_id, "completed", output_url=f"/api/reel-studio/jobs/{job_id}/download")
    except Exception as exc:
        detail = str(exc).strip() or repr(exc)
        _fail_reel(job_id, f"{type(exc).__name__}: {detail}")
        return "failed"
    return "completed"
