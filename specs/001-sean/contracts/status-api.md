# Status API Contract

**Endpoint**: `GET /api/documents/status`

Returns processing status for all documents or a specific document.

## List All Documents

```
GET /api/documents/status
```

### Response (200 OK)

```json
{
  "documents": [
    {
      "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "annual-report-2024",
      "format": "pdf",
      "status": "completed",
      "page_count": 24,
      "pages_processed": 24,
      "has_review_flags": true,
      "review_pages": [7, 15],
      "processing_time_ms": 18500,
      "is_compliant": true,
      "error_message": null,
      "upload_timestamp": "2026-03-11T20:00:00Z"
    },
    {
      "document_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "name": "budget-summary",
      "format": "docx",
      "status": "processing",
      "page_count": 10,
      "pages_processed": 6,
      "has_review_flags": false,
      "review_pages": [],
      "processing_time_ms": null,
      "is_compliant": null,
      "error_message": null,
      "upload_timestamp": "2026-03-11T20:05:00Z"
    }
  ],
  "summary": {
    "total": 15,
    "pending": 3,
    "processing": 2,
    "completed": 9,
    "failed": 1
  }
}
```

## Get Single Document

```
GET /api/documents/status/{document_id}
```

### Response (200 OK)

Same shape as a single item from the `documents` array above.

### Response (404 Not Found)

```json
{
  "error": "Document not found"
}
```

## Polling Guidance

Frontend should poll this endpoint every 3-5 seconds while documents are in
`pending` or `processing` status. Stop polling when all documents reach a
terminal state (`completed` or `failed`).
