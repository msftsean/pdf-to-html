# Tasks: WCAG-Compliant Document-to-HTML Converter

**Input**: Design documents from `/specs/001-sean/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per constitution Principle VII (Test-First Development — NON-NEGOTIABLE).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US8)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, dependency installation

- [ ] T001 Create backend test directories: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- [ ] T002 [P] Create frontend project with Next.js 14 App Router in `frontend/` — `npx create-next-app@14 frontend --typescript --app`
- [ ] T003 [P] Add Bootstrap 5 and axe-core dependencies to `frontend/package.json`
- [ ] T004 [P] Add python-docx, python-pptx, and pytest to `requirements.txt` and install
- [ ] T005 [P] Create NCDIT Digital Commons design tokens in `frontend/src/styles/digital-commons.css` — colors (navy #003366, action blue #1e79c8), fonts (Brandon Grotesque/Century Gothic headings, Georgia body)
- [ ] T006 [P] Create `frontend/src/styles/globals.css` importing Bootstrap 5 and Digital Commons tokens
- [ ] T007 Create `.env.example` with all required environment variables per quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create shared data models (Document, PageResult, TextSpan, TableData, CellData, ImageInfo) as Python dataclasses in `models.py` per data-model.md
- [ ] T009 [P] Create `status_service.py` — document processing status tracking (pending/processing/completed/failed) using blob metadata
- [ ] T010 [P] Create `wcag_validator.py` — axe-core validation wrapper that checks HTML output and returns WcagViolation list
- [ ] T011 [P] Create NC.gov layout components in `frontend/src/components/GovBanner.tsx` — "An official website of the State of North Carolina" banner with "How you know" expandable trust indicator
- [ ] T012 [P] Create `frontend/src/components/NCHeader.tsx` — NC.gov logo header with navigation per Digital Commons
- [ ] T013 [P] Create `frontend/src/components/NCFooter.tsx` — NC.gov standard footer layout per Digital Commons
- [ ] T014 Create root layout in `frontend/src/app/layout.tsx` integrating GovBanner, NCHeader, NCFooter, and global styles
- [ ] T015 [P] Create `frontend/src/services/uploadService.ts` — SAS token request + direct blob upload with progress tracking per contracts/upload-api.md
- [ ] T016 [P] Create `frontend/src/services/statusService.ts` — polling for document conversion status per contracts/status-api.md
- [ ] T017 [P] Create HTTP-triggered Azure Function for SAS token generation in `function_app.py` — `POST /api/upload/sas-token` per contracts/upload-api.md
- [ ] T018 [P] Create HTTP-triggered Azure Function for status queries in `function_app.py` — `GET /api/documents/status` per contracts/status-api.md
- [ ] T019 [P] Create HTTP-triggered Azure Function for download URLs in `function_app.py` — `GET /api/documents/{id}/download` per contracts/download-api.md
- [ ] T020 [P] Write unit tests for status_service.py in `tests/unit/test_status_service.py`
- [ ] T021 [P] Write unit tests for wcag_validator.py in `tests/unit/test_wcag_validator.py`
- [ ] T022 [P] Write unit tests for shared data models in `tests/unit/test_models.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Convert Digital PDF to Accessible HTML (Priority: P1) 🎯 MVP

**Goal**: Digital PDF upload produces WCAG 2.1 AA compliant HTML with proper headings, tables, images, and semantic structure

**Independent Test**: Upload a multi-page PDF with headings, tables, images, and lists. Verify output HTML passes axe-core WCAG 2.1 AA with zero critical violations.

### Tests for User Story 1

> **Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T023 [P] [US1] Write unit tests for WCAG-compliant HTML generation in `tests/unit/test_html_builder_wcag.py` — test heading hierarchy (no skipped levels), table scope attributes, figure/figcaption, alt text, lang attribute, skip navigation
- [ ] T024 [P] [US1] Write integration test for digital PDF pipeline in `tests/integration/test_pdf_pipeline.py` — upload sample-digital.pdf, verify output passes axe-core, verify text content preserved
- [ ] T025 [P] [US1] Create test fixture `tests/fixtures/sample-digital.pdf` — multi-page PDF with h1-h4 headings, data table, images, bulleted list

