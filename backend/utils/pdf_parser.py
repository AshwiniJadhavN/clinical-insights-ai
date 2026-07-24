"""
PDF and plain-text document parser.

Extracts clean text from uploaded clinical documents using pypdf.
Produces a ParsedDocument dataclass consumed by the chunker (rag/chunker.py).

Python patterns applied:
  - EAFP: attempt extraction and handle specific exceptions
  - Custom exception hierarchy: DocumentParseError for all parse failures
  - Dataclass with computed field: ParsedDocument.char_count set in __post_init__
  - Named constant: MIN_USEFUL_CHARS avoids magic numbers in logic

HIPAA note: extracted text may contain PHI. This module:
  - NEVER logs text content at any level
  - Logs only page numbers in warnings
  - Raises DocumentParseError with generic messages (no PHI in exceptions)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pypdf

logger = logging.getLogger(__name__)

# Documents with fewer extracted characters than this are likely image-based PDFs
# and should surface a warning.
MIN_USEFUL_CHARS: int = 50


class DocumentParseError(Exception):
    """
    Raised when a document cannot be parsed into usable text.

    All messages must be generic (no PHI). Internal details are logged
    separately via phi_filter.safe_error_response().
    """


@dataclass
class ParsedDocument:
    """
    Structured result of parsing a clinical document.

    Attributes:
        text:       Full extracted text (may be empty for image-only PDFs)
        page_count: Pages in the source document
        file_type:  "pdf" or "txt"
        char_count: Computed from text in __post_init__
        warnings:   Non-fatal issues that did not prevent extraction
    """

    text: str
    page_count: int
    file_type: str
    char_count: int = field(init=False)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)

    @property
    def is_empty(self) -> bool:
        """True when less text was extracted than the useful minimum."""
        return self.char_count < MIN_USEFUL_CHARS


def parse_document(file_path: Path) -> ParsedDocument:
    """
    Extract text from a PDF or plain-text file.

    Dispatches to the appropriate private parser based on file extension.

    Raises:
        DocumentParseError: if the file type is unsupported or unreadable.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _parse_pdf(file_path)
    if suffix == ".txt":
        return _parse_txt(file_path)

    raise DocumentParseError(
        f"Unsupported file type '{suffix}'. Supported: .pdf, .txt"
    )


def _parse_pdf(path: Path) -> ParsedDocument:
    """
    Extract text from a PDF using pypdf.

    EAFP: attempt each page; catch page-level failures and record as warnings
    rather than aborting the whole document. A partial extraction is more
    useful than no extraction.
    """
    warnings: list[str] = []

    try:
        reader = pypdf.PdfReader(str(path))
    except Exception as exc:
        raise DocumentParseError(
            "Could not open PDF. The file may be corrupted or password-protected."
        ) from exc

    page_count = len(reader.pages)
    page_texts: list[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        try:
            extracted = page.extract_text() or ""
            page_texts.append(extracted.strip())
        except Exception:
            warnings.append(f"Page {page_num}: text extraction failed and was skipped.")
            logger.warning("PDF page %d extraction failed — skipped.", page_num)

    full_text = "\n\n".join(t for t in page_texts if t)

    if len(full_text) < MIN_USEFUL_CHARS:
        warnings.append(
            "Very little text was extracted. This PDF may be image-based and "
            "require OCR processing (not yet supported in this version)."
        )

    return ParsedDocument(
        text=full_text,
        page_count=page_count,
        file_type="pdf",
        warnings=warnings,
    )


def _parse_txt(path: Path) -> ParsedDocument:
    """
    Read a plain-text file, trying common encodings in order.

    EAFP: try utf-8 first (most common), fall back to utf-8-sig
    (BOM-prefixed files from Windows), then latin-1 (legacy clinical exports).
    """
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
            return ParsedDocument(
                text=text.strip(),
                page_count=1,
                file_type="txt",
            )
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise DocumentParseError(
                "Could not read the file. It may have been deleted or is inaccessible."
            ) from exc

    raise DocumentParseError(
        "Could not decode the file with any supported encoding (UTF-8, UTF-8-BOM, Latin-1)."
    )
