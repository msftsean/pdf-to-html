"""
Pure-Python WCAG 2.1 AA pre-validator for generated HTML.

This module performs server-side checks for the most common accessibility
violations *before* the HTML reaches the browser.  It is **not** a replacement
for axe-core (which runs client-side) but catches low-hanging issues early so
the conversion pipeline can flag pages for review.

Implemented rules
-----------------
- **img-alt**: Every ``<img>`` must have a non-empty ``alt`` attribute.
- **table-header**: Tables must include ``<thead>``/``<th>`` elements with
  a ``scope`` attribute.
- **heading-order**: Headings must not skip levels (e.g. h1→h3 without h2).
- **html-lang**: The ``<html>`` element must have a ``lang`` attribute.
- **color-contrast**: Inline ``color``/``background-color`` styles are checked
  against WCAG AA minimum contrast ratio (4.5:1 normal, 3:1 large text).
- **label**: ``<input>`` elements must have associated ``<label>`` elements or
  ``aria-label`` / ``aria-labelledby``.
- **link-name**: ``<a>`` and ``<button>`` elements must not be empty.
"""

from __future__ import annotations

import logging
import math
import re
from html.parser import HTMLParser
from typing import Any

from models import WcagViolation, Severity

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_html(html_content: str) -> list[WcagViolation]:
    """Run all WCAG 2.1 AA pre-checks on *html_content*.

    Returns a list of ``WcagViolation`` instances (empty == no issues found).
    """
    violations: list[WcagViolation] = []

    violations.extend(_check_html_lang(html_content))
    violations.extend(_check_img_alt(html_content))
    violations.extend(_check_table_headers(html_content))
    violations.extend(_check_heading_order(html_content))
    violations.extend(_check_color_contrast(html_content))
    violations.extend(_check_form_labels(html_content))
    violations.extend(_check_empty_links_buttons(html_content))

    return violations


# ---------------------------------------------------------------------------
# Individual rule checks
# ---------------------------------------------------------------------------

def _check_html_lang(html_content: str) -> list[WcagViolation]:
    """WCAG 3.1.1 — ``<html>`` must have a ``lang`` attribute."""
    match = re.search(r"<html\b([^>]*)>", html_content, re.IGNORECASE)
    if match is None:
        return [WcagViolation(
            rule_id="html-has-lang",
            severity=Severity.SERIOUS.value,
            description="Document is missing <html> element",
            html_element="<html>",
            help_url="https://dequeuniversity.com/rules/axe/4.7/html-has-lang",
        )]

    attrs = match.group(1)
    if not re.search(r'\blang\s*=\s*["\'][a-zA-Z]', attrs):
        return [WcagViolation(
            rule_id="html-has-lang",
            severity=Severity.SERIOUS.value,
            description="<html> element must have a valid lang attribute",
            html_element=match.group(0),
            help_url="https://dequeuniversity.com/rules/axe/4.7/html-has-lang",
        )]
    return []


def _check_img_alt(html_content: str) -> list[WcagViolation]:
    """WCAG 1.1.1 — Every ``<img>`` must have a non-empty ``alt``."""
    violations: list[WcagViolation] = []
    for match in re.finditer(r"<img\b([^>]*)>", html_content, re.IGNORECASE):
        attrs = match.group(1)
        tag_html = match.group(0)

        # Check for role="presentation" or aria-hidden — decorative images exempt
        if re.search(r'role\s*=\s*["\']presentation["\']', attrs, re.IGNORECASE):
            continue
        if re.search(r'aria-hidden\s*=\s*["\']true["\']', attrs, re.IGNORECASE):
            continue

        alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', attrs)
        if alt_match is None:
            violations.append(WcagViolation(
                rule_id="image-alt",
                severity=Severity.CRITICAL.value,
                description="Image is missing alt attribute",
                html_element=_truncate(tag_html),
                help_url="https://dequeuniversity.com/rules/axe/4.7/image-alt",
            ))
        elif alt_match.group(1).strip() == "":
            # Empty alt without role=presentation
            violations.append(WcagViolation(
                rule_id="image-alt",
                severity=Severity.CRITICAL.value,
                description="Image has empty alt attribute without decorative role",
                html_element=_truncate(tag_html),
                help_url="https://dequeuniversity.com/rules/axe/4.7/image-alt",
            ))
    return violations


