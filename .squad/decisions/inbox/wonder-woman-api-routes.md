# Decision: Frontend API Routes Aligned to Backend (Source of Truth)

**Author:** Wonder-Woman (Backend Developer)  
**Date:** 2025-07-18  
**Status:** Implemented

## Context

Frontend services (`statusService.ts`, `uploadService.ts`) were calling API routes that didn't match the backend's actual Azure Functions routes, causing 404 errors misidentified as ERR_CONNECTION_REFUSED.

## Mismatches Found & Fixed

| Service | Frontend (before) | Backend (actual) | Fix Applied |
|---|---|---|---|
| Upload | `POST /api/upload` | `POST /api/upload/sas-token` | Updated frontend |
| Upload body | `file_size` field | `size_bytes` field | Updated frontend |
| Status (all) | `GET /api/status` | `GET /api/documents/status` | Updated frontend |
| Status (single) | `GET /api/status/:id` | `GET /api/documents/status?document_id=:id` | Updated frontend |
| Download | `GET /api/documents/:id/download` | `GET /api/documents/:id/download` | Already matched |

## Decision

**Backend routes are the source of truth.** Frontend was updated to match.

### Rationale
- Backend routes follow RESTful conventions (`/documents/status`, `/upload/sas-token`) and are already deployed/tested.
- Changing backend routes would break any existing integrations and require redeploying Azure Functions.
- Frontend changes are purely client-side string updates with zero risk.

## Canonical Route Table

All frontend services must use these exact routes:

```
POST /api/upload/sas-token          → requestSasToken()
GET  /api/documents/status          → getDocumentStatuses()
GET  /api/documents/status?document_id=X → getDocumentStatus(X)
GET  /api/documents/{id}/download   → getDownloadUrl()
```

## Impact
- **Flash (Frontend):** Routes are now fixed in all three service files. No UI changes needed.
- **Aquaman (QA):** Integration tests should use the canonical routes above.
- **Cyborg (DevOps):** No infrastructure changes.
