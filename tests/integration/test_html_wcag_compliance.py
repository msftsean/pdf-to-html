"""
Integration test: Generate HTML via build_html and validate with wcag_validator.

Verifies that the HTML builder produces output with zero critical/serious
WCAG violations, confirming the skip-nav, heading hierarchy, table scope,
image alt, and landmark changes are effective.
"""

import pytest

from html_builder import build_html, _enforce_heading_hierarchy
from pdf_extractor import PageResult, TextSpan, ImageInfo, TableData
from ocr_service import OcrPageResult, OcrSpan, OcrTable, OcrTableCell
from wcag_validator import validate_html


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_span(text, x0=72.0, y0=100.0, size=12.0, bold=False, italic=False):
    """Helper to create a TextSpan."""
    return TextSpan(
        text=text,
        x0=x0, y0=y0,
        x1=x0 + len(text) * 6, y1=y0 + size,
        font="Helvetica",
        size=size,
        color=0,
        bold=bold,
        italic=italic,
    )


def _make_page(
    page_number=0,
    is_scanned=False,
    spans=None,
    images=None,
    tables=None,
):
    """Helper to create a PageResult."""
    return PageResult(
        page_number=page_number,
        width=612.0,
        height=792.0,
        is_scanned=is_scanned,
        text_spans=spans or [],
        images=images or [],
        tables=tables or [],
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBuildHtmlWcagCompliance:
    """Verify that build_html output passes WCAG pre-validation."""

    def test_simple_digital_page_zero_violations(self):
        """A basic digital page with heading + paragraph should pass."""
        spans = [
            _make_span("Annual Report", y0=50, size=26.0, bold=True),  # h1
            _make_span("This is the introduction paragraph.", y0=100, size=12.0),
        ]
        pages = [_make_page(spans=spans)]
        html_out, _ = build_html(pages, {}, {"title": "Test Doc"})

        violations = validate_html(html_out)
        critical_serious = [
            v for v in violations if v.severity in ("critical", "serious")
        ]
        assert critical_serious == [], (
            f"Expected zero critical/serious violations, got: "
            f"{[(v.rule_id, v.description) for v in critical_serious]}"
        )

    def test_html_has_lang_attribute(self):
        """Output HTML must have lang='en' on the <html> element."""
        pages = [_make_page(spans=[_make_span("Hello")])]
        html_out, _ = build_html(pages, {}, {})
        assert 'lang="en"' in html_out

    def test_skip_nav_link_present(self):
        """Output must contain a skip navigation link."""
        pages = [_make_page(spans=[_make_span("Content")])]
        html_out, _ = build_html(pages, {}, {})
        assert 'class="skip-nav"' in html_out
        assert 'href="#main-content"' in html_out
        assert 'id="main-content"' in html_out

    def test_main_landmark_present(self):
        """Output must have a <main> landmark with id='main-content'."""
        pages = [_make_page(spans=[_make_span("Content")])]
        html_out, _ = build_html(pages, {}, {})
        assert '<main id="main-content">' in html_out

    def test_section_has_role_region(self):
        """Each page    section must have role='region'."""
        pages = [_make_page(spans=[_make_span("Content")])]
        html_out, _ = build_html(pages, {}, {})
        assert 'role="region"' in html_out

    def test_heading_hierarchy_no_gaps(self):
        """Headings must not skip levels — h1→h3 should become h1→h2."""
        blocks = [
            {"type": "heading", "level": 1, "text": "Title", "x0": 0},
            {"type": "heading", "level": 3, "text": "Subsection", "x0": 0},
            {"type": "heading", "level": 6, "text": "Deep", "x0": 0},
        ]
        result = _enforce_heading_hierarchy(blocks)
        levels = [b["level"] for b in result if b["type"] == "heading"]
        # Should be [1, 2, 3] — no gaps
        for i in range(1, len(levels)):
            assert levels[i] <= levels[i - 1] + 1, (
                f"Heading gap: h{levels[i]} follows h{levels[i-1]}"
            )

    def test_table_headers_have_scope(self):
        """Tables must have scope='col' on <th> elements."""
        table = TableData(
            bbox=(72, 200, 540, 400),
            header=["Name", "Value", "Unit"],
            rows=[["Length", "100", "cm"]],
        )
        pages = [_make_page(tables=[table])]
        html_out, _ = build_html(pages, {}, {"title": "Tables"})

        violations = validate_html(html_out)
        scope_violations = [v for v in violations if v.rule_id == "th-has-scope"]
        assert scope_violations == [], (
            f"Expected no scope violations, got: "
            f"{[v.description for v in scope_violations]}"
        )

    def test_images_have_meaningful_alt(self):
        """Images must have meaningful alt text, not just 'Image from page N'."""
        img = ImageInfo(
            page_number=0,
            x0=72, y0=100, x1=300, y1=400,
            image_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
            extension="png",
            xref=1,
        )
        pages = [_make_page(images=[img])]
        html_out, _ = build_html(pages, {}, {"title": "Images"})

        # Check no violations for image-alt
        violations = validate_html(html_out)
        alt_violations = [v for v in violations if v.rule_id == "image-alt"]
        assert alt_violations == [], f"Image alt violations:~ {alt_violations}"

        # Verify alt text is more meaningful than just "Image from page N"
        assert 'alt="Image from page' not in html_out
        assert 'alt="Figure' in html_out

    def test_images_wrapped_in_figure(self):
        """Images must be wrapped in <figure>/<figcaption>."""
        img = ImageInfo(
            page_number=0,
            x0=72, y0=100, x1=300, y1=400,
            image_bytes=b"\x89PNG" + b"\x00" * 50,
            extension="png",
            xref=1,
        )
        pages = [_make_page(images=[img])]
        html_out, _ = build_html(pages, {}, {})
        assert "<figure>" in html_out
        assert "<figcaption>" in html_out

    def test_focus_visible_styles_present(self):
        """CSS must include :focus-visible outline styles."""
        pages = [_make_page(spans=[_make_span("Content")])]
        html_out, _ = build_html(pages, {}, {})
        assert ":focus-visible" in html_out
        assert "outline:" in html_out or "outline :" in html_out

    def test_link_styles_have_underline(self):
        """Links must have text-decoration: underline for visibility."""
        pages = [_make_page(spans=[_make_span("Content")])]
        html_out, _ = build_html(pages, {}, {})
        assert "text-decoration: underline" in html_out

    def test_review_banner_shown_for_low_confidence(self):
        """Low-confidence OCR pages must show a review banner."""
        ocr_page = OcrPageResult(
            page_number=0,
            width=612, height=792,
            lines=[OcrSpan("Some text", 72, 100, 300, 112, 0.55)],
            confidence=0.55,
            needs_review=True,
        )
        pages = [_make_page(is_scanned=True)]
        html_out, _ = build_html(pages, {0: ocr_page}, {"title": "OCR Test"})

        assert 'class="review-notice"' in html_out
        assert 'role="alert"' in html_out
        assert "Review Required" in html_out
        assert "55%" in html_out

    def test_no_review_banner_for_high_confidence(self):
        """High-confidence OCR pages should NOT show a review banner."""
        ocr_page = OcrPageResult(
            page_number=0,
            width=612, height=792,
            lines=[OcrSpan("Clear text", 72, 100, 300, 112, 0.95)],
            confidence=0.95,
            needs_review=False,
        )
        pages = [_make_page(is_scanned=True)]
        html_out, _ = build_html(pages, {0: ocr_page}, {"title": "Good OCR"})
        assert "Review Required" not in html_out

    def test_content_unavailable_for_empty_ocr(self):
        """Pages with no OCR text should show a content-unavailable notice."""
        ocr_page = OcrPageResult(
            page_number=0,
            width=612, height=792,
            lines=[],
            tables=[],
            confidence=0.0,
            needs_review=True,
        )
        pages = [_make_page(is_scanned=True)]
        html_out, _ = build_html(pages, {0: ocr_page}, {"title": "Empty OCR"})
        assert "Content Unavailable" in html_out

    def test_scanned_page_no_ocr_result_shows_unavailable(self):
        """Scanned page with no OCR results at all shows content-unavailable."""
        pages = [_make_page(is_scanned=True)]
        html_out, _ = build_html(pages, {}, {"title": "Missing OCR"})
        assert "Content Unavailable" in html_out

    def test_full_document_zero_critical_serious(self):
        """A realistic multi-page document should have zero critical/serious violations."""
        spans_p1 = [
            _make_span("Department of Information Technology", y0=50, size=26.0, bold=True),
            _make_span("Annual Report 2025", y0=90, size=20.0, bold=True),
            _make_span("This document summarizes the department activities.", y0=140, size=12.0),
        ]
        spans_p2 = [
            _make_span("Budget Overview", y0=50, size=20.0, bold=True),
            _make_span("The total budget for FY2025 was $2.3M.", y0=100, size=12.0),
        ]
        table = TableData(
            bbox=(72, 200, 540, 400),
            header=["Category", "Amount", "Percentage"],
            rows=[
                ["Personnel", "$1.5M", "65%"],
                ["Operations", "$0.5M", "22%"],
                ["Technology", "$0.3M", "13%"],
            ],
        )
        pages = [
            _make_page(page_number=0, spans=spans_p1),
            _make_page(page_number=1, spans=spans_p2, tables=[table]),
        ]
        html_out, _ = build_html(pages, {}, {"title": "NCDIT Annual Report"})

        violations = validate_html(html_out)
        critical_serious = [
            v for v in violations if v.severity in ("critical", "serious")
        ]
        assert critical_serious == [], (
            f"Full document has critical/serious violations: "
            f"{[(v.rule_id, v.description) for v in critical_serious]}"
        )

    def test_contrast_colors_are_sufficient(self):
        """Body text color #1a1a1a on #fff should pass contrast check."""
        pages = [_make_page(spans=[_make_span("Test text")])]
        html_out, _ = build_html(pages, {}, {})
        violations = validate_html(html_out)
        contrast_violations = [v for v in violations if v.rule_id == "color-contrast"]
        assert contrast_violations == []
