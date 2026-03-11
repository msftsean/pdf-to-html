"""Debug script: dump spans from a PDF page to inspect layout."""
import pymupdf

doc = pymupdf.open("images/Fy26WebSchedules_10-14-2025.pdf")
page = doc[1]  # page 2
print(f"Page 2 size: {page.rect.width:.0f}x{page.rect.height:.0f}")

# Check for tables
tabs = page.find_tables()
print(f"find_tables(): {len(tabs.tables)} tables")

blocks = page.get_text("dict")["blocks"]
count = 0
for b in blocks:
    if b["type"] != 0:
        continue
    for l in b["lines"]:
        for s in l["spans"]:
            t = s["text"].strip()
            if not t:
                continue
            bbox = s["bbox"]
            print(f"  x0={bbox[0]:6.1f} y0={bbox[1]:6.1f} x1={bbox[2]:6.1f} y1={bbox[3]:6.1f}  sz={s['size']:4.1f}  {t[:80]}")
            count += 1
            if count >= 80:
                break
        if count >= 80:
            break
    if count >= 80:
        break
doc.close()
