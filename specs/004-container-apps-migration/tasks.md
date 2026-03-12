# Tasks: Azure Container Apps Migration

**Feature**: Azure Container Apps Migration
**Branch**: `004-container-apps-migration`
**Generated**: 2026-06-15
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 39 |
| Phases | 7 (Setup → Foundational → US1–US4 → Polish) |
| Parallel opportunities | 16 tasks marked [P] |
| User stories covered | US1 (Deploy), US2 (Queue Worker), US3 (docker-compose), US4 (API Compat), US5 (WCAG — covered implicitly via unchanged pipeline) |
| MVP scope | Phase 1–2 + US4 (API parity) + US2 (worker) |

---

## Phase 1 — Setup (Project Initialization)

> **Goal**: Create project scaffolding, update dependencies, establish configuration module.
> No user story label — these are shared infrastructure.

- [ ] T001 Create `app/__init__.py` as empty package init
- [ ] T002 Create environment configuration module in `app/config.py` with Pydantic `Settings` class reading `AZURE_STORAGE_CONNECTION_STRING`, `DOCUMENT_INTELLIGENCE_ENDPOINT`, `DOCUMENT_INTELLIGENCE_KEY`, `OUTPUT_CONTAINER` (default: `converted`), `INPUT_CONTAINER` (default: `files`), `QUEUE_NAME` (default: `conversion-jobs`), `PORT` (default: `8000`), `WORKER_MODE` (default: `false`), `LOG_LEVEL` (default: `INFO`) per data-model.md environment variables table
- [ ] T003 Create Pydantic request/response models in `app/models.py`: `SasTokenRequest` (filename, content_type, size_bytes with validation), `SasTokenResponse` (document_id, upload_url, expires_at), `DocumentStatus` response model, `StatusListResponse` (documents list + summary), `DownloadResponse` (download_url, filename, expires_at, image_urls), `DeleteResponse`, `DeleteAllResponse`, `HealthResponse`, `ErrorResponse` — matching all contracts in `contracts/upload-api.md`, `contracts/status-api.md`, `contracts/download-delete-api.md`
- [ ] T004 Create dependency injection module in `app/dependencies.py`: `get_blob_service_client()` (migrated from `_get_blob_service_client()`), `get_queue_client()` (new — returns `QueueClient` for `conversion-jobs` queue), `_extract_account_key()` (migrated), `_generate_download_sas_url()` (migrated), `_retry_blob_operation()` (migrated), `_is_azurite()` (simplified — checks connection string for `devstoreaccount1`). All functions use `app/config.py` settings. Expose as FastAPI `Depends()` callables.
- [ ] T005 Update `requirements.txt`: add `fastapi`, `uvicorn[standard]`, `azure-storage-queue`, `pydantic-settings`, `httpx` (for test client); remove `azure-functions`; keep all existing dependencies (`pymupdf`, `azure-ai-documentintelligence`, `azure-identity`, `azure-storage-blob`, `python-docx`, `python-pptx`, `jinja2`, `pytest`, `pytest-cov`, `pytest-asyncio`)

---

## Phase 2 — Foundational (Blocking Prerequisites)

> **Goal**: Create the FastAPI application shell with health probes and the backend Dockerfile.
> Must complete before any user story phase. No user story label.

