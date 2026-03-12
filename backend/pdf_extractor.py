"""
PDF extraction using PyMuPDF.
Extracts text blocks (with position/font metadata), images, and detects
whether each page is digital (has selectable text) or scanned (image-only).
"""

import io
import logging
import os
import base64
from dataclasses import dataclass, field

os.environ["PYMUPDF_MESSAGE"] = f"path:{os.devnull}"  # suppress "consider pymupdf_layout" notice
import pymupdf

logger = logging.getLogger(__name__)

# Minimum text length to consider a page "digital" rather than scanned
_MIN_TEXT_LENGTH = 20


@dataclass
class TextSpan:
    """A contiguous run of text with uniform formatting."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font: str
    size: float
    color: int  # sRGB packed int
    bold: bool
    italic: bool


@dataclass
class ImageInfo:
    """An image extracted from the PDF."""
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    image_bytes: bytes
    extension: str  # png, jpeg, etc.
    xref: int


@dataclass
class TableData:
    """A table extracted from a digital PDF page via PyMuPDF."""
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1
    header: list[str]
    rows: list[list[str]]


@dataclass
class PageResult:
    """Extraction results for a single page."""
    page_number: int
    width: float
    height: float
    is_scanned: bool
    text_spans: list[TextSpan] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    tables: list[TableData] = field(default_factory=list)


def _classify_page(page: pymupdf.Page) -> bool:
    """Return True if the page is scanned/image-only (needs OCR)."""
    text = page.get_text("text").strip()
    return len(text) < _MIN_TEXT_LENGTH


def _extract_text_spans(page: pymupdf.Page) -> list[TextSpan]:
    """Extract all text spans with position and font metadata, deduplicating overlapping spans."""
    spans: list[TextSpan] = []
    blocks = page.get_text("dict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]

    for block in blocks:
        if block["type"] != 0:  # text block
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"]
                if not text.strip():
                    continue
                bbox = span["bbox"]
                flags = span["flags"]

                # Deduplicate: skip if an existing span has the same text
                # and overlapping position (within a few points)
                is_dup = False
                for existing in spans:
                    if (existing.text == text
                            and abs(existing.x0 - bbox[0]) < 5.0
                            and abs(existing.y0 - bbox[1]) < 5.0):
                        is_dup = True
                        break
                if is_dup:
                    continue

                spans.append(TextSpan(
                    text=text,
                    x0=bbox[0],
                    y0=bbox[1],
                    x1=bbox[2],
                    y1=bbox[3],
                    font=span["font"],
                    size=round(span["size"], 1),
                    color=span["color"],
                    bold=bool(flags & 2**4),  # bit 4 = bold
                    italic=bool(flags & 2**1),  # bit 1 = italic
                ))
    return spans


def _extract_images(page: pymupdf.Page, page_number: int) -> list[ImageInfo]:
    """Extract embedded images from a page."""
    images: list[ImageInfo] = []
    image_list = page.get_images(full=True)

    for img_index, img_info in enumerate(image_list):
        xref = img_info[0]
        try:
            base_image = page.parent.extract_image(xref)
            if not base_image:
                continue

            image_bytes = base_image["image"]
            ext = base_image["ext"]

            # Get image position on the page
            rects = page.get_image_rects(xref)
            if rects:
                rect = rects[0]
                images.append(ImageInfo(
                    page_number=page_number,
                    x0=rect.x0,
                    y0=rect.y0,
                    x1=rect.x1,
                    y1=rect.y1,
                    image_bytes=image_bytes,
                    extension=ext,
                    xref=xref,
                ))
        except Exception:
            logger.warning("Failed to extract image xref=%d on page %d", xref, page_number)
    return images


def _extract_tables(page: pymupdf.Page) -> list[TableData]:
    """Extract tables from a page using PyMuPDF's table detection."""
    tables: list[TableData] = []
    tab_finder = page.find_tables()
    for table in tab_finder.tables:
        extracted = table.extract()
        if not extracted or len(extracted) < 2:
            continue
        # First row is header; clean None values to empty strings
        header = [cell or "" for cell in extracted[0]]
        rows = [[cell or "" for cell in row] for row in extracted[1:]]
        tables.append(TableData(
            bbox=table.bbox,
            header=header,
            rows=rows,
        ))
    return tables


def _filter_spans_outside_tables(
    spans: list[TextSpan],
    table_bboxes: list[tuple[float, float, float, float]],
) -> list[TextSpan]:
    """Remove text spans whose center falls inside any table bounding box."""
    if not table_bboxes:
        return spans
    filtered = []
    for span in spans:
        cx = (span.x0 + span.x1) / 2
        cy = (span.y0 + span.y1) / 2
        inside = False
        for (tx0, ty0, tx1, ty1) in table_bboxes:
            if tx0 <= cx <= tx1 and ty0 <= cy <= ty1:
                inside = True
                break
        if not inside:
            filtered.append(span)
    return filtered


import re as _re

