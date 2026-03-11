# Flash — History

## Session Log

- **2026-03-11:** Joined the squad as Frontend Developer.

## Learnings

### Phase 1 + Phase 2 Frontend Scaffold (Session 1)

**Tasks Completed:** T002, T003, T005, T006, T011, T012, T013, T014, T015, T016

1. **Next.js 14 scaffolding** — `create-next-app@14` with `--typescript --app --no-tailwind --no-eslint --no-src-dir` works well on Node 24, but the "Ok to proceed?" npm prompt requires interactive confirmation. May need `--yes` in CI.

2. **Bootstrap 5 + CSS variables coexist cleanly** — Importing Bootstrap via `@import 'bootstrap/dist/css/bootstrap.min.css'` in globals.css, then layering Digital Commons tokens via CSS custom properties (`--nc-*`) lets us use Bootstrap's grid/utilities while overriding colors and typography. No conflicts observed.

3. **Styled JSX for component-scoped styles** — Next.js 14 includes styled-jsx out of the box (`<style jsx>`). Used it for GovBanner, NCHeader, and NCFooter to keep styles co-located without adding CSS Modules or a CSS-in-JS library. This approach keeps the component tree simple and avoids flash-of-unstyled-content.

4. **XHR over Fetch for upload progress** — The Fetch API doesn't support `upload.onprogress`. Used `XMLHttpRequest` in `uploadService.ts` for real-time progress tracking. This is a browser limitation, not a library choice.

5. **WCAG essentials baked into layout** — Skip-nav link, `lang="en"` on `<html>`, `:focus-visible` outlines, `aria-expanded` on GovBanner toggle, semantic landmarks (`<header role="banner">`, `<main>`, `<footer role="contentinfo">`), and 4.5:1+ contrast ratios are all in the initial scaffold. axe-core is installed for dev-time auditing.

6. **Build verified** — `npm run build` compiles and generates static pages successfully. First Load JS is ~87 kB shared across routes.

