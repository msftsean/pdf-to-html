# Implementation Plan: Document Classification Engine

**Branch**: `002-classification-engine` | **Date**: 2026-03-12 | **ADR**: [batman-classification-engine.md](../../.squad/decisions/inbox/batman-classification-engine.md)
**Input**: Architecture Decision Record from `.squad/decisions/inbox/batman-classification-engine.md`

## Summary

Add a document-level classification pre-processing gate between blob upload
and extraction in the WCAG document-to-HTML converter. The engine analyzes
documents before conversion begins, classifies document type (report,
brochure, form, slide deck, newsletter), and returns a suitability score
for HTML conversion. Documents scoring below threshold receive a user-facing
warning but are never rejected — preserving user autonomy.

The implementation follows a phased rollout: **Phase 1** deploys lightweight
heuristics (text density, image ratio, page count analysis) to establish the
gate architecture and warning UX. **Phase 2** collects user feedback labels
in parallel. **Phase 3** swaps in an Azure AI Foundry custom model trained on
labeled data, with heuristics as fallback.

This plan covers Phase 1 (heuristics) only. Phases 2–3 are future work.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Node 20 (frontend)
**Primary Dependencies**: PyMuPDF (page analysis), azure-storage-blob
(metadata persistence), React 18 / Next.js 14 (warning display)
**Storage**: Azure Blob Storage — classification results stored as blob
metadata on the document's blob in the `files/` container
**Testing**: pytest (backend unit + integration), Jest + React Testing Library
(frontend), axe-core (WCAG validation on warning UI)
**Target Platform**: Azure Functions (Python) + Azure Static Web Apps (Next.js)
**Project Type**: Web application (backend pipeline extension + frontend UI)
**Performance Goals**: Classification step <100ms per document (heuristic);
no regression to existing <30s/50-page digital PDF pipeline
**Constraints**: Classification is **informational only** — never blocks
conversion; WCAG 2.1 AA compliance on all warning UI; zero external API calls
for Phase 1 (in-process heuristics only)
**Scale/Scope**: All documents flowing through the existing pipeline; no new
infrastructure required for Phase 1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. WCAG 2.1 AA Compliance | ✅ PASS | Warning UI must be WCAG compliant; classification warnings include accessible text; no visual-only signals |
| II. Multi-Format Ingestion | ✅ PASS | Classifier analyzes PDF, DOCX, PPTX — all supported formats; format-specific heuristic rules |
| III. Selective OCR | ✅ PASS | Classification runs pre-OCR; does not interfere with existing scanned page detection |
| IV. Accessible Semantic Output | ✅ PASS | Warning messages embedded as accessible HTML notices in output; proper ARIA roles |
| V. Batch Processing at Scale | ✅ PASS | <100ms heuristic adds negligible latency; no external API calls; no blocking |
| VI. Modular Pipeline | ✅ PASS | Classifier is a standalone module (`classification_service.py`) with clear input/output; independently testable; no Azure Functions runtime dependency |
| VII. Test-First Development | ✅ PASS | Tests for each heuristic rule, threshold edge cases, integration with function_app.py pipeline |
| VIII. Cloud-Native Resilience | ✅ PASS | Classification stored in blob metadata (existing pattern); stateless; graceful degradation if classifier fails (proceed without warning) |

**GATE RESULT**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-classification-engine/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity model
├── quickstart.md        # Phase 1: developer onboarding
├── contracts/           # Phase 1: API contracts
│   ├── classification-api.md
│   └── status-api-extension.md
└── tasks.md             # Phase 2: actionable tasks (via /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (Azure Functions - Python) — modified/new files
function_app.py              # MODIFIED: insert classification gate after password check
models.py                    # MODIFIED: add DocumentClassification dataclass + DocumentType enum
classification_service.py    # NEW: heuristic classification engine
status_service.py            # MODIFIED: support warning_message field

tests/
├── unit/
│   ├── test_classification_service.py   # NEW: heuristic rule tests
│   └── test_models_classification.py    # NEW: DocumentClassification validation
├── integration/
│   └── test_classification_pipeline.py  # NEW: end-to-end pipeline with classification
└── fixtures/
    ├── sample-report.pdf                # NEW: high-suitability test doc
    ├── sample-brochure.pdf              # NEW: low-suitability test doc
    └── sample-form.pdf                  # NEW: medium-suitability test doc

# Frontend (React/Next.js) — modified files
frontend/src/
├── components/
│   └── ClassificationWarning.tsx    # NEW: warning banner component
├── services/
│   └── statusService.ts             # MODIFIED: parse classification fields
└── tests/
    └── components/
        └── ClassificationWarning.test.tsx  # NEW: warning UI + a11y tests
```

**Structure Decision**: Extension of existing flat backend layout. The
classification service follows the same pattern as `ocr_service.py` and
`status_service.py` — a standalone module imported by `function_app.py`.
No new directories needed. Frontend adds one component and extends the
existing status service.

## Complexity Tracking

No constitution violations. No complexity justification needed.

## Constitution Re-Check (Post Phase 1 Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. WCAG 2.1 AA Compliance | ✅ PASS | `ClassificationWarning.tsx` uses `role="alert"` and accessible text |
| II. Multi-Format Ingestion | ✅ PASS | Per-format heuristic weights in `HEURISTIC_WEIGHTS` dict |
| III. Selective OCR | ✅ PASS | Classification runs before OCR; does not alter OCR routing |
| IV. Accessible Semantic Output | ✅ PASS | Warning notice uses `<aside>` with `aria-label` |
| V. Batch Processing at Scale | ✅ PASS | Heuristic is synchronous, <100ms, no I/O |
| VI. Modular Pipeline | ✅ PASS | `classification_service.py` has no imports from `function_app` |
| VII. Test-First Development | ✅ PASS | 14 test cases defined in data-model.md |
| VIII. Cloud-Native Resilience | ✅ PASS | Classification failure ⇒ log warning + proceed normally |

**GATE RESULT**: ALL PASS — proceed to task generation.
