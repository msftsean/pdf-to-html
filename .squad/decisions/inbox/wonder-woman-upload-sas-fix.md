# Decision: Azurite-Aware SAS URL Generation + 0-Byte Blob Guard

**Author:** Wonder-Woman (Backend Developer)  
**Date:** 2026-03-12  
**Status:** Implemented

## Context

File uploads were failing locally ("Conversion failed after 18ms") because of two independent bugs:
1. SAS upload URLs pointed at `https://devstoreaccount1.blob.core.windows.net/...` — a nonexistent Azure endpoint. Azurite listens at `http://127.0.0.1:10000/devstoreaccount1/...`.
2. The blob trigger fired on the 0-byte placeholder blob created for status tracking, crashing the conversion pipeline before the real file arrived.

## Decisions Made

### Azurite detection via `_is_azurite()` helper
- **Decision:** Added `_is_azurite(conn_str)` that checks for `UseDevelopmentStorage=true` or `127.0.0.1:10000` in the connection string. All SAS URL generation (upload and download) branches on this.
- **Rationale:** Single point of truth for "are we local?" avoids scattered if-checks. Works for both the shorthand and explicit Azurite connection strings.

### Well-known Azurite key in `_extract_account_key()`
- **Decision:** When Azurite is detected, `_extract_account_key()` returns the well-known dev account key instead of parsing `AccountKey=` from the connection string (which doesn't exist in the shorthand form).
- **Rationale:** `UseDevelopmentStorage=true` is a single token with no key-value pairs. Without this, SAS token generation raises `ValueError`.

### 0-byte blob guard in `file_upload()` blob trigger
- **Decision:** Added early return when `myblob.length == 0` at the top of the blob trigger function.
- **Rationale:** The placeholder blob is needed for immediate status tracking, but the conversion pipeline requires actual file data. The browser's SAS PUT overwrites the blob with real content, triggering the function again with data.

## Impact on Team
- **Flash (Frontend):** Upload flow should now work end-to-end locally. The `upload_url` returned by `/api/upload/sas-token` points to Azurite.
- **Cyborg (DevOps):** No infrastructure changes. Production Azure URLs are unchanged — the Azurite branch only activates for dev connection strings.
- **Aquaman (QA):** 0-byte placeholder blobs are now silently skipped. Status remains "pending" until the real upload arrives.
