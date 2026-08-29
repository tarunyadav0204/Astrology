"""Generate a factual, short-beat visual manifest around unchanged podcast audio."""

from __future__ import annotations

import html
import json
import logging
import os
import re
from typing import Any


logger = logging.getLogger(__name__)
ALLOWED_VISUAL_TYPES = {
    "opening", "natal_chart", "divisional_chart", "transit_chart", "house_highlight", "planet_highlight",
    "dasha_timeline", "date_window", "comparison", "action_steps", "warning",
    "key_takeaway", "closing", "zodiac_spotlight", "aspect_lines", "conjunction",
    "balance", "quote", "myth_reveal", "decision_path", "constellation_summary",
    "host_focus", "celestial_interlude", "topic_cards", "ashtakavarga_table",
    "house_activation_map",
}
SUPPORTED_DIVISIONS = {2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}
DIVISION_ALIASES = {
    2: ("hora", "होरा"), 3: ("drekkana", "dreshkana", "द्रेष्काण"), 4: ("chaturthamsa", "चतुर्थांश"),
    7: ("saptamsa", "saptamsha", "सप्तमांश"), 9: ("navamsa", "navamsha", "navansh", "नवांश"),
    10: ("dasamsa", "dashamsa", "dashamsha", "दशमांश"), 12: ("dwadasamsa", "dwadashamsa", "द्वादशांश"),
    16: ("shodasamsa", "shodashamsa"), 20: ("vimsamsa", "vimshamsa"),
    24: ("chaturvimsamsa", "chaturvimshamsa", "चतुर्विंशांश"), 27: ("saptavimsamsa", "saptavimshamsa"),
    30: ("trimsamsa", "trimshamsa", "त्रिंशांश"), 40: ("khavedamsa", "khavedamsha"),
    45: ("akshavedamsa", "akshavedamsha"), 60: ("shashtyamsa", "shashtiamsha", "षष्ट्यांश"),
}
PLANET_NAMES = (
    "Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu", "Uranus", "Neptune", "Pluto",
)
PLANET_ALIASES = {
    "लग्न": "Ascendant", "सूर्य": "Sun", "रवि": "Sun", "चंद्र": "Moon", "चन्द्र": "Moon",
    "मंगल": "Mars", "बुध": "Mercury", "गुरु": "Jupiter", "बृहस्पति": "Jupiter",
    "शुक्र": "Venus", "शनि": "Saturn", "राहु": "Rahu", "केतु": "Ketu",
}
HINDI_HOUSE_NUMBERS = {
    1: ("प्रथम", "पहला", "पहले"), 2: ("द्वितीय", "दूसरा", "दूसरे"),
    3: ("तृतीय", "तीसरा", "तीसरे"), 4: ("चतुर्थ", "चौथा", "चौथे"),
    5: ("पंचम", "पाँचवाँ", "पांचवां", "पाँचवें"), 6: ("षष्ठ", "छठा", "छठे"),
    7: ("सप्तम", "सातवाँ", "सातवें"), 8: ("अष्टम", "आठवाँ", "आठवें"),
    9: ("नवम", "नौवाँ", "नौवें"), 10: ("दशम", "दसवाँ", "दसवें"),
    11: ("एकादश", "ग्यारहवाँ", "ग्यारहवें"), 12: ("द्वादश", "बारहवाँ", "बारहवें"),
}
TRANSITIONS = ("reveal", "crossfade", "rise", "slide_left", "slide_right", "zoom")
ACCENTS = ("gold", "rose", "violet", "ember")
HINDI_SCENE_COPY = {
    "opening": ("आपकी व्यक्तिगत ज्योतिष कहानी", "आइए कुंडली के मुख्य संकेतों को समझें।"),
    "natal_chart": ("जन्म कुंडली का मुख्य संकेत", "यह पैटर्न आपकी कुंडली की मूल दिशा दिखाता है।"),
    "divisional_chart": ("वर्ग कुंडली का संकेत", "इस विषय की संबंधित वर्ग कुंडली को ध्यान से देखें।"),
    "transit_chart": ("वर्तमान गोचर का प्रभाव", "समय के साथ बदलते संकेतों पर ध्यान दें।"),
    "house_highlight": ("सक्रिय भाव का संकेत", "इस भाव से जुड़े जीवन क्षेत्र को ध्यान से देखें।"),
    "planet_highlight": ("ग्रह की प्रमुख भूमिका", "यह ग्रह इस विषय की दिशा को प्रभावित करता है।"),
    "dasha_timeline": ("दशा और समय का क्रम", "इस अवधि के संकेतों को क्रम से समझें।"),
    "date_window": ("महत्वपूर्ण समय अवधि", "इस समय में सोच-समझकर आगे बढ़ें।"),
    "action_steps": ("आपके लिए व्यावहारिक कदम", "छोटे और स्पष्ट कदमों से शुरुआत करें।"),
    "warning": ("यहाँ सावधानी जरूरी है", "निर्णय लेने से पहले पूरे संकेत को समझें।"),
    "closing": ("आज की मुख्य सीख", "सबसे उपयोगी संकेत को अपने साथ रखें।"),
    "ashtakavarga_table": ("अष्टकवर्ग शक्ति तालिका", "भावों के SAV और ग्रहवार BAV बिंदुओं को साथ देखें।"),
    "house_activation_map": ("सक्रिय भाव मानचित्र", "जन्म संकेत, दशा, गोचर और अष्टकवर्ग का संयुक्त प्रभाव देखें।"),
}
HINDI_DEFAULT_COPY = ("कुंडली का महत्वपूर्ण संकेत", "इस पैटर्न को ध्यान से समझें और फिर आगे बढ़ें।")


def visual_source(
    script: str,
    segments: list[tuple[str, str]],
    message_content: str = "",
    segment_audio_sizes: list[int] | None = None,
    segment_audio_durations_ms: list[int] | None = None,
    birth_chart_id: int | None = None,
) -> dict[str, Any]:
    audio_sizes = segment_audio_sizes or []
    audio_durations = segment_audio_durations_ms or []
    payload = {
        "version": 3,
        "script": script or "",
        "message_content": message_content or "",
        "segments": [
            {
                "index": index,
                "speaker": role,
                "text": text,
                # Every segment uses the same TTS encoding. Byte size is a
                # legacy duration proxy; frame duration is exact when present.
                "audio_weight": int(audio_sizes[index]) if index < len(audio_sizes) else 0,
                "audio_duration_ms": int(audio_durations[index]) if index < len(audio_durations) else 0,
            }
            for index, (role, text) in enumerate(segments)
            if str(text or "").strip()
        ],
    }
    if birth_chart_id is not None:
        payload["birth_chart_id"] = int(birth_chart_id)
    return payload


