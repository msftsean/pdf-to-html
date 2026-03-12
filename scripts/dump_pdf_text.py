"""
Dump raw extracted PDF content to a text file for LLM consumption.

Usage:
    python dump_pdf_text.py input.pdf [output.txt]

Output defaults to ./output/<pdf_name>.txt
"""

import os
import sys

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input.pdf> [output.txt]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join("output", f"{pdf_name}.txt")

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    from backend.pdf_extractor import extract_pdf
    pages, metadata = extract_pdf(pdf_data)

    lines: list[str] = []

    # Metadata
    title = metadata.get("title", "").strip()
    author = metadata.get("author", "").strip()
    if title:
        lines.append(f"Title: {title}")
    if author:
        lines.append(f"Author: {author}")
    lines.append(f"Pages: {len(pages)}")
    lines.append("")

    for page in pages:
        lines.append(f"{'=' * 60}")
        lines.append(f"PAGE {page.page_number + 1}")
        lines.append(f"{'=' * 60}")
        lines.append("")

        if page.is_scanned:
            lines.append("[Scanned page — no extractable text]")
            lines.append("")
            continue

        # Text content (spans sorted top-to-bottom, left-to-right)
        if page.text_spans:
            sorted_spans = sorted(page.text_spans, key=lambda s: (s.y0, s.x0))
            prev_y = None
            for span in sorted_spans:
                # Insert blank line for large vertical gaps (new paragraph)
                if prev_y is not None and span.y0 - prev_y > span.size * 1.5:
                    lines.append("")
                lines.append(span.text.rstrip())
                prev_y = span.y1

        # Tables
        for i, table in enumerate(page.tables):
            lines.append("")
            lines.append(f"[TABLE {i + 1}]")
            # Calculate column widths for alignment
            all_rows = [table.header] + table.rows
            col_widths = [
                max(len(row[c]) for row in all_rows)
                for c in range(len(table.header))
            ]
            # Header
            header_line = " | ".join(
                h.ljust(w) for h, w in zip(table.header, col_widths)
            )
            lines.append(header_line)
            lines.append("-+-".join("-" * w for w in col_widths))
            # Rows
            for row in table.rows:
                lines.append(" | ".join(
                    cell.ljust(w) for cell, w in zip(row, col_widths)
                ))

        # Images
        if page.images:
            lines.append("")
            lines.append(f"[{len(page.images)} image(s) on this page]")

        lines.append("")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {output_path} ({os.path.getsize(output_path):,} bytes)")


if __name__ == "__main__":
    main()
