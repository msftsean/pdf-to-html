# Implementation Plan: Azure Container Apps Migration

**Branch**: `004-container-apps-migration` | **Date**: 2026-06-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-container-apps-migration/spec.md`

## Summary

Migrate the pdf-to-html WCAG document converter from Azure Functions to Azure
Container Apps. The backend HTTP triggers become FastAPI routes served by
Uvicorn. The blob trigger is replaced by Event Grid → Storage Queue → KEDA
scaler pattern. The frontend's Next.js standalone build runs as a separate
Container App. Local development uses docker-compose with Azurite, providing
single-command startup. Deploy time drops from 5–10 minutes to ~30 seconds
via ACR image push + revision swap.

The `backend/` package (extractors, OCR, HTML builder, validator,
status_service) is **unchanged** — it has zero Azure Functions SDK
dependencies. Only `function_app.py` (the orchestrator) is replaced by
`app/main.py` (FastAPI routes) and `app/worker.py` (queue consumer).

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Node 20 (frontend)
**Primary Dependencies**:
- Backend: FastAPI, Uvicorn, azure-storage-blob, azure-storage-queue,
  azure-ai-documentintelligence, azure-identity, PyMuPDF, python-docx,
  python-pptx, Jinja2
- Frontend: React 18, Next.js 14, Bootstrap 5, axe-core (unchanged)
**Storage**: Azure Blob Storage (`files/` input, `converted/` output) — unchanged
**Queue**: Azure Storage Queue (`conversion-jobs`) — new
**Event Trigger**: Event Grid system topic on storage account — new
**Testing**: pytest (backend), Jest + React Testing Library (frontend) — unchanged
**Target Platform**: Azure Container Apps (Consumption plan)
**Container Registry**: Azure Container Registry (Basic SKU)
**Project Type**: Web application (containerized backend API + worker + frontend SPA)
**Performance Goals**: < 60s deploys; < 5s cold start; same conversion speed
**Constraints**: WCAG 2.1 AA mandatory; all 174+ tests must pass; zero
API contract changes; keep Azure Blob Storage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. WCAG 2.1 AA Compliance | ✅ PASS | Pipeline unchanged; HTML output identical; UI unchanged |
| II. Multi-Format Ingestion | ✅ PASS | Extractors untouched (pdf, docx, pptx) |
| III. Selective OCR | ✅ PASS | ocr_service.py unchanged; same Azure DI integration |
| IV. Accessible Semantic Output | ✅ PASS | html_builder.py unchanged; same WCAG features |
| V. Batch Processing at Scale | ✅ PASS | KEDA queue scaler enables parallel processing (0→10 replicas) |
| VI. Modular Pipeline | ✅ PASS | Backend package completely decoupled from hosting layer |
| VII. Test-First Development | ✅ PASS | All existing tests pass; new tests for FastAPI routes + worker |
| VIII. Cloud-Native Resilience | ✅ PASS | Container Apps health probes; queue retry; revision rollback |

**GATE RESULT**: ALL PASS — proceed to Phase 0.

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. WCAG 2.1 AA Compliance | ✅ PASS | No pipeline changes; contracts identical |
| V. Batch Processing at Scale | ✅ PASS | Queue-based processing with KEDA scales better than blob trigger |
| VI. Modular Pipeline | ✅ PASS | Clean separation: `app/` (hosting) vs `backend/` (pipeline) |
| VIII. Cloud-Native Resilience | ✅ PASS | Health probes, poison queue, zero-downtime revisions |

**POST-DESIGN GATE**: ALL PASS — proceed to Phase 2 task generation.

## Project Structure

### Documentation (this feature)

```text
specs/004-container-apps-migration/
├── spec.md                  # Feature specification
├── plan.md                  # This file
├── research.md              # Phase 0: technology decisions (7 research items)
├── data-model.md            # Phase 1: new entities (QueueMessage, infra)
├── quickstart.md            # Phase 1: developer onboarding
├── contracts/               # Phase 1: API contracts
│   ├── upload-api.md        # POST /api/upload/sas-token (unchanged)
│   ├── status-api.md        # GET /api/documents/status (unchanged)
│   ├── download-delete-api.md # GET download, DELETE endpoints (unchanged)
│   └── worker-queue.md      # Queue worker protocol (new)
├── checklists/
│   └── requirements.md      # Spec quality checklist
└── tasks.md                 # Phase 2: actionable tasks (via /speckit.tasks)
```

### Source Code Changes

```text
# NEW FILES
app/
├── __init__.py              # Package init
├── main.py                  # FastAPI app with HTTP routes
├── worker.py                # Queue consumer (replaces blob trigger)
├── dependencies.py          # DI: blob service, queue client
├── config.py                # Env var configuration
└── models.py                # Pydantic request/response schemas