def mp3_duration_ms(audio: bytes) -> int:
    """Read MPEG Layer III frame durations without external media tools."""
    data = bytes(audio or b"")
    position = 0
    duration_ms = 0.0
    frame_count = 0
    bitrate_v1 = (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0)
    bitrate_v2 = (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0)
    sample_rates = {
        3: (44100, 48000, 32000),  # MPEG-1
        2: (22050, 24000, 16000),  # MPEG-2
        0: (11025, 12000, 8000),   # MPEG-2.5
    }
    while position + 4 <= len(data):
        if data[position:position + 3] == b"ID3" and position + 10 <= len(data):
            size_bytes = data[position + 6:position + 10]
            tag_size = sum((byte & 0x7F) << shift for byte, shift in zip(size_bytes, (21, 14, 7, 0)))
            footer = 10 if data[position + 5] & 0x10 else 0
            position += 10 + tag_size + footer
            continue
        header = int.from_bytes(data[position:position + 4], "big")
        if (header & 0xFFE00000) != 0xFFE00000:
            position += 1
            continue
        version = (header >> 19) & 0b11
        layer = (header >> 17) & 0b11
        bitrate_index = (header >> 12) & 0xF
        sample_rate_index = (header >> 10) & 0b11
        padding = (header >> 9) & 0b1
        if version == 1 or layer != 1 or bitrate_index in {0, 15} or sample_rate_index == 3:
            position += 1
            continue
        bitrate = (bitrate_v1 if version == 3 else bitrate_v2)[bitrate_index]
        sample_rate = sample_rates[version][sample_rate_index]
        samples_per_frame = 1152 if version == 3 else 576
        frame_length = int((144000 if version == 3 else 72000) * bitrate / sample_rate + padding)
        if frame_length < 4 or position + frame_length > len(data):
            position += 1
            continue
        duration_ms += samples_per_frame * 1000.0 / sample_rate
        frame_count += 1
        position += frame_length
    return int(round(duration_ms)) if frame_count else 0


def add_audio_durations_to_source(source: dict[str, Any], audio: bytes) -> dict[str, Any]:
    """Upgrade a byte-weighted source using its unchanged concatenated MP3."""
    segments = source.get("segments") if isinstance(source.get("segments"), list) else []
    sizes = [max(0, int(item.get("audio_weight") or 0)) for item in segments if isinstance(item, dict)]
    if not sizes or len(sizes) != len(segments) or any(size <= 0 for size in sizes) or sum(sizes) > len(audio or b""):
        return source
    offset = 0
    durations = []
    for size in sizes:
        durations.append(mp3_duration_ms(audio[offset:offset + size]))
        offset += size
    if any(duration <= 0 for duration in durations):
        return source
    upgraded = dict(source)
    upgraded["segments"] = [
        {**item, "audio_duration_ms": durations[index]}
        for index, item in enumerate(segments)
    ]
    return upgraded


def visual_source_from_message(message_content: str) -> dict[str, Any]:
    """Build visual-only source data for podcasts created before v3 metadata."""
    text = re.sub(r"\s+", " ", str(message_content or "")).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?।])\s+", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in sentences or [text]:
        words = len(sentence.split())
        if current and current_words + words > 32:
            chunks.append(" ".join(current))
            current = []
            current_words = 0
        current.append(sentence)
        current_words += words
    if current:
        chunks.append(" ".join(current))
    chunks = chunks[:24] or ["Your personalised AstroRoshni reading"]
    return {
        "version": 3,
        "script": "",
        "message_content": text,
        "segments": [
            {"index": index, "speaker": "narration", "text": chunk, "audio_weight": 0}
            for index, chunk in enumerate(chunks)
        ],
    }


def _unwrap_cues(value: str) -> str:
    # PAUSE values are production instructions (short/medium/long), not
    # spoken copy. Prosody cues contain real words and should be unwrapped.
    text = re.sub(r"\[PAUSE:[^\]]*\]", " ", value or "", flags=re.IGNORECASE)
    return re.sub(r"\[(?:EMPHASIS|RISE|FALL|SLOW):([^\]]*)\]", r"\1", text, flags=re.IGNORECASE)


def _strip_cues(value: str) -> str:
    return re.sub(r"\s+", " ", _unwrap_cues(value)).strip()


def _word_weight(value: str) -> int:
    words = len(re.findall(r"\S+", _strip_cues(value)))
    pauses = len(re.findall(r"\[PAUSE:(?:medium|long)\]", value or "", flags=re.IGNORECASE))
    return max(1, words + pauses * 3)


def _extract_json(text: str) -> Any:
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object in visual response")
    return json.loads(raw[start:end + 1])


def _source_text(source: dict[str, Any]) -> str:
    segments = source.get("segments") if isinstance(source.get("segments"), list) else []
    spoken = " ".join(
        _strip_cues(str(item.get("text") or ""))
        for item in segments
        if isinstance(item, dict)
    )
    return re.sub(r"\s+", " ", spoken or str(source.get("message_content") or "")).strip()


def _source_facts(source: dict[str, Any]) -> dict[str, Any]:
    text = _source_text(source)
    lower = text.lower()
    houses: set[int] = set()
    house_patterns = (
        r"\b(?:house|bhava|भाव)\s*(?:number\s*)?(1[0-2]|[1-9])\b",
        r"\b(1[0-2]|[1-9])(?:st|nd|rd|th)?\s*(?:house|bhava|भाव)\b",
        r"\b(1[0-2]|[1-9])\s*(?:वाँ|वा|वें|वे|वां)\s*भाव\b",
    )
    for pattern in house_patterns:
        houses.update(int(value) for value in re.findall(pattern, lower, flags=re.IGNORECASE))
    # Numeric patterns do not cover commonly spoken Hindi ordinals such as
    # "दशम भाव". Keep the source-wide validator and scene selector aligned.
    houses.update(referenced_houses(text))
    planets = {planet.lower(): planet for planet in PLANET_NAMES if planet.lower() in lower}
    planets.update({alias.lower(): planet for alias, planet in PLANET_ALIASES.items() if alias.lower() in lower})
    # Date strings are validated by normalised source containment instead of
    # trying to interpret their calendar meaning.
    normalised = re.sub(r"[^\w\u0900-\u097f]+", " ", lower).strip()
    return {
        "text": text,
        "normalised": normalised,
        "houses": houses,
        "planets": planets,
        "divisions": referenced_divisions(text),
    }


