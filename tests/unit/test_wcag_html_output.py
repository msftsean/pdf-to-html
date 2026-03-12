"""
WCAG 2.1 AA compliance tests for HTML output from html_builder.

Tests verify that generated HTML meets all accessibility requirements:
- Skip navigation link present
- Heading hierarchy enforced (no skipped levels)
- All images have alt text
- Tables have proper headers with scope attributes
- ARIA landmarks present
- Language attribute set on <html>
- Color contrast in generated CSS
"""

import pytest
from html_builder import build_html
from pdf_extractor import PageResult, TextSpan, ImageInfo, TableData
from wcag_validator import validate_html
from models import Severity


def test_skip_navigation_link():
    """Generated HTML must include a skip navigation link."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    assert '<a href="#main-content" class="skip-nav">Skip to main content</a>' in html
    assert 'id="main-content"' in html


def test_lang_attribute():
    """HTML element must have lang attribute set."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    assert '<html lang="en">' in html or '<html lang="en-US">' in html
    
    # Verify validator doesn't flag it
    violations = validate_html(html)
    lang_violations = [v for v in violations if v.rule_id == "html-has-lang"]
    assert len(lang_violations) == 0


def test_heading_hierarchy_enforced():
    """Heading levels must not skip (h1→h3 without h2 not allowed)."""
    # Create spans that would naturally produce h1, then h3
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[
            TextSpan("Title", 100, 100, 200, 124, "Arial", 24, 0, True, False),  # h1
            TextSpan("Body text", 100, 150, 200, 162, "Arial", 12, 0, False, False),
            TextSpan("Subsection", 100, 200, 200, 214, "Arial", 14, 0, True, False),  # would be h3, corrected to h2
        ]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Verify no heading-order violations
    violations = validate_html(html)
    heading_violations = [v for v in violations if v.rule_id == "heading-order"]
    assert len(heading_violations) == 0


def test_images_have_alt_text():
    """All images must have alt attribute with meaningful text."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)],
        images=[
            ImageInfo(
                page_number=1,
                x0=100, y0=200, x1=300, y1=400,
                image_bytes=b"fake_image_data",
                extension="png",
                xref=1
            )
        ]
    )
    html, image_files = build_html([page], {}, {"title": "Test"})
    
    # Verify alt text is present (auto-generated from position)
    assert 'alt=' in html
    
    # Verify no image-alt violations
    violations = validate_html(html)
    img_violations = [v for v in violations if v.rule_id == "image-alt"]
    assert len(img_violations) == 0


def test_tables_have_headers_with_scope():
    """Tables must have <th> elements with scope attributes."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)],
        tables=[
            TableData(
                bbox=(100, 200, 400, 400),
                header=["Name", "Age", "City"],
                rows=[
                    ["Alice", "30", "Raleigh"],
                    ["Bob", "25", "Durham"],
                ]
            )
        ]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Verify headers have scope="col"
    assert 'scope="col"' in html
    
    # Verify no table violations
    violations = validate_html(html)
    table_violations = [v for v in violations if v.rule_id in ["table-has-header", "th-has-scope"]]
    assert len(table_violations) == 0


def test_aria_landmarks():
    """Generated HTML must include proper ARIA landmarks."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Check for main landmark
    assert 'id="main-content"' in html
    
    # Skip nav should be present
    assert '<a href="#main-content"' in html


def test_color_contrast_in_css():
    """CSS color definitions must meet WCAG AA contrast ratios."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Verify no color-contrast violations in generated HTML
    violations = validate_html(html)
    contrast_violations = [v for v in violations if v.rule_id == "color-contrast"]
    assert len(contrast_violations) == 0


def test_no_empty_links_or_buttons():
    """Links and buttons must have accessible names."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test content", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Verify no empty link/button violations
    violations = validate_html(html)
    link_violations = [v for v in violations if v.rule_id in ["link-name", "button-name"]]
    assert len(link_violations) == 0


def test_comprehensive_wcag_validation():
    """Full WCAG validation pass on complex document."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[
            TextSpan("Document Title", 100, 100, 300, 124, "Arial", 24, 0, True, False),
            TextSpan("Introduction", 100, 150, 250, 168, "Arial", 18, 0, True, False),
            TextSpan("This is the body text of the document.", 100, 200, 400, 212, "Arial", 12, 0, False, False),
            TextSpan("Section 1", 100, 250, 200, 268, "Arial", 18, 0, True, False),
            TextSpan("More content here.", 100, 300, 300, 312, "Arial", 12, 0, False, False),
        ],
        images=[
            ImageInfo(
                page_number=1,
                x0=100, y0=350, x1=300, y1=550,
                image_bytes=b"data",
                extension="png",
                xref=2
            )
        ],
        tables=[
            TableData(
                bbox=(100, 600, 400, 800),
                header=["Product", "Price", "Stock"],
                rows=[
                    ["Widget A", "$10", "50"],
                    ["Widget B", "$15", "30"],
                ]
            )
        ]
    )
    
    html, image_files = build_html([page], {}, {"title": "Test Document"})
    
    # Run full WCAG validation
    violations = validate_html(html)
    
    # Should have no critical or serious violations
    critical = [v for v in violations if v.severity == Severity.CRITICAL.value]
    serious = [v for v in violations if v.severity == Severity.SERIOUS.value]
    
    assert len(critical) == 0, f"Critical violations found: {critical}"
    assert len(serious) == 0, f"Serious violations found: {serious}"


def test_keyboard_focus_styles():
    """Generated CSS must include visible focus indicators."""
    page = PageResult(
        page_number=1,
        width=612,
        height=792,
        is_scanned=False,
        text_spans=[TextSpan("Test", 100, 100, 200, 112, "Arial", 12, 0, False, False)]
    )
    html, _ = build_html([page], {}, {"title": "Test"})
    
    # Check for focus-visible styles in CSS
    assert ':focus-visible' in html or ':focus' in html
    assert 'outline:' in html  # Focus outline should be defined
