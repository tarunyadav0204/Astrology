#!/usr/bin/env python3
"""Compose AstroRoshni screenshots into Play Store-ready portrait artwork."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "public" / "images" / "Screehshots"
OUTPUT_DIR = ROOT / "public" / "images" / "play-store-theme-screenshots"
BACKGROUND = OUTPUT_DIR / "astroroshni-store-background.png"

CANVAS_SIZE = (1080, 1920)
PHONE_SIZE = (664, 1482)
PHONE_POSITION = (208, 386)
GOLD = "#DDBF78"
IVORY = "#FFF8EA"
SOFT_IVORY = "#D9C8C4"

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold.ttf"
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"

SCREENS = [
    (
        "Screenshot_20260812_232901.png",
        "01-meet-tara.png",
        "YOUR VEDIC GUIDE",
        "Meet Tara. Read your life.",
    ),
    (
        "Screenshot_20260812_232928.png",
        "02-ask-tara.png",
        "PRIVATE CHART-AWARE GUIDANCE",
        "Ask anything. Read your whole chart.",
    ),
    (
        "Screenshot_20260812_232942.png",
        "03-vedic-chart.png",
        "18 DIVISIONAL VIEWS",
        "Your complete Vedic chart.",
    ),
    (
        "Screenshot_20260812_233014.png",
        "04-dasha-timing.png",
        "DASHA TIMING",
        "Navigate every planetary period.",
    ),
    (
        "Screenshot_20260812_233147.png",
        "05-karma-analysis.png",
        "KARMA ANALYSIS",
        "Understand your deeper patterns.",
    ),
]


def cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize(
        (round(image.width * ratio), round(image.height * ratio)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def fit_font(text: str, font_path: str, max_size: int, max_width: int) -> ImageFont.FreeTypeFont:
    size = max_size
    while size > 20:
        font = ImageFont.truetype(font_path, size)
        if font.getlength(text) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, size)


def rounded_image(image: Image.Image, size: tuple[int, int], radius: int) -> Image.Image:
    fitted = cover(image.convert("RGB"), size).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    fitted.putalpha(mask)
    return fitted


def make_artwork(source_name: str, output_name: str, eyebrow: str, headline: str) -> None:
    background = cover(Image.open(BACKGROUND).convert("RGB"), CANVAS_SIZE).convert("RGBA")
    overlay = Image.new("RGBA", CANVAS_SIZE, (20, 1, 11, 38))
    canvas = Image.alpha_composite(background, overlay)
    draw = ImageDraw.Draw(canvas)

    brand_font = ImageFont.truetype(ARIAL, 22)
    eyebrow_font = ImageFont.truetype(ARIAL, 24)
    headline_font = fit_font(headline, GEORGIA_BOLD, 65, 900)

    draw.line((90, 74, 150, 74), fill=GOLD, width=3)
    draw.text((172, 60), "ASTROROSHNI", font=brand_font, fill=SOFT_IVORY, stroke_width=0)
    draw.text((90, 126), eyebrow, font=eyebrow_font, fill=GOLD, stroke_width=0)
    draw.text((88, 170), headline, font=headline_font, fill=IVORY, stroke_width=0)

    px, py = PHONE_POSITION
    pw, ph = PHONE_SIZE

    shadow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (px - 18, py - 14, px + pw + 18, py + ph + 20),
        radius=74,
        fill=(0, 0, 0, 180),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(26))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (px - 7, py - 7, px + pw + 7, py + ph + 7),
        radius=66,
        fill="#14020B",
        outline=GOLD,
        width=3,
    )

    screenshot = rounded_image(Image.open(SOURCE_DIR / source_name), PHONE_SIZE, 58)
    canvas.alpha_composite(screenshot, PHONE_POSITION)

    canvas.convert("RGB").save(OUTPUT_DIR / output_name, quality=96, optimize=True)


def make_contact_sheet() -> None:
    thumb_size = (270, 480)
    gap = 18
    sheet = Image.new("RGB", (thumb_size[0] * 5 + gap * 6, thumb_size[1] + gap * 2), "#18030D")
    x = gap
    for _, output_name, _, _ in SCREENS:
        thumb = Image.open(OUTPUT_DIR / output_name).resize(thumb_size, Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, gap))
        x += thumb_size[0] + gap
    sheet.save(OUTPUT_DIR / "preview-contact-sheet.jpg", quality=92, optimize=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BACKGROUND.exists():
        raise FileNotFoundError(f"Missing generated background: {BACKGROUND}")
    for screen in SCREENS:
        make_artwork(*screen)
    make_contact_sheet()
    print(f"Created {len(SCREENS)} Play Store screenshots in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