### Implementation for User Story 1

- [ ] T026 [US1] Enhance `html_builder.py` — add WCAG compliance: `lang="en"` on html element, skip navigation link, heading hierarchy enforcement (h1-h6 no gaps), `scope="col"`/`scope="row"` on table headers, `<figure>`/`<figcaption>` for images with alt text, ARIA landmarks
- [ ] T027 [US1] Enhance `html_builder.py` — update inline CSS for WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text), keyboard-focusable elements with visible focus indicators
- [ ] T028 [US1] Update `function_app.py` blob trigger — integrate status_service (set pending→processing→completed/failed), integrate wcag_validator on output, store results as blob metadata
- [ ] T029 [US1] Run axe-core validation on sample-digital.pdf output and fix all critical/serious violations

**Checkpoint**: Digital PDF conversion produces WCAG 2.1 AA compliant HTML — independently testable

---

## Phase 4: User Story 2 — Convert Scanned Legacy PDF with OCR (Priority: P1) 🎯 MVP

**Goal**: Scanned PDFs from the 1990s are OCR-processed and produce accessible HTML; low-confidence pages are flagged for human review

**Independent Test**: Upload a scanned PDF, verify text extracted via OCR, HTML is WCAG compliant, low-confidence pages flagged

### Tests for User Story 2

- [ ] T030 [P] [US2] Write unit tests for OCR confidence flagging in `tests/unit/test_ocr_service.py` — test <70% confidence detection, test page flagging, test OCR failure graceful handling
- [ ] T031 [P] [US2] Write integration test for scanned PDF pipeline in `tests/integration/test_scanned_pipeline.py` — upload sample-scanned.pdf, verify OCR text extraction, verify flagged pages in output
- [ ] T032 [P] [US2] Create test fixture `tests/fixtures/sample-scanned.pdf` — scanned PDF with mixed quality pages

### Implementation for User Story 2

- [ ] T033 [US2] Enhance `ocr_service.py` — add per-page confidence scoring, return confidence in OcrPageResult, flag pages below 70% threshold
- [ ] T034 [US2] Enhance `html_builder.py` — add visible review notice banner on flagged pages ("This page was processed with OCR and may contain errors. Human review recommended.") with ARIA role="alert"
- [ ] T035 [US2] Update `function_app.py` — store has_review_flags and review_pages in document status metadata
- [ ] T036 [US2] Handle OCR failure gracefully — log error, skip page, continue processing remaining pages

**Checkpoint**: Scanned PDF + OCR pipeline works end-to-end with confidence flagging — independently testable

---

## Phase 5: User Story 6 — Upload Documents via Web Interface (Priority: P1) 🎯 MVP

**Goal**: Content managers can drag-and-drop documents onto the web UI, see upload progress, and trigger conversion

**Independent Test**: Open web app, drag a PDF onto upload zone, verify upload with progress bar and conversion begins

### Tests for User Story 6

- [ ] T037 [P] [US6] Write component tests for FileUpload in `frontend/tests/components/FileUpload.test.tsx` — test drag-and-drop, file type validation, size validation, progress display
- [ ] T038 [P] [US6] Write accessibility test for upload page in `frontend/tests/accessibility/wcag.test.tsx` — axe-core validation of entire upload interface
- [ ] T039 [P] [US6] Write E2E test for upload flow in `frontend/tests/e2e/upload-flow.spec.ts` — Playwright test: drag file, verify progress, verify conversion starts

### Implementation for User Story 6

