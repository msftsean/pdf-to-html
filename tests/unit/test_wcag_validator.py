"""
Unit tests for wcag_validator — T021

Tests the rule-based WCAG 2.1 AA HTML validator.
Validates the pure-Python pre-checker that catches common
accessibility violations before axe-core runs client-side.

Validates:
  - Missing lang attribute on <html>
  - Images without alt text / empty alt
  - Tables without proper headers / scope
  - Skipped heading levels (e.g. h1 → h3)
  - Empty links
  - Multiple violations in one document
  - Violation severity assignment
"""

import pytest

from models import Severity, WcagViolation
from wcag_validator import validate_html


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wrap_body(body_html: str, *, lang: str = "en") -> str:
    """Wrap a body snippet in a minimal valid HTML document."""
    return (
        "<!DOCTYPE html>\n"
        f'<html lang="{lang}">\n'
        "<head><meta charset=\"utf-8\"><title>Test</title></head>\n"
        f"<body>\n<h1>Heading</h1>\n{body_html}\n</body>\n</html>"
    )


def _no_lang_html(body_html: str = "<h1>Test</h1><p>Content</p>") -> str:
    """Return an HTML document with no lang attribute."""
    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        '<head><meta charset="utf-8"><title>Test</title></head>\n'
        f"<body>\n{body_html}\n</body>\n</html>"
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidHtml:
    """A fully compliant document should produce zero violations."""

    def test_valid_html_returns_no_violations(self, valid_html):
        violations = validate_html(valid_html)
        assert violations == []


# ---------------------------------------------------------------------------
# Language attribute
# ---------------------------------------------------------------------------


class TestLangAttribute:
    """WCAG SC 3.1.1 — Language of Page."""

    def test_missing_lang_attribute_flagged(self):
        html = _no_lang_html()
        violations = validate_html(html)

        lang_violations = [v for v in violations if "lang" in v.rule_id.lower()
                           or "lang" in v.description.lower()]
        assert len(lang_violations) >= 1, (
            "Missing lang attribute should produce at least one violation"
        )


# ---------------------------------------------------------------------------
# Images & alt text
# ---------------------------------------------------------------------------


class TestImageAlt:
    """WCAG SC 1.1.1 — Non-text Content."""

    def test_img_without_alt_flagged(self):
        html = _wrap_body('<img src="chart.png">')
        violations = validate_html(html)

        img_violations = [v for v in violations if "alt" in v.rule_id.lower()
                          or "img" in v.rule_id.lower()
                          or "image" in v.description.lower()]
        assert len(img_violations) >= 1, (
            "Image without alt should produce a violation"
        )

    def test_img_with_empty_alt_flagged(self):
        html = _wrap_body('<img src="chart.png" alt="">')
        violations = validate_html(html)

        img_violations = [v for v in violations if "alt" in v.rule_id.lower()
                          or "img" in v.rule_id.lower()
                          or "image" in v.description.lower()]
        assert len(img_violations) >= 1, (
            "Image with empty alt should produce a violation"
        )

    def test_img_with_alt_passes(self):
        html = _wrap_body('<img src="chart.png" alt="Quarterly revenue chart">')
        violations = validate_html(html)

        img_violations = [v for v in violations if "alt" in v.rule_id.lower()
                          or "img" in v.rule_id.lower()]
        assert len(img_violations) == 0, (
            "Image with meaningful alt text should NOT produce a violation"
        )


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------


class TestTableHeaders:
    """WCAG SC 1.3.1 — Info and Relationships (tables)."""

    def test_table_without_headers_flagged(self):
        html = _wrap_body(
            "<table>"
            "<tr><td>A</td><td>B</td></tr>"
            "<tr><td>1</td><td>2</td></tr>"
            "</table>"
        )
        violations = validate_html(html)

        table_violations = [v for v in violations if "table" in v.rule_id.lower()
                            or "th" in v.rule_id.lower()
                            or "header" in v.description.lower()]
        assert len(table_violations) >= 1, (
            "Table without <th> should produce a violation"
        )

    def test_table_with_proper_scope_passes(self):
        html = _wrap_body(
            "<table>"
            '<thead><tr><th scope="col">Name</th><th scope="col">Value</th></tr></thead>'
            "<tbody><tr><td>X</td><td>42</td></tr></tbody>"
            "</table>"
        )
        violations = validate_html(html)

        table_violations = [v for v in violations if "table" in v.rule_id.lower()
                            or "th" in v.rule_id.lower()
                            or "header" in v.description.lower()]
        assert len(table_violations) == 0, (
            "Table with proper <th scope> should NOT produce a violation"
        )


