"""
Shared data models for the WCAG-compliant document-to-HTML converter.

Re-exports existing extraction types from pdf_extractor and adds domain models
for document tracking, conversion results, and WCAG validation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Re-export existing extraction dataclasses so consumers can import from one place
from pdf_extractor import TextSpan, ImageInfo, TableData, PageResult  # noqa: F401


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocumentFormat(str, Enum):
    """Supported input document formats."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"


class DocumentStatus(str, Enum):
    """Document processing lifecycle states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    # Valid state transitions
    _transitions: dict[str, list[str]] = {  # type: ignore[assignment]
        "pending": ["processing"],
        "processing": ["completed", "failed"],
        "completed": [],
        "failed": ["pending"],  # allow retry
    }

    def can_transition_to(self, target: DocumentStatus) -> bool:
        transitions = {
            "pending": ["processing"],
            "processing": ["completed", "failed"],
            "completed": [],
            "failed": ["pending"],
        }
        return target.value in transitions.get(self.value, [])


class Severity(str, Enum):
    """WCAG violation severity levels."""
    CRITICAL = "critical"
    SERIOUS = "serious"
    MODERATE = "moderate"
    MINOR = "minor"


class SourceType(str, Enum):
    """How page content was originally encoded."""
    DIGITAL = "digital"
    SCANNED = "scanned"
    MIXED = "mixed"


class ExtractionMethod(str, Enum):
    """Method used to extract page content."""
    DIRECT = "direct"
    OCR = "ocr"
    HYBRID = "hybrid"


# ---------------------------------------------------------------------------
# Content-type / extension mappings
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: dict[str, DocumentFormat] = {
    ".pdf": DocumentFormat.PDF,
    ".docx": DocumentFormat.DOCX,
    ".pptx": DocumentFormat.PPTX,
}

EXTENSION_CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

MAX_FILE_SIZE_BYTES: int = 104_857_600  # 100 MB


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """Represents an uploaded document tracked through the conversion pipeline."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    format: str = DocumentFormat.PDF.value
    size_bytes: int = 0
    upload_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = DocumentStatus.PENDING.value
    error_message: str | None = None
    page_count: int | None = None
    pages_processed: int = 0
    has_review_flags: bool = False
    blob_path: str = ""
    output_path: str | None = None
    # Additional fields surfaced by the status API
    review_pages: list[int] = field(default_factory=list)
    processing_time_ms: int | None = None
    is_compliant: bool | None = None

    # -- Validation ----------------------------------------------------------

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty == valid)."""
        errors: list[str] = []
        if not self.name:
            errors.append("name must not be empty")
        try:
            DocumentFormat(self.format)
        except ValueError:
            errors.append(f"format must be one of {[f.value for f in DocumentFormat]}")
        if self.size_bytes <= 0:
            errors.append("size_bytes must be > 0")
        if self.size_bytes > MAX_FILE_SIZE_BYTES:
            errors.append(f"size_bytes must be ≤ {MAX_FILE_SIZE_BYTES}")
        try:
            DocumentStatus(self.status)
        except ValueError:
            errors.append(f"status must be one of {[s.value for s in DocumentStatus]}")
        return errors

    # -- Serialisation -------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-safe dict matching the status API contract."""
        return {
            "document_id": self.id,
            "name": self.name,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "upload_timestamp": self.upload_timestamp.isoformat() if isinstance(self.upload_timestamp, datetime) else self.upload_timestamp,
            "status": self.status,
            "error_message": self.error_message,
            "page_count": self.page_count,
            "pages_processed": self.pages_processed,
            "has_review_flags": self.has_review_flags,
            "review_pages": self.review_pages,
            "processing_time_ms": self.processing_time_ms,
            "is_compliant": self.is_compliant,
        }

    @classmethod
    def from_metadata(cls, doc_id: str, metadata: dict[str, str]) -> Document:
        """Reconstruct a Document from blob metadata key-value strings."""
        def _int_or_none(val: str | None) -> int | None:
            if val is None or val == "" or val == "None":
                return None
            return int(val)

        def _bool(val: str | None) -> bool:
            return val is not None and val.lower() in ("true", "1", "yes")

        def _list_int(val: str | None) -> list[int]:
            if not val or val == "[]":
                return []
            return [int(x.strip()) for x in val.strip("[]").split(",") if x.strip()]

        ts_raw = metadata.get("upload_timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw) if ts_raw else datetime.now(timezone.utc)
        except (ValueError, TypeError):
            ts = datetime.now(timezone.utc)

        return cls(
            id=doc_id,
            name=metadata.get("name", ""),
            format=metadata.get("format", "pdf"),
            size_bytes=int(metadata.get("size_bytes", "0")),
            upload_timestamp=ts,
            status=metadata.get("status", DocumentStatus.PENDING.value),
            error_message=metadata.get("error_message") or None,
            page_count=_int_or_none(metadata.get("page_count")),
            pages_processed=int(metadata.get("pages_processed", "0")),
            has_review_flags=_bool(metadata.get("has_review_flags")),
            blob_path=metadata.get("blob_path", ""),
            output_path=metadata.get("output_path") or None,
            review_pages=_list_int(metadata.get("review_pages")),
            processing_time_ms=_int_or_none(metadata.get("processing_time_ms")),
            is_compliant=_bool(metadata.get("is_compliant")) if metadata.get("is_compliant") else None,
        )

    def to_metadata(self) -> dict[str, str]:
        """Serialise to flat string dict suitable for blob metadata."""
        return {
            "name": self.name,
            "format": self.format,
            "size_bytes": str(self.size_bytes),
            "upload_timestamp": self.upload_timestamp.isoformat() if isinstance(self.upload_timestamp, datetime) else str(self.upload_timestamp),
            "status": self.status,
            "error_message": self.error_message or "",
            "page_count": str(self.page_count) if self.page_count is not None else "",
            "pages_processed": str(self.pages_processed),
            "has_review_flags": str(self.has_review_flags),
            "blob_path": self.blob_path,
            "output_path": self.output_path or "",
            "review_pages": str(self.review_pages),
            "processing_time_ms": str(self.processing_time_ms) if self.processing_time_ms is not None else "",
            "is_compliant": str(self.is_compliant) if self.is_compliant is not None else "",
        }


@dataclass
class CellData:
    """A single cell in a structured table (richer than TableData's string lists)."""
    text: str = ""
    is_header: bool = False
    rowspan: int = 1
    colspan: int = 1
    scope: str | None = None  # "col", "row", or None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.rowspan < 1:
            errors.append("rowspan must be >= 1")
        if self.colspan < 1:
            errors.append("colspan must be >= 1")
        if self.scope is not None and self.scope not in ("col", "row"):
            errors.append("scope must be 'col', 'row', or None")
        return errors


@dataclass
class WcagViolation:
    """A single WCAG 2.1 AA rule violation found in generated HTML."""
    rule_id: str = ""
    severity: str = Severity.MODERATE.value
    description: str = ""
    html_element: str = ""
    help_url: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.rule_id:
            errors.append("rule_id must not be empty")
        try:
            Severity(self.severity)
        except ValueError:
            errors.append(f"severity must be one of {[s.value for s in Severity]}")
        if not self.description:
            errors.append("description must not be empty")
        return errors

    def to_dict(self) -> dict[str, str]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "description": self.description,
            "html_element": self.html_element,
            "help_url": self.help_url,
        }