Dockerfile.backend           # Python backend container image
docker-compose.yml           # Local dev orchestration
frontend/Dockerfile          # Next.js standalone container image
.dockerignore                # Docker build exclusions

infra/
├── main.bicep               # Container Apps environment
├── modules/
│   ├── container-apps.bicep # API + Worker + Frontend apps
│   ├── container-registry.bicep
│   └── event-grid.bicep     # System topic + subscription
└── parameters/
    ├── dev.bicepparam
    └── prod.bicepparam

.github/workflows/
├── deploy.yml               # NEW: Build → push → deploy pipeline
└── ci.yml                   # UPDATED: Run tests in container

# MODIFIED FILES
requirements.txt             # +fastapi +uvicorn +azure-storage-queue
                             # -azure-functions
frontend/next.config.mjs     # BACKEND_URL default port 7071 → 8000

# UNCHANGED FILES (zero modifications)
backend/                     # Entire package unchanged
├── models.py
├── pdf_extractor.py
├── docx_extractor.py
├── pptx_extractor.py
├── ocr_service.py
├── html_builder.py
├── wcag_validator.py
└── status_service.py

# DEPRECATED (kept for reference, not deployed)
function_app.py              # Azure Functions orchestrator
host.json                    # Azure Functions config
local.settings.json          # Azure Functions local config
.funcignore                  # Azure Functions ignore
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Azure Container Apps Environment                │
│                        (cae-pdftohtml)                              │
│                                                                     │
│  ┌──────────────────────┐    ┌──────────────────────┐              │
│  │  ca-pdftohtml-api    │    │ ca-pdftohtml-frontend │              │
│  │  (FastAPI + Uvicorn) │    │ (Next.js standalone)  │              │
│  │  Port 8000           │◄───│ Port 3000             │              │
│  │  Min: 1, Max: 5      │    │ Min: 1, Max: 3        │              │
│  │  Scale: HTTP requests │    │ Scale: HTTP requests  │              │
│  └──────────────────────┘    └──────────────────────┘              │
│                                                                     │
│  ┌──────────────────────┐                                          │
│  │ ca-pdftohtml-worker  │                                          │
│  │ (Queue consumer)     │                                          │
│  │ Min: 0, Max: 10      │                                          │
│  │ Scale: KEDA queue    │                                          │
│  │ depth (azure-queue)  │                                          │
│  └──────────┬───────────┘                                          │
└─────────────┼───────────────────────────────────────────────────────┘
              │ dequeue
              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Azure Storage Account (stpdftohtml331ef3)                         │
│                                                                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐                │
│  │  files/   │  │ converted/│  │ conversion-jobs  │                │
│  │ (input)   │  │ (output)  │  │ (Storage Queue)  │                │
│  └─────┬─────┘  └───────────┘  └────────┬─────────┘                │
│        │ BlobCreated                     ▲ enqueue                  │
│        ▼                                 │                          │
│  ┌──────────────────────────────────────┐│                          │
│  │  Event Grid System Topic             ││                          │
│  │  (evgt-pdftohtml-storage)            ├┘                          │
│  │  Filter: files/, contentLength > 0   │                           │
│  └──────────────────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐
│  Azure Container        │
│  Registry (crpdftohtml) │
│  pdf-to-html-api:sha    │
│  pdf-to-html-frontend:sha│
└─────────────────────────┘

