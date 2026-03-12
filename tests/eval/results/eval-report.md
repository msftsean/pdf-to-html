# WCAG Evaluation Report

**🟢 PASS** — All documents meet WCAG 2.1 AA compliance

**Generated:** 2026-03-11T22:08:49.970654+00:00
**Samples directory:** `/workspaces/pdf-to-html/tests/eval/samples`

---

## Summary

| Metric | Value |
|--------|-------|
| Total documents | 4 |
| ✅ Pass | 4 |
| ⚠️ Warn | 0 |
| ❌ Fail | 0 |
| 💥 Error | 0 |

---

## Results by Document

| Document | Pages | Time (ms) | Headings | Tables | Images | Critical | Serious | Moderate | Minor | Result |
|----------|------:|----------:|---------:|-------:|-------:|---------:|--------:|---------:|------:|--------|
| complex-tables.pdf | 2 | 136 | 75.0% | 100.0% | 100.0% | 0 | 0 | 1 | 0 | ✅ PASS |
| digital-report.pdf | 5 | 91 | 83.3% | 100.0% | 100.0% | 0 | 0 | 1 | 0 | ✅ PASS |
| image-heavy.pdf | 3 | 19 | 75.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | ✅ PASS |
| simple-memo.pdf | 1 | 20 | 100.0% | 100.0% | 100.0% | 0 | 0 | 0 | 0 | ✅ PASS |

---

## Source vs. Output Comparison

| Document | Source Pages | Conversion Time | Violations Found | Compliance Score |
|----------|------------:|-----------------|-----------------:|------------------|
| complex-tables.pdf | 2 | 136 ms | 1 | ✅ PASS |
| digital-report.pdf | 5 | 91 ms | 1 | ✅ PASS |
| image-heavy.pdf | 3 | 19 ms | 0 | ✅ PASS |
| simple-memo.pdf | 1 | 20 ms | 0 | ✅ PASS |

---

## WCAG Violation Details

### `heading-order`

| Severity | Document | Description | Element |
|----------|----------|-------------|---------|
| 🟡 moderate | complex-tables.pdf | Heading level skipped: <h3> follows <h1> (expected ≤ h2) | `<h3>` |
| 🟡 moderate | digital-report.pdf | Heading level skipped: <h3> follows <h1> (expected ≤ h2) | `<h3>` |
📚 [Deque rule reference](https://dequeuniversity.com/rules/axe/4.7/heading-order)


---

## Per-Document Error Details

_No processing errors occurred._

---

<details>
<summary>Raw JSON report path</summary>

This report was generated from the eval harness JSON output.
Re-run with: `python scripts/run_evals.py`

</details>
