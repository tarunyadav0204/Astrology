"""Classical Shodashvarga (16 divisional charts) shared by Janam Kundli PDF."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Classical Parashara Shodashvarga order (D1–D60).
SHODASHVARGA_DIVISIONS: Tuple[int, ...] = (
    1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60,
)

# Dense atlas layout: 3 charts per row, 3 rows per page (9 charts / page).
SHODASHVARGA_CHARTS_PER_ROW = 3
SHODASHVARGA_CHARTS_PER_PAGE = 9

# (English short name, Hindi short name, English significance, Hindi significance)
SHODASHVARGA_META: Dict[int, Tuple[str, str, str, str]] = {
    1: ("Rashi", "राशि", "Overall life and personality", "संपूर्ण जीवन और व्यक्तित्व"),
    2: ("Hora", "होरा", "Wealth and material resources", "धन और भौतिक संसाधन"),
    3: ("Drekkana", "द्रेष्काण", "Siblings, courage, and effort", "सहोदर, साहस और प्रयास"),
    4: ("Chaturthamsa", "चतुर्थांश", "Home, property, and fortune", "घर, संपत्ति और भाग्य"),
    7: ("Saptamsa", "सप्तमांश", "Children and creative lineage", "संतान और रचनात्मक वंश"),
    9: ("Navamsa", "नवांश", "Marriage, dharma, and maturity", "विवाह, धर्म और परिपक्वता"),
    10: ("Dasamsa", "दशमांश", "Career, status, and karma in action", "करियर, प्रतिष्ठा और कर्म"),
    12: ("Dwadasamsa", "द्वादशांश", "Parents and ancestral line", "माता-पिता और पैतृक रेखा"),
    16: ("Shodasamsa", "षोडशांश", "Comforts, vehicles, and ease", "सुख, वाहन और सुविधाएँ"),
    20: ("Vimsamsa", "विंशांश", "Spiritual practice and devotion", "साधना और भक्ति"),
    24: ("Chaturvimsamsa", "चतुर्विंशांश", "Education and learning", "शिक्षा और अधिगम"),
    27: ("Saptavimsamsa", "सप्तविंशांश", "Strengths and weaknesses", "शक्ति और कमजोरी"),
    30: ("Trimsamsa", "त्रिंशांश", "Difficulties and vulnerabilities", "कष्ट और कमजोरियाँ"),
    40: ("Khavedamsa", "खवेदांश", "Maternal lineage themes", "मातृ पक्ष की प्रवृत्तियाँ"),
    45: ("Akshavedamsa", "अक्षवेदांश", "Paternal lineage themes", "पितृ पक्ष की प्रवृत्तियाँ"),
    60: ("Shashtyamsa", "षष्ट्यंश", "Deep karmic residue", "गहन कर्म अवशेष"),
}


def shodashvarga_chart_ref(division: int) -> str:
    return f"native_d{int(division)}"


def shodashvarga_label(division: int, *, hindi: bool = False) -> str:
    meta = SHODASHVARGA_META.get(int(division))
    if not meta:
        return f"डी-{division}" if hindi else f"D{division}"
    name = meta[1] if hindi else meta[0]
    if hindi:
        return f"डी-{division} {name}"
    return f"D{division} {name}"


def shodashvarga_atlas_title_subtitle(
    page_index: int,
    total_pages: int,
    *,
    hindi: bool = False,
) -> Tuple[str, str]:
    if hindi:
        return (
            f"षोडशवर्ग कुंडलियाँ ({page_index}/{total_pages})",
            "पारंपरिक सोलह वर्ग कुंडलियाँ",
        )
    return (
        f"Shodashvarga Charts ({page_index}/{total_pages})",
        "Classical sixteen varga charts",
    )


def build_shodashvarga_blueprint_pages() -> List[Dict[str, Any]]:
    """Pack Shodashvarga charts densely: several per row across atlas pages."""
    divisions = list(SHODASHVARGA_DIVISIONS)
    chunks: List[List[int]] = [
        divisions[i: i + SHODASHVARGA_CHARTS_PER_PAGE]
        for i in range(0, len(divisions), SHODASHVARGA_CHARTS_PER_PAGE)
    ]
    total_pages = max(1, len(chunks))
    pages: List[Dict[str, Any]] = []
    for index, chunk in enumerate(chunks, start=1):
        pages.append({
            "key": f"shodashvarga_{index}",
            "charts": [shodashvarga_chart_ref(d) for d in chunk],
            "divisions": chunk,
            "atlas_page": index,
            "atlas_pages": total_pages,
            "charts_per_row": SHODASHVARGA_CHARTS_PER_ROW,
            "chart_compact": True,
        })
    return pages


def build_janam_kundli_blueprint() -> List[Dict[str, Any]]:
    """Full Janam Kundli page spine with continuous Shodashvarga atlas after D10."""
    head: List[Dict[str, Any]] = [
        {"key": "cover", "charts": ["native_d1"]},
        # Merged into cover for PDF density; kept for API/LLM section keys.
        {"key": "birth_panchang", "charts": [], "skip_render": True},
        {"key": "primary_charts", "charts": ["native_moon"]},
        {"key": "navamsha", "charts": ["native_d9"]},
        {"key": "planetary_positions", "charts": []},
        {"key": "chalit_chart", "charts": ["native_chalit"]},
        {"key": "dashamsha", "charts": ["native_d10"]},
    ]
    atlas = build_shodashvarga_blueprint_pages()
    tail: List[Dict[str, Any]] = [
        {"key": "ashtakavarga", "charts": []},
        {"key": "past_life_blueprint", "charts": []},
        {"key": "personality", "charts": []},
        {"key": "emotional_blueprint", "charts": []},
        {"key": "education_intellect", "charts": []},
        {"key": "career_profession", "charts": ["native_d10"]},
        {"key": "wealth_finances", "charts": []},
        {"key": "love_relationships", "charts": ["native_d9"]},
        {"key": "health_profiles", "charts": []},
        {"key": "major_yogas", "charts": []},
        {"key": "dosha_checks", "charts": []},
        {"key": "sade_sati", "charts": []},
        {"key": "dasha_tree", "charts": []},
        {"key": "present_phase", "charts": []},
        {"key": "gemstones", "charts": []},
        {"key": "practical_remedies", "charts": []},
        {"key": "closing_guidance", "charts": []},
    ]
    out: List[Dict[str, Any]] = []
    for index, bp in enumerate(head + atlas + tail, start=1):
        row = dict(bp)
        row["num"] = index
        out.append(row)
    return out


def is_shodashvarga_page_key(key: str) -> bool:
    return str(key or "").startswith("shodashvarga")


def chart_manifest_refs(style: str) -> List[Dict[str, Any]]:
    refs: List[Dict[str, Any]] = [
        {"ref": "native_d1", "style": style},
        {"ref": "native_moon", "style": style},
        {"ref": "native_chalit", "style": style},
    ]
    seen = {"native_d1"}
    for division in SHODASHVARGA_DIVISIONS:
        ref = shodashvarga_chart_ref(division)
        if ref in seen:
            continue
        seen.add(ref)
        refs.append({"ref": ref, "style": style})
    return refs
