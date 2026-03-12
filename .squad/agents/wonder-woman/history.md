# Wonder-Woman — History

## Session Log

- **2026-03-11:** Joined the squad as Backend Developer.
- **Phase 2 Backend Sprint:** Completed T008–T010, T017–T019.
- **2026-03-12:** Completed Phase 10 US5 (PPTX Support).
- **2026-03-12:** Completed Phase 13 Backend Hardening (T071–T074).

## Learnings

- **Blob metadata as state store:** Azure Blob metadata (string key-value pairs) works well for tracking document status without a database. All values must be strings — serialize ints, bools, and lists explicitly. Reconstruction via `Document.from_metadata()` handles the parsing.
- **WCAG validation in Python is feasible for common rules:** A regex-based HTML parser catches 80%+ of server-side accessibility issues (missing alt, heading order, table headers, color contrast, form labels, empty links). Full axe-core validation still runs client-side.
- **SAS token flow:** The upload API creates an empty placeholder blob with metadata *before* the browser uploads. This ensures the status service can track the document immediately. The browser then overwrites the blob content via the SAS URL, which triggers the existing blob trigger.
- **Re-export pattern for models:** `models.py` imports and re-exports `TextSpan`, `ImageInfo`, `TableData`, `PageResult` from `pdf_extractor.py` so consumers can import from a single module. Avoids duplication while centralizing the data model.
- **Connection string key extraction:** Azure Storage connection strings use semicolon-delimited `Key=Value` pairs. `_extract_account_key()` parses `AccountKey=...` for SAS token generation. This avoids importing additional Azure Identity libraries for local dev.
- **Heading hierarchy enforcement:** PDF headings can skip levels (e.g. h1→h3) because PDFs don't enforce heading semantics. The `_enforce_heading_hierarchy()` function in html_builder.py flattens skipped levels down to prev+1 to pass WCAG 1.3.1. This runs after span-to-block conversion.
- **WCAG contrast thresholds for inline CSS:** figcaption color was #666 (3.95:1 on white — fails AA). Changed to #595959 (7.0:1). Table borders were #ccc — changed to #767676 (4.54:1). Always test contrast ratios against background explicitly.
- **OCR confidence scoring architecture:** OcrPageResult now carries `confidence` (float, 0.0–1.0) and `needs_review` (bool). Confidence is computed from Document Intelligence word-level scores averaged across the page. Pages below 0.70 threshold get review banners in the HTML and are tracked in blob metadata.
- **Graceful OCR failure pattern:** ocr_service.py now wraps both full-call and per-page processing in try/except. On failure, a stub OcrPageResult with confidence=0.0 and needs_review=True is returned so the pipeline continues without crashing. The html_builder renders a "Content Unavailable" notice for empty OCR results.
- **Blob trigger status lifecycle:** The blob trigger now follows a strict status flow: pending→processing→completed/failed. It times the entire conversion (time.monotonic), runs wcag_validator on the output HTML, collects OCR review_pages, and writes all metadata back via status_service.set_status(). On exception, it sets status to "failed" with the error context.
- **Password-protected document detection (T071):** PyMuPDF's `is_encrypted` property reliably detects encrypted PDFs. For DOCX/PPTX, python-docx and python-pptx raise exceptions containing "password", "encrypt", or "protected" when opening encrypted files. Early detection at the blob trigger stage sets status to "failed" with a clear user-facing error message before wasting processing cycles.
- **Multi-language lang attribute (T072):** Simple heuristic-based language detection using character frequency (ñ, ã, õ, ß, etc.) and common function words detects Spanish, French, German, Italian, and Portuguese with reasonable accuracy. Each `<section>` gets a `lang` attribute if it differs from the document default. Checking order matters: Portuguese (ãõ) first, then French (àâæèêë), then Spanish (ñ). Falls back to document default for ambiguous/English content.
- **Exponential backoff retry for blob operations (T073):** Wrapping Azure Blob operations in `_retry_blob_operation()` with exponential backoff (1s, 2s, 4s) + random jitter (0–50%) handles transient `ServiceResponseError`, `ServiceRequestError`, and `HttpResponseError` gracefully. Each retry is logged with attempt number. Non-transient exceptions (ValueError, TypeError) are not retried — fail fast on programmer errors.
- **Filename conflict handling via UUID document_id (T074):** Using UUID-based blob names (`{document_id}.pdf`) for storage eliminates filename collisions entirely. The original filename is preserved in blob metadata (`original_filename` field) for display purposes. No timestamp suffixes or conflict resolution needed — UUIDs guarantee uniqueness across concurrent uploads.

### Phase 10 — US5: PPTX Support (Session 3)

**Tasks Completed:** T085, T086, T087, T088

