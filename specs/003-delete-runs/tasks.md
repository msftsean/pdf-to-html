# Tasks: Delete Document Conversion Runs

**Input**: Feature description for deleting individual and bulk document conversion runs from the dashboard
**Prerequisites**: Existing codebase (function_app.py, status_service.py, frontend dashboard)

**Tests**: Not explicitly requested — test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup required — this feature extends the existing codebase. This phase captures the shared backend deletion logic that both user stories depend on.

- [ ] T001 Add `delete_document()` method to `status_service.py` that accepts a `BlobServiceClient` and `document_id`, locates the input blob in the `files` container using `_find_blob_by_id()`, reads its metadata to derive the document name and `output_path`, deletes all blobs under the output prefix in the `converted` container (HTML + images folder e.g. `{docname}/`), then deletes the input blob itself; returns a `dict` with `{"deleted": True, "document_id": str, "blobs_removed": int}` or raises `ResourceNotFoundError` if the document does not exist
- [ ] T002 [P] Add `delete_all_documents()` method to `status_service.py` that accepts a `BlobServiceClient`, iterates all blobs in the `files` container and deletes each one, then iterates all blobs in the `converted` container and deletes each one; returns a `dict` with `{"deleted_input": int, "deleted_output": int}` counts; use the `_INPUT_CONTAINER` constant and accept `output_container` as a parameter (default `"converted"`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend API endpoints and shared frontend infrastructure that MUST be complete before ANY user story UI work can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Add `DELETE /api/documents/{document_id}` endpoint in `function_app.py` using the decorator pattern `@app.route(route="documents/{document_id}", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)`; call `_get_blob_service_client()` to get the blob client, then call `status_service.delete_document(blob_service, document_id)`; return HTTP 200 JSON `{"message": "Document deleted", "document_id": "..."}` on success, HTTP 404 if document not found, HTTP 409 if document status is `"processing"` (refuse to delete mid-processing), HTTP 500 with error details on failure; wrap blob operations with `_retry_blob_operation` for transient failures
- [ ] T004 [P] Add `DELETE /api/documents` endpoint in `function_app.py` using the decorator `@app.route(route="documents", methods=["DELETE"], auth_level=func.AuthLevel.ANONYMOUS)`; call `status_service.delete_all_documents(blob_service, _OUTPUT_CONTAINER)`; return HTTP 200 JSON `{"message": "All documents deleted", "deleted_input": N, "deleted_output": N}` on success, HTTP 500 with error details on failure; log the operation with `logger.info` including deletion counts
- [ ] T005 [P] Create `frontend/services/deleteService.ts` with two exported async functions: (1) `deleteDocument(documentId: string): Promise<DeleteResponse>` — sends `DELETE` to `${API_BASE}/documents/${documentId}` using native `fetch`, returns parsed JSON response, throws on non-OK status with error message from response body; (2) `deleteAllDocuments(): Promise<DeleteAllResponse>` — sends `DELETE` to `${API_BASE}/documents`, same error handling pattern; export interfaces `DeleteResponse { message: string; document_id: string }` and `DeleteAllResponse { message: string; deleted_input: number; deleted_output: number }`; use the same `API_BASE` pattern as `statusService.ts`: `const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api'`
- [ ] T006 [P] Create `frontend/components/ConfirmDialog.tsx` — a WCAG 2.1 AA accessible modal confirmation dialog component using Bootstrap 5 modal markup; props: `isOpen: boolean`, `title: string`, `message: string`, `confirmLabel: string` (default "Delete"), `cancelLabel: string` (default "Cancel"), `variant: 'danger' | 'warning'` (default "danger"), `onConfirm: () => void`, `onCancel: () => void`, `isLoading?: boolean`; implement focus trap (focus the cancel button on open, trap Tab within modal), close on Escape key, render a backdrop overlay with `role="dialog"` and `aria-modal="true"` and `aria-labelledby` pointing to the title; confirm button should show a spinner and be disabled when `isLoading` is true; use NCDIT Digital Commons CSS variables for styling (`--nc-navy`, `--nc-font-heading`, `--nc-font-body`); include `data-testid="confirm-dialog"`, `data-testid="confirm-btn"`, `data-testid="cancel-btn"`

**Checkpoint**: Foundation ready — backend DELETE endpoints operational, frontend service layer and shared ConfirmDialog component available for user story implementation

---

## Phase 3: User Story 1 — Delete Individual Run (Priority: P1) 🎯 MVP

**Goal**: A user can delete a single document conversion from the dashboard, removing its input blob, output HTML, and all associated image assets from Azure Blob Storage

**Independent Test**: Upload a document, wait for completion, click the delete (🗑️) button on its row, confirm in the dialog, verify the document disappears from the dashboard list and the summary counts update; also verify that a document with status "processing" shows an error toast if deletion is attempted

### Implementation for User Story 1

- [ ] T007 [US1] Update `ProgressTrackerProps` interface in `frontend/components/ProgressTracker.tsx` to add an optional `onDelete?: (documentId: string, documentName: string) => void` callback prop; for every document `<li>` item, add a delete button in the actions area (alongside existing Preview/Download buttons for completed docs, or standalone for pending/failed docs) — render a `<button>` with `className="btn btn-sm btn-outline-danger"`, `aria-label={`Delete ${doc.name}`}`, `data-testid={`delete-btn-${doc.document_id}`}`, displaying 🗑️ icon + "Delete" text; call `onDelete(doc.document_id, doc.name)` on click; add CSS for `.progress-tracker__delete-btn` matching the existing retry button hover/focus styles but using `--nc-danger` color; position the delete button at the end of the actions row for completed docs, and in a new actions div for pending/failed docs
- [ ] T008 [US1] Wire individual document deletion in `frontend/app/dashboard/page.tsx`: add state `const [deleteTarget, setDeleteTarget] = useState<{id: string, name: string} | null>(null)` and `const [isDeleting, setIsDeleting] = useState(false)` and `const [deleteError, setDeleteError] = useState<string | null>(null)`; create `handleDeleteRequest(documentId: string, name: string)` that sets `deleteTarget`; create `handleDeleteConfirm()` that calls `deleteService.deleteDocument(deleteTarget.id)`, on success removes the document from `documents` state via `setDocuments(prev => prev.filter(d => d.document_id !== deleteTarget.id))` and decrements the appropriate summary counter, on failure sets `deleteError`; create `handleDeleteCancel()` that clears `deleteTarget`; pass `onDelete={handleDeleteRequest}` to `<ProgressTracker>`; render `<ConfirmDialog>` when `deleteTarget` is not null with `title="Delete Document"`, `message={`Are you sure you want to permanently delete "${deleteTarget.name}"? This will remove the original file and all converted output. This action cannot be undone.`}`, `isLoading={isDeleting}`; render a dismissible error alert when `deleteError` is set

**Checkpoint**: At this point, individual document deletion should be fully functional — user can delete any single document from the dashboard with confirmation

---

## Phase 4: User Story 2 — Delete All Runs (Priority: P2)

**Goal**: A user can clear all documents from the dashboard with a single "Clear All" action, removing all input blobs and all converted output from Azure Blob Storage

**Independent Test**: Upload 3+ documents, click the "Clear All" button in the dashboard header, confirm in the dialog, verify the document list becomes empty, summary counters reset to zero, and the empty state message ("No documents uploaded yet") appears

### Implementation for User Story 2

- [ ] T009 [US2] Add "Clear All" button and deletion handler in `frontend/app/dashboard/page.tsx`: add state `const [showClearAll, setShowClearAll] = useState(false)` and `const [isClearingAll, setIsClearingAll] = useState(false)`; render a `<button>` with `className="btn btn-sm btn-outline-danger"`, text "🗑️ Clear All", `aria-label="Delete all documents"`, `data-testid="clear-all-btn"` in the `.d-flex` toolbar row next to the existing Refresh button — only show when `documents.length > 0` and `!isPolling` (or always show when docs exist); on click set `setShowClearAll(true)`; create `handleClearAllConfirm()` that sets `isClearingAll(true)`, calls `deleteService.deleteAllDocuments()`, on success sets `setDocuments([])` and resets summary to all zeros, stops polling, on failure shows error alert; render a second `<ConfirmDialog>` when `showClearAll` is true with `title="Clear All Documents"`, `message={`Are you sure you want to permanently delete all ${documents.length} document(s)? This will remove all uploaded files and converted output. This action cannot be undone.`}`, `confirmLabel="Delete All"`, `variant="danger"`, `isLoading={isClearingAll}`

**Checkpoint**: Both individual and bulk deletion are fully functional and independently testable

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility refinements, error handling edge cases, and UX polish that span both user stories

- [ ] T010 [P] Add `aria-live` announcements for deletion outcomes in `frontend/app/dashboard/page.tsx`: add a visually hidden `<div aria-live="assertive" aria-atomic="true">` near the top of the page; after successful individual delete set its text to `"${name} has been deleted."`, after successful clear-all set it to `"All documents have been deleted."`, after failed deletion set it to `"Failed to delete document. Please try again."`; clear the announcement text after 5 seconds with `setTimeout`
- [ ] T011 [P] Add processing-state guard in `frontend/components/ProgressTracker.tsx`: when a document has `status === 'processing'`, render the delete button as disabled with `aria-disabled="true"` and `title="Cannot delete while processing"` instead of fully hiding it; add a tooltip or `title` attribute explaining why; in `function_app.py` the T003 endpoint already returns HTTP 409 for processing documents — ensure the frontend `deleteService.ts` maps 409 responses to a user-friendly error message like `"Cannot delete a document while it is being processed. Please wait for processing to complete."`
- [ ] T012 Verify keyboard navigation and focus management across the full delete flow in `frontend/components/ConfirmDialog.tsx` and `frontend/app/dashboard/page.tsx`: after ConfirmDialog closes (confirm or cancel), return focus to the element that triggered it (the delete button or Clear All button); ensure Tab order is logical within the dialog (Cancel → Confirm); ensure the dialog cannot be scrolled past (body scroll lock while open); test with screen reader announcement sequence: button press → dialog opens → title announced → user confirms → dialog closes → outcome announced via aria-live

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — adds backend service methods to existing `status_service.py`
- **Foundational (Phase 2)**: Depends on Phase 1 (needs `delete_document` and `delete_all_documents` methods) — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 (needs DELETE endpoint, `deleteService.ts`, `ConfirmDialog.tsx`)
- **User Story 2 (Phase 4)**: Depends on Phase 2 (needs DELETE-all endpoint, `deleteService.ts`, `ConfirmDialog.tsx`) — independent of US1
- **Polish (Phase 5)**: Depends on both US1 and US2 being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependency on US2
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) — No dependency on US1
- **US1 and US2 can proceed in parallel** once Phase 2 is complete

