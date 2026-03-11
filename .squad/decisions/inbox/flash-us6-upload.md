# Decision: US6 Upload Interface Architecture

**Author:** Flash (Frontend Developer)
**Date:** 2026-03-11
**Status:** Implemented

## Context

US6 requires a web upload interface with drag-and-drop, file validation, progress tracking, and NCDIT Digital Commons branding.

## Decisions Made

### 1. FileUpload is the only client component on the landing page

`page.tsx` remains a Server Component (no `'use client'`). Only `FileUpload.tsx` uses `'use client'`. This keeps the initial JS payload small (~95 kB first load) and lets Next.js statically generate the page shell.

### 2. Client-side validation duplicates uploadService validation

FileUpload validates file types and sizes *before* calling `uploadService.uploadDocument()`. The uploadService also validates. This dual validation gives instant user feedback while keeping the service layer defensive. Both now use 100 MB as the limit (raised from 50 MB per spec).

### 3. Error messages are user-friendly, not raw API errors

All upload errors are caught and mapped to plain-English messages. Network errors, SAS token failures, and timeouts each have specific friendly messages. The raw error is never shown to the user.

### 4. Drag counter pattern for reliable drag events

Used a `dragCounter` ref that increments on `dragenter` and decrements on `dragleave`. The drop zone's active state only changes when the counter reaches 0 or 1. This prevents the flickering caused by child elements firing their own drag events.

### 5. Page-level styles in globals.css, component styles in styled-jsx

Hero section, "How It Works" steps, and format card styles go in `globals.css` (they're used once on the page). FileUpload's styles are co-located via styled-jsx, following the pattern set by GovBanner, NCHeader, and NCFooter.

## Impact on Team

- **Wonder Woman (Backend):** The frontend now expects `POST /api/upload` to accept `{ filename, content_type, file_size }` and return `{ document_id, upload_url, expires_at }`. Max file size is 100 MB.
- **Aquaman (QA):** FileUpload needs screen reader testing for the `aria-live` announcements and keyboard navigation testing for the drop zone.
- **Batman (Tech Lead):** First Load JS increased from ~88 kB to ~95 kB. Still well within budget.
