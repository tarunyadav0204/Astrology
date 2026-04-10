import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

import google.generativeai as genai

from db import get_conn, execute


def _normalize_for_match(text: str) -> str:
    s = (text or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s]", "", s)
    return s


def _containment_duplicate(a_norm: str, b_norm: str, min_chars: int = 18) -> bool:
    if not a_norm or not b_norm:
        return False
    shorter, longer = (a_norm, b_norm) if len(a_norm) <= len(b_norm) else (b_norm, a_norm)
    if len(shorter) < min_chars:
        return False
    return shorter in longer


def _similarity_normalized(a_norm: str, b_norm: str) -> float:
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def _is_near_duplicate(category: str, fact_text: str, existing: List[Tuple[str, str]]) -> bool:
    """True if fact_text is the same or semantically redundant vs any stored fact."""
    n_new = _normalize_for_match(fact_text)
    if len(n_new) < 6:
        return False
    for ex_cat, ex_fact in existing:
        n_ex = _normalize_for_match(ex_fact)
        if not n_ex:
            continue
        if n_new == n_ex:
            return True
        same_cat = ex_cat == category
        ratio = _similarity_normalized(n_new, n_ex)
        if same_cat and (ratio >= 0.86 or _containment_duplicate(n_new, n_ex)):
            return True
        if not same_cat and ratio >= 0.93:
            return True
    return False


