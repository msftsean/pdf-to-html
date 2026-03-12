# Copilot Instructions

## Build & Test Commands

### Backend (Python 3.12)

```bash
pip install -r requirements.txt

# All backend tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Single test file
pytest tests/unit/test_wcag_validator.py -v

# Single test by keyword
pytest tests/ -k "test_heading_order" -v

# With coverage
pytest tests/ -v --cov=. --cov-report=html

# Integration tests (requires Azurite running)
pytest tests/integration/ -v
```

### Frontend (Next.js 14 / React 18)

```bash
cd frontend
npm install
npm run lint          # ESLint
npm run build         # TypeScript check + production build
npm test              # Jest suite
npm run test:a11y     # Accessibility tests (jest-axe)
```

### WCAG Evaluation Suite (runs on every PR)

```bash
python scripts/run_evals.py --output tests/eval/results/eval-report.json
python scripts/render_report.py --input tests/eval/results/eval-report.json --output tests/eval/results/eval-report.md
```

### Local Development

Requires three processes: Azurite (blob emulator on :10000), Azure Functions (`func start` on :7071), and Next.js (`npm run dev` on :3000). See `docs/QUICKSTART.md` for full setup.

## Architecture

This is a **stateless, blob-triggered document conversion pipeline** deployed as Azure Functions. There is no database — Azure Blob Storage metadata is the sole persistence layer for document status.

### Conversion Pipeline

1. **Upload**: Frontend requests a SAS token (`POST /api/upload/sas-token`), then uploads directly to blob storage (bypasses the 100MB Functions limit)
2. **Blob trigger** (`function_app.py:file_upload`): Fires on new blobs in the `files/` container
3. **Extraction**: Format-specific extractor runs → returns `list[PageResult]`
4. **OCR**: Scanned pages (text < 20 chars) are sent to Azure Document Intelligence
5. **HTML generation**: `backend.html_builder.build_html()` produces WCAG 2.1 AA compliant HTML
6. **Validation**: `backend.wcag_validator.validate_html()` runs 7 server-side compliance checks
7. **Output**: HTML + image assets stored to `converted/` container; status written as blob metadata

### Extractor Interface

All three extractors (in `backend/`) share the same function signature and return type — `html_builder` is format-agnostic:

```python
def extract_pdf(file_data: bytes) -> tuple[list[PageResult], dict]:
def extract_docx(file_data: bytes) -> tuple[list[PageResult], dict]:
def extract_pptx(file_data: bytes) -> tuple[list[PageResult], dict]:
```

`PageResult` is the universal intermediate representation (text spans, images, tables per page). DOCX returns a single virtual page; PPTX returns one page per slide.

### Frontend

Next.js 14 App Router with NCDIT Digital Commons branding (Bootstrap 5). Uploads go through SAS token → direct blob upload via `XMLHttpRequest` (for progress tracking). Status polling hits `GET /api/documents/status`. Download URLs are SAS-signed.

## Key Conventions

### Python

- **Type hints everywhere**: Use `list[...]`, `dict[..., ...]`, `str | None` (not `Optional`). All function signatures are typed.
- **Logging**: Use `logging.getLogger(__name__)` with format-string style (`logger.info("Processing %s", name)`), not f-strings.
- **Error handling**: Catch specific Azure exceptions (`ServiceRequestError`, `HttpResponseError`). OCR failures return stub results with `confidence=0.0, needs_review=True` rather than crashing the pipeline.
- **Private functions**: Prefixed with `_` (e.g., `_get_blob_service_client()`).
- **Constants**: Module-level `UPPER_CASE` with `_` prefix for internal ones.
- **Data models**: Pydantic-style dataclasses in `backend/models.py`. Import shared types (`PageResult`, `TextSpan`, `ImageInfo`, `TableData`) from `backend.models`, not directly from extractors.
- **Test organization**: Class-based grouping (`class TestDocument:`, `class TestHeadingOrder:`).