- [ ] T006 Create FastAPI application entry point in `app/main.py`: initialize `FastAPI(title="PDF-to-HTML WCAG Converter")`, add CORS middleware (allow all origins — matches current anonymous access), mount API router, implement `GET /health` liveness probe returning `{"status": "healthy", "version": "1.0.0", "checks": {"storage": "ok", "queue": "ok"}}` with 503 on failure, implement `GET /ready` readiness probe that verifies storage connectivity, add startup event to create blob containers (`files`, `converted`) and queue (`conversion-jobs`) if they don't exist (required for Azurite local dev). See `contracts/download-delete-api.md` health check section for response schema.
- [ ] T007 [P] Create `Dockerfile.backend` as multi-stage build: stage 1 (`builder`) installs dependencies from `requirements.txt`; stage 2 (`runtime`) uses `python:3.12-slim`, copies installed packages + `app/` + `backend/` directories, exposes port 8000, sets `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`. Target image size < 500MB. Include `--no-cache-dir` on pip install for smaller image.
- [ ] T008 [P] Create `.dockerignore` excluding `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `tests/`, `specs/`, `docs/`, `frontend/`, `*.pyc`, `.env*`, `node_modules/`, `.github/`
- [ ] T009 [P] Create `.env.example` template with all environment variables from `data-model.md` environment variables table (backend + frontend sections), with placeholder values and comments explaining each variable

---

## Phase 3 — User Story 4: All Existing API Endpoints Work (P0)

> **Goal**: Migrate all 5 HTTP endpoints from `function_app.py` to FastAPI with identical request/response contracts. Frontend requires only `BACKEND_URL` change.
> **Independent Test**: Run full test suite against FastAPI backend — all 174+ tests pass.
> **Why first**: API compatibility is the foundation — US1 (deploy) and US2 (worker) depend on a working API.

- [ ] T010 [US4] Implement `POST /api/upload/sas-token` route in `app/main.py`: migrate `generate_sas_token()` logic from `function_app.py` (lines 429–567). Accept `SasTokenRequest` Pydantic model, validate file extension (`.pdf`, `.docx`, `.pptx`), validate size (≤ 100MB), generate UUID `document_id`, create 0-byte placeholder blob with metadata (`document_id`, `name`, `format`, `size_bytes`, `status=pending`, `upload_timestamp`), generate SAS token with `rcw` permissions and 15-min expiry, return `SasTokenResponse`. Use `Depends(get_blob_service_client)` from `app/dependencies.py`. Error responses: 400 for validation, 500 for storage errors. See `contracts/upload-api.md`.
- [ ] T011 [US4] Implement `GET /api/documents/status` route in `app/main.py`: migrate `get_document_status()` from `function_app.py` (lines 569–619). Accept optional `document_id: str = Query(None)`. If `document_id` provided, return single document status (404 if not found). If omitted, list all blobs in `files/` container, read metadata, return `{"documents": [...], "summary": {"total", "pending", "processing", "completed", "failed"}}`. Use `status_service.get_document_status()` and `status_service.get_all_document_statuses()` from `backend/status_service.py`. See `contracts/status-api.md`.
- [ ] T012 [US4] Implement `GET /api/documents/{document_id}/download` route in `app/main.py`: migrate `get_download_url()` from `function_app.py` (lines 621–734). Path parameter `document_id: str`. Look up blob in `files/` container, check status is `completed` (409 if processing), find output in `converted/{document_id}/`, generate SAS download URLs (60-min expiry) for HTML file and all images, return `DownloadResponse`. See `contracts/download-delete-api.md`.
- [ ] T013 [US4] Implement `DELETE /api/documents/{document_id}` route in `app/main.py`: migrate `delete_document()` from `function_app.py` (lines 736–795). Check document exists (404), check not processing (409), delete input blob from `files/`, delete all output blobs from `converted/{document_id}/`, return `{"message": "Document deleted successfully", "document_id": "..."}`. See `contracts/download-delete-api.md`.
- [ ] T014 [US4] Implement `DELETE /api/documents` route in `app/main.py`: migrate `delete_all_documents()` from `function_app.py` (lines 796–830). List and delete all blobs in `files/` and `converted/` containers, return `{"message": "All documents deleted", "deleted_input": N, "deleted_output": M}`. See `contracts/download-delete-api.md`.
- [ ] T015 [US4] Migrate helper functions `_is_password_protected_pdf()`, `_is_password_protected_docx()`, `_is_password_protected_pptx()` from `function_app.py` (lines 104–175) into `app/dependencies.py` or keep in `app/main.py` as private helpers. These are used by the worker (US2) but are pure functions with no Azure Functions dependency.
- [ ] T016 [US4] Update test configuration in `tests/conftest.py`: add FastAPI `TestClient` fixture using `httpx` (`from fastapi.testclient import TestClient; from app.main import app`), add Azurite connection string fixture, ensure environment variables are set for test runs (`AZURE_STORAGE_CONNECTION_STRING` pointing to Azurite). Existing backend fixtures (for `backend/` package) must remain unchanged.
- [ ] T017 [US4] Verify all 174+ existing tests pass against the new FastAPI backend. Run `pytest tests/ -v` and confirm zero failures. If any test imports `function_app` directly, update the import to use `app.main` or the `TestClient` fixture. The `backend/` package tests should pass without modification since the package is unchanged.

---

## Phase 4 — User Story 2: File Upload Triggers Conversion (P0)

> **Goal**: Replace the Azure Functions blob trigger with Event Grid → Storage Queue → worker process. The conversion pipeline runs identically.
> **Independent Test**: Upload a PDF, verify conversion completes and status endpoint reports "completed".
> **Depends on**: Phase 3 (US4) — needs working `/api/upload/sas-token` and `/api/documents/status` endpoints.

- [ ] T018 [US2] Implement queue worker in `app/worker.py`: create main loop that polls `conversion-jobs` queue via `QueueClient.receive_messages(max_messages=1, visibility_timeout=300)`. For each message: parse Event Grid event envelope (extract `blob_name` from `subject`, `content_type` from `data.contentType`, `size_bytes` from `data.contentLength` per `contracts/worker-queue.md`), extract `document_id` from blob name (strip extension), download blob from `files/{blob_name}`, read blob metadata, set status to `processing`, run conversion pipeline (detect format → call `pdf_extractor`/`docx_extractor`/`pptx_extractor` → `ocr_service` if scanned → `html_builder.build_html()` → `wcag_validator.validate_html()` → upload to `converted/{doc_id}/`), set status to `completed` with metadata, delete queue message. On error: set status to `failed` with `error_message`, do NOT delete message (retry after visibility timeout). Use `app/config.py` settings and `app/dependencies.py` for clients. Poll interval: 2 seconds. Include graceful shutdown on SIGTERM/SIGINT.
- [ ] T019 [US2] Add poison queue handling in `app/worker.py`: after 3 failed dequeue attempts (`dequeue_count >= 3`), log error with document details, delete message from main queue (Azure Storage Queue auto-moves to `conversion-jobs-poison` queue after max dequeue count). Add startup log message showing worker configuration (queue name, poll interval, visibility timeout).
- [ ] T020 [P] [US2] Add password-protected file detection in `app/worker.py`: before running extraction pipeline, check if file is password-protected using `_is_password_protected_pdf()`, `_is_password_protected_docx()`, `_is_password_protected_pptx()` (migrated in T015). If password-protected, set status to `failed` with appropriate error message and delete the queue message (no retry needed).
- [ ] T021 [P] [US2] Create local queue simulation for development: in `app/worker.py`, when running locally (Azurite detected via connection string), the worker should enqueue a message to the `conversion-jobs` queue when a blob is uploaded via the SAS token endpoint. Add a background task in `POST /api/upload/sas-token` (in `app/main.py`) that enqueues a simulated Event Grid message to the queue after the placeholder blob is created. This replaces Event Grid which isn't available locally. Message format must match `contracts/worker-queue.md` Event Grid envelope.

---

## Phase 5 — User Story 3: Local Development with docker-compose (P1)

> **Goal**: Single `docker-compose up` command starts Azurite, backend API, worker, and frontend with hot-reload.
> **Independent Test**: Run `docker-compose up`, upload a PDF via `http://localhost:3000`, verify conversion completes.
> **Depends on**: Phase 3 (US4) + Phase 4 (US2) — needs working API and worker.

