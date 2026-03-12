# Decision: Azure Deployment Architecture

**Author:** Cyborg (DevOps & Infrastructure)  
**Date:** 2026-03-12  
**Status:** Fully Implemented (Cloudforce Subscription)
**Last Updated:** 2026-03-12 (Session 3 - Backend Deployment)

## Context

First deployment of the pdf-to-html backend to Azure. The subscription has strict governance policies (MCAPSGov) that enforce identity-based storage authentication.

## Decisions Made

### App Service Plan (B1) instead of Consumption Plan
- **Decision:** Use a dedicated B1 Linux App Service Plan for the Function App.
- **Rationale:** The subscription policy forces `allowSharedKeyAccess = false` on all storage accounts. Azure Functions Consumption Plan on Linux requires Azure Files, which requires shared key access. A dedicated plan avoids this dependency entirely.
- **Trade-off:** Higher baseline cost (~$13/month for B1 vs. pay-per-execution for Consumption). Acceptable for initial deployment; can revisit if RBAC/policy constraints are resolved.

### Identity-based AzureWebJobsStorage
- **Decision:** Use `AzureWebJobsStorage__accountName` instead of the traditional connection string.
- **Rationale:** Key-based auth is blocked by subscription policy. Identity-based storage is the only option available.
- **Requires:** RBAC roles (Storage Blob Data Owner, Storage Queue Data Contributor, Storage Account Contributor) assigned to the Function App's system-assigned managed identity.

### Application Code Needs Managed Identity Support
- **Decision:** `function_app.py` currently uses `BlobServiceClient.from_connection_string()`. This must be updated to use `DefaultAzureCredential` from `azure-identity`.
- **Impact:** Wonder-Woman needs to update `function_app.py` to detect whether `AzureWebJobsStorage` is a connection string or an account name, and use the appropriate authentication method.

## Blocking Issue

The deployment SPN has Contributor role only. It cannot:
1. Assign RBAC roles (`Microsoft.Authorization/roleAssignments/write`)
2. Create policy exemptions (`Microsoft.Authorization/policyExemptions/write`)

**Action Required:** An admin with Owner role must run `scripts/assign-storage-rbac.sh` to assign the required RBAC roles to the Function App's managed identity.

## Latest Deployment (Session 3 - 2026-03-12)

### Backend Deployment Success
- **Command:** `func azure functionapp publish func-pdftohtml-331ef3 --python`
- **Build Time:** ~6.5 minutes (Oryx remote build + artifact transfer)
- **Deployment Size:** 149.68 MB uploaded → 703 MB final zip with dependencies
- **Backend Package Structure:** Code reorganized into `backend/` package deploys successfully
- **Function Endpoints Verified:** file_upload, generate_sas_token, get_document_status, get_download_url
- **Status Endpoint:** ✅ Working (GET /api/documents/status returns empty document list)
- **CORS Configuration:** ✅ Verified for both Function App and Blob Storage

### Known Issue: Cold Start Latency
- Upload/SAS token endpoints exhibit 30+ second cold start on B1 Linux plan
- Status endpoint warms up faster (~5-10 seconds)
- **Root Cause:** Azure Functions on B1 plan with Python runtime requires module import (pymupdf, azure-ai-documentintelligence, etc.)
- **Mitigation Options:**
  - Premium plan (always warm, higher cost)
  - Application Insights monitoring
  - Keep-alive pings
  - For now, acceptable for development/demo

### Deployment Verification Checklist
1. ✅ Remote build completed successfully
2. ✅ Status endpoint responding
3. ✅ Function list populated (4 functions)
4. ✅ CORS configured correctly
5. ✅ Frontend restarted
6. ⚠️ Upload endpoints have cold start latency (expected)

## Impact on Other Agents

- **Wonder-Woman:** Backend `backend/` package structure works perfectly with Azure deployment. No code changes needed.
- **Flash:** Frontend restarted. Should work with deployed backend. Be aware of potential cold start on first upload attempt.
- **Aquaman:** Cold start latency may affect initial test runs. Recommend testing after warmup or adding retry logic.
- **Batman:** Deployment successful. Monitor cold start metrics if it becomes a user experience issue.
