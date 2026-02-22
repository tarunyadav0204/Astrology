#!/usr/bin/env python3
"""
Backfill category and canonical_question for existing user chat messages.
Uses batched Gemini calls: many questions per request to minimize API usage.

Usage (from backend/):
  python backfill_chat_categories.py                    # process all uncategorized
  python backfill_chat_categories.py --dry-run          # no DB writes, no API calls (shows counts only)
  python backfill_chat_categories.py --limit 500        # process at most 500 questions
  python backfill_chat_categories.py --batch-size 50    # 50 questions per Gemini call (default 100)

Expect ~30 API calls for 3000 questions at batch_size=100.
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from typing import List, Tuple

# Load env before importing genai
for env_path in ['.env', os.path.join(os.path.dirname(__file__), '.env')]:
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        break

import google.generativeai as genai

# Reuse same category set as live flow
FAQ_CATEGORIES = frozenset({
    'career', 'marriage', 'health', 'education', 'progeny', 'wealth',
    'trading', 'muhurat', 'karma', 'general', 'other'
})

DB_PATH = os.environ.get('ASTROLOGY_DB_PATH', 'astrology.db')


def get_uncategorized_batch(conn: sqlite3.Connection, batch_size: int, offset: int) -> List[Tuple[int, str]]:
    """Return list of (message_id, content) for user messages with no category, in order."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT message_id, content
        FROM chat_messages
        WHERE sender = 'user'
          AND (category IS NULL OR trim(coalesce(category, '')) = '')
          AND content IS NOT NULL AND trim(content) != ''
        ORDER BY message_id
        LIMIT ? OFFSET ?
    """, (batch_size, offset))
    return cursor.fetchall()


def count_uncategorized(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM chat_messages
        WHERE sender = 'user'
          AND (category IS NULL OR trim(coalesce(category, '')) = '')
          AND content IS NOT NULL AND trim(content) != ''
    """)
    return cursor.fetchone()[0]


def build_batch_prompt(rows: List[Tuple[int, str]]) -> str:
    lines = []
    for mid, content in rows:
        content_clean = (content or "").replace("\n", " ").strip()[:500]
        lines.append(f"[id: {mid}] {content_clean}")
    questions_block = "\n".join(lines)
    return f"""You are categorizing user questions from an astrology app. For each question below, output:
- category: exactly one of: career, marriage, health, education, progeny, wealth, trading, muhurat, karma, general, other (lowercase).
- canonical_question: a short FAQ-style phrase that summarizes the question intent (similar questions should get the same or very similar phrase).

Return ONLY a valid JSON array of objects, one per question, with keys: id, category, canonical_question.
Use the same "id" number as in the input (the number after "id:").
Do not include any other text, markdown, or explanation.

Questions:
{questions_block}

JSON array:"""


def parse_batch_response(text: str) -> List[dict]:
    """Extract JSON array from model response. Tolerates ```json wrapper and minor trailing commas."""
    raw = text.strip()
    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```\s*$", "", raw)
    # Try to find a JSON array
    start = raw.find("[")
    if start == -1:
        return []
    # Find matching closing bracket (simple approach: last ])
    end = raw.rfind("]")
    if end == -1 or end <= start:
        return []
    json_str = raw[start : end + 1]
    # Remove trailing commas before ] or }
    json_str = re.sub(r",\s*]", "]", json_str)
    json_str = re.sub(r",\s*}", "}", json_str)
    try:
        data = json.loads(json_str)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def normalize_entry(entry: dict) -> dict | None:
    """Validate and normalize one batch item. Returns None if invalid."""
    try:
        mid = entry.get("id")
        if mid is None:
            return None
        mid = int(mid)
        category = (entry.get("category") or "").strip().lower()
        if category not in FAQ_CATEGORIES:
            category = "other"
        canonical = (entry.get("canonical_question") or "").strip()[:300] or "Other"
        return {"id": mid, "category": category, "canonical_question": canonical}
    except (TypeError, ValueError):
        return None


def update_batch(conn: sqlite3.Connection, items: List[dict], dry_run: bool) -> None:
    if dry_run or not items:
        return
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    for item in items:
        cursor.execute(
            "UPDATE chat_messages SET category = ?, canonical_question = ?, categorized_at = ? WHERE message_id = ?",
            (item["category"], item["canonical_question"], now, item["id"]),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Backfill chat_messages category/canonical_question via batched Gemini calls")
    parser.add_argument("--dry-run", action="store_true", help="Only count uncategorized; no API calls, no DB writes")
    parser.add_argument("--limit", type=int, default=None, help="Max number of questions to process (default: all)")
    parser.add_argument("--batch-size", type=int, default=100, help="Questions per Gemini call (default 100)")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Path to astrology.db")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"❌ Database not found: {args.db}")
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    total = count_uncategorized(conn)
    print(f"📊 Uncategorized user questions: {total}")

    if args.dry_run:
        print("🔒 Dry run: no API calls or DB updates.")
        conn.close()
        return

    if total == 0:
        print("✅ Nothing to do.")
        conn.close()
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        sys.exit(1)
    genai.configure(api_key=api_key)
    gen_config = genai.GenerationConfig(temperature=0, top_p=0.95, top_k=40)
    model = None
    for name in ["models/gemini-2.5-flash", "models/gemini-2.0-flash"]:
        try:
            model = genai.GenerativeModel(name, generation_config=gen_config)
            print(f"✅ Using model: {name}")
            break
        except Exception:
            continue
    if not model:
        print("❌ No Gemini model available")
        sys.exit(1)

    limit = args.limit or total
    batch_size = min(args.batch_size, 100)  # cap for reliability
    offset = 0
    processed = 0
    batch_num = 0

    while offset < limit:
        batch = get_uncategorized_batch(conn, batch_size, offset)
        if not batch:
            break
        batch_num += 1
        print(f"\n📦 Batch {batch_num}: {len(batch)} questions (message_id {batch[0][0]}–{batch[-1][0]})")
        prompt = build_batch_prompt(batch)
        try:
            response = model.generate_content(prompt, request_options={"timeout": 120})
            text = (response.text or "").strip()
        except Exception as e:
            print(f"   ❌ Gemini error: {e}")
            offset += len(batch)
            continue
        parsed = parse_batch_response(text)
        ids_in_batch = {r[0] for r in batch}
        items = []
        for entry in parsed:
            n = normalize_entry(entry)
            if n and n["id"] in ids_in_batch:
                items.append(n)
        update_batch(conn, items, dry_run=False)
        processed += len(items)
        print(f"   ✅ Updated {len(items)} rows ({len(batch) - len(items)} missing/invalid in response)")
        offset += len(batch)
        if offset >= limit:
            break

    print(f"\n🎉 Done. Categorized {processed} questions in {batch_num} batch(es).")
    conn.close()


if __name__ == "__main__":
    main()