def referenced_divisions(value: str) -> list[int]:
    """Return only vargas explicitly named in spoken copy, in mention order."""
    text = str(value or "").lower()
    matches: list[tuple[int, int]] = []
    for match in re.finditer(r"\bd\s*[-–]?\s*(2|3|4|7|9|10|12|16|20|24|27|30|40|45|60)\b", text):
        matches.append((match.start(), int(match.group(1))))
    for division, aliases in DIVISION_ALIASES.items():
        for alias in aliases:
            match = re.search(
                re.escape(alias) if _has_devanagari(alias) else rf"\b{re.escape(alias)}\b",
                text,
            )
            if match:
                matches.append((match.start(), division))
    result: list[int] = []
    for _, division in sorted(matches):
        if division not in result:
            result.append(division)
    return result


def referenced_houses(value: str) -> list[int]:
    text = str(value or "").lower()
    result: list[int] = []
    patterns = (
        r"\b(?:house|bhava|भाव)\s*(?:number\s*)?(1[0-2]|[1-9])\b",
        r"\b(1[0-2]|[1-9])(?:st|nd|rd|th)?\s*(?:house|bhava|भाव)\b",
        # Common Latin-Hindi TTS/script spellings: "10ve bhaav",
        # "10ven bhav", "10va bhaav".
        r"\b(1[0-2]|[1-9])\s*(?:ve|ven|va|van)?\s*(?:bhav|bhaav)\b",
        r"\b(1[0-2]|[1-9])\s*(?:वाँ|वा|वें|वे|वां)‌?\s*भाव\b",
    )
    mentions: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            mentions.append((match.start(), int(match.group(1))))
    for house, aliases in HINDI_HOUSE_NUMBERS.items():
        for alias in aliases:
            for match in re.finditer(rf"{re.escape(alias)}\s*(?:घर|भाव)", text):
                mentions.append((match.start(), house))
    for _, house in sorted(mentions):
        if house not in result:
            result.append(house)
    return result


def _validated_division(value: Any, facts: dict[str, Any]) -> str:
    match = re.search(r"(?:^|\D)(\d{1,2})(?:$|\D)", str(value or ""))
    division = int(match.group(1)) if match else None
    if division in facts.get("divisions", []):
        return f"D{division}"
    return ""


def _mentions_dasha(value: str) -> bool:
    return bool(re.search(r"\b(?:maha\s*dasha|antar\s*dasha|pratyantar\s*dasha|dasha|dashas|vimshottari)\b|दशा", str(value or ""), re.IGNORECASE))


def _mentions_house_activation(value: str) -> bool:
    text = str(value or "")
    english = re.search(r"\bactivat(?:e|es|ed|ing|ion)\b", text, re.IGNORECASE) and re.search(
        r"\b(?:house|houses)\b", text, re.IGNORECASE
    )
    hindi = re.search(r"भाव", text) and re.search(r"सक्रिय|जागृत", text)
    return bool(english or hindi)


def _preferred_data_visual(value: str, chapter_index: int = 0) -> tuple[str, str]:
    """Choose one grounded visual anchor for a spoken chapter."""
    text = str(value or "")
    divisions = referenced_divisions(text)
    if _mentions_ashtakavarga(text):
        return "ashtakavarga_table", ""
    if _mentions_house_activation(text):
        return "house_activation_map", ""
    if divisions:
        return "divisional_chart", f"D{divisions[0]}"
    if _mentions_dasha(text):
        return "dasha_timeline", ""
    facts = _source_facts({"segments": [{"text": text}]})
    if facts["houses"]:
        return "house_highlight", ""
    if facts["planets"]:
        return "planet_highlight", ""
    return ("natal_chart", "") if chapter_index % 2 == 0 else ("zodiac_spotlight", "")


def _target_beat_count(source: dict[str, Any]) -> int:
    words = len(_source_text(source).split())
    # About one beat per 12 spoken words: normally 4–7 seconds at podcast pace.
    return max(6, min(75, int(round(words / 12.0))))


def _has_devanagari(value: Any) -> bool:
    return bool(re.search(r"[\u0900-\u097f]", str(value or "")))


def _hindi_copy(scene_type: str) -> tuple[str, str]:
    return HINDI_SCENE_COPY.get(scene_type, HINDI_DEFAULT_COPY)


def _mentions_ashtakavarga(value: Any) -> bool:
    text = str(value or "")
    return bool(re.search(
        r"\b(?:ashtakavarga|ashtakvarga|sarvashtakavarga|bhinnashtakavarga|SAVs?|BAVs?|bindus?)\b|अष्टकवर्ग|सर्वाष्टकवर्ग|भिन्नाष्टकवर्ग|बिंदु",
        text,
        flags=re.IGNORECASE,
    ))


def _clean_visible_copy(value: Any) -> str:
    """Turn chat Markdown/HTML into plain text suitable for video cards."""
    text = html.unescape(_unwrap_cues(str(value or "")))
    text = re.sub(r"<\s*br\s*/?\s*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*(?:[-+*>]|\d+[.)])\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"```(?:\w+)?|`", "", text)
    text = re.sub(r"(?<!\\)[*_~]+", "", text)
    text = text.replace("\\*", "*").replace("\\_", "_").replace("\\#", "#")
    return re.sub(r"\s+", " ", text).strip()


def _clip_copy(value: Any, limit: int) -> str:
    text = _clean_visible_copy(value)
    if len(text) <= limit:
        return text

    # Visible podcast copy must never end in half a word ("tea" instead of
    # "teaching"). Keep the ellipsis inside the requested character budget.
    ellipsis = "..."
    available = max(1, limit - len(ellipsis))
    raw_prefix = text[:available]
    prefix = raw_prefix.rstrip()
    cutoff_is_boundary = raw_prefix[-1:].isspace() or text[available:available + 1].isspace()
    if not cutoff_is_boundary:
        word_boundary = prefix.rfind(" ")
        if word_boundary > 0:
            prefix = prefix[:word_boundary]
    prefix = prefix.rstrip(" ,.;:!?—-")
    return f"{prefix}{ellipsis}"


def _caption_chunks(value: Any, max_words: int = 11) -> list[str]:
    """Create short readable caption cards from the actual host dialogue."""
    plain = _clean_visible_copy(value)
    if not plain:
        return []
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?।])\s+", plain)
        if part.strip()
    ] or [plain]
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= max_words:
            chunks.append(sentence)
            continue
        for start in range(0, len(words), max_words):
            chunks.append(" ".join(words[start:start + max_words]))
    return chunks


