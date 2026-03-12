# Decision: API Endpoint Migration to FastAPI (Phase 3+4)

**Author:** Wonder-Woman  
**Date:** 2026-07-15  
**Status:** Implemented  

## Context

The project is migrating from Azure Functions to Azure Container Apps with FastAPI. Phase 1+2 created the foundational plumbing (config, dependencies, health probes). Phase 3+4 migrates all HTTP endpoints and creates a queue-based conversion worker.

## Decisions

### 1. Inline routes in app/main.py (no separate router modules)

All 5 API endpoints are defined directly in `app/main.py` rather than split into separate router files. The endpoint count is small enough that a single file remains readable, and it avoids import complexity. If the API grows beyond ~10 endpoints, split into `app/routes/upload.py`, `app/routes/documents.py`, etc.

### 2. Password protection helpers in app/security.py

Created a dedicated `app/security.py` module for password-protection detection rather than keeping them in `dependencies.py`. These functions have heavy imports (pymupdf, python-docx, python-pptx) and are only called during conversion — separating them keeps `dependencies.py` lightweight and fast to import.

### 3. Queue worker as a class (ConversionWorker)

Implemented the worker as a `ConversionWorker` class rather than a bare function loop. This enables:
- Clean signal handling via instance method binding
- Testability (instantiate without starting the loop)
- Future extension (e.g. concurrent workers, health endpoint)

### 4. Content polling with timeout in worker

The worker waits up to 30 seconds for blob content to become non-zero after receiving a queue message. This handles the race condition where the queue message arrives before the browser finishes uploading via the SAS URL. Without this, the worker would attempt to convert 0-byte files.

### 5. Public aliases for dependency functions

Added public names (without `_` prefix) in `app/dependencies.py` pointing to the private implementations. This keeps the internal API stable while providing clean import paths for `app/main.py` and `app/worker.py`.

### 6. Base64 encoding for queue messages

Azure Storage Queue requires base64 encoding when using the Python SDK. The upload endpoint encodes messages before sending, and the worker decodes them on receipt with a fallback to raw string parsing.

## Files Changed

- `app/main.py` — Added 5 API endpoints (upload, status, download, delete single, delete all)
- `app/worker.py` — New queue-based conversion worker
- `app/security.py` — New password protection detection helpers
- `app/dependencies.py` — Added public aliases for private helper functions
- `tests/conftest.py` — Added FastAPI TestClient fixture

## Verification

- All 174 existing tests pass
- All 11 FastAPI routes registered correctly
- All new modules import without errors
