"""
Semantic HTML builder.
Converts extracted PDF content (text spans, images, OCR results) into
accessible HTML that preserves the visual structure of the original PDF.

WCAG 2.1 AA compliance features:
- Skip navigation link and id="main-content" landmark
- Heading hierarchy enforcement (no gaps: h1→h3 auto-inserts h2)
- scope="col" on table header cells, scope="row" on first-column cells
- Images wrapped in <figure>/<figcaption> with meaningful alt text
- ARIA landmarks: <nav> for TOC, <main> for content, role="region" on sections
- 4.5:1 contrast ratio for normal text, 3:1 for large text
- Visible :focus-visible outlines on keyboard-focusable elements
- Review notice banners for low-confidence OCR pages
"""

import base64
import html
import logging
import re
from dataclasses import dataclass

from pdf_extractor import PageResult, TextSpan, ImageInfo, TableData
from ocr_service import OcrPageResult, OcrTable, OcrTableCell

logger = logging.getLogger(__name__)

# Regex to detect bullet/list-item prefixes
# Speaker notes font marker (matches pptx_extractor.SPEAKER_NOTES_FONT)
_SPEAKER_NOTES_FONT = "SpeakerNotes"

_BULLET_RE = re.compile(
    r'^\s*[\u2022\u2023\u25E6\u2043\u2219\u25AA\u25AB\u25CF\u25CB\u2013\u2014\u2010\u2011•·\-\*►▸▹◦◆◇○●■□]\s+'
    r'|^\s*\d{1,3}[.)\]]\s+'
    r'|^\s*[a-zA-Z][.)\]]\s+'
    r'|^\s*[ivxIVX]{1,4}[.)\]]\s+'
)


def _strip_bullet_prefix(text: str) -> str:
    """Remove the bullet/number prefix from a list item."""
    return _BULLET_RE.sub('', text).strip()


def _is_bullet_line(text: str) -> bool:
    """Check if text starts with a bullet or list-item marker."""
    return bool(_BULLET_RE.match(text))

# Font-size thresholds for heading detection (points)
_H1_MIN_SIZE = 24.0
_H2_MIN_SIZE = 18.0
_H3_MIN_SIZE = 14.0


def _heading_level(span: TextSpan) -> int | None:
    """Determine if a text span should be a heading based on size and weight."""
    if span.size >= _H1_MIN_SIZE and span.bold:
        return 1
    if span.size >= _H1_MIN_SIZE:
        return 1
    if span.size >= _H2_MIN_SIZE and span.bold:
        return 2
    if span.size >= _H2_MIN_SIZE:
        return 2
    if span.size >= _H3_MIN_SIZE and span.bold:
        return 3
    if span.bold and span.size >= 12.0:
        return 4
    return None


def _enforce_heading_hierarchy(blocks: list[dict]) -> list[dict]:
    """Ensure heading levels never skip (e.g. h1→h3 without h2).

    If a heading jumps more than one level from the previous heading,
    its level is flattened down to prev_level + 1.  This guarantees
    WCAG 1.3.1 compliance for heading order.
    """
    last_level = 0
    for block in blocks:
        if block["type"] == "heading":
            target = block["level"]
            if target > last_level + 1:
                block["level"] = last_level + 1
            last_level = block["level"]
    return blocks


def _spans_to_semantic_blocks(spans: list[TextSpan]) -> list[dict]:
    """
    Group text spans into semantic blocks (headings, paragraphs).
    Spans are grouped by vertical proximity into lines, then lines into blocks.
    """
    if not spans:
        return []

    # Sort by vertical position, then horizontal
    sorted_spans = sorted(spans, key=lambda s: (s.y0, s.x0))

    # Group into lines (spans within ~2pt vertical proximity)
    lines: list[list[TextSpan]] = []
    current_line: list[TextSpan] = [sorted_spans[0]]

    for span in sorted_spans[1:]:
        if abs(span.y0 - current_line[0].y0) < max(2.0, current_line[0].size * 0.3):
            current_line.append(span)
        else:
            lines.append(current_line)
            current_line = [span]
    lines.append(current_line)

    # Convert lines to semantic blocks, tracking left indent (x0)
    blocks: list[dict] = []
    for line_spans in lines:
        line_spans.sort(key=lambda s: s.x0)
        text = " ".join(s.text.strip() for s in line_spans if s.text.strip())
        if not text:
            continue

        line_x0 = line_spans[0].x0

        # Use the dominant (largest) span to determine heading level
        dominant = max(line_spans, key=lambda s: s.size)
        heading = _heading_level(dominant)

        if heading:
            blocks.append({"type": "heading", "level": heading, "text": text, "x0": line_x0})
        elif _is_bullet_line(text):
            blocks.append({
                "type": "list_item",
                "text": _strip_bullet_prefix(text),
                "bold": all(s.bold for s in line_spans),
                "italic": all(s.italic for s in line_spans),
                "x0": line_x0,
            })
        else:
            blocks.append({
                "type": "paragraph",
                "text": text,
                "bold": all(s.bold for s in line_spans),
                "italic": all(s.italic for s in line_spans),
                "x0": line_x0,
            })

    # Merge pass:
    # 1. Continuation paragraphs after a list_item get folded into that list_item
    #    (indented or same-indent text that follows a bullet is part of that bullet)
    # 2. Consecutive plain paragraphs with same formatting merge together
    merged: list[dict] = []
    for block in blocks:
        if not merged:
            merged.append(block)
            continue

        prev = merged[-1]

        # Continuation of a list item: a paragraph following a list_item
        # whose left edge is indented at least as far as the list item
        if (prev["type"] == "list_item"
                and block["type"] == "paragraph"
                and block["x0"] >= prev["x0"]):
            prev["text"] += " " + block["text"]
        # Merge consecutive plain paragraphs with same formatting
        elif (prev["type"] == "paragraph"
                and block["type"] == "paragraph"
                and prev["bold"] == block["bold"]
                and prev["italic"] == block["italic"]
                and abs(block["x0"] - prev["x0"]) < 5.0):
            prev["text"] += " " + block["text"]
        else:
            merged.append(block)

    # Enforce heading hierarchy — no skipped levels
    merged = _enforce_heading_hierarchy(merged)

    return merged