# Patterns that indicate a page number
_PAGE_NUM_RE = _re.compile(
    r"^(?:"
    r"\d{1,4}"                     # plain number: 1, 23, 100
    r"|page\s+\d+"                 # Page 1
    r"|\d+\s+of\s+\d+"            # 1 of 10
    r"|page\s+\d+\s+of\s+\d+"     # Page 1 of 10
    r"|-\s*\d+\s*-"               # - 1 -
    r")$",
    _re.IGNORECASE,
)

# Margin zones: fraction of page height considered header / footer area
_HEADER_ZONE = 0.12   # top 12%
_FOOTER_ZONE = 0.12   # bottom 12%


def _remove_headers_footers(pages: list[PageResult]) -> list[PageResult]:
    """Remove repeated header/footer text that appears across multiple pages.

    Detection strategy (position-based):
    1. Scan all spans in the top/bottom margin zones.
    2. Group spans into y-bands (15pt buckets).
    3. If a y-band has spans on >= threshold pages, ALL spans in that band
       are removed — headers/footers often vary slightly in text (dates,
       page numbers, section titles) but always sit at the same vertical
       position.
    Requires at least 3 pages to activate.
    """
    digital_pages = [p for p in pages if not p.is_scanned and p.text_spans]
    if len(digital_pages) < 3:
        return pages

    page_height = digital_pages[0].height
    header_limit = page_height * _HEADER_ZONE
    footer_start = page_height * (1 - _FOOTER_ZONE)

    # Group by (rounded y-band, zone) → set of page numbers that have a span there
    Y_ROUND = 15.0
    band_pages: dict[tuple[float, str], set[int]] = {}

    for p in digital_pages:
        for span in p.text_spans:
            zone = None
            if span.y0 < header_limit:
                zone = "header"
            elif span.y0 > footer_start:
                zone = "footer"
            if zone is None:
                continue
            band = (round(span.y0 / Y_ROUND) * Y_ROUND, zone)
            band_pages.setdefault(band, set()).add(p.page_number)

    # Bands present on at least half the pages (min 3) are header/footer
    threshold = max(3, len(digital_pages) // 2)
    remove_bands: set[tuple[float, str]] = {
        band for band, pg_set in band_pages.items()
        if len(pg_set) >= threshold
    }

    if not remove_bands:
        return pages

    removed_count = 0
    for p in digital_pages:
        original_len = len(p.text_spans)
        filtered = []
        for span in p.text_spans:
            zone = None
            if span.y0 < header_limit:
                zone = "header"
            elif span.y0 > footer_start:
                zone = "footer"

            if zone is not None:
                band = (round(span.y0 / Y_ROUND) * Y_ROUND, zone)
                if band in remove_bands:
                    continue

            filtered.append(span)
        removed_count += original_len - len(filtered)
        p.text_spans = filtered

    if removed_count:
        logger.info("Removed %d header/footer spans across %d pages", removed_count, len(digital_pages))

    # Second pass: remove page-number patterns at a consistent position
    # regardless of margin zone (some PDFs place page numbers mid-page)
    pn_band_pages: dict[float, set[int]] = {}
    for p in digital_pages:
        for span in p.text_spans:
            if _PAGE_NUM_RE.match(span.text.strip()):
                band = round(span.y0 / Y_ROUND) * Y_ROUND
                pn_band_pages.setdefault(band, set()).add(p.page_number)

    remove_pn_bands = {band for band, pg in pn_band_pages.items() if len(pg) >= threshold}
    if remove_pn_bands:
        pn_removed = 0
        for p in digital_pages:
            before = len(p.text_spans)
            p.text_spans = [
                s for s in p.text_spans
                if not (_PAGE_NUM_RE.match(s.text.strip())
                        and round(s.y0 / Y_ROUND) * Y_ROUND in remove_pn_bands)
            ]
            pn_removed += before - len(p.text_spans)
        if pn_removed:
            logger.info("Removed %d page-number spans", pn_removed)

    return pages


def extract_pdf(pdf_data: bytes) -> tuple[list[PageResult], dict]:
    """
    Extract content from a PDF.

    Returns:
        - list of PageResult (one per page)
        - dict of PDF metadata (title, author, etc.)
    """
    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    metadata = doc.metadata or {}

    pages: list[PageResult] = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        is_scanned = _classify_page(page)

        text_spans = []
        tables: list[TableData] = []
        if not is_scanned:
            # Extract tables first so we can exclude table regions from text spans
            tables = _extract_tables(page)
            table_bboxes = [t.bbox for t in tables]
            text_spans = _extract_text_spans(page)
            # Filter out text spans that fall inside a detected table region
            text_spans = _filter_spans_outside_tables(text_spans, table_bboxes)

        page_images = _extract_images(page, page_num)

        pages.append(PageResult(
            page_number=page_num,
            width=page.rect.width,
            height=page.rect.height,
            is_scanned=is_scanned,
            text_spans=text_spans,
            images=page_images,
            tables=tables,
        ))

    doc.close()

    # Post-process: remove repeated headers/footers across pages
    pages = _remove_headers_footers(pages)

    return pages, metadata
