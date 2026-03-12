# Decision: Identity-Based Storage Auth Support

**Author:** Wonder-Woman (Backend Developer)  
**Date:** 2026-03-12  
**Status:** Implemented

## Context

After Cyborg deployed the backend to Azure with identity-based storage authentication (`AzureWebJobsStorage__accountName` + managed identity), all blob operations in `function_app.py` crashed. The code exclusively used `os.environ["AzureWebJobsStorage"]` to get a connection string, which doesn't exist in identity-based setups.

## Decisions Made

### Dual-Mode BlobServiceClient
- **Decision:** `_get_blob_service_client()` now auto-detects connection string vs. identity-based auth.
- **Rationale:** Supports local Azurite, connection-string deployments, and identity-based Azure deployments from a single code path. No environment-specific branches needed in calling code.

### UserDelegationKey for SAS Tokens
- **Decision:** SAS tokens are generated via `UserDelegationKey` when no account key is available (identity-based auth), using account key for local/Azurite.
- **Rationale:** `generate_blob_sas()` accepts either `account_key` or `user_delegation_key`. This is the standard Azure pattern for SAS generation with managed identity.
- **Requires:** `Storage Blob Delegator` RBAC role (added to `scripts/assign-storage-rbac.sh`).

### Robust 0-Byte Guard
- **Decision:** The blob trigger reads `file_data = myblob.read()` early and checks `len(file_data) == 0`, in addition to the existing `myblob.length` check.
- **Rationale:** `myblob.length` can be `None` with Azurite, bypassing the original guard and causing `EmptyFileError` crashes.

## Impact on Other Agents

- **Cyborg:** Must run updated `scripts/assign-storage-rbac.sh` to add `Storage Blob Delegator` role to the Function App MSI before redeploying.
- **Flash:** No changes needed. API contracts unchanged.
- **Aquaman:** Conversion pipeline end-to-end test confirmed working. All 174 tests pass.