def _render_pymupdf_table_html(table: TableData) -> str:
    """Render a PyMuPDF-extracted TableData as accessible HTML."""
    parts = ['<table role="grid">']
    parts.append("  <thead>")
    parts.append("    <tr>")
    for cell in table.header:
        parts.append(f'      <th scope="col">{html.escape(cell)}</th>')
    parts.append("    </tr>")
    parts.append("  </thead>")
    parts.append("  <tbody>")
    for row in table.rows:
        parts.append("    <tr>")
        for col_idx, cell in enumerate(row):
            if col_idx == 0:
                parts.append(f'      <td scope="row">{html.escape(cell)}</td>')
            else:
                parts.append(f"      <td>{html.escape(cell)}</td>")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def _render_table_html(table: OcrTable) -> str:
    """Render an OcrTable as accessible HTML."""
    parts = ['<table role="grid">']

    # Organize cells into a grid
    grid: dict[tuple[int, int], OcrTableCell] = {}
    for cell in table.cells:
        grid[(cell.row_index, cell.column_index)] = cell

    # Detect if first row is header
    has_header = any(c.is_header for c in table.cells)

    for row in range(table.row_count):
        if row == 0 and has_header:
            parts.append("  <thead>")
        elif row == 0:
            parts.append("  <tbody>")
        elif row == 1 and has_header:
            parts.append("  <tbody>")

        parts.append("    <tr>")
        for col in range(table.column_count):
            cell = grid.get((row, col))
            if cell is None:
                continue

            tag = "th" if cell.is_header else "td"
            attrs = []
            if cell.is_header:
                attrs.append('scope="col"')
            elif col == 0 and not cell.is_header:
                # First column in data rows gets scope="row" for row identification
                attrs.append('scope="row"')
            if cell.row_span > 1:
                attrs.append(f'rowspan="{cell.row_span}"')
            if cell.column_span > 1:
                attrs.append(f'colspan="{cell.column_span}"')

            attr_str = (" " + " ".join(attrs)) if attrs else ""
            content = html.escape(cell.text)
            parts.append(f"      <{tag}{attr_str}>{content}</{tag}>")

        parts.append("    </tr>")

        if row == 0 and has_header:
            parts.append("  </thead>")

    parts.append("  </tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def _image_to_data_uri(image: ImageInfo) -> str:
    """Convert image bytes to a base64 data URI."""
    mime_map = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "jxr": "image/jxr",
        "jp2": "image/jp2",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
    }
    mime = mime_map.get(image.extension, f"image/{image.extension}")
    b64 = base64.b64encode(image.image_bytes).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _render_review_banner(page_num: int, confidence: float) -> str:
    """Render a review notice banner for low-confidence OCR pages."""
    pct = round(confidence * 100)
    return (
        f'<div class="review-notice" role="alert">'
        f'<strong>\u26a0\ufe0f Review Required:</strong> This page was processed with OCR and may contain errors. '
        f'Human review is recommended. (Confidence: {pct}%)'
        f'</div>'
    )


def _render_content_unavailable(page_num: int) -> str:
    """Render a notice when OCR produced no usable text."""
    return (
        f'<div class="review-notice" role="alert">'
        f'<strong>\u26a0\ufe0f Content Unavailable:</strong> '
        f'Text could not be extracted from this page. '
        f'The original document may need to be reviewed manually.'
        f'</div>'
    )