- [ ] T022 [US3] Create `docker-compose.yml` in project root with 4 services per `quickstart.md` reference implementation: (1) `azurite` — `mcr.microsoft.com/azure-storage/azurite` with `--loose --skipApiVersionCheck` flags, ports 10000/10001/10002, named volume `azurite-data`; (2) `backend` — builds from `Dockerfile.backend`, port 8000, mounts `./backend:/app/backend` and `./app:/app/app` for hot-reload, depends on `azurite`, command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`, environment from `.env.example`; (3) `worker` — same image as backend, no port, command: `python -m app.worker`, mounts same volumes, depends on `azurite`; (4) `frontend` — builds from `frontend/Dockerfile`, port 3000, `BACKEND_URL=http://backend:8000`, depends on `backend`.
- [ ] T023 [US3] Create `frontend/Dockerfile` as multi-stage build: stage 1 (`deps`) uses `node:20-alpine`, installs npm dependencies; stage 2 (`builder`) copies source and runs `npm run build`; stage 3 (`runner`) uses `node:20-alpine`, copies `.next/standalone` and `.next/static` and `public/`, sets `PORT=3000`, `HOSTNAME=0.0.0.0`, runs `node server.js`. Target image size < 200MB. Next.js `output: 'standalone'` is already configured in `next.config.mjs`.
- [ ] T024 [US3] Update `frontend/next.config.mjs`: change default `BACKEND_URL` from `http://localhost:7071` to `http://localhost:8000` (FastAPI replaces Azure Functions on port 8000). The rewrite rules (`/api/:path*` → `${backendUrl}/api/:path*`) remain unchanged.

