#!/usr/bin/env python3
"""Import the private Deva Keralam scan into the reviewed source catalogue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from classical_sources.deva_keralam_ingestion import ImportOptions, import_volume
from db import get_conn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Import source pages and unreviewed OCR verse candidates. "
            "This command never publishes executable prediction rules."
        )
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page-start", type=int, default=1)
    parser.add_argument("--page-end", type=int)
    parser.add_argument("--dpi", type=int, default=80)
    parser.add_argument("--ocr-languages", default="eng+san")
    parser.add_argument("--ocr-columns", type=int, choices=(1, 2), default=2)
    parser.add_argument("--ocr-psm", type=int, default=1)
    parser.add_argument("--metadata-only", action="store_true", help="render/catalogue pages without OCR")
    parser.add_argument("--no-extract-candidates", action="store_true")
    parser.add_argument("--force", action="store_true", help="reprocess pages already current for this PDF hash")
    parser.add_argument(
        "--image-dir",
        type=Path,
        help="retain rendered private page images here; omit to keep only hashes and OCR",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(BACKEND_DIR / ".env", override=False)
    options = ImportOptions(
        page_start=args.page_start,
        page_end=args.page_end,
        dpi=args.dpi,
        ocr=not args.metadata_only,
        ocr_languages=args.ocr_languages,
        ocr_columns=args.ocr_columns,
        ocr_psm=args.ocr_psm,
        extract_candidates=not args.no_extract_candidates,
        force=args.force,
        image_dir=args.image_dir,
    )
    with get_conn() as conn:
        result = import_volume(args.pdf, conn, options)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
