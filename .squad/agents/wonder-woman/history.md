# Wonder-Woman — History

## Session Log

- **2026-03-11:** Joined the squad as Backend Developer.
- **Phase 2 Backend Sprint:** Completed T008–T010, T017–T019.
- **2026-03-12:** Completed Phase 10 US5 (PPTX Support).
- **2026-03-12:** Completed Phase 13 Backend Hardening (T071–T074).

## Learnings

- **Blob metadata as state store:** Azure Blob metadata (string key-value pairs) works well for tracking document status without a database. All values must be strings — serialize ints, bools, and lists explicitly. Reconstruction via `Document.from_metadata()` handles the parsing.
- **SAS PUT overwrites ALL blob metadata:** When a browser uploads via SAS URL (HTTP PUT), Azure Blob Storage replaces the entire blob — including metadata. The placeholder blob created by `generate_sas_token()` loses its `document_id`, `status`, and all tracking fields. Fix: (1) return metadata in the SAS response so the frontend can set `x-ms-meta-*` headers on the PUT, and (2) add a safety net in the blob trigger that detects missing metadata and reconstructs it from the blob name. (3) `_find_blob_by_id()` must fall back to name-prefix matching when metadata is absent.
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

### Azurite SAS URL + Blob Trigger Bugfixes (Session 6)

**Bugs Fixed:** 3 bugs causing "Conversion failed after 18ms" on file upload.

1. **SAS upload URL wrong for Azurite (BUG 1):** `generate_sas_token` hardcoded `https://{account}.blob.core.windows.net/...` for the upload URL. Azurite listens at `http://127.0.0.1:10000/devstoreaccount1/...`. Added `_is_azurite()` helper that checks connection string for `UseDevelopmentStorage=true` or `127.0.0.1:10000`, and branches URL generation accordingly.

2. **Blob trigger fires on 0-byte placeholder (BUG 2):** The SAS token endpoint creates a 0-byte placeholder blob with metadata so status tracking works immediately. But the blob trigger fires on this empty blob, crashing because there's no file data. Added a guard at the top of `file_upload()` that returns early when `myblob.length == 0`.

3. **`_extract_account_key` fails on Azurite shorthand (BUG 3):** `UseDevelopmentStorage=true` has no `AccountKey=` segment. The function now returns the well-known Azurite account key (`Eby8vdM02x...`) when it detects an Azurite connection string.

4. **Also fixed `_generate_download_sas_url`** — same Azurite URL pattern issue applied to download SAS URLs.

- **Azurite URL format differs from Azure:** Azure Blob uses `https://{account}.blob.core.windows.net/{container}/{blob}`. Azurite uses `http://127.0.0.1:10000/{account}/{container}/{blob}`. Always branch URL construction with `_is_azurite()` when generating SAS URLs.
- **Well-known Azurite credentials:** Account name is `devstoreaccount1`, account key is `Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==`. These are public constants, not secrets.
- **0-byte blob guard pattern:** When using placeholder blobs for early status tracking, the blob trigger MUST skip them. Check `myblob.length == 0` before processing.

- **Blob deletion output prefix derivation:** Output blobs are stored under `{document_id}/` in the converted container (HTML at `{document_id}/{document_id}.html`, images at `{document_id}/images/`). The `output_path` metadata field provides the canonical path; parse it to get the prefix, or fall back to `document_id + "/"` for documents that were never processed.
- **Processing-state guard for deletion:** The DELETE endpoint checks document status via `get_status()` before calling `delete_document()`. Documents with status `"processing"` are refused (HTTP 409) to prevent data corruption mid-conversion. This is a pre-check — the actual deletion is wrapped in `_retry_blob_operation` for transient failures.
- **Idempotent bulk deletion:** `delete_all_documents()` iterates and deletes blobs one by one, counting deletions per container. Each container's iteration is wrapped in try/except so a failure in one container doesn't block the other.

### Download Endpoint → Frontend Contract Fix (Session 7)

**Bug:** Preview button caused a 500 error. Frontend (`downloadService.ts`) destructures `{ download_url, filename, image_urls }` from the download endpoint response. Backend returned `{ html_url, name, assets }` — different field names. `download_url` resolved to `undefined`, iframe loaded `/undefined`, Next.js 500'd.

**Fix:** Added three alias fields to the download endpoint response in `function_app.py` (line ~715):
- `"download_url": html_url` — alias for `html_url`
- `"filename": doc.name` — alias for `name`
- `"image_urls": [url, ...]` — flat URL list extracted from `assets` objects

