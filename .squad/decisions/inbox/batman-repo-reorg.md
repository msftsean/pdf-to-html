# Decision: Repository Root Reorganization

**Author:** Batman (Tech Lead)  
**Date:** 2025-07-25  
**Status:** Implemented  
**Requested by:** Sean

## Context

The repo root had 13 loose files — 8 backend Python modules, 2 documentation files, and 3 Azure Functions config files that must stay at root. Sean flagged this as messy and hard to navigate.

## Decision

### 1. Created `backend/` Python package

Moved all 8 backend modules into `backend/` with an `__init__.py`:

| Module | Purpose |
|--------|---------|
| `pdf_extractor.py` | PDF → text/images/tables (PyMuPDF) |
| `docx_extractor.py` | Word document extraction |
| `pptx_extractor.py` | PowerPoint extraction |
| `ocr_service.py` | Azure Document Intelligence OCR |
| `html_builder.py` | WCAG-compliant HTML generation |
| `wcag_validator.py` | Server-side WCAG 2.1 AA validation |
| `status_service.py` | Document processing status tracking |
| `models.py` | Shared data models |

**Import convention:**
- Within `backend/`: relative imports (`from .pdf_extractor import ...`)
- From `function_app.py`, tests, scripts: absolute imports (`from backend.pdf_extractor import ...`)

### 2. Moved documentation into `docs/`

- `DEPLOYMENT.md` → `docs/DEPLOYMENT.md`
- `QUICKSTART.md` → `docs/QUICKSTART.md`

### 3. Left `pdf-to-html/` subdirectory in place

This directory contains project governance infrastructure (`.specify/memory/constitution.md`, `.squad/`, `.github/agents/`). All 5 agent configurations and the copilot-instructions.md reference `pdf-to-html/.specify/memory/constitution.md`. Removing it would break governance tooling.

**Future action:** Consider promoting `.specify/` to repo root and updating all agent references.

### 4. Azure Functions constraints respected

These files MUST remain at root per Azure Functions v2 Python runtime requirements:
- `function_app.py`
- `host.json`
- `local.settings.json`
- `requirements.txt`

## Impact

- **Root directory:** Reduced from 13 loose files to 6
- **Tests:** All 174 tests pass — zero regressions
- **All team members:** Import paths changed. Use `from backend.X import Y` going forward.
- **Cyborg (DevOps):** No infrastructure changes needed. Azure Functions will resolve `backend.X` imports from root.
- **Wonder-Woman (Backend):** New modules go in `backend/`. Use relative imports within the package.
- **Flash (Frontend):** No impact — frontend is unchanged.
- **Aquaman (QA):** Test imports updated. New tests should use `from backend.X import Y`.

## Files Modified

- `function_app.py` — updated all imports to `backend.*`
- `backend/__init__.py` — new package init
- `backend/*.py` — 8 modules moved, cross-module imports updated to relative
- `tests/unit/*.py` — 7 test files updated
- `tests/integration/*.py` — 4 test files updated
- `scripts/*.py` — 3 script files updated
- `README.md` — project structure section updated
- `docs/QUICKSTART.md` — project structure section updated
- `.github/copilot-instructions.md` — updated module references and QUICKSTART path
