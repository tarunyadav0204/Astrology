"""Unicode font registration for premium report PDFs.

Helvetica cannot render Hindi/Tamil/etc. We embed OFL fonts from reports/fonts/
and pick a family from the report language.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"

# language -> (regular filename, bold filename)
_LANGUAGE_FONT_FILES: Dict[str, Tuple[str, str]] = {
    "hindi": ("Mukta-Regular.ttf", "Mukta-Bold.ttf"),
    "marathi": ("Mukta-Regular.ttf", "Mukta-Bold.ttf"),
    "tamil": ("NotoSansTamil-Regular.ttf", "NotoSansTamil-Bold.ttf"),
    "telugu": ("NotoSansTelugu-Regular.ttf", "NotoSansTelugu-Bold.ttf"),
    "gujarati": ("NotoSansGujarati-Regular.ttf", "NotoSansGujarati-Bold.ttf"),
    "russian": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    "german": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    "french": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    "chinese": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
    "mandarin": ("NotoSans-Regular.ttf", "NotoSans-Bold.ttf"),
}

# Pair with Noto Sans for ASCII/Latin runs.
# Hindi/Marathi Mukta + HarfBuzz mis-shapes Latin clusters like "st" (trust, AstroRoshni).
_NEEDS_LATIN_FALLBACK = frozenset({"tamil", "telugu", "gujarati", "hindi", "marathi"})

_INDIC_CHAR = re.compile(
    r"[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF"
    r"\u0B00-\u0B7F\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]"
)


@dataclass(frozen=True)
class PdfFontSet:
    regular: str
    bold: str
    latin_regular: str
    latin_bold: str
    needs_latin_fallback: bool

    @property
    def family(self) -> str:
        return self.regular


def _ttfont_supports_shapable() -> bool:
    """ReportLab < 4.4 rejects TTFont(..., shapable=...)."""
    try:
        import inspect

        return "shapable" in inspect.signature(TTFont.__init__).parameters
    except Exception:
        return False


def _make_ttfont(name: str, path: Path, *, shapable: bool) -> TTFont:
    """Register-compatible TTFont; older ReportLab builds omit the shapable kwarg.

    Always try/except — do not trust signature inspection alone (stale venv / odd wraps).
    """
    try:
        return TTFont(name, str(path), shapable=bool(shapable))
    except TypeError as exc:
        if "shapable" not in str(exc):
            raise
        return TTFont(name, str(path))


def _register_pair(
    family: str,
    regular_path: Path,
    bold_path: Path,
    *,
    shapable: Optional[bool] = None,
) -> Tuple[str, str]:
    """Register TTF pair. shapable=True enables HarfBuzz for Indic scripts when uharfbuzz is installed."""
    regular_name = family
    bold_name = f"{family}-Bold"
    if shapable is None:
        # ReportLab shapes Devanagari/Tamil/etc. only when uharfbuzz is importable
        # *and* this ReportLab build accepts shapable=.
        has_harfbuzz = False
        try:
            import uharfbuzz  # noqa: F401

            has_harfbuzz = True
        except Exception:
            logger.warning(
                "uharfbuzz not installed — Indic PDF text may show incorrect conjuncts/matras. "
                "Install with: pip install uharfbuzz"
            )
        supports_shapable = _ttfont_supports_shapable()
        if has_harfbuzz and not supports_shapable:
            logger.warning(
                "ReportLab TTFont has no shapable= support — upgrade reportlab>=4.4 for Hindi shaping."
            )
        shapable = bool(has_harfbuzz and supports_shapable)

    if regular_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(_make_ttfont(regular_name, regular_path, shapable=bool(shapable)))
    if bold_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(_make_ttfont(bold_name, bold_path, shapable=bool(shapable)))
    try:
        registerFontFamily(family, normal=regular_name, bold=bold_name)
    except Exception:
        # Family may already be registered from a previous call.
        pass
    return regular_name, bold_name


@lru_cache(maxsize=1)
def _register_latin_fallback() -> Tuple[str, str]:
    regular = _FONTS_DIR / "NotoSans-Regular.ttf"
    bold = _FONTS_DIR / "NotoSans-Bold.ttf"
    if regular.is_file() and bold.is_file():
        # Never shape the Latin fallback — avoids "st"/"fi" ligature corruption.
        return _register_pair("ARSans", regular, bold, shapable=False)
    return "Helvetica", "Helvetica-Bold"


@lru_cache(maxsize=16)
def resolve_pdf_fonts(language: Optional[str]) -> PdfFontSet:
    """Return registered ReportLab font names for a report language."""
    lang = (language or "english").strip().lower() or "english"
    latin_regular, latin_bold = _register_latin_fallback()

    if lang in {"english", "en"}:
        return PdfFontSet(
            regular="Helvetica",
            bold="Helvetica-Bold",
            latin_regular="Helvetica",
            latin_bold="Helvetica-Bold",
            needs_latin_fallback=False,
        )

    files = _LANGUAGE_FONT_FILES.get(lang)
    if not files:
        # Prefer Unicode Noto Sans over Helvetica for unknown non-English languages.
        return PdfFontSet(
            regular=latin_regular,
            bold=latin_bold,
            latin_regular=latin_regular,
            latin_bold=latin_bold,
            needs_latin_fallback=False,
        )

    regular_path = _FONTS_DIR / files[0]
    bold_path = _FONTS_DIR / files[1]
    if not regular_path.is_file() or not bold_path.is_file():
        logger.warning(
            "Missing PDF fonts for language=%s (%s / %s); falling back to %s",
            lang,
            regular_path.name,
            bold_path.name,
            latin_regular,
        )
        return PdfFontSet(
            regular=latin_regular,
            bold=latin_bold,
            latin_regular=latin_regular,
            latin_bold=latin_bold,
            needs_latin_fallback=False,
        )

    family = f"ARLang_{lang}"
    try:
        regular_name, bold_name = _register_pair(family, regular_path, bold_path)
    except Exception as exc:
        logger.warning("Failed to register PDF fonts for %s: %s", lang, exc)
        return PdfFontSet(
            regular=latin_regular,
            bold=latin_bold,
            latin_regular=latin_regular,
            latin_bold=latin_bold,
            needs_latin_fallback=False,
        )

    return PdfFontSet(
        regular=regular_name,
        bold=bold_name,
        latin_regular=latin_regular,
        latin_bold=latin_bold,
        needs_latin_fallback=lang in _NEEDS_LATIN_FALLBACK and latin_regular != regular_name,
    )


def escape_pdf_text(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def rich_text_for_fonts(text: str, fonts: PdfFontSet, *, bold: bool = False) -> str:
    """Escape text and, when needed, route Latin-only runs to the Latin fallback font.

    Important: do **not** insert mid-string ``<font>`` switches on mixed Indic lines.
    ReportLab ``Paragraph(shaping=1)`` corrupts those splits — e.g.
    ``शनि (Saturn) 10वें`` becomes ``(dm¡¢~z(`` plus tofu after digits.
    Latin-only chrome ("Prepared with AstroRoshni", "trust") still uses the
    non-shapable Latin face so Mukta+HarfBuzz does not ligature-corrupt ``st``.
    """
    value = text or ""
    if not fonts.needs_latin_fallback:
        return escape_pdf_text(value)

    latin = fonts.latin_bold if bold else fonts.latin_regular
    # Mixed Indic + Latin/digits: keep one shapable primary run (style fontName).
    if _INDIC_CHAR.search(value):
        return escape_pdf_text(value)

    return f'<font name="{latin}">{escape_pdf_text(value)}</font>'
