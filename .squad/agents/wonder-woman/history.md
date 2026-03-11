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
