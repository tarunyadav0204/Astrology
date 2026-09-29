"""Keep the original scene and frame. Draw a shaped Devanagari Pitri chart."""

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path("/Users/tarunydv/Desktop/Code/AstrologyApp")
SRC = "/Users/tarunydv/.cursor/projects/Users-tarunydv-Desktop-Code-AstrologyApp/assets/WhatsApp_Image_2026-09-29_at_5.17.27_PM-9fb6f5a0-2637-415b-9d2a-cb433ddd5711.jpg"
OUT = ROOT / "pitri-shapa-chart.png"
LABELS = ROOT / "backend/scripts/_pitri_labels"
SWIFT = ROOT / "backend/scripts/render_devanagari.swift"
SCALE = 2

INK = (62, 32, 18)
RULE = (156, 36, 32)
POLYGONS = {
    1: [(200, 0), (300, 100), (200, 200), (100, 100)],
    2: [(0, 0), (200, 0), (100, 100)],
    3: [(0, 0), (100, 100), (0, 200)],
    4: [(0, 200), (100, 100), (200, 200), (100, 300)],
    5: [(0, 200), (100, 300), (0, 400)],
    6: [(0, 400), (100, 300), (200, 400)],
    7: [(200, 200), (300, 300), (200, 400), (100, 300)],
    8: [(200, 400), (300, 300), (400, 400)],
    9: [(300, 300), (400, 200), (400, 400)],
    10: [(200, 200), (300, 100), (400, 200), (300, 300)],
    11: [(300, 100), (400, 0), (400, 200)],
    12: [(200, 0), (400, 0), (300, 100)],
}
HOUSES = {
    1: ("मेष", ["सूर्य 10°"], True),
    2: ("वृष", ["केतु 15°"], False),
    3: ("मिथुन", ["चंद्र 18°"], False),
    4: ("कर्क", [], False),
    5: ("सिंह", ["मंगल 8°", "शनि 22°"], True),
    6: ("कन्या", ["शुक्र 14°"], False),
    7: ("तुला", ["बुध 6°"], False),
    8: ("वृश्चिक", ["राहु 15°"], True),
    9: ("धनु", [], False),
    10: ("मकर", [], False),
    11: ("कुंभ", [], False),
    12: ("मीन", ["गुरु 12°"], True),
}


def scaled(box):
    return tuple(int(v * SCALE) for v in box)


def centroid(points):
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def paperize(region):
    low = np.asarray(region.filter(ImageFilter.GaussianBlur(radius=46))).astype(np.float32)
    mean = low.mean(axis=(0, 1), keepdims=True)
    low = mean + (low - mean) * 0.62
    grain = np.random.default_rng(3).normal(0, 2.8, low.shape)
    return Image.fromarray(np.clip(low + grain, 0, 255).astype(np.uint8))


def paste_feather(dest, patch, box, fade=12):
    mask = Image.new("L", patch.size, 255)
    draw = ImageDraw.Draw(mask)
    width, height = patch.size
    for i in range(fade):
        draw.rectangle([i, i, width - 1 - i, height - 1 - i], outline=int(255 * (i / fade)))
    dest.paste(patch, (box[0], box[1]), mask)


def render_labels():
    jobs = [
        {"name": "title", "text": "जन्म कुण्डली - पितृ दोष", "size": 34, "weight": "bold"},
        {"name": "footer", "text": "BPHS 83.27 · सूर्य भाव 1 · मंगल-शनि भाव 5 · राहु भाव 8 · गुरु भाव 12", "size": 16, "weight": "medium"},
        {"name": "caption", "text": "पितृ शाप: सूर्य लग्न में, मंगल और शनि पंचम में, राहु अष्टम में, गुरु द्वादश में।", "size": 17, "weight": "semibold"},
    ]
    for house, (sign, planets, marked) in HOUSES.items():
        jobs.append({"name": f"sign-{house}", "text": sign, "size": 15, "weight": "soft"})
        for index, planet in enumerate(planets):
            jobs.append({
                "name": f"planet-{house}-{index}",
                "text": planet,
                "size": 14,
                "weight": "rule" if marked else "semibold",
            })
    job_path = LABELS / "jobs.json"
    LABELS.mkdir(parents=True, exist_ok=True)
    job_path.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["swift", str(SWIFT), str(job_path), str(LABELS)], check=True)


def paste_center(base, name, center):
    image = Image.open(LABELS / f"{name}.png").convert("RGBA")
    x = int(center[0] - image.width / 2)
    y = int(center[1] - image.height / 2)
    base.paste(image, (x, y), image)


def main():
    render_labels()
    base = Image.open(SRC).convert("RGB").resize(
        (Image.open(SRC).width * SCALE, Image.open(SRC).height * SCALE),
        Image.Resampling.LANCZOS,
    )
    base = base.convert("RGBA")
    sheet = scaled((248, 62, 776, 430))
    paper = paperize(base.crop(sheet).convert("RGB")).convert("RGBA")
    paste_feather(base, paper, sheet, fade=12)

    draw = ImageDraw.Draw(base)
    sx0, sy0, sx1, sy1 = sheet
    paste_center(base, "title", ((sx0 + sx1) / 2, sy0 + 28))

    chart_size = 470
    origin_x = (sx0 + sx1) / 2 - chart_size / 2
    origin_y = sy0 + 78
    scale = chart_size / 400
    for house, points in POLYGONS.items():
        plotted = [(origin_x + px * scale, origin_y + py * scale) for px, py in points]
        _, planets, marked = HOUSES[house]
        draw.line(plotted + [plotted[0]], fill=RULE if marked else INK, width=3 if marked else 2)
        cx, cy = centroid(points)
        x = origin_x + (cx + (200 - cx) * 0.18) * scale
        y = origin_y + (cy + (200 - cy) * 0.12) * scale
        lines = [f"sign-{house}"] + [f"planet-{house}-{index}" for index in range(len(planets))]
        line_h = 18
        top = y - (len(lines) - 1) * line_h / 2
        for index, name in enumerate(lines):
            paste_center(base, name, (x, top + index * line_h))

    paste_center(base, "footer", ((sx0 + sx1) / 2, sy1 - 28))

    scroll = scaled((286, 436, 734, 478))
    scroll_paper = paperize(base.crop(scroll).convert("RGB")).convert("RGBA")
    paste_feather(base, scroll_paper, scroll, fade=8)
    cx0, cy0, cx1, cy1 = scroll
    paste_center(base, "caption", ((cx0 + cx1) / 2, (cy0 + cy1) / 2))

    base.convert("RGB").save(OUT, quality=95)
    print(OUT)


if __name__ == "__main__":
    main()