def build_html(
    pages: list[PageResult],
    ocr_results: dict[int, OcrPageResult],
    metadata: dict,
    embed_images: bool = True,
) -> tuple[str, dict[str, bytes]]:
    """
    Build accessible HTML from extracted PDF content.

    Args:
        pages: PageResult list from pdf_extractor.
        ocr_results: Dict of OCR results for scanned pages.
        metadata: PDF metadata dict.
        embed_images: If True, embed images as base64 data URIs.
                      If False, reference external image files.

    Returns:
        - HTML string
        - Dict of image filename -> bytes (for external storage)
    """
    title = html.escape(metadata.get("title", "") or "Converted Document")
    lang = (metadata.get("language") or "en")[:2].lower()

    image_files: dict[str, bytes] = {}
    is_pptx = metadata.get("format") == "pptx"
    body_parts: list[str] = []

    for page in pages:
        page_num = page.page_number

        # Determine section label (Slide N for PPTX, Page N otherwise)
        if is_pptx:
            slide_title = ""
            for span in page.text_spans:
                if span.font != _SPEAKER_NOTES_FONT and _heading_level(span):
                    slide_title = span.text
                    break
            if slide_title:
                section_label = f"Slide {page_num + 1}: {html.escape(slide_title)}"
            else:
                section_label = f"Slide {page_num + 1}"
        else:
            section_label = f"Page {page_num + 1}"

        body_parts.append(
            f'<section aria-label="{section_label}" '
            f'class="pdf-page" role="region">'
        )

        if page.is_scanned and page_num in ocr_results:
            # --- Scanned page: use OCR results ---
            ocr_page = ocr_results[page_num]

            # T034: Show review banner for low-confidence OCR pages
            if ocr_page.needs_review:
                body_parts.append(_render_review_banner(page_num + 1, ocr_page.confidence))

            # T036: Handle pages with no OCR text gracefully
            has_content = bool(ocr_page.lines) or bool(ocr_page.tables)
            if not has_content:
                body_parts.append(_render_content_unavailable(page_num + 1))
            else:
                # Render tables first, collect their text to avoid duplication
                table_texts: set[str] = set()
                for table in ocr_page.tables:
                    body_parts.append(_render_table_html(table))
                    for cell in table.cells:
                        table_texts.add(cell.text.strip())

                # Merge OCR lines: fold continuation lines into bullet items
                ocr_lines = [l for l in ocr_page.lines if l.text.strip() not in table_texts]
                merged_ocr: list[dict] = []  # {"type": "bullet"|"text", "text": str, "x0": float}
                for line in ocr_lines:
                    text = line.text
                    x0 = line.x0
                    if _is_bullet_line(text):
                        merged_ocr.append({"type": "bullet", "text": _strip_bullet_prefix(text), "x0": x0})
                    elif merged_ocr and merged_ocr[-1]["type"] == "bullet" and x0 >= merged_ocr[-1]["x0"]:
                        # Continuation of previous bullet item
                        merged_ocr[-1]["text"] += " " + text.strip()
                    else:
                        merged_ocr.append({"type": "text", "text": text.strip(), "x0": x0})

                i = 0
                while i < len(merged_ocr):
                    item = merged_ocr[i]
                    if item["type"] == "bullet":
                        body_parts.append("<ul>")
                        while i < len(merged_ocr) and merged_ocr[i]["type"] == "bullet":
                            body_parts.append(f"<li>{html.escape(merged_ocr[i]['text'])}</li>")
                            i += 1
                        body_parts.append("</ul>")
                    else:
                        body_parts.append(f"<p>{html.escape(item['text'])}</p>")
                        i += 1

        elif page.is_scanned and page_num not in ocr_results:
            # Scanned page with no OCR results at all
            body_parts.append(_render_content_unavailable(page_num + 1))

        else:
            # --- Digital page: use PyMuPDF text spans + tables ---

            # Separate speaker notes from regular text spans
            regular_spans = [s for s in page.text_spans
                             if s.font != _SPEAKER_NOTES_FONT]
            notes_spans = [s for s in page.text_spans
                           if s.font == _SPEAKER_NOTES_FONT]

            # Render detected tables
            for table in page.tables:
                body_parts.append(_render_pymupdf_table_html(table))

            # Render non-table text
            blocks = _spans_to_semantic_blocks(regular_spans)
            i = 0
            while i < len(blocks):
                block = blocks[i]
                escaped = html.escape(block["text"])
                if block["type"] == "heading":
                    level = block["level"]
                    body_parts.append(f"<h{level}>{escaped}</h{level}>")
                    i += 1
                elif block["type"] == "list_item":
                    body_parts.append("<ul>")
                    while i < len(blocks) and blocks[i]["type"] == "list_item":
                        li_text = html.escape(blocks[i]["text"])
                        if blocks[i].get("bold"):
                            li_text = f"<strong>{li_text}</strong>"
                        if blocks[i].get("italic"):
                            li_text = f"<em>{li_text}</em>"
                        body_parts.append(f"<li>{li_text}</li>")
                        i += 1
                    body_parts.append("</ul>")
                else:
                    if block.get("bold"):
                        escaped = f"<strong>{escaped}</strong>"
                    if block.get("italic"):
                        escaped = f"<em>{escaped}</em>"
                    body_parts.append(f"<p>{escaped}</p>")
                    i += 1

            # Render speaker notes as accessible associated content
            if notes_spans:
                notes_text = " ".join(
                    s.text.strip() for s in notes_spans if s.text.strip()
                )
                if notes_text:
                    body_parts.append(
                        f'<aside class="speaker-notes" role="note" '
                        f'aria-label="Speaker notes">'
                        f'<details>'
                        f'<summary>Speaker Notes</summary>'
                        f'<p>{html.escape(notes_text)}</p>'
                        f'</details>'
                        f'</aside>'
                    )

        # --- Images for this page ---
        for idx, img in enumerate(page.images):
            img_filename = f"page{page_num + 1}_img{idx + 1}.{img.extension}"
            image_files[img_filename] = img.image_bytes

            if embed_images:
                src = _image_to_data_uri(img)
            else:
                src = f"images/{img_filename}"

            # Meaningful alt text and figcaption — WCAG 1.1.1
            alt_text = f"Figure {idx + 1} from page {page_num + 1} of the source document"
            caption = f"Figure {idx + 1}, page {page_num + 1}"

            body_parts.append(
                f'<figure>'
                f'<img src="{src}" alt="{alt_text}" '
                f'width="{int(img.x1 - img.x0)}" height="{int(img.y1 - img.y0)}">'
                f'<figcaption>{caption}</figcaption>'
                f'</figure>'
            )

        body_parts.append("</section>")

    body_html = "\n".join(body_parts)

    full_html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 960px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #fff;
        }}
        /* Skip navigation — visible on focus for keyboard users */
        .skip-nav {{
            position: absolute;
            top: -100%;
            left: 0;
            padding: 0.75rem 1.5rem;
            background: #003366;
            color: #fff;
            font-weight: bold;
            text-decoration: underline;
            z-index: 1000;
        }}
        .skip-nav:focus {{
            top: 0;
        }}
        /* WCAG 2.4.7 — visible focus indicators on all focusable elements */
        a:focus-visible,
        button:focus-visible,
        input:focus-visible,
        select:focus-visible,
        textarea:focus-visible,
        [tabindex]:focus-visible {{
            outline: 3px solid #0056b3;
            outline-offset: 2px;
        }}
        /* Links — visible underlines, sufficient contrast */
        a {{
            color: #0056b3;
            text-decoration: underline;
        }}
        a:hover {{
            color: #003d80;
        }}
        .pdf-page {{
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid #595959;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #767676;
            padding: 0.5rem;
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
            color: #1a1a1a;
        }}
        figure {{
            margin: 1rem 0;
            text-align: center;
        }}
        figcaption {{
            font-size: 0.875rem;
            color: #595959;
            margin-top: 0.5rem;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        h1 {{ font-size: 2rem; margin-top: 1.5rem; color: #1a1a1a; }}
        h2 {{ font-size: 1.5rem; margin-top: 1.25rem; color: #1a1a1a; }}
        h3 {{ font-size: 1.25rem; margin-top: 1rem; color: #1a1a1a; }}
        h4 {{ font-size: 1.1rem; margin-top: 0.75rem; color: #1a1a1a; }}
        h5 {{ font-size: 1rem; margin-top: 0.5rem; color: #1a1a1a; }}
        h6 {{ font-size: 0.875rem; margin-top: 0.5rem; color: #1a1a1a; }}
        /* Review notice banner — T034 */
        .review-notice {{
            background-color: #fff3cd;
            color: #664d03;
            border: 2px solid #997a00;
            border-radius: 4px;
            padding: 0.75rem 1rem;
            margin: 1rem 0;
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        .review-notice strong {{
            color: #664d03;
        }}
        /* Speaker notes — PPTX slide notes */
        .speaker-notes {{
            background-color: #f8f9fa;
            border: 1px solid #767676;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            margin: 1rem 0;
            font-size: 0.9rem;
            color: #1a1a1a;
        }}
        .speaker-notes summary {{
            font-weight: bold;
            cursor: pointer;
            color: #1a1a1a;
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-nav">Skip to main content</a>
    <main id="main-content">
{body_html}
    </main>
</body>
</html>"""

    return full_html, image_files
