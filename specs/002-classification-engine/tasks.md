# Tasks: Document Classification Engine

**Input**: Design documents from `/specs/002-classification-engine/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md
**ADR**: `.squad/decisions/inbox/batman-classification-engine.md`
**Scope**: Phase 1 only — heuristic classification (no ML model, no user feedback collection)

**Tests**: Included — plan.md Constitution VII mandates test-first development and the project structure explicitly lists test files.

**Note**: No `spec.md` exists for this feature. User stories are derived from plan.md, research.md, contracts, and the originating ADR.

**Organization**: Tasks are grouped into three user stories derived from the feature design:

| Story | Title | Priority | Source |
|-------|-------|----------|--------|
| US1 | Heuristic Classification Engine | P1 (MVP) | plan.md §Summary, research.md R1–R7, contracts/classification-api.md |
| US2 | Pipeline Integration & Metadata Persistence | P2 | plan.md §Project Structure, research.md R4+R8, contracts/status-api-extension.md |
| US3 | Frontend Warning Display | P3 | plan.md §Project Structure, research.md R6, contracts/status-api-extension.md §Frontend |

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All file paths are relative to repository root (`/workspaces/pdf-to-html/`)

---

## Phase 1: Setup

**Purpose**: Generate test fixtures and verify prerequisites for classification development

- [ ] T001 Create test fixture generation script in tests/fixtures/generate_classification_fixtures.py that produces sample-report.pdf (20-page text-heavy, high text density, few images), sample-brochure.pdf (4-page image-heavy, multi-column, low text density), and sample-form.pdf (10-page form layout with high object count) using PyMuPDF (fitz) — following the existing pattern of tests/fixtures/generate_sample_docx.py

---

## Phase 2: Foundational (Data Model & Infrastructure)

**Purpose**: Core data model extensions and infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add DocumentType enum (report, whitepaper, form, brochure, newsletter, slide_deck, unknown) and DocumentClassification dataclass (document_type: str, suitability_score: float, confidence: float, warning_message: str|None, metadata: dict) to models.py after the ExtractionMethod enum (~line 76), with validation rules: score/confidence in [0.0, 1.0], warning_message required when score <0.70 and null when ≥0.70
- [ ] T003 Extend Document dataclass in models.py with three optional fields (classification_type: str|None, suitability_score: float|None, classification_warning: str|None) and update to_dict(), to_metadata(), and from_metadata() methods to serialize/deserialize these fields as blob metadata strings
- [ ] T004 [P] Add set_classification() function to status_service.py that accepts blob_service, document_id, classification_type (str), suitability_score (float), classification_confidence (float), classification_warning (str), and classification_engine (str) as keyword-only args, and writes them as blob metadata following the same read-merge-write pattern as set_status()

**Checkpoint**: Data model and metadata infrastructure ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Heuristic Classification Engine (Priority: P1) 🎯 MVP

**Goal**: Build a standalone classification module that analyzes document bytes and returns a DocumentClassification with type, suitability score, confidence, and optional warning message using heuristic signals (text density, image ratio, object count, page uniformity)

**Independent Test**: `pytest tests/unit/test_classification_service.py tests/unit/test_models_classification.py -v` — all 14 test cases from data-model.md pass; classify_document() returns correct types and scores for sample PDFs, DOCX, and PPTX files without requiring Azure Functions runtime or blob storage

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T005 [P] [US1] Write unit tests for DocumentType enum membership and DocumentClassification field validation (score range 0.0–1.0, confidence range 0.0–1.0, warning_message required when score <0.70 and null when ≥0.70, metadata dict presence) in tests/unit/test_models_classification.py
- [ ] T006 [P] [US1] Write unit tests covering all 14 test cases from data-model.md in tests/unit/test_classification_service.py: (1) text-heavy report PDF→report/0.85–1.0/no warning, (2) image-heavy brochure PDF→brochure/0.15–0.40/warning, (3) government form PDF→form/0.40–0.65/warning, (4) PPTX slide deck→slide_deck/0.20–0.45/warning, (5) mixed newsletter PDF→newsletter/0.30–0.55/warning, (6) standard DOCX→report/0.80–0.95/no warning, (7) empty PDF→unknown/0.50/no warning, (8) single-page text PDF→report/0.85–1.0/no warning, (9) score exactly 0.70→no warning, (10) score 0.69→warning, (11) classifier exception→safe default (unknown/0.50/confidence=0.0), (12) password-protected PDF handled before classification, (13) scanned text-heavy report, (14) mixed 50/50 PDF; use sample fixtures from tests/fixtures/

### Implementation for User Story 1

- [ ] T007 [US1] Create classification_service.py with module-level constants SUITABILITY_THRESHOLD=0.70, HEURISTIC_WEIGHTS dict (text_density: 0.35, image_ratio: 0.30, object_count: 0.20, page_uniformity: 0.15), WARNING_TEMPLATES dict with type-specific messages per data-model.md, and implement three helper functions: _compute_suitability_score(signals: dict) → float (weighted sum of normalized signals), _determine_document_type(signals: dict, score: float) → tuple[str, float] (type + confidence via rule matching), _generate_warning(document_type: str, score: float) → str|None (returns template-formatted warning when score < threshold, None otherwise)
- [ ] T008 [US1] Implement _classify_pdf(file_data: bytes) → DocumentClassification in classification_service.py using PyMuPDF (fitz): open PDF from bytes via fitz.open(stream=file_data, filetype="pdf"), iterate pages computing text density (len(page.get_text("text"))/page.rect.width*page.rect.height), image ratio (sum of image areas from page.get_images(full=True)/page area), object count (len(page.get_drawings()) per page), and page uniformity (std dev of per-page text density); normalize each signal to [0.0, 1.0] via clamped linear scaling per research.md R2 thresholds; pass signals to _compute_suitability_score, _determine_document_type, _generate_warning; populate metadata dict with page_count, avg_text_density, avg_image_ratio, avg_object_count, text_density_std, classification_engine="heuristic_v1", classification_time_ms
- [ ] T009 [US1] Implement _classify_docx(file_data: bytes) → DocumentClassification in classification_service.py using python-docx: open DOCX from io.BytesIO(file_data), analyze paragraph count, heading usage (styles starting with "Heading"), image count (inline shapes), table count; apply 0.80 baseline suitability per research.md R7; adjust based on content structure (high heading usage + paragraphs → report, high image count → lower suitability); set classification_engine="heuristic_v1"
- [ ] T010 [US1] Implement _classify_pptx(file_data: bytes) → DocumentClassification in classification_service.py using python-pptx: open PPTX from io.BytesIO(file_data), classify as slide_deck with 0.35 baseline suitability per research.md R7; adjust upward only if slides are text-heavy (total text frame characters > total image area equivalent); compute confidence based on slide count and content consistency; always generate warning since baseline <0.70; set classification_engine="heuristic_v1"
- [ ] T011 [US1] Implement classify_document(file_data: bytes, file_extension: str) → DocumentClassification public function in classification_service.py that dispatches to _classify_pdf for ".pdf", _classify_docx for ".docx", _classify_pptx for ".pptx"; wraps each call in try/except and returns safe default DocumentClassification(document_type="unknown", suitability_score=0.50, confidence=0.0, warning_message=None, metadata={"classification_engine": "heuristic_v1", "error": str(e)}) on any exception; logs warning on failure via logging module; function is stateless and re-entrant per contracts/classification-api.md

**Checkpoint**: Classification engine is fully functional and independently testable — `classify_document(file_bytes, ".pdf")` returns correct DocumentClassification for any supported format

---

## Phase 4: User Story 2 — Pipeline Integration & Metadata Persistence (Priority: P2)

**Goal**: Wire the classification engine into the existing document conversion pipeline so classification runs automatically between validation and extraction, with results persisted in blob metadata and exposed through the existing status API

**Independent Test**: `pytest tests/integration/test_classification_pipeline.py -v` — upload a test document to the pipeline, verify classification metadata appears on the blob, verify status API response includes classification_type, suitability_score, and classification_warning fields

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US2] Write integration tests in tests/integration/test_classification_pipeline.py verifying: (1) uploading a text-heavy PDF produces classification_type="report" and suitability_score≥0.70 in blob metadata with no classification_warning, (2) uploading a brochure-style PDF produces classification_type="brochure" and suitability_score<0.70 with a non-empty classification_warning in blob metadata, (3) classification failure (e.g., corrupted file) does not block extraction — document still reaches "completed" status, (4) classification metadata fields appear in status API response via Document.to_dict()

### Implementation for User Story 2

- [ ] T013 [US2] Insert classification gate in function_app.py after the password-protection check (~line 225) and before extraction begins (~line 227): import classify_document from classification_service, call classify_document(file_data, ext), call status_service.set_classification() with all result fields (classification_type, suitability_score, classification_confidence=confidence, classification_warning=warning_message or "", classification_engine from metadata), wrap entire block in try/except Exception with logger.warning("Classification failed for %s — proceeding without", blob_name) for graceful degradation per Constitution VIII

**Checkpoint**: Classification runs automatically in the pipeline — upload any document and verify classification metadata appears in blob properties and status API response

---

## Phase 5: User Story 3 — Frontend Warning Display (Priority: P3)

**Goal**: Display a WCAG 2.1 AA-compliant warning banner in the web dashboard when a document has a suitability score below 0.70, showing the classification type, score, and context-specific warning message

**Independent Test**: `cd frontend && npm test` — ClassificationWarning renders for low-suitability documents, is hidden for suitable documents, passes axe-core accessibility audit with role="alert" and proper aria attributes

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US3] Write unit tests and axe-core accessibility tests for ClassificationWarning component in frontend/__tests__/components/ClassificationWarning.test.tsx: (1) renders warning banner when classification_warning is non-null and score <0.70, (2) returns null/renders nothing when classification_warning is null or score ≥0.70, (3) displays document type, score formatted as "X.XX/1.0", and warning message text, (4) uses role="alert" and aria-label="Document classification warning", (5) passes jest-axe toHaveNoViolations for WCAG 2.1 AA; import from @testing-library/react and jest-axe following the pattern in frontend/__tests__/components/DownloadButton.test.tsx

### Implementation for User Story 3

- [ ] T015 [P] [US3] Extend DocumentStatus interface in frontend/services/statusService.ts with three optional fields: classification_type?: string, suitability_score?: number | null, classification_warning?: string | null — these map directly to the blob metadata fields returned by the status API per contracts/status-api-extension.md
- [ ] T016 [US3] Create ClassificationWarning.tsx component in frontend/components/ that accepts props { type?: string, score?: number | null, message?: string | null }, renders an <aside role="alert" aria-label="Document classification warning"> containing the warning message and formatted suitability score, returns null when message is falsy or score ≥0.70, and follows NC Digital Commons styling patterns used by existing components (GovBanner.tsx for reference)
- [ ] T017 [US3] Integrate ClassificationWarning into the document conversion progress view by importing it in the appropriate parent component (ProgressTracker.tsx or DocumentPreview.tsx) and conditionally rendering it when classification_warning is non-null/non-empty, passing classification_type, suitability_score, and classification_warning props from the polled DocumentStatus data

**Checkpoint**: Upload a brochure-style PDF through the web UI — warning banner appears in the dashboard with the classification message and suitability score; upload a report-style PDF — no warning appears

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation, accessibility compliance, and documentation updates

- [ ] T018 [P] Validate classification pipeline against all quickstart.md test scenarios: standalone classification via Python REPL (classify_document on sample-digital.pdf), pipeline integration via blob upload + metadata check (azurite + func start), frontend warning display via web UI at localhost:3000
- [ ] T019 [P] Run axe-core WCAG 2.1 AA compliance validation on all ClassificationWarning states (warning visible with brochure type, warning visible with slide_deck type, warning hidden for report type, warning hidden when classification not performed) using the pattern from frontend/__tests__/accessibility.test.tsx
- [ ] T020 [P] Update README.md with classification feature overview (what it does, how it works, link to quickstart.md), verify all file paths in plan.md project structure match actual created files, ensure quickstart.md code examples work with final implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (T002–T003 for data model types)
- **US2 (Phase 4)**: Depends on Phase 2 (T004 for set_classification) + US1 (T011 for classify_document)
- **US3 (Phase 5)**: Depends on Phase 2 (T003 for Document serialization) — can start in parallel with US1/US2 for frontend-only work
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P2)**: Depends on US1 completion (needs classify_document function) — cannot start Phase 4 implementation until T011 is done
- **US3 (P3)**: Frontend type extension (T015) and component (T016) can start after Phase 2; integration (T017) benefits from US2 being complete to test end-to-end but is not strictly blocked

### Within Each User Story

1. Tests MUST be written and FAIL before implementation (Constitution VII)
2. Constants and helpers before format-specific classifiers (T007 before T008–T010)
3. Format-specific classifiers before public dispatch (T008–T010 before T011)
4. Infrastructure before pipeline wiring (T004 before T013)
5. Component before integration (T016 before T017)

### Parallel Opportunities

**Phase 2** (different files):
- T004 (status_service.py) can run in parallel with T002–T003 (models.py)

**Phase 3 — US1** (different files):
- T005 (test_models_classification.py) ∥ T006 (test_classification_service.py) — both test files written simultaneously
- Tests (T005–T006) ∥ implementation start is possible but TDD prefers tests-first

**Phase 5 — US3** (different files):
- T014 (test file) ∥ T015 (statusService.ts) — no shared dependencies

**Cross-story parallelism**:
- US3 frontend work (T014–T016) can overlap with US1 backend work (T007–T011) since they modify completely different file sets

---

## Parallel Example: User Story 1

```bash
# Step 1: Launch both test files in parallel (TDD — write failing tests first):
Task: T005 "Model validation tests in tests/unit/test_models_classification.py"
Task: T006 "Classification service tests in tests/unit/test_classification_service.py"