### Within Each User Story

- Backend endpoint before frontend integration
- Service layer before UI wiring
- Core interaction before polish

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different methods, same file but non-overlapping)
- **Phase 2**: T003+T004 in parallel (different endpoints in same file, but different route handlers); T005+T006 in parallel (different files entirely)
- **Post-Foundational**: US1 (Phase 3) and US2 (Phase 4) can start in parallel
- **Phase 5**: T010 and T011 can run in parallel (different files)

---

## Parallel Example: Foundational Phase

```bash
# Launch backend endpoints in parallel (different route handlers):
Task: T003 "Add DELETE /api/documents/{document_id} endpoint in function_app.py"
Task: T004 "Add DELETE /api/documents endpoint (clear all) in function_app.py"

# Launch frontend infrastructure in parallel (different files):
Task: T005 "Create deleteService.ts in frontend/services/deleteService.ts"
Task: T006 "Create ConfirmDialog.tsx in frontend/components/ConfirmDialog.tsx"
```

## Parallel Example: User Stories

```bash
# After Phase 2 completes, launch both stories in parallel:
# Developer A: User Story 1 (individual delete)
Task: T007 "Update ProgressTracker.tsx with delete button"
Task: T008 "Wire individual delete handler in dashboard/page.tsx"

# Developer B: User Story 2 (clear all)
Task: T009 "Add Clear All button and handler in dashboard/page.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Backend deletion methods in `status_service.py`
2. Complete Phase 2: DELETE endpoint + `deleteService.ts` + `ConfirmDialog.tsx`
3. Complete Phase 3: User Story 1 — Individual document deletion
4. **STOP and VALIDATE**: Test individual delete with uploaded documents
5. Deploy/demo if ready

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation ready (backend + shared components)
2. Add User Story 1 → Test independently → Deploy/Demo (**MVP!**)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Phase 5 Polish → Final accessibility & edge-case hardening

### Key Files Modified

| File | Changes |
|------|---------|
| `status_service.py` | Add `delete_document()`, `delete_all_documents()` |
| `function_app.py` | Add 2 DELETE endpoints |
| `frontend/services/deleteService.ts` | **New file** — API client for delete operations |
| `frontend/components/ConfirmDialog.tsx` | **New file** — Accessible confirmation dialog |
| `frontend/components/ProgressTracker.tsx` | Add `onDelete` prop + delete buttons per row |
| `frontend/app/dashboard/page.tsx` | Add delete/clear-all handlers, state, ConfirmDialog integration |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- The `ConfirmDialog` component is shared infrastructure — built once, used by both stories
- Backend enforces a processing-state guard (HTTP 409) to prevent data corruption
- All UI interactions must be WCAG 2.1 AA compliant (focus management, aria-live, keyboard nav)
- Blob deletions are permanent — confirmation dialogs are mandatory for both operations
- The frontend optimistically removes deleted documents from state (no re-poll needed)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