@dataclass
class ConversionResult:
    """Output of a full document conversion run."""
    document_id: str = ""
    html_content: str = ""
    image_assets: list[dict[str, Any]] = field(default_factory=list)  # [{filename, bytes}]
    wcag_violations: list[WcagViolation] = field(default_factory=list)
    is_compliant: bool = True
    review_pages: list[int] = field(default_factory=list)
    processing_time_ms: int = 0

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.document_id:
            errors.append("document_id must not be empty")
        if not self.html_content:
            errors.append("html_content must not be empty")
        if self.processing_time_ms < 0:
            errors.append("processing_time_ms must be >= 0")
        for v in self.wcag_violations:
            errors.extend(v.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "wcag_violations": [v.to_dict() for v in self.wcag_violations],
            "is_compliant": self.is_compliant,
            "review_pages": self.review_pages,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class EnhancedPageResult:
    """Extended page result with OCR metadata — wraps the existing PageResult.

    Use this when you need source_type/extraction_method/ocr_confidence metadata
    alongside the raw extraction data stored in a pdf_extractor.PageResult.
    """
    page_number: int = 0
    source_type: str = SourceType.DIGITAL.value
    text_spans: list[TextSpan] = field(default_factory=list)
    tables: list[TableData] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    ocr_confidence: float | None = None
    needs_review: bool = False
    extraction_method: str = ExtractionMethod.DIRECT.value

    @classmethod
    def from_page_result(
        cls,
        pr: PageResult,
        ocr_confidence: float | None = None,
    ) -> EnhancedPageResult:
        """Build from an existing pdf_extractor.PageResult."""
        if pr.is_scanned:
            source = SourceType.SCANNED.value
            method = ExtractionMethod.OCR.value
        else:
            source = SourceType.DIGITAL.value
            method = ExtractionMethod.DIRECT.value

        needs_review = (ocr_confidence is not None and ocr_confidence < 0.70)

        return cls(
            page_number=pr.page_number,
            source_type=source,
            text_spans=pr.text_spans,
            tables=pr.tables,
            images=pr.images,
            ocr_confidence=ocr_confidence,
            needs_review=needs_review,
            extraction_method=method,
        )