def _dedupe_extracted_batch(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicates within the model's single response (order-preserving)."""
    out: List[Dict[str, Any]] = []
    seen_pairs: List[Tuple[str, str]] = []
    for item in facts:
        if not isinstance(item, dict):
            continue
        cat = (item.get("category") or "").strip()
        fact = (item.get("fact") or "").strip()
        if not cat or not fact:
            continue
        if _is_near_duplicate(cat, fact, seen_pairs):
            continue
        seen_pairs.append((cat, fact))
        out.append(item)
    return out


class FactExtractor:
    """Extract and store user facts from conversations using Gemini Flash"""

    # Cap rows loaded for dedupe + prompt (performance)
    _EXISTING_FETCH_LIMIT = 400
    _PROMPT_EXISTING_MAX = 40

    def __init__(self):
        from dotenv import load_dotenv
        import os

        load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ GEMINI_API_KEY not found - fact extraction disabled")
            self.model = None
            return

        genai.configure(api_key=api_key)
        from utils.admin_settings import get_gemini_analysis_model

        self.model = genai.GenerativeModel(get_gemini_analysis_model())

    def _load_existing_rows(self, birth_chart_id: int) -> List[Tuple[str, str]]:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT category, fact
                FROM user_facts
                WHERE birth_chart_id = %s
                ORDER BY extracted_at DESC
                LIMIT %s
                """,
                (birth_chart_id, self._EXISTING_FETCH_LIMIT),
            )
            return list(cur.fetchall() or [])

    def _format_existing_for_prompt(self, rows: List[Tuple[str, str]]) -> str:
        if not rows:
            return "(none yet)"
        lines = []
        for cat, fact in rows[: self._PROMPT_EXISTING_MAX]:
            lines.append(f"- [{cat}] {fact}")
        return "\n".join(lines)

    async def extract_facts(self, question: str, response: str, birth_chart_id: int):
        """Extract facts from Q&A pair and store them"""
        from datetime import datetime

        if not self.model:
            print("⚠️ Fact extraction skipped - model not initialized")
            return

        existing_rows = self._load_existing_rows(birth_chart_id)
        existing_for_prompt = self._format_existing_for_prompt(existing_rows)

        prompt = f"""Extract ONLY factual information that the USER explicitly stated about themselves.
DO NOT extract astrological predictions, analysis, or interpretations.

User's Question/Statement: {question}
Assistant's Response: {response}

ALREADY STORED FACTS for this profile (from earlier chats — do NOT output these again, even with different wording):
{existing_for_prompt}

DEDUPLICATION (mandatory):
- Each array item must describe a SINGLE distinct piece of information.
- Do NOT include two facts that mean the same thing (e.g. "Works as engineer" and "Software engineer job" → keep one best phrasing).
- Do NOT output a fact if it is already represented above — same meaning counts as duplicate, not only exact text match.
- If the user only repeats something we already store, return [].
- Prefer one richer sentence over multiple overlapping fragments.

RULES:
1. ONLY extract facts from the USER'S question/statement, NOT from the assistant's astrological analysis
2. Extract concrete personal information like:
   - "I work as a software engineer" → career fact
   - "I got married in 2020" → family/major_events fact
   - "I'm planning to move to Canada" → location/preferences fact
   - "I have two children" → family fact

3. CRITICAL - TEMPORAL CONTEXT:
   - If user mentions time-sensitive events ("I have surgery today", "I'm traveling next week"), include the temporal context
   - Format: "Surgery scheduled (mentioned on [current date])"
   - For ongoing states without dates ("I work as engineer"), no date needed
   - For past events with dates ("married in 2020"), include the year
   - For future plans ("planning to move"), mark as "planned" or "upcoming"

4. DO NOT extract:
   - Astrological predictions ("you will face challenges")
   - Chart interpretations ("partnerships are important for you")
   - Future forecasts ("2026 will be good for career")
   - General advice or analysis

Categories:
- career: Job, profession, work experience, industry
- family: Marital status, children, parents, siblings
- health: Medical conditions, health concerns, surgeries, treatments
- location: Current city, country, places lived
- preferences: Interests, hobbies, goals
- education: Degrees, studies, institutions
- relationships: Dating status, engagement, divorce
- major_events: Significant life events with dates
- temporary_events: Time-sensitive events (surgeries, trips, interviews)

Return ONLY a JSON array of facts:
[
  {{"category": "career", "fact": "Software Engineer with 2 years experience", "confidence": 0.9}},
  {{"category": "temporary_events", "fact": "Surgery scheduled (mentioned on {datetime.now().strftime('%Y-%m-%d')})", "confidence": 1.0}},
  {{"category": "family", "fact": "Married in 2020", "confidence": 1.0}}
]

If no USER-STATED facts found, return empty array: []
"""

        try:
            result = await self.model.generate_content_async(prompt)
            cleaned = result.text.replace("```json", "").replace("```", "").strip()
            facts = json.loads(cleaned)

            if not isinstance(facts, list):
                return

            facts = _dedupe_extracted_batch(facts)
            if not facts:
                return

            inserted = self._store_facts(facts, birth_chart_id, existing_rows)
            if inserted:
                print(f"✅ Stored {inserted} new fact(s) for birth_chart_id={birth_chart_id} (after dedupe)")
            else:
                print(f"ℹ️ No new facts stored for birth_chart_id={birth_chart_id} (all duplicates)")

        except Exception as e:
            print(f"❌ Fact extraction error: {e}")

    def _store_facts(
        self, facts: List[Dict[str, Any]], birth_chart_id: int, existing_rows: List[Tuple[str, str]]
    ) -> int:
        """Insert facts that are not near-duplicates of existing DB rows. Returns count inserted."""
        # Refresh combined list as we insert so batch doesn't duplicate itself
        combined: List[Tuple[str, str]] = list(existing_rows)
        inserted = 0
        with get_conn() as conn:
            for fact_data in facts:
                cat = (fact_data.get("category") or "").strip()
                fact = (fact_data.get("fact") or "").strip()
                if not cat or not fact:
                    continue
                if _is_near_duplicate(cat, fact, combined):
                    continue
                execute(
                    conn,
                    """
                    INSERT INTO user_facts (birth_chart_id, category, fact, confidence)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        birth_chart_id,
                        cat,
                        fact,
                        fact_data.get("confidence", 1.0),
                    ),
                )
                combined.insert(0, (cat, fact))
                inserted += 1
            conn.commit()
        return inserted

    def get_facts(self, birth_chart_id: int) -> Dict[str, List[str]]:
        """Retrieve all facts for a birth chart, filtering out old temporary events"""
        from datetime import datetime, timedelta

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT category, fact, extracted_at
                FROM user_facts
                WHERE birth_chart_id = %s
                ORDER BY extracted_at DESC
                """,
                (birth_chart_id,),
            )
            rows = cur.fetchall()

        facts_by_category = {}
        cutoff_date = datetime.now() - timedelta(days=7)  # Filter temporary events older than 7 days

        for category, fact, extracted_at in rows:
            if category == "temporary_events":
                try:
                    fact_date = (
                        extracted_at
                        if isinstance(extracted_at, datetime)
                        else datetime.fromisoformat(str(extracted_at).replace("Z", "+00:00"))
                    )
                    if fact_date.replace(tzinfo=None) < cutoff_date:
                        continue
                except Exception:
                    pass

            if category not in facts_by_category:
                facts_by_category[category] = []
            facts_by_category[category].append(fact)

        return facts_by_category
