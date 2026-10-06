from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from classical_sources.deva_keralam_ingestion import (
    EDITION_KEY,
    ImportOptions,
    SourceCatalogRepository,
    VerseCandidate,
    build_passage_key,
    parse_pdfinfo,
    run_tesseract,
    segment_verse_candidates,
    sha256_file,
)
from migrations.apply_runtime_migrations import RUNTIME_MIGRATIONS


MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
RESEGMENT_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "resegment_deva_keralam.py"


class RecordingCursor:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row


class RecordingConnection:
    def __init__(self, row=None):
        self.cursors = []
        self.row = row

    def cursor(self):
        cursor = RecordingCursor(self.row)
        self.cursors.append(cursor)
        return cursor


def test_pdfinfo_parser_keeps_page_count_and_optional_metadata():
    metadata = parse_pdfinfo("Title: Deva Keralam\nAuthor: Editor\nPages: 260\n")

    assert metadata.pages == 260
    assert metadata.title == "Deva Keralam"
    assert metadata.author == "Editor"


def test_edition_ocr_defaults_are_memory_safe_and_preserve_columns():
    options = ImportOptions()

    assert options.dpi == 80
    assert options.ocr_languages == "eng+san"
    assert options.ocr_columns == 2
    assert options.ocr_psm == 1


@pytest.mark.parametrize("output", ["Pages: unknown", "Title: scan", "Pages: 0"])
def test_pdfinfo_parser_rejects_unusable_page_counts(output):
    with pytest.raises(ValueError):
        parse_pdfinfo(output)


def test_file_hash_is_streamed_and_stable(tmp_path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"scan-page-data")

    assert sha256_file(source) == hashlib.sha256(b"scan-page-data").hexdigest()


def test_tesseract_uses_source_verified_language_and_page_segmentation_options(tmp_path):
    image = tmp_path / "page.jpg"
    image.write_bytes(b"not-read-by-fake-runner")
    calls = []

    def fake_runner(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="130. About Mother: source text")

    output = run_tesseract(
        image,
        languages="eng+san",
        columns=1,
        psm=1,
        runner=fake_runner,
    )

    assert output.startswith("130.")
    assert calls[0][0] == [
        "tesseract",
        str(image),
        "stdout",
        "-l",
        "eng+san",
        "--psm",
        "1",
    ]


def test_two_column_ocr_uses_subprocess_readable_temp_root(tmp_path, monkeypatch):
    from PIL import Image

    image = tmp_path / "page.jpg"
    Image.new("RGB", (100, 120), "white").save(image)
    subprocess_tmp = tmp_path / "ocr-subprocess-tmp"
    subprocess_tmp.mkdir()
    monkeypatch.setenv("ASTROROSHNI_OCR_TMP_DIR", str(subprocess_tmp))
    calls = []

    def fake_runner(command, **kwargs):
        calls.append(command)
        assert Path(command[1]).is_relative_to(subprocess_tmp)
        assert Path(command[1]).is_file()
        assert Path(command[1]).suffix == ".png"
        assert Path(command[1]).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        return SimpleNamespace(stdout=f"column {len(calls)}")

    output = run_tesseract(
        image,
        languages="eng+san",
        columns=2,
        psm=1,
        runner=fake_runner,
    )

    assert output == "column 1\n\ncolumn 2\n"
    assert len(calls) == 2


def test_ocr_segmentation_is_conservative_and_preserves_ranges():
    raw = """
    130. About Mother. If birth is in the former half of Agada Nadiamsa,
    the Moon occupying Kutila Nadiamsa gives the stated result.

    131-132. The fourth lord and its aspect further qualify the result.

    15
    """

    candidates = segment_verse_candidates(raw)

    assert [(item.verse_start, item.verse_end) for item in candidates] == [(130, 130), (131, 132)]
    assert "former half" in candidates[0].text
    assert build_passage_key(40, candidates[0]) == "DK1.OCR.P0040.V0130-0130"


def test_ocr_segmentation_expands_abbreviated_large_verse_ranges_and_drops_header_noise():
    raw = """
    1 Running heading accidentally read as a long candidate with unrelated material.
    2497-98. Physical Description: The native has the following stated results.
    2499-2500. Coborn: The text gives results for brothers and sisters here.
    """

    candidates = segment_verse_candidates(raw)

    assert [(item.verse_start, item.verse_end) for item in candidates] == [
        (2497, 2498),
        (2499, 2500),
    ]


