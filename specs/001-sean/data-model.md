# Data Model: WCAG-Compliant Document-to-HTML Converter

**Phase 1 Output** | **Date**: 2026-03-11

## Entities

### Document

Represents an input file uploaded for conversion.

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Unique document identifier |
| name | string | Original filename without extension |
| format | enum | `pdf`, `docx`, `pptx` |
| size_bytes | integer | File size in bytes |
| upload_timestamp | datetime | When the file was uploaded |
| status | enum | `pending`, `processing`, `completed`, `failed` |
| error_message | string (nullable) | Error description if status is `failed` |
| page_count | integer (nullable) | Total pages/slides (set after extraction) |
| pages_processed | integer | Pages processed so far (for progress) |
| has_review_flags | boolean | True if any page flagged for human review |
| blob_path | string | Path in `files/` container |
| output_path | string (nullable) | Path in `converted/` container |

**State transitions**:
```
pending → processing → completed
                    → failed (retryable)
```

**Validation rules**:
- `format` must be one of: pdf, docx, pptx
- `size_bytes` must be > 0 and ≤ 100MB (web UI limit)
- `name` must not be empty

### PageResult

Represents extracted content from a single page or slide.

| Field | Type | Description |
|-------|------|-------------|
| page_number | integer | 1-based page/slide index |
| source_type | enum | `digital`, `scanned`, `mixed` |
| text_spans | list[TextSpan] | Extracted text with formatting |
| tables | list[TableData] | Extracted table structures |
| images | list[ImageInfo] | Extracted images with metadata |
| ocr_confidence | float (nullable) | OCR confidence score (0-1) if OCR was used |
| needs_review | boolean | True if OCR confidence < 0.70 |
| extraction_method | enum | `direct`, `ocr`, `hybrid` |

### TextSpan

Represents a unit of text with positioning and formatting.

| Field | Type | Description |
|-------|------|-------------|
| text | string | The text content |
| x0, y0, x1, y1 | float | Bounding box coordinates |
| font_name | string | Font family name |
| font_size | float | Font size in points |
| is_bold | boolean | Bold formatting flag |
| is_italic | boolean | Italic formatting flag |
| color | string | Text color (hex) |

### TableData

Represents a structured table extracted from a document.

| Field | Type | Description |
|-------|------|-------------|
| rows | list[list[CellData]] | 2D array of cell content |
| has_header | boolean | Whether first row is a header |
| row_count | integer | Number of rows |
| col_count | integer | Number of columns |
| bounding_box | tuple | Position on page (x0, y0, x1, y1) |

### CellData

| Field | Type | Description |
|-------|------|-------------|
| text | string | Cell text content |
| is_header | boolean | Whether this cell is a header |
| rowspan | integer | Number of rows this cell spans |
| colspan | integer | Number of columns this cell spans |
| scope | string (nullable) | `col`, `row`, or null |

### ImageInfo

| Field | Type | Description |
|-------|------|-------------|
| image_bytes | bytes | Raw image data |
| format | string | Image format (png, jpeg, etc.) |
| alt_text | string | Generated alt text |
| width | integer | Image width in pixels |
| height | integer | Image height in pixels |
| page_position | tuple | Position on page (x0, y0, x1, y1) |

### ConversionResult

Represents the output of a document conversion.

| Field | Type | Description |
|-------|------|-------------|
| document_id | string | Reference to source Document |
| html_content | string | Generated WCAG-compliant HTML |
| image_assets | list[ImageAsset] | Extracted image files |
| wcag_violations | list[WcagViolation] | axe-core validation results |
| is_compliant | boolean | True if zero critical WCAG violations |
| review_pages | list[integer] | Page numbers flagged for human review |
| processing_time_ms | integer | Total conversion time |

### WcagViolation

| Field | Type | Description |
|-------|------|-------------|
| rule_id | string | axe-core rule identifier |
| severity | enum | `critical`, `serious`, `moderate`, `minor` |
| description | string | Human-readable violation description |
| html_element | string | The offending HTML snippet |
| help_url | string | Link to remediation guidance |

## Relationships

```
Document 1 ──→ * PageResult       (one document has many pages)
PageResult 1 ──→ * TextSpan       (one page has many text spans)
PageResult 1 ──→ * TableData      (one page has many tables)
PageResult 1 ──→ * ImageInfo      (one page has many images)
Document 1 ──→ 1 ConversionResult (one document produces one result)
ConversionResult 1 ──→ * WcagViolation (result may have violations)
```
