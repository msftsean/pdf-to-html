# Decision: Preview Proxy via Next.js API Route

**Date:** 2025-07-14  
**Author:** Flash (Frontend)  
**Status:** Implemented

## Context

The preview iframe tried to load HTML directly from Azurite blob storage at
`http://127.0.0.1:10000/devstoreaccount1/...`. In GitHub Codespaces the browser
runs on a remote machine and cannot reach that address — it's only accessible
from the server.

## Decision

Added a Next.js server-side API route at `/api/preview/[documentId]` that:

1. Calls the backend `/api/documents/:id/download` to get the signed URL
2. Fetches the HTML content from that URL **server-side** (where Azurite is reachable)
3. Returns the HTML to the browser with `Content-Type: text/html`

The dashboard now sets `previewUrl` to `/api/preview/<id>` instead of calling
`getDownloadUrl` client-side.

## Rewrite Rules

The existing `next.config.mjs` rewrite (`/api/:path* → backend`) was updated to
exclude `/api/preview/*` using a negative lookahead pattern. This ensures the
preview route is handled by Next.js itself while all other `/api/*` traffic
continues to proxy to the Azure Functions backend.

## Files Changed

- `frontend/app/api/preview/[documentId]/route.ts` — new proxy route
- `frontend/app/dashboard/page.tsx` — simplified preview handler
- `frontend/next.config.mjs` — rewrite exclusion for `/api/preview/*`