All existing fields kept for backward compatibility. 174 tests pass, no regressions.

- **Frontend-backend response field contracts:** Always verify that the field names the frontend destructures from API responses match exactly what the backend returns. Type interfaces in TS (`DownloadUrlResponse`) should mirror backend JSON keys 1:1. Alias fields (returning the same value under two names) are a safe backward-compatible fix when the mismatch is discovered late.

### Container Apps Migration — Phase 1 + Phase 2 (2026-07-15)

Implemented the foundational FastAPI + Azure Container Apps migration:

**Phase 1 — Core plumbing:**
- `app/__init__.py` — Package init
- `app/config.py` — Pydantic Settings centralising all env vars via `settings` singleton. Supports both new `AZURE_STORAGE_CONNECTION_STRING` and legacy `AzureWebJobsStorage` names.
- `app/models.py` — 11 Pydantic request/response models matching exact JSON shapes from `function_app.py` for full backwards-compatibility with the frontend.
- `app/dependencies.py` — Migrated all shared helpers from function_app.py (blob client, queue client, SAS generation, retry, Azurite detection). All `os.environ.get()` calls replaced with `settings.*`.
- `requirements.txt` — Removed `azure-functions`, added `fastapi`, `uvicorn[standard]`, `azure-storage-queue`, `pydantic-settings`, `httpx`.

**Phase 2 — Application shell:**
- `app/main.py` — FastAPI app with CORS, startup container/queue init, `/health` and `/ready` probes.
- `Dockerfile.backend` — Multi-stage Python 3.12-slim build.
- `.dockerignore` — Excludes tests, docs, frontend, specs from Docker context.
- `.env.example` — Updated with all new env vars, points frontend at port 8000 instead of 7071.

**Verification:** All 174 existing tests pass. FastAPI app imports and loads cleanly. All Pydantic models validate. Dependency helpers pass basic sanity checks.

### Identity-Based Auth + Conversion Pipeline Fix (Session 9)

**Root Cause:** After Cyborg deployed to Azure with identity-based storage auth (`AzureWebJobsStorage__accountName`), all blob operations in `function_app.py` crashed. `_get_blob_service_client()` hardcoded `os.environ["AzureWebJobsStorage"]` which throws `KeyError` when only the `__accountName` variant is set. SAS token generation also relied on `_extract_account_key()` parsing an account key from a connection string that no longer exists.

**Bugs Fixed:**

1. **`_get_blob_service_client()` only supported connection strings (BUG 1):** Added dual-mode detection — tries connection string first (`AzureWebJobsStorage` with `AccountKey=` or `UseDevelopmentStorage=true`), falls back to identity-based auth (`AzureWebJobsStorage__accountName` + `DefaultAzureCredential`). Local/Azurite path unchanged.

2. **SAS token generation fails without account key (BUG 2):** Created `_generate_sas_token_str()` that uses account key when available (local) or requests a `UserDelegationKey` from the blob service for identity-based auth (Azure). Updated both upload SAS and download SAS paths.

3. **0-byte placeholder guard missed when `myblob.length` is None (BUG 3):** Azurite can set `myblob.length = None` for certain blobs. The old guard `myblob.length is not None and myblob.length == 0` didn't catch these. Now reads the blob data early and checks `len(file_data) == 0` as a definitive fallback.

4. **Metadata safety net too narrow (BUG 4):** Only checked for `document_id` and `status` in metadata, but `name` was also missing after SAS PUT overwrites. Without `name`, the download endpoint constructed path `/.html` instead of `{uuid}/{uuid}.html` → BlobNotFound. Now also checks for `name` and reconstructs from `original_filename` or `document_id`.

5. **RBAC script missing Storage Blob Delegator role:** Added `Storage Blob Delegator` to `scripts/assign-storage-rbac.sh` — required for `UserDelegationKey`-based SAS generation with managed identity.

