import json
import os
from typing import Any, Dict, List

import google.generativeai as genai

from utils.admin_settings import GEMINI_MODEL_OPTIONS, get_gemini_analysis_model


class GeminiAstroVastuAnalyzer:
    """AI narrative layer for AstroVastu deterministic outputs."""

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)

        model_name = get_gemini_analysis_model()
        fallbacks = [m[0] for m in GEMINI_MODEL_OPTIONS if m[0] != model_name]
        self.model = None
        self.model_name = None
        for name in [model_name] + fallbacks:
            try:
                self.model = genai.GenerativeModel(name)
                self.model_name = name
                break
            except Exception:
                continue
        if not self.model:
            raise ValueError("No available Gemini model found for AstroVastu analysis")

    def enrich(
        self,
        payload: Dict[str, Any],
        birth_data: Dict[str, Any],
        goal: str,
        door_facing: str,
        zone_tags: Dict[str, List[str]] | None,
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(payload, birth_data, goal, door_facing, zone_tags or {})
        response = self.model.generate_content(prompt)
        parsed = self._parse_json(response.text or "")
        parsed["ai_model"] = self.model_name
        return parsed

    def _build_prompt(
        self,
        payload: Dict[str, Any],
        birth_data: Dict[str, Any],
        goal: str,
        door_facing: str,
        zone_tags: Dict[str, List[str]],
    ) -> str:
        mapped_directions = payload.get("directions") or {}
        full_payload = {
            "goal": payload.get("goal"),
            "door_facing": payload.get("door_facing"),
            "mapping_version": payload.get("mapping_version"),
            "mapping_model": payload.get("mapping_model"),
            "dasha_context": payload.get("dasha_context"),
            "area_scores": payload.get("area_scores"),
            "methodology": payload.get("methodology"),
            "hero": payload.get("hero"),
            "ranked_directions": payload.get("ranked_directions", [])[:8],
            "directions": {
                d: mapped_directions.get(d, {})
                for d in ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
            },
        }
        chart_identity = {
            "name": birth_data.get("name"),
            "date": birth_data.get("date"),
            "time": birth_data.get("time"),
            "place": birth_data.get("place"),
        }
        return f"""
You are a Vedic-astrology-aware AstroVastu explanation writer.
Use ONLY the structured deterministic data below. Do not invent planets, signs, houses, or directions.

Output STRICT JSON with this exact schema:
{{
  "report_title_ai": "Short title",
  "snapshot": {{
    "topline": "1-2 sentence quick summary",
    "current_dasha_note": "1 sentence",
    "top_directions": ["3 short items like: NW - mixed, focus on..."]
  }},
  "executive_summary_ai": "4-8 sentences with direct conclusion and why",
  "what_this_means": {{
    "career": "2-4 sentences",
    "wealth": "2-4 sentences",
    "relationships_family": "2-4 sentences",
    "health_routine": "2-4 sentences",
    "focus_mental": "2-4 sentences",
    "spiritual_home_harmony": "2-4 sentences"
  }},
  "direction_ai": {{
    "N": "4-8 sentence explanation",
    "NE": "4-8 sentence explanation",
    "E": "4-8 sentence explanation",
    "SE": "4-8 sentence explanation",
    "S": "4-8 sentence explanation",
    "SW": "4-8 sentence explanation",
    "W": "4-8 sentence explanation",
    "NW": "4-8 sentence explanation"
  }},
  "room_specific_guidance": [
    {{"room_tag":"temple_prayer","direction":"NE","status":"supportive|mixed|challenging","advice":"2-3 sentences"}}
  ],
  "timing_plan": {{
    "now_0_3_months": ["3-5 concrete points"],
    "months_3_6": ["3-5 concrete points"],
    "months_6_18": ["3-5 concrete points"]
  }},
  "action_plan": {{
    "this_week": ["3-5 actions"],
    "this_month": ["3-5 actions"],
    "optional_upgrades": ["2-4 actions"]
  }},
  "non_renovation_options": ["4-8 renter-safe reversible actions"],
  "confidence_note_ai": "One short sentence about deterministic + interpretive blend"
}}

Rules:
- This is a COMPLETE analysis report, not a short add-on.
- Cover all areas explicitly: career, wealth, relationship/family, health, focus/mental, spiritual-home harmony.
- If hero has no planets and mostly tag pressure, say that explicitly.
- Mention sign->direction logic briefly, and that door does not rotate chart.
- Be specific about why the chosen hero direction is prioritized for this goal.
- For every direction, explain: (a) which planets/signs map there, (b) tag effects, (c) how grahas relate to **houses in that sector**.
- **House anchoring (critical):** Each direction block includes `house_life_themes` with `houses_with_planets_themes` and `mapped_houses_with_themes`.
  Open every `direction_ai` entry by grounding planets in **`houses_with_planets_themes`** when non-empty; otherwise use **`mapped_houses_with_themes`**.
  Interpret Saturn/Rahu/Mars/etc. **only** through those house themes (e.g. H2 = wealth, speech, food, close family — **not** career).
- **Do not** frame a compass sector as mainly about career, promotion, or employer issues unless **H10** is listed in that sector's house themes **or** you are clearly discussing **H6** as daily work/health habits **for planets that actually occupy H6 in that sector**.
  Never infer “professional path” from heavy planets alone if they sit in H2, H4, H5, etc.
- **Cross-sector career:** Put general career advice in `what_this_means.career` or the sector where **H10** (or H6 if relevant) actually maps — not wherever Saturn falls.

**what_this_means — quality (mandatory):**
- `deterministic.area_scores` has one entry per theme: **career, wealth, relationship, health, focus, spiritual**. Each contains `top_directions` (best-ranked compass sectors for that theme after house-weighting and tags — use these scores).
- **Map JSON keys:** `career`↔career, `wealth`↔wealth, `relationships_family`↔relationship, `health_routine`↔health, `focus_mental`↔focus, `spiritual_home_harmony`↔spiritual.
- In **each** of the six `what_this_means` strings: (1) name the **top 1–2 directions from `area_scores.<key>.top_directions`** for that theme (direction + score), (2) tie to **specific houses/planets OR empty sectors** from `directions`, (3) one sentence on **why** this combination matters for that life area (house meaning, not generic Vastu).
- **Anti-boilerplate:** Do **not** end more than **one** of the six life-area paragraphs with generic advice like "keep clutter-free / well-lit / clean / orderly" — preferably **none** in `what_this_means`. Put routine spatial steps in `action_plan` and `non_renovation_options` instead.
- **Anti-copy-paste:** If the same compass sector (e.g. West) appears in several life areas, each paragraph must use a **different angle** (e.g. wealth vs speech vs family vs assets), citing different `house_life_themes` or planet **temperaments** — never the same closing recommendation twice.
- When key houses for a theme map to a direction with **no natal grahas**, say that once plainly, then pivot using **`area_scores` for that theme** (which may highlight other winds where grahas actually concentrate) — do not fill every such case with identical "declutter the East" padding.
- **Dasha:** In at least **two** of the six `what_this_means` paragraphs (and in `snapshot.current_dasha_note`), tie `dasha_context` to a **specific house or planet placement** from the deterministic map, not vague "internalizing energy" alone.

- IMPORTANT: Do NOT use absolute statements like "toilets are bad in homes" or "storage is always bad".
- Treat room tags as direction-sensitive and conditional. Some placements can be acceptable/supportive depending on direction and upkeep.
- Use calibrated language: "supportive", "mixed", "challenging" rather than absolute good/bad.
- Never invent planets/signs/houses not present in deterministic input.
- No markdown, no bullets outside JSON array, no extra keys.

INPUT:
goal={goal}
door_facing={door_facing}
zone_tags={json.dumps(zone_tags, ensure_ascii=True, default=str)}
chart_identity={json.dumps(chart_identity, ensure_ascii=True, default=str)}
deterministic={json.dumps(full_payload, ensure_ascii=True, default=str)}
"""

    def _parse_json(self, text: str) -> Dict[str, Any]:
        raw = text.strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        return {
            "report_title_ai": "",
            "snapshot": {"topline": "", "current_dasha_note": "", "top_directions": []},
            "executive_summary_ai": "",
            "what_this_means": {},
            "direction_ai": {},
            "room_specific_guidance": [],
            "timing_plan": {"now_0_3_months": [], "months_3_6": [], "months_6_18": []},
            "action_plan": {"this_week": [], "this_month": [], "optional_upgrades": []},
            "non_renovation_options": [],
            "confidence_note_ai": "",
        }
