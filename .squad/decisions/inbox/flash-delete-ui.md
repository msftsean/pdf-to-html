# Decision: Delete UI Architecture

**Author:** Flash (Frontend Developer)  
**Date:** 2025-07-18  
**Status:** Implemented

## Context

Implemented the complete frontend for document deletion (Tasks T005–T012 from specs/003-delete-runs). This includes individual document deletion, bulk "Clear All", and all WCAG accessibility polish.

## Decisions Made

**Shared ConfirmDialog component**
- Built a single reusable `ConfirmDialog.tsx` component used by both individual delete and Clear All flows. Props-driven (`title`, `message`, `confirmLabel`, `variant`, `isLoading`) so it adapts to each context. This avoids duplicating modal logic and ensures consistent focus trap / keyboard behavior across both use cases.

**Optimistic state removal after delete**
- On successful `deleteDocument()`, the document is immediately removed from the `documents` array and the summary counter is decremented — without waiting for a re-poll. This gives instant visual feedback. The backend is the source of truth; the next poll would reconcile if needed, but optimistic removal avoids a jarring "document still visible" delay.

**Focus return pattern using refs**
- Before opening any dialog, the trigger button's DOM reference is captured via a ref (`deleteTriggerRef` / `clearAllTriggerRef`). After the dialog closes (confirm or cancel), focus is returned to that ref via `setTimeout`. This satisfies WCAG 2.4.3 (Focus Order) and ensures keyboard users aren't lost after a modal interaction.

**Processing-state guard is visual + API-enforced**
- When a document has `status === 'processing'`, the delete button is rendered as `disabled` with a title tooltip explaining why. The backend also enforces this with HTTP 409. The deleteService maps 409 to a friendly error message. This is defense-in-depth — UI prevents the action, but the API also refuses it.

**aria-live="assertive" for delete announcements**
- Used `assertive` (not `polite`) because deletions are destructive actions that users must be notified about immediately. The announcement clears itself after 5 seconds to avoid stale text being re-read on focus changes.

## Impact on Team

- **Wonder-Woman (Backend):** Frontend expects `DELETE /api/documents/{id}` (200/404/409) and `DELETE /api/documents` (200/500). Response shapes: `DeleteResponse { message, document_id }` and `DeleteAllResponse { message, deleted_input, deleted_output }`.
- **Aquaman (QA):** New data-testid attributes available: `confirm-dialog`, `confirm-btn`, `cancel-btn`, `delete-btn-{id}`, `clear-all-btn`, `delete-error`, `delete-announcement`. Focus return after dialog close needs screen reader validation.
- **Cyborg (DevOps):** No infrastructure changes. Delete operations go through same `/api` proxy.

## Files Created/Modified

| File | Change |
|------|--------|
| `frontend/services/deleteService.ts` | **New** — DELETE API client |
| `frontend/components/ConfirmDialog.tsx` | **New** — Accessible confirmation modal |
| `frontend/components/ProgressTracker.tsx` | Added `onDelete` prop + delete buttons per row |
| `frontend/app/dashboard/page.tsx` | Added delete/clear-all state, handlers, ConfirmDialogs, aria-live |
