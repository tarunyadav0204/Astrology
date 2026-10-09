"""Sync maintained chat definitions and aliases without deleting admin terms.

From backend/, with the database environment loaded:
    venv/bin/python scripts/sync_chat_glossary.py --preserve-existing

--preserve-existing retains populated admin definitions and merges aliases.
Only explicitly flagged spelling corrections replace an existing display label.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from db import execute, get_conn

DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
TERMS_PATH = DATA_DIR / 'chat_glossary_terms_v2.json'


def load_terms(paths):
    merged = {}
    for path in paths:
        rows = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(rows, list):
            raise ValueError(f'Expected a JSON list in {path}')
        for term in rows:
            for field in ('term_id', 'display_text', 'definition', 'language'):
                if not str(term.get(field) or '').strip():
                    raise ValueError(f'Missing {field} in {path}')
            tid = term['term_id'].strip()
            prior = merged.get(tid, {})
            aliases = list(dict.fromkeys([*prior.get('aliases', []), *term.get('aliases', [])]))
            merged[tid] = {**prior, **term, 'aliases': aliases}
    return list(merged.values())


def sync_terms(conn, terms, *, preserve_existing=False):
    for term in terms:
        existing = execute(conn, 'SELECT display_text, definition, language, aliases FROM glossary_terms WHERE term_id = %s FOR UPDATE', (term['term_id'],)).fetchone()
        aliases = term.get('aliases') or []
        display = term['display_text'].strip()
        definition = term['definition'].strip()
        language = term['language'].strip().lower()
        if existing and preserve_existing:
            old_aliases = existing[3] or []
            if isinstance(old_aliases, str):
                old_aliases = json.loads(old_aliases)
            if not isinstance(old_aliases, list):
                old_aliases = []
            aliases = list(dict.fromkeys([*old_aliases, existing[0], *aliases]))
            aliases = [a for a in aliases if isinstance(a, str) and a.strip()]
            if not term.get('correct_display_text'):
                display = existing[0] or display
            definition = existing[1] if str(existing[1] or '').strip() else definition
            language = existing[2] or language
        execute(conn, '''
            INSERT INTO glossary_terms (term_id, display_text, definition, language, aliases)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (term_id) DO UPDATE SET
                display_text = EXCLUDED.display_text,
                definition = EXCLUDED.definition,
                language = EXCLUDED.language,
                aliases = EXCLUDED.aliases
        ''', (term['term_id'].strip(), display, definition, language, json.dumps(aliases, ensure_ascii=False)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--terms-file', type=Path, action='append')
    parser.add_argument('--preserve-existing', action='store_true')
    args = parser.parse_args()
    paths = args.terms_file or [TERMS_PATH, DATA_DIR / 'chat_glossary_terms_v3.json']
    terms = load_terms(paths)
    with get_conn() as conn:
        sync_terms(conn, terms, preserve_existing=args.preserve_existing)
        conn.commit()
    print(f'Synced {len(terms)} glossary entries; no terms deleted.')


if __name__ == '__main__':
    main()
