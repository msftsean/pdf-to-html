# API Contract: Upload SAS Token (FastAPI)

**Migrated from**: Azure Functions `generate_sas_token()` in `function_app.py`
**Contract status**: **Unchanged** — request/response schema identical

## Endpoint

```
POST /api/upload/sas-token
Content-Type: application/json
```

## Request

```json
{
  "filename": "annual-report-2024.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048576
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| filename | string | Yes | Extension must be `.pdf`, `.docx`, or `.pptx` |
| content_type | string | Yes | Must match extension MIME type |
| size_bytes | integer | Yes | Must be > 0 and ≤ 104,857,600 (100 MB) |

## Response (200 OK)

```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "upload_url": "https://stpdftohtml331ef3.blob.core.windows.net/files/a1b2c3d4.pdf?sv=2022-11-02&st=...&se=...&sr=b&sp=rcw&sig=...",
  "expires_at": "2026-06-15T10:15:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| document_id | string (UUID) | Unique document identifier |
| upload_url | string (URL) | SAS-signed blob URL (15-min expiry, read/create/write) |
| expires_at | string (ISO 8601) | SAS token expiration time |

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Missing required fields | `{"error": "Missing required fields: filename, content_type, size_bytes"}` |
| 400 | Invalid file extension | `{"error": "Unsupported file type: .xyz. Allowed: .pdf, .docx, .pptx"}` |
| 400 | File too large | `{"error": "File size exceeds 100MB limit"}` |
| 500 | Storage error | `{"error": "Failed to generate upload URL"}` |

## Implementation Change

| Aspect | Azure Functions | FastAPI |
|--------|----------------|---------|
| Decorator | `@app.route(route="upload/sas-token", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)` | `@router.post("/api/upload/sas-token")` |
| Request parsing | `req.get_json()` | `request: SasTokenRequest` (Pydantic model) |
| Response | `func.HttpResponse(json.dumps(data), status_code=200, mimetype="application/json")` | `return JSONResponse(content=data)` |
| Blob client | `_get_blob_service_client()` (reads connection string) | Injected via `Depends(get_blob_service)` |

## Side Effects

1. Creates a 0-byte placeholder blob at `files/{document_id}.{ext}` with metadata:
   - `document_id`, `name`, `format`, `size_bytes`, `status=pending`, `upload_timestamp`
2. Sets blob content type to match the uploaded file

## Notes

- Frontend uploads the file directly to the SAS URL (browser → Azure Blob Storage)
- The 0-byte placeholder is overwritten by the actual file upload via PUT
- Event Grid `BlobCreated` fires on the PUT (not the placeholder creation) — filter `contentLength > 0` ensures this
