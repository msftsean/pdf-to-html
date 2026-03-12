# Cyborg — History

## Session Log

- **2026-03-11:** Joined the squad as DevOps & Infrastructure.
- **2026-03-12 (Session 1):** First Azure deployment attempt in MCAPS subscription — provisioned storage, app service plan, function app, and deployed backend code. Blocked on RBAC role assignment (SPN has Contributor only, needs Owner for role assignment writes) and MCAPSGov policy blocking shared key access.
- **2026-03-12 (Session 2):** **SUCCESSFUL FULL DEPLOYMENT** in new Cloudforce Sponsorship subscription. Provisioned all infrastructure from scratch: resource group, storage account (with shared key access), app service plan (B1 Linux), function app (Python 3.12), managed identity, RBAC roles, and deployed function code. Everything working end-to-end.

## Learnings

### Subscription Policies & Permissions
- **MCAPSGov Policy (MCAPS sub only)**: Forces `allowSharedKeyAccess = false` on all storage accounts. Cannot be overridden — not even via ARM REST API or ARM template deployments. Makes key-based authentication impossible.
- **Cloudforce Sponsorship (New sub)**: No MCAPSGov policy. Shared key access works perfectly. This is the standard Azure experience.
- **SPN Permissions Matter**: The old SPN in MCAPS had only Contributor role (no role assignment write permission). The new SPN in Cloudforce has Contributor + User Access Administrator, enabling full RBAC automation.
- **Cross-Tenant != Cross-Sub**: Cross-subscription access requires both subscriptions to be in the same Azure AD tenant. MCAPS and Cloudforce are in different tenants, making cross-sub impossible.

### Architecture Decisions
- **Connection Strings vs Identity-Based Auth**: When shared key access is available, use connection strings (simpler, fewer moving parts). When blocked by policy, fall back to identity-based (`AzureWebJobsStorage__accountName` + RBAC roles).
- **App Service Plan (B1) over Consumption Plan**: Consumption plan requires Azure Files which requires shared key access. Since MCAPS policy blocked shared key, we used B1 Linux instead. In Cloudforce, either would work, but B1 gives consistent performance and easier debugging.
- **RBAC Roles for Functions**: Managed identity needs: Storage Blob Data Contributor, Storage Queue Data Contributor, Storage Account Contributor (for Functions runtime metadata operations).

### Deployment Automation
- **func azure functionapp publish**: Works reliably for Python Azure Functions. Remote build with Oryx handles all dependencies. Typical deployment: ~10 minutes including pip install.
- **Identity Propagation Delay**: After creating a managed identity, wait 5-10 seconds before assigning RBAC roles to avoid race conditions.
- **Container Creation via CLI**: When shared key works, use `az storage container create --connection-string`. When blocked, use ARM control-plane API (`az rest --method put`).

### Subscription Comparison
| Feature | MCAPS (`4b27ac87...`) | Cloudforce (`098ef2f6...`) |
|---------|----------------------|----------------------------|
| Shared Key Access | ❌ Blocked by policy | ✅ Allowed |
| SPN Permissions | Contributor only | Contributor + UAA |
| RBAC Automation | ❌ Manual portal needed | ✅ Fully automated |
| Cross-Sub Storage | ❌ Different tenant | N/A (not needed) |
| Deployment Success | ❌ Partial | ✅ Complete |

### Key Resource Names
- **MCAPS Subscription** (`4b27ac87-dec6-45d5-8634-b9f71bd1dd26`) — LEGACY/ABANDONED:
  - Function App: `func-pdftohtml-284728`
  - App Service Plan: `plan-pdftohtml`
  - Resource Group: `rg-pdf-to-html` (location: `northcentralus`)
  - Old storage (unusable): `stpdftohtml284588`
  - MSI Principal ID: `350374e1-8c09-4553-9eac-1e983ea9f5b0`