def _check_table_headers(html_content: str) -> list[WcagViolation]:
    """WCAG 1.3.1 — Tables must have ``<th>`` with ``scope``."""
    violations: list[WcagViolation] = []
    for table_match in re.finditer(
        r"<table\b[^>]*>(.*?)</table>", html_content, re.IGNORECASE | re.DOTALL
    ):
        table_html = table_match.group(0)
        table_body = table_match.group(1)

        # Layout tables (role=presentation) are exempt
        if re.search(r'role\s*=\s*["\']presentation["\']', table_html, re.IGNORECASE):
            continue

        # Must have at least one <th>
        if not re.search(r"<th\b", table_body, re.IGNORECASE):
            violations.append(WcagViolation(
                rule_id="table-has-header",
                severity=Severity.SERIOUS.value,
                description="Data table is missing header cells (<th>)",
                html_element=_truncate(table_html),
                help_url="https://dequeuniversity.com/rules/axe/4.7/td-has-header",
            ))
            continue

        # Each <th> should have scope
        for th_match in re.finditer(r"<th\b([^>]*)>", table_body, re.IGNORECASE):
            th_attrs = th_match.group(1)
            if not re.search(r'scope\s*=\s*["\']', th_attrs, re.IGNORECASE):
                violations.append(WcagViolation(
                    rule_id="th-has-scope",
                    severity=Severity.MODERATE.value,
                    description="Table header (<th>) is missing scope attribute",
                    html_element=_truncate(th_match.group(0)),
                    help_url="https://dequeuniversity.com/rules/axe/4.7/th-has-data-cells",
                ))
    return violations


def _check_heading_order(html_content: str) -> list[WcagViolation]:
    """WCAG 1.3.1 — Headings must not skip levels (h1→h3 without h2)."""
    violations: list[WcagViolation] = []
    headings = re.findall(r"<(h[1-6])\b[^>]*>", html_content, re.IGNORECASE)
    if not headings:
        return []

    levels = [int(h[1]) for h in headings]
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            violations.append(WcagViolation(
                rule_id="heading-order",
                severity=Severity.MODERATE.value,
                description=(
                    f"Heading level skipped: <h{levels[i]}> follows <h{levels[i-1]}> "
                    f"(expected ≤ h{levels[i-1] + 1})"
                ),
                html_element=f"<h{levels[i]}>",
                help_url="https://dequeuniversity.com/rules/axe/4.7/heading-order",
            ))
    return violations


def _check_color_contrast(html_content: str) -> list[WcagViolation]:
    """WCAG 1.4.3 — Check inline style color vs background-color contrast.

    Only inspects elements with *both* ``color`` and ``background-color`` set
    in a ``style`` attribute.  This is inherently limited (CSS classes, inherited
    styles are not evaluated) but catches the most common server-side issues.
    """
    violations: list[WcagViolation] = []
    for match in re.finditer(
        r"<(\w+)\b([^>]*style\s*=\s*[\"'][^\"']*[\"'][^>]*)>",
        html_content,
        re.IGNORECASE,
    ):
        tag = match.group(1)
        attrs = match.group(2)

        style_match = re.search(r'style\s*=\s*["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        if style_match is None:
            continue

        style = style_match.group(1)
        fg = _parse_css_color(style, "color")
        bg = _parse_css_color(style, "background-color")

        if fg is None or bg is None:
            continue

        ratio = _contrast_ratio(fg, bg)
        # AA threshold: 4.5:1 for normal text, 3:1 for large text
        # We use 4.5 as we can't reliably determine font size here
        if ratio < 4.5:
            violations.append(WcagViolation(
                rule_id="color-contrast",
                severity=Severity.SERIOUS.value,
                description=(
                    f"Insufficient contrast ratio {ratio:.2f}:1 "
                    f"(minimum 4.5:1 for WCAG AA)"
                ),
                html_element=_truncate(match.group(0)),
                help_url="https://dequeuniversity.com/rules/axe/4.7/color-contrast",
            ))
    return violations


def _check_form_labels(html_content: str) -> list[WcagViolation]:
    """WCAG 1.3.1 / 4.1.2 — Form inputs must have associated labels."""
    violations: list[WcagViolation] = []

    # Collect all <label for="..."> targets
    label_fors: set[str] = set()
    for lbl in re.finditer(r'<label\b[^>]*\bfor\s*=\s*["\']([^"\']+)["\']', html_content, re.IGNORECASE):
        label_fors.add(lbl.group(1))

    for input_match in re.finditer(r"<input\b([^>]*)>", html_content, re.IGNORECASE):
        attrs = input_match.group(1)

        # Hidden inputs are exempt
        if re.search(r'type\s*=\s*["\']hidden["\']', attrs, re.IGNORECASE):
            continue
        # Submit/button inputs are exempt
        if re.search(r'type\s*=\s*["\'](submit|button|reset|image)["\']', attrs, re.IGNORECASE):
            continue

        # Check for aria-label or aria-labelledby
        if re.search(r'aria-label\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE):
            continue
        if re.search(r'aria-labelledby\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE):
            continue

        # Check for a matching <label for="id">
        id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attrs)
        if id_match and id_match.group(1) in label_fors:
            continue

        violations.append(WcagViolation(
            rule_id="label",
            severity=Severity.CRITICAL.value,
            description="Form input is missing an associated label",
            html_element=_truncate(input_match.group(0)),
            help_url="https://dequeuniversity.com/rules/axe/4.7/label",
        ))
    return violations


def _check_empty_links_buttons(html_content: str) -> list[WcagViolation]:
    """WCAG 4.1.2 / 2.4.4 — Links and buttons must not be empty."""
    violations: list[WcagViolation] = []

    # Check <a> tags
    for match in re.finditer(
        r"<a\b([^>]*)>(.*?)</a>", html_content, re.IGNORECASE | re.DOTALL
    ):
        attrs = match.group(1)
        content = match.group(2).strip()

        # aria-label counts as accessible name
        if re.search(r'aria-label\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE):
            continue
        # Content with text or img with alt is fine
        if _has_text_content(content):
            continue

        violations.append(WcagViolation(
            rule_id="link-name",
            severity=Severity.SERIOUS.value,
            description="Link has no accessible name (empty content and no aria-label)",
            html_element=_truncate(match.group(0)),
            help_url="https://dequeuniversity.com/rules/axe/4.7/link-name",
        ))

    # Check <button> tags
    for match in re.finditer(
        r"<button\b([^>]*)>(.*?)</button>", html_content, re.IGNORECASE | re.DOTALL
    ):
        attrs = match.group(1)
        content = match.group(2).strip()

        if re.search(r'aria-label\s*=\s*["\'][^"\']+["\']', attrs, re.IGNORECASE):
            continue
        if _has_text_content(content):
            continue

        violations.append(WcagViolation(
            rule_id="button-name",
            severity=Severity.SERIOUS.value,
            description="Button has no accessible name (empty content and no aria-label)",
            html_element=_truncate(match.group(0)),
            help_url="https://dequeuniversity.com/rules/axe/4.7/button-name",
        ))

    return violations


# ---------------------------------------------------------------------------
# Color-contrast helpers
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})")
_RGB_RE = re.compile(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)")
_RGBA_RE = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)")

