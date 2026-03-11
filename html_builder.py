"""
Semantic HTML builder.
Converts extracted PDF content (text spans, images, OCR results) into
accessible HTML that preserves the visual structure of the original PDF.
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
        for cell in row:
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
    body_parts: list[str] = []

    for page in pages:
        page_num = page.page_number
        body_parts.append(f'<section aria-label="Page {page_num + 1}" class="pdf-page">')

        if page.is_scanned and page_num in ocr_results:
            # --- Scanned page: use OCR results ---
            ocr_page = ocr_results[page_num]

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

        else:
            # --- Digital page: use PyMuPDF text spans + tables ---

            # Render detected tables
            for table in page.tables:
                body_parts.append(_render_pymupdf_table_html(table))

            # Render non-table text
            blocks = _spans_to_semantic_blocks(page.text_spans)
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

        # --- Images for this page ---
        for idx, img in enumerate(page.images):
            img_filename = f"page{page_num + 1}_img{idx + 1}.{img.extension}"
            image_files[img_filename] = img.image_bytes

            if embed_images:
                src = _image_to_data_uri(img)
            else:
                src = f"images/{img_filename}"

            body_parts.append(
                f'<figure>'
                f'<img src="{src}" alt="Image from page {page_num + 1}" '
                f'width="{int(img.x1 - img.x0)}" height="{int(img.y1 - img.y0)}">'
                f'<figcaption>Image from page {page_num + 1}</figcaption>'
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
        }}
        .pdf-page {{
            margin-bottom: 2rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid #e0e0e0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 0.5rem;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        figure {{
            margin: 1rem 0;
            text-align: center;
        }}
        figcaption {{
            font-size: 0.875rem;
            color: #666;
            margin-top: 0.5rem;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        h1 {{ font-size: 2rem; margin-top: 1.5rem; }}
        h2 {{ font-size: 1.5rem; margin-top: 1.25rem; }}
        h3 {{ font-size: 1.25rem; margin-top: 1rem; }}
        h4 {{ font-size: 1.1rem; margin-top: 0.75rem; }}
    </style>
</head>
<body>
    <main>
{body_html}
    </main>
</body>
</html>"""

    return full_html, image_files
