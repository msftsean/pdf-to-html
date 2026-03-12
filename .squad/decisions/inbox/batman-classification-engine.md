# Document Classification Engine — Future Architecture

### 2026-03-12 03:16:03 UTC: Proposed Document Classification Pre-Processing Gate

**By:** Batman (Tech Lead)

**Status:** Proposed

**What:** Add a document-level classification step as a pre-processing gate between blob upload and extraction. This engine will analyze documents before conversion begins, classify document type (report, brochure, form, slide deck, newsletter, etc.), and return a suitability score for HTML conversion.

**Why:**

The current pipeline converts all uploaded documents blindly, regardless of document type or visual complexity. Some documents — notably brochures, PowerPoint exports, highly visual layouts, and forms — translate poorly to HTML due to their design-first nature:

- Brochures rely on magazine-style multi-column layouts and visual hierarchy that don't map to semantic HTML
- Slide decks are image-heavy with complex positioning that becomes meaningless as linear HTML
- Forms with intricate field layouts lose their spatial relationships and usability in HTML
- Newsletters depend on color, typography, and spatial design to communicate structure

**Luke (stakeholder) flagged this limitation early.** The current `_classify_page()` function in `pdf_extractor.py` only determines if a page is scanned (image-only) vs. text-based; it does NOT assess document suitability for HTML conversion.

Without a pre-screening step, users receive degraded output without warning, leading to user frustration and potential loss of trust in the tool's capabilities.

**Details:**

#### Problem Statement

- **Current behavior:** All documents pass through to extraction and conversion regardless of type
- **Gap:** No mechanism to predict conversion quality before expensive processing begins
- **User impact:** Users may invest conversion effort on documents that will produce poor HTML
- **Signal:** Document type (slide deck, brochure, form) is a strong predictor of HTML suitability

#### Proposed Solution

Insert a **Classification Gate** between the blob trigger (`function_app.py` line ~130) and the extraction pipeline:

```
Blob Upload → Validation → [NEW] Classification → Extract → OCR → HTML Build → WCAG Validation → Output
                                    ↑
                                Returns suitability score
                                Flags unsuitable docs with warning
```

The classification step will:

1. **Analyze document structure** (page count, text density, image ratio, object complexity)
2. **Classify document type** (report, brochure, form, slide deck, newsletter, presentation, whitepaper, etc.)
3. **Return a suitability score** (0–1.0, where >0.7 = high HTML suitability)
4. **Emit warnings** for documents below threshold (does NOT silently reject them)

#### Implementation Options

**Option A: Azure AI Foundry Custom Model** (Luke's preferred direction)
- Train a custom multimodal model on past conversions + user feedback labels
- Highest accuracy, learns from your specific use cases
- Requires labeled training data (~100–200 annotated documents)
- 7–14 day training cycle; inference cost ~$0.001–0.002 per document
- Scales well; can be versioned and A/B tested

**Option B: Azure Document Intelligence Custom Classifier** (Legacy, deprecating)
- Microsoft's built-in document classification model
- Good for standard document types (invoice, contract, receipt)
- Limited on custom types (brochure, newsletters, presentations)
- No fine-tuning; static model
- Cheaper than custom models (~$0.00025 per document)

**Option C: Lightweight Heuristic (Short-term fast track)**
- Analyze page count, text density, image ratio, object count per page
- Simple rule-based scoring (e.g., >50% images per page → low suitability)
- No external API calls; runs in-process
- 1–2 day implementation; zero inference cost
- Limited accuracy; high false positive rate on valid documents
- **Best for MVP/proof-of-concept; transition to Option A for production**

#### Recommended Path

1. **Phase 1 (Immediate):** Implement Option C (heuristics) to establish the gate architecture and warning UX
2. **Phase 2 (1–2 sprints):** Collect user feedback and document labels while heuristics run in parallel
3. **Phase 3 (After 200+ labeled samples):** Train Option A (custom model) and swap it in, keeping heuristics as fallback

#### Integration Point

In `function_app.py`, after blob metadata is initialized:

```python
# Existing: validate file type and size
validate_upload(blob_name, file_size)

# NEW: Classify document before starting expensive extraction
classification = classify_document(blob_client, blob_name)

# Store classification in blob metadata
blob_client.set_blob_metadata(blob_name, {
    "classification_type": classification.document_type,
    "suitability_score": str(classification.suitability_score),
    "classification_warning": classification.warning_message or "",
})

# If warning exists, update status and continue (don't reject)
if classification.warning_message:
    status_service.update_document_status(
        document_id,
        warning_message=classification.warning_message
    )

# Proceed to extraction (no gate; optional pre-processing only)
extract_and_convert(...)
```

#### Frontend Changes (Out of scope for this spec, but consider):

- Display classification warning in the status dashboard
- Suggest alternative formats (e.g., "This appears to be a brochure. Consider keeping it as PDF or exporting as image slideshow for best visual fidelity.")
- Let users explicitly proceed despite warning or request alternate format
- Track user actions (ignore warning, accept output, request re-export) for model retraining

#### Data Model Extension

```python
# In models.py
@dataclass
class DocumentClassification:
    document_type: str  # "report", "brochure", "form", "slide_deck", "newsletter", etc.
    suitability_score: float  # 0.0–1.0
    confidence: float  # Confidence in the classification (0.0–1.0)
    warning_message: str | None  # User-facing warning if suitability_score < 0.7
    metadata: dict[str, Any]  # Engine-specific data (e.g., page_count, text_density, image_ratio)
```

#### Success Metrics

- **Short-term:** Heuristic classifier achieves >90% recall on "unsuitable" documents (brochures, slide decks) with <30% false positive rate on reports and whitepapers
- **Long-term (after ML model):** >95% accuracy on user-labeled test set; <2% false negative rate
- **User satisfaction:** Users report fewer surprises; conversion expectations better matched to actual quality

#### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| False positives (warn on good documents) | Start conservative (>0.8 suitability threshold); user feedback loop to retrain model |
| Added latency | Heuristic approach (<100ms); custom model with async batching if needed |
| Model training data shortage | Collect labels from existing conversions; offer optional user feedback checkbox after download |
| Scope creep (feature gate becomes main gate) | Keep classification **optional/informational**, never a blocker; status quo is "convert everything" |

#### Open Questions

1. Should we reject documents below suitability threshold, or always attempt conversion with a warning?
   - **Recommendation:** Always convert; warn user. Preserves user autonomy and data.

2. What is the threshold for "warn the user"?
   - **Recommendation:** 0.70 initially (>70% = good HTML conversion likely); tune based on feedback.

3. Should users be able to override the warning?
   - **Recommendation:** Yes. Some users may have use cases we don't anticipate.

4. How do we collect feedback to improve the model?
   - **Recommendation:** Optional checkbox post-download: "Was the HTML conversion quality helpful?" Tie feedback to document classification.

---

## Related Decisions

- **US1+US2 Backend Implementation:** OCR confidence flagging (0.70 threshold) shows precedent for ML-driven quality signals
- **Phase 2 Backend Architecture:** Blob metadata for status tracking is the natural storage layer for classification results
- **Frontend Architecture:** Status dashboard already polls for document state; can extend to display classification warnings

## Next Steps

1. **Review with team:** Validate that this direction aligns with product roadmap
2. **Scope Phase 1:** Define heuristic rules (text density, image ratio, page count thresholds)
3. **Create issue:** File Phase X user story for heuristic implementation when backlog allows
4. **Data collection:** Begin tagging past conversions with document type labels for future model training
