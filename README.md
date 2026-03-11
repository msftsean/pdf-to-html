<div align="center">

<img src="https://files.nc.gov/digital-solutions/styles/_inline_extra_large_/public/images/2025-02/2021.08.09%20NCDIT%20Logo_White.png" alt="NCDIT Logo" width="280" />

# 📄 pdf-to-html

### WCAG 2.1 AA Compliant Document-to-HTML Converter

*An Azure Functions-powered document conversion service for the State of North Carolina*

[![WCAG 2.1 AA](https://img.shields.io/badge/WCAG-2.1_AA-green?style=for-the-badge&logo=w3c&logoColor=white)](https://www.w3.org/WAI/WCAG21/quickref/)
[![ADA Title II](https://img.shields.io/badge/ADA-Title_II-blue?style=for-the-badge)](https://www.ada.gov/law-and-regs/title-ii-2010-regulations/)
[![Azure Functions](https://img.shields.io/badge/Azure-Functions-0078D4?style=for-the-badge&logo=azure-functions&logoColor=white)](https://azure.microsoft.com/en-us/products/functions)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

**🏛️ Built for NC State Government** · **♿ Accessibility First** · **⚡ Serverless at Scale**

</div>

---

## 🎯 Mission

Convert PDF, Word, and PowerPoint documents published on North Carolina state websites into **fully accessible HTML** — meeting the **DOJ April 2026 deadline** for WCAG 2.1 Level AA compliance under **Title II ADA** digital accessibility requirements.

## 📊 Project Status

| Milestone | Status | Progress |
|-----------|--------|----------|
| 📋 Specification | ✅ Complete | ![100%](https://img.shields.io/badge/100%25-brightgreen?style=flat-square) |
| 📐 Architecture | ✅ Complete | ![100%](https://img.shields.io/badge/100%25-brightgreen?style=flat-square) |
| 🗺️ Implementation Plan | ✅ Complete | ![100%](https://img.shields.io/badge/100%25-brightgreen?style=flat-square) |
| ✅ Task Breakdown | ✅ Complete | ![100%](https://img.shields.io/badge/100%25-brightgreen?style=flat-square) |
| 🔧 Backend (PDF) | 🚧 In Progress | ![40%](https://img.shields.io/badge/40%25-yellow?style=flat-square) |
| 🔍 OCR Pipeline | 🚧 In Progress | ![35%](https://img.shields.io/badge/35%25-yellow?style=flat-square) |
| 🌐 Web UI | 📋 Planned | ![0%](https://img.shields.io/badge/0%25-lightgrey?style=flat-square) |
| 📝 DOCX Support | 📋 Planned | ![0%](https://img.shields.io/badge/0%25-lightgrey?style=flat-square) |
| 📊 PPTX Support | 📋 Planned | ![0%](https://img.shields.io/badge/0%25-lightgrey?style=flat-square) |

## ✨ Features

| Feature | Description | Priority |
|---------|-------------|----------|
| 📄 **Digital PDF Conversion** | Extract text, headings, tables, images → WCAG HTML | P1 🎯 |
| 🔍 **Scanned PDF + OCR** | Azure Document Intelligence for legacy 1990s documents | P1 🎯 |
| 🖱️ **Web Upload Interface** | Drag-and-drop upload with NCDIT Digital Commons branding | P1 🎯 |
| 📦 **Batch Processing** | Process hundreds of documents concurrently | P2 |
| 📊 **Live Dashboard** | Real-time conversion progress tracking | P2 |
| 📝 **Word (.docx)** | Preserve Word document structure in HTML | P2 |
| 👁️ **Preview & Download** | In-browser HTML preview + zip package download | P2 |
| 📊 **PowerPoint (.pptx)** | Slide-by-slide HTML with speaker notes | P3 |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   🌐 Web Interface                  │
│         React / Next.js / Bootstrap 5               │
│         NCDIT Digital Commons Design System         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Upload   │  │ Status   │  │ Download/Preview │  │
│  │ API      │  │ API      │  │ API              │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                 │            │
├───────┴──────────────┴─────────────────┴────────────┤
│              ⚡ Azure Functions (Python)             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌────────────┐  ┌─────────┐  ┌──────────────┐     │
│  │ PDF        │  │ DOCX    │  │ PPTX         │     │
│  │ Extractor  │  │ Extract │  │ Extractor    │     │
│  │ (PyMuPDF)  │  │ (docx)  │  │ (pptx)       │     │
│  └─────┬──────┘  └────┬────┘  └──────┬───────┘     │
│        │              │              │              │
│        └──────────────┼──────────────┘              │
│                       ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │         🔍 OCR Service                     │     │
│  │    Azure Document Intelligence             │     │
│  │    (scanned pages only, <20 chars)         │     │
│  └────────────────────┬───────────────────────┘     │
│                       ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │         ♿ HTML Builder                     │     │
│  │    Semantic HTML5 + WCAG 2.1 AA            │     │
│  │    axe-core validation on output           │     │
│  └────────────────────┬───────────────────────┘     │
│                       ▼                             │
│  ┌────────────────────────────────────────────┐     │
│  │         📦 Azure Blob Storage              │     │
│  │    files/ (input) → converted/ (output)    │     │
│  └────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Azure Functions Core Tools v4
- Azurite (local blob storage emulator)

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AzureWebJobsStorage="UseDevelopmentStorage=true"
export DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/"
export OUTPUT_CONTAINER="converted"

# Start local storage emulator
azurite-blob --silent &

# Start Azure Functions
func start
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Convert a Document

```bash
# Upload via CLI
az storage blob upload \
  --container-name files \
  --file my-document.pdf \
  --name my-document.pdf \
  --connection-string "UseDevelopmentStorage=true"

# Or drag-and-drop via the web UI at http://localhost:3000
```

## 🧪 Testing

```bash
# Backend tests
pytest tests/ -v

# Frontend tests
cd frontend && npm test

# Accessibility validation
cd frontend && npm run test:a11y

# E2E tests
npx playwright test
```

## 🦸 Squad (Justice League)

This project uses [Squad](https://github.com/bradygaster/squad) for AI-assisted team coordination.

| Agent | Role | Domain |
|-------|------|--------|
| 🦇 **Batman** | Tech Lead | Architecture, code review, triage |
| 🛡️ **Wonder-Woman** | Backend Developer | PDF/DOCX/PPTX extraction, OCR, Azure Functions |
| ⚡ **Flash** | Frontend Developer | React/Next.js UI, NCDIT Digital Commons styling |
| 🤖 **Cyborg** | DevOps & Infrastructure | Azure deployment, CI/CD, monitoring |
| 🔱 **Aquaman** | QA & Testing | WCAG validation, test coverage, edge cases |
| 📝 **Scribe** | Documentation | Session logging, decision records |

## 📋 Spec Kit

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) for specification-driven development.

| Artifact | Path | Description |
|----------|------|-------------|
| 📜 Constitution | `pdf-to-html/.specify/memory/constitution.md` | Project principles (v2.0.0) |
| 📋 Specification | `specs/001-sean/spec.md` | Feature spec (8 user stories, 25 FRs) |
| 🗺️ Plan | `specs/001-sean/plan.md` | Implementation plan |
| 🔬 Research | `specs/001-sean/research.md` | Technology decisions |
| 📊 Data Model | `specs/001-sean/data-model.md` | Entity definitions |
| 🔌 API Contracts | `specs/001-sean/contracts/` | Upload, Status, Download APIs |
| ✅ Tasks | `specs/001-sean/tasks.md` | 79 actionable implementation tasks |

## 📦 Version Matrix

| Version | Date | Component | Changes |
|---------|------|-----------|---------|
| v0.4.0 | 2026-03-11 | 📋 Tasks | 79 implementation tasks generated with squad assignments |
| v0.3.0 | 2026-03-11 | 🗺️ Plan | Implementation plan, research, data model, API contracts |
| v0.2.0 | 2026-03-11 | 📋 Spec | 8 user stories, 25 FRs, NCDIT Digital Commons UI requirements |
| v0.1.0 | 2026-03-11 | 📜 Constitution | v2.0.0 — WCAG 2.1 AA, multi-format, batch processing principles |
| v0.0.1 | 2026-03-11 | 🏗️ Scaffold | Project init, Squad (Justice League), Spec Kit, frontend-design skill |

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| ⚡ Runtime | Azure Functions (Python 3.12) | Serverless document processing |
| 📄 PDF | PyMuPDF (fitz) | Digital PDF text/image/table extraction |
| 🔍 OCR | Azure Document Intelligence | Scanned page recognition (prebuilt-layout) |
| 📝 DOCX | python-docx | Word document structure extraction |
| 📊 PPTX | python-pptx | PowerPoint slide extraction |
| ♿ Validation | axe-core | Automated WCAG 2.1 AA compliance testing |
| 🌐 Frontend | React 18 / Next.js 14 | Component-based web UI with SSR |
| 🎨 UI Framework | Bootstrap 5 | NCDIT Digital Commons compatible |
| 🏛️ Design System | NCDIT Digital Commons | NC.gov brand compliance |
| ☁️ Storage | Azure Blob Storage | Document input/output persistence |
| 🔐 Auth | Azure Identity (Entra ID) | Managed identity, zero secrets |

## 📁 Project Structure

```
pdf-to-html/
├── 📄 function_app.py          # Azure Functions orchestrator
├── 📄 pdf_extractor.py         # PDF extraction (PyMuPDF)
├── 🔍 ocr_service.py           # OCR service (Document Intelligence)
├── ♿ html_builder.py           # WCAG-compliant HTML generation
├── 📝 docx_extractor.py        # Word document extraction (planned)
├── 📊 pptx_extractor.py        # PowerPoint extraction (planned)
├── ✅ wcag_validator.py         # axe-core validation wrapper (planned)
├── 📊 status_service.py        # Processing status tracking (planned)
├── 📦 requirements.txt         # Python dependencies
├── ⚙️ host.json                # Azure Functions configuration
├── �� frontend/                # React/Next.js web interface (planned)
├── 🧪 tests/                   # Backend test suite
├── 📋 specs/                   # Spec Kit artifacts
│   └── 001-sean/               # Feature spec, plan, tasks
├── 🦸 pdf-to-html/.squad/      # Squad team configuration
└── 🎨 .agents/skills/          # AI skills (frontend-design)
```

## ♿ Accessibility Commitment

This project exists because **accessible government services are a civil right**. Every North Carolinian — regardless of ability — deserves equal access to public information.

- 🎯 **WCAG 2.1 Level AA** — the legal standard, our minimum bar
- 🔍 **Automated + manual testing** — axe-core catches ~57%, humans catch the rest
- 📋 **NC Digital Accessibility & Usability Standard v1.1** — our compliance framework
- ⚖️ **Title II ADA** — the law that drives this work
- 🗓️ **April 2026** — the deadline that makes it urgent

## 📜 Regulatory Context

> *All content published on North Carolina state websites must be fully accessible by April 2026, per DOJ ruling under Title II ADA digital accessibility requirements. The compliance standard is WCAG 2.1 Level AA.*

---

<div align="center">

**Built with ❤️ for the people of North Carolina**

🏛️ [NC.gov](https://www.nc.gov) · 💻 [NCDIT](https://it.nc.gov) · ♿ [Digital Accessibility](https://it.nc.gov/documents/digital-accessibility-usability-standard/open)

</div>
