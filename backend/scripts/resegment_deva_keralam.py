#!/usr/bin/env python3
"""Rebuild unreviewed OCR passage candidates without repeating page OCR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from classical_sources.deva_keralam_ingestion import (
    EDITION_KEY,
    FIRST_VERSE_PDF_PAGE,
    SourceCatalogRepository,
    segment_verse_candidates,
)
from db import get_conn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-start", type=int, default=FIRST_VERSE_PDF_PAGE)
    parser.add_argument("--page-end", type=int, default=260)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.page_start < FIRST_VERSE_PDF_PAGE or args.page_end < args.page_start:
        raise SystemExit(f"Page range must start at {FIRST_VERSE_PDF_PAGE} or later")
    load_dotenv(BACKEND_DIR / ".env", override=False)

    with get_conn() as conn:
        cursor = conn.cursor()
        # Old importer revisions could misread publication years and copy
        # counts in the front matter as verse numbers. Purge only generated,
        # still-unreviewed candidates; reviewed/manual records remain intact.
        cursor.execute(
            """
            DELETE FROM classical_passages
             WHERE edition_key = %s
               AND passage_key LIKE 'DK1.OCR.%%'
               AND review_status = 'pending'
               AND executable_status = 'catalogued'
               AND COALESCE((metadata ->> 'generated_from_ocr')::boolean, FALSE)
               AND pdf_page_start < %s
            """,
            (EDITION_KEY, FIRST_VERSE_PDF_PAGE),
        )
        front_matter_deleted = cursor.rowcount
        cursor.execute(
            """
            DELETE FROM classical_passages
             WHERE edition_key = %s
               AND passage_key LIKE 'DK1.OCR.%%'
               AND review_status = 'pending'
               AND executable_status = 'catalogued'
               AND COALESCE((metadata ->> 'generated_from_ocr')::boolean, FALSE)
               AND pdf_page_start BETWEEN %s AND %s
            """,
            (EDITION_KEY, args.page_start, args.page_end),
        )
        deleted = cursor.rowcount
        cursor.execute(
            """
            SELECT pdf_page, raw_ocr
              FROM classical_source_pages
             WHERE edition_key = %s
               AND ocr_status = 'complete'
               AND pdf_page BETWEEN %s AND %s
             ORDER BY pdf_page
            """,
            (EDITION_KEY, args.page_start, args.page_end),
        )
        pages = cursor.fetchall()
        repository = SourceCatalogRepository(conn)
        candidates = 0
        for pdf_page, raw_ocr in pages:
            candidates += repository.save_candidates(
                pdf_page=pdf_page,
                candidates=segment_verse_candidates(raw_ocr or ""),
            )
        conn.commit()

    print(
        json.dumps(
            {
                "pages": len(pages),
                "front_matter_deleted": front_matter_deleted,
                "deleted": deleted,
                "candidates": candidates,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
