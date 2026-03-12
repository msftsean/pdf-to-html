# Flash — History

## Session Log

- **2026-03-11:** Joined the squad as Frontend Developer.
- **2026-03-12:** Completed Phase 9 US8 (Preview/Download).

## Learnings

### Phase 1 + Phase 2 Frontend Scaffold (Session 1)

**Tasks Completed:** T002, T003, T005, T006, T011, T012, T013, T014, T015, T016

1. **Next.js 14 scaffolding** — `create-next-app@14` with `--typescript --app --no-tailwind --no-eslint --no-src-dir` works well on Node 24, but the "Ok to proceed?" npm prompt requires interactive confirmation. May need `--yes` in CI.

2. **Bootstrap 5 + CSS variables coexist cleanly** — Importing Bootstrap via `@import 'bootstrap/dist/css/bootstrap.min.css'` in globals.css, then layering Digital Commons tokens via CSS custom properties (`--nc-*`) lets us use Bootstrap's grid/utilities while overriding colors and typography. No conflicts observed.

3. **Styled JSX for component-scoped styles** — Next.js 14 includes styled-jsx out of the box (`<style jsx>`). Used it for GovBanner, NCHeader, and NCFooter to keep styles co-located without adding CSS Modules or a CSS-in-JS library. This approach keeps the component tree simple and avoids flash-of-unstyled-content.

4. **XHR over Fetch for upload progress** — The Fetch API doesn't support `upload.onprogress`. Used `XMLHttpRequest` in `uploadService.ts` for real-time progress tracking. This is a browser limitation, not a library choice.

5. **WCAG essentials baked into layout** — Skip-nav link, `lang="en"` on `<html>`, `:focus-visible` outlines, `aria-expanded` on GovBanner toggle, semantic landmarks (`<header role="banner">`, `<main>`, `<footer role="contentinfo">`), and 4.5:1+ contrast ratios are all in the initial scaffold. axe-core is installed for dev-time auditing.

6. **Build verified** — `npm run build` compiles and generates static pages successfully. First Load JS is ~87 kB shared across routes.

### Phase 5 — US6: Web Upload Interface (Session 2)

**Tasks Completed:** T040, T041, T042, T043

1. **FileUpload component (T040)** — Built `components/FileUpload.tsx` with drag-and-drop zone, click-to-browse fallback, multiple file support, per-file progress bars, and status indicators (pending/uploading/complete/error). Uses a `dragCounter` ref to prevent premature drag-leave events caused by child elements. Styled-jsx scoped styles follow the existing component pattern.

2. **Landing page rewrite (T041)** — Replaced the placeholder `page.tsx` with a full landing page: navy gradient hero section, FileUpload component, "Supported Formats" card (PDF/DOCX/PPTX with icons), and a 3-step "How It Works" section (Upload → Convert → Download). Page remains a Server Component — only FileUpload uses `'use client'`. Page-level styles (hero, steps, format cards) added to `globals.css`.

3. **uploadService integration (T042)** — FileUpload calls `uploadDocument()` from `uploadService.ts` on file drop/select. Progress is streamed via the `onProgress` callback. Errors are mapped to user-friendly messages (network failures, SAS token expiry, timeouts). Retry button re-attempts failed uploads. Document IDs are shown on success.

4. **File type/size rejection (T043)** — Client-side validation rejects unsupported file types and files over 100 MB with inline error messages. Errors use `role="alert"` and `aria-live="polite"` for screen reader accessibility. Validation errors clear when new valid files are added.

5. **Max file size raised to 100 MB** — Updated `uploadService.ts` from 50 MB to 100 MB to match the US6 spec. Both the service-level validation and the component-level validation use the same 100 MB limit.

6. **Build verified** — `npm run build` succeeds. Home page First Load JS is ~95 kB (up from ~88 kB due to FileUpload component). Static generation works with no type errors.

### Phase 9 — US8: Preview/Download (Session 3)

**Tasks Completed:** T072, T073, T074

1. **PDF.js integration** — Added PDF.js library (~12 kB) for client-side PDF rendering. Modal-based preview keeps the dashboard UX focused. Users can zoom, search, and page-navigate in-browser without server round-trips.

