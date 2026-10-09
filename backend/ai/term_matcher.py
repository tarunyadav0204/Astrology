import json
import re
from typing import Dict, List, Tuple

from db import get_conn, execute


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
  normalized_language = str(language or "english").strip().lower()
  normalized_language = {
      "en": "english",
      "english": "english",
      "hi": "hindi",
      "hin": "hindi",
      "hindi": "hindi",
      "हिंदी": "hindi",
      "हिन्दी": "hindi",
  }.get(normalized_language, normalized_language)
  try:
    with get_conn() as conn:
      cur = execute(
        conn,
        """
        SELECT term_id, display_text, definition, COALESCE(aliases, '[]') AS aliases_json
        FROM glossary_terms
        WHERE LOWER(language) = %s OR language IS NULL
        """,
        (normalized_language,),
      )
      rows = cur.fetchall() or []
  except Exception:
    # If anything goes wrong (e.g. table not created yet), fall back gracefully
    return []

  terms: List[dict] = []
  for row in rows:
    # Row is a tuple (psycopg2), ordered as selected:
    # term_id, display_text, definition, aliases_json
    term_id = row[0]
    display_text = row[1]
    definition = row[2]
    aliases_json = row[3] if len(row) > 3 else "[]"
    try:
      aliases = json.loads(aliases_json) if isinstance(aliases_json, str) else (aliases_json or [])
      if not isinstance(aliases, list):
        aliases = []
    except Exception:
      aliases = []

    terms.append(
      {
        "term_id": term_id,
        "display_text": display_text,
        "definition": definition,
        "aliases": aliases,
      }
    )
  return terms


def find_terms_in_text(text: str, language: str = "english") -> Tuple[List[str], Dict[str, str]]:
  """
  Scan arbitrary Gemini response text and return:

  - term_ids: list of matched term_id strings
  - glossary: mapping term_id and the longest matched display label/alias -> definition

  Matching is done against display_text and any aliases, case‑insensitive,
  using whole‑word boundaries where possible.
  """
  if not text:
    return [], {}

  glossary_terms = load_glossary_terms(language)
  if not glossary_terms:
    return [], {}

  matches: Dict[str, str] = {}
  matched_labels: Dict[str, List[str]] = {}

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
    normalized_label = label.lower()
    # ``\b`` is unreliable for Indic scripts because combining vowel marks
    # are not consistently treated as word characters. Use exact substring
    # matching for non-ASCII labels; the labels are sorted longest-first, so
    # a longer term such as "नक्षत्र पाद" still wins over "नक्षत्र".
    matches_label = (
      normalized_label in lowered
      if any(ord(char) > 127 for char in normalized_label)
      else bool(re.search(r"\b" + re.escape(normalized_label) + r"\b", lowered))
    )
    if matches_label:
      if term_id not in matches:
        # Look up the full term object to get definition
        term_obj = next((t for t in glossary_terms if t["term_id"] == term_id), None)
        if term_obj and str(term_obj.get("definition") or "").strip():
          matches[term_id] = term_obj["definition"]
          matched_labels[term_id] = []
      if term_id in matches:
        labels = matched_labels.setdefault(term_id, [])
        if label not in labels:
          labels.append(label)

  # Keep stable ids for explicitly tagged content and every spelling actually
  # present in the answer for automatic wrapping. Clients match longest-first
  # in one pass so a shorter term cannot nest inside a longer term's tooltip.
  glossary: Dict[str, str] = dict(matches)
  for term_id, labels in matched_labels.items():
    definition = matches.get(term_id)
    if not definition:
      continue
    for label in labels:
      glossary.setdefault(str(label).strip().lower(), definition)

  return list(matches.keys()), glossary
