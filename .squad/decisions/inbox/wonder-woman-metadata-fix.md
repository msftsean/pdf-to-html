# Decision: Fix SAS Upload Metadata Loss

**Author:** Wonder-Woman  
**Date:** 2025-07-18  
**Status:** Implemented  
**Scope:** function_app.py, status_service.py

## Problem

When the browser uploads a file via SAS URL (HTTP PUT to Azure Blob Storage), the PUT operation replaces the entire blob — including all metadata. The placeholder blob created by `generate_sas_token()` carried all tracking metadata (`document_id`, `status`, `name`, etc.), but this was silently wiped on every real upload.

**Impact:** `_find_blob_by_id()` couldn't find the blob. `set_status()` silently failed. `list_documents()` skipped the blob because `"status" not in metadata`. Dashboard showed nothing for SAS-uploaded documents even though conversion succeeded.

## Solution — Three-Layer Defense

### Part 1: Return metadata in SAS token response
`generate_sas_token()` now includes a `metadata` object in its JSON response containing all 14 metadata fields. The frontend can set these as `x-ms-meta-*` HTTP headers on the PUT request, preserving metadata through the upload.

### Part 2: Safety net in blob trigger
`file_upload()` now checks whether the blob has metadata after the 0-byte guard. If `document_id` is missing from metadata, it reconstructs essential fields from the blob name (which follows the `<uuid>.<ext>` convention) and writes them back via `set_blob_metadata()`. This catches cases where the frontend doesn't (or can't) set the headers.

### Part 3: `_find_blob_by_id()` fallback
Added a middle tier to the lookup: after the fast metadata-match path fails, try matching by blob name prefix *without* requiring metadata. Only falls through to the expensive full-scan if the prefix scan also fails.

## Files Changed

- `function_app.py` — Parts 1 & 2
- `status_service.py` — Part 3
- `tests/unit/test_status_service.py` — 3 new tests for fallback lookup

## Test Results

174 tests pass (171 existing + 3 new). No regressions.

## Trade-offs

- Part 2 (reconstruction) uses the blob filename as a best-effort `name` field since the original filename is lost if the frontend didn't set headers. This is acceptable — it's a safety net, not the primary path.
- Part 3 adds one extra `list_blobs` call in the fallback path, but only when metadata is missing (not on the happy path).
