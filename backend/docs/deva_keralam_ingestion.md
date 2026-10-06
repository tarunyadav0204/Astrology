# Deva Keralam source ingestion

The source importer catalogues a private scanned edition before any passage is
allowed to participate in prediction. OCR output and automatically segmented
verse candidates are always stored as unreviewed, non-executable evidence.

## Prerequisites

1. Apply runtime migrations, including `add_deva_keralam_source_catalog.sql`.
2. Install Poppler (`pdfinfo` and `pdftoppm`).
3. Install Tesseract with English and Sanskrit language data. This edition's
   verified default is `eng+san` with page-segmentation mode 1. The importer
   crops and reads the left and right columns separately to preserve reading
   order. Set `ASTROROSHNI_OCR_TMP_DIR` when OCR subprocesses need a specific
   readable temporary directory; macOS defaults to `/private/tmp`.
   The edition default is 80 DPI: the source scan is unusually large, and
   higher renders consume substantially more memory without improving the
   English translation OCR in representative tests.
4. Configure the normal backend PostgreSQL DSN.

## Resumable import

```bash
cd backend
.venv/bin/python scripts/import_deva_keralam.py \
  /Users/tarunydv/Downloads/Deva-Keralam-1-Chandrakala-Nadi.pdf \
  --image-dir private_classical_sources/deva_keralam_volume_1/pages
```

Use `--page-start` and `--page-end` to process a review batch. Re-running the
same PDF skips pages already imported with the same document hash and completed
OCR. `--force` deliberately reprocesses them. `--metadata-only` renders and
catalogues page evidence without requiring Tesseract.

The importer commits after each page. A stopped or failed run can therefore be
resumed without losing completed work.

If segmentation improves after OCR has already completed, rebuild only the
unreviewed OCR candidates without re-rendering the book:

```bash
.venv/bin/python scripts/resegment_deva_keralam.py
```

The command never deletes reviewed or executable passages.

## Review and prediction gate

- `classical_source_pages` contains page evidence and OCR state.
- `classical_context_blocks` holds reviewer-confirmed inherited context.
- `classical_passages` contains source, translation and editorial status.
- `classical_passage_anchors` supports source review/search.
- `classical_rule_versions` remains the executable rule boundary.
- `classical_rule_anchors` narrows runtime candidates after publication.
- `classical_rule_tests` stores matching and non-matching fixtures.

An OCR candidate must not be promoted merely because its text looks complete.
The page scan, verse range, inherited context, degree precision and editorial
notes must be reviewed first. The `classical_source_coverage` view reports page,
OCR, review, passage and executable-rule coverage for each edition.