# Step 2: Implement sequentially in classification_service.py:
Task: T007 "Constants + helper functions"
Task: T008 "_classify_pdf()"
Task: T009 "_classify_docx()"
Task: T010 "_classify_pptx()"
Task: T011 "classify_document() public dispatch"

# Step 3: Verify all tests pass:
pytest tests/unit/test_classification_service.py tests/unit/test_models_classification.py -v
```

## Parallel Example: Cross-Story

```bash
# After Phase 2 completes, backend and frontend can work simultaneously:

# Developer A (Backend — US1):
Task: T007–T011 "Build classification_service.py"

# Developer B (Frontend — US3):
Task: T015 "Extend statusService.ts interface"
Task: T016 "Create ClassificationWarning.tsx"
Task: T014 "Write component tests"

# Sync point: T013 (pipeline gate) + T017 (frontend integration) after both complete
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (generate test fixtures)
2. Complete Phase 2: Foundational (data model extensions)
3. Complete Phase 3: User Story 1 (classification engine)
4. **STOP and VALIDATE**: `pytest tests/unit/test_classification_service.py -v` — all heuristic tests pass
5. Classification engine is usable standalone (Python REPL per quickstart.md)

### Incremental Delivery

1. Setup + Foundational → Data model ready
2. Add US1 → Standalone classification engine (MVP!)
3. Add US2 → Classification runs automatically in pipeline, results in blob metadata
4. Add US3 → Users see warnings in dashboard → Feature complete
5. Each story adds value without breaking previous stories

### Key Design Decisions (from research.md)

- **R1**: Heuristic approach (PyMuPDF metrics) — no external API calls, <100ms
- **R2**: Four signals: text density, image ratio, object count, page uniformity
- **R3**: 0.70 threshold for warnings — matches existing OCR confidence threshold
- **R4**: Blob metadata storage — extends existing pattern, zero new infrastructure
- **R5**: 7-type taxonomy — covers NC state document corpus
- **R6**: Type-specific warning messages with actionable suggestions
- **R7**: Format-specific strategies (DOCX 0.80 baseline, PPTX 0.35 baseline)
- **R8**: Insert between password check and extraction in function_app.py

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (Constitution VII)
- Commit after each task or logical group
- Classification is **informational only** — never blocks conversion (ADR requirement)
- WCAG 2.1 AA compliance required on all warning UI (Constitution I)
- Graceful degradation: classification failure → log warning + proceed normally (Constitution VIII)
- Performance target: classification step <100ms per document
