import os
import json
import re
from datetime import datetime
import google.generativeai as genai
from calculators.ashtakavarga import AshtakavargaCalculator

# Global oracle instance to maintain cache across requests
_oracle_instance = None

def get_oracle_instance():
    global _oracle_instance
    if _oracle_instance is None:
        _oracle_instance = AshtakvargaOracle()
    return _oracle_instance

class AshtakvargaOracle:
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        if api_key:
            genai.configure(api_key=api_key)
            from utils.admin_settings import get_gemini_analysis_model
            self.model = genai.GenerativeModel(get_gemini_analysis_model())
        
        # Sign names for reference
        self.sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
    
    @staticmethod
    def _to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _extract_house_rows(self, ashtakvarga_data):
        rows = []
        chart_rows = ashtakvarga_data.get('chart_ashtakavarga', {}) or {}
        for house in range(1, 13):
            row = chart_rows.get(str(house), {}) or {}
            sign_idx = self._to_int(row.get('sign'), 0)
            bindus = self._to_int(row.get('bindus'), 0)
            rows.append({
                "house": house,
                "sign_index": sign_idx,
                "sign": self.sign_names[sign_idx],
                "bindus": bindus,
                "strength": row.get('strength') or ("Strong" if bindus >= 30 else "Weak" if bindus <= 25 else "Moderate"),
            })
        return rows

    def _extract_bav_rows(self, ashtakvarga_data):
        rows = []
        individual = ((ashtakvarga_data.get('ashtakavarga') or {}).get('individual_charts') or {})
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            chart = individual.get(planet) or {}
            bindus = chart.get("bindus") or {}
            total = self._to_int(chart.get("total"), 0)
            if not bindus:
                continue
            per_sign = []
            for sign_idx in range(12):
                val = self._to_int(bindus.get(sign_idx), self._to_int(bindus.get(str(sign_idx)), 0))
                per_sign.append({"sign_index": sign_idx, "sign": self.sign_names[sign_idx], "bindus": val})
            strongest = max(per_sign, key=lambda item: item["bindus"])
            weakest = min(per_sign, key=lambda item: item["bindus"])
            rows.append({
                "planet": planet,
                "total": total,
                "per_sign": per_sign,
                "strongest_sign": strongest,
                "weakest_sign": weakest,
            })
        return rows

    @staticmethod
    def _normalize_text(value):
        return str(value or "").strip()

    @staticmethod
    def _tokenize_question(text):
        return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if token]

    def _infer_question_context(self, query_type, question_text):
        normalized_question = self._normalize_text(question_text)
        text = normalized_question.lower()
        tokens = set(self._tokenize_question(text))
        mode = "question" if text else (query_type or "overview")
        default_houses = [1, 2, 4, 5, 7, 9, 10, 11]
        default_planets = ["Sun", "Moon", "Mercury", "Jupiter", "Venus", "Saturn"]

        topic_rules = [
            {
                "focus": "career",
                "keywords": ["career", "job", "profession", "work", "office", "promotion", "boss", "employment", "role"],
                "houses": [2, 6, 10, 11],
                "planets": ["Sun", "Mercury", "Jupiter", "Saturn"],
                "weight": 3,
            },
            {
                "focus": "business_trade",
                "keywords": ["business", "trading", "trade", "stock", "stocks", "market", "markets", "share", "shares", "speculation", "speculative", "crypto", "option", "options", "futures", "intraday"],
                "houses": [2, 5, 8, 11],
                "planets": ["Mercury", "Jupiter", "Mars", "Rahu", "Saturn"],
                "weight": 4,
            },
            {
                "focus": "wealth",
                "keywords": ["money", "wealth", "income", "finance", "finances", "investment", "investments", "savings", "profit", "profits", "gain", "gains", "cash"],
                "houses": [2, 5, 9, 11],
                "planets": ["Jupiter", "Mercury", "Venus", "Saturn"],
                "weight": 3,
            },
            {
                "focus": "marriage_relationship",
                "keywords": ["marriage", "relationship", "relationships", "spouse", "partner", "love", "wife", "husband", "romance", "dating"],
                "houses": [2, 5, 7, 8, 12],
                "planets": ["Venus", "Moon", "Jupiter", "Mars", "Saturn"],
                "weight": 3,
            },
            {
                "focus": "health",
                "keywords": ["health", "disease", "body", "illness", "hospital", "recovery", "medical", "surgery", "symptom", "symptoms"],
                "houses": [1, 6, 8, 12],
                "planets": ["Sun", "Moon", "Mars", "Saturn"],
                "weight": 3,
            },
            {
                "focus": "property_home",
                "keywords": ["property", "home", "house", "vehicle", "realestate", "real", "estate", "land", "mother"],
                "houses": [4, 8, 11, 12],
                "planets": ["Moon", "Mars", "Venus", "Saturn"],
                "weight": 2,
            },
            {
                "focus": "education_children",
                "keywords": ["education", "study", "studies", "exam", "learning", "children", "child", "pregnancy", "creative", "creativity"],
                "houses": [4, 5, 9, 11],
                "planets": ["Jupiter", "Mercury", "Moon", "Sun"],
                "weight": 2,
            },
            {
                "focus": "travel_foreign",
                "keywords": ["travel", "foreign", "abroad", "visa", "journey", "journeys", "relocation", "overseas"],
                "houses": [3, 9, 12],
                "planets": ["Moon", "Jupiter", "Rahu", "Saturn"],
                "weight": 2,
            },
            {
                "focus": "litigation_obstacles",
                "keywords": ["court", "case", "legal", "lawsuit", "litigation", "enemy", "enemies", "obstacle", "obstacles", "debt", "debts"],
                "houses": [6, 8, 12],
                "planets": ["Mars", "Saturn", "Rahu", "Mercury"],
                "weight": 3,
            },
            {
                "focus": "timing",
                "keywords": ["when", "timing", "month", "period", "window", "date", "now", "currently", "today", "tomorrow", "week", "weeks"],
                "houses": [1, 6, 7, 10, 11],
                "planets": ["Moon", "Jupiter", "Saturn", "Mercury"],
                "weight": 2,
            },
            {
                "focus": "planetary_delivery",
                "keywords": ["planet", "graha", "bav", "deliver", "delivery", "mercury", "venus", "saturn", "jupiter", "mars", "sun", "moon"],
                "houses": [1, 2, 5, 7, 10, 11],
                "planets": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
                "weight": 2,
            },
            {
                "focus": "house_strength",
                "keywords": ["bhava", "houses", "housewise", "strongest house", "weakest house"],
                "houses": list(range(1, 13)),
                "planets": ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"],
                "weight": 1,
            },
        ]

        matched_topics = []
        all_houses = set()
        all_planets = set()
        reasons = []

        for rule in topic_rules:
            matched_keywords = []
            for keyword in rule["keywords"]:
                if " " in keyword:
                    if keyword in text:
                        matched_keywords.append(keyword)
                elif keyword in tokens:
                    matched_keywords.append(keyword)
            if matched_keywords:
                matched_topics.append({
                    "focus": rule["focus"],
                    "weight": rule["weight"] + len(matched_keywords),
                    "keywords": matched_keywords,
                })
                all_houses.update(rule["houses"])
                all_planets.update(rule["planets"])
                reasons.append(f"{rule['focus']}: {', '.join(sorted(set(matched_keywords)))}")

        if mode != "question":
            mode = "overview"

        if not matched_topics:
            focus = "general_overview"
            houses = default_houses
            planets = default_planets
        else:
            matched_topics.sort(key=lambda item: item["weight"], reverse=True)
            primary = matched_topics[0]["focus"]
            secondary = [item["focus"] for item in matched_topics[1:3]]
            focus = primary if not secondary else f"{primary}+{' + '.join(secondary)}"
            houses = sorted(all_houses)
            planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
            planets = [planet for planet in planet_order if planet in all_planets]

        if mode != "question":
            focus = "general_overview"
            reasons = []

        return {
            "mode": mode,
            "question_text": normalized_question,
            "focus": focus,
            "houses": houses,
            "planets": planets,
            "matched_topics": [item["focus"] for item in matched_topics],
            "focus_reasons": reasons,
        }

    def _build_topic_house_snapshot(self, current_rows, birth_rows, focus_houses):
        birth_map = {row["house"]: row for row in birth_rows}
        rows = []
        for house in focus_houses:
            row = next((item for item in current_rows if item["house"] == house), None)
            if not row:
                continue
            natal = birth_map.get(house, row)
            rows.append({
                "house": house,
                "sign": row["sign"],
                "current": row["bindus"],
                "natal": natal["bindus"],
                "delta": row["bindus"] - natal["bindus"],
                "strength": row["strength"],
            })
        return rows

    def _build_topic_bav_snapshot(self, current_bav_rows, birth_bav_rows, current_house_rows, focus_houses, focus_planets):
        house_sign_map = {row["house"]: row["sign_index"] for row in current_house_rows}
        birth_bav_map = {row["planet"]: row for row in birth_bav_rows}
        rows = []
        for row in current_bav_rows:
            if row["planet"] not in focus_planets:
                continue
            natal_match = birth_bav_map.get(row["planet"], row)
            house_values = []
            for house in focus_houses:
                sign_idx = house_sign_map.get(house)
                if sign_idx is None:
                    continue
                current_val = next((item["bindus"] for item in row.get("per_sign", []) if item["sign_index"] == sign_idx), 0)
                natal_val = next((item["bindus"] for item in natal_match.get("per_sign", []) if item["sign_index"] == sign_idx), current_val)
                house_values.append({
                    "house": house,
                    "sign": self.sign_names[sign_idx],
                    "current": current_val,
                    "natal": natal_val,
                    "delta": current_val - natal_val,
                })
            rows.append({
                "planet": row["planet"],
                "total": row["total"],
                "strongest_sign": row["strongest_sign"],
                "weakest_sign": row["weakest_sign"],
                "focus_house_values": house_values,
            })
        return rows

    def _build_fallback_response(self, birth_data, current_rows, birth_rows, current_bav, date, chart_type, question_context=None):
        strongest = max(current_rows, key=lambda item: item["bindus"]) if current_rows else None
        weakest = min(current_rows, key=lambda item: item["bindus"]) if current_rows else None
        strongest_bav = sorted(current_bav, key=lambda item: item["strongest_sign"]["bindus"], reverse=True)[:2]
        weakest_bav = sorted(current_bav, key=lambda item: item["weakest_sign"]["bindus"])[:2]
        question_context = question_context or {"mode": "overview", "question_text": "", "focus": "general_overview"}
        deltas = []
        birth_map = {row["house"]: row for row in birth_rows}
        for row in current_rows:
            natal = birth_map.get(row["house"])
            if natal:
                deltas.append({
                    "house": row["house"],
                    "sign": row["sign"],
                    "delta": row["bindus"] - natal["bindus"],
                    "current": row["bindus"],
                    "natal": natal["bindus"],
                })
        up = sorted(deltas, key=lambda item: item["delta"], reverse=True)[:2]
        down = sorted(deltas, key=lambda item: item["delta"])[:2]

        headline_bits = []
        if strongest:
            headline_bits.append(
                f"The strongest house is {strongest['house']} ({strongest['sign']}) with {strongest['bindus']} bindus."
            )
        if weakest:
            headline_bits.append(
                f"The weakest house is {weakest['house']} ({weakest['sign']}) with {weakest['bindus']} bindus."
            )
        if chart_type == 'transit' and up:
            headline_bits.append(
                f"Compared with birth, house {up[0]['house']} improves the most by {up[0]['delta']} bindus."
            )
        if question_context.get("mode") == "question" and question_context.get("question_text"):
            headline_bits.insert(0, f"Question focus: {question_context['question_text']}.")

        sections = [
            {
                "title": "Direct answer" if question_context.get("mode") == "question" else "Natal foundation",
                "bullets": [
                    f"Your strongest natal support sits in house {strongest['house']} ({strongest['sign']}) at {strongest['bindus']} bindus." if strongest else "Natal house support is being calculated.",
                    f"Your weakest natal field is house {weakest['house']} ({weakest['sign']}) at {weakest['bindus']} bindus, so this area needs more effort." if weakest else "Weak natal areas are being calculated.",
                ],
            },
            {
                "title": "Relevant house support" if question_context.get("mode") == "question" else "Current transit activation",
                "bullets": (
                    [f"House {item['house']} ({item['sign']}) is up by {item['delta']} bindus from birth, showing temporary support." for item in up if item["delta"] > 0] +
                    [f"House {item['house']} ({item['sign']}) is down by {abs(item['delta'])} bindus from birth, so delivery is weaker right now." for item in down if item["delta"] < 0]
                ) or ["Transit-vs-birth shifts are not available for this date."]
            },
            {
                "title": "Planet delivery (BAV)",
                "bullets": (
                    [f"{row['planet']} delivers best through {row['strongest_sign']['sign']} ({row['strongest_sign']['bindus']} bindus)." for row in strongest_bav] +
                    [f"{row['planet']} is strained in {row['weakest_sign']['sign']} ({row['weakest_sign']['bindus']} bindus)." for row in weakest_bav]
                ) or ["Planet-wise BAV detail is not available."]
            },
            {
                "title": "Timing and practical focus" if question_context.get("mode") == "question" else "Practical focus",
                "bullets": [
                    "Use the strongest houses for decisions that need momentum, confidence, or visible progress.",
                    "Delay major risk in the weakest houses unless dasha and transit support are also favorable.",
                ],
            },
        ]

        return {
            "analysis_title": "Ashtakavarga Analysis",
            "headline": " ".join(headline_bits).strip() or "Your Ashtakavarga shows a mixed but usable pattern of support.",
            "snapshot": {
                "date": date,
                "chart_type": chart_type,
                "total_bindus": sum(row["bindus"] for row in current_rows),
                "strongest_house": strongest,
                "weakest_house": weakest,
                "question_mode": question_context.get("mode", "overview"),
                "focus": question_context.get("focus", "general_overview"),
                "matched_topics": question_context.get("matched_topics", []),
            },
            "sections": sections,
            "key_takeaways": [bullet for section in sections for bullet in section["bullets"][:1]][:4],
            "oracle_message": " ".join(headline_bits).strip() or "Your Ashtakavarga shows a mixed but usable pattern of support.",
            "pillar_insights": [
                f"{row['sign']} (House {row['house']}): {row['bindus']} bindus - {row['strength']} support."
                for row in current_rows
            ],
        }

    
    def generate_complete_oracle(self, birth_data, ashtakvarga_data, date, query_type='general', timeline_years=3):
        """Generate complete oracle response with insights and timeline in single Gemini call"""
        
        try:
            birth_ashtakavarga_data = ashtakvarga_data.get('birth_ashtakavarga_data') or {}
            question_text = self._normalize_text(ashtakvarga_data.get('question_text'))
            sarva = ashtakvarga_data.get('ashtakavarga', {}).get('sarvashtakavarga', {})
            total_bindus = ashtakvarga_data.get('ashtakavarga', {}).get('total_bindus', 0)
            chart_type = str(ashtakvarga_data.get('chart_type') or 'lagna')
            current_house_rows = self._extract_house_rows(ashtakvarga_data)
            birth_house_rows = self._extract_house_rows(birth_ashtakavarga_data) if birth_ashtakavarga_data else current_house_rows
            current_bav_rows = self._extract_bav_rows(ashtakvarga_data)
            birth_bav_rows = self._extract_bav_rows(birth_ashtakavarga_data) if birth_ashtakavarga_data else current_bav_rows
            question_context = self._infer_question_context(query_type, question_text)
            focus_house_rows = self._build_topic_house_snapshot(current_house_rows, birth_house_rows, question_context["houses"])
            focus_bav_rows = self._build_topic_bav_snapshot(
                current_bav_rows,
                birth_bav_rows,
                current_house_rows,
                question_context["houses"],
                question_context["planets"],
            )
            
            # Get chart data for proper house calculation
            chart_data = ashtakvarga_data.get('chart_data', {})
            ascendant = chart_data.get('ascendant', 0)
            ascendant_sign = int(ascendant / 30) if ascendant else 0
            
            # Find strongest and weakest signs
            if sarva and len(sarva) > 0:
                strongest_sign = max(sarva.keys(), key=lambda k: sarva[k])
                weakest_sign = min(sarva.keys(), key=lambda k: sarva[k])
                # Convert to int if string
                strongest_sign = int(strongest_sign) if isinstance(strongest_sign, str) else strongest_sign
                weakest_sign = int(weakest_sign) if isinstance(weakest_sign, str) else weakest_sign
                max_bindus = sarva.get(str(strongest_sign), sarva.get(strongest_sign, 0))
                min_bindus = sarva.get(str(weakest_sign), sarva.get(weakest_sign, 0))
            else:
                strongest_sign = 0
                weakest_sign = 0
                max_bindus = 0
                min_bindus = 0
            
            # Format distribution for prompt with proper house numbers
            distribution_text = ""
            for i in range(12):
                # Keys are strings in the sarva dict, so use str(i)
                points = sarva.get(str(i), 0) if sarva else 0
                strength = "Strong" if points >= 30 else "Weak" if points <= 25 else "Moderate"
                # Calculate proper house number from ascendant
                house_num = ((i - ascendant_sign) % 12) + 1
                distribution_text += f"- {self.sign_names[i]} (House {house_num}): {points} points ({strength})\n"

            house_shift_text = ""
            birth_map = {row["house"]: row for row in birth_house_rows}
            for row in current_house_rows:
                natal = birth_map.get(row["house"])
                natal_bindus = natal["bindus"] if natal else row["bindus"]
                delta = row["bindus"] - natal_bindus
                house_shift_text += (
                    f"- House {row['house']} ({row['sign']}): natal {natal_bindus}, current {row['bindus']}, delta {delta:+d}\n"
                )

            bav_text = ""
            for row in current_bav_rows:
                natal_match = next((item for item in birth_bav_rows if item["planet"] == row["planet"]), None)
                natal_best = natal_match["strongest_sign"]["bindus"] if natal_match else row["strongest_sign"]["bindus"]
                natal_worst = natal_match["weakest_sign"]["bindus"] if natal_match else row["weakest_sign"]["bindus"]
                bav_text += (
                    f"- {row['planet']}: strongest {row['strongest_sign']['sign']}={row['strongest_sign']['bindus']} "
                    f"(natal {natal_best}), weakest {row['weakest_sign']['sign']}={row['weakest_sign']['bindus']} "
                    f"(natal {natal_worst}), total={row['total']}\n"
                )

            focus_house_text = ""
            for row in focus_house_rows:
                focus_house_text += (
                    f"- House {row['house']} ({row['sign']}): current {row['current']}, natal {row['natal']}, "
                    f"delta {row['delta']:+d}, strength={row['strength']}\n"
                )

            focus_bav_text = ""
            for row in focus_bav_rows:
                focus_bav_text += (
                    f"- {row['planet']}: total {row['total']}, strongest {row['strongest_sign']['sign']}={row['strongest_sign']['bindus']}, "
                    f"weakest {row['weakest_sign']['sign']}={row['weakest_sign']['bindus']}\n"
                )
                for item in row["focus_house_values"]:
                    focus_bav_text += (
                        f"  • House {item['house']} ({item['sign']}): current {item['current']}, natal {item['natal']}, delta {item['delta']:+d}\n"
                    )

            # CONSTRUCTION THE PROMPT
            prompt = f"""
You are an expert Vedic Astrologer specializing in Ashtakavarga. 
Your goal is to provide CLEAR, DATA-DRIVEN, and PRACTICAL Ashtakavarga analysis that gives real value.
Do NOT use flowery, mystical, vague, or poetic language. Speak like a serious consultant.

USER PROFILE:
- Name: {birth_data.get('name', 'Client')}
- Birth Date: {birth_data.get('date')} (YYYY-MM-DD)
- Current Date for Analysis: {date}
- Analysis Mode: {"Transit overlay relative to natal chart" if chart_type == "transit" else "Natal chart baseline"}
- Request Mode: {question_context['mode']}
- User Question: {question_context['question_text'] or "Overview reading"}
- Focus Topic: {question_context['focus']}
- Matched Topic Drivers: {", ".join(question_context.get('matched_topics', [])) or "overview"}
- Focus Reasons: {" | ".join(question_context.get('focus_reasons', [])) or "No special focus drivers"}
- Priority Houses: {", ".join(str(house) for house in question_context['houses'])}
- Priority Planets: {", ".join(question_context['planets'])}

ASHTAKAVARGA DATA (The Logic):
- Total Bindus: {total_bindus}/337
- Strongest Sector: {self.sign_names[strongest_sign]} ({max_bindus} points)
- Weakest Sector: {self.sign_names[weakest_sign]} ({min_bindus} points)

CURRENT HOUSE SCORECARD:
{distribution_text}

HOUSE SHIFTS VS NATAL:
{house_shift_text}

PLANET DELIVERY (BAV) SNAPSHOT:
{bav_text}

QUESTION-FOCUSED HOUSE SNAPSHOT:
{focus_house_text or "- No focused house snapshot available.\n"}

QUESTION-FOCUSED BAV SNAPSHOT:
{focus_bav_text or "- No focused BAV snapshot available.\n"}

INSTRUCTIONS:
1. Give a grounded Ashtakavarga reading, not a horoscope slogan.
2. If User Question is present, answer that exact question first. Do not drift into a generic overview.
3. Explain natal house support clearly from SAV.
4. If this is a transit date, compare current house support to natal and explain what is temporarily activated or strained.
5. Use Bhinnashtakavarga seriously:
   - explain which planets currently deliver well,
   - which planets are strained,
   - and where natal vs current BAV changes matter.
6. Focus on real value for the customer: career, money, relationships, health, confidence, family, gains, losses.
7. If the question is topic-specific, use ALL relevant houses implied by the topic drivers, not just one broad category.
8. Explicitly say where Ashtakavarga supports, strains, or only partially supports the result.
9. If the question asks about "right now" or timing, mention whether the support is natal, current transit, or both.
10. Avoid percentages as the main message. Use actual bindu counts and house language.
11. Do NOT output "Power Actions", mystical labels, or fake confidence slogans.

REQUIRED JSON FORMAT:
{{
  "analysis_title": "Ashtakavarga Analysis",
  "headline": "2-3 sentences with the real top conclusion using actual bindu counts and house areas, answering the user question first if present.",
  "snapshot": {{
    "date": "{date}",
    "chart_type": "{chart_type}",
    "total_bindus": {total_bindus},
    "strongest_house": {{"house": 11, "sign": "Aquarius", "bindus": 34}},
    "weakest_house": {{"house": 8, "sign": "Capricorn", "bindus": 21}},
    "question_mode": "{question_context['mode']}",
    "focus": "{question_context['focus']}"
  }},
  "key_takeaways": [
    "4 short, concrete takeaways"
  ],
  "sections": [
    {{
      "title": "{'Direct answer' if question_context['mode'] == 'question' else 'Natal foundation'}",
      "bullets": ["2-4 bullets"]
    }},
    {{
      "title": "{'Relevant house support' if question_context['mode'] == 'question' else 'Current transit activation'}",
      "bullets": ["2-4 bullets; if natal chart only, explain current emphasis without inventing transit."]
    }},
    {{
      "title": "Planet delivery (BAV)",
      "bullets": ["2-4 bullets naming actual planets and signs"]
    }},
    {{
      "title": "{'Timing and practical focus' if question_context['mode'] == 'question' else 'Practical focus'}",
      "bullets": ["2-4 bullets with useful decision guidance"]
    }}
  ],
  "oracle_message": "A short summary version of the headline",
  "pillar_insights": [
    "One short line per house/sign using actual bindu counts"
  ]
}}

Return ONLY valid JSON. No markdown formatting. No explanatory text.
"""
            if self.model is None:
                return self._build_fallback_response(
                    birth_data=birth_data,
                    current_rows=current_house_rows,
                    birth_rows=birth_house_rows,
                    current_bav=current_bav_rows,
                    date=date,
                    chart_type=chart_type,
                    question_context=question_context,
                )

            response = self.model.generate_content(prompt)
            
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            complete_data = json.loads(text.strip())
            complete_data.setdefault("analysis_title", "Ashtakavarga Analysis")
            complete_data.setdefault("oracle_message", complete_data.get("headline") or "")
            complete_data.setdefault("snapshot", {})
            complete_data["snapshot"].setdefault("question_mode", question_context["mode"])
            complete_data["snapshot"].setdefault("focus", question_context["focus"])
            return complete_data
            
        except Exception as e:
            return self._build_fallback_response(
                birth_data=birth_data,
                current_rows=current_house_rows,
                birth_rows=birth_house_rows,
                current_bav=current_bav_rows,
                date=date,
                chart_type=chart_type,
                question_context=question_context if 'question_context' in locals() else None,
            )
    
    def generate_oracle_insight(self, birth_data, ashtakvarga_data, date):
        """Returns complete oracle data for frontend caching"""
        return self.generate_complete_oracle(birth_data, ashtakvarga_data, date)
