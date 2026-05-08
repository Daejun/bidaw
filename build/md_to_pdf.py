"""Convert Markdown study materials to PDF with Korean font support."""
import sys, os, re
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

CSS_STR = """
@page {
    size: A4;
    margin: 22mm 18mm 24mm 18mm;
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-family: "Noto Sans CJK KR", sans-serif;
        font-size: 9pt;
        color: #888;
    }
    @bottom-left {
        content: string(doctitle);
        font-family: "Noto Sans CJK KR", sans-serif;
        font-size: 9pt;
        color: #888;
    }
}
html { font-size: 11pt; }
body {
    /* DejaVu Sans is added so math/superscript glyphs (ᵀ ᵢ √ Σ) that the
       Noto CJK KR family lacks still render instead of falling back to ?.   */
    font-family: "Noto Sans CJK KR", "Noto Sans", "DejaVu Sans", sans-serif;
    color: #1f2937;
    line-height: 1.55;
    font-feature-settings: "kern" 1;
}
h1 {
    string-set: doctitle content();
    color: #1F3A68;
    font-size: 22pt;
    border-bottom: 3px solid #E86A33;
    padding-bottom: 0.25em;
    margin-top: 0.4em;
    page-break-before: avoid;
}
h2 {
    color: #1F3A68;
    font-size: 16pt;
    border-bottom: 1px solid #d0d5dd;
    padding-bottom: 0.15em;
    margin-top: 1.6em;
    page-break-after: avoid;
}
h3 {
    color: #1F3A68;
    font-size: 13pt;
    margin-top: 1.2em;
    page-break-after: avoid;
}
h4 {
    color: #374151;
    font-size: 11.5pt;
    margin-top: 1em;
    page-break-after: avoid;
}
p { margin: 0.45em 0; }
ul, ol { margin: 0.4em 0 0.6em 1.2em; padding-left: 0.6em; }
li { margin: 0.15em 0; }
li > p { margin: 0.15em 0; }
strong { color: #111827; }
em { color: #b45309; font-style: italic; }
code {
    font-family: "DejaVu Sans Mono", "Consolas", monospace;
    background: #f1f4f9;
    color: #1F3A68;
    border-radius: 3px;
    padding: 1px 4px;
    font-size: 0.92em;
}
pre {
    background: #f7f9fc;
    border-left: 3px solid #1F3A68;
    padding: 8px 12px;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 9.5pt;
    line-height: 1.4;
    overflow-x: auto;
    page-break-inside: avoid;
    margin: 0.6em 0;
}
pre code { background: transparent; padding: 0; color: inherit; }
blockquote {
    border-left: 3px solid #E86A33;
    background: #fff7ee;
    padding: 6px 12px;
    margin: 0.6em 0;
    color: #6b4a23;
}
hr {
    border: none;
    border-top: 1px dashed #d0d5dd;
    margin: 1.4em 0;
}
table {
    border-collapse: collapse;
    margin: 0.6em 0;
    font-size: 10.5pt;
    page-break-inside: avoid;
    width: auto;
}
th, td {
    border: 1px solid #d0d5dd;
    padding: 5px 9px;
    text-align: left;
    vertical-align: top;
}
th {
    background: #1F3A68;
    color: white;
    font-weight: 600;
}
tr:nth-child(even) td { background: #f7f9fc; }

/* Highlighted "Q:" / "A:" lines (best-effort visual cue) */
.qa-q { color: #1F3A68; font-weight: 700; }
.qa-a { color: #b45309; }

/* Cover */
.cover {
    height: 240mm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    page-break-after: always;
}
.cover .kicker {
    color: #E86A33;
    font-weight: 700;
    letter-spacing: 0.08em;
    font-size: 11pt;
    text-transform: uppercase;
}
.cover h1 {
    border: none;
    color: #1F3A68;
    font-size: 30pt;
    margin: 12pt 0 4pt 0;
}
.cover .sub {
    color: #6b6b6b;
    font-size: 13pt;
    margin-top: 2pt;
}
.cover .meta {
    margin-top: 80pt;
    color: #6b6b6b;
    font-size: 10.5pt;
    line-height: 1.7;
}
"""

