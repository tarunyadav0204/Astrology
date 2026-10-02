"""Small, evidence-bound openings. No language inference or model calls here."""
from __future__ import annotations

import json

# Complete sentences, never translated word-by-word at request time. Unknown
# languages/scripts deliberately have no English fallback.
_PLANETS = {
    "english": "Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu".split(),
    "hindi": "सूर्य चंद्र मंगल बुध गुरु शुक्र शनि राहु केतु".split(),
    "hinglish": "Surya Chandra Mangal Budh Guru Shukra Shani Rahu Ketu".split(),
    "tamil": "சூரியன் சந்திரன் செவ்வாய் புதன் குரு சுக்கிரன் சனி ராகு கேது".split(),
    "telugu": "సూర్య చంద్ర కుజ బుధ గురు శుక్ర శని రాహు కేతు".split(),
    "gujarati": "સૂર્ય ચંદ્ર મંગળ બુધ ગુરુ શુક્ર શનિ રાહુ કેતુ".split(),
    "marathi": "सूर्य चंद्र मंगळ बुध गुरू शुक्र शनी राहू केतू".split(),
    "bengali": "সূর্য চন্দ্র মঙ্গল বুধ বৃহস্পতি শুক্র শনি রাহু কেতু".split(),
    "spanish": "Sol Luna Marte Mercurio Júpiter Venus Saturno Rahu Ketu".split(),
    "french": "Soleil Lune Mars Mercure Jupiter Vénus Saturne Rahu Ketu".split(),
    "german": "Sonne Mond Mars Merkur Jupiter Venus Saturn Rahu Ketu".split(),
    "russian": "Солнце Луна Марс Меркурий Юпитер Венера Сатурн Раху Кету".split(),
    "chinese": "太阳 月亮 火星 水星 木星 金星 土星 罗睺 计都".split(),
    "arabic": "الشمس القمر المريخ عطارد المشتري الزهرة زحل راهو كيتو".split(),
}
_ALIASES = dict(zip("en hi ta te gu mr bn es fr de ru zh ar".split(),
                    "english hindi tamil telugu gujarati marathi bengali spanish french german russian chinese arabic".split()))
_ALIASES.update({"roman hindi": "hinglish", "romanized hindi": "hinglish", "roman_hindi": "hinglish"})
_SCRIPTS = dict(zip(_PLANETS, "latn deva latn taml telu gujr deva beng latn latn latn cyrl hans arab".split()))


# Labels belong to the chart context panel; no deterministic verdict becomes
# part of the assistant answer. Latin-script variants remain explicit.
_CONTEXT_LABELS = {
    "english": ("Chart context · Calculated", "Tara’s answer", "Major period", "Sub-period", "Inner period"),
    "hindi": ("कुंडली के तथ्य · गणना", "तारा का उत्तर", "महादशा", "अंतर्दशा", "प्रत्यंतर दशा"),
    "hinglish": ("Kundli ke tathya · Calculation", "Tara ka jawab", "Mahadasha", "Antardasha", "Pratyantar dasha"),
    "tamil": ("ஜாதக விவரங்கள் · கணக்கீடு", "தாராவின் பதில்", "மகாதசை", "புத்தி", "அந்தரம்"),
    "telugu": ("జాతక వివరాలు · గణన", "తారా సమాధానం", "మహాదశ", "అంతర్దశ", "ప్రత్యంతర్దశ"),
    "gujarati": ("કુંડળીના તથ્યો · ગણતરી", "તારાનો જવાબ", "મહાદશા", "અંતર્દશા", "પ્રત્યંતર દશા"),
    "marathi": ("कुंडलीतील तथ्ये · गणना", "ताराचे उत्तर", "महादशा", "अंतर्दशा", "प्रत्यंतर दशा"),
    "bengali": ("জন্মছকের তথ্য · গণনা", "তারার উত্তর", "মহাদশা", "অন্তর্দশা", "প্রত্যন্তর দশা"),
    "spanish": ("Datos de la carta · Calculados", "Respuesta de Tara", "Período principal", "Subperíodo", "Período interno"),
    "french": ("Données du thème · Calculées", "Réponse de Tara", "Période majeure", "Sous-période", "Période intérieure"),
    "german": ("Horoskopdaten · Berechnet", "Taras Antwort", "Hauptperiode", "Unterperiode", "Innere Periode"),
    "russian": ("Данные карты · Расчёт", "Ответ Тары", "Большой период", "Подпериод", "Внутренний период"),
    "chinese": ("星盘资料 · 计算结果", "Tara 的回答", "大运", "分运", "次级分运"),
    "arabic": ("بيانات الخريطة · محسوبة", "إجابة تارا", "الفترة الكبرى", "الفترة الفرعية", "الفترة الداخلية"),
}


