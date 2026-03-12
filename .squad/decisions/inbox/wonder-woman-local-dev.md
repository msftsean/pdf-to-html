# Decision: Local Dev Setup with Azurite

**Author:** Wonder-Woman (Backend Developer)
**Date:** 2026-03-12
**Status:** Implemented

## Context

Sean needs to test the function app locally while Cyborg deploys Azure infrastructure. The backend uses Azure Blob Storage for file uploads and converted output.

## Decisions Made

**Azurite with `--skipApiVersionCheck` for local blob storage**
- Decision: Use Azurite (npm) with `--skipApiVersionCheck` flag for local development.
- Rationale: The azure-storage-blob Python SDK sends API version 2026-02-06 which Azurite's current release doesn't natively support. The flag bypasses version validation without affecting functionality.

**Explicit container creation step**
- Decision: Containers `files` and `converted` must be created manually after starting Azurite (via Python SDK or az CLI).
- Rationale: Unlike Azure, Azurite starts with no containers. The function app expects both containers to exist.

**local.settings.json with CORS wildcard**
- Decision: Created `local.settings.json` with `"CORS": "*"` for local dev.
- Rationale: Enables the Next.js frontend (port 3000) to call the function app (port 7071) without CORS issues during development.

## Impact on Team
- **Flash (Frontend):** Can now run the frontend against `http://localhost:7071/api` with no CORS issues.
- **Cyborg (DevOps):** No infra changes needed. Local dev is fully self-contained.
- **Aquaman (QA):** All 171 tests pass locally. Can run `pytest tests/` to verify.
- **Sean:** Full local dev environment ready — see startup commands below.

## Quick Start Commands
```bash
# 1. Start Azurite
azurite --silent --location /tmp/azurite-data --skipApiVersionCheck &

# 2. Create containers (one-time)
python3 -c "
from azure.storage.blob import BlobServiceClient
conn = 'DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'
client = BlobServiceClient.from_connection_string(conn)
for c in ['files', 'converted']:
    client.create_container(c)
"

# 3. Start function app
func start

# 4. Test it
curl http://localhost:7071/api/documents/status
```