---

## Phase 6 — User Story 1: Developer Deploys a Backend Change (P0)

> **Goal**: CI/CD pipeline builds container images, pushes to ACR, and deploys to Container Apps in < 60 seconds.
> **Independent Test**: Push a one-line change, measure time from `git push` to new revision serving traffic (< 60s).
> **Depends on**: Phase 2 (Dockerfile), Phase 5 (frontend Dockerfile).

- [ ] T025 [US1] Create GitHub Actions deploy workflow in `.github/workflows/deploy.yml`: trigger on push to `main` branch. Jobs: (1) `build-backend` — checkout, `az acr build --registry crpdftohtml --image pdf-to-html-api:${{ github.sha }}` using `Dockerfile.backend`; (2) `build-frontend` — `az acr build --registry crpdftohtml --image pdf-to-html-frontend:${{ github.sha }}` using `frontend/Dockerfile`; (3) `deploy` (depends on builds) — `az containerapp update` for `ca-pdftohtml-api`, `ca-pdftohtml-worker`, and `ca-pdftohtml-frontend` with new image tags. Use `AZURE_CREDENTIALS` secret for `az login`. Include concurrency group to prevent parallel deploys.
- [ ] T026 [P] [US1] Update existing CI workflow `.github/workflows/eval.yml` to run backend tests inside the container: add a step that builds the backend image and runs `pytest tests/ -v` inside the container, or add a step that installs dependencies from `requirements.txt` and runs `pytest` directly (simpler). Ensure the CI step uses `pip install -r requirements.txt` without `azure-functions` (removed in T005).
- [ ] T027 [P] [US1] Create Bicep infrastructure-as-code in `infra/main.bicep`: orchestrator template that deploys Container Apps Environment, ACR, Event Grid, and Container Apps using modules. Parameters: `location`, `environmentName`, `storageAccountName`, `storageAccountResourceGroup`.
- [ ] T028 [P] [US1] Create `infra/modules/container-registry.bicep`: Azure Container Registry (Basic SKU, admin disabled, managed identity pull). Output: `loginServer`, `registryName`.
- [ ] T029 [P] [US1] Create `infra/modules/container-apps.bicep`: Container Apps Environment (`cae-pdftohtml`) + three Container Apps per `data-model.md` infrastructure entities: (1) `ca-pdftohtml-api` — port 8000, external ingress, min 1 / max 5, HTTP scale rule (10 concurrent), liveness probe on `/health`, readiness probe on `/ready`; (2) `ca-pdftohtml-worker` — no ingress, min 0 / max 10, KEDA `azure-queue` scale rule (`queueName=conversion-jobs`, `queueLength=1`), command `python -m app.worker`; (3) `ca-pdftohtml-frontend` — port 3000, external ingress, min 1 / max 3, HTTP scale rule (50 concurrent). All apps reference ACR images and pass environment variables.
- [ ] T030 [P] [US1] Create `infra/modules/event-grid.bicep`: Event Grid system topic (`evgt-pdftohtml-storage`) on storage account + subscription (`evgs-pdftohtml-blobcreated`) filtered to `Microsoft.Storage.BlobCreated` on `/blobServices/default/containers/files/` with `data.contentLength > 0` advanced filter, endpoint type `StorageQueue`, destination `conversion-jobs`. See `research.md` R7 and `data-model.md` Event Grid entities.
- [ ] T031 [P] [US1] Create `infra/parameters/dev.bicepparam` and `infra/parameters/prod.bicepparam` with environment-specific values: resource group names, storage account names, location, Container Apps environment names, SKU differences.