# ---------------------------------------------------------------------------
# Heading hierarchy
# ---------------------------------------------------------------------------


class TestHeadingHierarchy:
    """WCAG SC 1.3.1 — Heading levels must not be skipped."""

    def test_skipped_heading_levels_flagged(self):
        """h1 followed directly by h3 (skipping h2) is a violation."""
        html = (
            '<!DOCTYPE html>\n<html lang="en">\n'
            '<head><meta charset="utf-8"><title>Test</title></head>\n'
            "<body>\n"
            "  <h1>Main</h1>\n"
            "  <h3>Skipped h2!</h3>\n"
            "</body>\n</html>"
        )
        violations = validate_html(html)

        heading_violations = [v for v in violations if "heading" in v.rule_id.lower()
                              or "heading" in v.description.lower()]
        assert len(heading_violations) >= 1, (
            "Skipping from h1 to h3 should produce a heading violation"
        )

    def test_sequential_headings_pass(self):
        """h1 → h2 → h3 is valid sequential order."""
        html = (
            '<!DOCTYPE html>\n<html lang="en">\n'
            '<head><meta charset="utf-8"><title>Test</title></head>\n'
            "<body>\n"
            "  <h1>Main</h1>\n"
            "  <h2>Section</h2>\n"
            "  <h3>Subsection</h3>\n"
            '  <img src="x.png" alt="Photo">\n'
            "</body>\n</html>"
        )
        violations = validate_html(html)

        heading_violations = [v for v in violations if "heading" in v.rule_id.lower()
                              or "heading" in v.description.lower()]
        assert len(heading_violations) == 0, (
            "Sequential headings h1→h2→h3 should NOT produce violations"
        )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


class TestEmptyLinks:
    """WCAG SC 2.4.4 — Link Purpose (In Context)."""

    def test_empty_link_flagged(self):
        html = _wrap_body('<a href="https://example.com"></a>')
        violations = validate_html(html)

        link_violations = [v for v in violations if "link" in v.rule_id.lower()
                           or "link" in v.description.lower()
                           or "anchor" in v.description.lower()]
        assert len(link_violations) >= 1, (
            "Empty link (no text content) should produce a violation"
        )


# ---------------------------------------------------------------------------
# Multiple violations & severity
# ---------------------------------------------------------------------------


class TestMultipleViolations:
    """Edge case: documents with several WCAG issues at once."""

    def test_multiple_violations_returned(self):
        """A document with multiple issues should return multiple violations."""
        html = (
            "<!DOCTYPE html>\n<html>\n"  # missing lang
            '<head><meta charset="utf-8"><title>Test</title></head>\n'
            "<body>\n"
            "  <h1>Main</h1>\n"
            '  <img src="pic.png">\n'  # missing alt
            '  <a href="/page"></a>\n'  # empty link
            "  <h3>Oops</h3>\n"  # skipped heading
            "</body>\n</html>"
        )
        violations = validate_html(html)

        assert len(violations) >= 3, (
            f"Expected ≥3 violations, got {len(violations)}: "
            f"{[v.rule_id for v in violations]}"
        )

    def test_violation_severity_levels(self):
        """Every returned violation must have a valid severity."""
        html = (
            "<!DOCTYPE html>\n<html>\n"
            '<head><meta charset="utf-8"><title>Test</title></head>\n'
            "<body>\n"
            '  <img src="x.png">\n'
            "</body>\n</html>"
        )
        violations = validate_html(html)
        valid_severities = {s.value for s in Severity}

        for v in violations:
            assert isinstance(v, WcagViolation), (
                f"Expected WcagViolation, got {type(v)}"
            )
            assert v.severity in valid_severities, (
                f"Invalid severity: {v.severity}"
            )
