"""
Extract figures from the Bidaw FAST'26 paper — v2.

Strategy:
- Render each page at high DPI for output.
- For every "Figure N:" caption, find vector drawings + raster image bboxes
  whose center is within the caption's column AND above the caption's y0.
- Union these bboxes -> figure bbox.
- Fall back to text-block boundary if no drawings found.
- Add small padding.
"""

import re
import os
import json
import fitz

PDF = "/home/pdaejun/bidaw/fast26-hu-shipeng.pdf"
OUT = "/home/pdaejun/bidaw/figures"
DPI = 240
ZOOM = DPI / 72.0

os.makedirs(OUT, exist_ok=True)
doc = fitz.open(PDF)

LEFT_COL  = (50, 305)
RIGHT_COL = (305, 565)
PAGE_HEADER_BOTTOM = 70  # ignore everything above this (header / page number)


def column_for(cap_bbox):
    cx0, _, cx1, _ = cap_bbox
    if cx0 < 200 and cx1 > 330:
        return "full", (LEFT_COL[0] - 4, RIGHT_COL[1] + 4)
    if cx0 < 200:
        return "left", (LEFT_COL[0] - 4, LEFT_COL[1] + 4)
    return "right", (RIGHT_COL[0] - 4, RIGHT_COL[1] + 4)


def gather_caption_blocks(page):
    caps = []
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, text, *_ = b
        if not text:
            continue
        m = re.search(r"Figure\s+(\d+)\s*:", text)
        if m:
            caps.append({"fig": int(m.group(1)), "bbox": (x0, y0, x1, y1)})
    caps.sort(key=lambda c: c["bbox"][1])
    return caps


def gather_graphic_bboxes(page):
    """Return list of (x0, y0, x1, y1) for vector drawings + images on page."""
    out = []
    # raster images
    for im in page.get_images(full=True):
        xref = im[0]
        for r in page.get_image_rects(xref):
            out.append((r.x0, r.y0, r.x1, r.y1))
    # vector drawings
    for d in page.get_drawings():
        r = d.get("rect")
        if r is None:
            continue
        # filter degenerate / page-sized rects
        if r.width < 2 or r.height < 2:
            continue
        if r.width > page.rect.width * 0.95 and r.height > page.rect.height * 0.95:
            continue
        out.append((r.x0, r.y0, r.x1, r.y1))
    return out


def union_bbox(boxes):
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)
    return (x0, y0, x1, y1)


def extract_for_caption(page, cap, prev_caps_on_page):
    cx0, cy0, cx1, cy1 = cap["bbox"]
    col_kind, (cl, cr) = column_for(cap["bbox"])

    # Lower bound on figure top: bottom of previous caption in same column on this page,
    # else page header bottom.
    top_floor = PAGE_HEADER_BOTTOM
    for pc in prev_caps_on_page:
        pk, _ = column_for(pc["bbox"])
        # If prev caption shares column or one of them is full-width, treat its bottom as floor
        same = (pk == col_kind) or (pk == "full") or (col_kind == "full")
        if same and pc["bbox"][3] < cy0:
            top_floor = max(top_floor, pc["bbox"][3] + 4)

    grx = gather_graphic_bboxes(page)
    # Filter graphics that fall in the column horizontally and lie strictly between top_floor and caption.y0
    relevant = []
    for g in grx:
        gx0, gy0, gx1, gy1 = g
        cx_center = (gx0 + gx1) / 2
        # horizontal: center inside column, OR for full-width caption accept anything spanning both cols
        if col_kind == "full":
            in_col = True
        else:
            in_col = (cl - 2) <= cx_center <= (cr + 2)
        if not in_col:
            continue
        if gy1 > cy0 + 1:  # extends below caption
            continue
        if gy0 < top_floor - 1:
            continue
        relevant.append(g)

    used_graphics = bool(relevant)
    if relevant:
        gx0, gy0, gx1, gy1 = union_bbox(relevant)
        # pad
        top    = max(top_floor, gy0 - 4)
        bottom = min(cy0 - 1, gy1 + 4)
        left   = max(cl,   gx0 - 6)
        right  = min(cr,   gx1 + 6)
    else:
        # Fallback: use text blocks above caption in column
        top = top_floor
        for b in page.get_text("blocks"):
            x0, y0, x1, y1, text, *_ = b
            if not text or y1 >= cy0 - 1:
                continue
            cx_center = (x0 + x1) / 2
            if col_kind != "full" and not (cl - 2 <= cx_center <= cr + 2):
                continue
            if y1 > top:
                top = y1 + 4
        left, right = cl, cr
        bottom = cy0 - 2

    if bottom - top < 30:
        top = max(top_floor, cy0 - 360)

    return col_kind, used_graphics, (left, top, right, bottom)


results = {}
for page_idx in range(len(doc)):
    page = doc[page_idx]
    caps = gather_caption_blocks(page)
    if not caps:
        continue
    for i, cap in enumerate(caps):
        col_kind, used_g, bbox = extract_for_caption(page, cap, caps[:i])
        rect = fitz.Rect(*bbox)
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=rect, alpha=False)
        out_path = os.path.join(OUT, f"figure_{cap['fig']:02d}.png")
        pix.save(out_path)
        results[cap["fig"]] = {
            "page": page_idx + 1,
            "col": col_kind,
            "used_graphics": used_g,
            "bbox_pts": [round(v, 1) for v in bbox],
            "file": out_path,
        }

# Pages for reference
pages_dir = os.path.join(OUT, "pages")
os.makedirs(pages_dir, exist_ok=True)
for page_idx in range(len(doc)):
    page = doc[page_idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), alpha=False)
    pix.save(os.path.join(pages_dir, f"page_{page_idx+1:02d}.png"))

with open(os.path.join(OUT, "_extraction.json"), "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(results)} figures")
for fig in sorted(results):
    info = results[fig]
    flag = "G" if info["used_graphics"] else "T"
    print(f"  Fig{fig:>2} [{flag}] page {info['page']:>2} col={info['col']:<5} bbox={info['bbox_pts']}")