---

## Phase 7 — Polish & Cross-Cutting Concerns

> **Goal**: Documentation, deprecation markers, validation, and operational readiness.
> No user story label — applies across all stories.

- [ ] T032 Add deprecation notice to `function_app.py`: insert a comment block at the top of the file stating it is deprecated, replaced by `app/main.py` (API) and `app/worker.py` (worker), kept as reference only, not deployed. Do NOT delete the file — it serves as fallback reference per spec.
- [ ] T033 [P] Add deprecation notice to `host.json` and `local.settings.json`: insert comment or note that these are Azure Functions configuration files, replaced by `docker-compose.yml` (local dev) and Bicep parameters (production).
- [ ] T034 [P] Update `README.md`: add "Container Apps Migration" section documenting new architecture (link to `specs/004-container-apps-migration/plan.md` architecture diagram), local development instructions (`docker-compose up`), deployment instructions (reference `infra/` and `.github/workflows/deploy.yml`), environment variables table, and health check endpoints.
- [ ] T035 [P] Create `scripts/migrate-verify.sh` validation script: checks that (1) `docker-compose up` starts all 4 services successfully, (2) `curl http://localhost:8000/health` returns 200, (3) `curl http://localhost:3000` returns 200, (4) `pytest tests/ -v` passes all tests, (5) `POST /api/upload/sas-token` returns valid response. Script exits 0 on success, 1 on any failure. Used for manual migration verification.
- [ ] T036 [P] Create `MIGRATION.md` in project root: document the migration from Azure Functions to Container Apps including architecture comparison (before/after), rollback procedure (redeploy Function App from `function_app.py`), environment variable mapping (Functions `local.settings.json` → Container Apps env vars), and known differences (port 7071 → 8000, blob trigger → queue worker).
- [ ] T037 Add structured logging in `app/main.py` and `app/worker.py`: configure Python `logging` module with JSON formatter for production (structured logs for Azure Monitor), human-readable formatter for local dev, log level from `LOG_LEVEL` env var. Include request ID in API logs and message ID in worker logs.
- [ ] T038 [P] Add `__main__.py` entry point for worker in `app/__main__.py`: allow running the worker as `python -m app` with `WORKER_MODE=true` as an alternative to `python -m app.worker`. This provides flexibility for the Container Apps command override.
- [ ] T039 Perform end-to-end validation: run `docker-compose up --build`, upload a test PDF via `POST /api/upload/sas-token` + `PUT` to SAS URL, poll `GET /api/documents/status` until `completed`, verify `GET /api/documents/{id}/download` returns valid download URL, verify `DELETE /api/documents/{id}` succeeds, confirm all 174+ tests still pass with `pytest tests/ -v`. Document results in a comment on the feature branch PR.

---

## Dependency Graph

```
Phase 1 (Setup)
  T001 ─┐
  T002 ─┤
  T003 ─┼──► Phase 2 (Foundational)
  T004 ─┤     T006 ──────────────────────────────────┐
  T005 ─┘     T007 [P] ──┐                           │
              T008 [P] ──┤                           │
              T009 [P] ──┘                           │
                                                     ▼
                                    Phase 3 (US4: API Endpoints)
                                      T010–T014 (routes)
                                      T015 (helpers)
                                      T016 (test config)
                                      T017 (verify tests)
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            │
                   Phase 4 (US2)    Phase 5 (US3)       │
                   T018 (worker)    T022 (compose)      │
                   T019 (poison)    T023 (fe Dockerfile) │
                   T020 [P]         T024 (next.config)  │
                   T021 [P]              │              │
                        │                │              │
                        └────────┬───────┘              │
                                 ▼                      │
                          Phase 6 (US1: Deploy)         │
                          T025 (deploy workflow)        │
                          T026 [P] (CI update)          │
                          T027–T031 [P] (Bicep IaC)     │
                                 │                      │
                                 ▼                      │
                          Phase 7 (Polish)◄─────────────┘
                          T032–T039
```

