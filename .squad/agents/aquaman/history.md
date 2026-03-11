# Aquaman — History

## Session Log

- **2026-03-11:** Joined the squad as QA & Testing.
- **2026-03-11:** Completed T020, T021, T022 — wrote 34 unit tests across 3 files:
  - `tests/unit/test_models.py` (12 tests) — Document, ConversionResult, WcagViolation, CellData
  - `tests/unit/test_status_service.py` (10 tests) — set_status, get_status, list_documents, get_summary, state transitions
  - `tests/unit/test_wcag_validator.py` (12 tests) — lang attr, img alt, table headers, heading order, empty links, multi-violation, severity
  - `tests/conftest.py` — shared fixtures (sample_document_kwargs, sample_wcag_violation_kwargs, valid_html, blob service mocks)
  - All 34 tests passing ✅

## Learnings

- **Severity enum:** The WCAG violation severity enum is named `Severity` (not `ViolationSeverity`) in `models.py`. Import as `from models import Severity`.
- **String-valued fields:** `Document.status`, `Document.format`, and `WcagViolation.severity` store **string values** (e.g. `"pending"`, `"pdf"`, `"critical"`), not enum instances. Compare with `DocumentStatus.PENDING.value`, not `DocumentStatus.PENDING`.
- **DocumentStatus enum oddity:** `DocumentStatus._transitions` is treated as an enum member (Python str+Enum quirk). When iterating `DocumentStatus`, filter with `isinstance(s.value, str)` to get only the four lifecycle states.
- **status_service blob scanning:** `_find_blob_by_id()` scans blobs via `container_client.list_blobs(name_starts_with=doc_id)` looking for `metadata["document_id"] == doc_id`. Mocks must provide blob items with `.name` and `.metadata` dict containing `document_id`.
- **list_documents filtering:** `list_documents()` only includes blobs that have a `"status"` key in their metadata — blobs without it are silently skipped.
- **wcag_validator rule_ids:** The actual rule IDs used are: `html-has-lang`, `image-alt`, `table-has-header`, `th-has-scope`, `heading-order`, `color-contrast`, `label`, `link-name`, `button-name`.