def _validated_houses(values: Any, facts: dict[str, Any]) -> list[int]:
    result = []
    for value in values if isinstance(values, list) else []:
        if str(value).isdigit():
            house = int(value)
            if 1 <= house <= 12 and house in facts["houses"] and house not in result:
                result.append(house)
    return result[:4]


def _validated_planets(values: Any, facts: dict[str, Any]) -> list[str]:
    result = []
    for value in values if isinstance(values, list) else []:
        key = str(value or "").strip().lower()
        canonical = facts["planets"].get(key)
        if canonical and canonical not in result:
            result.append(canonical)
    return result[:5]


def _validated_dates(values: Any, facts: dict[str, Any]) -> list[str]:
    result = []
    for value in values if isinstance(values, list) else []:
        date = _clip_copy(value, 50)
        needle = re.sub(r"[^\w\u0900-\u097f]+", " ", date.lower()).strip()
        if needle and needle in facts["normalised"] and date not in result:
            result.append(date)
    return result[:3]


def _beat(item: dict[str, Any], facts: dict[str, Any], index: int, chapter_index: int) -> dict[str, Any]:
    scene_type = str(item.get("type") or "key_takeaway").strip().lower()
    if scene_type not in ALLOWED_VISUAL_TYPES:
        scene_type = "key_takeaway"
    item_copy = f"{item.get('headline') or ''} {item.get('supporting_text') or ''}"
    copy_divisions = [division for division in referenced_divisions(item_copy) if division in facts.get("divisions", [])]
    if copy_divisions and scene_type in {"natal_chart", "house_highlight", "planet_highlight", "key_takeaway"}:
        scene_type = "divisional_chart"
    elif _mentions_house_activation(item_copy) and scene_type in {"house_highlight", "key_takeaway", "topic_cards"}:
        scene_type = "house_activation_map"
    elif _mentions_dasha(item_copy) and scene_type in {"date_window", "key_takeaway", "topic_cards"}:
        scene_type = "dasha_timeline"
    transition = str(item.get("transition") or "").strip().lower()
    if transition not in TRANSITIONS:
        transition = "reveal" if index == 0 else TRANSITIONS[(index + chapter_index) % len(TRANSITIONS)]
    accent = str(item.get("accent") or "").strip().lower()
    if accent not in ACCENTS:
        accent = ACCENTS[(index + chapter_index) % len(ACCENTS)]
    division = _validated_division(item.get("division"), facts)
    if not division and copy_divisions:
        division = f"D{copy_divisions[0]}"
    if scene_type == "divisional_chart" and not division and facts.get("divisions"):
        division = f"D{facts['divisions'][0]}"
    return {
        "type": scene_type,
        "headline": _clip_copy(item.get("headline") or "AstroRoshni", 64),
        "supporting_text": _clip_copy(item.get("supporting_text"), 120),
        "houses": _validated_houses(item.get("houses"), facts),
        "planets": _validated_planets(item.get("planets"), facts),
        "dates": _validated_dates(item.get("dates"), facts),
        "division": division,
        "steps": [_clip_copy(value, 72) for value in (item.get("steps") or []) if _clip_copy(value, 72)][:3],
        "transition": transition,
        "accent": accent,
        "hold": max(1, min(3, int(item.get("hold") or 1))),
    }


def _fallback_manifest(source: dict[str, Any], lang: str) -> dict[str, Any]:
    segments = source.get("segments") if isinstance(source.get("segments"), list) else []
    valid = [item for item in segments if isinstance(item, dict)]
    facts = _source_facts(source)
    target = _target_beat_count(source)
    chapter_count = max(1, min(10, len(valid) or 1))
    type_cycle = [
        "host_focus", "key_takeaway", "natal_chart", "planet_highlight",
        "comparison", "balance", "date_window", "action_steps", "constellation_summary",
    ]
    chapters = []
    use_hindi = str(lang).lower().startswith("hi")
    for chapter_index in range(chapter_count):
        start = round(chapter_index * max(1, len(valid)) / chapter_count)
        end = max(start, round((chapter_index + 1) * max(1, len(valid)) / chapter_count) - 1)
        chapter_segments = valid[start:end + 1]
        text = " ".join(_strip_cues(str(item.get("text") or "")) for item in chapter_segments).strip()
        chapter_facts = _source_facts({"segments": [{"text": text}]})
        sentences = [part.strip() for part in re.split(r"(?<=[.!?।])\s+", text) if part.strip()] or [text or "Your AstroRoshni insight"]
        beat_count = max(2, min(7, round(target / chapter_count)))
        beats = []
        for beat_index in range(beat_count):
            sentence = sentences[min(beat_index, len(sentences) - 1)]
            sentence_divisions = referenced_divisions(sentence)
            sentence_facts = _source_facts({"segments": [{"text": sentence}]})
            anchor_type, anchor_division = _preferred_data_visual(text, chapter_index)
            visual_facts = chapter_facts if beat_index == 1 else sentence_facts
            scene_type = (
                "ashtakavarga_table"
                if beat_index == 0 and _mentions_ashtakavarga(text)
                else "house_activation_map" if _mentions_house_activation(sentence)
                else "divisional_chart" if sentence_divisions and (not _mentions_dasha(sentence) or beat_index % 2 == 0)
                else "dasha_timeline" if _mentions_dasha(sentence)
                # Short fallback chapters commonly contain only two beats.
                # Put their grounded chart/data visual in that visible window
                # instead of waiting until the fourth position in a cycle.
                else anchor_type if beat_index == 1
                else type_cycle[(chapter_index + beat_index) % len(type_cycle)]
            )
            hindi_headline, hindi_supporting = _hindi_copy(scene_type)
            beats.append(_beat({
                "type": scene_type,
                "headline": sentence if not use_hindi or _has_devanagari(sentence) else hindi_headline,
                "supporting_text": sentence if not use_hindi or _has_devanagari(sentence) else hindi_supporting,
                "houses": sorted(visual_facts["houses"]),
                "planets": list(visual_facts["planets"]),
                "division": f"D{sentence_divisions[0]}" if sentence_divisions else anchor_division if beat_index == 1 else "",
                "transition": TRANSITIONS[(chapter_index + beat_index) % len(TRANSITIONS)],
                "accent": ACCENTS[(chapter_index + beat_index) % len(ACCENTS)],
            }, facts, beat_index, chapter_index))
        chapters.append({
            "title": _clip_copy(
                sentences[0] if not use_hindi or _has_devanagari(sentences[0]) else "आपकी ज्योतिषीय दिशा",
                72,
            ),
            "segment_start": start,
            "segment_end": end,
            "beats": beats,
        })
    return {
        "version": 3,
        "language": "hi" if str(lang).startswith("hi") else "en",
        "title": "AstroRoshni Visual Podcast",
        "chapters": chapters,
    }


