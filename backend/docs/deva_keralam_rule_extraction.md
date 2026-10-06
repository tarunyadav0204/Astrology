# Deva Keralam rule-candidate extraction

This authoring pipeline converts catalogued passages into **draft candidates**.
It cannot publish a classical rule and is not imported by chart, chat or the
runtime rule registry.

## Preview an eligible batch

```bash
cd backend
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py \
  --batch-size 20 \
  --dry-run
```

Dry-run reads the catalogue only. It makes no Gemini request and performs no
database write.

## Extract a batch

```bash
cd backend
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py \
  --batch-size 20
```

The default model is `models/gemini-3.1-flash-lite`. Override it with
`DEVA_KERALAM_EXTRACTION_MODEL` or `--model`. Thinking defaults to `minimal`
and can be changed with `DEVA_KERALAM_EXTRACTION_THINKING_LEVEL`.

Every accepted response must pass the strict Pydantic schema. The stored row
snapshots the passage hash, verse range, OCR/review status, context status,
inherited context, model, prompt version, uncertainties and usage metadata.

Malformed JSON or a Pydantic schema error receives exactly one repair attempt.
The repair request contains the unchanged original source prompt and sanitized
validation errors. It does not normalize comparator names or reuse invalid
output. A second validation failure stops the run at the same resumable cursor.
Token usage from both attempts is combined in the stored usage metadata.

## Run disjoint workers

Use inclusive PDF-page ranges. The range is stored on the run and a resume is
rejected if it supplies different bounds. Page 26 is the first eligible content
page; front matter cannot be assigned to a worker.

```bash
cd backend
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py --page-start 26  --page-end 84  --batch-size 50
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py --page-start 85  --page-end 143 --batch-size 50
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py --page-start 144 --page-end 202 --batch-size 50
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py --page-start 203 --page-end 260 --batch-size 50
```

Workers may run concurrently because their inclusive ranges do not overlap.
The candidate uniqueness constraint remains an additional safeguard.

## Resume after failure or interruption

Each successfully saved passage advances and commits the run cursor. A failed
passage does not advance it.

```bash
cd backend
.venv/bin/python scripts/extract_deva_keralam_rule_candidates.py \
  --resume-run-key DKRE-... \
  --page-start 26 \
  --page-end 84
```

Candidate statuses are limited by the database to `draft`, `in_review` and
`rejected`. The tables have no foreign key or automatic path to
`classical_rule_versions` or a release.
