# 🦇 Documentation Audit — Batman (Tech Lead)

**Date:** 2025-07-24
**Scope:** All user-facing documentation files

---

## 🔴 Stale / Incorrect Content Found

### 1. Ghost Health Endpoint (QUICKSTART.md)

**Severity:** 🔴 High
**Location:** QUICKSTART.md — "Start the Services" section and "API Contracts"
**Issue:** Documentation referenced `GET /api/health` endpoint that does not exist in `function_app.py`. The actual endpoints are:
- `POST /api/upload/sas-token` (SAS token generation)
- `GET /api/documents/status` (conversion status)
- `GET /api/documents/{document_id}/download` (download URL)

**Fix applied:** Replaced health check verification with status endpoint. Rewrote API Contracts section with all three actual endpoints.

### 2. Incorrect wcag_validator.py Description (QUICKSTART.md)

**Severity:** 🟡 Medium
**Location:** QUICKSTART.md — Project Structure section, line 269
**Issue:** `wcag_validator.py` was described as "axe-core accessibility validation" — incorrect. It's a Python-based server-side validator with 7 WCAG rules (heading order, alt text, table headers, etc.). axe-core is used in the frontend test suite (`jest-axe`), not in the backend validator.

**Fix applied:** Changed description to "Server-side WCAG 2.1 AA validation (7 Python rules)".

### 3. Missing Backend Extractors (QUICKSTART.md)

**Severity:** 🟡 Medium
**Location:** QUICKSTART.md — Project Structure section
**Issue:** `docx_extractor.py` and `pptx_extractor.py` were completely missing from the project structure listing, even though DOCX and PPTX extraction are core features (US-04, US-05).

**Fix applied:** Added both files with descriptions.

### 4. Default Boilerplate Frontend README (frontend/README.md)

**Severity:** 🔴 High
**Location:** `frontend/README.md`
**Issue:** Entire file was the default `create-next-app` template boilerplate. No project-specific information — mentioned Vercel deployment (not used), Geist font (not relevant), and generic instructions.

**Fix applied:** Complete rewrite with project-specific content, version matrix, component listing, feature status table, and NCDIT-specific guidance.

### 5. Incomplete API Documentation (QUICKSTART.md)

**Severity:** 🟡 Medium
**Location:** QUICKSTART.md — API Contracts section
**Issue:** Only documented 2 of 3 endpoints (health + status). Missing the SAS token upload endpoint and the download endpoint, which are the primary user-facing APIs.

**Fix applied:** Documented all three actual endpoints with request/response examples.

### 6. Stale Project Structure References (QUICKSTART.md)

**Severity:** 🟢 Low
**Location:** QUICKSTART.md — Project Structure
**Issue:** Missing `eval/` test directory, `run_evals.py` and `render_report.py` scripts, `contracts/` directory, and `tasks.md` from specs listing.

**Fix applied:** Updated to include all current directories and files.

---

## ✅ Content Verified Accurate

- README.md architecture diagram matches actual code structure
- README.md feature table matches implemented user stories
- README.md technology stack matches actual dependencies
- Backend setup instructions in QUICKSTART.md are correct
- Frontend setup instructions in QUICKSTART.md are correct
- Runbook README.md deployment workflow description is accurate
- Encryption guide StaticCrypt instructions are correct

---

## 📊 Summary

| Finding | Severity | Status |
|---------|----------|--------|
| Ghost health endpoint | 🔴 High | ✅ Fixed |
| Incorrect validator description | 🟡 Medium | ✅ Fixed |
| Missing extractors in structure | 🟡 Medium | ✅ Fixed |
| Boilerplate frontend README | 🔴 High | ✅ Fixed |
| Incomplete API docs | 🟡 Medium | ✅ Fixed |
| Stale project structure | 🟢 Low | ✅ Fixed |