GROUNDED_VISUAL_TYPES = {
    "natal_chart", "zodiac_spotlight", "house_highlight", "planet_highlight",
    "dasha_timeline", "divisional_chart", "ashtakavarga_table", "house_activation_map",
}


def _ensure_grounded_visuals(
    chapters: list[dict[str, Any]],
    source: dict[str, Any],
    facts: dict[str, Any],
) -> list[dict[str, Any]]:
    """Guarantee every chapter contains a factual chart/data visual."""
    segments = [item for item in (source.get("segments") or []) if isinstance(item, dict)]
    for chapter_index, chapter in enumerate(chapters):
        beats = chapter.get("beats") if isinstance(chapter.get("beats"), list) else []
        if not beats:
            continue
        start = max(0, min(len(segments) - 1, int(chapter.get("segment_start") or 0))) if segments else 0
        end = max(start, min(len(segments) - 1, int(chapter.get("segment_end") or start))) if segments else start
        chapter_text = " ".join(
            _strip_cues(str(item.get("text") or "")) for item in segments[start:end + 1]
        )
        scene_type, division = _preferred_data_visual(chapter_text, chapter_index)
        chapter_facts = _source_facts({"segments": [{"text": chapter_text}]})
        existing_types = {str(beat.get("type") or "") for beat in beats if isinstance(beat, dict)}
        # Technical references are contractual, not optional variety. A
        # generic natal chart must not suppress SAV, dasha, varga, or house
        # activation visuals explicitly discussed by the hosts.
        required_specific = scene_type in {
            "ashtakavarga_table", "house_activation_map", "divisional_chart", "dasha_timeline",
        }
        if required_specific and scene_type in existing_types:
            # The densifier may already have selected the right technical
            # scene before it knew which house/planet to focus. Enrich that
            # existing beat instead of treating its type alone as complete.
            target = next(
                index for index, beat in enumerate(beats)
                if isinstance(beat, dict) and beat.get("type") == scene_type
            )
            enriched = dict(beats[target])
            enriched.update({
                "houses": sorted(chapter_facts["houses"]),
                "planets": list(chapter_facts["planets"]),
                "division": division,
            })
            beats[target] = _beat(enriched, facts, target, chapter_index)
            chapter["beats"] = beats
            continue
        if not required_specific and any(existing_type in GROUNDED_VISUAL_TYPES for existing_type in existing_types):
            continue
        target = 1 if len(beats) > 1 else 0
        replacement = dict(beats[target])
        replacement.update({
            "type": scene_type,
            "houses": sorted(chapter_facts["houses"]),
            # Use detected source spellings as validator keys; _beat converts
            # both English and Hindi aliases to canonical planet names.
            "planets": list(chapter_facts["planets"]),
            "division": division,
        })
        beats[target] = _beat(replacement, facts, target, chapter_index)
        chapter["beats"] = beats
    return chapters


def _is_podcast_intro(value: str) -> bool:
    text = _strip_cues(str(value or ""))
    return bool(re.search(
        r"welcome\s+to\s+the\s+astroroshni|(?:i(?:'|’)m|i\s+am)\s+(?:ananya|arjun)|"
        r"astroroshni\s+podcast\s+में\s+आपका\s+स्वागत|मैं\s+हूँ\s+(?:अनन्या|अर्जुन)|और\s+मैं\s+हूँ\s+अर्जुन",
        text,
        flags=re.IGNORECASE,
    ))


def _is_podcast_outro(value: str) -> bool:
    text = _strip_cues(str(value or ""))
    return bool(re.search(
        r"reading\s+for\s+today|thank\s+you\s+for\s+listening|meet\s+you\s+again|"
        r"आज\s+के\s+लिए\s+बस|सुनने\s+के\s+लिए\s+धन्यवाद|फिर\s+मिलेंगे|"
        r"(?:and\s+i(?:'|’)m\s+ananya|और\s+मैं\s+अनन्या)",
        text,
        flags=re.IGNORECASE,
    ))


