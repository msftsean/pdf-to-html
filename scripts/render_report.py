#!/usr/bin/env python3
"""
Render an eval report from JSON output using the Jinja2 markdown template.

Usage:
    python scripts/render_report.py
    python scripts/render_report.py --input tests/eval/results/eval-report.json
    python scripts/render_report.py --output tests/eval/results/eval-report.md
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("❌ jinja2 is required. Install with: pip install jinja2", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = Path(__file__).parent
DEFAULT_INPUT = PROJECT_ROOT / "tests" / "eval" / "results" / "eval-report.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "tests" / "eval" / "results" / "eval-report.md"


def load_report(input_path: Path) -> dict:
    """Load evaluation report JSON from disk."""
    if not input_path.exists():
        print(f"❌ Report not found: {input_path}", file=sys.stderr)
        print("   Run the eval suite first: python scripts/run_evals.py", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_report(report: dict, template_name: str = "eval_report.md.j2") -> str:
    """Render the Jinja2 markdown template with report data.

    Args:
        report: Eval report dict (from run_evals.py JSON output).
        template_name: Jinja2 template filename in the scripts/ directory.

    Returns:
        Rendered markdown string.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(template_name)
    return template.render(**report)


def has_critical_violations(report: dict) -> bool:
    """Check if report contains any critical WCAG violations.

    Returns True if any document has critical violations or errors.
    """
    summary = report.get("summary", {})
    return summary.get("fail", 0) > 0 or summary.get("error", 0) > 0


def main():
    parser = argparse.ArgumentParser(
        description="Render eval report from JSON to Markdown"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to eval JSON report (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path for rendered Markdown output (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print rendered report to stdout instead of file",
    )
    args = parser.parse_args()

    # Load JSON report
    report = load_report(args.input)

    # Render Jinja2 template
    rendered = render_report(report)

    if args.stdout:
        print(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"📄 Report rendered to {args.output}")

    # Report compliance status
    if has_critical_violations(report):
        print("🔴 Critical WCAG violations found.", file=sys.stderr)
        sys.exit(1)
    else:
        summary = report.get("summary", {})
        if summary.get("warn", 0) > 0:
            print("🟡 Warnings present but no critical violations.", file=sys.stderr)
        else:
            print("🟢 All documents WCAG 2.1 AA compliant.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
