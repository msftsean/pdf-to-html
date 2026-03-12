# Upload API Contract

**Endpoint**: `POST /api/upload/sas-token`

Generates a short-lived SAS token for direct browser-to-blob upload.

## Request

```
POST /api/upload/sas-token
Content-Type: application/json

{
  "filename": "annual-report-2024.pdf",
  "content_type": "application/pdf",
  "size_bytes": 2048576
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| filename | string | Yes | Original filename with extension |
| content_type | string | Yes | MIME type of the file |
| size_bytes | integer | Yes | File size in bytes |

### Validation

- `filename` extension must be one of: `.pdf`, `.docx`, `.pptx`
- `size_bytes` must be ≤ 104857600 (100MB)
- `content_type` must match extension

## Response (200 OK)

```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "upload_url": "https://<storage>.blob.core.windows.net/files/a1b2c3d4.pdf?sv=...",
  "expires_at": "2026-03-11T22:00:00Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| document_id | string | Assigned document ID for status tracking |
| upload_url | string | SAS-token URL for direct PUT upload |
| expires_at | datetime | Token expiration (15 minutes from creation) |

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Unsupported file type | `{"error": "Unsupported format. Accepted: .pdf, .docx, .pptx"}` |
| 400 | File too large | `{"error": "File exceeds 100MB limit"}` |
| 500 | Storage unavailable | `{"error": "Storage service unavailable. Please retry."}` |

## Upload Flow

1. Frontend calls `POST /api/upload/sas-token` with file metadata
2. Backend validates, creates document record (status: `pending`), generates SAS
3. Frontend uploads file directly to blob storage using the SAS URL
4. Blob trigger fires, updates status to `processing`, begins conversion