EXTENSIONS = [
    "extra",        # tables, fenced_code, footnotes, etc.
    "sane_lists",
    "toc",
    "codehilite",
]
EXT_CONFIGS = {
    "codehilite": {"guess_lang": False, "noclasses": True},
}


def md_to_html(md_text, *, kicker, title, subtitle):
    body_html = markdown.markdown(md_text, extensions=EXTENSIONS, extension_configs=EXT_CONFIGS)
    cover = f"""
    <div class="cover">
        <div class="kicker">{kicker}</div>
        <h1>{title}</h1>
        <div class="sub">{subtitle}</div>
        <div class="meta">
            Bidaw — FAST '26 paper seminar 보조자료<br>
            Bidaw: Enhancing Key-Value Caching for Interactive LLM Serving via Bidirectional Computation–Storage Awareness<br>
            Hu et al., FAST '26
        </div>
    </div>
    """
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title></head>
<body>{cover}{body_html}</body></html>"""


def convert(md_path, pdf_path, *, kicker, title, subtitle):
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    # Strip the very first H1 from md body (we use cover instead)
    md = re.sub(r"^# .*?\n", "", md, count=1)
    html = md_to_html(md, kicker=kicker, title=title, subtitle=subtitle)
    fc = FontConfiguration()
    HTML(string=html).write_pdf(
        pdf_path,
        stylesheets=[CSS(string=CSS_STR, font_config=fc)],
        font_config=fc,
    )
    print(f"  {os.path.basename(pdf_path):40s}  ({os.path.getsize(pdf_path)/1024:.0f} KB)")


JOBS = [
    {
        "md":  "/home/pdaejun/bidaw/Bidaw_study_notes.md",
        "pdf": "/home/pdaejun/bidaw/Bidaw_study_notes.pdf",
        "kicker":   "Deep-dive Study Notes",
        "title":    "Bidaw 학습 노트",
        "subtitle": "논문 + 배경 지식 보강",
    },
    {
        "md":  "/home/pdaejun/bidaw/Bidaw_study_notes_brief.md",
        "pdf": "/home/pdaejun/bidaw/Bidaw_study_notes_brief.pdf",
        "kicker":   "Study Notes — Brief",
        "title":    "Bidaw 학습 노트 (간략판)",
        "subtitle": "3–4 페이지 다이제스트",
    },
    {
        "md":  "/home/pdaejun/bidaw/Bidaw_qa.md",
        "pdf": "/home/pdaejun/bidaw/Bidaw_qa.pdf",
        "kicker":   "Anticipated Tough Questions",
        "title":    "Bidaw 예상 까다로운 질문 30선",
        "subtitle": "전문가 청중 방어용",
    },
    {
        "md":  "/home/pdaejun/bidaw/Bidaw_qa_brief.md",
        "pdf": "/home/pdaejun/bidaw/Bidaw_qa_brief.pdf",
        "kicker":   "Q&A — Brief",
        "title":    "Bidaw 예상 질문 10선 (간략판)",
        "subtitle": "발표 직전 빠른 점검",
    },
    {
        "md":  "/home/pdaejun/bidaw/Bidaw_cheatsheet.md",
        "pdf": "/home/pdaejun/bidaw/Bidaw_cheatsheet.pdf",
        "kicker":   "Cheat Sheet",
        "title":    "Bidaw 1-페이지 Cheat Sheet",
        "subtitle": "발표 5분 전 훑는 압축 요약",
    },
]

if __name__ == "__main__":
    print("Converting Markdown study materials to PDF…")
    for job in JOBS:
        convert(job["md"], job["pdf"],
                kicker=job["kicker"], title=job["title"], subtitle=job["subtitle"])
    print("Done.")