- [ ] T040 [P] [US6] Create `frontend/src/components/FileUpload.tsx` — drag-and-drop zone with file type validation (.pdf/.docx/.pptx), size limit (100MB), progress bar per file, accessible keyboard interaction, NCDIT Digital Commons styling
- [ ] T041 [US6] Create upload page in `frontend/src/app/page.tsx` — landing page with FileUpload component, supported formats info, NCDIT branding, hero section explaining the service
- [ ] T042 [US6] Integrate uploadService.ts with FileUpload component — request SAS token, upload to blob, show progress, handle errors with user-friendly messages
- [ ] T043 [US6] Add file type rejection with clear error messages listing supported formats per FR-024

**Checkpoint**: Web upload interface works end-to-end with NCDIT branding — independently testable

---

## Phase 6: User Story 3 — Batch Process Multiple Documents (Priority: P2)

**Goal**: Multiple documents process independently with status tracking; failed docs do not block others

**Independent Test**: Upload 10 documents, verify all processed, status tracked, completion summary available

### Tests for User Story 3

- [ ] T044 [P] [US3] Write integration test for batch processing in `tests/integration/test_batch_processing.py` — upload 5 documents, verify independent processing, verify failure isolation

### Implementation for User Story 3

- [ ] T045 [US3] Enhance `status_service.py` — add batch summary endpoint returning total/pending/processing/completed/failed counts
- [ ] T046 [US3] Update status API function in `function_app.py` — add summary aggregation to `GET /api/documents/status`
- [ ] T047 [US3] Ensure blob trigger handles concurrent document processing without interference — verify stateless execution

**Checkpoint**: Batch processing with status tracking works — independently testable

---

## Phase 7: User Story 7 — Track Conversion Progress in Real-Time (Priority: P2)

**Goal**: Dashboard shows live status for all documents with progress indicators, error details, and retry option

**Independent Test**: Upload 5 documents, verify dashboard updates in real-time showing status progression

### Tests for User Story 7

- [ ] T048 [P] [US7] Write component tests for ProgressTracker in `frontend/tests/components/ProgressTracker.test.tsx` — test status display, progress bar, error state, retry button
- [ ] T049 [P] [US7] Write accessibility test for dashboard in `frontend/tests/accessibility/dashboard-wcag.test.tsx`

### Implementation for User Story 7

- [ ] T050 [P] [US7] Create `frontend/src/components/ProgressTracker.tsx` — document list with status badges (pending/processing/completed/failed), progress bar for in-progress docs, error message display, retry button for failed docs
- [ ] T051 [US7] Create dashboard page in `frontend/src/app/dashboard/page.tsx` — batch summary stats, ProgressTracker list, auto-refresh via statusService polling (3-5s interval), NCDIT Digital Commons card layout
- [ ] T052 [US7] Integrate statusService.ts with dashboard — polling logic, state management, auto-stop when all terminal

**Checkpoint**: Real-time progress dashboard works — independently testable

---

## Phase 8: User Story 4 — Convert Word Documents to Accessible HTML (Priority: P2)

**Goal**: .docx files produce WCAG 2.1 AA compliant HTML preserving Word document structure

**Independent Test**: Upload a .docx with styled headings, tables, images. Verify output passes WCAG validation.

### Tests for User Story 4

- [ ] T053 [P] [US4] Write unit tests for DOCX extractor in `tests/unit/test_docx_extractor.py` — test heading extraction, table extraction, image extraction, list extraction
- [ ] T054 [P] [US4] Write integration test for DOCX pipeline in `tests/integration/test_docx_pipeline.py`
- [ ] T055 [P] [US4] Create test fixture `tests/fixtures/sample.docx` — Word doc with Heading 1-3 styles, data table, embedded image, bulleted list

### Implementation for User Story 4

- [ ] T056 [US4] Create `docx_extractor.py` — extract headings (from Word styles), paragraphs, tables, images, lists from .docx using python-docx; output PageResult format per data-model.md
- [ ] T057 [US4] Update `function_app.py` — detect .docx format in blob trigger, route to docx_extractor, then html_builder for WCAG HTML output
- [ ] T058 [US4] Handle .docx with no heading styles — infer headings from font size per FR edge case

