"""
Local test runner for the PDF-to-HTML pipeline.
Runs the same extraction and HTML generation without Azure Functions or Blob Storage.

Usage:
    python test_local.py input.pdf [output_dir]

Output is written to output_dir (defaults to ./output/<pdf_name>/).
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input.pdf> [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.isfile(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join("output", pdf_name)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    logger.info("Input: %s (%d bytes)", pdf_path, len(pdf_data))

    # --- Step 1: Extract with PyMuPDF ---
    from pdf_extractor import extract_pdf

    t0 = time.perf_counter()
    pages, metadata = extract_pdf(pdf_data)
    t1 = time.perf_counter()
    logger.info("Extracted %d pages in %.2fs", len(pages), t1 - t0)

    digital = sum(1 for p in pages if not p.is_scanned)
    scanned = sum(1 for p in pages if p.is_scanned)
    logger.info("  Digital pages: %d, Scanned pages: %d", digital, scanned)

    # --- Step 2: OCR scanned pages (if any and if DI is configured) ---
    ocr_results = {}
    scanned_pages = [p.page_number for p in pages if p.is_scanned]

    if scanned_pages:
        endpoint = os.environ.get("DOCUMENT_INTELLIGENCE_ENDPOINT", "")
        if endpoint:
            from ocr_service import ocr_pdf_pages

            logger.info("Running OCR on %d scanned page(s)...", len(scanned_pages))
            t0 = time.perf_counter()
            ocr_results = ocr_pdf_pages(pdf_data, scanned_pages)
            t1 = time.perf_counter()
            logger.info("OCR complete in %.2fs", t1 - t0)
        else:
            logger.warning(
                "Skipping OCR — DOCUMENT_INTELLIGENCE_ENDPOINT not set. "
                "Scanned pages will have no text."
            )

    # --- Step 3: Build HTML ---
    from html_builder import build_html

    html_content, image_files = build_html(
        pages=pages,
        ocr_results=ocr_results,
        metadata=metadata,
        embed_images=False,
    )

    # --- Step 4: Write output ---
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    if image_files:
        os.makedirs(images_dir, exist_ok=True)

    html_path = os.path.join(output_dir, f"{pdf_name}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    for img_filename, img_bytes in image_files.items():
        img_path = os.path.join(images_dir, img_filename)
        with open(img_path, "wb") as f:
            f.write(img_bytes)

    logger.info("Output: %s", html_path)
    logger.info("  HTML: %.1f KB", len(html_content) / 1024)
    logger.info("  Images: %d files", len(image_files))
    print(f"\nDone! Open {html_path} in a browser to review.")


if __name__ == "__main__":
    main()
