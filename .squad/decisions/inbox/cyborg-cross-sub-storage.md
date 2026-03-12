# Decision: Cross-Subscription Storage Architecture

**Author:** Cyborg (DevOps)  
**Date:** 2025-07-18  
**Status:** ⏳ Blocked — waiting on Sean  
**Requested by:** Sean Gayle

## Context

The MCAPS subscription (`4b27ac87-dec6-45d5-8634-b9f71bd1dd26`) has two compounding problems that make it impossible to set up working storage for the Function App:

1. **MCAPSGov policy** forces `allowSharedKeyAccess = false` on all storage accounts — no connection strings allowed.
2. **SPN has Contributor only** — cannot assign RBAC roles (needs Owner or User Access Administrator).

Without RBAC roles on the storage account, the Function App's managed identity can't read or write blobs, and the SPN can't fix that.

## Decision

Move the storage account to Sean's other subscription (`098ef2f6-cea4-4839-8093-ef90622e1b8c`) where he has **Owner** access. The Function App remains in the MCAPS subscription and connects to the cross-subscription storage via managed identity (`AzureWebJobsStorage__accountName`).

## Architecture

```
┌─ MCAPS Sub (4b27ac87-...) ──────────────┐     ┌─ Sean's Sub (098ef2f6-...) ─────────────┐
│                                          │     │                                          │
│  func-pdftohtml-284728                   │     │  stpdftohtmldata                         │
│  (Function App + Managed Identity)       │────▶│  (Standard_LRS, StorageV2)               │
│  MSI: 350374e1-...                       │     │  Containers: files, converted             │
│                                          │     │  RG: rg-pdf-to-html-storage               │
└──────────────────────────────────────────┘     └──────────────────────────────────────────┘
```

## Current Blocker

**The SPN (`894189e2-b616-429a-9871-17acfc3a7614`) has NO access to subscription `098ef2f6-...`.**

### Sean must run this command (as Owner on that subscription):

```bash
az role assignment create \
  --assignee 894189e2-b616-429a-9871-17acfc3a7614 \
  --role Contributor \
  --scope /subscriptions/098ef2f6-cea4-4839-8093-ef90622e1b8c
```

Or do it via Azure Portal:
1. Go to subscription `098ef2f6-cea4-4839-8093-ef90622e1b8c` → Access control (IAM)
2. Add role assignment → Contributor
3. Select member: search for the SPN app ID `894189e2-b616-429a-9871-17acfc3a7614`

### After that, run the automation:

```bash
./scripts/setup-cross-sub-storage.sh
```

This will create the storage account, containers, assign RBAC for both the MSI and SPN, update the Function App settings, and verify health.

## Risks

- **Cross-sub latency**: Minimal — both subs are in the same Azure tenant (`16b3c013-...`), same region available.
- **Cost isolation**: Storage costs go to Sean's subscription, compute costs stay in MCAPS.
- **Networking**: No VNet restrictions expected, but firewall rules may need updating if storage account firewall is enabled.

## Team Impact

- **Flash/Wonder Woman**: No code changes needed — storage container names stay the same (`files`, `converted`).
- **Batman**: Architecture doc should note the cross-sub topology.
- **Aquaman**: No impact on test strategy — Azurite still used locally.

## Files Changed

- `scripts/setup-cross-sub-storage.sh` — NEW: Full cross-sub automation script
- `scripts/assign-storage-rbac.sh` — UPDATED: Points at new storage scope
- `.squad/agents/cyborg/history.md` — Updated with cross-sub learnings
