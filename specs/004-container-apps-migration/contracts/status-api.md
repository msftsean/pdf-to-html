# API Contract: Document Status (FastAPI)

**Migrated from**: Azure Functions `get_document_status()` in `function_app.py`
**Contract status**: **Unchanged** — request/response schema identical

## Endpoints

### List All Documents

```
GET /api/documents/status
Accept: application/json
```

#### Response (200 OK)

```json
{
  "documents": [
    {
      "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "annual-report-2024",
      "format": "pdf",
      "status": "completed",
      "size_bytes": 2048576,
      "page_count": 42,
      "pages_processed": 42,
      "has_review_flags": true,
      "review_pages": [3, 17],
      "processing_time_ms": 15200,
      "is_compliant": true,
      "error_message": null,
      "upload_timestamp": "2026-06-15T10:00:00Z"
    }
  ],
  "summary": {
    "total": 5,
    "pending": 1,
    "processing": 1,
    "completed": 2,
    "failed": 1
  }
}
```

### Get Single Document Status

```
GET /api/documents/status?document_id={uuid}
Accept: application/json
```

#### Response (200 OK)

Same schema as single entry in `documents[]` above, wrapped in an object:

```json
{
  "document_id": "a1b2c3d4",
  "name": "annual-report-2024",
  "format": "pdf",
  "status": "processing",
  "page_count": null,
  "pages_processed": 0,
  "has_review_flags": false,
  "review_pages": [],
  "processing_time_ms": null,
  "is_compliant": null,
  "error_message": null,
  "upload_timestamp": "2026-06-15T10:00:00Z"
}
```

#### Response (404 Not Found)

```json
{
  "error": "Document not found: a1b2c3d4"
}
```

## Document Status Fields

| Field | Type | Description |
|-------|------|-------------|
| document_id | string | UUID identifier |
| name | string | Original filename (no extension) |
| format | string | pdf, docx, pptx |
| status | enum | pending, processing, completed, failed |
| size_bytes | integer | File size in bytes |
| page_count | integer \| null | Total pages (set after extraction) |
| pages_processed | integer | Pages processed so far |
| has_review_flags | boolean | True if any OCR page needs review |
| review_pages | integer[] | Page numbers needing review |
| processing_time_ms | integer \| null | Total processing time |
| is_compliant | boolean \| null | WCAG 2.1 AA compliance result |
| error_message | string \| null | Error description if failed |
| upload_timestamp | string | ISO 8601 upload time |

## Implementation Change

| Aspect | Azure Functions | FastAPI |
|--------|----------------|---------|
| Decorator | `@app.route(route="documents/status", methods=["GET"])` | `@router.get("/api/documents/status")` |
| Query param | `req.params.get("document_id")` | `document_id: Optional[str] = Query(None)` |
| Response | `func.HttpResponse(json.dumps(data))` | `return JSONResponse(content=data)` |

## Notes

- Frontend polls this endpoint every 3 seconds during active processing
- Status is read from blob metadata in `files/` container (no database)
- Performance is O(n) for list (scans all blobs); acceptable for < 1,000 documents
