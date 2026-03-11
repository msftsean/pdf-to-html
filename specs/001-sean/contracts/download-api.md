# Download API Contract

**Endpoint**: `GET /api/documents/{document_id}/download`

Returns a download URL for the converted HTML and associated assets.

## Request

```
GET /api/documents/{document_id}/download
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| document_id | string (UUID) | The document identifier |

## Response (200 OK)

```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "annual-report-2024",
  "html_url": "https://<storage>.blob.core.windows.net/converted/annual-report-2024/annual-report-2024.html?sv=...",
  "preview_url": "https://<storage>.blob.core.windows.net/converted/annual-report-2024/annual-report-2024.html?sv=...",
  "assets": [
    {
      "filename": "page1_img1.png",
      "url": "https://<storage>.blob.core.windows.net/converted/annual-report-2024/images/page1_img1.png?sv=...",
      "size_bytes": 45678
    }
  ],
  "zip_url": "https://<storage>.blob.core.windows.net/converted/annual-report-2024/annual-report-2024.zip?sv=...",
  "wcag_compliant": true,
  "review_pages": [7, 15],
  "expires_at": "2026-03-11T23:00:00Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| html_url | string | SAS URL for the converted HTML file |
| preview_url | string | SAS URL for iframe preview (same as html_url) |
| assets | list | Individual image/asset files with SAS URLs |
| zip_url | string | SAS URL for packaged zip (HTML + images) |
| wcag_compliant | boolean | Whether output passes WCAG 2.1 AA |
| review_pages | list[int] | Pages flagged for human review |
| expires_at | datetime | When download URLs expire (1 hour) |

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 404 | Document not found | `{"error": "Document not found"}` |
| 409 | Not yet completed | `{"error": "Document is still processing", "status": "processing"}` |
| 410 | Output expired/deleted | `{"error": "Converted output has expired"}` |

## Preview Flow

1. Frontend calls `GET /api/documents/{id}/download`
2. Uses `preview_url` in an `<iframe>` for in-browser preview
3. Uses `zip_url` for the download button (HTML + all image assets)