**Checkpoint**: DOCX conversion produces WCAG 2.1 AA compliant HTML — independently testable

---

## Phase 9: User Story 8 — Preview and Download Converted HTML (Priority: P2)

**Goal**: Content managers preview generated HTML in-browser and download HTML + image assets as a package

**Independent Test**: Complete a conversion, click preview, verify HTML renders, download zip package

### Tests for User Story 8

- [ ] T059 [P] [US8] Write component tests for DocumentPreview in `frontend/tests/components/DocumentPreview.test.tsx`
- [ ] T060 [P] [US8] Write component tests for DownloadButton in `frontend/tests/components/DownloadButton.test.tsx`

### Implementation for User Story 8

- [ ] T061 [P] [US8] Create `frontend/src/components/DocumentPreview.tsx` — iframe preview of converted HTML, highlight flagged pages with confidence warning
- [ ] T062 [P] [US8] Create `frontend/src/components/DownloadButton.tsx` — download zip package (HTML + images) via download API
- [ ] T063 [US8] Update dashboard page to show preview and download actions on completed documents
- [ ] T064 [US8] Create zip packaging in download API function in `function_app.py` — bundle HTML + images into zip, generate SAS URL per contracts/download-api.md

**Checkpoint**: Preview and download works — independently testable

---

## Phase 10: User Story 5 — Convert PowerPoint to Accessible HTML (Priority: P3)

**Goal**: .pptx files produce WCAG 2.1 AA compliant HTML with slide-by-slide sections and speaker notes

**Independent Test**: Upload a .pptx with slides, tables, speaker notes. Verify slide-by-slide HTML passes WCAG validation.

### Tests for User Story 5

- [ ] T065 [P] [US5] Write unit tests for PPTX extractor in `tests/unit/test_pptx_extractor.py` — test slide content, speaker notes, table, image extraction
- [ ] T066 [P] [US5] Write integration test for PPTX pipeline in `tests/integration/test_pptx_pipeline.py`
- [ ] T067 [P] [US5] Create test fixture `tests/fixtures/sample.pptx` — 5-slide deck with tables, images, speaker notes

### Implementation for User Story 5

- [ ] T068 [US5] Create `pptx_extractor.py` — extract slide titles, text frames, tables, images, speaker notes from .pptx using python-pptx; each slide maps to a PageResult with slide title as heading
- [ ] T069 [US5] Enhance `html_builder.py` — render slides as `<section>` elements with slide title as heading, speaker notes as accessible associated content
- [ ] T070 [US5] Update `function_app.py` — detect .pptx format in blob trigger, route to pptx_extractor

**Checkpoint**: PPTX conversion produces WCAG 2.1 AA compliant HTML — independently testable

---

## Phase 11: Evaluation Suite

**Purpose**: End-to-end evaluation of the converter against real-world sample documents with WCAG compliance scoring

### Sample Documents

- [ ] T080 [P] Curate eval corpus in `tests/eval/samples/` — gather/create 6-8 representative documents:
  - `digital-report.pdf` — multi-page digital PDF with headings, tables, images, lists (20+ pages)
  - `scanned-legacy.pdf` — scanned document from 1990s-era (low quality, mixed orientation)
  - `mixed-content.pdf` — PDF with both digital and scanned pages in one file
  - `complex-tables.pdf` — PDF with nested/merged-cell tables, multi-page tables
  - `image-heavy.pdf` — PDF with charts, photos, diagrams needing alt text
  - `simple-memo.pdf` — single-page text-only memo (baseline/sanity check)
  - `sample.docx` — Word doc with styled headings, tables, images (if DOCX extractor ready)
  - `sample.pptx` — slide deck with speaker notes, tables (if PPTX extractor ready)

### Eval Harness

