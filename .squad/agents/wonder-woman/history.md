# Wonder-Woman — History

## Session Log

- **2026-03-11:** Joined the squad as Backend Developer.
- **Phase 2 Backend Sprint:** Completed T008–T010, T017–T019.

## Learnings

- **Blob metadata as state store:** Azure Blob metadata (string key-value pairs) works well for tracking document status without a database. All values must be strings — serialize ints, bools, and lists explicitly. Reconstruction via `Document.from_metadata()` handles the parsing.
- **WCAG validation in Python is feasible for common rules:** A regex-based HTML parser catches 80%+ of server-side accessibility issues (missing alt, heading order, table headers, color contrast, form labels, empty links). Full axe-core validation still runs client-side.
- **SAS token flow:** The upload API creates an empty placeholder blob with metadata *before* the browser uploads. This ensures the status service can track the document immediately. The browser then overwrites the blob content via the SAS URL, which triggers the existing blob trigger.
- **Re-export pattern for models:** `models.py` imports and re-exports `TextSpan`, `ImageInfo`, `TableData`, `PageResult` from `pdf_extractor.py` so consumers can import from a single module. Avoids duplication while centralizing the data model.
- **Connection string key extraction:** Azure Storage connection strings use semicolon-delimited `Key=Value` pairs. `_extract_account_key()` parses `AccountKey=...` for SAS token generation. This avoids importing additional Azure Identity libraries for local dev.
- **Heading hierarchy enforcement:** PDF headings can skip levels (e.g. h1→h3) because PDFs don't enforce heading semantics. The `_enforce_heading_hierarchy()` function in html_builder.py flattens skipped levels down to prev+1 to pass WCAG 1.3.1. This runs after span-to-block conversion.
- **WCAG contrast thresholds for inline CSS:** figcaption color was #666 (3.95:1 on white — fails AA). Changed to #595959 (7.0:1). Table borders were #ccc — changed to #767676 (4.54:1). Always test contrast ratios against background explicitly.
- **OCR confidence scoring architecture:** OcrPageResult now carries `confidence` (float, 0.0–1.0) and `needs_review` (bool). Confidence is computed from Document Intelligence word-level scores averaged across the page. Pages below 0.70 threshold get review banners in the HTML and are tracked in blob metadata.
- **Graceful OCR failure pattern:** ocr_service.py now wraps both full-call and per-page processing in try/except. On failure, a stub OcrPageResult with confidence=0.0 and needs_review=True is returned so the pipeline continues without crashing. The html_builder renders a "Content Unavailable" notice for empty OCR results.
- **Blob trigger status lifecycle:** The blob trigger now follows a strict status flow: pending→processing→completed/failed. It times the entire conversion (time.monotonic), runs wcag_validator on the output HTML, collects OCR review_pages, and writes all metadata back via status_service.set_status(). On exception, it sets status to "failed" with the error context.
