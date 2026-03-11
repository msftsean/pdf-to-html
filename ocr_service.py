"""
Azure Document Intelligence integration for OCR on scanned PDF pages.
Uses the prebuilt-layout model to extract text, tables, and reading order.
"""

import logging
import os
from dataclasses import dataclass, field

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    DocumentAnalysisFeature,
    AnalyzeResult,
)
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


@dataclass
class OcrSpan:
    """A text span extracted via OCR."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float


@dataclass
class OcrTableCell:
    """A single cell in a detected table."""
    row_index: int
    column_index: int
    text: str
    is_header: bool = False
    row_span: int = 1
    column_span: int = 1


@dataclass
class OcrTable:
    """A table detected on a page."""
    row_count: int
    column_count: int
    cells: list[OcrTableCell] = field(default_factory=list)


@dataclass
class OcrPageResult:
    """OCR results for a single page."""
    page_number: int  # 0-based to match PageResult
    width: float
    height: float
    lines: list[OcrSpan] = field(default_factory=list)
    tables: list[OcrTable] = field(default_factory=list)


def _get_client() -> DocumentIntelligenceClient:
    """Create a Document Intelligence client using Entra ID authentication."""
    endpoint = os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"]
    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )


def _polygon_to_bbox(polygon: list[float]) -> tuple[float, float, float, float]:
    """Convert a polygon [x1,y1,x2,y2,...] to (x0, y0, x1, y1) bounding box."""
    xs = polygon[0::2]
    ys = polygon[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def ocr_pdf_pages(pdf_data: bytes, page_numbers: list[int]) -> dict[int, OcrPageResult]:
    """
    Run OCR on specific pages of a PDF using Azure Document Intelligence.

    Args:
        pdf_data: The full PDF file bytes.
        page_numbers: 0-based page numbers that need OCR.

    Returns:
        Dict mapping 0-based page number to OcrPageResult.
    """
    if not page_numbers:
        return {}

    client = _get_client()

    # Document Intelligence uses 1-based page numbers
    di_pages = ",".join(str(p + 1) for p in page_numbers)

    poller = client.begin_analyze_document(
        "prebuilt-layout",
        AnalyzeDocumentRequest(bytes_source=pdf_data),
        pages=di_pages,
        features=[DocumentAnalysisFeature.QUERY_FIELDS],
    )
    result: AnalyzeResult = poller.result()

    results: dict[int, OcrPageResult] = {}

    # Process pages
    if result.pages:
        for di_page in result.pages:
            page_num = di_page.page_number - 1  # convert to 0-based
            if page_num not in [p for p in page_numbers]:
                continue

            ocr_page = OcrPageResult(
                page_number=page_num,
                width=di_page.width or 0,
                height=di_page.height or 0,
            )

            # Extract lines with positions
            if di_page.lines:
                for line in di_page.lines:
                    if line.polygon and line.content:
                        x0, y0, x1, y1 = _polygon_to_bbox(line.polygon)
                        ocr_page.lines.append(OcrSpan(
                            text=line.content,
                            x0=x0, y0=y0, x1=x1, y1=y1,
                            confidence=1.0,  # line-level confidence not always available
                        ))

            results[page_num] = ocr_page

    # Process tables and assign to pages
    if result.tables:
        for table in result.tables:
            if not table.bounding_regions:
                continue
            table_page = table.bounding_regions[0].page_number - 1
            if table_page not in results:
                continue

            ocr_table = OcrTable(
                row_count=table.row_count,
                column_count=table.column_count,
            )
            if table.cells:
                for cell in table.cells:
                    ocr_table.cells.append(OcrTableCell(
                        row_index=cell.row_index,
                        column_index=cell.column_index,
                        text=cell.content or "",
                        is_header=(cell.kind == "columnHeader") if cell.kind else False,
                        row_span=cell.row_span or 1,
                        column_span=cell.column_span or 1,
                    ))
            results[table_page].tables.append(ocr_table)

    return results