- [ ] T081 Create eval harness script `scripts/run_evals.py` — orchestrator that:
  - Discovers all files in `tests/eval/samples/`
  - Runs each through the conversion pipeline (pdf_extractor → ocr_service → html_builder)
  - Runs wcag_validator on each HTML output
  - Generates a structured JSON report at `tests/eval/results/eval-report.json`
  - Prints a summary table to stdout with pass/fail per document

- [ ] T082 [P] Create eval metrics module `scripts/eval_metrics.py` — calculates per-document:
  - WCAG violation count by severity (critical/serious/moderate/minor)
  - Heading hierarchy correctness score (0-100%)
  - Table accessibility score (scope attributes, headers present)
  - Image alt-text coverage (% of images with meaningful alt text)
  - Overall compliance score (weighted: critical=0 tolerance, serious=heavy penalty)

- [ ] T083 [P] Create eval report template `scripts/eval_report.md.j2` — Jinja2 markdown template that renders:
  - Summary table with ✅/❌ per document per metric
  - WCAG violation details grouped by rule
  - Side-by-side comparison: source doc info vs. output HTML stats
  - Overall compliance badge (PASS/FAIL based on zero critical violations)

- [ ] T084 Create `scripts/run_evals.sh` — shell wrapper that:
  - Starts Azurite if not running
  - Creates blob containers
  - Runs `scripts/run_evals.py`
  - Renders eval report from JSON to markdown
  - Opens report or prints to stdout

### Eval Validation

- [ ] T085 Run eval suite against all sample documents and capture baseline metrics
- [ ] T086 [P] Add eval to CI — GitHub Actions workflow `.github/workflows/eval.yml` that runs evals on PR and posts summary as PR comment

---

## Phase 12: Developer Quickstart Validation

**Purpose**: Ensure the quickstart guide actually works from a cold start

- [ ] T087 Create validated quickstart script `scripts/quickstart-check.sh` — automated script that:
  - Checks all prerequisites (Python 3.12+, Node.js 20+, func CLI, Azurite)
  - Installs backend deps (`pip install -r requirements.txt`)
  - Installs frontend deps (`cd frontend && npm install`)
  - Starts Azurite in background
  - Creates blob containers
  - Starts Azure Functions in background
  - Starts frontend dev server in background
  - Uploads a sample PDF via CLI
  - Polls for completion (up to 60s)
  - Verifies converted HTML exists in output container
  - Prints ✅/❌ for each step
  - Cleans up background processes on exit

- [ ] T088 [P] Update root `QUICKSTART.md` (or create if missing) — verified developer onboarding guide with:
  - Copy-paste commands that work on Linux/macOS/Codespaces
  - Troubleshooting section for common issues
  - "Hello World" section: convert your first document in under 5 minutes
  - Links to spec, architecture, and API contracts

- [ ] T089 Run quickstart validation — execute `scripts/quickstart-check.sh` and fix any failures

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T071 [P] Add password-protected/encrypted document rejection with clear error message per FR-013 in `function_app.py`
- [ ] T072 [P] Add multi-language `lang` attribute detection on content sections per edge case in `html_builder.py`
- [ ] T073 [P] Add exponential backoff retry for blob storage failures in `function_app.py`
- [ ] T074 [P] Add filename conflict handling for concurrent uploads with same name per edge case in `function_app.py`
- [ ] T075 Run full WCAG 2.1 AA audit on web UI (all pages) with axe-core — fix all violations
- [ ] T076 Run full WCAG 2.1 AA audit on sample HTML output (all formats) — fix all violations
- [ ] T077 [P] Update `README.md` with project overview, architecture, and quickstart
- [ ] T078 [P] Run quickstart.md validation — verify all steps work end-to-end
- [ ] T079 Performance validation — verify <30s for 50-page digital PDF, <3min for scanned PDF per SC-002/SC-003

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — MVP core
- **US2 (Phase 4)**: Depends on Foundational — can parallel with US1
- **US6 (Phase 5)**: Depends on Foundational + API functions (T017-T019) — MVP frontend
- **US3 (Phase 6)**: Depends on US1 or US2 (needs working pipeline)
- **US7 (Phase 7)**: Depends on US6 (needs upload UI) + US3 (needs status tracking)
- **US4 (Phase 8)**: Depends on Foundational — can parallel with US1/US2
- **US8 (Phase 9)**: Depends on US6 + US7 (needs dashboard) + download API (T019)
- **US5 (Phase 10)**: Depends on Foundational — can parallel with others
- **Polish (Phase 11)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1 (Digital PDF)**: Foundational only — fully independent
- **US2 (Scanned PDF)**: Foundational only — fully independent, can parallel with US1
- **US6 (Web Upload)**: Foundational + API functions — can parallel with US1/US2
- **US3 (Batch)**: Needs working pipeline (US1 or US2)
- **US7 (Dashboard)**: Needs US6 + US3
- **US4 (DOCX)**: Foundational only — fully independent
- **US8 (Preview/Download)**: Needs US6 + US7 + download API
- **US5 (PPTX)**: Foundational only — fully independent

