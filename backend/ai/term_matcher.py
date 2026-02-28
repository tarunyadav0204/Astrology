import sqlite3
import json
import re
from typing import Dict, List, Tuple


def _get_db_connection() -> sqlite3.Connection:
  """
  Lightweight helper to get a read-only style connection for glossary usage.
  """
  conn = sqlite3.connect("astrology.db")
  conn.row_factory = sqlite3.Row
  return conn


def load_glossary_terms(language: str = "english") -> List[dict]:
  """
  Load all glossary terms for the given language (or language‑agnostic terms).

  Returns a list of dicts:
  {
    "term_id": str,
    "display_text": str,
    "definition": str,
    "aliases": [str, ...],
  }
  """
  try:
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
      """
      SELECT term_id, display_text, definition, COALESCE(aliases, '[]') AS aliases_json
      FROM glossary_terms
      WHERE language = ? OR language IS NULL
      """,
      (language,),
    )
    rows = cursor.fetchall()
    conn.close()
  except Exception:
    # If anything goes wrong (e.g. table not created yet), fall back gracefully
    return []

  terms: List[dict] = []
  for row in rows:
    try:
      aliases = json.loads(row["aliases_json"]) if row["aliases_json"] else []
      if not isinstance(aliases, list):
        aliases = []
    except Exception:
      aliases = []

    terms.append(
      {
        "term_id": row["term_id"],
        "display_text": row["display_text"],
        "definition": row["definition"],
        "aliases": aliases,
      }
    )
  return terms


def find_terms_in_text(text: str, language: str = "english") -> Tuple[List[str], Dict[str, str]]:
  """
  Scan arbitrary Gemini response text and return:

  - term_ids: list of matched term_id strings
  - glossary: mapping term_id -> definition

  Matching is done against display_text and any aliases, case‑insensitive,
  using whole‑word boundaries where possible.
  """
  if not text:
    return [], {}

  glossary_terms = load_glossary_terms(language)
  if not glossary_terms:
    return [], {}

  matches: Dict[str, str] = {}

  # Build list of (term_id, label_to_match) pairs
  label_items: List[Tuple[str, str]] = []
  for term in glossary_terms:
    all_labels = [term.get("display_text", "")] + term.get("aliases", [])
    for label in all_labels:
      label = (label or "").strip()
      if label:
        label_items.append((term["term_id"], label))

  # Sort by label length descending to avoid shorter labels eating longer ones
  label_items.sort(key=lambda item: len(item[1]), reverse=True)

  lowered = text.lower()

  for term_id, label in label_items:
    pattern = r"\b" + re.escape(label.lower()) + r"\b"
    if re.search(pattern, lowered):
      if term_id not in matches:
        # Look up the full term object to get definition
        term_obj = next((t for t in glossary_terms if t["term_id"] == term_id), None)
        if term_obj and term_obj.get("definition"):
          matches[term_id] = term_obj["definition"]

  return list(matches.keys()), matches

