"""Apply manual bbox overrides for figures that auto-extraction clipped."""
import os, fitz

PDF = "/home/pdaejun/bidaw/fast26-hu-shipeng.pdf"
OUT = "/home/pdaejun/bidaw/figures"
DPI = 240
ZOOM = DPI / 72.0

# figure_id -> (page_index_1based, x0, y0, x1, y1) in PDF points
OVERRIDES = {
    11: (7, 318, 60, 552, 235),     # extend top to capture labels above circles
    1:  (2, 311, 245, 569, 318),    # tighten Figure 1
    6:  (5, 50, 230, 296, 318),     # Fig 6 a/b CDF + bar
}

doc = fitz.open(PDF)
for fig_id, (page_one, x0, y0, x1, y1) in OVERRIDES.items():
    page = doc[page_one - 1]
    rect = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=rect, alpha=False)
    out_path = os.path.join(OUT, f"figure_{fig_id:02d}.png")
    pix.save(out_path)
    print(f"Re-saved Figure {fig_id} -> {out_path}")
