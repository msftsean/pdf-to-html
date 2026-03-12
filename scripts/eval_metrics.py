#!/usr/bin/env python3
"""
Evaluation metrics for WCAG compliance scoring.
Provides granular scoring functions for heading hierarchy, table accessibility,
image alt text coverage, and overall compliance assessment.
"""

from __future__ import annotations

import re
from typing import Any


def count_violations_by_severity(violations: list[dict[str, Any]]) -> dict[str, int]:
    """Count WCAG violations grouped by severity level.

    Args:
        violations: List of violation dicts with 'severity' key.

    Returns:
        Dict mapping severity → count. Always includes all four levels.
    """
    counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    for v in violations:
        sev = v.get("severity", "moderate").lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["moderate"] += 1  # unknown severity → moderate
    return counts


def heading_hierarchy_score(html_content: str) -> float:
    """Score heading hierarchy for WCAG compliance (0–100).

    Checks:
    - No heading levels are skipped (h1→h3 without h2)
    - Document starts with h1

    Returns:
        Float 0–100. 100 = perfect hierarchy.
    """
    headings = re.findall(r"<(h[1-6])\b[^>]*>", html_content, re.IGNORECASE)
    if not headings:
        return 100.0  # No headings = nothing to violate

    levels = [int(h[1]) for h in headings]
    total_checks = len(levels)
    penalties = 0

    # Penalty if document doesn't start with h1
    if levels[0] != 1:
        penalties += 1

    # Penalty for each skipped level
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            penalties += 1

    if total_checks == 0:
        return 100.0
    score = max(0.0, (1.0 - penalties / total_checks) * 100.0)
    return round(score, 1)


def table_accessibility_score(html_content: str) -> float:
    """Score table accessibility for WCAG compliance (0–100).

    Checks for each table:
    - Has <th> header cells
    - <th> cells have scope attribute
    - Has <thead> wrapper

    Returns:
        Float 0–100. 100 = all tables fully accessible.
    """
    tables = re.findall(
        r"<table\b[^>]*>(.*?)</table>",
        html_content,
        re.IGNORECASE | re.DOTALL,
    )

    if not tables:
        return 100.0  # No tables = nothing to violate

    total_score = 0.0
    for table_body in tables:
        table_points = 0.0
        max_points = 3.0  # has_th, has_scope, has_thead

        # Check for <th>
        th_matches = re.findall(r"<th\b([^>]*)>", table_body, re.IGNORECASE)
        if th_matches:
            table_points += 1.0

            # Check scope on <th> elements
            with_scope = sum(
                1 for attrs in th_matches
                if re.search(r'scope\s*=', attrs, re.IGNORECASE)
            )
            if th_matches and with_scope == len(th_matches):
                table_points += 1.0
            elif th_matches:
                table_points += (with_scope / len(th_matches))

        # Check for <thead>
        if re.search(r"<thead\b", table_body, re.IGNORECASE):
            table_points += 1.0

        total_score += (table_points / max_points) * 100.0

    return round(total_score / len(tables), 1)


def image_alt_coverage(html_content: str) -> float:
    """Calculate percentage of images with non-empty alt text (0–100).

    Images with role="presentation" or aria-hidden="true" are excluded
    (decorative images don't need alt text).

    Returns:
        Float 0–100. 100 = all non-decorative images have alt text.
    """
    img_tags = re.findall(r"<img\b([^>]*)>", html_content, re.IGNORECASE)
    if not img_tags:
        return 100.0  # No images = nothing to violate

    total = 0
    with_alt = 0

    for attrs in img_tags:
        # Skip decorative images
        if re.search(r'role\s*=\s*["\']presentation["\']', attrs, re.IGNORECASE):
            continue
        if re.search(r'aria-hidden\s*=\s*["\']true["\']', attrs, re.IGNORECASE):
            continue

        total += 1
        alt_match = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', attrs)
        if alt_match and alt_match.group(1).strip():
            with_alt += 1

    if total == 0:
        return 100.0
    return round((with_alt / total) * 100.0, 1)


def overall_compliance_score(violations: list[dict[str, Any]]) -> str:
    """Determine overall compliance status based on violation severities.

    Rules:
    - FAIL: Any critical violations
    - WARN: Any serious violations (but no critical)
    - PASS: Only moderate/minor violations or none

    Returns:
        'PASS', 'WARN', or 'FAIL'
    """
    counts = count_violations_by_severity(violations)

    if counts["critical"] > 0:
        return "FAIL"
    if counts["serious"] > 0:
        return "WARN"
    return "PASS"