### Squad Assignment (Justice League)

| Agent | Stories | Rationale |
|-------|---------|-----------|
| Wonder-Woman | US1, US2, US4, US5 | Backend: PDF, OCR, DOCX, PPTX extraction |
| Flash | US6, US7, US8 | Frontend: upload, dashboard, preview/download |
| Cyborg | Phase 1, Phase 2 (infra), Phase 12 | DevOps: project setup, Azure config, CI/CD, quickstart |
| Aquaman | All test tasks, Phase 11 (evals) | QA: write tests first, validate WCAG compliance, run evals |
| Batman | Review all phases, Phase 11 (eval design) | Lead: triage, review, architecture, eval strategy |

---

## Parallel Opportunities

### Phase 2 (Foundational) — 15 tasks, 12 parallelizable

```
Parallel group A: T009, T010, T011, T012, T013 (backend services + NC components)
Parallel group B: T015, T016, T017, T018, T019 (frontend services + API functions)
Parallel group C: T020, T021, T022 (unit tests)
Sequential: T008 (shared models — needed by T009, T010), T014 (layout — needs T011-T013)
```

### After Foundational — 4 stories can start in parallel

```
Wonder-Woman: US1 (Digital PDF) + US2 (Scanned PDF)
Flash: US6 (Web Upload UI)
Aquaman: Writing tests for all three simultaneously
```

---

## Implementation Strategy

### MVP First (P1 Stories — April 2026 Deadline)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US1 — Digital PDF conversion
4. Complete Phase 4: US2 — Scanned PDF with OCR
5. Complete Phase 5: US6 — Web upload interface
6. **STOP and VALIDATE**: Test all P1 stories independently
7. Deploy MVP — agencies can start converting PDFs immediately

### Incremental Delivery (P2/P3 as timeline permits)

8. Add US3 (Batch) + US7 (Dashboard) — operational efficiency
9. Add US4 (DOCX) + US8 (Preview/Download) — format coverage + UX
10. Add US5 (PPTX) — complete format coverage
11. Phase 11: Polish — security hardening, performance, documentation

---

## Summary

| Metric | Count |
|--------|-------|
| Total tasks | 89 |
| Phase 1 (Setup) | 7 |
| Phase 2 (Foundational) | 15 |
| US1 (Digital PDF) — P1 | 7 |
| US2 (Scanned PDF) — P1 | 7 |
| US6 (Web Upload) — P1 | 7 |
| US3 (Batch) — P2 | 4 |
| US7 (Dashboard) — P2 | 5 |
| US4 (DOCX) — P2 | 6 |
| US8 (Preview/Download) — P2 | 6 |
| US5 (PPTX) — P3 | 6 |
| Eval Suite (Phase 11) | 7 |
| Quickstart Validation (Phase 12) | 3 |
| Polish (Phase 13) | 9 |
| Parallel opportunities | 45 tasks (57%) |
| MVP scope (P1 only) | 36 tasks |
