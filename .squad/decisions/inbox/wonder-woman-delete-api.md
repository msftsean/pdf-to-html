# Decision: Delete API Backend Implementation

**Author:** Wonder-Woman (Backend Developer)
**Date:** 2026-03-13
**Status:** Implemented

## Context

Tasks T001–T004 from `specs/003-delete-runs/tasks.md` required backend support for deleting individual documents and bulk-clearing all documents from Azure Blob Storage.

## Decisions Made

**Processing-state guard (HTTP 409)**
- Decision: The `DELETE /api/documents/{document_id}` endpoint checks document status before deletion and refuses to delete documents with `status == "processing"`.
- Rationale: Deleting blobs mid-conversion could leave orphaned output or corrupt metadata. The 409 response gives the frontend a clear signal to show a user-friendly message.

**Output prefix derived from metadata, fallback to document_id**
- Decision: `delete_document()` reads the blob's `output_path` metadata to determine where output blobs live. If `output_path` is empty (document never processed), it falls back to `document_id + "/"`.
- Rationale: Using metadata is more robust than hardcoding assumptions about the blob naming convention. The fallback ensures pending/failed documents can still be cleaned up.

**Bulk deletion iterates per-container with independent error handling**
- Decision: `delete_all_documents()` wraps each container's iteration in its own try/except so a failure in the input container doesn't prevent output cleanup (and vice versa).
- Rationale: Partial cleanup is better than no cleanup. Counts are returned so the caller knows exactly what was deleted.

## Impact on Other Agents

- **Flash (Frontend):** Can now call `DELETE /api/documents/{id}` and `DELETE /api/documents`. Response shapes are documented in the task spec. Map HTTP 409 to a user-friendly "cannot delete while processing" message.
- **Aquaman (QA):** New endpoints need testing — especially the 409 guard, 404 for missing docs, and bulk deletion with mixed statuses.
- **Cyborg (DevOps):** No infrastructure changes. Deletion uses existing blob storage containers.
