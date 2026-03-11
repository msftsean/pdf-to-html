# Wonder-Woman Decision: US1+US2 Backend Implementation

**Date:** 2025-07-24
**Author:** Wonder-Woman (Backend Developer)
**Scope:** html_builder.py, ocr_service.py, function_app.py

## Decisions Made

### 1. Heading Hierarchy Enforcement Strategy
**Decision:** Flatten skipped heading levels down to `prev_level + 1` rather than inserting hidden intermediate headings.
**Rationale:** Inserting invisible h2s between h1 and h3 would be confusing for screen readers. Flattening preserves the content hierarchy without adding phantom elements. The WCAG validator confirms zero heading-order violations.

### 2. OCR Confidence Threshold at 0.70
**Decision:** Pages with average OCR confidence < 70% are flagged with `needs_review=True` and get a visible banner.
**Rationale:** 70% balances false positives (alerting on readable text) vs. false negatives (missing errors). This matches Azure Document Intelligence's own quality tiers. The threshold is a module-level constant (`_CONFIDENCE_THRESHOLD`) for easy tuning.

### 3. Graceful OCR Failure Returns Stub Results
**Decision:** When OCR fails for a page or entirely, return `OcrPageResult(confidence=0.0, needs_review=True)` with empty lines/tables instead of raising.
**Rationale:** The conversion pipeline must not crash on OCR failure — digital content on other pages is still valuable. The html_builder renders a "Content Unavailable" notice so users know what happened.

### 4. Color Contrast Fixes
**Decision:** Changed figcaption from `#666` (3.95:1) to `#595959` (7.0:1), table borders from `#ccc` to `#767676`, page borders from `#e0e0e0` to `#595959`.
**Rationale:** WCAG AA requires 4.5:1 for normal text and 3:1 for non-text UI. The old values failed. New values were verified against white (#fff) background using the WCAG relative luminance formula.

### 5. Review Banner Uses `role="alert"`
**Decision:** Low-confidence OCR banners use `role="alert"` so screen readers announce them immediately.
**Rationale:** WCAG 4.1.3 — status messages must be programmatically determinable. Users relying on assistive tech need to know when a page may have OCR errors without having to discover the banner visually.

## Impact on Other Agents
- **Flash (Frontend):** The status API now returns `review_pages` (1-based page numbers) and `has_review_flags`. The frontend should display these in the document status UI.
- **Cyborg (DevOps):** No infra changes needed. All state still lives in blob metadata.
- **Aquaman (QA):** 17 new integration tests in `tests/integration/test_html_wcag_compliance.py` cover all WCAG changes. Run with `pytest tests/integration/`.