- **Identity-based auth dual-mode pattern:** `_get_blob_service_client()` checks `AzureWebJobsStorage` for a connection string first, then falls back to `AzureWebJobsStorage__accountName` + `DefaultAzureCredential`. This supports local Azurite, connection-string deployments, and identity-based Azure deployments from a single code path.
- **UserDelegationKey for SAS tokens with managed identity:** When no account key is available, `generate_blob_sas()` accepts a `user_delegation_key` parameter obtained from `blob_service.get_user_delegation_key()`. Requires `Storage Blob Delegator` RBAC role.
- **0-byte guard must read the stream:** `myblob.length` is unreliable with Azurite (can be `None`). Always read `file_data = myblob.read()` early and check `len(file_data) == 0` for a definitive guard.
- **Metadata safety net must check all essential fields:** Checking only `document_id` and `status` is insufficient — also check `name` since it's required for output path construction. The SAS PUT from browsers will overwrite all metadata; any field the browser doesn't send is lost.



### Container Apps Migration — Phase 3 + Phase 4 (API Endpoints & Queue Worker)

**Tasks Completed:** T010–T021

**Phase 3 — API Endpoints (T010–T016):**

1. **POST /api/upload/sas-token (T010):** Migrated SAS token generation endpoint from function_app.py to FastAPI. Validates extension (.pdf/.docx/.pptx), content type, size (≤100MB). Creates UUID document_id, 0-byte placeholder blob with metadata, generates SAS upload URL. Added T021 local dev queue simulation — when running on Azurite, auto-enqueues a base64-encoded Event Grid message to `conversion-jobs` queue so the worker picks up the upload.

2. **GET /api/documents/status (T011):** Migrated status query. Accepts optional `document_id` query param. Single doc returns 404 if not found. List mode returns all documents with batch summary via `status_service`.

3. **GET /api/documents/{document_id}/download (T012):** Migrated download URL generation. Checks document exists (404), checks status completed (409 for processing/pending, 404 for failed). Generates SAS download URLs for HTML + images in `converted/{doc_id}/`. Returns full response shape with frontend-compatible aliases (`download_url`, `filename`, `image_urls`).

4. **DELETE /api/documents/{document_id} (T013):** Migrated single deletion. Guards against deleting processing documents (409). Uses retry_blob_operation for transient failures.

5. **DELETE /api/documents (T014):** Migrated bulk deletion. Deletes all documents from input and output containers.

6. **Password protection helpers (T015):** Created `app/security.py` with `is_password_protected_pdf()`, `is_password_protected_docx()`, `is_password_protected_pptx()`, and convenience `check_password_protection()` dispatcher.

7. **Test config (T016):** Added FastAPI `TestClient` fixture to `tests/conftest.py`.

**Phase 4 — Queue Worker (T018–T021):**

8. **app/worker.py (T018):** Created queue-based conversion worker as `ConversionWorker` class. Main poll loop receives messages from `conversion-jobs` queue every 2 seconds. For each message: parses Event Grid envelope, extracts blob_name from `subject` field, waits for non-zero content (up to 30s), downloads blob, runs full conversion pipeline (detect format → extract → OCR → build HTML → WCAG validate → upload to converted/), sets status to completed/failed with metadata. Graceful shutdown on SIGTERM/SIGINT.

9. **Poison queue handling (T019):** Messages with `dequeue_count >= 3` are logged and deleted to prevent infinite retries.

10. **Password detection in worker (T020):** Before conversion, checks password protection using `app.security.check_password_protection()`. Rejects encrypted files with clear error message.

11. **Local queue simulation (T021):** Handled in T010 — the SAS token endpoint enqueues a simulated Event Grid message when running on Azurite.

12. **Public dependency aliases:** Added public names (`generate_sas_token_str`, `generate_download_sas_url`, `retry_blob_operation`, `is_local_storage`, `is_azurite`, `extract_account_key`) to `app/dependencies.py` for clean imports.

**Verification:** All 174 existing tests pass. All 11 FastAPI routes registered. Worker, security, and dependency modules import cleanly.

- **Queue message format for local dev:** Messages are base64-encoded JSON with Event Grid envelope shape: `{"subject": "/blobServices/default/containers/files/blobs/<name>", "data": {"contentType": "...", "contentLength": N}}`. The worker parses `subject` to extract blob_name by splitting on `/blobs/`.
- **Worker content polling pattern:** The SAS upload creates a 0-byte placeholder, but the browser's PUT via SAS URL overwrites it with real content. The worker must poll for non-zero content (up to 30s) before starting conversion, since the queue message may arrive before the upload completes.
- **Poison queue threshold:** After 3 failed dequeue attempts (`dequeue_count >= 3`), the message is deleted and logged as poison. This prevents infinite retry loops for permanently broken documents.
