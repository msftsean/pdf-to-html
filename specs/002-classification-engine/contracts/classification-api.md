# Classification API Contract

**Module**: `classification_service.py`

This is a **Python module contract** — the classification service is an
internal module called by `function_app.py`, not an HTTP endpoint. Phase 1
has no new HTTP APIs; classification results are exposed through the existing
status API via blob metadata.

## Public Function: `classify_document`

```python
def classify_document(
    file_data: bytes,
    file_extension: str,
) -> DocumentClassification:
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_data` | bytes | Yes | Raw file content (already read from blob) |
| `file_extension` | string | Yes | File extension including dot (`.pdf`, `.docx`, `.pptx`) |

### Return Value

Returns a `DocumentClassification` dataclass:

```python
@dataclass
class DocumentClassification:
    document_type: str        # e.g., "report", "brochure", "slide_deck"
    suitability_score: float  # 0.0–1.0
    confidence: float         # 0.0–1.0
    warning_message: str | None
    metadata: dict[str, Any]
```

### Behavior

1. Opens the document using the format-appropriate library:
   - `.pdf` → PyMuPDF (`fitz.open`)
   - `.docx` → python-docx (`Document()`)
   - `.pptx` → python-pptx (`Presentation()`)
2. Computes heuristic signals (text density, image ratio, object count,
   page uniformity)
3. Calculates weighted suitability score
4. Matches document type from type rules
5. Generates warning message if score < `SUITABILITY_THRESHOLD` (0.70)
6. Returns `DocumentClassification` with all fields populated

### Error Handling

- If the document cannot be opened or analyzed, the function logs a warning
  and returns a **safe default**:
  ```python
  DocumentClassification(
      document_type="unknown",
      suitability_score=0.50,
      confidence=0.0,
      warning_message=None,
      metadata={"classification_engine": "heuristic_v1", "error": str(e)},
  )
  ```
- The caller (`function_app.py`) wraps the call in try/except and proceeds
  normally if classification fails.

### Thread Safety

The function is stateless and re-entrant. No module-level mutable state.
Safe for concurrent Azure Functions invocations.

## Internal Functions

### `_classify_pdf(file_data: bytes) -> DocumentClassification`

PDF-specific classification using PyMuPDF.

### `_classify_docx(file_data: bytes) -> DocumentClassification`

DOCX-specific classification using python-docx.

### `_classify_pptx(file_data: bytes) -> DocumentClassification`

PPTX-specific classification using python-pptx.

### `_compute_suitability_score(signals: dict[str, float]) -> float`

Compute weighted suitability score from normalized heuristic signals.

### `_determine_document_type(signals: dict[str, float], score: float) -> tuple[str, float]`

Match signals against type rules to determine document type and confidence.

### `_generate_warning(document_type: str, score: float) -> str | None`

Generate type-specific warning message if score < threshold.

## Constants

```python
SUITABILITY_THRESHOLD: float = 0.70
HEURISTIC_WEIGHTS: dict[str, float] = {
    "text_density": 0.35,
    "image_ratio": 0.30,
    "object_count": 0.20,
    "page_uniformity": 0.15,
}
WARNING_TEMPLATES: dict[str, str]  # Per-type warning message templates
```

## Usage in function_app.py

```python
# After password protection check, before extraction:
try:
    from classification_service import classify_document
    classification = classify_document(file_data, ext)

    # Store in blob metadata
    if blob_service:
        status_service.set_classification(
            blob_service, document_id,
            classification_type=classification.document_type,
            suitability_score=classification.suitability_score,
            classification_confidence=classification.confidence,
            classification_warning=classification.warning_message or "",
            classification_engine=classification.metadata.get(
                "classification_engine", "heuristic_v1"
            ),
        )
except Exception:
    logger.warning("Classification failed for %s — proceeding without",
                   blob_name)

# Proceed to extraction (unchanged)
```
