#!/usr/bin/env python3
"""
Generate sample PDF documents for the evaluation suite.
Uses fpdf2 to create programmatic test PDFs covering various document structures.
"""

import os
import struct
import zlib
from pathlib import Path
from fpdf import FPDF


SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
    "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
)

LOREM2 = (
    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
    "eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, "
    "sunt in culpa qui officia deserunt mollit anim id est laborum."
)

LOREM3 = (
    "Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, "
    "turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis "
    "sollicitudin mauris. Integer in mauris eu nibh euismod gravida."
)


def _create_png_image(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Create a minimal solid-color PNG image in memory."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # IDAT - raw image data
    raw_rows = b""
    row_bytes = bytes([r, g, b]) * width
    for _ in range(height):
        raw_rows += b"\x00" + row_bytes  # filter byte 0 (None) per row

    compressed = zlib.compress(raw_rows)
    idat = _chunk(b"IDAT", compressed)

    # IEND
    iend = _chunk(b"IEND", b"")

    return sig + ihdr + idat + iend


def generate_simple_memo() -> Path:
    """T080-1: Single page memo with title + date + 3 paragraphs."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 15, "Internal Memorandum", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # Date line
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Date: January 15, 2025", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "To: All Department Heads", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "From: Office of the Secretary", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Subject: Quarterly Review Process Updates", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # 3 paragraphs
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 6, LOREM)
    pdf.ln(5)
    pdf.multi_cell(0, 6, LOREM2)
    pdf.ln(5)
    pdf.multi_cell(0, 6, LOREM3)

    path = SAMPLES_DIR / "simple-memo.pdf"
    pdf.output(str(path))
    return path


def generate_digital_report() -> Path:
    """T080-2: Multi-page report with headings, TOC, tables, lists."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)

    # --- Page 1: Title page ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 32)
    pdf.ln(60)
    pdf.cell(0, 20, "Annual Performance Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 16)
    pdf.cell(0, 12, "North Carolina Department of Information Technology", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 12, "Fiscal Year 2024-2025", new_x="LMARGIN", new_y="NEXT", align="C")

    # --- Page 2: Table of contents ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    toc_items = [
        "1. Executive Summary .......................... 3",
        "2. Department Overview ........................ 3",
        "   2.1 Mission and Vision ..................... 3",
        "   2.2 Organizational Structure ............... 3",
        "3. Performance Metrics ........................ 4",
        "4. Budget Summary ............................. 4",
        "5. Recommendations ............................ 5",
    ]
    for item in toc_items:
        pdf.cell(0, 8, item, new_x="LMARGIN", new_y="NEXT")

    # --- Page 3: Executive Summary + Department Overview ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "1. Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(3)
    pdf.multi_cell(0, 6, LOREM)
    pdf.ln(5)
    pdf.multi_cell(0, 6, LOREM2)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "2. Department Overview", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "2.1 Mission and Vision", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(2)
    pdf.multi_cell(0, 6, LOREM3)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "2.2 Organizational Structure", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(2)
    pdf.multi_cell(0, 6, LOREM)

    # --- Page 4: Performance Metrics with data table ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "3. Performance Metrics", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Data table
    pdf.set_font("Helvetica", "B", 11)
    col_widths = [50, 35, 35, 35, 35]
    headers = ["Metric", "Q1", "Q2", "Q3", "Q4"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 11)
    table_data = [
        ["Service Uptime (%)", "99.7", "99.8", "99.9", "99.6"],
        ["Tickets Resolved", "1,245", "1,389", "1,502", "1,678"],
        ["Avg Response (hrs)", "2.3", "2.1", "1.8", "1.9"],
        ["Customer Sat (%)", "87", "89", "91", "90"],
        ["Projects Delivered", "12", "15", "18", "14"],
        ["Budget Utilization", "92%", "88%", "95%", "91%"],
    ]
    for row in table_data:
        for i, cell in enumerate(row):
            pdf.cell(col_widths[i], 7, cell, border=1, align="C" if i > 0 else "L")
        pdf.ln()

    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "4. Budget Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(3)
    pdf.multi_cell(0, 6, LOREM2)

    # Bulleted list
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Budget Items:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    bullets = [
        "- Infrastructure modernization: $2.4M",
        "- Cybersecurity enhancements: $1.8M",
        "- Cloud migration services: $3.1M",
        "- Staff training and development: $750K",
        "- Digital accessibility compliance: $420K",
    ]
    for b in bullets:
        pdf.cell(0, 7, b, new_x="LMARGIN", new_y="NEXT")

    # --- Page 5: Recommendations ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "5. Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(3)
    pdf.multi_cell(0, 6, LOREM)
    pdf.ln(5)
    pdf.multi_cell(0, 6, LOREM3)

    path = SAMPLES_DIR / "digital-report.pdf"
    pdf.output(str(path))
    return path


def generate_complex_tables() -> Path:
    """T080-3: Tables-focused PDF with varying column counts and widths."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "Data Tables Reference", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    # Table 1: Simple 3x4
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Table 1: Employee Directory", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    w3 = [60, 65, 65]
    for i, h in enumerate(["Name", "Department", "Extension"]):
        pdf.cell(w3[i], 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 11)
    rows3 = [
        ["Alice Johnson", "Engineering", "x4521"],
        ["Bob Martinez", "Human Resources", "x3100"],
        ["Carol Chen", "Finance", "x2890"],
        ["David Williams", "IT Security", "x4150"],
    ]
    for row in rows3:
        for i, cell in enumerate(row):
            pdf.cell(w3[i], 7, cell, border=1)
        pdf.ln()

    pdf.ln(12)

    # Table 2: Wide 7-column table
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Table 2: Monthly Performance Dashboard", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 9)
    w7 = [28, 24, 24, 24, 24, 28, 38]
    headers7 = ["Month", "Revenue", "Expense", "Profit", "Staff", "Uptime", "Satisfaction"]
    for i, h in enumerate(headers7):
        pdf.cell(w7[i], 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    rows7 = [
        ["January", "$45.2K", "$38.1K", "$7.1K", "142", "99.8%", "92%"],
        ["February", "$42.8K", "$36.5K", "$6.3K", "140", "99.9%", "91%"],
        ["March", "$48.1K", "$39.2K", "$8.9K", "145", "99.7%", "93%"],
        ["April", "$51.3K", "$41.0K", "$10.3K", "148", "99.9%", "94%"],
        ["May", "$49.7K", "$40.5K", "$9.2K", "147", "99.6%", "90%"],
        ["June", "$53.4K", "$42.8K", "$10.6K", "150", "99.8%", "95%"],
    ]
    for row in rows7:
        for i, cell in enumerate(row):
            pdf.cell(w7[i], 7, cell, border=1, align="C" if i > 0 else "L")
        pdf.ln()

    # New page for Table 3
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Table 3: Full-Width Budget Allocation", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    w_full = [50, 30, 30, 30, 30, 20]
    headers_full = ["Category", "FY2022", "FY2023", "FY2024", "FY2025", "Change"]
    for i, h in enumerate(headers_full):
        pdf.cell(w_full[i], 8, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    rows_full = [
        ["Personnel", "$12.5M", "$13.2M", "$14.0M", "$14.8M", "+5.7%"],
        ["Technology", "$8.3M", "$9.1M", "$10.5M", "$11.2M", "+6.7%"],
        ["Facilities", "$3.2M", "$3.4M", "$3.5M", "$3.6M", "+2.9%"],
        ["Training", "$1.1M", "$1.3M", "$1.5M", "$1.7M", "+13.3%"],
        ["Operations", "$5.8M", "$6.0M", "$6.3M", "$6.5M", "+3.2%"],
        ["Total", "$30.9M", "$33.0M", "$35.8M", "$37.8M", "+5.6%"],
    ]
    for row in rows_full:
        for i, cell in enumerate(row):
            style = "B" if row[0] == "Total" else ""
            if style:
                pdf.set_font("Helvetica", "B", 10)
            else:
                pdf.set_font("Helvetica", "", 10)
            pdf.cell(w_full[i], 7, cell, border=1, align="C" if i > 0 else "L")
        pdf.ln()

    path = SAMPLES_DIR / "complex-tables.pdf"
    pdf.output(str(path))
    return path


def generate_image_heavy() -> Path:
    """T080-4: PDF with embedded geometric images and captions."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 14, "Visual Assets Report", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 6, (
        "This document contains visual elements for testing image extraction "
        "and alt text generation in the WCAG-compliant converter."
    ))
    pdf.ln(5)

    # Generate and embed colored rectangles as images
    colors = [
        ("Blue Status Indicator", 0, 51, 153, 120, 60),
        ("Green Performance Bar", 0, 128, 64, 150, 40),
        ("Red Alert Banner", 204, 0, 0, 140, 50),
        ("Orange Notification Badge", 255, 140, 0, 80, 80),
    ]

    import tempfile
    tmp_files = []

    for label, r, g, b, w, h in colors:
        png_data = _create_png_image(w, h, r, g, b)
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(png_data)
        tmp.flush()
        tmp_files.append(tmp.name)

        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")

        pdf.image(tmp.name, x=pdf.get_x() + 10, w=w, h=h)
        pdf.ln(h + 3)

        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, f"Figure: {label} ({w}x{h} pixels)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)

    # Cleanup temp files
    for f in tmp_files:
        try:
            os.unlink(f)
        except OSError:
            pass

    path = SAMPLES_DIR / "image-heavy.pdf"
    pdf.output(str(path))
    return path


def generate_all() -> list[Path]:
    """Generate all sample PDFs. Returns list of created paths."""
    generators = [
        ("simple-memo.pdf", generate_simple_memo),
        ("digital-report.pdf", generate_digital_report),
        ("complex-tables.pdf", generate_complex_tables),
        ("image-heavy.pdf", generate_image_heavy),
    ]
    paths = []
    for name, gen_fn in generators:
        path = gen_fn()
        size_kb = path.stat().st_size / 1024
        print(f"  ✅ Generated {name} ({size_kb:.1f} KB)")
        paths.append(path)
    return paths


if __name__ == "__main__":
    print("Generating evaluation sample PDFs...")
    paths = generate_all()
    print(f"\n{len(paths)} samples created in {SAMPLES_DIR}/")