def _ensure_programme_bookends(
    chapters: list[dict[str, Any]],
    source: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reserve branded visuals for the application's fixed intro and outro."""
    segments = [item for item in (source.get("segments") or []) if isinstance(item, dict)]
    intro_indexes = {
        index for index, item in enumerate(segments[:3])
        if _is_podcast_intro(str(item.get("text") or ""))
    }
    outro_indexes = {
        index for index, item in enumerate(segments)
        if index >= max(0, len(segments) - 4) and _is_podcast_outro(str(item.get("text") or ""))
    }
    for chapter in chapters:
        beats = chapter.get("beats") if isinstance(chapter.get("beats"), list) else []
        if not beats:
            continue
        start = max(0, int(chapter.get("segment_start") or 0))
        end = max(start, int(chapter.get("segment_end") or start))
        covered = list(range(start, end + 1))
        intro_ratio = sum(index in intro_indexes for index in covered) / max(1, len(covered))
        outro_ratio = sum(index in outro_indexes for index in covered) / max(1, len(covered))
        intro_beats = min(len(beats), int(round(len(beats) * intro_ratio)))
        outro_beats = min(len(beats) - intro_beats, int(round(len(beats) * outro_ratio)))
        if intro_ratio and not intro_beats:
            intro_beats = 1
        if outro_ratio and not outro_beats and intro_beats < len(beats):
            outro_beats = 1
        for index in range(intro_beats):
            beats[index] = {
                **beats[index], "type": "opening", "houses": [], "planets": [],
                "dates": [], "division": "", "steps": [], "accent": "gold",
            }
        for index in range(max(intro_beats, len(beats) - outro_beats), len(beats)):
            beats[index] = {
                **beats[index], "type": "closing", "houses": [], "planets": [],
                "dates": [], "division": "", "steps": [], "accent": "violet",
            }
        # Opening and closing are programme structure, never decorative scene
        # variety. Remove model/fallback bookend labels from the body.
        body_end = max(intro_beats, len(beats) - outro_beats)
        for index in range(intro_beats, body_end):
            if beats[index].get("type") in {"opening", "closing"}:
                beats[index] = {**beats[index], "type": "key_takeaway"}
        chapter["beats"] = beats
    return chapters


def _timed_fallback_manifest(source: dict[str, Any], lang: str) -> dict[str, Any]:
    fallback = _fallback_manifest(source, lang)
    fallback["chapters"] = _ensure_programme_bookends(fallback.get("chapters") or [], source)
    return _add_timing(fallback, source)


def _densify_chapters(
    chapters: list[dict[str, Any]],
    source: dict[str, Any],
    facts: dict[str, Any],
    lang: str,
) -> list[dict[str, Any]]:
    """Guarantee lively pacing even when the model returns too few beats."""
    if not chapters:
        return chapters
    segments = [item for item in (source.get("segments") or []) if isinstance(item, dict)]
    target = _target_beat_count(source)
    chapter_weights = []
    for chapter in chapters:
        start = max(0, int(chapter.get("segment_start") or 0))
        end = max(start, int(chapter.get("segment_end") or start))
        chapter_weights.append(sum(_word_weight(str(item.get("text") or "")) for item in segments[start:end + 1]) or 1)
    weight_total = max(1, sum(chapter_weights))
    generic_cycle = (
        "host_focus", "natal_chart", "quote", "zodiac_spotlight", "topic_cards",
        "natal_chart", "balance", "decision_path", "constellation_summary",
    )
    use_hindi = str(lang).lower().startswith("hi")
    for chapter_index, (chapter, weight) in enumerate(zip(chapters, chapter_weights)):
        desired = max(2, min(8, int(round(target * weight / weight_total))))
        beats = chapter.get("beats") or []
        if len(beats) > desired:
            chapter["beats"] = beats[:desired - 1] + [beats[-1]]
            continue
        if len(beats) == desired:
            continue
        start = max(0, int(chapter.get("segment_start") or 0))
        end = max(start, int(chapter.get("segment_end") or start))
        chapter_text = " ".join(
            _strip_cues(str(item.get("text") or "")) for item in segments[start:end + 1]
        )
        clauses = [
            part.strip() for part in re.split(r"(?<=[.!?।])\s+|\s*[;—]\s*", chapter_text) if part.strip()
        ] or [chapter.get("title") or "Your AstroRoshni insight"]
        seed = beats or [_beat({"headline": chapter.get("title")}, facts, 0, chapter_index)]
        while len(beats) < desired:
            beat_index = len(beats)
            base = dict(seed[beat_index % len(seed)])
            clause = clauses[beat_index % len(clauses)]
            has_chart_facts = bool(base.get("houses") or base.get("planets") or base.get("dates"))
            if not has_chart_facts or beat_index % 2:
                base["type"] = generic_cycle[(chapter_index + beat_index) % len(generic_cycle)]
            if beat_index % 2 == 0 and _mentions_ashtakavarga(clause):
                base["type"] = "ashtakavarga_table"
            if _mentions_house_activation(clause):
                base["type"] = "house_activation_map"
            clause_divisions = referenced_divisions(clause)
            if clause_divisions and (not _mentions_dasha(clause) or beat_index % 2 == 0):
                base["type"] = "divisional_chart"
                base["division"] = f"D{clause_divisions[0]}"
            elif _mentions_dasha(clause):
                base["type"] = "dasha_timeline"
            if not use_hindi or _has_devanagari(clause):
                base["headline"] = _clip_copy(clause, 64)
                base["supporting_text"] = _clip_copy(base.get("supporting_text") or clause, 120)
            else:
                # The stored dialogue for older Hindi podcasts may be the
                # original English chat answer. Preserve the model's Hindi
                # seed instead of reintroducing English while densifying.
                hindi_headline, hindi_supporting = _hindi_copy(str(base.get("type") or ""))
                base["headline"] = _clip_copy(
                    base.get("headline") if _has_devanagari(base.get("headline")) else hindi_headline,
                    64,
                )
                base["supporting_text"] = _clip_copy(
                    base.get("supporting_text") if _has_devanagari(base.get("supporting_text")) else hindi_supporting,
                    120,
                )
            base["transition"] = TRANSITIONS[(chapter_index + beat_index) % len(TRANSITIONS)]
            base["accent"] = ACCENTS[(chapter_index + beat_index) % len(ACCENTS)]
            base["hold"] = 1
            beats.append(base)
        chapter["beats"] = beats
    while sum(len(chapter.get("beats") or []) for chapter in chapters) > 75:
        largest = max(chapters, key=lambda chapter: len(chapter.get("beats") or []))
        beats = largest.get("beats") or []
        if len(beats) <= 2:
            break
        largest["beats"] = beats[:-2] + [beats[-1]]
    return chapters


def _generate_with_gemini(source: dict[str, Any], lang: str) -> dict[str, Any]:
    import google.generativeai as genai
    from utils.admin_settings import get_gemini_analysis_model

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_PODCAST_VISUAL_MODEL") or os.getenv("GEMINI_PODCAST_MODEL") or get_gemini_analysis_model()
    model = genai.GenerativeModel(model_name)
    segments = source.get("segments") or []
    compact_segments = [
        {"index": item.get("index"), "speaker": item.get("speaker"), "text": _strip_cues(str(item.get("text") or ""))}
        for item in segments if isinstance(item, dict)
    ]
    language_name = "Hindi" if str(lang).lower().startswith("hi") else "English"
    target_beats = _target_beat_count(source)
    target_chapters = max(1, min(12, len(compact_segments) or 1, int(round(target_beats / 5))))
    prompt = f"""Create a cinematic visual plan for an AstroRoshni two-host astrology podcast.

Return ONLY valid compact JSON. Visible copy must be {language_name}.

STRUCTURE AND PACING:
- Build {target_chapters} coherent chapters that cover every dialogue segment once, in order.
- Return exactly 2 concise seed beats per chapter. Do not return all {target_beats} final beats.
- The backend deterministically expands these seeds to about {target_beats} short beats using the original spoken clauses.
- A chart may persist across adjacent beats, but its focus must change: reveal, illuminate, connect, compare, then conclude.
- Use visual variety deliberately; do not repeat one visual type more than twice consecutively.
- Every chapter must include at least one grounded visual: natal_chart, zodiac_spotlight, a factual house/planet highlight, dasha_timeline, divisional_chart, ashtakavarga_table, or house_activation_map.
- Use opening for the branded greeting and closing for the sign-off. Never show chart evidence or generic symbolic artwork during those programme bookends.
- Whenever the dialogue discusses Ashtakavarga, Sarvashtakavarga, SAV/SAVs, BAV/BAVs or bindus, use ashtakavarga_table for that beat.
- Whenever it names D2/D3/D4/D7/D9/D10/D12/D16/D20/D24/D27/D30/D40/D45/D60 or a varga name such as Navamsa or Dashamsa, use divisional_chart and set division to that D-number.
- Whenever it discusses a dasha, use dasha_timeline. The client supplies calculated periods; never create generic then/now/later labels.
- Whenever it explains that one or more houses are activated, use house_activation_map. The client supplies all four calculated evidence layers.

STRICT FACTUAL RULES:
- Use only conclusions, houses, planets, dashas, dates and ranges explicitly present in the dialogue.
- Never invent a placement, transit, date, remedy or prediction.
- Each chapter references consecutive zero-based dialogue indexes using segment_start and segment_end.
- Headlines under 45 characters; supporting text under 85 characters.
- Allowed types: {', '.join(sorted(ALLOWED_VISUAL_TYPES))}.
- Allowed transitions: {', '.join(TRANSITIONS)}. Allowed accents: {', '.join(ACCENTS)}.
- Only action_steps may contain steps, maximum 3. Use hold=1 normally, 2 for reading, 3 only for a complex chart.

JSON shape:
{{"version":3,"title":"short title","chapters":[{{"title":"chapter","segment_start":0,"segment_end":2,"beats":[{{"type":"opening","headline":"...","supporting_text":"...","houses":[],"planets":[],"dates":[],"division":"","steps":[],"transition":"reveal","accent":"gold","hold":1}}]}}]}}

Dialogue:
{json.dumps(compact_segments, ensure_ascii=False, separators=(',', ':'))}
"""
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.25, "max_output_tokens": 4096, "response_mime_type": "application/json"},
        request_options={
            "timeout": max(5.0, float(os.getenv("GEMINI_PODCAST_VISUAL_TIMEOUT_S", "18") or "18")),
            # Visuals have a complete local fallback. Disable the SDK's long
            # default retry loop so one transient Gemini/DNS failure cannot
            # hold the Watch request open for a minute.
            "retry": None,
        },
    )
    if not response or not getattr(response, "text", None):
        raise RuntimeError("Gemini returned an empty visual plan")
    return _extract_json(response.text)


