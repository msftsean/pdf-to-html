# Decision: Azure Container Apps IaC + CI/CD Pipeline

**Author:** Cyborg (DevOps)
**Date:** $(date -u +%Y-%m-%d)
**Status:** Implemented (pending deployment)

## Context

The project is migrating from Azure Functions to Azure Container Apps to gain:
- Sidecar/multi-container support for future OCR workers
- KEDA-based autoscaling (queue-driven worker scaling 0→10)
- Better control over runtime, health probes, and resource allocation
- Unified container-based deployment across API, Worker, and Frontend

## Decisions

### 1. Infrastructure as Code with Bicep (not Terraform)
**Why:** Azure-native, first-class support in `az deployment`, no state file management needed. Team already uses Azure CLI heavily. Bicep modules are composable and type-safe.

### 2. ACR Tasks for CI image builds (not Docker-in-Docker)
**Why:** `az acr build` offloads image building to Azure — no Docker daemon needed in GitHub Actions. Faster, more secure, and images are built close to the registry (no push latency).

### 3. Managed Identity for ACR pull (not admin credentials)
**Why:** Zero secrets. User-Assigned Managed Identity with AcrPull role lets Container Apps pull images without storing registry passwords. Aligned with project constitution (identity-based auth, no shared keys in code).

### 4. Worker scales on queue length = 1
**Why:** PDF conversion is CPU-intensive (10–60s per document). One message = one replica ensures each conversion gets dedicated resources. Max 10 replicas prevents runaway costs while supporting burst uploads.

### 5. Event Grid for blob-to-queue routing (not polling)
**Why:** Event-driven architecture. Event Grid's BlobCreated filter on `/blobServices/default/containers/files/` with `contentLength > 0` ensures only real uploads trigger conversion. No polling, no wasted compute.

### 6. Single image for API + Worker
**Why:** Both use the same Python codebase. The worker overrides the command to `python -m app.worker` instead of running uvicorn. One build, two deployments — simpler CI, consistent dependencies.

### 7. Pytest added to eval workflow
**Why:** The eval workflow previously only ran WCAG evaluations. Adding pytest ensures unit tests run on every PR alongside accessibility checks. Tests use Azurite (already started by the workflow).

## Risks

- **Storage connection string in env vars:** Currently passed as plaintext env var. Future improvement: use managed identity for storage access (requires app code changes to use DefaultAzureCredential).
- **Single region:** No multi-region failover. Acceptable for current scale (NC state government internal tool).
- **ACR Basic SKU:** No geo-replication, no retention policies. Upgrade to Standard if image storage grows.

## Files Created

- `.github/workflows/deploy-aca.yml`
- `infra/main.bicep`
- `infra/modules/container-registry.bicep`
- `infra/modules/container-apps.bicep`
- `infra/modules/event-grid.bicep`
- `infra/parameters/dev.bicepparam`
- `infra/parameters/prod.bicepparam`