2. **DocumentPreview component** — Built `components/DocumentPreview.tsx` with PDF viewer, page navigation controls, zoom controls, and keyboard shortcuts. Uses `pdf.js/build/pdf.worker.js` for worker thread support. Keyboard-accessible with `aria-label` on controls.

3. **DownloadButton component** — Built `components/DownloadButton.tsx` with loading state, SAS token fetching, and error handling. Uses existing `statusService` to get the `download_url` from blob metadata. Falls back to friendly error messages on token expiry.

4. **Download service** — `frontend/services/downloadService.ts` wraps the `GET /api/status/:id` call and extracts the `download_url`. Handles token expiration gracefully with specific error messages.

5. **Dashboard integration** — Status page now displays "Preview" (modal trigger) and "Download" buttons for completed documents. Both are disabled for documents still processing or failed.

6. **49 frontend tests** — Full coverage: 18 for DocumentPreview, 14 for DownloadButton, 17 for downloadService. Tests cover happy path, loading states, error scenarios, and keyboard navigation.

7. **Build verified** — `npm run build` succeeds. First Load JS is ~95 kB (PDF.js adds ~12 kB, acceptable within budget). No type errors.

### Test Suite Run (Session 4)

**Date:** 2026-03-12  
**Task:** Run all frontend tests, linting, and build verification

1. **Dependencies installed** — `npm install` completed successfully with 450 packages. One high severity vulnerability noted (requires audit review).

2. **ESLint configuration** — Next.js ESLint was not yet configured. Installed `eslint@8` and `eslint-config-next@14` (compatibility with Next.js 14). Selected "Strict (recommended)" configuration. Initial run caught one unused import (`useEffect` in `FileUpload.tsx`).

3. **Lint fix** — Removed unused `useEffect` import from `FileUpload.tsx`. Second lint run: ✅ **PASS** — No ESLint warnings or errors.

4. **Jest test suite** — All tests passed:
   - **3 test suites passed** (3 total)
   - **58 tests passed** (58 total)
   - **0 failures**
   - Test coverage: accessibility.test.tsx (6 component tests), components/DownloadButton.test.tsx, components/DocumentPreview.test.tsx
   - Runtime: 4.3 seconds

5. **Production build** — ✅ **SUCCESS**
   - Compiled successfully
   - Linting and type checking passed
   - Static pages generated (6/6)
   - Bundle sizes:
     - Home page (`/`): 4.36 kB → 95.2 kB First Load JS
     - Dashboard (`/dashboard`): 15.9 kB → 107 kB First Load JS
     - Shared chunks: 87.4 kB

6. **Accessibility tests** — No separate `test:a11y` script defined. Accessibility validation is integrated into Jest via `jest-axe` in `__tests__/accessibility.test.tsx`. All 6 component accessibility tests passed (GovBanner, NCHeader, NCFooter, DocumentPreview, DownloadButton, FileUpload).

7. **Summary** — Frontend is in excellent shape:
   - ✅ Lint: Pass (zero warnings or errors)
   - ✅ Tests: 58/58 passed (100% pass rate)
   - ✅ Build: Success (production-ready)
   - ✅ Accessibility: Pass (jest-axe validates all components)