# Named CSS colours frequently used in government documents
_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "silver": (192, 192, 192),
    "navy": (0, 0, 128),
    "maroon": (128, 0, 0),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
    "teal": (0, 128, 128),
}


def _parse_css_color(
    style: str,
    prop: str,
) -> tuple[int, int, int] | None:
    """Extract an RGB tuple for a CSS property from a style string."""
    # Match property: value, handling the special case of "color" not matching
    # "background-color" by using word boundary
    pattern = rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)"
    match = re.search(pattern, style, re.IGNORECASE)
    if match is None:
        return None

    value = match.group(1).strip().lower()

    # Named colour
    if value in _NAMED_COLORS:
        return _NAMED_COLORS[value]

    # #hex
    hex_m = _HEX_RE.search(value)
    if hex_m:
        h = hex_m.group(1)
        if len(h) == 3:
            return (int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16))
        if len(h) >= 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    # rgb(r, g, b)
    rgb_m = _RGB_RE.search(value)
    if rgb_m:
        return (int(rgb_m.group(1)), int(rgb_m.group(2)), int(rgb_m.group(3)))

    # rgba(r, g, b, a) — ignore alpha
    rgba_m = _RGBA_RE.search(value)
    if rgba_m:
        return (int(rgba_m.group(1)), int(rgba_m.group(2)), int(rgba_m.group(3)))

    return None


def _relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG 2.x relative luminance calculation."""
    def _linearize(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def _contrast_ratio(
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
) -> float:
    """Calculate WCAG contrast ratio between two RGB colours."""
    l1 = _relative_luminance(*fg)
    l2 = _relative_luminance(*bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 200) -> str:
    """Truncate a string for inclusion in violation reports."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _has_text_content(html_fragment: str) -> bool:
    """Return True if the fragment contains visible text or an img with alt."""
    # Strip HTML tags and check for remaining text
    text_only = re.sub(r"<[^>]+>", " ", html_fragment).strip()
    if text_only:
        return True
    # Check for img with non-empty alt inside the fragment
    if re.search(r'<img\b[^>]*\balt\s*=\s*["\'][^"\']+["\']', html_fragment, re.IGNORECASE):
        return True
    return False
