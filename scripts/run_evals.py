#!/usr/bin/env python3
"""
Evaluation harness for pdf-to-html converter.
Runs sample documents through the conversion pipeline and validates WCAG compliance.

Usage:
    python scripts/run_evals.py
    python scripts/run_evals.py --samples-dir tests/eval/samples
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from pdf_extractor import extract_pdf
from html_builder import build_html
from wcag_validator import validate_html
from eval_metrics import (
    count_violations_by_severity,
    heading_hierarchy_score,
    table_accessibility_score,
    image_alt_coverage,
    overall_compliance_score,
)


def evaluate_document(pdf_path: Path) -> dict:
    """Run a single document through the pipeline and evaluate.

    Returns a result dict with:
      - filename, page_count, conversion_time_ms
      - violation counts by severity
      - detailed scores (heading, table, image)
      - overall result (PASS/WARN/FAIL)
      - full violation details
      - generated HTML (for debugging)
    """
    result = {
        "filename": pdf_path.name,
        "page_count": 0,
        "conversion_time_ms": 0,
        "violations": {"critical": 0, "serious": 0, "moderate": 0, "minor": 0},
        "scores": {
            "heading_hierarchy": 0.0,
            "table_accessibility": 0.0,
            "image_alt_coverage": 0.0,
        },
        "result": "FAIL",
        "violation_details": [],
        "error": None,
    }

    try:
        # Read PDF bytes
        pdf_bytes = pdf_path.read_bytes()

        # Time the conversion pipeline
        t0 = time.perf_counter()

        # Step 1: Extract PDF content
        pages, metadata = extract_pdf(pdf_bytes)

        # Step 2: Build HTML (no OCR results for digital PDFs)
        ocr_results = {}  # digital PDFs don't need OCR
        html_content, image_files = build_html(pages, ocr_results, metadata)

        t1 = time.perf_counter()
        conversion_ms = int((t1 - t0) * 1000)

        # Step 3: Validate WCAG compliance
        violations = validate_html(html_content)
        violation_dicts = [v.to_dict() for v in violations]

        # Step 4: Calculate metrics
        severity_counts = count_violations_by_severity(violation_dicts)
        h_score = heading_hierarchy_score(html_content)
        t_score = table_accessibility_score(html_content)
        i_score = image_alt_coverage(html_content)
        overall = overall_compliance_score(violation_dicts)

        result.update({
            "page_count": len(pages),
            "conversion_time_ms": conversion_ms,
            "violations": severity_counts,
            "scores": {
                "heading_hierarchy": h_score,
                "table_accessibility": t_score,
                "image_alt_coverage": i_score,
            },
            "result": overall,
            "violation_details": violation_dicts,
        })

        # Save generated HTML for inspection
        output_dir = PROJECT_ROOT / "tests" / "eval" / "results" / "html"
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / f"{pdf_path.stem}.html"
        html_path.write_text(html_content, encoding="utf-8")

    except Exception as e:
        result["error"] = str(e)
        result["result"] = "ERROR"

    return result


def run_all_evals(samples_dir: Path) -> dict:
    """Run all sample documents and aggregate results.

    Returns a full report dict with individual results and summary.
    """
    pdf_files = sorted(samples_dir.glob("*.pdf"))
    if not pdf_files:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "samples_dir": str(samples_dir),
            "documents": [],
            "summary": {"total": 0, "pass": 0, "warn": 0, "fail": 0, "error": 0},
        }

    documents = []
    for pdf_path in pdf_files:
        print(f"  Evaluating {pdf_path.name}...", end=" ", flush=True)
        doc_result = evaluate_document(pdf_path)
        status_icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "ERROR": "💥"}.get(
            doc_result["result"], "?"
        )
        print(f"{status_icon} {doc_result['result']} ({doc_result['conversion_time_ms']}ms)")
        documents.append(doc_result)

    # Aggregate summary
    summary = {"total": len(documents), "pass": 0, "warn": 0, "fail": 0, "error": 0}
    for doc in documents:
        key = doc["result"].lower()
        if key in summary:
            summary[key] += 1

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "samples_dir": str(samples_dir),
        "documents": documents,
        "summary": summary,
    }


def print_summary(report: dict):
    """Print a human-readable summary table to stdout."""
    docs = report.get("documents", [])
    if not docs:
        print("\nNo documents evaluated.")
        return

    # Column widths
    name_w = max(len(d["filename"]) for d in docs) + 2
    name_w = max(name_w, 21)  # minimum width

    # Header
    header = (
        f"│ {'Document':<{name_w}} │ {'Pages':>5} │ {'Time(ms)':>8} │ "
        f"{'Crit':>4} │ {'Serious':>7} │ {'Moderate':>8} │ {'Minor':>5} │ {'Result':<9} │"
    )
    sep_line = "─" * (len(header) - 1)

    print(f"\n┌{'─' * (len(header) - 2)}┐")
    print(header)
    print(f"├{'─' * (len(header) - 2)}┤")

    for doc in docs:
        v = doc["violations"]
        result_icon = {"PASS": "✅ PASS", "WARN": "⚠️  WARN", "FAIL": "❌ FAIL", "ERROR": "💥 ERR"}.get(
            doc["result"], doc["result"]
        )
        row = (
            f"│ {doc['filename']:<{name_w}} │ {doc['page_count']:>5} │ "
            f"{doc['conversion_time_ms']:>8} │ {v['critical']:>4} │ "
            f"{v['serious']:>7} │ {v['moderate']:>8} │ {v['minor']:>5} │ "
            f"{result_icon:<9} │"
        )
        print(row)

    print(f"└{'─' * (len(header) - 2)}┘")

    # Scores summary
    print("\n📊 Detailed Scores:")
    for doc in docs:
        scores = doc["scores"]
        print(
            f"  {doc['filename']}: "
            f"Heading={scores['heading_hierarchy']:.0f}% "
            f"Table={scores['table_accessibility']:.0f}% "
            f"ImageAlt={scores['image_alt_coverage']:.0f}%"
        )

    # Violations detail (if any)
    has_violations = any(doc["violation_details"] for doc in docs)
    if has_violations:
        print("\n🔍 Violation Details:")
        for doc in docs:
            if doc["violation_details"]:
                print(f"\n  {doc['filename']}:")
                for v in doc["violation_details"]:
                    sev_icon = {
                        "critical": "🔴",
                        "serious": "🟠",
                        "moderate": "🟡",
                        "minor": "🔵",
                    }.get(v["severity"], "⚪")
                    print(f"    {sev_icon} [{v['severity'].upper()}] {v['rule_id']}: {v['description']}")

    # Overall summary
    s = report["summary"]
    print(
        f"\nOverall: {s['total']}/{s['total']} documents processed, "
        f"{s['pass']} PASS, {s['warn']} WARN, {s['fail']} FAIL"
        + (f", {s['error']} ERROR" if s["error"] else "")
    )


def main():
    """Entry point: generate samples if needed, run evals, save report."""
    import argparse

    parser = argparse.ArgumentParser(description="Run pdf-to-html evaluation suite")
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=PROJECT_ROOT / "tests" / "eval" / "samples",
        help="Directory containing sample PDFs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "tests" / "eval" / "results" / "eval-report.json",
        help="Path for JSON report output",
    )
    args = parser.parse_args()

    samples_dir = args.samples_dir
    output_path = args.output

    # Generate samples if directory is empty
    if not list(samples_dir.glob("*.pdf")):
        print("📄 No sample PDFs found. Generating...")
        sys.path.insert(0, str(PROJECT_ROOT / "tests" / "eval"))
        from generate_samples import generate_all
        generate_all()
        print()

    print("🏃 Running evaluation suite...\n")
    report = run_all_evals(samples_dir)

    # Save JSON report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Report saved to {output_path}")

    # Print human-readable summary
    print_summary(report)

    # Exit code: non-zero if any FAIL
    if report["summary"]["fail"] > 0 or report["summary"]["error"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