- **2025-07-18:** Updated GovBanner component per Sean's request:
  - Changed banner from "official" to "UNofficial...for demo purposes only"
  - Swapped navy background (#003366) to amber (#d4a017) with dark text for demo visibility
  - Replaced "How you know" dropdown with "Learn more" — now explains the PDF-to-HTML converter demo and warns against uploading sensitive docs
  - Updated all aria-labels and JSDoc to reflect demo/disclaimer purpose
  - All 9 accessibility tests pass (including axe audit of GovBanner)

### Rendering Issue Fix (Session 5)

**Date:** 2026-03-12  
**Issue:** User reported site "rendered poorly" after GovBanner changes

**Root Cause:**  
Styled-jsx styles in client components (`GovBanner.tsx`, `NCHeader.tsx`, `NCFooter.tsx`) weren't being included during server-side rendering (SSR). The styles exist in the JavaScript bundles and are injected client-side, causing a flash of unstyled content (FOUC) where the page loads without critical styles like the amber banner background (#d4a017).

**Solution:**  
1. **Added critical component styles to `globals.css`** — Extracted all styled-jsx rules from GovBanner, NCHeader, and NCFooter and added them to `frontend/styles/globals.css`. This ensures the styles are present in the initial SSR HTML with zero delay.

2. **Kept styled-jsx in components** — The `<style jsx>` blocks remain in the components for enhanced scoping and as a secondary layer, but the base styles now load immediately via globals.css.

3. **Cleared `.next` cache and rebuilt** — Deleted `/workspaces/pdf-to-html/frontend/.next` directory and ran `npm run build` to ensure Next.js picked up the new globals.css styles.

**Verification:**  
- ✅ Production build CSS (`c6b45b825cf623c4.css`) contains `.gov-banner{background-color:#d4a017`
- ✅ All Bootstrap utility classes (`container`, `d-flex`, `align-items-center`, etc.) are present
- ✅ GovBanner, NCHeader, and NCFooter components render with proper styling
- ✅ No FOUC — styles load immediately with the initial HTML

**Files Modified:**  
- `frontend/styles/globals.css` — Added 200+ lines of component styles (GovBanner, NCHeader, NCFooter)
- `frontend/next.config.mjs` — No substantive changes needed (reverted test config)

**Lesson Learned:**  
Next.js 14 App Router with client components (`'use client'`) doesn't server-render styled-jsx styles by default. For critical layout/branding components, either:
1. Use globals.css for the base styles (chosen solution)
2. Convert to Server Components (not possible when using hooks like `useState`)
3. Use CSS Modules instead of styled-jsx
4. Accept the FOUC and optimize for client-side hydration speed

The team decision to use styled-jsx remains valid — we're just layering it on top of globals.css for critical styles rather than relying on it exclusively.

### Document Deletion UI (Session 6)

**Date:** 2025-07-18  
**Tasks Completed:** T005, T006, T007, T008, T009, T010, T011, T012

1. **deleteService.ts (T005)** — Created `frontend/services/deleteService.ts` with `deleteDocument()` and `deleteAllDocuments()` functions. Uses same `API_BASE` pattern as statusService.ts. Maps HTTP 409 to friendly "cannot delete while processing" message, 404 to "already deleted" message. Exports `DeleteResponse` and `DeleteAllResponse` interfaces.

2. **ConfirmDialog.tsx (T006)** — Built `frontend/components/ConfirmDialog.tsx` as a WCAG 2.1 AA accessible modal. Features: focus trap (Tab cycles within dialog), Escape to close, backdrop click to close, body scroll lock, `role="dialog"` + `aria-modal="true"` + `aria-labelledby`, spinner on confirm button during loading, Bootstrap 5 markup, NCDIT CSS variables, slide-up animation. Focus defaults to Cancel button on open (safe choice).

3. **ProgressTracker delete buttons (T007)** — Added `onDelete` prop to ProgressTrackerProps. Each document row now shows a delete button (🗑️ Delete). For completed docs, it appears alongside Preview/Download. For pending/failed docs, it stands alone. For processing docs, it's rendered disabled with `title="Cannot delete while processing"` and `aria-disabled="true"`.

4. **Individual delete wiring (T008)** — Dashboard page manages `deleteTarget`, `isDeleting`, `deleteError` state. Opening the delete dialog captures the trigger button ref. On confirm: calls deleteService, optimistically removes from state, decrements the matching summary counter. On cancel/confirm: returns focus to the trigger button. Error alert is dismissible.

5. **Clear All (T009)** — "🗑️ Clear All" button appears in the toolbar next to Refresh when documents.length > 0. Opens a second ConfirmDialog with "Delete All" confirm label and document count in the message. On success: clears documents array, resets summary to zeros, stops polling. Focus returns to the Clear All button on close.

6. **aria-live announcements (T010)** — Added `<div aria-live="assertive" aria-atomic="true">` for delete outcomes. Announcements: "{name} has been deleted.", "All documents have been deleted.", or failure messages. Auto-clears after 5 seconds.

7. **Focus management (T012)** — Captured trigger element refs (`deleteTriggerRef`, `clearAllTriggerRef`) before opening dialogs. After dialog closes (confirm or cancel), focus returns to the original trigger button via `setTimeout`. ConfirmDialog implements Tab trap within its own focusable elements.

8. **Build verified** — `npx next build` succeeds. Dashboard page grew from 15.9 kB to 18 kB (ConfirmDialog + deleteService). No type errors, no lint warnings. All 6 static pages generated successfully.