def _sanitize_manifest(raw: dict[str, Any], source: dict[str, Any], lang: str) -> dict[str, Any]:
    segments = source.get("segments") if isinstance(source.get("segments"), list) else []
    segment_count = max(1, len(segments))
    facts = _source_facts(source)
    raw_chapters = raw.get("chapters") if isinstance(raw, dict) else None
    legacy_flat_shape = False
    # Backward-compatible ingestion of the old flat Gemini shape.
    if not isinstance(raw_chapters, list) and isinstance(raw.get("scenes") if isinstance(raw, dict) else None, list):
        legacy_flat_shape = True
        raw_chapters = [
            {
                "title": item.get("headline") or "Chapter",
                "segment_start": item.get("segment_start"),
                "segment_end": item.get("segment_end"),
                "beats": [item],
            }
            for item in raw["scenes"] if isinstance(item, dict)
        ]
    if not isinstance(raw_chapters, list) or not raw_chapters:
        return _timed_fallback_manifest(source, lang)

    chapters = []
    previous_end = -1
    for chapter_index, item in enumerate(raw_chapters[:12]):
        if not isinstance(item, dict) or previous_end >= segment_count - 1:
            continue
        start = max(previous_end + 1, min(segment_count - 1, int(item.get("segment_start") or 0)))
        end = max(start, min(segment_count - 1, int(item.get("segment_end") if item.get("segment_end") is not None else start)))
        raw_beats = item.get("beats") if isinstance(item.get("beats"), list) else []
        beats = [
            _beat(beat, facts, beat_index, chapter_index)
            for beat_index, beat in enumerate(raw_beats[:8])
            if isinstance(beat, dict)
        ]
        if not beats:
            beats = [_beat({"type": "key_takeaway", "headline": item.get("title")}, facts, 0, chapter_index)]
        chapters.append({
            "title": _clip_copy(item.get("title") or beats[0]["headline"], 72),
            "segment_start": start,
            "segment_end": end,
            "beats": beats,
        })
        previous_end = end
    if not chapters:
        return _timed_fallback_manifest(source, lang)
    chapters[0]["segment_start"] = 0
    chapters[-1]["segment_end"] = segment_count - 1
    if not legacy_flat_shape:
        chapters = _densify_chapters(chapters, source, facts, lang)
        chapters = _ensure_grounded_visuals(chapters, source, facts)
        chapters = _ensure_programme_bookends(chapters, source)
    if str(lang).lower().startswith("hi"):
        for chapter in chapters:
            if not _has_devanagari(chapter.get("title")):
                chapter["title"] = "आपकी ज्योतिषीय दिशा"
            for beat in chapter.get("beats") or []:
                hindi_headline, hindi_supporting = _hindi_copy(str(beat.get("type") or ""))
                if not _has_devanagari(beat.get("headline")):
                    beat["headline"] = hindi_headline
                if beat.get("supporting_text") and not _has_devanagari(beat.get("supporting_text")):
                    beat["supporting_text"] = hindi_supporting
    manifest = {
        "version": 3,
        "language": "hi" if str(lang).lower().startswith("hi") else "en",
        "title": _clip_copy(
            "AstroRoshni दृश्य पॉडकास्ट"
            if str(lang).lower().startswith("hi") and not _has_devanagari(raw.get("title"))
            else raw.get("title") or "AstroRoshni Visual Podcast",
            100,
        ),
        "chapters": chapters,
    }
    return _add_timing(manifest, source)


