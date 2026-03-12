# Data Model: Document Classification Engine

**Phase 1 Output** | **Date**: 2026-03-12

## New Entities

### DocumentClassification

Represents the classification result for a single document, produced by the
classification engine before extraction begins.

| Field | Type | Description |
|-------|------|-------------|
| document_type | string (enum) | Classified document type: `report`, `whitepaper`, `form`, `brochure`, `newsletter`, `slide_deck`, `unknown` |
| suitability_score | float | HTML conversion suitability (0.0–1.0, where ≥0.70 = good) |
| confidence | float | Confidence in the classification itself (0.0–1.0) |
| warning_message | string (nullable) | User-facing warning if suitability_score <0.70; null if suitable |
| metadata | dict[str, Any] | Engine-specific analysis data (see Metadata Fields below) |

**Validation rules**:
- `document_type` must be one of the 7 defined types
- `suitability_score` must be in range [0.0, 1.0]
- `confidence` must be in range [0.0, 1.0]
- `warning_message` must be non-empty if `suitability_score < 0.70`
- `warning_message` must be null/None if `suitability_score >= 0.70`

**Metadata Fields** (stored in `metadata` dict):

| Key | Type | Description |
|-----|------|-------------|
| `page_count` | int | Number of pages in the document |
| `avg_text_density` | float | Average characters per unit page area |
| `avg_image_ratio` | float | Average image area / page area |
| `avg_object_count` | float | Average drawings + annotations per page |
| `text_density_std` | float | Standard deviation of text density across pages |
| `classification_engine` | string | Engine that produced the result (e.g., `heuristic_v1`) |
| `classification_time_ms` | int | Time taken for classification in milliseconds |

### DocumentType (Enum)

New enum for document type classification.

| Value | Description |
|-------|-------------|
| `report` | Text-heavy document with structured headings |
| `whitepaper` | Similar to report, may have more figures |
| `form` | Document with field layouts, checkboxes |
| `brochure` | Image-heavy, multi-column visual layout |
| `newsletter` | Mixed content with varied layouts |
| `slide_deck` | Presentation with low text density |
| `unknown` | Could not be classified with confidence |

## Modified Entities

### Document (existing — `models.py`)

Add optional classification fields to the existing `Document` dataclass:

| New Field | Type | Description |
|-----------|------|-------------|
| classification_type | string (nullable) | Classified document type (from DocumentType enum) |
| suitability_score | float (nullable) | HTML suitability score (0.0–1.0) |
| classification_warning | string (nullable) | Warning message if score <0.70 |

These fields are persisted as blob metadata (extending `to_metadata()` and
`from_metadata()`).

### Status API Response (existing — `status_service.py`)

The `to_dict()` serialisation includes the new classification fields so
the frontend can display warnings without API changes:

```json
{
  "document_id": "...",
  "classification_type": "brochure",
  "suitability_score": 0.32,
  "classification_warning": "This document appears to be a brochure..."
}
```

## Relationships

```
Document 1 ──→ 0..1 DocumentClassification  (one document may have one classification)
```

The relationship is **optional** because:
- Existing documents processed before this feature have no classification
- Classification failures result in null classification (graceful degradation)
- The `DocumentClassification` is computed at runtime and stored as fields
  on the `Document` blob metadata — not as a separate entity

## State Transitions

Classification does NOT affect the document status state machine. The
existing state transitions remain:

```
pending → processing → completed
                    → failed (retryable)
```

Classification runs during the `processing` state, after validation but
before extraction. If a warning is generated, it is stored in metadata but
does not change the status to `failed`.

## Blob Metadata Schema Extension

Current metadata keys (from `Document.to_metadata()`):
```
name, format, size_bytes, upload_timestamp, status, error_message,
page_count, pages_processed, has_review_flags, blob_path, output_path,
review_pages, processing_time_ms, is_compliant
```

New metadata keys (added by classification):
```
classification_type       # "report", "brochure", etc.
suitability_score         # "0.85" (string representation of float)
classification_confidence # "0.92"
classification_warning    # "This document appears to be..." or ""
classification_engine     # "heuristic_v1"
```

## Heuristic Scoring Model

The classification service computes scores using a weighted sum of normalized
heuristic signals:

```python
HEURISTIC_WEIGHTS = {
    "text_density": 0.35,      # High text density → high suitability
    "image_ratio": 0.30,       # High image ratio → low suitability (inverted)
    "object_count": 0.20,      # High object count → low suitability (inverted)
    "page_uniformity": 0.15,   # Low std dev → high suitability
}

# Normalization: each signal mapped to [0.0, 1.0] via clamp + linear scale
# Final score = weighted sum of normalized signals
# Document type = highest-confidence rule match from type_rules table
```

## Warning Message Templates

| Document Type | Warning Message |
|---------------|----------------|
| `brochure` | "This document appears to be a brochure. Brochures rely on visual layout and multi-column designs that may not translate well to linear HTML. The converted output will preserve text content but may lose visual formatting. Suitability score: {score}/1.0." |
| `slide_deck` | "This document appears to be a slide deck or presentation. Slide layouts with positioned elements and heavy imagery may not map well to semantic HTML. Consider keeping the original format for visual fidelity. Suitability score: {score}/1.0." |
| `form` | "This document appears to be a form. Form field layouts and spatial relationships may not be fully preserved in HTML conversion. Interactive form elements will appear as static content. Suitability score: {score}/1.0." |
| `newsletter` | "This document appears to be a newsletter. Newsletter layouts with mixed columns, images, and design elements may not fully translate to HTML. Text content will be preserved. Suitability score: {score}/1.0." |

No warning is generated for `report`, `whitepaper`, or `unknown` types
when suitability score is ≥0.70.

## Test Cases

| # | Input | Expected Classification | Expected Score Range | Warning? |
|---|-------|------------------------|---------------------|----------|
| 1 | 20-page text-heavy report PDF | `report` | 0.85–1.0 | No |
| 2 | 4-page image-heavy brochure PDF | `brochure` | 0.15–0.40 | Yes |
| 3 | 10-page government form PDF | `form` | 0.40–0.65 | Yes |
| 4 | 30-slide presentation PPTX | `slide_deck` | 0.20–0.45 | Yes |
| 5 | 15-page mixed-content newsletter PDF | `newsletter` | 0.30–0.55 | Yes |
| 6 | Standard .docx with headings | `report` | 0.80–0.95 | No |
| 7 | Empty/blank PDF (0 text, 0 images) | `unknown` | 0.50 | No |
| 8 | Single-page text PDF | `report` | 0.85–1.0 | No |
| 9 | PDF with exactly 0.70 score | (any) | 0.70 | No |
| 10 | PDF with 0.69 score | (any) | 0.69 | Yes |
| 11 | Classification service throws exception | N/A | N/A | No (graceful skip) |
| 12 | Password-protected PDF (rejected before classification) | N/A | N/A | N/A |
| 13 | Scanned text-heavy report (image-only but text-dense via OCR history) | `report` | 0.70–0.85 | No |
| 14 | Mixed PDF: 50% report pages, 50% brochure pages | `unknown` or `report` | 0.55–0.70 | Maybe |