def test_ocr_segmentation_does_not_treat_years_or_unpunctuated_numbers_as_verses():
    raw = """
    Published 1972 by the editorial office.
    1800 Copies printed in the first edition.
    130. A genuine verse heading has an explicit stop and readable prose.
    """

    candidates = segment_verse_candidates(raw)

    assert [(item.verse_start, item.verse_end) for item in candidates] == [(130, 130)]


def test_ocr_segmentation_rejects_zero_padded_noise_as_a_verse_number():
    raw = """
    0888. Notes created from an OCR ornament must not become verse 888.
    250. A genuine translated verse heading remains eligible for review.
    """

    candidates = segment_verse_candidates(raw)

    assert [(item.verse_start, item.verse_end) for item in candidates] == [(250, 250)]


def test_ocr_candidates_are_catalogued_as_non_executable_and_unreviewed():
    conn = RecordingConnection()
    repository = SourceCatalogRepository(conn)

    saved = repository.save_candidates(
        pdf_page=40,
        candidates=[VerseCandidate(130, 131, "130-131 About Mother. A sufficiently long OCR candidate.")],
    )

    assert saved == 1
    sql, params = conn.cursors[0].calls[0]
    assert "'ocr_unverified'" in sql
    assert "'pending'" in sql
    assert "'catalogued'" in sql
    assert '"not_executable": true' in params[5]
    assert params[0] == "DK1.OCR.P0040.V0130-0131"
    assert params[1] == EDITION_KEY


def test_source_catalog_migration_is_runtime_applied_and_prediction_gated():
    filename = "add_deva_keralam_source_catalog.sql"
    assert filename in RUNTIME_MIGRATIONS
    assert RUNTIME_MIGRATIONS.index(filename) > RUNTIME_MIGRATIONS.index("create_classical_rule_engine.sql")

    sql = (MIGRATIONS / filename).read_text(encoding="utf-8")
    for table in (
        "classical_source_import_runs",
        "classical_source_pages",
        "classical_context_blocks",
        "classical_passage_anchors",
        "classical_rule_anchors",
        "classical_rule_tests",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "CREATE OR REPLACE VIEW classical_source_coverage" in sql
    assert '"prediction_gate":"reviewed_rules_only"' in sql
    assert "internal_reference_only" in sql


def test_reviewed_passage_text_is_not_overwritten_by_a_later_ocr_resume():
    conn = RecordingConnection()
    repository = SourceCatalogRepository(conn)
    repository.save_candidates(
        pdf_page=40,
        candidates=[VerseCandidate(130, 130, "130 A sufficiently long replacement OCR candidate.")],
    )

    insert_sql = conn.cursors[0].calls[0][0]
    update_sql = conn.cursors[1].calls[0][0]
    assert "ON CONFLICT DO NOTHING" in insert_sql
    assert "AND review_status = 'pending'" in update_sql


def test_page_failure_diagnostics_are_bounded_and_do_not_include_source_payloads():
    conn = RecordingConnection()
    repository = SourceCatalogRepository(conn)
    repository.record_page_failure(
        "run-1",
        pdf_page=240,
        error=RuntimeError("worker failed\n" + ("x" * 800)),
    )

    sql, params = conn.cursors[0].calls[0]
    assert "pages_failed = pages_failed + 1" in sql
    assert "jsonb_array_length(page_errors) >= 50" in sql
    assert params[0] == 240
    assert params[1] == "RuntimeError"
    assert len(params[2]) == 500
    assert "raw_ocr" not in sql


def test_resegment_script_deletes_only_unreviewed_generated_candidates():
    source = RESEGMENT_SCRIPT.read_text(encoding="utf-8")

    assert "passage_key LIKE 'DK1.OCR.%%'" in source
    assert "review_status = 'pending'" in source
    assert "executable_status = 'catalogued'" in source
    assert "generated_from_ocr" in source
    assert "pdf_page_start < %s" in source
    assert '"front_matter_deleted"' in source
    assert "DELETE FROM classical_passages" in source
    assert "DELETE FROM classical_source_pages" not in source