1. **pptx_extractor.py (T085)** — Built slide extraction module (310 lines) with full support for:
   - Text extraction from slide shapes with formatting preserved
   - Table extraction via python-pptx; tables are converted to intermediate markdown format for reuse
   - Image extraction with embedded PNG conversion; alt text sourced from slide notes
   - Graceful handling of missing/empty shapes (no crashes on edge cases)
   - Returns `PageResult[]` compatible with existing html_builder pipeline

2. **html_builder.py PPTX support (T086)** — Extended HTML builder to handle PPTX:
   - Each slide becomes an `<section>` with slide number + title in `<h2>`
   - Tables are converted to WCAG-compliant `<table>` markup via existing `_convert_markdown_table_to_html()` function (avoids duplication)
   - Images are embedded as `<img>` tags with alt text from slide notes
   - Heading hierarchy is validated (same 7 WCAG rules apply to PPTX output)
   - No changes to PDF/DOCX pipeline (full backward compatibility)

3. **function_app.py PPTX routing (T087)** — Added PPTX dispatch:
   - `POST /api/convert` now detects `application/vnd.openxmlformats-officedocument.presentationml.presentation` content type
   - Routes to `pptx_extractor.extract_pptx(blob_stream)` via the existing dispatcher pattern
   - No new endpoints; transparent to frontend

4. **Unit + Integration tests (T088)** — Full test coverage (40 tests):
   - 22 unit tests for pptx_extractor: text extraction, table parsing, image handling, graceful failures
   - 18 integration tests for PPTX conversion: end-to-end flow, WCAG validation, metadata tracking
   - All tests pass; no regressions to PDF/DOCX

5. **Key architectural insight:** PPTX extraction returns `PageResult[]` (same type as PDF/DOCX), allowing full reuse of html_builder, wcag_validator, and status tracking. The conversion pipeline treats all three formats uniformly — only the extractor changes per format.

6. **Build verified** — `pytest tests/` passes all 40 new tests plus existing suite. No breaking changes to backend API.

### Local Dev Environment Setup (Session 4)

1. **Azurite requires `--skipApiVersionCheck`:** The azure-storage-blob SDK (v12.x) sends API version 2026-02-06, which Azurite's npm release doesn't support yet. Must start Azurite with `--skipApiVersionCheck` flag to avoid `InvalidHeaderValue` errors.
2. **Azurite ports:** Blob on 10000, Queue on 10001, Table on 10002. All on 127.0.0.1 by default.
3. **Blob containers needed:** `files` (input) and `converted` (output) must be created manually in Azurite before the function app will work. Use the Python SDK with the well-known Azurite connection string.
4. **local.settings.json:** Not committed to git (`.gitignore`). Must be created manually with `AzureWebJobsStorage=UseDevelopmentStorage=true`, `FUNCTIONS_WORKER_RUNTIME=python`, and `OUTPUT_CONTAINER=converted`. CORS set to `*` for local dev.
5. **Function app endpoints (local):**
   - `POST http://localhost:7071/api/upload/sas-token` — Generate SAS upload URL
   - `GET http://localhost:7071/api/documents/status` — List all document statuses
   - `GET http://localhost:7071/api/documents/{document_id}/download` — Download URL
   - `blobTrigger` on `files` container — Automatic conversion on upload
6. **Azure Functions Core Tools v4.8.0** works with Python 3.12. `func start` from project root.
7. **All 171 tests pass** with `pytest tests/ -x -q` in ~3 seconds.

### API Route Mismatch Fix (Session 5)

1. **Fixed 4 frontend→backend route mismatches** that caused ERR_CONNECTION_REFUSED (actually 404s):
   - `uploadService.ts`: `POST /api/upload` → `POST /api/upload/sas-token`
   - `uploadService.ts`: Request body field `file_size` → `size_bytes` (matching backend's `body.get("size_bytes")`)
   - `statusService.ts`: `GET /api/status` → `GET /api/documents/status`
   - `statusService.ts`: `GET /api/status/{id}` → `GET /api/documents/status?document_id={id}` (backend uses query param, not path param)
2. `downloadService.ts` was already correct (`GET /api/documents/{id}/download`).
3. **Root cause:** Frontend was built against the route spec in Decision 1 (`/api/upload`, `/api/status`), but backend implemented RESTful routes under `/api/documents/` and `/api/upload/sas-token`. The two teams never synced route names.
4. **Verified:** curl confirmed correct routes return 200, old routes return 404. All 171 backend tests pass.

- **Frontend-backend route contracts must be verified early:** The original decisions doc (Decision 1) listed simplified route names (`/api/upload`, `/api/status`) but the backend implemented more RESTful names. Always verify actual route strings match between frontend and backend before integration testing.

