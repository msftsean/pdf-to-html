# Decision: GovBanner converted to Demo Disclaimer

**Date:** 2025-07-18
**Author:** Flash (Frontend Developer)
**Requested by:** Sean Gayle

## Context

The GovBanner component previously mimicked the official NC.gov USWDS trust banner pattern ("An official website of the State of North Carolina"). Since this is a demo/prototype app, it was misleading.

## Decision

- **Banner text** changed to: "An UNofficial website of the State of North Carolina. For demo purposes only."
- **Background color** changed from navy (#003366) to amber (#d4a017) to visually signal "demo/warning" rather than "official government."
- **Dropdown content** replaced official-site verification info with:
  - "What is this?" — explains PDF-to-HTML WCAG 2.1 AA converter
  - "Not an official NC.gov site" — warns users not to upload sensitive documents
- **Toggle label** changed from "How you know" to "Learn more"
- **Icon** changed from 🏛️ (government) to ⚠️ (warning)

## Rationale

Using the official NC.gov trust banner pattern on a demo could confuse users or violate state branding guidelines. The amber color and warning icon make it immediately clear this is a prototype.

## Impact

- `GovBanner.tsx` — single file changed
- Footer still references "official" — left unchanged as Sean's request was specific to the header banner
- All accessibility tests still pass (9/9)
