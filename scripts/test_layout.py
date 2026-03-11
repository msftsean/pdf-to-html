"""
Extract PDF content using pymupdf4llm (layout-aware) and save as Markdown
with images written to disk.

Usage:
    python test_layout.py input.pdf [output_dir]

Output defaults to ./output/<pdf_name>_layout/
Produces:
    <output_dir>/<pdf_name>.md   — Markdown with embedded image references
    <output_dir>/images/         — extracted images
"""

import os
import sys
import time


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input.pdf> [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join("output", f"{pdf_name}_layout")
    image_dir = os.path.join(output_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    import pymupdf4llm

    print(f"Input: {pdf_path}")
    print(f"Output: {output_dir}")
    print(f"pymupdf4llm version: {pymupdf4llm.__version__}")
    print(f"Layout engine: {'yes' if pymupdf4llm._use_layout else 'no'}")
    print()

    t0 = time.perf_counter()
    md_text = pymupdf4llm.to_markdown(
        pdf_path,
        write_images=True,
        image_path=image_dir,
        image_format="png",
        dpi=200,
    )
    t1 = time.perf_counter()

    # Write Markdown
    md_path = os.path.join(output_dir, f"{pdf_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    # Count extracted images
    image_files = [f for f in os.listdir(image_dir) if not f.startswith(".")]

    print(f"Extracted in {t1 - t0:.2f}s")
    print(f"Markdown: {md_path} ({os.path.getsize(md_path):,} bytes)")
    print(f"Images: {len(image_files)} file(s) in {image_dir}")
    print()
    print(f"Done! Open {md_path} to review.")


if __name__ == "__main__":
    main()
