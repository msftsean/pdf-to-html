# Status API Extension Contract

**Extends**: `/specs/001-sean/contracts/status-api.md`

The existing Status API (`GET /api/documents/status`) is extended with
classification fields. No new endpoints are added — the classification data
flows through the existing blob metadata → status API response pipeline.

## Extended Response Fields

The document object in the status API response gains three new optional
fields:

```json
{
  "document_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "agency-brochure-2024",
  "format": "pdf",
  "status": "completed",
  "classification_type": "brochure",
  "suitability_score": 0.32,
  "classification_warning": "This document appears to be a brochure. Brochures rely on visual layout and multi-column designs that may not translate well to linear HTML. The converted output will preserve text content but may lose visual formatting. Suitability score: 0.32/1.0.",
  "page_count": 4,
  "pages_processed": 4,
  "has_review_flags": false,
  "review_pages": [],
  "processing_time_ms": 2100,
  "is_compliant": true,
  "error_message": null,
  "upload_timestamp": "2026-03-12T14:00:00Z"
}
```

### New Fields

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `classification_type` | string | Yes | Document type (e.g., `report`, `brochure`, `slide_deck`). Null if classification was not performed. |
| `suitability_score` | float | Yes | HTML conversion suitability (0.0–1.0). Null if classification was not performed. |
| `classification_warning` | string | Yes | User-facing warning message. Null/empty if score ≥0.70 or classification not performed. |

### Backwards Compatibility

- All three fields are **optional** (nullable). Existing clients that don't
  read these fields are unaffected.
- Documents processed before the classification feature was deployed will
  have `null` for all three fields.
- The `summary` object in the list response is unchanged.

## status_service.py Extension

### New Function: `set_classification`

```python
def set_classification(
    blob_service: BlobServiceClient,
    document_id: str,
    *,
    classification_type: str,
    suitability_score: float,
    classification_confidence: float,
    classification_warning: str,
    classification_engine: str,
) -> None:
```

Writes classification metadata fields to the document's blob. Follows the
same pattern as `set_status()` — reads existing metadata, merges new fields,
writes back.

### Modified Function: `get_status` / `get_all_statuses`

These functions already read blob metadata and return `Document` objects.
The `Document.from_metadata()` and `Document.to_dict()` methods are extended
to include the new classification fields automatically.

## Frontend Integration

The `statusService.ts` polling response parser is extended to read the new
fields:

```typescript
interface DocumentStatus {
  // ... existing fields ...
  classification_type?: string;
  suitability_score?: number;
  classification_warning?: string;
}
```

The `ClassificationWarning.tsx` component renders the warning when
`classification_warning` is non-null and non-empty:

```tsx
{doc.classification_warning && (
  <ClassificationWarning
    type={doc.classification_type}
    score={doc.suitability_score}
    message={doc.classification_warning}
  />
)}
```
