"""Resumable, source-first ingestion for the scanned Deva Keralam volume.

This module intentionally stops at source pages and unreviewed verse candidates.
OCR text is not an executable rule and cannot affect chart or chat responses.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence
from uuid import uuid4


WORK_KEY = "deva_keralam"
EDITION_KEY = "deva_keralam_volume_1_scan"
FIRST_VERSE_PDF_PAGE = 26


@dataclass(frozen=True)
class PdfMetadata:
    pages: int
    title: str = ""
    author: str = ""


@dataclass(frozen=True)
class VerseCandidate:
    verse_start: int
    verse_end: int
    text: str


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_pdfinfo(output: str) -> PdfMetadata:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip().lower()] = value.strip()
    try:
        pages = int(fields["pages"])
    except (KeyError, ValueError) as exc:
        raise ValueError("pdfinfo output did not contain a valid Pages field") from exc
    if pages <= 0:
        raise ValueError("PDF must contain at least one page")
    return PdfMetadata(pages=pages, title=fields.get("title", ""), author=fields.get("author", ""))


def inspect_pdf(path: Path, *, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> PdfMetadata:
    result = runner(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_pdfinfo(result.stdout)


_VERSE_LINE = re.compile(
    r"(?m)(?:^|\s)(?P<start>\d{1,4})(?:\s*[-–—]\s*(?P<end>\d{1,4}))?"
    r"[.)]\s*(?=[A-Z])"
)


def segment_verse_candidates(raw_ocr: str) -> list[VerseCandidate]:
    """Return conservative OCR candidates without granting rule semantics.

    The scan contains prose notes and page numbers, so candidates remain
    unreviewed.  Context, translation and executable predicates must be added
    by a reviewer or a later extraction workflow. Callers must additionally
    avoid the edition's front matter, where publication years resemble verses.
    """
    normalized = raw_ocr.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(_VERSE_LINE.finditer(normalized))
    preliminary: list[VerseCandidate] = []
    for index, match in enumerate(matches):
        raw_start = match.group("start")
        # Printed verse numbers in this edition are never zero-padded. OCR can
        # turn ornament/noise into values such as ``0888.``; retaining those
        # creates a false passage that may swallow nearby Sanskrit lines.
        if len(raw_start) > 1 and raw_start.startswith("0"):
            continue
        start = int(raw_start)
        raw_end = match.group("end")
        if raw_end and len(raw_end) < len(match.group("start")):
            # Printed ranges commonly abbreviate the repeated prefix:
            # 2497-98 means 2497-2498, not an inverted range.
            prefix = match.group("start")[: len(match.group("start")) - len(raw_end)]
            end = int(prefix + raw_end)
        else:
            end = int(raw_end or start)
        if end < start or end - start > 20:
            continue
        text_end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
        text = normalized[match.start():text_end].strip()
        # Page numbers and isolated OCR noise are much shorter than a verse.
        if len(text) < 24 or not re.search(r"[A-Za-z]", text):
            continue
        preliminary.append(VerseCandidate(start, end, text))

    # On late pages a running header or Sanskrit line is occasionally read as
    # verse 1.  Once the page clearly contains four-digit verse numbering,
    # discard distant low-number noise rather than creating a false passage.
    highest = max((item.verse_start for item in preliminary), default=0)
    if highest >= 100:
        preliminary = [item for item in preliminary if item.verse_start >= highest - 100]
    return preliminary


def build_passage_key(pdf_page: int, verse: VerseCandidate) -> str:
    return f"DK1.OCR.P{pdf_page:04d}.V{verse.verse_start:04d}-{verse.verse_end:04d}"


def render_page(
    pdf_path: Path,
    pdf_page: int,
    output_stem: Path,
    *,
    dpi: int,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> Path:
    runner(
        [
            "pdftoppm",
            "-f",
            str(pdf_page),
            "-l",
            str(pdf_page),
            "-singlefile",
            "-jpeg",
            "-r",
            str(dpi),
            str(pdf_path),
            str(output_stem),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    image_path = output_stem.with_suffix(".jpg")
    if not image_path.is_file():
        raise RuntimeError(f"pdftoppm did not create {image_path}")
    return image_path


def run_tesseract(
    image_path: Path,
    *,
    languages: str,
    columns: int = 2,
    psm: int = 1,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> str:
    if columns not in {1, 2}:
        raise ValueError("columns must be 1 or 2")

    def recognize(path: Path) -> str:
        result = runner(
            ["tesseract", str(path), "stdout", "-l", languages, "--psm", str(psm)],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    if columns == 1:
        return recognize(image_path)

    # The book's main text uses two columns. OCR of the full page interleaves
    # unrelated lines and destroys verse context, so recognize left then right.
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    configured_tmp = os.getenv("ASTROROSHNI_OCR_TMP_DIR", "").strip()
    subprocess_tmp = configured_tmp or ("/private/tmp" if Path("/private/tmp").is_dir() else None)
    with Image.open(image_path) as image, tempfile.TemporaryDirectory(
        prefix="deva-columns-",
        dir=subprocess_tmp,
    ) as directory:
        width, height = image.size
        overlap = max(4, width // 500)
        boxes = (
            (0, 0, width // 2 + overlap, height),
            (width // 2 - overlap, 0, width, height),
        )
        outputs: list[str] = []
        for index, box in enumerate(boxes, start=1):
            # Lossless PNG is intentional. Under sustained parallel imports,
            # Tesseract/Leptonica intermittently observed freshly-written JPEG
            # crops as prematurely terminated even though Pillow had returned.
            column_path = Path(directory) / f"column-{index}.png"
            image.crop(box).save(column_path, format="PNG")
            outputs.append(recognize(column_path).strip())
        return "\n\n".join(output for output in outputs if output) + "\n"


def _cursor(conn, sql: str, params: Sequence[object] = ()):
    cursor = conn.cursor()
    cursor.execute(sql, params)
    return cursor


class SourceCatalogRepository:
    """Small persistence boundary kept separate from runtime rule evaluation."""

    def __init__(self, conn):
        self.conn = conn

    def register_document(self, *, source_hash: str, file_name: str, metadata: PdfMetadata) -> None:
        _cursor(
            self.conn,
            """
            UPDATE classical_editions
               SET content_hash = %s,
                   page_count = %s,
                   source_file_name = %s,
                   import_metadata = import_metadata || %s::jsonb
             WHERE edition_key = %s
            """,
            (
                source_hash,
                metadata.pages,
                file_name,
                json.dumps({"pdf_title": metadata.title, "pdf_author": metadata.author}),
                EDITION_KEY,
            ),
        )

    def start_run(
        self,
        *,
        source_hash: str,
        file_name: str,
        page_start: int,
        page_end: int,
        options: dict,
    ) -> str:
        run_key = f"DK1-{uuid4()}"
        _cursor(
            self.conn,
            """
            INSERT INTO classical_source_import_runs
              (import_run_key, edition_key, source_document_hash, source_file_name,
               status, page_start, page_end, options)
            VALUES (%s, %s, %s, %s, 'running', %s, %s, %s::jsonb)
            """,
            (run_key, EDITION_KEY, source_hash, file_name, page_start, page_end, json.dumps(options)),
        )
        return run_key

    def page_is_current(self, *, pdf_page: int, source_hash: str, require_ocr: bool) -> bool:
        cursor = _cursor(
            self.conn,
            """
            SELECT source_document_hash, ocr_status
              FROM classical_source_pages
             WHERE edition_key = %s AND pdf_page = %s
            """,
            (EDITION_KEY, pdf_page),
        )
        row = cursor.fetchone()
        if not row or row[0] != source_hash:
            return False
        return not require_ocr or row[1] == "complete"

    def save_page(
        self,
        *,
        run_key: str,
        pdf_page: int,
        source_hash: str,
        image_object_key: str,
        image_hash: str,
        raw_ocr: str,
        ocr_engine: str,
        ocr_languages: str,
        ocr_status: str,
        metadata: dict,
    ) -> None:
        _cursor(
            self.conn,
            """
            INSERT INTO classical_source_pages
              (edition_key, pdf_page, image_object_key, image_hash,
               source_document_hash, raw_ocr, ocr_engine, ocr_languages,
               ocr_status, metadata, last_import_run_key, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (edition_key, pdf_page) DO UPDATE SET
              image_object_key = EXCLUDED.image_object_key,
              image_hash = EXCLUDED.image_hash,
              source_document_hash = EXCLUDED.source_document_hash,
              raw_ocr = EXCLUDED.raw_ocr,
              ocr_engine = EXCLUDED.ocr_engine,
              ocr_languages = EXCLUDED.ocr_languages,
              ocr_status = EXCLUDED.ocr_status,
              metadata = classical_source_pages.metadata || EXCLUDED.metadata,
              last_import_run_key = EXCLUDED.last_import_run_key,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                EDITION_KEY,
                pdf_page,
                image_object_key,
                image_hash,
                source_hash,
                raw_ocr,
                ocr_engine,
                ocr_languages,
                ocr_status,
                json.dumps(metadata),
                run_key,
            ),
        )

    def save_candidates(self, *, pdf_page: int, candidates: Iterable[VerseCandidate]) -> int:
        saved = 0
        for candidate in candidates:
            passage_key = build_passage_key(pdf_page, candidate)
            _cursor(
                self.conn,
                """
                INSERT INTO classical_passages
                  (passage_key, edition_key, chapter_number, verse_start, verse_end,
                   title, classification, operational_summary, source_text_status,
                   review_status, metadata, pdf_page_start, pdf_page_end,
                   source_text, textual_confidence, executable_status, content_hash)
                VALUES
                  (%s, %s, 1, %s, %s, %s, 'ocr_candidate', '', 'ocr_unverified',
                   'pending', %s::jsonb, %s, %s, %s, 'unreviewed', 'catalogued', %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    passage_key,
                    EDITION_KEY,
                    candidate.verse_start,
                    candidate.verse_end,
                    f"OCR candidate: verses {candidate.verse_start}–{candidate.verse_end}",
                    json.dumps({"generated_from_ocr": True, "not_executable": True}),
                    pdf_page,
                    pdf_page,
                    candidate.text,
                    sha256_text(candidate.text),
                ),
            )
            # Update only our own still-unreviewed candidate.  A duplicate
            # verse-range row may already exist under a reviewer-assigned key;
            # the INSERT above deliberately leaves that authoritative row alone.
            _cursor(
                self.conn,
                """
                UPDATE classical_passages
                   SET source_text = %s,
                       content_hash = %s,
                       metadata = metadata || %s::jsonb
                 WHERE passage_key = %s
                   AND review_status = 'pending'
                """,
                (
                    candidate.text,
                    sha256_text(candidate.text),
                    json.dumps({"generated_from_ocr": True, "not_executable": True}),
                    passage_key,
                ),
            )
            saved += 1
        return saved

    def record_progress(self, run_key: str, *, failed: bool = False) -> None:
        column = "pages_failed" if failed else "pages_completed"
        _cursor(
            self.conn,
            f"UPDATE classical_source_import_runs SET {column} = {column} + 1 WHERE import_run_key = %s",
            (run_key,),
        )

    def record_page_failure(self, run_key: str, *, pdf_page: int, error: Exception) -> None:
        """Persist bounded diagnostics without storing source/OCR payloads."""
        message = " ".join(str(error).split())[:500]
        _cursor(
            self.conn,
            """
            UPDATE classical_source_import_runs
               SET pages_failed = pages_failed + 1,
                   page_errors = (
                     CASE
                       WHEN jsonb_array_length(page_errors) >= 50 THEN page_errors - 0
                       ELSE page_errors
                     END
                   ) || jsonb_build_array(jsonb_build_object(
                     'pdf_page', %s,
                     'error_type', %s,
                     'message', %s,
                     'recorded_at', CURRENT_TIMESTAMP
                   ))
             WHERE import_run_key = %s
            """,
            (pdf_page, type(error).__name__, message, run_key),
        )

    def finish_run(self, run_key: str, *, status: str, error_message: str = "") -> None:
        _cursor(
            self.conn,
            """
            UPDATE classical_source_import_runs
               SET status = %s, error_message = %s, completed_at = CURRENT_TIMESTAMP
             WHERE import_run_key = %s
            """,
            (status, error_message[:4000], run_key),
        )


@dataclass(frozen=True)
class ImportOptions:
    page_start: int = 1
    page_end: int | None = None
    dpi: int = 80
    ocr: bool = True
    ocr_languages: str = "eng+san"
    ocr_columns: int = 2
    ocr_psm: int = 1
    extract_candidates: bool = True
    force: bool = False
    image_dir: Path | None = None


def import_volume(pdf_path: Path, conn, options: ImportOptions) -> dict[str, int | str]:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    metadata = inspect_pdf(pdf_path)
    page_end = options.page_end or metadata.pages
    if options.page_start < 1 or page_end > metadata.pages or page_end < options.page_start:
        raise ValueError(f"Page range must be within 1..{metadata.pages}")
    if options.ocr and shutil.which("tesseract") is None:
        raise RuntimeError("tesseract is required for OCR; install it or pass --metadata-only")

    source_hash = sha256_file(pdf_path)
    repository = SourceCatalogRepository(conn)
    repository.register_document(source_hash=source_hash, file_name=pdf_path.name, metadata=metadata)
    run_key = repository.start_run(
        source_hash=source_hash,
        file_name=pdf_path.name,
        page_start=options.page_start,
        page_end=page_end,
        options={
            "dpi": options.dpi,
            "ocr": options.ocr,
            "ocr_languages": options.ocr_languages,
            "ocr_columns": options.ocr_columns,
            "ocr_psm": options.ocr_psm,
            "extract_candidates": options.extract_candidates,
            "force": options.force,
        },
    )
    conn.commit()

    completed = skipped = failed = candidates_saved = 0
    try:
        for pdf_page in range(options.page_start, page_end + 1):
            if not options.force and repository.page_is_current(
                pdf_page=pdf_page,
                source_hash=source_hash,
                require_ocr=options.ocr,
            ):
                skipped += 1
                continue
            try:
                with tempfile.TemporaryDirectory(prefix="deva-keralam-") as directory:
                    image_path = render_page(
                        pdf_path,
                        pdf_page,
                        Path(directory) / f"page-{pdf_page:04d}",
                        dpi=options.dpi,
                    )
                    image_hash = sha256_file(image_path)
                    image_object_key = ""
                    if options.image_dir:
                        options.image_dir.mkdir(parents=True, exist_ok=True)
                        retained = options.image_dir / f"page-{pdf_page:04d}-{image_hash[:12]}.jpg"
                        shutil.copyfile(image_path, retained)
                        image_object_key = str(retained)
                    raw_ocr = ""
                    if options.ocr:
                        raw_ocr = run_tesseract(
                            image_path,
                            languages=options.ocr_languages,
                            columns=options.ocr_columns,
                            psm=options.ocr_psm,
                        )
                    ocr_status = "complete" if options.ocr else "not_requested"
                    repository.save_page(
                        run_key=run_key,
                        pdf_page=pdf_page,
                        source_hash=source_hash,
                        image_object_key=image_object_key,
                        image_hash=image_hash,
                        raw_ocr=raw_ocr,
                        ocr_engine="tesseract" if options.ocr else "",
                        ocr_languages=options.ocr_languages if options.ocr else "",
                        ocr_status=ocr_status,
                        metadata={
                            "render_dpi": options.dpi,
                            "ocr_columns": options.ocr_columns,
                            "ocr_psm": options.ocr_psm,
                        },
                    )
                    if (
                        options.ocr
                        and options.extract_candidates
                        and pdf_page >= FIRST_VERSE_PDF_PAGE
                    ):
                        candidates_saved += repository.save_candidates(
                            pdf_page=pdf_page,
                            candidates=segment_verse_candidates(raw_ocr),
                        )
                    repository.record_progress(run_key)
                    conn.commit()
                    completed += 1
            except Exception as exc:
                conn.rollback()
                repository.record_page_failure(run_key, pdf_page=pdf_page, error=exc)
                conn.commit()
                failed += 1
        status = "completed" if failed == 0 else "failed"
        repository.finish_run(run_key, status=status, error_message=f"{failed} page(s) failed" if failed else "")
        conn.commit()
    except BaseException as exc:
        conn.rollback()
        repository.finish_run(run_key, status="failed", error_message=str(exc))
        conn.commit()
        raise

    return {
        "run_key": run_key,
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "candidates_saved": candidates_saved,
    }
