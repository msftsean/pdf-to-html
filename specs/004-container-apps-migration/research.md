# Research: Azure Container Apps Migration

**Phase 0 Output** | **Date**: 2026-06-15

## R1: Blob Trigger Replacement Strategy

**Decision**: Replace Azure Functions blob trigger with **Event Grid →
Azure Storage Queue → KEDA azure-queue scaler** pattern.

**Rationale**: The current blob trigger fires when a file lands in the
`files/` container. Azure Container Apps doesn't support blob triggers
natively, but KEDA (built into Container Apps) supports queue-based
scaling. The recommended pattern is:

1. **Event Grid subscription** on the storage account filters for
   `Microsoft.Storage.BlobCreated` events on the `files/` container.
2. Events are routed to an **Azure Storage Queue** (`conversion-jobs`).
3. A **KEDA `azure-queue` scaler** on the worker Container App monitors
   queue depth and scales from 0 → N replicas.
4. Each worker dequeues a message, reads the blob, and runs the pipeline.

This is preferred over the KEDA blob scaler (which counts total blobs,
not new arrivals) and over Event Grid → direct HTTP webhook (which has
no built-in retry/dead-letter without a queue).

**Alternatives considered**:
- **KEDA azure-blob scaler**: Scales on blob count, not new blobs. Would
  require processing and deleting blobs, changing the current architecture
  where input blobs persist in `files/`.
- **Event Grid → HTTP webhook**: Container App receives HTTP POST on blob
  creation. No automatic retry, no dead-letter, no scale-to-zero. Requires
  the app to be always-on.
- **Azure Service Bus**: More features than Storage Queue but adds cost and
  complexity. Storage Queue is sufficient for this workload (simple messages,
  low throughput).
- **Keep blob trigger via Functions-in-Container**: Run Azure Functions
  runtime inside a container. Adds complexity and keeps the Functions SDK
  dependency we want to eliminate.

**Queue message schema**:
```json
{
  "blob_name": "abc123.pdf",
  "container": "files",
  "document_id": "abc123",
  "content_type": "application/pdf",
  "size_bytes": 2048576,
  "timestamp": "2026-06-15T10:00:00Z"
}
```

---

## R2: HTTP Framework — Azure Functions to FastAPI

**Decision**: Replace Azure Functions HTTP triggers with **FastAPI** running
on **Uvicorn** inside a Python container.

**Rationale**: FastAPI is the natural successor for Azure Functions HTTP
triggers because:

1. **Direct route mapping**: `@app.route(...)` → `@router.get/post/delete(...)`
   with identical path patterns.
2. **Type safety**: Pydantic models for request/response validation replace
   manual `req.get_json()` / `func.HttpResponse()`.
3. **OpenAPI docs**: Automatic Swagger UI at `/docs` for API exploration.
4. **Async support**: Native `async def` handlers for I/O-bound blob
   operations.
5. **Standard ASGI**: Runs with Uvicorn, Gunicorn, or any ASGI server.
   No proprietary runtime.
6. **Health checks**: Built-in support for liveness/readiness probes
   required by Container Apps.

**Migration mapping**:

| Azure Functions | FastAPI |
|----------------|---------|
| `@app.route(route="upload/sas-token", methods=["POST"])` | `@router.post("/api/upload/sas-token")` |
| `req.get_json()` | `request: SasTokenRequest` (Pydantic) |
| `func.HttpResponse(json.dumps(data), status_code=200)` | `return JSONResponse(data)` |
| `req.params.get("document_id")` | `document_id: str = Query(...)` |
| `req.route_params.get("document_id")` | `document_id: str` (path param) |

**Alternatives considered**:
- **Flask**: Mature but synchronous (WSGI). Would need Celery for async
  processing. FastAPI's async is better for I/O-bound blob operations.
- **Django REST Framework**: Overkill for 5 endpoints. Brings ORM, admin,
  migrations we don't need.
- **Azure Functions in Container**: Keeps `func` runtime as a dependency.
  Adds image size and startup latency.
- **Starlette (raw)**: FastAPI is built on Starlette; using FastAPI adds
  Pydantic validation and OpenAPI docs for free.

---

## R3: Container Architecture — Split vs. Monolith

**Decision**: **Two Container Apps** — `api` (HTTP + worker) with separate
scaling rules, or split into `api` + `worker` if needed.

**Rationale**: Start with a single container image that runs in two modes:

1. **API mode** (`CMD ["uvicorn", "app.main:app"]`): Serves HTTP endpoints.
   Scaled by HTTP traffic (concurrent requests).
2. **Worker mode** (`CMD ["python", "-m", "app.worker"]`): Processes queue
   messages. Scaled by KEDA queue depth.

Same image, different entrypoints. This simplifies CI/CD (one image to build)
while allowing independent scaling. Both share the same `backend/` package
code.

