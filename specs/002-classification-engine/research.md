# Research: Document Classification Engine

**Phase 0 Output** | **Date**: 2026-03-12

## R1: Classification Approach for Phase 1

**Decision**: Lightweight heuristic analysis using PyMuPDF page-level
metrics (text density, image ratio, object count, page dimensions).

**Rationale**: The ADR recommends Option C (heuristics) as the immediate
Phase 1 approach. This is the right choice because:
- Zero external API calls = zero additional cost and latency
- 1–2 day implementation timeline fits the compressed DOJ deadline
- Establishes the pipeline gate architecture and warning UX patterns
  that persist into future ML-based phases
- PyMuPDF already parses every page during extraction — we reuse the
  same library for pre-extraction analysis at negligible cost
- The existing `_classify_page()` function in `pdf_extractor.py` already
  demonstrates this pattern (text length threshold for scanned detection)

**Alternatives considered**:
- Azure AI Foundry custom model (Option A): Highest accuracy but requires
  100–200 labeled documents and 7–14 day training cycle; premature without
  ground truth data
- Azure Document Intelligence classifier (Option B): Limited to standard
  document types (invoice, contract); doesn't recognize brochures,
  newsletters, or slide decks; deprecating
- Pre-trained multimodal model (GPT-4V, Florence): Adds latency (2–5s per
  document), cost, and external dependency; overkill for document-level
  classification that doesn't need visual understanding

## R2: Heuristic Signals and Thresholds

**Decision**: Use four primary heuristic signals with weighted scoring:

| Signal | Metric | High-Suitability Range | Low-Suitability Range |
|--------|--------|----------------------|---------------------|
| Text density | chars per page / page area | >0.003 | <0.001 |
| Image ratio | total image area / total page area | <0.30 | >0.60 |
| Object count | drawings + annotations per page | <5 avg | >15 avg |
| Page uniformity | std deviation of text density across pages | <0.002 | >0.005 |

**Rationale**: These signals map directly to the problem statement:
- Brochures have high image ratio + high object count + low text density
- Slide decks have low text density + high image ratio + variable layouts
- Forms have moderate text density but high object count (fields, boxes)
- Reports have high text density + low image ratio + uniform page layouts
- Newsletters have moderate text density but high layout variability

Research into PyMuPDF's page analysis capabilities confirms all four signals
are extractable without OCR or rendering:
- `page.get_text("text")` → text density calculation
- `page.get_images()` → image area calculation
- `page.get_drawings()` → object/annotation count
- `page.rect` → page dimensions for normalization

**Alternatives considered**:
- Font diversity analysis: Complex to implement; diminishing returns for
  Phase 1 accuracy targets
- Color analysis: Requires rendering; adds latency; useful for brochure
  detection but not essential for MVP
- Structural element analysis (headers, footers): Already extracted by
  the existing pipeline; could augment Phase 2

## R3: Suitability Score Threshold

**Decision**: 0.70 threshold for warning generation. Documents scoring
≥0.70 proceed silently; documents <0.70 get a user-facing warning but
still proceed to conversion.

**Rationale**: The ADR recommends 0.70 based on alignment with the existing
OCR confidence threshold (also 0.70 — see `EnhancedPageResult` in
`models.py` line 337). Using the same threshold creates cognitive
consistency for users ("0.70 = needs attention" is a shared mental model).

Starting at 0.70 is conservative enough to catch clearly unsuitable
documents (brochures scoring ~0.3, slide decks ~0.4) while avoiding
false positives on mixed documents. The ADR notes 0.80 as an alternative
if false positive rate is too high — this can be tuned post-deployment.

**Alternatives considered**:
- 0.50 threshold: Too aggressive; would warn on too many valid documents
- 0.80 threshold: Too conservative; would miss borderline cases
- Tiered thresholds (0.50 = reject, 0.70 = warn): ADR explicitly
  recommends never rejecting; single threshold is simpler

## R4: Classification Result Storage

**Decision**: Store classification results as blob metadata fields on the
document's blob in the `files/` container, extending the existing metadata
pattern used by `status_service.py`.

**Rationale**: The project already stores document status as blob metadata
(see `status_service.py` and `models.py` `to_metadata()`/`from_metadata()`).
Adding classification fields (`classification_type`, `suitability_score`,
`classification_confidence`, `classification_warning`) follows the same
pattern with zero new infrastructure.

Blob metadata is queryable by the status API (already implemented), so
the frontend can read classification results through the existing polling
mechanism without API changes.

