# Aquaman — History

## Session Log

- **2026-03-11:** Joined the squad as QA & Testing.
- **2026-03-11:** Completed T020, T021, T022 — wrote 34 unit tests across 3 files:
  - `tests/unit/test_models.py` (12 tests) — Document, ConversionResult, WcagViolation, CellData
  - `tests/unit/test_status_service.py` (10 tests) — set_status, get_status, list_documents, get_summary, state transitions
  - `tests/unit/test_wcag_validator.py` (12 tests) — lang attr, img alt, table headers, heading order, empty links, multi-violation, severity
  - `tests/conftest.py` — shared fixtures (sample_document_kwargs, sample_wcag_violation_kwargs, valid_html, blob service mocks)
  - All 34 tests passing ✅

- **2026-03-11:** Completed Phase 11 — Evaluation Suite (T080, T081, T082, T085):
  - **T080:** Created 4 sample PDFs via fpdf2: `simple-memo.pdf` (1.7KB), `digital-report.pdf` (4.8KB, 5 pages), `complex-tables.pdf` (3.1KB, 3 tables), `image-heavy.pdf` (4.1KB, 4 embedded images)
  - **T081:** Built `scripts/run_evals.py` — full pipeline harness: extract_pdf → build_html → validate_html, with JSON report + pretty-printed summary table
  - **T082:** Built `scripts/eval_metrics.py` — scoring functions: heading_hierarchy_score, table_accessibility_score, image_alt_coverage, overall_compliance_score
  - **T085:** Ran full eval suite — **4/4 documents PASS**, 0 critical, 0 serious, 2 moderate (heading-order from font-size thresholds). All tables score 100%, all images score 100%.
  - Outputs: `tests/eval/results/eval-report.json`, `tests/eval/results/html/` (4 converted HTML files)

## Learnings

- **Severity enum:** The WCAG violation severity enum is named `Severity` (not `ViolationSeverity`) in `models.py`. Import as `from models import Severity`.
- **String-valued fields:** `Document.status`, `Document.format`, and `WcagViolation.severity` store **string values** (e.g. `"pending"`, `"pdf"`, `"critical"`), not enum instances. Compare with `DocumentStatus.PENDING.value`, not `DocumentStatus.PENDING`.
- **DocumentStatus enum oddity:** `DocumentStatus._transitions` is treated as an enum member (Python str+Enum quirk). When iterating `DocumentStatus`, filter with `isinstance(s.value, str)` to get only the four lifecycle states.
- **status_service blob scanning:** `_find_blob_by_id()` scans blobs via `container_client.list_blobs(name_starts_with=doc_id)` looking for `metadata["document_id"] == doc_id`. Mocks must provide blob items with `.name` and `.metadata` dict containing `document_id`.
- **list_documents filtering:** `list_documents()` only includes blobs that have a `"status"` key in their metadata — blobs without it are silently skipped.
- **wcag_validator rule_ids:** The actual rule IDs used are: `html-has-lang`, `image-alt`, `table-has-header`, `th-has-scope`, `heading-order`, `color-contrast`, `label`, `link-name`, `button-name`.
- **Pipeline API:** `extract_pdf(bytes)` → `(pages, metadata)`; `build_html(pages, ocr_results={}, metadata)` → `(html_string, image_files)`; `validate_html(html)` → `list[WcagViolation]`. For digital PDFs, `ocr_results` can be an empty dict.
- **Heading detection thresholds:** `_heading_level()` in html_builder uses 24pt→h1, 18pt→h2, 14pt+bold→h3, 12pt+bold→h4. When PDFs use 16pt bold for sub-headers, they get classified as h3 instead of h2, causing moderate heading-order violations. This is expected pipeline behavior, not a test bug.
- **fpdf2 font limitations:** Standard Helvetica font in fpdf2 doesn't support Unicode bullets (•). Use ASCII dashes (-) or add a Unicode-capable font for bullet lists in test PDFs.
- **Eval suite command:** Run `python scripts/run_evals.py` from project root. Generates samples if none exist, outputs JSON to `tests/eval/results/eval-report.json`.
