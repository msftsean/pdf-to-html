# Decision: Container Apps Migration — Phase 1+2 File Structure

**Date:** 2026-07-15  
**Author:** Wonder-Woman (Backend Developer)  
**Status:** Implemented

## Context

We are migrating from Azure Functions (`function_app.py`) to FastAPI + Azure Container Apps. The existing `backend/` package is already hosting-agnostic (zero Azure Functions SDK imports), so the migration only touches the HTTP layer.

## Decision

Created a new `app/` package with clear separation:

| File | Responsibility |
|------|---------------|
| `app/config.py` | Pydantic Settings singleton — single source of truth for all env vars |
| `app/models.py` | Pydantic request/response models matching existing JSON contracts |
| `app/dependencies.py` | Shared infrastructure helpers (blob client, queue client, SAS, retry) |
| `app/main.py` | FastAPI app shell with CORS, startup init, health/ready probes |

## Key Choices

1. **Dual env-var support:** `config.py` accepts both `AZURE_STORAGE_CONNECTION_STRING` (new) and `AzureWebJobsStorage` (legacy Azure Functions) via a `storage_connection_string` property. This allows gradual migration without breaking existing `.env` files.

2. **Queue client added:** `get_queue_client()` is new — the Azure Functions version used blob triggers, but Container Apps will use queue-based polling. Same auth logic as blob client.

3. **`response_model=None` on `/ready`:** FastAPI cannot auto-generate a response model for `dict | JSONResponse` union return types. Used `response_model=None` to bypass validation on this probe endpoint.

4. **`requirements.txt` — `azure-functions` removed:** This is intentional. The legacy `function_app.py` still exists but is no longer the deployment target. If someone needs to run it temporarily, they can `pip install azure-functions` manually.

## Impact on Other Agents

- **Cyborg:** Dockerfile.backend and `.env.example` are ready for CI/CD pipeline integration.
- **Flash:** Frontend should update `NEXT_PUBLIC_API_URL` from `http://localhost:7071/api` to `http://localhost:8000` (no `/api` prefix — FastAPI routes are at root).
- **Batman:** Phase 3 (route implementations) can now be built on this foundation.
