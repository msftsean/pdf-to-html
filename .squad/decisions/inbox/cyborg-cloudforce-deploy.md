# Cloudforce Subscription Deployment

**Author:** Cyborg (DevOps & Infrastructure)  
**Date:** 2026-03-12  
**Status:** Completed

## Context

After hours fighting Azure infrastructure constraints in the MCAPS subscription (MCAPSGov policy blocking shared key access, SPN lacking RBAC permissions, cross-subscription complexity with different tenants), we pivoted to a fresh deployment in Sean's new Cloudforce Sponsorship subscription where he has Owner access.

The Azure CLI was already authenticated with a new SPN in the Cloudforce tenant, and we had a clean slate to deploy everything from scratch.

## Decision

Deploy ALL infrastructure in the Cloudforce Sponsorship subscription (`098ef2f6-cea4-4839-8093-ef90622e1b8c`) using full automation:

1. Resource Group: `rg-pdf-to-html` (eastus)
2. Storage Account: `stpdftohtml331ef3` with `allowSharedKeyAccess=true`
3. App Service Plan: `plan-pdftohtml` (B1 Linux)
4. Function App: `func-pdftohtml-331ef3` (Python 3.12, Functions v4)
5. Managed Identity: System-assigned on the Function App
6. RBAC Roles: Storage Blob Data Contributor, Storage Queue Data Contributor, Storage Account Contributor
7. App Settings: Connection string for AzureWebJobsStorage, OUTPUT_CONTAINER=converted
8. Code Deployment: `func azure functionapp publish` with remote build

## Rationale

- **No Policy Blockers**: Cloudforce subscription has no MCAPSGov policy. Shared key access works, enabling the standard connection string pattern.
- **Full Permissions**: The new SPN has Contributor + User Access Administrator roles, allowing complete RBAC automation without manual portal intervention.
- **Single-Tenant Deployment**: All resources in one subscription within one tenant. No cross-subscription complexity.
- **Proven Automation**: Used standard Azure CLI commands throughout. No workarounds, no ARM REST API hacks, no manual steps.
- **Clean Architecture**: B1 App Service Plan gives consistent performance and avoids Consumption plan's Azure Files dependency (which would have required shared key anyway).

## Results

✅ **Complete success.** All infrastructure deployed in ~15 minutes. Function App is running and responding (HTTP 200). Application Insights enabled. RBAC roles assigned and verified. Storage containers created. Code deployed with all dependencies.

The Cloudforce deployment is now the **production environment**. The MCAPS resources remain as legacy/reference but are not actively used.

## Impact on Other Agents

- **Wonder-Woman (Backend)**: Function App URL is `https://func-pdftohtml-331ef3.azurewebsites.net`. Storage connection uses the Cloudforce storage account. No code changes needed — the deployment handles everything.
- **Flash (Frontend)**: API endpoints remain the same contract. The frontend will point to the new Function App URL once configured.
- **Batman (Tech Lead)**: We now have a working production environment. Next steps: configure OCR endpoint, deploy frontend, set up CI/CD.
- **Aquaman (QA)**: Can begin end-to-end testing against the live environment.

## Key Learnings

1. **Subscription Policies Matter**: MCAPSGov policy was a hard blocker. No amount of workarounds could enable shared key access in that environment.
2. **SPN Permissions Are Critical**: Contributor alone is not enough for infrastructure automation. Need User Access Administrator (or Owner) for RBAC operations.
3. **Cross-Tenant = No Cross-Sub**: Cross-subscription access requires same Azure AD tenant. MCAPS and Cloudforce are in different tenants.
4. **Connection Strings > Identity-Based (When Possible)**: Shared key access is simpler, fewer moving parts, easier debugging. Identity-based auth is the fallback when policy blocks shared key.
5. **Fresh Start > Workarounds**: Sometimes it's faster to deploy everything fresh in a new environment than to fight policy constraints with elaborate workarounds.

## Resource Names (for reference)

- Resource Group: `rg-pdf-to-html`
- Storage Account: `stpdftohtml331ef3`
- App Service Plan: `plan-pdftohtml`
- Function App: `func-pdftohtml-331ef3`
- Function URL: `https://func-pdftohtml-331ef3.azurewebsites.net`
- Managed Identity Principal ID: `f6fed8bf-5932-410b-ba38-f32c5a47408e`
- Application Insights: `func-pdftohtml-331ef3`