**Alternatives considered**:
- Separate classification table (Azure Table Storage): Adds infrastructure;
  violates "no separate database" principle in status_service.py
- In-memory only: Loses classification data if function restarts; can't
  display in frontend
- Azure Cosmos DB: Massive overkill for key-value metadata

## R5: Document Type Taxonomy

**Decision**: Initial taxonomy of 7 document types for Phase 1:

| Type | Expected Suitability | Description |
|------|---------------------|-------------|
| `report` | 0.85–1.0 | Text-heavy, structured headings, data tables |
| `whitepaper` | 0.80–0.95 | Similar to report, may have more figures |
| `form` | 0.40–0.65 | Field layouts, checkboxes, spatial structure |
| `brochure` | 0.15–0.40 | Image-heavy, multi-column, visual layout |
| `newsletter` | 0.30–0.55 | Mixed content, varied layouts, color-dependent |
| `slide_deck` | 0.20–0.45 | Low text density, image-heavy, positional |
| `unknown` | 0.50 | Default when heuristics are inconclusive |

**Rationale**: These 7 types cover the document categories flagged in the
ADR and align with the NC state website document corpus (annual reports,
policy papers, agency brochures, departmental newsletters, training
presentations, permit forms). The `unknown` fallback ensures no document
is un-typed.

**Alternatives considered**:
- Finer taxonomy (20+ types): Over-engineered for heuristic classification;
  accuracy drops with more categories
- Binary classification (suitable/unsuitable): Loses valuable type
  information needed for targeted warning messages
- Hierarchical taxonomy (document → sub-type): Adds complexity; flat
  taxonomy is sufficient for Phase 1

## R6: Warning Message Strategy

**Decision**: Context-specific warning messages per document type, with
a suggestion for alternative handling.

**Rationale**: The ADR's frontend section recommends suggesting alternative
formats (e.g., "Consider keeping as PDF for best visual fidelity"). Generic
warnings ("This document may not convert well") are unhelpful. Type-specific
messages set expectations and provide actionable next steps.

Warning template: "This document appears to be a {type}. {type_specific_note}
Conversion will proceed, but the HTML output may not fully preserve the
original visual layout. Suitability score: {score}/1.0."

**Alternatives considered**:
- Generic warning for all types: Unhelpful; doesn't explain why
- Score-only display: Too abstract; users don't know what 0.35 means
- Block with "contact administrator": Removes user autonomy; ADR explicitly
  rejects this

## R7: DOCX and PPTX Classification

**Decision**: Apply format-specific heuristic strategies for non-PDF formats:

- **DOCX**: Analyze paragraph count, heading usage, image count, table count
  using python-docx's document model. DOCX files are generally well-suited
  for HTML conversion (they already have semantic structure), so default
  suitability is higher (0.80 baseline).
- **PPTX**: Classify all PPTX as `slide_deck` type with a baseline
  suitability of 0.35. PPTX files are inherently low-suitability for HTML
  conversion due to their spatial, image-heavy nature. Adjust upward only
  if slides are text-heavy (speaker notes + text frames > image area).

**Rationale**: The ADR identifies slide decks and image-heavy layouts as
the primary problem. PPTX files are almost always slide decks. DOCX files
generally map well to HTML. Classification effort should focus on PDFs where
the document type is ambiguous.

**Alternatives considered**:
- Skip DOCX/PPTX classification: Misses the PPTX warning case that's
  central to the ADR
- Same heuristics for all formats: Doesn't account for format-specific
  structural differences

## R8: Integration Timing in Pipeline

**Decision**: Insert classification between password-protection check and
content extraction in `function_app.py`, exactly as the ADR proposes
(after line ~225, before line ~227 in current code).

**Rationale**: This placement:
1. Runs after file validation (format check, password check) — no wasted
   classification on invalid files
2. Runs before extraction — provides the "pre-screening" benefit the ADR
   describes
3. For PDFs, uses PyMuPDF to open the document briefly for heuristic
   analysis, then closes it; the extractor re-opens it (PyMuPDF open is
   fast, <10ms for typical documents)
4. For DOCX/PPTX, uses python-docx/python-pptx to read structure metadata

The classification step is wrapped in a try/except — if it fails, the
pipeline continues without classification (graceful degradation per
Constitution VIII).

**Alternatives considered**:
- After extraction (post-processing): Loses the pre-screening benefit;
  expensive extraction already done
- Parallel with extraction: Adds concurrency complexity; classification
  is <100ms so sequential is fine
- As a separate Azure Function: Over-engineering; adds infrastructure
  and inter-function communication
