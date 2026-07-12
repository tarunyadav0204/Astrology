from __future__ import annotations

from typing import Any, Dict, List, Optional

from .gandanta_calculator import GandantaCalculator
from .mudakku_calculator import MudakkuCalculator
from .mrityu_bhaga_calculator import MrityuBhagaCalculator
from .nakshatra_remedy_calculator import NakshatraRemedyCalculator


class RemedyEngine:
    """
    Builds a structured remedy blueprint from chart evidence.

    The goal is not to invent a generic list of upayas. We use the active
    period planets, focus houses, nakshatra-level remedies, and special block
    indicators like Gandanta / Mudakku / Mrityu Bhaga when available.
    """

    GEMSTONES = {
        "Sun": "Ruby, only if suitability checks support it",
        "Moon": "Pearl, only if suitability checks support it",
        "Mars": "Red Coral, only if suitability checks support it",
        "Mercury": "Emerald, only if suitability checks support it",
        "Jupiter": "Yellow Sapphire, only if suitability checks support it",
        "Venus": "Diamond or White Sapphire, only if suitability checks support it",
        "Saturn": "Blue Sapphire, only if suitability checks support it",
        "Rahu": "Hessonite, only if suitability checks support it",
        "Ketu": "Cat's Eye, only if suitability checks support it",
    }

    MANTRAS = {
        "Sun": "Om Suryaya Namaha",
        "Moon": "Om Chandraya Namaha",
        "Mars": "Om Mangalaya Namaha",
        "Mercury": "Om Budhaya Namaha",
        "Jupiter": "Om Gurave Namaha",
        "Venus": "Om Shukraya Namaha",
        "Saturn": "Om Sham Shanicharaya Namaha",
        "Rahu": "Om Rahave Namaha",
        "Ketu": "Om Ketave Namaha",
    }

    CHARITY = {
        "Sun": "Donate wheat, copper, or support father/mentor figures on Sundays.",
        "Moon": "Donate milk, white cloth, rice, or support women/mothers on Mondays.",
        "Mars": "Donate red lentils, jaggery, or support soldiers, athletes, or blood donation drives on Tuesdays.",
        "Mercury": "Donate green vegetables, books, stationery, or support students on Wednesdays.",
        "Jupiter": "Donate turmeric, yellow food, or support teachers, priests, and children on Thursdays.",
        "Venus": "Donate white sweets, clothes, or support women, art, and harmony on Fridays.",
        "Saturn": "Donate black sesame, blankets, or support the poor, elderly, and laborers on Saturdays.",
        "Rahu": "Donate dark blankets, mustard oil, or support overlooked communities and addiction recovery work.",
        "Ketu": "Donate blankets, sesame, or support temples, stray animals, and spiritual learning.",
    }

    SEVA = {
        "Sun": "Serve elders and authorities with sincerity; keep promises.",
        "Moon": "Care for the mother-line, home peace, and emotional steadiness.",
        "Mars": "Channel energy into disciplined exercise and protective service.",
        "Mercury": "Use speech carefully; help with writing, teaching, or communication.",
        "Jupiter": "Support teachers, mentors, and dharmic study.",
        "Venus": "Support women, arts, relationships, and respectful conduct.",
        "Saturn": "Serve through patient labor, consistency, and practical help.",
        "Rahu": "Serve in unconventional, marginalized, or crisis contexts without drama.",
        "Ketu": "Serve quietly, spiritually, and without needing credit.",
    }

    DIET = {
        "Sun": "Warm, simple, sattvic food; avoid overindulgence and late nights.",
        "Moon": "Hydrating, cooling food; protect sleep and routine.",
        "Mars": "Reduce excess heat, anger, alcohol, and overly spicy food.",
        "Mercury": "Light, clean meals; keep the nervous system calm.",
        "Jupiter": "Moderate rich foods; avoid excess sugar and lazy overeating.",
        "Venus": "Moderation in sweets, comfort food, and sensory excess.",
        "Saturn": "Simple, disciplined eating; avoid irregularity.",
        "Rahu": "Reduce processed food, stimulants, and addictive patterns.",
        "Ketu": "Keep meals light and consistent; avoid erratic fasting extremes.",
    }

    COLORS = {
        "Sun": "Gold, saffron, orange",
        "Moon": "White, silver, cream",
        "Mars": "Red, deep orange",
        "Mercury": "Green, light green",
        "Jupiter": "Yellow, mustard",
        "Venus": "White, pastel pink",
        "Saturn": "Blue, dark grey, black",
        "Rahu": "Smoke grey, dark blue, earthy tones",
        "Ketu": "Dull white, smoky grey, muted tones",
    }

    DIRECTIONS = {
        "Sun": "East",
        "Moon": "North-West",
        "Mars": "South",
        "Mercury": "North",
        "Jupiter": "North-East",
        "Venus": "South-East",
        "Saturn": "West",
        "Rahu": "South-West",
        "Ketu": "North-East",
    }

    HOUSE_THEME_LABELS = {
        1: "self, vitality, personal direction",
        2: "income, family assets, speech, resources",
        3: "effort, communication, initiative, short moves",
        4: "home, peace, property, emotional base",
        5: "creativity, children, romance, learning, speculative intelligence",
        6: "workload, conflict, debt, health strain, disciplined service",
        7: "partners, clients, agreements, spouse themes",
        8: "research, hidden matters, transformation, deep healing, crisis navigation",
        9: "fortune, mentors, dharma, long-range support",
        10: "career, public role, authority, visibility",
        11: "gains, networks, fulfillment, support circles",
        12: "retreat, foreign links, sleep, isolation, letting go, behind-the-scenes work",
    }

    def __init__(self, chart_data: Dict[str, Any], divisional_charts: Optional[Dict[str, Any]] = None):
        self.chart_data = chart_data or {}
        self.divisional_charts = divisional_charts or {}
        self._nakshatra_engine = NakshatraRemedyCalculator()
        self._mudakku_engine = MudakkuCalculator(self.chart_data)
        self._gandanta_engine = GandantaCalculator(self.chart_data)
        self._mrityu_engine = MrityuBhagaCalculator(self.chart_data)

    def build_remedy_blueprint(
        self,
        *,
        question: str,
        category: str,
        instant_parashari: Dict[str, Any],
        normalized_evidence: Dict[str, Any],
        current_dashas_context: Dict[str, Any],
        target_chart_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        focus_houses = [int(h) for h in (instant_parashari.get("focus_houses") or []) if str(h).strip().isdigit()]
        active_planets = self._candidate_planets(current_dashas_context, focus_houses)
        chart_planets = (self.chart_data.get("planets") or {}) if isinstance(self.chart_data, dict) else {}
        candidate_planet_rows = [self._planet_summary(planet, chart_planets.get(planet) or {}) for planet in active_planets]
        special_points = self._special_point_summary()

        remedy_sections = {
            "house_expression": self._house_expression_guidance(active_planets, focus_houses, current_dashas_context),
            "gemstones": self._section_for_planets(active_planets, "gemstone"),
            "nakshatra": self._section_for_planets(active_planets, "nakshatra"),
            "mantras": self._section_for_planets(active_planets, "mantra"),
            "biological": self._section_for_planets(active_planets, "biological"),
            "ritual": self._section_for_planets(active_planets, "ritual"),
            "charity": self._section_for_planets(active_planets, "charity"),
            "seva": self._section_for_planets(active_planets, "seva"),
            "diet": self._section_for_planets(active_planets, "diet"),
            "color_and_clothing": self._section_for_planets(active_planets, "color"),
            "direction_and_timing": self._direction_and_timing(active_planets, instant_parashari, normalized_evidence),
            "behavioral": self._behavioral_guidance(category, active_planets, instant_parashari, target_chart_context),
        }

        if special_points.get("mudakku"):
            remedy_sections.setdefault("special_blockages", []).append({
                "label": "Mudakku / Modakku",
                "summary": special_points["mudakku"]["summary"],
                "action": "Use this as a focused block-analysis layer when the issue feels repetitive or stubborn.",
            })
        if special_points.get("gandanta"):
            remedy_sections.setdefault("special_blockages", []).append({
                "label": "Gandanta / G/M zone",
                "summary": special_points["gandanta"]["summary"],
                "action": "Handle with slower, grounding remedies: mantra, steady routine, and patience before escalation.",
            })
        if special_points.get("mrityu_bhaga"):
            remedy_sections.setdefault("special_blockages", []).append({
                "label": "Mrityu Bhaga",
                "summary": special_points["mrityu_bhaga"]["summary"],
                "action": "Keep this as a caution layer only; pair it with practical care and avoid fear-based language.",
            })

        return {
            "answer_mode": "remedy_action",
            "category": category,
            "question_focus": self._summarize_focus(question, category, instant_parashari, normalized_evidence),
            "candidate_planets": candidate_planet_rows,
            "special_points": special_points,
            "priority_order": active_planets[:3],
            "constructive_house_expression": self._house_expression_guidance(active_planets, focus_houses, current_dashas_context),
            "remedy_sections": remedy_sections,
            "caution": self._caution_line(active_planets, special_points),
            "follow_up_prompts": self._follow_up_prompts(category),
        }

    def _candidate_planets(self, current_dashas_context: Dict[str, Any], focus_houses: List[int]) -> List[str]:
        planets: List[str] = []
        for lvl in ("md", "ad", "pd", "sk", "pr"):
            row = (current_dashas_context or {}).get(lvl) or {}
            planet = str(row.get("planet") or "").strip()
            if planet and planet not in planets:
                planets.append(planet)
        if not planets:
            for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
                if planet in (self.chart_data.get("planets") or {}):
                    planets.append(planet)
        if focus_houses:
            for planet, data in (self.chart_data.get("planets") or {}).items():
                if not isinstance(data, dict):
                    continue
                if int(data.get("house") or 0) in focus_houses and planet not in planets:
                    planets.append(planet)
        return planets[:4]

    def _planet_summary(self, planet: str, planet_row: Dict[str, Any]) -> Dict[str, Any]:
        nakshatra = str(planet_row.get("nakshatra") or "").strip()
        pada = planet_row.get("nakshatra_pada", {}).get("pada") if isinstance(planet_row.get("nakshatra_pada"), dict) else None
        summary = {
            "planet": planet,
            "house": planet_row.get("house"),
            "sign": planet_row.get("sign_name"),
            "nakshatra": nakshatra,
            "pada": pada,
            "gemstone": self.GEMSTONES.get(planet),
            "mantra": self.MANTRAS.get(planet),
            "charity": self.CHARITY.get(planet),
            "seva": self.SEVA.get(planet),
            "diet": self.DIET.get(planet),
            "color": self.COLORS.get(planet),
            "direction": self.DIRECTIONS.get(planet),
        }
        if nakshatra and pada:
            nk_remedy = self._nakshatra_engine.get_remedy(planet, nakshatra, int(pada))
            summary["nakshatra_remedy"] = {
                "shakti": nk_remedy.get("shakti"),
                "deity": nk_remedy.get("deity"),
                "vriksha": nk_remedy.get("vriksha"),
                "mantra": nk_remedy.get("mantra"),
                "tier_1_biological": nk_remedy.get("remedy_tier_1_biological"),
                "tier_2_sound": nk_remedy.get("remedy_tier_2_sound"),
                "tier_3_ritual": nk_remedy.get("remedy_tier_3_ritual"),
                "tier_4_dietary": nk_remedy.get("remedy_tier_4_dietary"),
                "tier_5_vastra": nk_remedy.get("remedy_tier_5_vastra"),
            }
        return summary

    def _section_for_planets(self, planets: List[str], section: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for planet in planets[:3]:
            row = self._planet_summary(planet, (self.chart_data.get("planets") or {}).get(planet) or {})
            if section == "gemstone":
                out.append({"planet": planet, "text": row.get("gemstone")})
            elif section == "nakshatra":
                nk = row.get("nakshatra_remedy") or {}
                text = None
                if nk:
                    text = " | ".join(
                        part
                        for part in [
                            f"Shakti: {nk.get('shakti')}",
                            f"Deity: {nk.get('deity')}",
                            f"Vriksha: {nk.get('vriksha')}",
                            f"Pada syllable: {nk.get('pada_syllable')}",
                        ]
                        if part and not part.endswith(": None")
                    )
                if not text:
                    text = f"Use the nakshatra-specific remedy layer for {planet}."
                out.append({"planet": planet, "text": text, "details": nk})
            elif section == "mantra":
                text = row.get("mantra")
                if row.get("nakshatra_remedy") and row["nakshatra_remedy"].get("tier_2_sound"):
                    text = row["nakshatra_remedy"]["tier_2_sound"]
                out.append({"planet": planet, "text": text})
            elif section == "biological":
                text = row.get("nakshatra_remedy", {}).get("tier_1_biological") or f"Nurture {planet} through simple, steady bodily routines."
                out.append({"planet": planet, "text": text})
            elif section == "ritual":
                text = row.get("nakshatra_remedy", {}).get("tier_3_ritual") or f"Use a quiet ritual for {planet} with discipline and sincerity."
                out.append({"planet": planet, "text": text})
            elif section == "charity":
                out.append({"planet": planet, "text": row.get("charity")})
            elif section == "seva":
                out.append({"planet": planet, "text": row.get("seva")})
            elif section == "diet":
                text = row.get("nakshatra_remedy", {}).get("tier_4_dietary") or row.get("diet")
                out.append({"planet": planet, "text": text})
            elif section == "color":
                text = row.get("nakshatra_remedy", {}).get("tier_5_vastra") or row.get("color")
                out.append({"planet": planet, "text": text})
        return [row for row in out if row.get("text")]

    def _direction_and_timing(
        self,
        planets: List[str],
        instant_parashari: Dict[str, Any],
        normalized_evidence: Dict[str, Any],
    ) -> List[str]:
        lines: List[str] = []
        for planet in planets[:3]:
            direction = self.DIRECTIONS.get(planet)
            if direction:
                lines.append(f"Orient work and prayer toward {direction} while working with {planet} themes.")
        period_window = instant_parashari.get("period_window") or {}
        if period_window.get("kind") == "window":
            lines.append(
                f"Use the requested window {period_window.get('start')} to {period_window.get('end')} for steady repetition rather than one-off fixes."
            )
        if normalized_evidence.get("month_tone", {}).get("enabled"):
            tone = normalized_evidence["month_tone"].get("summary")
            if tone:
                lines.append(tone)
        return lines[:4]

    def _behavioral_guidance(
        self,
        category: str,
        planets: List[str],
        instant_parashari: Dict[str, Any],
        target_chart_context: Optional[Dict[str, Any]],
    ) -> List[str]:
        category = str(category or "general").lower()
        lines = []
        if category in {"health"}:
            lines.append("Keep routines stable, sleep regular, and avoid forcing a quick cure when the chart wants gradual repair.")
        elif category in {"career", "job", "business"}:
            lines.append("Use disciplined effort, skill-building, and consistent follow-through instead of switching direction impulsively.")
        elif category in {"marriage", "relationship", "love", "partner", "spouse"}:
            lines.append("Use softer speech, repair patterns quickly, and do not let pride or silence harden the issue.")
        else:
            lines.append("Reduce the friction that repeats the problem: overreaction, inconsistency, secrecy, or impatience.")
        if planets:
            lines.append(f"Support {', '.join(planets[:2])} through steady habits instead of expecting one dramatic remedy.")
        if target_chart_context:
            target_name = (target_chart_context.get("target_birth_summary") or {}).get("name")
            if target_name:
                lines.append(f"If this is about {target_name}, keep the remedy tied to their own chart frame.")
        return lines[:4]

    def _house_expression_guidance(
        self,
        planets: List[str],
        focus_houses: List[int],
        current_dashas_context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        house_set = list(dict.fromkeys([int(h) for h in focus_houses if int(h) in self.HOUSE_THEME_LABELS]))
        for planet in planets[:3]:
            row = (self.chart_data.get("planets") or {}).get(planet) or {}
            natal_house = row.get("house")
            natal_sign = row.get("sign_name")
            planet_house_label = self.HOUSE_THEME_LABELS.get(int(natal_house or 0))
            current_dasha_house_notes: List[str] = []
            for lvl in ("md", "ad", "pd", "sk", "pr"):
                dasha_row = (current_dashas_context or {}).get(lvl) or {}
                if str(dasha_row.get("planet") or "").strip() != planet:
                    continue
                for h in dasha_row.get("lordships") or []:
                    if isinstance(h, int) and h in self.HOUSE_THEME_LABELS:
                        current_dasha_house_notes.append(self.HOUSE_THEME_LABELS[h])
            constructive_focuses: List[str] = []
            if house_set:
                for house in house_set[:3]:
                    constructive_focuses.append(self.HOUSE_THEME_LABELS.get(house, f"house {house}"))
            elif natal_house in self.HOUSE_THEME_LABELS:
                constructive_focuses.append(self.HOUSE_THEME_LABELS[int(natal_house)])
            if current_dasha_house_notes:
                constructive_focuses.extend(current_dasha_house_notes[:2])
            constructive_focuses = [item for item in dict.fromkeys(constructive_focuses) if item]
            if not constructive_focuses and planet_house_label:
                constructive_focuses.append(planet_house_label)
            rows.append({
                "planet": planet,
                "natal_house": natal_house,
                "natal_sign": natal_sign,
                "constructive_expression": f"Let {planet} work through its constructive house themes: {', '.join(constructive_focuses[:3])}." if constructive_focuses else f"Let {planet} work through disciplined, constructive expression instead of reactive expression.",
                "positive_direction": self._positive_house_direction(planet, natal_house, constructive_focuses[:3]),
            })
        if house_set:
            rows.append({
                "planet": "house_focus",
                "natal_house": None,
                "natal_sign": None,
                "constructive_expression": f"Channel the pressure into these focus houses as strengths: {', '.join(self.HOUSE_THEME_LABELS.get(h, f'house {h}') for h in house_set[:3])}.",
                "positive_direction": "Use the house as an active strength, not just a problem zone.",
            })
        return rows[:4]

    def _positive_house_direction(self, planet: str, natal_house: Any, constructive_focuses: List[str]) -> str:
        house_label = self.HOUSE_THEME_LABELS.get(int(natal_house or 0)) if str(natal_house or "").isdigit() else None
        focus_text = constructive_focuses[0] if constructive_focuses else (house_label or "the relevant house")
        if planet == "Rahu":
            return f"Rahu does well when it is used for research, unusual systems, technology, depth work, and hidden-pattern discovery in {focus_text}."
        if planet == "Ketu":
            return f"Ketu does well when it is used for detachment, deep study, spiritual focus, and quiet mastery in {focus_text}."
        if planet == "Saturn":
            return f"Saturn is strengthened by patience, structure, repetition, and long-term building in {focus_text}."
        if planet == "Mercury":
            return f"Mercury is strengthened by analysis, writing, logic, and communication in {focus_text}."
        if planet == "Jupiter":
            return f"Jupiter is strengthened by teaching, advice, ethics, and synthesis in {focus_text}."
        if planet == "Venus":
            return f"Venus is strengthened by aesthetics, harmony, relationships, and refinement in {focus_text}."
        if planet == "Mars":
            return f"Mars is strengthened by action, courage, problem-solving, and disciplined effort in {focus_text}."
        if planet == "Moon":
            return f"Moon is strengthened by emotional care, rhythm, nourishment, and responsiveness in {focus_text}."
        if planet == "Sun":
            return f"Sun is strengthened by leadership, confidence, visibility, and purpose in {focus_text}."
        return f"Use {planet} in a constructive way through {focus_text}."

    def _special_point_summary(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        try:
            mudakku = self._mudakku_engine.get_mudakku_summary(self.chart_data)
            out["mudakku"] = {
                "summary": f"Sun nakshatra {mudakku.get('sun_nakshatra')} -> Mudakku nakshatra {mudakku.get('mudakku_nakshatra')} / {mudakku.get('mudakku_rashi')}.",
                "details": mudakku,
            }
        except Exception:
            pass
        try:
            gandanta = self._gandanta_engine.calculate_gandanta_analysis()
            if gandanta.get("planets_in_gandanta") or gandanta.get("lagna_gandanta", {}).get("is_gandanta") or gandanta.get("moon_gandanta", {}).get("is_gandanta"):
                out["gandanta"] = {
                    "summary": self._summarize_gandanta(gandanta),
                    "details": gandanta,
                }
        except Exception:
            pass
        try:
            mrityu = self._mrityu_engine.analyze_chart_mrityu_bhaga()
            if mrityu.get("planets_in_mrityu"):
                out["mrityu_bhaga"] = {
                    "summary": self._summarize_mrityu_bhaga(mrityu),
                    "details": mrityu,
                }
        except Exception:
            pass
        return out

    def _summarize_gandanta(self, gandanta: Dict[str, Any]) -> str:
        planets = [row.get("planet") for row in (gandanta.get("planets_in_gandanta") or [])[:4] if row.get("planet")]
        if planets:
            return f"Gandanta is active for {', '.join(planets)}."
        if gandanta.get("lagna_gandanta", {}).get("is_gandanta"):
            return "Lagna is in Gandanta."
        if gandanta.get("moon_gandanta", {}).get("is_gandanta"):
            return "Moon is in Gandanta."
        return "Gandanta is present in a subtle form."

    def _summarize_mrityu_bhaga(self, mrityu: Dict[str, Any]) -> str:
        planets = [row.get("planet") for row in (mrityu.get("planets_in_mrityu") or [])[:4] if row.get("planet")]
        return f"Mrityu Bhaga touches {', '.join(planets)}." if planets else "Mrityu Bhaga is present."

    def _summarize_focus(
        self,
        question: str,
        category: str,
        instant_parashari: Dict[str, Any],
        normalized_evidence: Dict[str, Any],
    ) -> str:
        risks = list((instant_parashari.get("top_risks") or [])[:2])
        if risks:
            return " ".join(risks)
        topic = (normalized_evidence.get("topic_confirmation") or {}).get("topic_signals") or {}
        if topic:
            return f"Remedy focus is tied to {category} and the active chart pressure."
        return f"Use the remedy mode to address the chart issue raised in: {question}"

    def _caution_line(self, planets: List[str], special_points: Dict[str, Any]) -> str:
        if special_points.get("mrityu_bhaga"):
            return "Treat gemstone suggestions as optional and suitability-dependent; keep the emphasis on mantra, behavior, charity, and steady routine."
        if planets:
            return f"Do not apply every remedy at once; start with the first planet in the priority order and measure change."
        return "Start with one or two remedies only and keep them simple."

    def _follow_up_prompts(self, category: str) -> List[str]:
        category = str(category or "general").lower()
        if category in {"marriage", "relationship", "love", "partner", "spouse"}:
            return ["Show spouse-focused remedies", "Add compatibility-specific upayas", "Focus only on continuity remedies"]
        if category in {"career", "job", "business"}:
            return ["Show career remedies by planet", "Add work-function remedies", "Focus on status and stability"]
        if category == "health":
            return ["Show routine-based remedies", "Add calming remedies", "Focus on body and sleep support"]
        return ["Show the next remedy layer", "Focus on the strongest planet", "Add special blockage remedies"]
