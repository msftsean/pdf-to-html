# Decision: Frontend Deployment to Azure App Service

**Author:** Cyborg (DevOps & Infrastructure)
**Date:** 2026-03-12
**Status:** Implemented

## Context

The Next.js frontend needed a public deployment target. Three options were evaluated:
1. Azure Static Web Apps — good for static/hybrid, but Next.js 14 SSR support can be limited
2. Azure App Service — full Node.js runtime, SSR support, existing B1 plan available
3. Azure Storage static website — no SSR, no server-side logic

## Decision

**Azure App Service (Node.js 20 LTS)** on the existing `plan-pdftohtml` B1 Linux plan.

### Rationale
- Next.js 14 uses Server Components requiring a Node.js runtime
- The B1 App Service Plan was already provisioned for the Function App — adding a second web app costs nothing extra
- Full control over startup, environment, and scaling
- Simpler than Static Web Apps for SSR workloads

## Resources Created
- **App Service**: `app-pdftohtml-frontend` in `rg-pdf-to-html` (eastus)
- **URL**: https://app-pdftohtml-frontend.azurewebsites.net
- **CORS**: Added `https://app-pdftohtml-frontend.azurewebsites.net` to `func-pdftohtml-331ef3`

## Configuration
- `output: 'standalone'` in `next.config.mjs`
- `NEXT_PUBLIC_API_URL=https://func-pdftohtml-331ef3.azurewebsites.net/api`
- `WEBSITES_PORT=3000`, startup: `node server.js`

## Impact on Team
- **Flash**: `next.config.mjs` now has `output: 'standalone'` — this changes the build output structure. Local dev (`next dev`) is unaffected.
- **Sean**: Frontend is publicly accessible at the URL above.
- **All**: Future frontend deploys should rebuild with `NEXT_PUBLIC_API_URL` set, then zip `.next/standalone/` and deploy via `az webapp deploy`.
