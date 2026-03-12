# Feature Specification: Azure Container Apps Migration

**Feature Branch**: `004-container-apps-migration`
**Created**: 2026-06-15
**Status**: Draft
**Input**: Migrate pdf-to-html WCAG document converter from Azure Functions to Azure Container Apps for faster deploys, simpler local dev, and elimination of blob trigger runtime coupling.

## Problem Statement

The current Azure Functions deployment has three critical pain points:

1. **Slow deploys**: `func azure functionapp publish` takes 5–10+ minutes per deploy, blocking iteration velocity.
2. **Blob trigger coupling**: The blob trigger requires the Azure Functions runtime and specific extension bundles; it cannot run outside `func start`.
3. **Local dev friction**: Azurite requires special SAS URL handling for `_is_azurite()` workarounds, and three separate processes must be started manually.

The migration to Azure Container Apps targets **sub-minute deploys** (~30s container push + revision swap), a **standard HTTP framework** (FastAPI), and a **single `docker-compose up`** for local development.

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Developer Deploys a Backend Change (Priority: P0)

A developer merges a Python backend fix. CI builds a Docker image, pushes to
ACR, and triggers a Container Apps revision swap. The new code is live within
60 seconds of the push completing.

**Why this priority**: Deploy speed is the primary motivation for this
migration. Every deploy currently costs 5–10 minutes of blocked time.

**Independent Test**: Push a one-line change to backend, measure time from
`git push` to the new revision serving traffic. Must be < 60 seconds.

**Acceptance Scenarios**:

1. **Given** a backend code change is merged, **When** CI runs, **Then** a
   new container image is built, pushed to ACR, and a new Container App
   revision is activated within 60 seconds.
2. **Given** a revision swap fails health checks, **When** the new revision
   returns 5xx on `/health`, **Then** traffic remains on the previous
   revision (zero-downtime rollback).

---

### User Story 2 – File Upload Triggers Conversion (Priority: P0)

A user uploads a PDF via the web UI. The file lands in Azure Blob Storage.
An Event Grid event fires, placing a message on an Azure Storage Queue. The
backend worker (KEDA-scaled) picks up the message and runs the conversion
pipeline. The user sees real-time status updates via polling.

**Why this priority**: The blob trigger replacement is the core architectural
change. All existing functionality must work identically from the user's
perspective.

**Independent Test**: Upload a 10-page PDF, verify conversion completes and
status endpoint reports "completed" with correct page_count.

**Acceptance Scenarios**:

1. **Given** a file is uploaded to `files/` container, **When** Event Grid
   fires a BlobCreated event, **Then** a message is enqueued to `conversion-jobs`
   queue within 2 seconds.
2. **Given** a queue message arrives, **When** the worker container processes
   it, **Then** the same pipeline runs (extract → OCR → build HTML → validate
   WCAG → upload output → update status).
3. **Given** 10 files are uploaded simultaneously, **When** KEDA detects queue
   depth > 0, **Then** the worker scales from 0 → N replicas to process in
   parallel.
4. **Given** a worker fails mid-processing, **When** the message visibility
   timeout expires, **Then** the message is retried (up to 3 attempts before
   poison queue).

---

### User Story 3 – Local Development with docker-compose (Priority: P1)

A developer clones the repo and runs `docker-compose up`. Azurite, the
backend API, and the frontend all start. The developer can upload files,
see them convert, and iterate on code with hot-reload.

**Why this priority**: Simplifying local dev is a secondary goal but critical
for developer experience. Currently requires manually starting 3 processes.

**Independent Test**: Clone repo, run `docker-compose up`, upload a PDF via
`http://localhost:3000`, verify conversion completes.

**Acceptance Scenarios**:

1. **Given** a developer runs `docker-compose up`, **When** all services
   start, **Then** Azurite (port 10000), backend (port 8000), and frontend
   (port 3000) are accessible.
2. **Given** the developer modifies a Python file, **When** uvicorn detects
   the change, **Then** the backend reloads within 3 seconds.
3. **Given** Azurite is used locally, **When** SAS tokens are generated,
   **Then** they use `http://localhost:10000` endpoints (no special
   `_is_azurite()` workarounds needed).

---

### User Story 4 – All Existing API Endpoints Work (Priority: P0)

Every existing HTTP endpoint continues to function with identical
request/response contracts. Frontend code requires only a `BACKEND_URL`
environment variable change.

**Why this priority**: Zero functional regression is mandatory. The 174
backend tests must pass. All frontend service files must work unchanged.

**Independent Test**: Run the full test suite against the new FastAPI
backend. All 174+ tests pass.

**Acceptance Scenarios**:

1. **Given** `POST /api/upload/sas-token` is called, **When** the FastAPI
   backend processes it, **Then** the response matches the existing contract
   (document_id, upload_url, expires_at).
2. **Given** `GET /api/documents/status` is called, **When** the backend
   queries blob metadata, **Then** the response includes documents[] and
   summary{} in the same format.
3. **Given** `GET /api/documents/{id}/download` is called, **Then** the
   response includes download_url (SAS), filename, and image_urls[].
4. **Given** `DELETE /api/documents/{id}` is called, **Then** the document
   and its outputs are deleted, response matches existing contract.
5. **Given** `DELETE /api/documents` is called, **Then** all documents are
   deleted with deleted_input/deleted_output counts.

---

### User Story 5 – WCAG 2.1 AA Compliance Maintained (Priority: P0)

All converted HTML output remains WCAG 2.1 AA compliant. The conversion
pipeline (extractors, OCR, HTML builder, validator) is unchanged. The
frontend UI remains accessible.

**Why this priority**: WCAG compliance is a legal requirement (DOJ April
2026). Infrastructure migration must not introduce accessibility regressions.

**Independent Test**: Run WCAG evaluation suite against output from the
containerized backend. Zero new violations.

**Acceptance Scenarios**:

1. **Given** the containerized backend processes a PDF, **When** the HTML
   output is validated, **Then** it passes all 7 server-side WCAG rules.
2. **Given** the frontend is served from a Container App, **When** axe-core
   scans the UI, **Then** zero WCAG 2.1 AA violations are found.

## Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| Deploy time | < 60 seconds | CI pipeline: image push to revision active |
| Cold start | < 5 seconds | Time from scale-from-zero to first 200 response |
| Local dev startup | < 30 seconds | `docker-compose up` to all services healthy |
| Test compatibility | 100% | All 174+ existing tests pass |
| API compatibility | 100% | All request/response contracts identical |
| Availability | 99.9% | Azure Container Apps SLA |
| Cost | ≤ current | Consumption plan pricing vs Functions consumption |

## Out of Scope

- Database migration (there is no database; blob metadata remains the status store)
- Changing the conversion pipeline logic (extractors, OCR, HTML builder, validator)
- Frontend redesign (only BACKEND_URL config changes)
- Multi-region deployment
- Authentication/authorization changes (endpoints remain anonymous)
- WebSocket real-time updates (polling stays at 3s interval)
