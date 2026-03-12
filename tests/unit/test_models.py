"""
Unit tests for shared data models — T022

Tests the dataclass models defined in models.py.
Validates field defaults, enum values, UUID generation,
and compliance semantics per specs/001-sean/data-model.md.

Covers:
  - Document (status enum, format enum, UUID id, defaults)
  - ConversionResult (compliance logic)
  - WcagViolation (severity enum)
  - CellData (defaults, header cells, spanning)
"""

import uuid
from datetime import datetime

import pytest

from backend.models import (
    CellData,
    ConversionResult,
    Document,
    DocumentFormat,
    DocumentStatus,
    Severity,
    WcagViolation,
)


# ── Document ────────────────────────────────────────────────────────────


class TestDocument:
    """Document model tests."""

    def test_document_creation_with_defaults(self, sample_document_kwargs):
        """Creating a Document with only required fields should populate
        sensible defaults for optional / auto-generated fields."""
        doc = Document(**sample_document_kwargs)

        assert doc.name == "annual-report-2025"
        # Document stores format as a string value, not enum instance
        assert doc.format == DocumentFormat.PDF.value  # "pdf"
        assert doc.size_bytes == 2_048_576
        assert doc.blob_path == "files/annual-report-2025.pdf"

        # Auto-generated / default fields
        assert doc.id is not None
        assert doc.status == DocumentStatus.PENDING.value  # "pending"
        assert doc.error_message is None
        assert doc.page_count is None
        assert doc.pages_processed == 0
        assert doc.has_review_flags is False
        assert doc.output_path is None
        assert isinstance(doc.upload_timestamp, datetime)

    def test_document_status_enum_values(self):
        """DocumentStatus must expose the four lifecycle states."""
        expected = {"pending", "processing", "completed", "failed"}
        # Filter to string-valued members only (excludes _transitions dict)
        actual = {s.value for s in DocumentStatus if isinstance(s.value, str)}
        assert expected.issubset(actual)

    def test_document_format_enum_values(self):
        """DocumentFormat must expose exactly three members."""
        expected = {"pdf", "docx", "pptx"}
        actual = {f.value for f in DocumentFormat}
        assert actual == expected

    def test_document_id_is_uuid_format(self, sample_document_kwargs):
        """Document.id should be a valid UUID string."""
        doc = Document(**sample_document_kwargs)
        # Should not raise — validates UUID format
        parsed = uuid.UUID(doc.id)
        assert str(parsed) == doc.id


# ── ConversionResult ────────────────────────────────────────────────────


class TestConversionResult:
    """ConversionResult model tests."""

    def test_conversion_result_creation(self):
        """ConversionResult should be creatable with all required fields."""
        result = ConversionResult(
            document_id="abc-123",
            html_content="<html></html>",
            image_assets=[],
            wcag_violations=[],
            is_compliant=True,
            review_pages=[],
            processing_time_ms=1500,
        )

        assert result.document_id == "abc-123"
        assert result.html_content == "<html></html>"
        assert result.image_assets == []
        assert result.wcag_violations == []
        assert result.is_compliant is True
        assert result.review_pages == []
        assert result.processing_time_ms == 1500

    def test_conversion_result_is_compliant_when_no_violations(self):
        """A result with zero WCAG violations should be compliant."""
        result = ConversionResult(
            document_id="abc-123",
            html_content="<html></html>",
            image_assets=[],
            wcag_violations=[],
            is_compliant=True,
            review_pages=[],
            processing_time_ms=800,
        )
        assert result.is_compliant is True
        assert len(result.wcag_violations) == 0

    def test_conversion_result_not_compliant_with_critical_violations(
        self, sample_wcag_violation_kwargs
    ):
        """A result with critical violations must NOT be compliant."""
        violation = WcagViolation(**sample_wcag_violation_kwargs)
        assert violation.severity == Severity.CRITICAL.value  # "critical"

        result = ConversionResult(
            document_id="abc-123",
            html_content="<html></html>",
            image_assets=[],
            wcag_violations=[violation],
            is_compliant=False,
            review_pages=[],
            processing_time_ms=1200,
        )
        assert result.is_compliant is False
        assert len(result.wcag_violations) == 1
        assert result.wcag_violations[0].severity == Severity.CRITICAL.value


# ── WcagViolation ───────────────────────────────────────────────────────


class TestWcagViolation:
    """WcagViolation model tests."""

    def test_wcag_violation_creation(self, sample_wcag_violation_kwargs):
        """WcagViolation should be creatable with all required fields."""
        v = WcagViolation(**sample_wcag_violation_kwargs)

        assert v.rule_id == "image-alt"
        assert v.severity == Severity.CRITICAL.value  # stored as string
        assert v.description == "Images must have alternate text"
        assert v.html_element == '<img src="chart.png">'
        assert "dequeuniversity.com" in v.help_url

    def test_wcag_violation_severity_values(self):
        """Severity must expose exactly four levels."""
        expected = {"critical", "serious", "moderate", "minor"}
        actual = {s.value for s in Severity}
        assert actual == expected


# ── CellData ────────────────────────────────────────────────────────────


class TestCellData:
    """CellData model tests."""

    def test_cell_data_defaults(self):
        """CellData created with only text should have sane defaults."""
        cell = CellData(text="Revenue")

        assert cell.text == "Revenue"
        assert cell.is_header is False
        assert cell.rowspan == 1
        assert cell.colspan == 1
        assert cell.scope is None

    def test_cell_data_header_cell(self):
        """A header CellData should carry is_header=True and a scope."""
        cell = CellData(text="Quarter", is_header=True, scope="col")

        assert cell.is_header is True
        assert cell.scope == "col"

    def test_cell_data_with_spans(self):
        """CellData should support rowspan and colspan > 1."""
        cell = CellData(text="Merged", rowspan=2, colspan=3)

        assert cell.rowspan == 2
        assert cell.colspan == 3
