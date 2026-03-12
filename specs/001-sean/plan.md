# Implementation Plan: WCAG-Compliant Document-to-HTML Converter

**Branch**: `001-sean` | **Date**: 2026-03-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-sean/spec.md`

## Summary

Build a WCAG 2.1 AA compliant document-to-HTML conversion system for North
Carolina state government, driven by the DOJ April 2026 accessibility
deadline. The system converts PDFs (digital and scanned), Word documents, and
PowerPoint files into accessible HTML via an Azure Functions backend with OCR
support. A React/Next.js web interface following the NCDIT Digital Commons
design system provides drag-and-drop upload, real-time progress tracking, and
HTML preview/download. The existing PyMuPDF-based PDF extraction pipeline
serves as the foundation, extended with WCAG compliance, multi-format support,
and a production web UI.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Node 20 (frontend)
**Primary Dependencies**: PyMuPDF, Azure Document Intelligence SDK,
azure-storage-blob, azure-identity (backend); React 18, Next.js 14,
Bootstrap 5, axe-core (frontend)
**Storage**: Azure Blob Storage (`files/` input, `converted/` output)
**Testing**: pytest (backend), Jest + React Testing Library + axe-core
(frontend), Playwright (E2E)
**Target Platform**: Azure Functions (Python) + Azure Static Web Apps or
App Service (Next.js)
**Project Type**: Web application (backend API + frontend SPA)
**Performance Goals**: <30s per 50-page digital PDF; <3min per 50-page
scanned PDF; 100 concurrent documents; <3s UI load time
**Constraints**: WCAG 2.1 AA mandatory; April 2026 deadline; NCDIT Digital
Commons brand compliance; all output self-contained HTML
**Scale/Scope**: NC state agency websites; hundreds to thousands of documents;
multiple concurrent agency users

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. WCAG 2.1 AA Compliance | ✅ PASS | axe-core validation on all output; UI itself WCAG compliant |
| II. Multi-Format Ingestion | ✅ PASS | PDF (existing), DOCX (python-docx), PPTX (python-pptx) extractors planned |
| III. Selective OCR | ✅ PASS | Existing <20 char threshold; Document Intelligence prebuilt-layout |
| IV. Accessible Semantic Output | ✅ PASS | HTML5 semantic elements, ARIA, scope, alt text, lang attribute |
| V. Batch Processing at Scale | ✅ PASS | Blob trigger + parallel processing + status tracking |
| VI. Modular Pipeline | ✅ PASS | Extractors → OCR → HTML Builder → Orchestrator; injectable deps |
| VII. Test-First Development | ✅ PASS | pytest + Jest + Playwright; WCAG regression tests in CI |
| VIII. Cloud-Native Resilience | ✅ PASS | Stateless functions; DefaultAzureCredential; graceful degradation |

**GATE RESULT**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-sean/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity model
├── quickstart.md        # Phase 1: developer onboarding
├── contracts/           # Phase 1: API contracts
│   ├── upload-api.md
│   ├── status-api.md
│   └── download-api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2: actionable tasks (via /speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (Azure Functions - Python)
function_app.py              # Azure Functions orchestrator (existing)
pdf_extractor.py             # PDF extraction module (existing)
ocr_service.py               # OCR service module (existing)
html_builder.py              # HTML generation module (existing)
docx_extractor.py            # Word document extractor (new)
pptx_extractor.py            # PowerPoint extractor (new)
wcag_validator.py            # WCAG validation wrapper (new)
status_service.py            # Document processing status tracking (new)
requirements.txt             # Python dependencies (existing)
host.json                    # Azure Functions config (existing)

tests/
├── unit/
│   ├── test_pdf_extractor.py
│   ├── test_ocr_service.py
│   ├── test_html_builder.py
│   ├── test_docx_extractor.py
│   ├── test_pptx_extractor.py
│   └── test_wcag_validator.py
├── integration/
│   ├── test_pdf_pipeline.py
│   ├── test_docx_pipeline.py
│   └── test_pptx_pipeline.py
└── fixtures/
    ├── sample-digital.pdf
    ├── sample-scanned.pdf
    ├── sample.docx
    └── sample.pptx

# Frontend (React/Next.js)
frontend/
├── package.json
├── next.config.js
├── tsconfig.json
├── public/
│   ├── nc-logo.png          # NC.gov official logo
│   └── favicon.ico
├── src/
│   ├── app/
│   │   ├── layout.tsx        # Root layout with NC.gov header/footer
│   │   ├── page.tsx          # Upload page (landing)
│   │   └── dashboard/
│   │       └── page.tsx      # Progress dashboard
│   ├── components/
│   │   ├── GovBanner.tsx     # "Official website of NC" banner
│   │   ├── NCHeader.tsx      # NC.gov branded header
│   │   ├── NCFooter.tsx      # NC.gov standard footer
│   │   ├── FileUpload.tsx    # Drag-and-drop upload zone
│   │   ├── ProgressTracker.tsx # Real-time conversion status
│   │   ├── DocumentPreview.tsx # HTML preview iframe
│   │   └── DownloadButton.tsx  # Package download
│   ├── services/
│   │   ├── uploadService.ts  # Blob upload with progress
│   │   └── statusService.ts  # Polling/SSE for conversion status
│   └── styles/
│       ├── digital-commons.css # NCDIT design tokens
│       └── globals.css
└── tests/
    ├── components/
    │   ├── FileUpload.test.tsx
    │   ├── ProgressTracker.test.tsx
    │   └── GovBanner.test.tsx
    ├── accessibility/
    │   └── wcag.test.tsx     # axe-core UI validation
    └── e2e/
        └── upload-flow.spec.ts  # Playwright E2E
```

**Structure Decision**: Web application with existing Python backend (Azure
Functions) extended in-place, plus a new Next.js frontend directory. The
backend stays flat (matching existing convention) while the frontend follows
Next.js App Router conventions with NCDIT Digital Commons styling.

## Complexity Tracking

No constitution violations. No complexity justification needed.
