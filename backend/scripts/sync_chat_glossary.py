"""Upsert the maintained multilingual chat glossary into Postgres.

Run from ``backend/`` after loading the environment that contains POSTGRES_DSN:

    venv/bin/python scripts/sync_chat_glossary.py

The script is idempotent. It never deletes administrator-created terms.
"""

from __future__ import annotations

import json
from pathlib import Path

from db import execute, get_conn


TERMS_PATH = Path(__file__).resolve().parents[1] / "data" / "chat_glossary_terms_v2.json"


def main() -> None:
    terms = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
    if not isinstance(terms, list):
        raise ValueError(f"Expected a JSON list in {TERMS_PATH}")

    with get_conn() as conn:
        for term in terms:
            execute(
                conn,
                """
                INSERT INTO glossary_terms (term_id, display_text, definition, language, aliases)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (term_id) DO UPDATE SET
                    display_text = EXCLUDED.display_text,
                    definition = EXCLUDED.definition,
                    language = EXCLUDED.language,
                    aliases = EXCLUDED.aliases
                """,
                (
                    str(term["term_id"]).strip(),
                    str(term["display_text"]).strip(),
                    str(term["definition"]).strip(),
                    str(term["language"]).strip().lower(),
                    json.dumps(term.get("aliases") or [], ensure_ascii=False),
                ),
            )
        conn.commit()
    print(f"Upserted {len(terms)} chat glossary terms from {TERMS_PATH.name}.")


if __name__ == "__main__":
    main()