- **Cloudforce Sponsorship Subscription** (`098ef2f6-cea4-4839-8093-ef90622e1b8c`) — **ACTIVE**:
  - Tenant ID: `8251a5cb-be5c-4a08-b918-4ebc01628829`
  - SPN Client ID: `361cf2bc-9059-4e75-8a97-27c1aee974f6`
  - Resource Group: `rg-pdf-to-html` (location: `eastus`)
  - Storage Account: `stpdftohtml331ef3` (Standard_LRS, StorageV2, shared key ENABLED)
  - Containers: `files`, `converted`
  - App Service Plan: `plan-pdftohtml` (B1, Linux)
  - Function App: `func-pdftohtml-331ef3` (Python 3.12, Functions v4)
  - Function URL: `https://func-pdftohtml-331ef3.azurewebsites.net`
  - MSI Principal ID: `f6fed8bf-5932-410b-ba38-f32c5a47408e`
  - Application Insights: `func-pdftohtml-331ef3`

### Key File Paths
- `scripts/setup-cross-sub-storage.sh` — **NEW** Full cross-sub setup (RG, storage, containers, RBAC, Function App settings)
- `scripts/assign-storage-rbac.sh` — Updated for cross-sub storage scope
- `function_app.py` — Uses `BlobServiceClient.from_connection_string()` — needs update to `DefaultAzureCredential` for managed identity
- `.funcignore` — Already configured, excludes test files and local settings
- `host.json` — Functions v2 config with extension bundle [4.*, 5.0.0)

### Frontend Deployment (2026-03-12)
- **Approach**: Azure App Service (Node.js 20 LTS) on the existing `plan-pdftohtml` B1 Linux plan. Chose App Service over Static Web Apps because Next.js 14 uses Server Components/SSR and the B1 plan was already provisioned.
- **Next.js Standalone Mode**: Added `output: 'standalone'` to `next.config.mjs` for self-contained deployment. The standalone build bundles only required `node_modules` (~5.5 MB zip).
- **Frontend App Service**: `app-pdftohtml-frontend` in `rg-pdf-to-html` (eastus)
- **Frontend URL**: `https://app-pdftohtml-frontend.azurewebsites.net`
- **API URL**: `NEXT_PUBLIC_API_URL=https://func-pdftohtml-331ef3.azurewebsites.net/api` (set as app setting + baked into build)
- **CORS**: Configured on `func-pdftohtml-331ef3` to allow `https://app-pdftohtml-frontend.azurewebsites.net`
- **Startup Command**: `node server.js` (Next.js standalone server on port 3000, mapped via `WEBSITES_PORT=3000`)
- **Gotcha**: `NEXT_PUBLIC_*` env vars are baked into the Next.js build at compile time, not read at runtime. Must set `NEXT_PUBLIC_API_URL` in the build environment, not just as an app setting. The app setting is there for documentation/reference only.

### Backend Deployment (2026-03-12 Session 3)
- **Deployment Method**: `func azure functionapp publish func-pdftohtml-331ef3 --python` with remote build
- **Build Time**: ~6.5 minutes (391 seconds Oryx build + artifact transfer)
- **Remote Build Details**: Oryx automatically installs Python 3.12.12, runs pip install from requirements.txt, and packages everything into .python_packages/lib/site-packages
- **Deployment Artifacts**: 149.68 MB uploaded, 703 MB final zip with all dependencies
- **Backend Package Structure**: Code reorganized into `backend/` package (pdf_extractor, ocr_service, html_builder, models, status_service) - imports work correctly after deployment
- **Function Endpoints**: `/api/file_upload`, `/api/generate-sas-token`, `/api/get_document_status`, `/api/get_download_url` (verified via `az functionapp function list`)
- **Cold Start Issue**: Upload/SAS endpoints exhibit 30+ second cold start on B1 plan after deployment. Status endpoint (GET) warms up faster. This is expected behavior for Azure Functions on Consumption/Basic plans with Python runtime.
- **CORS Verified**: Function App CORS allows `https://app-pdftohtml-frontend.azurewebsites.net`, Blob Storage CORS allows PUT with x-ms-meta-* headers from frontend origin
- **Frontend Restart**: Restarted `app-pdftohtml-frontend` to ensure it picks up any connection changes

### Deployment Troubleshooting Notes
- **Resource Group Name**: Correct name is `rg-pdf-to-html` (NOT `rg-pdftohtml`)
- **Cold Start Mitigation**: For production, consider Premium plan (always warm) or configure Application Insights to monitor cold start metrics
- **Function Naming Convention**: Azure Functions automatically converts snake_case function names to kebab-case URLs (e.g., `generate_sas_token` → `/api/generate-sas-token`)