**Alternatives considered**:
- **Single process (API + worker)**: Worker blocks the event loop during
  heavy PDF processing. API latency would spike.
- **Three containers (API + worker + frontend)**: Already planned — frontend
  is always a separate Next.js container.
- **Sidecar pattern**: Adds complexity without benefit for this workload.

---

## R4: Container Registry and Deploy Pipeline

**Decision**: Use **Azure Container Registry (ACR)** with **GitHub Actions**
for CI/CD, deploying via `az containerapp update --image`.

**Rationale**: ACR integrates natively with Container Apps (no registry
credentials needed when using managed identity). GitHub Actions already
exists in the repo for CI. The deploy flow:

1. `docker build -t <acr>.azurecr.io/pdf-to-html-api:$SHA .`
2. `docker push <acr>.azurecr.io/pdf-to-html-api:$SHA`
3. `az containerapp update --name <app> --image <acr>.azurecr.io/pdf-to-html-api:$SHA`

Revision swap is ~5–10 seconds after image pull. Total: ~30–45 seconds.

**Alternatives considered**:
- **Docker Hub**: Adds external dependency and credential management.
- **GitHub Container Registry (ghcr.io)**: Viable but requires explicit
  registry credentials in Container Apps. ACR + managed identity is simpler.
- **Azure DevOps Pipelines**: Team already uses GitHub Actions.

---

## R5: Local Development — docker-compose with Azurite

**Decision**: Use **docker-compose** with three services: `azurite`,
`backend`, `frontend`. Backend uses Uvicorn with `--reload` for hot-reload.

**Rationale**: Replaces the current 3-process manual startup. Benefits:

1. **Single command**: `docker-compose up` starts everything.
2. **Network isolation**: Services communicate via Docker network names
   (`azurite:10000`, `backend:8000`).
3. **No Azurite SAS workarounds**: The `_is_azurite()` check in
   `function_app.py` becomes unnecessary — the connection string points
   to `azurite:10000` inside the Docker network, and SAS tokens work
   identically.
4. **Volume mounts**: Source code mounted for hot-reload; Azurite data
   persisted in a named volume.

**Local queue processing**: In local dev, the worker polls the Azurite
queue directly (same KEDA pattern, just without KEDA itself). A simple
`while True: dequeue()` loop replaces the KEDA scaler.

**Alternatives considered**:
- **Keep manual 3-process startup**: Works but error-prone and undiscoverable.
- **Tilt/Skaffold**: Overkill for 3 services. docker-compose is simpler.
- **Dev Containers only**: Limits developers to VS Code. docker-compose
  is IDE-agnostic.

---

## R6: SAS Token Handling in Containers

**Decision**: Backend generates SAS tokens using the **storage account key**
extracted from the connection string, identical to the current implementation.
For production, migrate to **User Delegation SAS** with managed identity.

**Rationale**: The current `_extract_account_key()` function parses the
connection string and generates SAS tokens with `generate_blob_sas()`. This
works identically in a container — the connection string is passed via
environment variable. No code change needed for Phase 1.

In Phase 2 (post-migration), upgrade to User Delegation SAS:
- Use `DefaultAzureCredential` → `BlobServiceClient` → `get_user_delegation_key()`
- Eliminates the need for account keys in environment variables
- Container App's managed identity gets `Storage Blob Data Contributor` role

**Alternatives considered**:
- **User Delegation SAS immediately**: Requires managed identity setup before
  migration. Adds scope and risk. Better as a follow-up.
- **Pre-signed URLs via separate service**: Over-engineering for this use case.

---

## R7: Event Grid Subscription Setup

**Decision**: Use **Azure Event Grid system topic** on the storage account
with a **Storage Queue destination** filtered to `BlobCreated` events on
the `files/` container.

**Rationale**: Event Grid system topics are automatically available for
storage accounts. The subscription filters ensure only relevant events
(new uploads to `files/`) trigger processing. Storage Queue destination
provides at-least-once delivery with built-in retry and dead-letter.

**Event Grid filter**:
```json
{
  "includedEventTypes": ["Microsoft.Storage.BlobCreated"],
  "subjectBeginsWith": "/blobServices/default/containers/files/",
  "advancedFilters": [
    {
      "operatorType": "NumberGreaterThan",
      "key": "data.contentLength",
      "value": 0
    }
  ]
}
```

The `contentLength > 0` filter skips the 0-byte placeholder blobs created
during the SAS token flow, replacing the current guard in `file_upload()`.

**Alternatives considered**:
- **Event Grid → direct HTTP endpoint**: No retry semantics, no dead-letter,
  no scale-to-zero support.
- **Blob change feed**: Designed for audit/replication, not event-driven
  processing. Higher latency.
- **Custom polling**: Wasteful and adds latency. Event Grid is near-instant.
