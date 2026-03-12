# Phase 13 Backend Hardening — Technical Decisions

**Author:** Wonder-Woman (Backend Developer)  
**Date:** 2026-03-12  
**Status:** Implemented  
**Tasks:** T071–T074

## Context

Phase 13 focused on production readiness: handling edge cases (password-protected files, concurrent uploads), improving WCAG compliance (multi-language support), and adding resilience (blob storage retry logic).

## Decisions Made

### 1. Password-Protected Document Detection Strategy (T071)

**Decision:** Detect encrypted documents at the blob trigger stage before extraction begins.

**Implementation:**
- **PDFs:** Use PyMuPDF's `doc.is_encrypted` property after opening the document
- **DOCX/PPTX:** Catch exceptions from python-docx/python-pptx that contain keywords "password", "encrypt", or "protected"
- Set document status to "failed" immediately with error message: "This document is password-protected. Please remove the password and re-upload."

**Rationale:**
- Early detection saves processing cycles — no point extracting content from an inaccessible document
- User-facing error message is clear and actionable
- Prevents wasting Azure Document Intelligence credits on encrypted scanned PDFs

**Alternatives Considered:**
- **Allow password input:** Rejected — adds UI complexity, introduces security concerns (password storage), and increases attack surface
- **Detect at SAS token generation:** Rejected — would require downloading/inspecting the file before generating the URL, adding latency to the upload flow

### 2. Multi-Language Detection Heuristics (T072)

**Decision:** Use lightweight character frequency + function word patterns for language detection. Apply `lang` attributes to `<section>` elements when detected language differs from document default.

**Implementation:**
- Portuguese first (unique markers: ã, õ)
- French second (àâæèêë, excluding ç)
- Spanish third (ñ and accented vowels)
- German (äöüß + common words like "der", "die", "das")
- Italian (function words: "il", "la", "di", "è")
- Falls back to document default for English/ambiguous content

**Rationale:**
- **WCAG 3.1.2 (Language of Parts):** Requires `lang` attribute on content sections in different languages
- Heuristics are "good enough" for government documents (typically monolingual or bilingual)
- Avoids external dependencies (langdetect, langid) which add 2MB+ to deployment package
- Checking order matters: Portuguese and French share some accents (à, ô) — ã/õ are unique to Portuguese

**Alternatives Considered:**
- **External library (langdetect):** Rejected — adds dependencies, increases cold start time, overkill for our use case
- **Azure Cognitive Services Text Analytics:** Rejected — adds cost, API latency, requires separate service provisioning
- **No detection (default to "en" everywhere):** Rejected — violates WCAG 3.1.2 for multi-language documents

### 3. Exponential Backoff Retry for Blob Operations (T073)

**Decision:** Wrap all Azure Blob Storage operations in a retry wrapper with exponential backoff + jitter.

**Implementation:**
- Max 3 retries
- Initial delay: 1s, then 2s, then 4s (exponential backoff)
- Jitter: random 0–50% added to each delay to prevent thundering herd
- Only retry transient errors: `ServiceResponseError`, `ServiceRequestError`, `HttpResponseError`
- Log each retry attempt with attempt number and delay
- Re-raise non-transient exceptions immediately (ValueError, TypeError)

**Rationale:**
- Azure Blob Storage can experience transient failures (throttling, network issues, service updates)
- Exponential backoff prevents overwhelming the service during recovery
- Jitter prevents multiple workers from retrying simultaneously
- Logging helps diagnose persistent issues in production

**Alternatives Considered:**
- **No retries:** Rejected — transient failures would cause document conversions to fail unnecessarily
- **Fixed delay retry:** Rejected — doesn't back off during service degradation, can worsen the problem
- **Unlimited retries:** Rejected — could cause blob trigger to time out (10min limit for consumption plan)

### 4. Filename Conflict Handling (T074)

**Decision:** Use UUID-based blob names (`{document_id}.pdf`) instead of original filenames. Store original filename in blob metadata.

**Implementation:**
- Generate `document_id = str(uuid.uuid4())` for each upload
- Blob name: `{document_id}{extension}` (e.g., "abc-123-def.pdf")
- Metadata field: `original_filename = "My Report.pdf"`
- Display name in UI uses `metadata["name"]` (basename without extension)

**Rationale:**
- **UUID collision probability is negligible:** 2^122 possible UUIDs — would need 2.7 quintillion uploads before 50% collision chance
- Eliminates race conditions entirely — no conflict detection logic needed
- Preserves original filename for display without allowing it to affect storage
- Works transparently with existing status tracking (document_id is already the primary key)

**Alternatives Considered:**
- **Timestamp suffix (report.pdf → report_20260312_153045.pdf):** Rejected — still allows collisions if uploads happen within the same second
- **Check-and-append counter (report.pdf → report_1.pdf):** Rejected — requires read-modify-write transaction, adds latency, still has race condition
- **Hash of content + filename:** Rejected — requires reading file content before upload (breaks SAS token flow)

## Impact on Other Team Members

- **Flash (Frontend):** No API contract changes. Password-protected uploads will receive 409 status with descriptive error message. Multi-language documents will render with correct `lang` attributes (improves screen reader experience).
- **Aquaman (QA):** New test fixtures for encrypted documents (`test_phase13_hardening.py`). Language detection tests verify 5 languages (Spanish, French, German, Italian, Portuguese).
- **Cyborg (DevOps):** No infrastructure changes. Retry logic handles transient Azure failures gracefully, reducing false-positive alerts.

## Follow-up Tasks

- [ ] Monitor retry logs in production to identify persistent blob storage issues
- [ ] Consider adding language detection confidence score for review flagging (future enhancement)
- [ ] Add telemetry for password-protected document rejection rate (useful for support team)