### User Story Dependencies

| Story | Depends On | Can Parallel With |
|-------|-----------|-------------------|
| US4 (API Compat) | Phase 2 (Foundational) | — (must be first story) |
| US2 (Queue Worker) | US4 (needs upload endpoint) | US3 (docker-compose) |
| US3 (docker-compose) | US4 (needs working API) | US2 (worker) |
| US1 (Deploy Pipeline) | US2 + US3 (needs Dockerfiles) | — |
| US5 (WCAG) | Implicit — pipeline unchanged | All (no tasks needed) |

---

## Parallel Execution Opportunities

### Within Phase 2 (Foundational)
```
T006 (main.py)  ──►  sequential (other tasks depend on app shell)
T007 (Dockerfile) ─┐
T008 (.dockerignore)├─►  parallel (independent files)
T009 (.env.example) ┘
```

### Within Phase 3 (US4)
```
T010 (upload)    ─┐
T011 (status)    ─┤
T012 (download)  ─┼─►  parallel (independent routes, same file but different functions)
T013 (delete one)─┤
T014 (delete all)─┘
T015 (helpers)   ─►  parallel with routes (pure functions)
T016 (test config)─► after routes complete
T017 (verify)     ─► after T016
```

### Within Phase 4 (US2) + Phase 5 (US3)
```
T018 (worker)       ─► sequential (core worker logic)
T019 (poison queue) ─► after T018
T020 [P] (password) ─┐
T021 [P] (local sim) ┼─► parallel with T019
                      │
T022 (compose)       ─┤
T023 (fe Dockerfile)  ┼─► parallel (Phase 5 runs alongside Phase 4)
T024 (next.config)   ─┘
```

### Within Phase 6 (US1) — Maximum Parallelism
```
T025 (deploy.yml)  ─► sequential (depends on all Dockerfiles)
T026 [P] (CI)      ─┐
T027 [P] (main.bicep)─┤
T028 [P] (ACR bicep)  ─┤
T029 [P] (CA bicep)    ─┼─► all parallel (independent IaC modules)
T030 [P] (EG bicep)    ─┤
T031 [P] (params)      ─┘
```

---

## Implementation Strategy

### MVP (Minimum Viable Migration)
**Phases 1–4**: Setup + Foundational + US4 (API) + US2 (Worker)
- All API endpoints working on FastAPI
- Queue worker processing files
- All 174+ tests passing
- Can be verified locally with `pytest` before containerization

### Incremental Delivery Order
1. **Phase 1 + 2**: Get `app/main.py` running with health probes (1 day)
2. **Phase 3 (US4)**: Migrate all HTTP routes, verify tests (1–2 days)
3. **Phase 4 (US2)**: Build queue worker, verify e2e conversion (1 day)
4. **Phase 5 (US3)**: docker-compose for local dev (0.5 days)
5. **Phase 6 (US1)**: CI/CD + IaC — deploy to Azure (1 day)
6. **Phase 7**: Polish, docs, validation (0.5 days)

**Estimated total**: 5–6 days

### Rollback Plan
- `function_app.py` is NOT deleted (T032 adds deprecation notice only)
- Azure Functions app remains deployed as fallback
- To rollback: redeploy Function App with `func azure functionapp publish`
- Frontend only needs `BACKEND_URL` change to point back to Functions endpoint

### Key Risk Mitigations
- **Test compatibility**: T017 explicitly verifies all 174+ tests pass before proceeding
- **API contract parity**: Each route task (T010–T014) references specific contract docs
- **Local dev parity**: T022 docker-compose matches production architecture
- **Zero-downtime deploy**: T029 configures health probes and revision management
