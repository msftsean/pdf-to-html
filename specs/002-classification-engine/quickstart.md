# Quickstart: Document Classification Engine

## Prerequisites

Same as the base project:
- Python 3.12+
- Node.js 20+ (for frontend warning component)
- Azure Functions Core Tools v4
- Azurite (local blob storage)

No new Azure services required for Phase 1 (heuristic classification).

## What This Feature Adds

A pre-processing classification step that analyzes uploaded documents before
conversion begins. The classifier:

1. Opens the document and computes structural metrics (text density, image
   ratio, object count, page uniformity)
2. Classifies the document type (report, brochure, form, slide deck, etc.)
3. Computes a suitability score (0.0–1.0) for HTML conversion
4. Stores classification results in blob metadata
5. If suitability score <0.70, generates a user-facing warning (but always
   proceeds with conversion)

## New/Modified Files

| File | Status | Purpose |
|------|--------|---------|
| `classification_service.py` | **NEW** | Heuristic classification engine |
| `models.py` | Modified | `DocumentClassification` dataclass, `DocumentType` enum |
| `function_app.py` | Modified | Classification gate between validation and extraction |
| `status_service.py` | Modified | Warning message support |
| `frontend/src/components/ClassificationWarning.tsx` | **NEW** | Warning banner UI |
| `frontend/src/services/statusService.ts` | Modified | Parse classification fields |
| `tests/unit/test_classification_service.py` | **NEW** | Heuristic rule tests |
| `tests/unit/test_models_classification.py` | **NEW** | Data model tests |
| `tests/integration/test_classification_pipeline.py` | **NEW** | End-to-end pipeline |

## Running the Classification Service

### Standalone Testing

```bash
cd /workspaces/pdf-to-html

# Run classification tests
pytest tests/unit/test_classification_service.py -v

# Run data model tests
pytest tests/unit/test_models_classification.py -v

# Run integration tests (requires Azurite)
pytest tests/integration/test_classification_pipeline.py -v
```

### Manual Classification (Python REPL)

```python
from classification_service import classify_document

# Classify a PDF file
with open("tests/fixtures/sample-digital.pdf", "rb") as f:
    result = classify_document(f.read(), ".pdf")

print(f"Type: {result.document_type}")
print(f"Score: {result.suitability_score:.2f}")
print(f"Warning: {result.warning_message or 'None'}")
print(f"Metadata: {result.metadata}")
```

### Pipeline Integration

The classification gate fires automatically when a document is uploaded
to the `files/` blob container. No manual invocation needed.

```bash
# Start the local environment
azurite-blob --silent &
func start

# Upload a test document — classification runs automatically
az storage blob upload \
  --container-name files \
  --file tests/fixtures/sample-digital.pdf \
  --name test-report.pdf \
  --connection-string "UseDevelopmentStorage=true"

# Check classification results in blob metadata
az storage blob metadata show \
  --container-name files \
  --name test-report.pdf \
  --connection-string "UseDevelopmentStorage=true" \
  --output table
```

Expected metadata output includes:
```
classification_type       : report
suitability_score         : 0.87
classification_confidence : 0.91
classification_warning    :
classification_engine     : heuristic_v1
```

### Frontend Warning Display

```bash
cd frontend
npm install
npm run dev
```

Upload a brochure-style PDF through the web UI at http://localhost:3000.
The dashboard will display a warning banner with the classification message
and suitability score.

## Architecture Overview

```
                    ┌─────────────────┐
                    │  Blob Upload    │
                    │  (files/{name}) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Validation     │
                    │  (format, size, │
                    │   password)     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
              NEW → │ Classification  │ ← <100ms heuristic
                    │ (type, score,   │
                    │  warning)       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Store metadata │
                    │  (blob tags)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Extraction     │
                    │  (PDF/DOCX/PPTX)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  OCR (if needed)│
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  HTML Build     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  WCAG Validate  │
                    └─────────────────┘
```

## Tuning Thresholds

The warning threshold and heuristic weights are defined as constants in
`classification_service.py`:

```python
SUITABILITY_THRESHOLD = 0.70  # Below this → generate warning

HEURISTIC_WEIGHTS = {
    "text_density": 0.35,
    "image_ratio": 0.30,
    "object_count": 0.20,
    "page_uniformity": 0.15,
}
```

Adjust these values and re-run tests to calibrate for the NC state document
corpus. See `research.md` R2 for rationale behind default values.
