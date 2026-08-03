"""
Deterministic locational recommendation map for chat summary_image.

Uses Pillow only (no matplotlib/cartopy). Cities are plotted with
equirectangular projection onto India or world bounds from the pack.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Fallback only if the GeoJSON asset is missing — prefer chat/data/india_outline.json.
_INDIA_OUTLINE_FALLBACK: List[Tuple[float, float]] = [
    (68.1, 23.6), (69.0, 22.0), (70.0, 20.7), (72.8, 18.9), (72.9, 16.0),
    (74.0, 14.5), (74.9, 12.8), (76.2, 10.0), (77.5, 8.1), (80.2, 13.0),
    (80.3, 15.9), (82.0, 17.0), (85.0, 19.8), (87.0, 21.5), (88.4, 21.9),
    (88.9, 23.0), (89.0, 24.5), (88.2, 26.2), (89.8, 26.8), (92.0, 24.5),
    (93.5, 24.0), (95.0, 26.0), (97.4, 27.8), (95.5, 28.5), (94.0, 28.8),
    (91.8, 27.5), (89.5, 28.0), (88.0, 27.5), (86.0, 27.0), (83.0, 28.5),
    (80.0, 30.5), (78.0, 31.5), (76.5, 32.5), (74.5, 34.0), (74.0, 35.0),
    (73.0, 34.0), (72.0, 33.0), (71.0, 30.0), (70.0, 28.0), (69.5, 26.0),
    (68.5, 24.5), (68.1, 23.6),
]

_INDIA_OUTLINE_CACHE: Optional[List[Tuple[float, float]]] = None
_WORLD_LAND_CACHE: Optional[List[List[Tuple[float, float]]]] = None


def _load_india_outline() -> List[Tuple[float, float]]:
    global _INDIA_OUTLINE_CACHE
    if _INDIA_OUTLINE_CACHE is not None:
        return _INDIA_OUTLINE_CACHE
    path = Path(__file__).resolve().parent / "data" / "india_outline.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        coords = payload.get("coordinates") if isinstance(payload, dict) else None
        ring = coords[0] if isinstance(coords, list) and coords else None
        points: List[Tuple[float, float]] = []
        if isinstance(ring, list):
            for pair in ring:
                if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                    continue
                points.append((float(pair[0]), float(pair[1])))
        if len(points) >= 20:
            _INDIA_OUTLINE_CACHE = points
            return points
    except Exception:
        logger.warning("india_outline_load_failed path=%s", path, exc_info=True)
    _INDIA_OUTLINE_CACHE = list(_INDIA_OUTLINE_FALLBACK)
    return _INDIA_OUTLINE_CACHE


def _load_world_land() -> List[List[Tuple[float, float]]]:
    """Simplified country mainland polygons for abroad/both base maps."""
    global _WORLD_LAND_CACHE
    if _WORLD_LAND_CACHE is not None:
        return _WORLD_LAND_CACHE
    path = Path(__file__).resolve().parent / "data" / "world_land.json"
    polygons: List[List[Tuple[float, float]]] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw = payload.get("polygons") if isinstance(payload, dict) else None
        if isinstance(raw, list):
            for ring in raw:
                if not isinstance(ring, list) or len(ring) < 4:
                    continue
                pts: List[Tuple[float, float]] = []
                for pair in ring:
                    if not isinstance(pair, (list, tuple)) or len(pair) < 2:
                        continue
                    pts.append((float(pair[0]), float(pair[1])))
                if len(pts) < 4:
                    continue
                lons = [p[0] for p in pts]
                lats = [p[1] for p in pts]
                # Skip antimeridian-wrapping rings (they render as full-width bands).
                if max(lons) - min(lons) > 170:
                    continue
                # Skip Antarctica-heavy rings (looks like a flat strip at the bottom).
                if max(lats) < -55:
                    continue
                polygons.append(pts)
    except Exception:
        logger.warning("world_land_load_failed path=%s", path, exc_info=True)
    if not polygons:
        # Minimal fallback continents if asset missing.
        polygons = [
            [(-170, 65), (-50, 70), (-55, 45), (-80, 25), (-105, 20), (-125, 50), (-170, 65)],
            [(-85, 15), (-35, 5), (-35, -55), (-70, -55), (-80, -20), (-85, 15)],
            [(-15, 70), (40, 70), (60, 55), (40, 35), (10, 35), (-10, 50), (-15, 70)],
            [(40, 55), (145, 65), (145, 35), (100, 5), (40, 10), (40, 55)],
            [(110, -10), (155, -10), (155, -45), (110, -45), (110, -10)],
            [(20, 35), (50, 30), (50, -35), (15, -35), (10, 0), (20, 35)],
        ]
    _WORLD_LAND_CACHE = polygons
    return polygons


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _project(
    lon: float,
    lat: float,
    *,
    lon_min: float,
    lon_max: float,
    lat_min: float,
    lat_max: float,
    left: int,
    top: int,
    width: int,
    height: int,
) -> Tuple[int, int]:
    x = left + int((lon - lon_min) / max(lon_max - lon_min, 1e-6) * width)
    y = top + int((lat_max - lat) / max(lat_max - lat_min, 1e-6) * height)
    return x, y


def _draw_polygon(
    draw: ImageDraw.ImageDraw,
    points: Sequence[Tuple[float, float]],
    bounds: Dict[str, float],
    box: Tuple[int, int, int, int],
    *,
    fill: Optional[Tuple[int, ...]] = None,
    outline: Tuple[int, ...] = (180, 180, 190),
    width: int = 1,
) -> None:
    left, top, w, h = box
    xy = [
        _project(
            lon,
            lat,
            lon_min=bounds["lon_min"],
            lon_max=bounds["lon_max"],
            lat_min=bounds["lat_min"],
            lat_max=bounds["lat_max"],
            left=left,
            top=top,
            width=w,
            height=h,
        )
        for lon, lat in points
    ]
    if len(xy) >= 3:
        draw.polygon(xy, fill=fill, outline=outline)
        if width > 1:
            # Single thicker outline pass (avoid double-stroke ghosting).
            draw.line(xy + [xy[0]], fill=outline, width=width)


def _lookup_city_coords(name: str) -> Optional[Dict[str, Any]]:
    from calculators.locational_calculator import GLOBAL_HUBS, INDIA_METROS

    needle = str(name or "").strip().lower()
    if not needle:
        return None
    for row in list(INDIA_METROS) + list(GLOBAL_HUBS):
        if str(row.get("name") or "").strip().lower() == needle:
            return dict(row)
    return None


def _pick_cities(pack: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    scope = str(pack.get("location_scope") or "india").lower()
    top = list(pack.get("top_cities") or [])
    ranked = list(pack.get("all_cities_ranked") or [])

    def _with_coords(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(row, dict):
            return None
        if row.get("latitude") is not None and row.get("longitude") is not None:
            return row
        found = _lookup_city_coords(str(row.get("name") or ""))
        if not found:
            return None
        merged = dict(found)
        merged.update({k: v for k, v in row.items() if v is not None})
        return merged

    good: List[Dict[str, Any]] = []
    for row in top[:6]:
        full = _with_coords(row) if isinstance(row, dict) else None
        if full:
            good.append(full)

    good_names = {str(c.get("name") or "") for c in good}
    caution: List[Dict[str, Any]] = []
    for row in reversed(ranked):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "")
        if not name or name in good_names:
            continue
        full = _with_coords(row)
        if not full:
            continue
        caution.append(full)
        if len(caution) >= 3:
            break

    if scope == "both":
        india = [_with_coords(c) for c in (pack.get("top_cities_india") or []) if isinstance(c, dict)]
        abroad = [_with_coords(c) for c in (pack.get("top_cities_abroad") or []) if isinstance(c, dict)]
        merged: List[Dict[str, Any]] = []
        seen = set()
        for c in [x for x in india + abroad if x] + good:
            name = str(c.get("name") or "")
            if not name or name in seen:
                continue
            seen.add(name)
            merged.append(c)
        good = merged[:6]

    return good, caution


def _bounds_for_scope(scope: str, cities: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    # Always use fixed frames so land polygons keep a recognizable shape.
    if scope == "india":
        return {"lon_min": 67.0, "lon_max": 98.5, "lat_min": 6.5, "lat_max": 37.5}
    # abroad + both: full equirectangular world (exclude deep Antarctica strip)
    return {"lon_min": -170.0, "lon_max": 180.0, "lat_min": -50.0, "lat_max": 72.0}


def _fit_map_box(
    bounds: Dict[str, float],
    panel_left: int,
    panel_top: int,
    panel_w: int,
    panel_h: int,
) -> Tuple[int, int, int, int]:
    """Letterbox the geographic frame inside the panel to preserve aspect ratio."""
    geo_w = max(bounds["lon_max"] - bounds["lon_min"], 1e-6)
    geo_h = max(bounds["lat_max"] - bounds["lat_min"], 1e-6)
    geo_aspect = geo_w / geo_h
    panel_aspect = panel_w / max(panel_h, 1)
    if panel_aspect > geo_aspect:
        height = panel_h
        width = max(1, int(round(height * geo_aspect)))
        left = panel_left + (panel_w - width) // 2
        top = panel_top
    else:
        width = panel_w
        height = max(1, int(round(width / geo_aspect)))
        left = panel_left
        top = panel_top + (panel_h - height) // 2
    return left, top, width, height


def render_locational_map_png_bytes(pack: Dict[str, Any]) -> Optional[bytes]:
    if not isinstance(pack, dict):
        return None
    scope = str(pack.get("location_scope") or "india").lower()
    good, caution = _pick_cities(pack)
    if not good and not caution:
        return None

    # Render at 2x then downscale for smoother coastlines/labels.
    scale = 2
    width, height = 960 * scale, 720 * scale
    img = Image.new("RGB", (width, height), (246, 243, 236))
    draw = ImageDraw.Draw(img)

    title_font = _font(28 * scale)
    label_font = _font(15 * scale)
    small_font = _font(14 * scale)

    title = {
        "india": "Favorable places in India",
        "abroad": "Favorable places abroad",
        "both": "Favorable places (India + abroad)",
    }.get(scope, "Favorable places")
    draw.text((28 * scale, 22 * scale), title, fill=(40, 36, 32), font=title_font)

    panel_left, panel_top = 40 * scale, 70 * scale
    panel_right, panel_bottom = width - 40 * scale, height - 90 * scale
    panel_w, panel_h = panel_right - panel_left, panel_bottom - panel_top
    bounds = _bounds_for_scope(scope, good + caution)

    # India uses the full panel. World maps letterbox to keep continents recognizable.
    if scope == "india":
        map_left, map_top, map_w, map_h = panel_left, panel_top, panel_w, panel_h
    else:
        map_left, map_top, map_w, map_h = _fit_map_box(bounds, panel_left, panel_top, panel_w, panel_h)

    # Map panel background (ocean)
    draw.rounded_rectangle(
        [panel_left - 8 * scale, panel_top - 8 * scale, panel_right + 8 * scale, panel_bottom + 8 * scale],
        radius=16 * scale,
        fill=(214, 228, 238),
        outline=(198, 210, 220),
        width=2 * scale,
    )

    # Draw land onto a dedicated surface so polygons never spill outside the frame.
    map_img = Image.new("RGB", (map_w, map_h), (205, 222, 234))
    map_draw = ImageDraw.Draw(map_img)
    local_box = (0, 0, map_w, map_h)

    if scope == "india":
        _draw_polygon(
            map_draw,
            _load_india_outline(),
            bounds,
            local_box,
            fill=(214, 226, 214),
            outline=(90, 120, 95),
            width=max(2, scale),
        )
    else:
        for poly in _load_world_land():
            _draw_polygon(
                map_draw,
                poly,
                bounds,
                local_box,
                fill=(218, 226, 216),
                outline=(130, 148, 136),
                width=1,
            )

    def _plot_on(target_draw: ImageDraw.ImageDraw, cities: Sequence[Dict[str, Any]], color: Tuple[int, int, int], ring: Tuple[int, int, int]) -> None:
        for city in cities:
            try:
                lon = float(city["longitude"])
                lat = float(city["latitude"])
            except (KeyError, TypeError, ValueError):
                continue
            x, y = _project(
                lon,
                lat,
                lon_min=bounds["lon_min"],
                lon_max=bounds["lon_max"],
                lat_min=bounds["lat_min"],
                lat_max=bounds["lat_max"],
                left=0,
                top=0,
                width=map_w,
                height=map_h,
            )
            r = 7 * scale if scope == "india" else 6 * scale
            target_draw.ellipse([x - r, y - r, x + r, y + r], fill=color, outline=ring, width=max(2, scale))
            name = str(city.get("name") or "")
            if name:
                target_draw.text((x + 9 * scale, y - 9 * scale), name, fill=(35, 35, 40), font=label_font)

    _plot_on(map_draw, caution, (196, 80, 70), (120, 40, 35))
    _plot_on(map_draw, good, (46, 140, 90), (20, 80, 45))
    img.paste(map_img, (map_left, map_top))
    draw.rectangle(
        [map_left, map_top, map_left + map_w, map_top + map_h],
        outline=(180, 196, 208),
        width=max(1, scale),
    )

    # Legend
    legend_y = height - 58 * scale
    draw.ellipse(
        [40 * scale, legend_y, 56 * scale, legend_y + 16 * scale],
        fill=(46, 140, 90),
        outline=(20, 80, 45),
        width=max(2, scale),
    )
    draw.text((64 * scale, legend_y - 1 * scale), "Favorable", fill=(40, 36, 32), font=small_font)
    draw.ellipse(
        [180 * scale, legend_y, 196 * scale, legend_y + 16 * scale],
        fill=(196, 80, 70),
        outline=(120, 40, 35),
        width=max(2, scale),
    )
    draw.text((204 * scale, legend_y - 1 * scale), "Less favorable", fill=(40, 36, 32), font=small_font)
    draw.text(
        (400 * scale, legend_y - 1 * scale),
        "Vedic relocated-chart shortlist",
        fill=(110, 105, 98),
        font=small_font,
    )

    if scale > 1:
        img = img.resize((960, 720), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def render_locational_map_data_uri(pack: Dict[str, Any]) -> Optional[str]:
    try:
        png = render_locational_map_png_bytes(pack)
        if not png:
            return None
        b64 = base64.b64encode(png).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        logger.exception("locational_map_render_failed")
        return None


def render_and_store_locational_map_url(pack: Dict[str, Any]) -> Optional[str]:
    """
    Render map PNG, upload to GCS, return public https URL.
    Falls back to data URI only when upload is unavailable (local/dev).
    """
    try:
        png = render_locational_map_png_bytes(pack)
        if not png:
            return None
    except Exception:
        logger.exception("locational_map_render_failed")
        return None

    scope = str(pack.get("location_scope") or "india").strip().lower() or "india"
    goal = str(pack.get("goal_category") or "general").strip().lower() or "general"
    filename_stem = f"locational-{scope}-{goal}"

    try:
        from utils.chat_summary_image_gcs import upload_chat_summary_png

        url = upload_chat_summary_png(png, filename_stem=filename_stem, folder="chat-summary/locational")
        if url:
            return url
    except Exception:
        logger.exception("locational_map_gcs_upload_failed")

    # Dev fallback so local chat still shows a map when GCS creds/bucket are missing.
    allow_data_uri = (os.getenv("CHAT_SUMMARY_IMAGE_ALLOW_DATA_URI") or "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if allow_data_uri:
        logger.warning("locational_map_using_data_uri_fallback")
        b64 = base64.b64encode(png).decode("ascii")
        return f"data:image/png;base64,{b64}"
    return None


def maybe_attach_locational_summary_image(
    result: Dict[str, Any],
    astrological_context: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Attach map as summary_image when locational pack is present and image missing."""
    if not isinstance(result, dict):
        return result
    if result.get("summary_image"):
        return result
    ctx = astrological_context if isinstance(astrological_context, dict) else {}
    pack = ctx.get("locational_recommendation")
    if not isinstance(pack, dict):
        return result
    image_ref = render_and_store_locational_map_url(pack)
    if image_ref:
        result["summary_image"] = image_ref
        result["summary_image_kind"] = "locational_map"
    return result