┌─────────────────────────┐
│  Azure Document         │
│  Intelligence           │
│  (OCR service)          │
└─────────────────────────┘
```

## Migration Mapping: function_app.py → FastAPI

### HTTP Endpoints

| # | Current (Azure Functions) | New (FastAPI) | Changes |
|---|--------------------------|---------------|---------|
| 1 | `@app.route("upload/sas-token", POST)` | `@router.post("/api/upload/sas-token")` | Pydantic validation |
| 2 | `@app.route("documents/status", GET)` | `@router.get("/api/documents/status")` | Query params via `Query()` |
| 3 | `@app.route("documents/{id}/download", GET)` | `@router.get("/api/documents/{document_id}/download")` | Path params native |
| 4 | `@app.route("documents/{id}", DELETE)` | `@router.delete("/api/documents/{document_id}")` | Same |
| 5 | `@app.route("documents", DELETE)` | `@router.delete("/api/documents")` | Same |
| 6 | N/A | `@app.get("/health")` | **NEW**: Health check probe |
| 7 | N/A | `@app.get("/ready")` | **NEW**: Readiness probe |

### Blob Trigger → Queue Worker

| Aspect | Current | New |
|--------|---------|-----|
| Trigger | `@app.blob_trigger("files/{name}")` | `queue_client.receive_messages()` |
| Input | `func.InputStream` (blob data) | Queue message → read blob via SDK |
| Scaling | Azure Functions runtime | KEDA azure-queue scaler |
| Retry | Functions runtime retry | Queue visibility timeout (3 attempts) |
| Dead letter | None configured | `conversion-jobs-poison` queue |
| Local dev | `func start` + Azurite | `docker-compose up` + Azurite queue |

### Helper Functions Migration

| Function | Current Location | New Location | Changes |
|----------|-----------------|--------------|---------|
| `_get_blob_service_client()` | `function_app.py` | `app/dependencies.py` | FastAPI dependency injection |
| `_extract_account_key()` | `function_app.py` | `app/dependencies.py` | Same logic |
| `_generate_download_sas_url()` | `function_app.py` | `app/dependencies.py` | Same logic |
| `_retry_blob_operation()` | `function_app.py` | `backend/blob_utils.py` or `app/dependencies.py` | Same logic |
| `_is_azurite()` | `function_app.py` | `app/config.py` | Simplified — docker-compose handles network |
| `_is_password_protected_*()` | `function_app.py` | `app/worker.py` | Same logic |
| `_json_error()` | `function_app.py` | Replaced by FastAPI `HTTPException` | Simplified |

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Event Grid → Queue latency > 2s | Low | Low | Event Grid is near-instant; monitor with metrics |
| KEDA cold start > 5s | Medium | Medium | Set `minReplicas: 1` for worker if latency matters |
| SAS token Azurite incompatibility | Low | Low | `--loose` and `--skipApiVersionCheck` flags |
| Test failures from import changes | Medium | Medium | Update imports incrementally; CI catches regressions |
| Docker image size > 1GB | Low | Medium | Multi-stage build; `python:3.12-slim` base |
| Frontend CORS issues | Low | Low | Next.js rewrites proxy (no CORS needed) |

## Dependencies & Prerequisites

Before implementation:
1. ✅ Azure subscription with Container Apps provider registered
2. ✅ SPN credentials in `.env` for Azure CLI operations
3. ✅ Storage account `stpdftohtml331ef3` accessible
4. ☐ ACR `crpdftohtml` created (Task T001)
5. ☐ Container Apps Environment created (Task T002)
6. ☐ Event Grid system topic enabled on storage account (Task T003)