def build_instant_preview(packet, intent):
    """Expose calculated inputs separately, never an early generated answer."""
    if not isinstance(packet, dict) or not isinstance(intent, dict):
        return None
    language = str(intent.get("response_language") or intent.get("detected_language") or "").strip().lower()
    language = _ALIASES.get(language, language)
    script = str(intent.get("response_script") or "").strip().lower()
    script = {"latin": "latn", "roman": "latn"}.get(script, script)
    if language == "hindi" and script == "latn":
        language = "hinglish"
    if language not in _CONTEXT_LABELS or script != _SCRIPTS[language]:
        return None
    plan = packet.get("query_plan") or {}
    if (plan.get("route_action", "answer") != "answer"
            or (plan.get("target_subject") or {}).get("key") != "self"
            or plan.get("interpretation_frame") == "native_chart_derived_house"
            or len(intent.get("target_subject_keys") or []) > 1):
        return None
    if plan.get("answer_mode") not in {"timing_window", "event_prediction"}:
        return None
    records = (packet.get("evidence_ledger") or {}).get("records") or []
    record = next((r for r in records if isinstance(r, dict) and r.get("kind") == "current_dasha"), {})
    value = record.get("value") or {}
    levels = value.get("levels") or {}
    # The production compiler emits a dictionary; older callers emit a list.
    if isinstance(levels, list):
        aliases = {"mahadasha": "md", "antardasha": "ad", "pratyantardasha": "pd"}
        levels = {aliases.get(str(r.get("level", "")).lower(), str(r.get("level", "")).lower()): r
                  for r in levels if isinstance(r, dict)}
    if not isinstance(levels, dict) or not record.get("evidence_id"):
        return None
    scope = plan.get("time_scope") or {}
    if scope.get("retrospective") or scope.get("relation") == "past":
        return None
    labels = _CONTEXT_LABELS[language]
    rows = []
    for index, level in enumerate(("md", "ad", "pd")):
        planet = (levels.get(level) or {}).get("planet")
        if planet not in _PLANETS["english"]:
            continue
        name = _PLANETS[language][_PLANETS["english"].index(planet)]
        rows.append({"key": "dasha-" + level, "text": f"{labels[index + 2]}: {name}",
                     "source": "calculation", "evidence_id": record["evidence_id"]})
    if not rows:
        return None
    return {"type": "instant_preview", "version": 2, "source": "calculation",
            "title": labels[0], "answer_label": labels[1], "rows": rows,
            "content": "\n".join(row["text"] for row in rows),
            "language": language, "script": script, "as_of": value.get("as_of"),
            "direction": "rtl" if language == "arabic" else "ltr"}


def read_instant_preview(updates):
    """Read the separately persisted preview; it is never completed content."""
    try:
        rows = json.loads(updates) if isinstance(updates, str) else updates
        if isinstance(rows, list):
            return next((r for r in rows if isinstance(r, dict)
                         and r.get("type") == "instant_preview" and isinstance(r.get("content"), str)), None)
    except (TypeError, ValueError):
        pass
    return None

