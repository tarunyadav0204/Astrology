"""Premium, chart-grounded Reel Studio renderer.

Each output intercuts an original AI astrologer speaking to camera, a
deterministic kundali, a deterministic dasha timeline, and generated
live-action b-roll. It never substitutes generic text cards for chart data.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path
from typing import Any

import httpx
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from db import execute, get_conn
from partner_profile.image_provider import OpenAIPartnerPortraitProvider
from tts.routes import SpeechSynthesisRequest, synthesize
from utils.admin_settings import get_podcast_tts_voices

ROOT = Path(os.getenv("REEL_LOCAL_OUTPUT_DIR", "storage/reels"))
VIDEO_MODEL = "gemini-omni-1.1-flash"
# Temporary cost-control mode.  Keep the Omni call below intact for later, but
# do not invoke it unless this is explicitly enabled in deployment.
OMNI_VIDEO_ENABLED = os.getenv("REEL_ENABLE_OMNI_VIDEO", "false").strip().lower() in {"1", "true", "yes", "on"}
WIDTH, HEIGHT = 1080, 1920
PLANET_ABBR = {"Jupiter": "Ju", "Mercury": "Me", "Saturn": "Sa", "Venus": "Ve", "Mars": "Ma", "Moon": "Mo", "Sun": "Su", "Rahu": "Ra", "Ketu": "Ke"}
USD_TO_INR = float(os.getenv("REEL_USD_TO_INR", "95"))
VIDEO_TOKEN_COST_INR = 17.50 * USD_TO_INR / 1_000_000
OMNI_INPUT_TOKEN_COST_INR = 1.50 * USD_TO_INR / 1_000_000
OMNI_TEXT_TOKEN_COST_INR = 9.00 * USD_TO_INR / 1_000_000
GPT_IMAGE_COST_INR = 0.041 * USD_TO_INR  # GPT Image 2, 1024x1536 medium
CHIRP_TTS_CHAR_COST_INR = 30.0 * USD_TO_INR / 1_000_000


def _update(job_id: str, status: str, *, output_url: str | None = None, error: str | None = None) -> None:
    with get_conn() as conn:
        execute(conn, """UPDATE reel_render_jobs SET status=%s, output_url=COALESCE(%s, output_url),
            error_message=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s""", (status, output_url, error, job_id))
        conn.commit()


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


def _base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    # The data cards use the same warm editorial language as the product, not
    # generic "AI astrology" gradients.
    image = Image.new("RGB", (WIDTH, HEIGHT), "#31040f")
    draw = ImageDraw.Draw(image)
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
    draw.text((136, 416), "‹", fill="#f7e2b7", font=_display_font(46))
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


def _chart_visual(path: Path, snapshot: dict, *, focus_nodes: list[str] | None = None, draw_edges: list[str] | None = None) -> None:
    image, draw = _base_canvas()
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
        by_house.get(house, []).append(PLANET_ABBR.get(planet, "?")); planet_houses[planet.lower()] = house
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
        lines = ([" ".join(planets)] if len(planets) <= 2 else planets) if planets else []
        for index, line in enumerate(lines):
            draw.text((x, y + 10 + index * 31 - (len(lines) - 1) * 15), line, anchor="mm", fill="#211713", font=_font(26 if len(lines) < 3 else 23, True))
    draw.rounded_rectangle((118, 1530, 962, 1690), radius=26, fill="#fffaf1", outline="#bd8629", width=3)
    draw.text((152, 1562), "READING RULE", fill="#8d1b38", font=_font(20, True))
    for line_index, line in enumerate(textwrap.wrap("Every highlighted placement and arrow is resolved from the saved chart.", width=54)):
        draw.text((152, 1600 + line_index * 31), line, fill="#33251f", font=_font(22))
    image.save(path, "PNG")


def _dasha_visual(path: Path, snapshot: dict) -> None:
    image, draw = _base_canvas()
    draw.text((540, 150), "Dasha Stack", anchor="mm", fill="#ffe4a2", font=_display_font(68, True))
    draw.text((540, 224), "the timing behind the reading", anchor="mm", fill="#ebc985", font=_display_font(28))
    _phone_shell(draw, "Dasha Browser", "Dasha")
    dashas = snapshot.get("current_dashas") or {}
    for index, (key, label) in enumerate((("mahadasha", "MAHADASHA"), ("antardasha", "ANTARDASHA"), ("pratyantardasha", "PRATYANTARDASHA"))):
        y = 625 + index * 280; period = dashas.get(key) or {}
        draw.text((142, y), f"0{index + 1}", fill="#8d1b38", font=_font(20, True))
        draw.text((205, y), label, fill="#471421", font=_display_font(31, True))
        draw.rounded_rectangle((142, y + 52, 938, y + 217), radius=24, fill="#fffaf1", outline="#d5b37b", width=2)
        draw.rounded_rectangle((165, y + 72, 505, y + 195), radius=19, fill="#68142d", outline="#e5b855", width=4)
        draw.text((195, y + 100), str(period.get("planet") or "Not available"), fill="#fff0d0", font=_display_font(39, True))
        draw.text((195, y + 156), " → ".join(filter(None, (str(period.get("start") or ""), str(period.get("end") or "")))) or "Current period", fill="#f3dcae", font=_font(17))
        if index < 2:
            draw.line((190, y + 220, 190, y + 268), fill="#bd8629", width=4)
            draw.polygon([(190, y + 270), (181, y + 256), (199, y + 256)], fill="#bd8629")
    draw.rounded_rectangle((140, 1518, 940, 1665), radius=25, fill="#fff9ef", outline="#bd8629", width=3)
    draw.text((175, 1553), "TIMING, NOT CERTAINTY", fill="#8d1b38", font=_font(19, True))
    _wrapped(draw, "Dashas show the active sequence used in this reading.", (175, 1590), 48, 24)
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


async def _gpt_image(prompt: str) -> bytes:
    return (await OpenAIPartnerPortraitProvider().generate_portrait(prompt, 0)).content


async def _podcast_audio(text: str, language: str) -> tuple[bytes, str]:
    """Use the admin-selected Indian podcast voice at its natural cadence."""
    female_voice, _ = get_podcast_tts_voices(language)
    response = await synthesize(request=SpeechSynthesisRequest(
        text=text, lang=language, voice_name=female_voice, prepare_spoken=True,
        speaking_rate=0.95 if language.startswith("hi") else 1.0,
    ))
    payload = json.loads(response.body)
    return base64.b64decode(payload["audio"]), str(payload.get("voice_name") or female_voice)


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
    motion = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00065,1.08)':d={int(seconds * 30)}:s={WIDTH}x{HEIGHT}:fps=30,format=yuv420p"
    subprocess.run([ffmpeg, "-y", "-loop", "1", "-i", str(image), "-t", str(seconds), "-vf", motion, "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)], check=True, capture_output=True, timeout=120)


def _video_segment(ffmpeg: str, source: Path, output: Path, start: float) -> None:
    subprocess.run([ffmpeg, "-y", "-ss", str(start), "-i", str(source), "-t", "5", "-c", "copy", str(output)], check=True, capture_output=True, timeout=120)


def _duration(ffmpeg: str, media: Path) -> float:
    probe = subprocess.run([ffmpeg, "-i", str(media)], capture_output=True, text=True, check=False, timeout=30)
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
    subprocess.run([ffmpeg, "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", str(output)], check=True, capture_output=True, timeout=600)


def process_reel_job(job_id: str) -> None:
    with get_conn() as conn:
        row = execute(conn, "SELECT user_id, plan_json FROM reel_render_jobs WHERE id=%s", (job_id,)).fetchone()
    if not row: return
    user_id, raw_plan = row; plan = json.loads(raw_plan); run_id = plan["run_id"]
    snapshot = plan.get("chart_snapshot")
    if not snapshot:
        _update(job_id, "failed", error="Premium reels require the chat to be linked to a saved birth chart. No chart visual was generated.")
        return
    work = ROOT / str(user_id) / job_id
    try:
        work.mkdir(parents=True, exist_ok=True); ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        language = plan.get("settings", {}).get("language", "en")
        beats = plan.get("storyboard") or []
        if len(beats) != 9:
            raise RuntimeError("The approved reel plan must contain exactly nine directed beats.")
        _update(job_id, "creating_presenter")
        portrait_path = work / "presenter.png"
        portrait = portrait_path.read_bytes() if portrait_path.exists() else asyncio.run(_gpt_image("Original fictional Indian woman astrologer in her early thirties, warm confident expression, editorial studio portrait, deep indigo sari-inspired outfit, subtle gold jewellery, soft cinematic key light, centred vertical composition with clean negative space, premium social video, no text, no logos"))
        portrait_path.write_bytes(portrait)
        _record(user_id, run_id, "image", "openai:gpt-image-2", 1, {"role": "original_presenter", "pricing": "gpt-image-2-1024x1536-medium"}, GPT_IMAGE_COST_INR)
        chart_image, dasha_image, av_image = work / "chart.png", work / "dashas.png", work / "ashtakavarga.png"
        _chart_visual(chart_image, snapshot); _dasha_visual(dasha_image, snapshot); _ashtakavarga_visual(av_image, snapshot)
        stills = {"chart": chart_image, "dasha": dasha_image, "ashtakavarga": av_image, "closing": chart_image}
        _update(job_id, "creating_planned_shots")
        clips: list[Path] = []
        timeline_audio: list[Path | None] = []
        presenter_audio_positions: set[int] = set()
        presenter_source: Path | None = None
        presenter_uses = 0
        presenter_script = " ".join(str(beat.get("narration") or "").strip() for beat in beats if beat.get("type") == "presenter")
        for index, beat in enumerate(beats):
            kind = str(beat.get("type") or "")
            line = str(beat.get("narration") or "").strip()
            if not line:
                raise RuntimeError(f"Beat {index + 1} has no narration.")
            if kind == "presenter":
                if OMNI_VIDEO_ENABLED and presenter_source is None:
                    video, usage = _run_video(f"Use the reference portrait as the same original fictional Indian astrologer. In one continuous 10-second shot she faces camera and says exactly: \"{presenter_script}\". Warm clear {'Hindi' if language == 'hi' else 'Indian English'} female voice and accent, synchronized natural speech, precise lip movements and restrained hand gestures. Editorial studio lighting. No text, charts, symbols, captions, or extra voices.", image=portrait)
                    presenter_source = work / "presenter-source.mp4"; presenter_source.write_bytes(video)
                    _record_omni_usage(user_id, run_id, "10_second_presenter", usage)
                if OMNI_VIDEO_ENABLED and presenter_uses == 0:
                    clip = presenter_source
                elif OMNI_VIDEO_ENABLED:
                    clip = work / f"presenter-{index}.mp4"; _video_segment(ffmpeg, presenter_source, clip, 5)
                else:
                    audio, voice = asyncio.run(_podcast_audio(line, language))
                    audio_path = work / f"podcast-presenter-{index}.mp3"; audio_path.write_bytes(audio)
                    clip = work / f"presenter-still-{index}.mp4"; _still_clip(ffmpeg, portrait_path, clip, max(4.0, _duration(ffmpeg, audio_path) + 0.35))
                presenter_uses += 1
                clips.append(clip)
                if OMNI_VIDEO_ENABLED:
                    presenter_audio_positions.add(len(clips) - 1); timeline_audio.append(None)
                else:
                    timeline_audio.append(audio_path)
                    _record(user_id, run_id, "tts", f"google-tts:{voice}", len(line), {"role": "presenter", "unit": "characters"}, CHIRP_TTS_CHAR_COST_INR)
            elif kind == "lifestyle_image":
                image_bytes = asyncio.run(_gpt_image(f"Luxury editorial photograph for an AstroRoshni astrology reel: {beat.get('visual_instruction')}. Refined Indian editorial art direction, warm champagne-gold highlights, deep burgundy and espresso palette, realistic tactile materials, soft cinematic bokeh, sophisticated magazine composition, natural human emotion, photographic realism. No text, no logos, no charts, no astrology symbols, no cheap fantasy, no plastic AI look."))
                image_path = work / f"lifestyle-{index}.png"; image_path.write_bytes(image_bytes)
                audio, voice = asyncio.run(_podcast_audio(line, language)); audio_path = work / f"podcast-{index}.mp3"; audio_path.write_bytes(audio); timeline_audio.append(audio_path)
                clip = work / f"lifestyle-{index}.mp4"; _still_clip(ffmpeg, image_path, clip, max(4.0, _duration(ffmpeg, audio_path) + 0.35)); clips.append(clip)
                _record(user_id, run_id, "image", "openai:gpt-image-2", 1, {"role": "lifestyle_image", "pricing": "gpt-image-2-1024x1536-medium"}, GPT_IMAGE_COST_INR)
                _record(user_id, run_id, "tts", f"google-tts:{voice}", len(line), {"role": kind, "unit": "characters"}, CHIRP_TTS_CHAR_COST_INR)
            else:
                if kind == "chart":
                    image = work / f"chart-focus-{index}.png"
                    _chart_visual(image, snapshot, focus_nodes=list(beat.get("focus_nodes") or []), draw_edges=list(beat.get("draw_edges") or []))
                else:
                    image = stills.get(kind)
                    if image is None:
                        raise RuntimeError(f"No deterministic renderer is registered for reel beat type: {kind}")
                audio, voice = asyncio.run(_podcast_audio(line, language)); audio_path = work / f"podcast-{index}.mp3"; audio_path.write_bytes(audio); timeline_audio.append(audio_path)
                clip = work / f"{kind}-{index}.mp4"; _still_clip(ffmpeg, image, clip, max(4.0, _duration(ffmpeg, audio_path) + 0.35)); clips.append(clip)
                _record(user_id, run_id, "tts", f"google-tts:{voice}", len(line), {"role": kind, "unit": "characters"}, CHIRP_TTS_CHAR_COST_INR)
        _update(job_id, "premium_compositing")
        output = work / "final-reel.mp4"; _compose(ffmpeg, clips, timeline_audio, output, source_audio=presenter_audio_positions)
        _record(user_id, run_id, "render", "ffmpeg", 1, {"composition": "gpt_images+deterministic_astrology_visuals+podcast_tts", "omni_video_enabled": OMNI_VIDEO_ENABLED})
        _update(job_id, "completed", output_url=f"/api/reel-studio/jobs/{job_id}/download")
    except Exception as exc:
        _update(job_id, "failed", error=str(exc)[:1000])