### TypeScript / React

- **Components**: PascalCase files in `frontend/components/`. Use `'use client'` directive for interactive components.
- **Services**: `frontend/services/` contains API client modules (`uploadService.ts`, `statusService.ts`, `downloadService.ts`).
- **Path aliases**: Import with `@/` prefix (e.g., `@/services/uploadService`).

### WCAG Compliance

This project enforces WCAG 2.1 Level AA as a hard requirement. All generated HTML must include:
- `lang` attribute on `<html>`
- Skip navigation link + `id="main-content"`
- Heading hierarchy with no skipped levels (auto-corrected by `html_builder`)
- `<th scope="col|row">` on all data tables
- `alt` text on all images (unless `role="presentation"`)
- 4.5:1 color contrast ratio for normal text, 3:1 for large text

The WCAG validator (`wcag_validator.py`) runs server-side before output; `jest-axe` validates the frontend.

### Squad Agents

This project uses Squad (Justice League theme) for AI-assisted development. Agent charters are in `.squad/agents/`. Key agents: Batman (tech lead/triage), Wonder-Woman (backend/TDD), Flash (frontend), Cyborg (DevOps), Aquaman (QA). Copilot Coding Agents are configured in `.github/agents/`.

### Spec Kit

Feature specifications live in `specs/` with numbered subdirectories:
- `specs/001-sean/` — WCAG Document-to-HTML Converter (core pipeline, spec, plan, tasks, contracts, research, data model)
- `specs/002-classification-engine/` — Document Classification Engine (pre-processing gate, heuristic classification, warning UX)
- `specs/004-container-apps-migration/` — Azure Container Apps Migration (FastAPI backend, KEDA queue worker, docker-compose local dev)

The project constitution is at `pdf-to-html/.specify/memory/constitution.md`.

### Container Apps Migration (004)

The migration from Azure Functions to Azure Container Apps introduces:

- **Backend**: `app/main.py` (FastAPI + Uvicorn replacing `function_app.py`), `app/worker.py` (queue consumer replacing blob trigger)
- **Infrastructure**: Event Grid → Storage Queue → KEDA scaler pattern for file processing
- **Local dev**: `docker-compose.yml` with Azurite, backend, worker, and frontend services
- **Containers**: `Dockerfile.backend` (Python 3.12-slim), `frontend/Dockerfile` (Node 20 Alpine multi-stage)
- **IaC**: `infra/` directory with Bicep modules for Container Apps, ACR, Event Grid
- **Key principle**: `backend/` package is completely unchanged — zero Azure Functions SDK dependencies exist in it
- **API contracts**: All HTTP endpoints maintain identical request/response schemas
- **Dependencies changed**: `requirements.txt` adds `fastapi`, `uvicorn`, `azure-storage-queue`; removes `azure-functions`

### Document Classification Engine (002)

The classification engine is a **pre-processing gate** that analyzes documents before conversion begins. Key design decisions:

- **Module**: `classification_service.py` — standalone, independently testable, no Azure Functions runtime dependency
- **Entry point**: `classify_document(file_data: bytes, file_extension: str) -> DocumentClassification`
- **Data model**: `DocumentClassification` dataclass in `models.py` with `document_type`, `suitability_score`, `confidence`, `warning_message`, `metadata`
- **Document types**: `report`, `whitepaper`, `form`, `brochure`, `newsletter`, `slide_deck`, `unknown` (enum `DocumentType`)
- **Heuristic signals**: text density (0.35 weight), image ratio (0.30), object count (0.20), page uniformity (0.15)
- **Threshold**: 0.70 suitability score — below triggers a warning, never blocks conversion
- **Storage**: Classification results stored as blob metadata (same pattern as `status_service.py`)
- **Integration**: Runs in `function_app.py` after password check, before extraction; wrapped in try/except for graceful degradation
- **Frontend**: `ClassificationWarning.tsx` component renders warnings in the status dashboard