def _add_timing(manifest: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    segments = source.get("segments") if isinstance(source.get("segments"), list) else []
    valid_segments = [item for item in segments if isinstance(item, dict)]
    audio_durations = [max(0, int(item.get("audio_duration_ms") or 0)) for item in valid_segments]
    use_audio_durations = bool(audio_durations) and all(duration > 0 for duration in audio_durations)
    audio_weights = [max(0, int(item.get("audio_weight") or 0)) for item in valid_segments]
    use_audio_weights = bool(audio_weights) and all(weight > 0 for weight in audio_weights)
    weights = (
        audio_durations if use_audio_durations
        else audio_weights if use_audio_weights
        else [_word_weight(str(item.get("text") or "")) for item in valid_segments]
    )
    if not weights:
        weights = [1]
    cumulative = [0]
    for weight in weights:
        cumulative.append(cumulative[-1] + weight)
    total = max(1, cumulative[-1])

    chapters = manifest.get("chapters") if isinstance(manifest.get("chapters"), list) else []
    if not chapters and isinstance(manifest.get("scenes"), list):
        # Preserve v2 unit-test and old cached-manifest semantics.
        chapters = [{
            "title": scene.get("headline") or "Chapter",
            "segment_start": scene.get("segment_start", 0),
            "segment_end": scene.get("segment_end", 0),
            "beats": [scene],
        } for scene in manifest["scenes"]]

    flattened = []
    for chapter_index, chapter in enumerate(chapters):
        start = max(0, min(len(weights) - 1, int(chapter.get("segment_start") or 0)))
        end = max(start, min(len(weights) - 1, int(chapter.get("segment_end") if chapter.get("segment_end") is not None else start)))
        chapter_start = cumulative[start] / total
        chapter_end = cumulative[end + 1] / total
        beats = chapter.get("beats") if isinstance(chapter.get("beats"), list) and chapter.get("beats") else [{}]
        holds = [max(1, min(3, int(beat.get("hold") or 1))) for beat in beats]
        hold_total = max(1, sum(holds))
        elapsed = 0
        for beat_index, (beat, hold) in enumerate(zip(beats, holds)):
            beat_start = chapter_start + (chapter_end - chapter_start) * elapsed / hold_total
            elapsed += hold
            beat_end = chapter_start + (chapter_end - chapter_start) * elapsed / hold_total
            scene = dict(beat)
            scene.update({
                "chapter_index": chapter_index,
                "chapter_title": chapter.get("title") or "",
                "beat_index": beat_index,
                "segment_start": start,
                "segment_end": end,
                "start_fraction": round(beat_start, 6),
                "end_fraction": round(beat_end, 6),
            })
            flattened.append(scene)
        chapter["start_fraction"] = round(chapter_start, 6)
        chapter["end_fraction"] = round(chapter_end, 6)
    if flattened:
        flattened[0]["start_fraction"] = 0.0
        flattened[-1]["end_fraction"] = 1.0
    manifest["scenes"] = flattened[:75]
    # If a malformed model response exceeds 75 beats, the final retained beat
    # owns the remainder so playback never falls into an uncovered gap.
    if manifest["scenes"]:
        manifest["scenes"][-1]["end_fraction"] = 1.0
    named_speakers = [
        str(item.get("speaker") or "").strip().lower()
        for item in valid_segments[:len(weights)]
    ]
    has_exact_speaker_timing = any(speaker in {"female", "male"} for speaker in named_speakers)
    manifest["turns"] = []
    if has_exact_speaker_timing:
        for index, speaker in enumerate(named_speakers):
            manifest["turns"].append({
                "speaker": speaker if speaker in {"female", "male"} else "narration",
                "start_fraction": round(cumulative[index] / total, 6),
                "end_fraction": round(cumulative[index + 1] / total, 6),
            })
        manifest["speaker_timing_basis"] = "audio_segments"
    else:
        # Podcasts created before visual metadata have the final MP3 but not
        # the original FEMALE/MALE script. Alternate at the coarsest useful
        # visual boundaries instead of permanently attributing them to Ananya.
        estimated_units = chapters if len(chapters) > 1 else flattened
        for index, unit in enumerate(estimated_units):
            manifest["turns"].append({
                "speaker": "female" if index % 2 == 0 else "male",
                "start_fraction": round(float(unit.get("start_fraction") or 0), 6),
                "end_fraction": round(float(unit.get("end_fraction") or 1), 6),
            })
        manifest["speaker_timing_basis"] = "estimated_visual_boundaries"
    manifest["captions"] = []
    if has_exact_speaker_timing:
        for segment_index, (item, speaker) in enumerate(zip(valid_segments[:len(weights)], named_speakers)):
            if speaker not in {"female", "male"}:
                continue
            chunks = _caption_chunks(item.get("text"))
            if not chunks:
                continue
            segment_start = cumulative[segment_index] / total
            segment_end = cumulative[segment_index + 1] / total
            chunk_weights = [max(1, len(re.findall(r"\S+", chunk))) for chunk in chunks]
            chunk_total = max(1, sum(chunk_weights))
            elapsed = 0
            for chunk, chunk_weight in zip(chunks, chunk_weights):
                start = segment_start + (segment_end - segment_start) * elapsed / chunk_total
                elapsed += chunk_weight
                end = segment_start + (segment_end - segment_start) * elapsed / chunk_total
                manifest["captions"].append({
                    "speaker": speaker,
                    "text": _clip_copy(chunk, 110),
                    "start_fraction": round(start, 6),
                    "end_fraction": round(end, 6),
                })
        if manifest["captions"]:
            manifest["captions"][0]["start_fraction"] = 0.0
            manifest["captions"][-1]["end_fraction"] = 1.0
    manifest["caption_timing_basis"] = (
        "measured_audio_segments" if manifest["captions"] and use_audio_durations
        else "audio_segment_bytes" if manifest["captions"] and use_audio_weights
        else "unavailable"
    )
    manifest["timing_basis"] = "audio_segments" if use_audio_durations or use_audio_weights else "spoken_words"
    manifest["audio_timing_measure"] = "duration_ms" if use_audio_durations else "byte_size" if use_audio_weights else "spoken_words"
    manifest["pacing"] = {"target_seconds": [3, 8], "max_beats": 75}
    return manifest


def generate_visual_manifest(source: dict[str, Any], lang: str = "en") -> dict[str, Any]:
    try:
        raw = _generate_with_gemini(source, lang)
        manifest = _sanitize_manifest(raw, source, lang)
        manifest["planning_source"] = "gemini"
        return manifest
    except Exception as exc:
        # A visual plan is an enhancement. Timeouts/truncated model JSON are
        # expected recoverable failures and should not emit an ERROR traceback
        # for an otherwise successful Watch request.
        logger.warning("Visual podcast planning unavailable; using deterministic v3 fallback: %s", exc)
        manifest = _timed_fallback_manifest(source, lang)
        manifest["planning_source"] = "deterministic_fallback"
        return manifest
