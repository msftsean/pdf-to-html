# API Contract: Download & Delete (FastAPI)

**Migrated from**: Azure Functions `get_download_url()`, `delete_document()`,
`delete_all_documents()` in `function_app.py`
**Contract status**: **Unchanged** — request/response schemas identical

---

## Download

### Get Download URLs

```
GET /api/documents/{document_id}/download
Accept: application/json
```

#### Response (200 OK)

```json
{
  "download_url": "https://stpdftohtml331ef3.blob.core.windows.net/converted/abc123/abc123.html?sv=...&sig=...",
  "filename": "annual-report-2024.html",
  "expires_at": "2026-06-15T11:00:00Z",
  "image_urls": [
    "https://stpdftohtml331ef3.blob.core.windows.net/converted/abc123/images/img-001.png?sv=...&sig=...",
    "https://stpdftohtml331ef3.blob.core.windows.net/converted/abc123/images/img-002.png?sv=...&sig=..."
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| download_url | string (URL) | SAS-signed URL to HTML file (60-min expiry) |
| filename | string | Suggested download filename |
| expires_at | string (ISO 8601) | SAS token expiration |
| image_urls | string[] | SAS-signed URLs to extracted images |

#### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Document not found | `{"error": "Document not found: {id}"}` |
| 404 | Output not found | `{"error": "Conversion output not found for document: {id}"}` |
| 409 | Still processing | `{"error": "Document is still processing"}` |

---

## Delete Single Document

```
DELETE /api/documents/{document_id}
Accept: application/json
```

#### Response (200 OK)

```json
{
  "message": "Document deleted successfully",
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

#### Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Document not found | `{"error": "Document not found: {id}"}` |
| 409 | Still processing | `{"error": "Cannot delete document while processing"}` |

---

## Delete All Documents

```
DELETE /api/documents
Accept: application/json
```

#### Response (200 OK)

```json
{
  "message": "All documents deleted",
  "deleted_input": 15,
  "deleted_output": 42
}
```

---

## Implementation Changes

| Aspect | Azure Functions | FastAPI |
|--------|----------------|---------|
| Download route | `@app.route(route="documents/{document_id}/download")` | `@router.get("/api/documents/{document_id}/download")` |
| Delete route | `@app.route(route="documents/{document_id}", methods=["DELETE"])` | `@router.delete("/api/documents/{document_id}")` |
| Delete all | `@app.route(route="documents", methods=["DELETE"])` | `@router.delete("/api/documents")` |
| Path param | `req.route_params.get("document_id")` | `document_id: str` (FastAPI path param) |

---

## Health Check (NEW)

### Liveness Probe

```
GET /health
```

#### Response (200 OK)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "storage": "ok",
    "queue": "ok"
  }
}
```

#### Response (503 Service Unavailable)

```json
{
  "status": "unhealthy",
  "checks": {
    "storage": "ok",
    "queue": "error: connection refused"
  }
}
```

### Readiness Probe

```
GET /ready
```

Returns 200 when the app is ready to accept traffic (storage connection
verified). Returns 503 during startup or if storage is unreachable.

| Aspect | Description |
|--------|-------------|
| Liveness path | `/health` — checks app is running |
| Readiness path | `/ready` — checks dependencies (storage, queue) |
| Container Apps config | `initialDelaySeconds: 5`, `periodSeconds: 10` |
| Failure threshold | 3 consecutive failures → restart (liveness) or remove from LB (readiness) |
