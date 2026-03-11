# Squad Decisions

## Active Decisions

### 1. Frontend Architecture — Phase 1+2 Scaffold

**Author:** Flash (Frontend Developer)  
**Date:** 2026-03-11  
**Status:** Implemented

#### Context
Stood up the full Next.js 14 frontend from scratch, including design system tokens, layout shell, government branding components, and backend service layers.

#### Decisions Made

**Styled JSX for component-scoped CSS**
- Chose: Next.js built-in `<style jsx>` for GovBanner, NCHeader, NCFooter
- Over: CSS Modules or Tailwind
- Why: Zero config, co-located with components, no extra dependencies, works with SSR. Bootstrap handles layout; styled-jsx handles component-specific overrides.

**CSS Custom Properties for Design Tokens**
- Chose: CSS `--nc-*` custom properties in `digital-commons.css`
- Over: Sass variables, JS theme objects, or Tailwind config
- Why: Works natively in CSS, no build tooling required, easily consumed by both Bootstrap overrides and component styles. Future theme switching (dark mode, high-contrast) becomes trivial.

**XMLHttpRequest for Upload Progress**
- Chose: XHR in `uploadService.ts`
- Over: Fetch API or third-party upload libraries (tus, Uppy)
- Why: Fetch API doesn't support `upload.onprogress`. XHR is the only browser-native option for real-time upload progress bars. Keeps dependencies minimal.

**Polling-based Status Updates**
- Chose: `setTimeout`-based polling in `statusService.ts` (3s interval)
- Over: WebSocket, SSE, or long-polling
- Why: Simpler backend contract (stateless HTTP), works with Azure Functions consumption plan, easy to implement. Can migrate to SSE later if needed. Minimum 1s guard prevents accidental server overload.

#### Impact
- Wonder-Woman: Backend API must implement `POST /api/upload` (returns SAS token) and `GET /api/status` / `GET /api/status/:id` endpoints.
- Cyborg: No WebSocket infrastructure needed initially; standard HTTP endpoints suffice.
- Aquaman: axe-core is installed and ready for dev-time accessibility auditing.

---

### 2. Phase 2 Backend Architecture

**Author:** Wonder-Woman (Backend Developer)  
**Date:** 2026-03-11  
**Status:** Implemented

#### Context
Phase 2 required three new HTTP API endpoints (SAS upload, status query, download URLs) plus shared infrastructure modules (models, status tracking, WCAG validation).

#### Decisions Made

**Blob metadata for status tracking (no database)**
- Decision: Store all document status as Azure Blob metadata on the uploaded file in the `files/` container.
- Rationale: Avoids provisioning a database service for what is currently a small-scale deployment. Blob metadata is transactional, free, and co-located with the files. If scale requires it later, the `status_service.py` interface can be swapped to CosmosDB without changing callers.
- Trade-off: `list_documents()` does a full container scan. Acceptable for < 1,000 documents; will need pagination or an index beyond that.

**SAS token upload flow with placeholder blob**
- Decision: `generate_sas_token` creates an empty placeholder blob with full metadata before returning the SAS URL to the browser.
- Rationale: This ensures the status service can track the document immediately (e.g., the frontend can poll `/documents/status` right away). The browser's PUT upload overwrites the blob content but preserves metadata.

**Python-side WCAG pre-validation**
- Decision: `wcag_validator.py` implements 7 WCAG rules in pure Python using regex parsing. This is a server-side pre-check, not a replacement for axe-core.
- Rationale: Catches critical issues (missing alt text, broken heading hierarchy, missing table headers) before the HTML even reaches the browser. Reduces round-trips for obvious violations. The frontend still runs full axe-core for comprehensive validation.

**models.py re-exports existing dataclasses**
- Decision: `models.py` imports `TextSpan`, `ImageInfo`, `TableData`, `PageResult` from `pdf_extractor.py` and re-exports them alongside new domain models.
- Rationale: Single import point for all data types. Avoids duplicating the extraction dataclasses while adding `Document`, `ConversionResult`, `WcagViolation`, `CellData`, and `EnhancedPageResult`.

#### Impact on Other Team Members
- Flash (Frontend): Can now call all three API endpoints. Response shapes match the contracts in `specs/001-sean/contracts/`.
- Aquaman (QA): `wcag_validator.py` is independently testable — pass HTML string, get violation list.
- Cyborg (DevOps): No new infrastructure dependencies. All state lives in blob storage.

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
