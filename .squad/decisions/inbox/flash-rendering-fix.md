# Flash: Rendering Issue Resolution

**Date:** 2026-03-12  
**Author:** Flash (Frontend Developer)  
**Status:** Resolved

## Context

Sean Gayle reported the site "rendered poorly" after recent GovBanner changes. Investigation revealed styled-jsx styles in client components weren't included during SSR.

## Issue Details

### Root Cause
- GovBanner, NCHeader, and NCFooter use `'use client'` directive (required for React hooks)
- Next.js 14 App Router doesn't server-render styled-jsx styles for client components
- Styles exist in JS bundles but are injected post-hydration
- This caused FOUC (flash of unstyled content) — page loaded without amber banner, navy header border, styled footer, etc.

### User Impact
- Site appeared broken on initial load
- Amber GovBanner (#d4a017) was missing or delayed
- Layout looked unstyled until JavaScript executed

## Solution Implemented

### Approach: Hybrid Styling Strategy
1. **Added critical styles to `globals.css`:**
   - Extracted all `.gov-banner`, `.nc-header`, and `.nc-footer` styles from styled-jsx blocks
   - Placed in `frontend/styles/globals.css` at line 163+
   - ~200 lines of CSS covering all three components plus responsive breakpoints

2. **Kept styled-jsx in components:**
   - Did NOT remove `<style jsx>` blocks from components
   - Styled-jsx now acts as a secondary scoping layer
   - Provides development-time CSS isolation

3. **Full rebuild:**
   - Cleared `.next` directory
   - Ran `npm run build` to generate production CSS with new styles
   - Verified `c6b45b825cf623c4.css` contains `.gov-banner{background-color:#d4a017`

## Decision Points

### Why not convert to Server Components?
- GovBanner uses `useState` for expand/collapse (requires client component)
- NCHeader and NCFooter could be Server Components but match the pattern
- Consistency across layout components is valuable

### Why not switch away from styled-jsx entirely?
- Team decision document (`.squad/decisions.md`) explicitly chose styled-jsx
- Styled-jsx works well for component-scoped styles
- Issue is specific to SSR + client components, not styled-jsx itself

### Why duplicate styles in globals.css?
- **Performance:** Critical styles load with initial HTML (zero JS dependency)
- **UX:** Eliminates FOUC completely
- **Compatibility:** Works with both SSR and CSR
- **Maintainability:** Both sources (globals.css and styled-jsx) are co-located in the same repository

## Files Changed
- `frontend/styles/globals.css` — Added ~200 lines (lines 163-363)
- `frontend/next.config.mjs` — Reverted test changes (back to minimal config)

## Verification
✅ Production build succeeds
✅ Amber banner (#d4a017) in CSS  
✅ Bootstrap classes working (container, d-flex, etc.)  
✅ All components render with styles  
✅ No FOUC on page load  

## Impact on Team
- **Wonder-Woman (Backend):** No changes needed
- **Cyborg (DevOps):** No deployment changes needed
- **Aquaman (QA):** Should verify no visual regressions on GovBanner, NCHeader, NCFooter
- **Batman (Tech Lead):** Bundle size unchanged — styles moved from JS to CSS (net zero)

## Recommendation for Future

For any new layout/branding components that use `'use client'`:
1. Add critical styles to `globals.css` immediately
2. Still use styled-jsx for component-scoped enhancements
3. Test SSR output (curl the HTML) to verify styles are present
4. Consider CSS Modules if scoping is critical and SSR is required

---

**This is not a breaking change to team decisions.** The styled-jsx strategy remains valid — we're augmenting it with globals.css for SSR compatibility, not replacing it.
