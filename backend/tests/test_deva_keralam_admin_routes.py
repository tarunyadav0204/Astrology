from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from sutra_rules import admin_routes


class _Cursor:
    def __init__(self, columns, rows):
        self.description = [(column,) for column in columns]
        self._rows = list(rows)

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


@contextmanager
def _connection():
    yield object()


def test_deva_admin_reads_require_admin_role():
    class User:
        role = "user"

    with pytest.raises(HTTPException) as exc:
        admin_routes.require_admin(User())
    assert exc.value.status_code == 403


def test_coverage_returns_progress_and_status_totals_without_source_text(monkeypatch):
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)

    def fake_execute(_conn, sql, _params=()):
        if "FROM classical_source_coverage" in sql:
            return _Cursor(
                ["edition_key", "expected_pages", "catalogued_pages", "ocr_complete_pages",
                 "verified_pages", "catalogued_passages", "executable_passages", "source_linked_rules"],
                [(admin_routes.DEVA_KERALAM_EDITION_KEY, 260, 40, 38, 4, 120, 2, 1)],
            )
        if "FROM classical_source_import_runs" in sql:
            return _Cursor(
                ["import_run_key", "status", "page_start", "page_end", "pages_completed",
                 "pages_failed", "started_at", "completed_at", "error_message"],
                [("DK1-run", "running", 1, 260, 39, 1, now, None, "")],
            )
        if "GROUP BY ocr_status" in sql:
            return _Cursor(["ocr_status", "count"], [("complete", 38), ("failed", 2)])
        if "classical_source_pages" in sql and "GROUP BY review_status" in sql:
            return _Cursor(["review_status", "count"], [("unreviewed", 36), ("verified", 4)])
        if "classical_context_blocks" in sql:
            return _Cursor(["context_status", "count"], [("candidate", 5)])
        if "GROUP BY review_status" in sql:
            return _Cursor(["review_status", "count"], [("pending", 118), ("verified", 2)])
        if "GROUP BY executable_status" in sql:
            return _Cursor(["executable_status", "count"], [("catalogued", 118), ("executable", 2)])
        raise AssertionError(sql)

    monkeypatch.setattr(admin_routes, "get_conn", _connection)
    monkeypatch.setattr(admin_routes, "execute", fake_execute)
    result = admin_routes.get_deva_keralam_coverage(_=object())

    assert result["coverage"]["catalogued_pages"] == 40
    assert result["latest_import_run"]["processed_pages"] == 40
    assert result["latest_import_run"]["progress_percent"] == pytest.approx(15.38)
    assert result["status_totals"]["passage_execution"]["executable"] == 2
    assert result["source_text_included"] is False


def test_page_listing_exposes_review_metadata_but_not_ocr_or_storage_key(monkeypatch):
    now = datetime(2026, 10, 4, tzinfo=timezone.utc)

    def fake_execute(_conn, sql, params=()):
        if "SELECT COUNT(*)" in sql:
            assert params == (admin_routes.DEVA_KERALAM_EDITION_KEY, "complete", "verified")
            return _Cursor(["count"], [(1,)])
        assert "raw_ocr <> ''" in sql
        return _Cursor(
            ["source_page_id", "pdf_page", "printed_page_label", "chapter_label", "ocr_engine",
             "ocr_languages", "ocr_confidence", "ocr_status", "review_status",
             "last_import_run_key", "updated_at", "has_raw_ocr", "has_corrected_text", "has_page_image"],
            [(7, 40, "15", "", "tesseract", "eng+san", None, "complete", "verified",
              "DK1-run", now, True, False, True)],
        )

    monkeypatch.setattr(admin_routes, "get_conn", _connection)
    monkeypatch.setattr(admin_routes, "execute", fake_execute)
    result = admin_routes.list_deva_keralam_pages(
        limit=25, offset=0, ocr_status="complete", review_status="verified", _=object()
    )
    page = result["pages"][0]
    assert page["has_raw_ocr"] is True
    assert "raw_ocr" not in page
    assert "corrected_text" not in page
    assert "image_object_key" not in page
    assert result["pagination"] == {"total": 1, "limit": 25, "offset": 0}


def test_executable_rule_listing_groups_source_status_without_expression(monkeypatch):
    def fake_execute(_conn, sql, _params=()):
        if "COUNT(DISTINCT" in sql:
            return _Cursor(["count"], [(1,)])
        return _Cursor(
            ["rule_key", "version", "title", "rule_type", "scope", "status",
             "calculator_binding", "topics", "created_at", "relationship", "passage_key",
             "verse_start", "verse_end", "pdf_page_start", "pdf_page_end",
             "source_review_status", "source_textual_confidence", "source_executable_status"],
            [("DK.1.2497", 1, "Physical description", "contextual_exact_match", "natal", "published",
              "calculator", ["appearance"], None, "authority", "DK1.2497-2498", 2497, 2498,
              240, 240, "verified", "reviewed_clear", "executable")],
        )

    monkeypatch.setattr(admin_routes, "get_conn", _connection)
    monkeypatch.setattr(admin_routes, "execute", fake_execute)
    result = admin_routes.list_deva_keralam_executable_rules(
        limit=50, offset=0, status="published", _=object()
    )
    rule = result["rules"][0]
    assert rule["status"] == "published"
    assert rule["sources"][0]["pdf_page_start"] == 240
    assert rule["sources"][0]["review_status"] == "verified"
    assert "expression" not in rule
    assert result["source_text_included"] is False


def test_passage_listing_shows_candidate_readiness_without_source_text(monkeypatch):
    def fake_execute(_conn, sql, params=()):
        if "SELECT COUNT(*)" in sql:
            assert params == (admin_routes.DEVA_KERALAM_EDITION_KEY, "pending", "catalogued")
            return _Cursor(["count"], [(1,)])
        return _Cursor(
            ["passage_key", "context_block_key", "chapter_number", "verse_start", "verse_end",
             "title", "classification", "source_text_status", "review_status",
             "textual_confidence", "executable_status", "pdf_page_start", "pdf_page_end",
             "printed_page_start", "printed_page_end", "has_source_text", "has_translation",
             "has_editor_notes", "anchor_count", "linked_rule_count"],
            [("DK1.OCR.P0040.V0130-0131", None, 1, 130, 131, "OCR candidate",
              "ocr_candidate", "ocr_unverified", "pending", "unreviewed", "catalogued",
              40, 40, "15", "15", True, False, False, 0, 0)],
        )

    monkeypatch.setattr(admin_routes, "get_conn", _connection)
    monkeypatch.setattr(admin_routes, "execute", fake_execute)
    result = admin_routes.list_deva_keralam_passages(
        limit=10, offset=0, review_status="pending", executable_status="catalogued", _=object()
    )
    passage = result["passages"][0]
    assert passage["verse_start"] == 130
    assert passage["has_source_text"] is True
    assert passage["linked_rule_count"] == 0
    assert "source_text" not in passage
    assert "translation_text" not in passage
    assert result["source_text_included"] is False
