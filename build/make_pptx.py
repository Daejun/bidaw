"""
Build the 30-slide Bidaw seminar deck.

- 16:9, ~30 slides
- Korean body text, English technical terms preserved
- Embeds extracted figures from /home/pdaejun/bidaw/figures
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

FIG_DIR = "/home/pdaejun/bidaw/figures"
OUT_PATH = "/home/pdaejun/bidaw/Bidaw_seminar.pptx"

# 16:9
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Color palette — vLLM Kwon (SOSP'23) style: large type, white background,
# one red emphasis colour, occasional pastel callout boxes.
COLOR_PRIMARY = RGBColor(0x1F, 0x29, 0x37)   # near-black title/body
COLOR_TEXT    = RGBColor(0x1F, 0x29, 0x37)
COLOR_ACCENT  = RGBColor(0xD9, 0x35, 0x2A)   # red emphasis on key terms/numbers
COLOR_LIGHT   = RGBColor(0x6B, 0x72, 0x80)   # kicker / footer / caption
COLOR_RULE    = RGBColor(0xE5, 0xE7, 0xEB)   # thin separator
COLOR_BG_BAND = RGBColor(0xFF, 0xFF, 0xFF)   # legacy alias for plain bg
COLOR_WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
# Soft pastel callouts (Kwon-style figure annotations)
COLOR_CALL_YELLOW = RGBColor(0xFF, 0xEF, 0xC8)
COLOR_CALL_BLUE   = RGBColor(0xD8, 0xE6, 0xFA)
COLOR_CALL_GREEN  = RGBColor(0xDC, 0xEE, 0xCB)
COLOR_CALL_PEACH  = RGBColor(0xFC, 0xE0, 0xCC)
# Title-slide vertical accent bars
COLOR_BAR_YELLOW  = RGBColor(0xF5, 0xC2, 0x42)
COLOR_BAR_BLUE    = RGBColor(0x46, 0x88, 0xF1)

# Type scale (vLLM Kwon-inspired but slightly tightened so Korean
# titles fit on one line)
SIZE_TITLE    = 28   # slide title
SIZE_KICKER   = 12   # small label above title
SIZE_SUBHEAD  = 20   # within-slide section header
SIZE_BODY     = 18   # body text
SIZE_BODY_SM  = 16   # secondary text
SIZE_CAPTION  = 11   # figure caption
SIZE_FOOTER   = 10

KOREAN_FONT  = "맑은 고딕"        # 한글
LATIN_FONT   = "Calibri"         # 영문/숫자/기호
MONO_FONT    = "Consolas"

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H

BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def set_run(run, text, *, size=18, bold=False, color=COLOR_TEXT, italic=False, mono=False):
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = MONO_FONT if mono else LATIN_FONT
    # Set East Asian font for Korean glyphs via XML
    rPr = run._r.get_or_add_rPr()
    # remove existing eastAsia font if any
    for ea in rPr.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}ea"):
        rPr.remove(ea)
    from lxml import etree
    ea = etree.SubElement(rPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}ea")
    ea.set("typeface", KOREAN_FONT)


def add_textbox(slide, left, top, width, height, *, anchor="top"):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    if anchor == "middle":
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    elif anchor == "bottom":
        tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    return tf


def add_para(tf, text, *, size=18, bold=False, color=COLOR_TEXT, italic=False,
             align="left", bullet=None, mono=False, space_after=4):
    p = tf.add_paragraph() if tf.paragraphs[0].runs or tf.paragraphs[0].text else tf.paragraphs[0]
    p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
    p.space_after = Pt(space_after)
    if bullet:
        full = f"{bullet}  {text}"
    else:
        full = text
    run = p.add_run() if not (p.runs and not p.runs[0].text) else p.runs[0]
    set_run(run, full, size=size, bold=bold, color=color, italic=italic, mono=mono)


def add_rich_para(tf, segments, *, align="left", space_after=4, indent_level=0):
    """segments: list of dicts {text, size, bold, color, italic, mono}"""
    if tf.paragraphs[0].runs or tf.paragraphs[0].text:
        p = tf.add_paragraph()
    else:
        p = tf.paragraphs[0]
    p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[align]
    p.space_after = Pt(space_after)
    p.level = indent_level
    for i, seg in enumerate(segments):
        run = p.add_run()
        set_run(
            run,
            seg["text"],
            size=seg.get("size", 18),
            bold=seg.get("bold", False),
            color=seg.get("color", COLOR_TEXT),
            italic=seg.get("italic", False),
            mono=seg.get("mono", False),
        )


def add_rect(slide, left, top, width, height, fill, line=None):
    """Filled rectangle. In the minimal style, panels that used to be tinted
    callout bands (fill=COLOR_BG_BAND, no border) are auto-promoted to a
    bordered white box so the grouping meaning is kept without colour."""
    auto_border = (line is None and tuple(fill) == tuple(COLOR_BG_BAND))
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if auto_border:
        shp.line.color.rgb = COLOR_RULE
        shp.line.width = Pt(0.5)
    elif line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def add_line(slide, x1, y1, x2, y2, color=COLOR_RULE, weight=1.0):
    ln = slide.shapes.add_connector(1, x1, y1, x2, y2)
    ln.line.color.rgb = color
    ln.line.width = Pt(weight)
    return ln


def add_header_band(slide, title, *, kicker=None):
    """vLLM Kwon-style header: small grey kicker, large near-black title.
    No band, no rule by default — generous breathing room above body."""
    tf = add_textbox(slide, Inches(0.6), Inches(0.35), SLIDE_W - Inches(1.2), Inches(1.0))
    if kicker:
        add_rich_para(tf, [
            {"text": kicker.upper(), "size": SIZE_KICKER, "bold": True, "color": COLOR_LIGHT},
        ], space_after=2)
    add_rich_para(tf, [
        {"text": title, "size": SIZE_TITLE, "bold": True, "color": COLOR_PRIMARY},
    ])


def add_footer(slide, page_num, total=30):
    """Minimal footer: a small grey page number on the bottom-right.
    No conference name strip — Kwon-style decks keep the bottom clean."""
    tf2 = add_textbox(slide, SLIDE_W - Inches(1.2), Inches(7.05), Inches(0.9), Inches(0.3))
    add_rich_para(tf2, [
        {"text": f"{page_num}", "size": SIZE_FOOTER, "color": COLOR_LIGHT},
    ], align="right")


def add_image_fit(slide, fig_path, left, top, max_w, max_h, *, caption=None):
    """Add image scaled to fit within (max_w, max_h), centered horizontally inside that box.
       Returns (placed_left, placed_top, placed_w, placed_h)."""
    with Image.open(fig_path) as im:
        iw, ih = im.size
    aspect = iw / ih
    max_w_in = max_w / 914400
    max_h_in = max_h / 914400
    if max_w_in / max_h_in >= aspect:
        # height-bounded
        h_in = max_h_in
        w_in = h_in * aspect
    else:
        w_in = max_w_in
        h_in = w_in / aspect
    placed_left = left + Emu(int((max_w - Inches(w_in)) / 2))
    placed_top = top
    pic = slide.shapes.add_picture(fig_path, placed_left, placed_top, width=Inches(w_in), height=Inches(h_in))
    if caption:
        cap_tf = add_textbox(slide, left, placed_top + Inches(h_in) + Inches(0.05),
                             max_w, Inches(0.35))
        add_rich_para(cap_tf, [
            {"text": caption, "size": 10, "italic": True, "color": COLOR_LIGHT},
        ], align="center")
    return placed_left, placed_top, Inches(w_in), Inches(h_in)


def fig_path(fig_id):
    return os.path.join(FIG_DIR, f"figure_{fig_id:02d}.png")


# ============================================================================
# Slide builders
# ============================================================================

# ---- Slide 1: Title — vLLM Kwon style with vertical accent bars ----------
def slide_01():
    s = add_slide()
    # Vertical yellow + blue accent bars on the left
    add_rect(s, Inches(0.7), Inches(1.6), Inches(0.10), Inches(2.1),
             fill=COLOR_BAR_YELLOW)
    add_rect(s, Inches(0.7), Inches(4.4), Inches(0.10), Inches(0.9),
             fill=COLOR_BAR_BLUE)

    tf_title = add_textbox(s, Inches(1.1), Inches(1.55), SLIDE_W - Inches(2.0), Inches(2.3))
    add_rich_para(tf_title, [
        {"text": "Bidaw: Enhancing Key-Value Caching",
         "size": 38, "bold": True, "color": COLOR_PRIMARY},
    ], space_after=4)
    add_rich_para(tf_title, [
        {"text": "for Interactive LLM Serving",
         "size": 38, "bold": True, "color": COLOR_PRIMARY},
    ], space_after=8)
    add_rich_para(tf_title, [
        {"text": "via Bidirectional Computation–Storage Awareness",
         "size": 20, "color": COLOR_LIGHT},
    ])

    tf2 = add_textbox(s, Inches(1.1), Inches(4.4), SLIDE_W - Inches(2.0), Inches(0.9))
    add_rich_para(tf2, [
        {"text": "Shipeng Hu", "size": 18, "bold": True, "color": COLOR_PRIMARY},
        {"text": "  ·  Guangyan Zhang  ·  Yuqi Zhou  ·  Yaya Wei  ·  Ziyan Zhong  ·  Jike Chen",
         "size": 18, "color": COLOR_TEXT},
    ], space_after=2)
    add_rich_para(tf2, [
        {"text": "Tsinghua University · CUGB · China Telecom",
         "size": 14, "color": COLOR_LIGHT},
    ])

    tf3 = add_textbox(s, Inches(0.7), SLIDE_H - Inches(1.1), SLIDE_W - Inches(1.4), Inches(0.7))
    add_rich_para(tf3, [
        {"text": "FAST '26 Paper Seminar", "size": 18, "bold": True, "color": COLOR_LIGHT},
    ], space_after=2)
    add_rich_para(tf3, [
        {"text": "발표자: ____________    ·    일시: ____________",
         "size": 14, "color": COLOR_LIGHT},
    ])


# ---- Slide 2: Agenda ------------------------------------------------------
def slide_02():
    s = add_slide()
    add_header_band(s, "발표 순서", kicker="AGENDA")
    items = [
        ("1", "Background", "Interactive LLM serving과 KV cache 역할"),
        ("2", "Motivation",  "KV loading 병목과 워크로드 관찰 세 가지"),
        ("3", "Key Idea",    "Bidirectional computation–storage awareness"),
        ("4", "Mechanism 1", "I/O-aware request scheduling (compute 측)"),
        ("5", "Mechanism 2", "Previous-answer-based eviction (storage 측)"),
        ("6", "Mechanism 3", "Storage-efficient tensor caching"),
        ("7", "Evaluation",  "모델 5종에 걸친 핵심 plot 7개"),
        ("8", "Discussion",  "한계와 일반화 가능성"),
    ]
    top0 = Inches(1.55)
    row_h = Inches(0.62)
    for i, (n, head, body) in enumerate(items):
        y = top0 + row_h * i
        # Light grey leading number, no circle
        n_tf = add_textbox(s, Inches(0.55), y, Inches(0.65), row_h, anchor="middle")
        add_rich_para(n_tf, [
            {"text": n, "size": 18, "bold": True, "color": COLOR_LIGHT},
        ], align="right")
        tf = add_textbox(s, Inches(1.35), y, Inches(11), row_h, anchor="middle")
        add_rich_para(tf, [
            {"text": head, "size": 17, "bold": True, "color": COLOR_PRIMARY},
            {"text": "    " + body, "size": 18, "color": COLOR_TEXT},
        ])
    add_footer(s, 2)


# ---- Slide 3: What is interactive LLM serving? ----------------------------
def slide_03():
    s = add_slide()
    add_header_band(s, "Interactive LLM serving — 멀티 라운드 대화 패턴", kicker="BACKGROUND")
    # Image right
    add_image_fit(s, fig_path(1), Inches(6.7), Inches(1.3), Inches(6.3), Inches(3.0),
                  caption="Figure 1. 각 라운드의 답변은 이전 라운드의 KV tensor를 참조한다")
    # Bullets left
    tf = add_textbox(s, Inches(0.5), Inches(1.2), Inches(6.0), Inches(5.5))
    add_rich_para(tf, [
        {"text": "사례", "size": 20, "bold": True, "color": COLOR_PRIMARY}], space_after=4)
    for t in [
        "Replika · Duolingo · 챗봇 — 사용자와 LLM이 번갈아 주고받는 대화",
        "사용자 한 명당 평균 22.4 라운드 (P90 = 45 라운드)",
        "한 대화 지속 시간 평균 수 분, 길면 60분 이상",
    ]:
        add_rich_para(tf, [
            {"text": "•  ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_rich_para(tf, [
        {"text": "기술적 핵심", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    for t in [
        "N번째 라운드 답변 = 0~N-1 라운드의 KV를 재사용",
        "재계산은 GPU FLOPs 낭비 → caching이 필수",
    ]:
        add_rich_para(tf, [
            {"text": "•  ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_footer(s, 3)


# ---- Slide 4: KV cache 메커니즘 -------------------------------------------
def slide_04():
    s = add_slide()
    add_header_band(s, "KV cache 역할 — attention 재계산을 피하는 핵심 자료구조",
                    kicker="BACKGROUND")
    # Schematic on right (custom drawing) — wider to keep formula on one line
    diag_left = Inches(6.7); diag_top = Inches(1.4)
    add_rect(s, diag_left, diag_top, Inches(6.1), Inches(4.8), fill=COLOR_BG_BAND)
    tf_d = add_textbox(s, diag_left + Inches(0.2), diag_top + Inches(0.2),
                       Inches(5.7), Inches(4.4))
    add_rich_para(tf_d, [
        {"text": "Self-attention 요점", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tf_d, [
        {"text": "Attention(Q,K,V) = softmax(Q·K^T / sqrt(d))·V",
         "size": 18, "mono": True}], space_after=10)
    add_rich_para(tf_d, [
        {"text": "▸ 새 토큰 1개의 Q만 새로 계산", "size": 18}], space_after=2)
    add_rich_para(tf_d, [
        {"text": "▸ 과거 토큰의 K, V는 그대로 → ", "size": 18},
        {"text": "재사용 가능", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ], space_after=10)
    add_rich_para(tf_d, [
        {"text": "토큰 t개 · layer L · head h · head_dim d 일 때", "size": 18, "color": COLOR_LIGHT}
    ], space_after=2)
    add_rich_para(tf_d, [
        {"text": "KV size = 2 · t · L · h · d · sizeof(dtype)", "size": 18, "mono": True}
    ], space_after=8)
    add_rich_para(tf_d, [
        {"text": "예: OPT-13B에서 2,048 토큰이면 약 0.78 GB / user",
         "size": 18, "italic": True, "color": COLOR_LIGHT}])
    # Bullets left — narrowed so the right-side schematic box is not overrun
    tf = add_textbox(s, Inches(0.5), Inches(1.3), Inches(6.0), Inches(5.6))
    add_rich_para(tf, [
        {"text": "왜 KV cache가 필요한가", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=6)
    for t in [
        ("재계산을 피하면 ", "응답 latency가 그만큼 짧아진다"),
        ("저장 비용이 큼 ", "→ 효율적 관리가 시스템 설계의 첫 과제"),
        ("vLLM, PagedAttention 같은 가속 시스템도 ", "결국 KV cache 관리가 중심"),
    ]:
        add_rich_para(tf, [
            {"text": "•  ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18},
            {"text": t[1], "size": 18, "bold": True},
        ], space_after=4)
    add_rich_para(tf, [
        {"text": "이 논문이 다루는 KV는?", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tf, [
        {"text": "▸ 한 사용자의 ", "size": 18},
        {"text": "여러 라운드 대화 KV", "size": 18, "bold": True, "color": COLOR_ACCENT},
        {"text": "를 보존 — 사용자 간 KV 공유는 범위 밖", "size": 18},
    ])
    add_footer(s, 4)


# ---- Slide 5: GPU 메모리만으로는 안 되는 이유 -----------------------------
def slide_05():
    s = add_slide()
    add_header_band(s, "왜 GPU 메모리에 다 담을 수 없는가", kicker="BACKGROUND")
    # Image right
    add_image_fit(s, fig_path(5), Inches(6.7), Inches(1.3), Inches(6.3), Inches(4.5),
                  caption="Figure 5. 사용자 도착률 vs 동시 캐싱 KV 총량 (perf layer 200GB 기준)")
    tf = add_textbox(s, Inches(0.5), Inches(1.3), Inches(6.0), Inches(5.6))
    for t in [
        ("80GB A800 GPU 1장 ", "→ KV가 GPU 메모리를 곧바로 채움"),
        ("도착률 30 users/min에서 ",  "OPT-13B의 동시 캐싱 KV ≈ 480 GB"),
        ("LLM 서버의 host memory ", "≈ GPU 메모리의 1.6–3.2배"),
        ("→ host memory도 부족 ", "→ capacity SSD까지 같이 써야 함"),
    ]:
        add_rich_para(tf, [
            {"text": "•  ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18, "bold": True},
            {"text": t[1], "size": 18},
        ], space_after=6)
    # Big number callout
    box = add_rect(s, Inches(0.5), Inches(5.2), Inches(6.0), Inches(1.6),
                   fill=COLOR_BG_BAND)
    tfb = add_textbox(s, Inches(0.7), Inches(5.3), Inches(5.6), Inches(1.4),
                      anchor="middle")
    add_rich_para(tfb, [
        {"text": "동시 캐싱 KV가 perf layer를 ", "size": 20},
        {"text": "최대 3.91배", "size": 20, "bold": True, "color": COLOR_ACCENT},
        {"text": " 초과", "size": 20},
    ], space_after=2)
    add_rich_para(tfb, [
        {"text": "→ 2-tier (host memory + SSD) 캐싱이 불가피", "size": 18, "italic": True,
         "color": COLOR_LIGHT}])
    add_footer(s, 5)


# ---- Slide 6: Two-tier storage ------------------------------------------
def slide_06():
    s = add_slide()
    add_header_band(s, "기존 솔루션 — Two-tier storage caching",
                    kicker="BACKGROUND")
    add_image_fit(s, fig_path(2), Inches(0.5), Inches(1.3), Inches(7.5), Inches(3.4),
                  caption="Figure 2. Compute engine과 two-tier storage의 구조")
    tf = add_textbox(s, Inches(8.2), Inches(1.3), Inches(4.7), Inches(5.6))
    add_rich_para(tf, [
        {"text": "Performance layer", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "Host DRAM — 빠르지만 용량이 작음", "size": 18, "color": COLOR_LIGHT}],
        space_after=8)
    add_rich_para(tf, [
        {"text": "Capacity layer", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "SSD (RAID-5, 이 논문은 1.5 GB/s)", "size": 18, "color": COLOR_LIGHT}],
        space_after=10)
    add_rich_para(tf, [
        {"text": "주요 선행 시스템", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    for t in [
        ("CachedAttention", "[ATC ’24] queue-enhanced LRU eviction"),
        ("FlashGen",        "[FAST ’25] inclusive caching + GPU-fit scheduling"),
        ("HCache",          "[EuroSys ’25] intermediate activation 캐싱"),
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18, "bold": True},
            {"text": "  " + t[1], "size": 14, "color": COLOR_LIGHT},
        ], space_after=4)
    # Critical path callout
    add_rect(s, Inches(0.5), Inches(5.7), Inches(7.5), Inches(1.3), fill=COLOR_BG_BAND)
    tfc = add_textbox(s, Inches(0.7), Inches(5.8), Inches(7.1), Inches(1.1),
                      anchor="middle")
    add_rich_para(tfc, [
        {"text": "쓰기는 백그라운드로 빠졌지만, 읽기(load)는 여전히 ",
         "size": 18},
        {"text": "critical path 위에 남아 있다", "size": 18, "bold": True,
         "color": COLOR_ACCENT},
    ])
    add_footer(s, 6)


# ---- Slide 7: KV loading is the bottleneck -------------------------------
def slide_07():
    s = add_slide()
    add_header_band(s, "KV loading 자체가 병목 — 이상치 대비 큰 격차",
                    kicker="BACKGROUND")
    add_image_fit(s, fig_path(3), Inches(0.5), Inches(1.3), Inches(7.8), Inches(4.5),
                  caption="Figure 3. KV 재계산 / 기존 cache / Ideal cache의 latency 비교")
    tf = add_textbox(s, Inches(8.6), Inches(1.4), Inches(4.4), Inches(5.5))
    add_rich_para(tf, [
        {"text": "측정 환경", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "OPT-13B · A800 80GB · 200GB host · 1.5 GB/s SSD",
         "size": 14, "color": COLOR_LIGHT}], space_after=10)
    add_rich_para(tf, [
        {"text": "성능 격차", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tf, [
        {"text": "▸ 응답 latency ", "size": 18},
        {"text": "최대 3.8배 증가", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ], space_after=4)
    add_rich_para(tf, [
        {"text": "▸ throughput ", "size": 18},
        {"text": "최대 2.0배 감소", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ], space_after=10)
    add_rich_para(tf, [
        {"text": "Ideal vs 현실", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "Ideal = 모든 KV가 perf layer에 있다고 가정한 동일 시스템",
         "size": 14, "color": COLOR_LIGHT}], space_after=2)
    add_rich_para(tf, [
        {"text": "이 격차의 원인을 풀어내는 것이 이 논문의 출발점이다.",
         "size": 14, "italic": True, "color": COLOR_PRIMARY}])
    add_footer(s, 7)


# ---- Slide 8: Workload introduction --------------------------------------
def slide_08():
    s = add_slide()
    add_header_band(s, "워크로드 — 100만 라운드 규모의 실서비스 대화 trace",
                    kicker="MOTIVATION")
    add_image_fit(s, fig_path(4), Inches(0.5), Inches(1.3), Inches(7.8), Inches(3.6),
                  caption="Figure 4. (a) 사용자별 대화 지속시간, (b) 라운드 수 CDF")
    tf = add_textbox(s, Inches(8.6), Inches(1.4), Inches(4.4), Inches(5.5))
    add_rich_para(tf, [
        {"text": "Trace 출처", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "China Telecom · 100만+ 라운드 · 사용자 timestamp 포함",
         "size": 14, "color": COLOR_LIGHT}], space_after=10)
    add_rich_para(tf, [
        {"text": "ShareGPT · Mooncake와의 차이", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    for t in [
        "ShareGPT: 5.7 라운드 — 인터랙티브 분석엔 짧음",
        "Mooncake: 12k+ 토큰 — 길지만 대화 패턴 없음",
        "이 trace: 22.4 라운드 / 36 토큰 — 인터랙티브 워크로드에 잘 맞음",
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 14}], space_after=4)
    # Three observations preview — slim teaser instead of an oversize box
    tfo = add_textbox(s, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.7),
                      anchor="middle")
    add_rich_para(tfo, [
        {"text": "이어지는 세 슬라이드에서 다룰 내용  →  ", "size": 18, "color": COLOR_LIGHT},
        {"text": "Observation 1 · 2 · 3", "size": 22, "bold": True, "color": COLOR_ACCENT},
    ])
    add_footer(s, 8)


# ---- Slide 9: Obs 1 -------------------------------------------------------
def slide_09():
    s = add_slide()
    add_header_band(s, "Observation 1 — 동시 캐싱 KV가 perf layer를 크게 초과",
                    kicker="MOTIVATION")
    add_image_fit(s, fig_path(5), Inches(0.5), Inches(1.4), Inches(8.0), Inches(4.5),
                  caption="Figure 5. 사용자 도착률 vs 동시 캐싱 KV 총량 / 동시 사용자 수")
    tf = add_textbox(s, Inches(8.8), Inches(1.4), Inches(4.3), Inches(5.5))
    add_rich_para(tf, [
        {"text": "관찰", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    for t in [
        "한 사용자의 KV가 22.4 라운드 동안 살아 있음",
        "도착률↑ → 동시 사용자 수 선형 증가",
        "30 users/min에서 480 GB > perf 200 GB",
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_rich_para(tf, [
        {"text": "함의", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    for t in [
        "perf layer를 키워도 결국 한계가 있음",
        "eviction이 비효율적이면 capacity layer로 자주 떨어짐",
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_footer(s, 9)


# ---- Slide 10: Obs 2 ------------------------------------------------------
def slide_10():
    s = add_slide()
    add_header_band(s, "Observation 2 — KV access의 temporal locality가 매우 약함",
                    kicker="MOTIVATION")
    add_image_fit(s, fig_path(6), Inches(0.5), Inches(1.4), Inches(8.0), Inches(3.4),
                  caption="Figure 6. (a) Weighted reuse distance CDF, (b) hit rate")
    tf = add_textbox(s, Inches(8.8), Inches(1.4), Inches(4.3), Inches(5.5))
    add_rich_para(tf, [
        {"text": "Weighted reuse distance", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "두 access 사이에 접근된 ", "size": 14},
        {"text": "다른 KV들의 크기 합", "size": 14, "bold": True},
    ], space_after=8)
    add_rich_para(tf, [
        {"text": "측정치", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    for t in [
        ("access의 80%가 ", "perf 200 GB를 초과"),
        ("정책에 상관없이 ",   "hit ≈ 20%"),
        ("perf가 40%를 담아도 ", "hit은 절반 수준"),
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 17},
            {"text": t[1], "size": 17, "bold": True},
        ], space_after=4)
    add_rich_para(tf, [
        {"text": "→ 사용자가 답을 읽는 사이 ", "size": 16},
        {"text": "다른 KV가 끼어든다", "size": 16, "italic": True,
         "color": COLOR_LIGHT},
    ])
    add_footer(s, 10)


# ---- Slide 11: Obs 3 ------------------------------------------------------
def slide_11():
    s = add_slide()
    add_header_band(s, "Observation 3 — KV loading 시간 분산이 매우 큼",
                    kicker="MOTIVATION")
    # Two figures side-by-side across the top, body across the bottom
    add_image_fit(s, fig_path(7), Inches(0.5), Inches(1.4), Inches(6.2), Inches(2.7),
                  caption="Figure 7. 시간 구간별 KV loading time의 변동계수 CV")
    add_image_fit(s, fig_path(8), Inches(6.9), Inches(1.4), Inches(6.0), Inches(2.7),
                  caption="Figure 8. 로드된 KV 크기 분포 (히스토그램)")

    tf = add_textbox(s, Inches(0.5), Inches(4.7), Inches(12.3), Inches(2.4))
    add_rich_para(tf, [
        {"text": "왜 분산이 큰가", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tf, [
        {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
        {"text": "host DRAM과 SSD의 ", "size": 18},
        {"text": "bandwidth 격차", "size": 18, "bold": True},
        {"text": "  ·  요청마다 ", "size": 18},
        {"text": "KV size가 수십 MB ~ 수백 MB로 다양", "size": 18, "bold": True},
        {"text": "  ·  ", "size": 18},
        {"text": "5초 윈도우에서도 CV > 90%", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ], space_after=10)
    add_rich_para(tf, [
        {"text": "함의 — ", "size": 20, "bold": True, "color": COLOR_PRIMARY},
        {"text": "큰 KV 한 개가 ", "size": 20},
        {"text": "뒤따르는 작은 KV들까지 막아 GPU를 놀게 만든다", "size": 20,
         "bold": True, "color": COLOR_ACCENT},
    ])
    add_footer(s, 11)


# ---- Slide 12: Root cause -------------------------------------------------
def slide_12():
    s = add_slide()
    add_header_band(s, "Root cause — compute engine과 storage가 서로를 모름",
                    kicker="ROOT CAUSE")
    # Two columns of issue boxes
    box1 = add_rect(s, Inches(0.5), Inches(1.4), Inches(6.0), Inches(2.8),
                    fill=COLOR_BG_BAND, line=COLOR_RULE)
    tf1 = add_textbox(s, Inches(0.7), Inches(1.5), Inches(5.6), Inches(2.6))
    add_rich_para(tf1, [
        {"text": "문제 1. Compute engine이 storage I/O latency를 모른다",
         "size": 20, "bold": True, "color": COLOR_PRIMARY}], space_after=6)
    add_rich_para(tf1, [
        {"text": "▸ 어느 요청의 KV가 perf layer에 있고, 어느 것이 capacity layer에 있는지",
         "size": 18}], space_after=2)
    add_rich_para(tf1, [
        {"text": "▸ 어느 요청의 KV size가 크고 어느 것이 작은지",
         "size": 18}], space_after=2)
    add_rich_para(tf1, [
        {"text": "→ FCFS로 보내면 큰 I/O 하나가 큐 앞을 막아 GPU가 논다",
         "size": 18, "italic": True, "color": COLOR_ACCENT}])
    box2 = add_rect(s, Inches(6.8), Inches(1.4), Inches(6.0), Inches(2.8),
                    fill=COLOR_BG_BAND, line=COLOR_RULE)
    tf2 = add_textbox(s, Inches(7.0), Inches(1.5), Inches(5.6), Inches(2.6))
    add_rich_para(tf2, [
        {"text": "문제 2. Storage가 사용자 대화 패턴을 모른다",
         "size": 20, "bold": True, "color": COLOR_PRIMARY}], space_after=6)
    add_rich_para(tf2, [
        {"text": "▸ eviction이 storage 쪽 KV access history만 사용",
         "size": 18}], space_after=2)
    add_rich_para(tf2, [
        {"text": "▸ 사용자의 다음 질문 시점은 compute가 만든 답변 길이가 결정",
         "size": 18}], space_after=2)
    add_rich_para(tf2, [
        {"text": "→ 정보 부족으로 hit rate가 20% 수준에 머무름",
         "size": 18, "italic": True, "color": COLOR_ACCENT}])
    # Bottom take-away — bordered white box, no fill colour
    add_rect(s, Inches(0.5), Inches(4.5), Inches(12.3), Inches(2.4),
             fill=COLOR_WHITE, line=COLOR_RULE)
    tfb = add_textbox(s, Inches(0.7), Inches(4.6), Inches(12), Inches(2.2),
                      anchor="middle")
    add_rich_para(tfb, [
        {"text": "두 문제 모두 ", "size": 18, "color": COLOR_TEXT},
        {"text": "정보 교환이 한 방향에 그치거나 아예 끊겨 있다는 점에서 같다",
         "size": 18, "bold": True, "color": COLOR_PRIMARY},
    ], align="center", space_after=6)
    add_rich_para(tfb, [
        {"text": "Bidaw의 가설: ", "size": 15, "color": COLOR_LIGHT},
        {"text": "양방향 정보 교환을 열어주면 두 문제가 함께 풀린다",
         "size": 15, "bold": True, "color": COLOR_PRIMARY},
    ], align="center")
    add_footer(s, 12)


# ---- Slide 13: Key idea ---------------------------------------------------
def slide_13():
    s = add_slide()
    add_header_band(s, "핵심 아이디어 — Bidirectional awareness",
                    kicker="KEY IDEA")
    # Left half: down arrow info — box height matched to actual content
    add_rect(s, Inches(0.5), Inches(1.55), Inches(6.0), Inches(3.8),
             fill=COLOR_BG_BAND)
    tf1 = add_textbox(s, Inches(0.7), Inches(1.7), Inches(5.6), Inches(3.5))
    add_rich_para(tf1, [
        {"text": "Compute → Storage", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=4)
    add_rich_para(tf1, [
        {"text": "이전 라운드의 ", "size": 18},
        {"text": "답변 길이", "size": 18, "bold": True, "color": COLOR_ACCENT},
        {"text": "를 storage에 전달", "size": 18},
    ], space_after=8)
    for t in [
        "이 길이가 다음 질문 도착 시점을 가늠하는 신호",
        "storage는 이 신호로 다음 access의 reuse distance를 추정",
        "hit potential이 가장 낮은 KV를 evict",
    ]:
        add_rich_para(tf1, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    # Right half: up arrow info
    add_rect(s, Inches(6.8), Inches(1.55), Inches(6.0), Inches(3.8),
             fill=COLOR_BG_BAND)
    tf2 = add_textbox(s, Inches(7.0), Inches(1.7), Inches(5.6), Inches(3.5))
    add_rich_para(tf2, [
        {"text": "Storage → Compute", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=4)
    add_rich_para(tf2, [
        {"text": "각 요청 KV의 ", "size": 18},
        {"text": "위치(layer)와 크기", "size": 18, "bold": True, "color": COLOR_ACCENT},
        {"text": "를 compute에 전달", "size": 18},
    ], space_after=8)
    for t in [
        "compute가 KV의 위치와 크기를 알고 dispatch",
        "ready / preparing 두 큐로 I/O 길이를 분리",
        "GPU 유휴 시간 제거 + 큐잉 지연 감소",
    ]:
        add_rich_para(tf2, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_footer(s, 13)


# ---- Slide 14: System overview --------------------------------------------
def slide_14():
    s = add_slide()
    add_header_band(s, "시스템 구성 — 3개 컴포넌트와 양방향 신호",
                    kicker="DESIGN")
    add_image_fit(s, fig_path(9), Inches(0.5), Inches(1.3), Inches(6.3), Inches(5.5),
                  caption="Figure 9. Bidaw 시스템 구조")
    tf = add_textbox(s, Inches(7.1), Inches(1.3), Inches(6.0), Inches(5.6))
    add_rich_para(tf, [
        {"text": "①  Scheduler  (§3.2)", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=2)
    add_rich_para(tf, [
        {"text": "storage에서 KV 위치와 크기를 받아 ready/preparing 큐로 분리",
         "size": 18, "color": COLOR_LIGHT}], space_after=8)
    add_rich_para(tf, [
        {"text": "②  History Cacher  (§4)", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=2)
    add_rich_para(tf, [
        {"text": "GPU에서 만들어진 history tensor 중 storage-efficient tensor만 캐싱",
         "size": 18, "color": COLOR_LIGHT}], space_after=8)
    add_rich_para(tf, [
        {"text": "③  Eviction Manager  (§3.3)", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=2)
    add_rich_para(tf, [
        {"text": "compute가 보낸 답변 길이로 reuse distance를 추정하고 hit potential이 가장 낮은 KV를 evict",
         "size": 18, "color": COLOR_LIGHT}], space_after=8)
    add_rich_para(tf, [
        {"text": "Bidirectional 신호", "size": 20, "bold": True, "color": COLOR_ACCENT}
    ], space_after=2)
    add_rich_para(tf, [
        {"text": "▸ Storage → Compute: KV의 위치와 크기", "size": 18}], space_after=2)
    add_rich_para(tf, [
        {"text": "▸ Compute → Storage: 다음 access 시점(= 답변 길이)",
         "size": 18}])
    add_footer(s, 14)


# ---- Slide 15: Workflow ---------------------------------------------------
def slide_15():
    s = add_slide()
    add_header_band(s, "End-to-end workflow", kicker="DESIGN")
    steps = [
        ("①", "사용자 요청이 도착하면 Scheduler가 KV의 위치와 크기를 storage에서 조회",
              "→ Ready queue 또는 Preparing queue로 보냄"),
        ("②", "GPU가 inference 중에 만든 storage-efficient tensor를 History Cacher가 보관",
              "→ KV tensor 대신 더 작은 intermediate tensor를 저장 (MHA에 한함)"),
        ("③", "GPU 응답이 끝나면 답변 토큰 길이를 Eviction Manager에 전달",
              "→ 다음 KV access의 reuse distance 분포를 추정"),
        ("④", "perf layer 여유 공간이 임계치 아래로 떨어지면 eviction 트리거",
              "→ hit potential이 가장 낮은 KV를 capacity layer로 이동 (inclusive caching)"),
    ]
    top0 = Inches(1.4)
    row_h = Inches(1.3)
    for i, (n, head, sub) in enumerate(steps):
        y = top0 + row_h * i
        # Number as plain large grey character, no filled block
        ntb = add_textbox(s, Inches(0.5), y, Inches(0.8), Inches(1.1), anchor="middle")
        add_rich_para(ntb, [
            {"text": n, "size": 32, "bold": True, "color": COLOR_LIGHT}],
            align="center")
        tf = add_textbox(s, Inches(1.4), y + Inches(0.05), Inches(11.5), Inches(1.1))
        add_rich_para(tf, [
            {"text": head, "size": 15, "bold": True, "color": COLOR_PRIMARY}], space_after=4)
        add_rich_para(tf, [
            {"text": sub, "size": 18, "color": COLOR_LIGHT}])
    add_footer(s, 15)


# ---- Slide 16: I/O blocking 문제 ------------------------------------------
def slide_16():
    s = add_slide()
    add_header_band(s, "Mechanism 1의 동기 — I/O blocking과 overlap의 한계",
                    kicker="MECHANISM 1 / 3")
    add_image_fit(s, fig_path(10), Inches(0.5), Inches(1.3), Inches(7.3), Inches(2.6),
                  caption="Figure 10. I/O-aware request scheduling 전략 개요")
    tf = add_textbox(s, Inches(8.1), Inches(1.3), Inches(5.0), Inches(5.6))
    add_rich_para(tf, [
        {"text": "왜 단순한 overlap으로는 부족한가", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    for t in [
        "GPU compute 한 iteration = 수십 ms",
        "capacity layer I/O = 수백 ms",
        "다음 layer KV load와 겹쳐도 시간 차가 너무 큼",
        "naive overlap만으로는 GPU가 다음 토큰을 기다리며 다시 논다",
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    # Bottom: design goal box
    add_rect(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.6), fill=COLOR_BG_BAND)
    tfg = add_textbox(s, Inches(0.7), Inches(5.5), Inches(12), Inches(1.4),
                      anchor="middle")
    add_rich_para(tfg, [
        {"text": "설계 목표 — ", "size": 20, "bold": True},
        {"text": "느린 I/O가 빠른 I/O를 막지 않으면서, ",
         "size": 20},
        {"text": "큰 KV 요청도 starvation 없이 처리한다", "size": 20, "bold": True,
         "color": COLOR_ACCENT},
    ], align="center")
    add_footer(s, 16)


# ---- Slide 17: Dual queue + disk-HRRN -------------------------------------
def slide_17():
    s = add_slide()
    add_header_band(s, "I/O-aware scheduling — Dual queue + disk-HRRN",
                    kicker="MECHANISM 1 / 3")
    # Two columns — slim height
    add_rect(s, Inches(0.5), Inches(1.4), Inches(6.2), Inches(4.0),
             fill=COLOR_BG_BAND)
    tfL = add_textbox(s, Inches(0.7), Inches(1.55), Inches(5.8), Inches(3.7))
    add_rich_para(tfL, [
        {"text": "Dual queue", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tfL, [
        {"text": "Ready queue", "size": 18, "bold": True}], space_after=2)
    add_rich_para(tfL, [
        {"text": "KV가 perf layer에 있는 요청 — FCFS로 GPU에 바로 보냄",
         "size": 18, "color": COLOR_LIGHT}], space_after=6)
    add_rich_para(tfL, [
        {"text": "Preparing queue", "size": 18, "bold": True}], space_after=2)
    add_rich_para(tfL, [
        {"text": "KV가 capacity layer에 있는 요청 — 백그라운드로 perf layer에 올림",
         "size": 18, "color": COLOR_LIGHT}], space_after=10)
    add_rich_para(tfL, [
        {"text": "promotion 후에도 ", "size": 18},
        {"text": "원래 도착 시각을 유지", "size": 18, "bold": True, "color": COLOR_ACCENT},
        {"text": "해 tail latency 급증을 막음", "size": 18}])

    add_rect(s, Inches(6.9), Inches(1.4), Inches(5.9), Inches(4.0),
             fill=COLOR_BG_BAND)
    tfR = add_textbox(s, Inches(7.1), Inches(1.55), Inches(5.5), Inches(3.7))
    add_rich_para(tfR, [
        {"text": "disk-HRRN (preparing queue 정렬)", "size": 20, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    add_rich_para(tfR, [
        {"text": "Response ratio = 1 + (Request waiting time) / (KV size)",
         "size": 20, "mono": True}], space_after=10)
    for t in [
        ("작은 KV 먼저 ",        "→ ready queue로 빠르게 promote"),
        ("대기 시간이 길어지면 ", "큰 KV도 promote (starvation 방지)"),
        ("classical HRRN을 ",  "I/O time ≈ KV size에 맞춰 변형"),
    ]:
        add_rich_para(tfR, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18},
            {"text": t[1], "size": 18, "bold": True},
        ], space_after=4)
    add_footer(s, 17)


# ---- Slide 18: Schedule example -------------------------------------------
def slide_18():
    s = add_slide()
    add_header_band(s, "동작 예 — GPU 유휴 시간을 어떻게 없애는가",
                    kicker="MECHANISM 1 / 3")
    add_image_fit(s, fig_path(11), Inches(0.5), Inches(1.3), Inches(8.0), Inches(5.0),
                  caption="Figure 11. (a) FCFS vs (b) I/O-aware scheduling의 timeline 비교")
    tf = add_textbox(s, Inches(8.8), Inches(1.4), Inches(4.3), Inches(5.5))
    add_rich_para(tf, [
        {"text": "(a) FCFS", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "큐 앞쪽의 req 1, 2(큰 capacity-layer KV)가 막아서",
         "size": 18}], space_after=2)
    add_rich_para(tf, [
        {"text": "GPU와 perf-layer I/O가 모두 논다", "size": 18, "italic": True,
         "color": COLOR_ACCENT}], space_after=10)
    add_rich_para(tf, [
        {"text": "(b) I/O-aware", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "req 3, 4, 5(perf-layer hit)가 먼저 GPU로 가고, 그 사이 req 2가 promote",
         "size": 18}], space_after=4)
    add_rich_para(tf, [
        {"text": "평균 큐잉 시간 ", "size": 18},
        {"text": "5.76s → 2.45s (-57.5%)", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ])
    add_footer(s, 18)


# ---- Slide 19: Reuse distance correlation ---------------------------------
def slide_19():
    s = add_slide()
    add_header_band(s, "Mechanism 2의 핵심 관찰 — 답변 길이와 다음 reuse distance",
                    kicker="MECHANISM 2 / 3")
    add_image_fit(s, fig_path(12), Inches(0.5), Inches(1.3), Inches(12.3), Inches(3.6),
                  caption="Figure 12. 시간대별 답변 길이(가로축) vs 다음 KV access의 reuse distance(세로축). 빨간 선 = 하한")
    tf = add_textbox(s, Inches(0.5), Inches(5.2), Inches(12.3), Inches(1.8))
    add_rich_para(tf, [
        {"text": "정의 — Weighted reuse distance", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=2)
    add_rich_para(tf, [
        {"text": "현재 access와 다음 access 사이에 접근되는 다른 KV의 ",
         "size": 18},
        {"text": "byte 합", "size": 18, "bold": True},
    ], space_after=8)
    add_rich_para(tf, [
        {"text": "관찰 — 답변이 길수록 사용자가 다음 질문을 늦게 보내고, 그 사이 다른 사용자의 KV가 끼어들면서 reuse distance 하한이 ",
         "size": 18},
        {"text": "꾸준히 증가 (Spearman ρ = 0.94 ~ 0.98)", "size": 18, "bold": True,
         "color": COLOR_ACCENT},
    ])
    add_footer(s, 19)


# ---- Slide 20: hit potential w/ large reuse distance ----------------------
def slide_20():
    s = add_slide()
    add_header_band(s, "reuse distance가 크다고 곧 미스인 것은 아니다",
                    kicker="MECHANISM 2 / 3")
    add_image_fit(s, fig_path(13), Inches(0.5), Inches(1.3), Inches(7.5), Inches(3.4),
                  caption="Figure 13. Reuse distance 구간별 hit rate (Optimal vs FIFO/LRU/Q-enh)")
    tf = add_textbox(s, Inches(8.3), Inches(1.4), Inches(4.8), Inches(5.5))
    add_rich_para(tf, [
        {"text": "세 영역으로 나눔", "size": 20, "bold": True, "color": COLOR_PRIMARY}],
        space_after=4)
    add_rich_para(tf, [
        {"text": "Small  (< perf layer size)", "size": 18, "bold": True}], space_after=2)
    add_rich_para(tf, [
        {"text": "어떤 정책이든 hit ≈ 1.0", "size": 18, "color": COLOR_LIGHT}],
        space_after=8)
    add_rich_para(tf, [
        {"text": "Promising  (중간 영역)", "size": 18, "bold": True, "color": COLOR_ACCENT}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "Optimal(Belady)은 100%에 가깝지만 LRU는 0~40% 수준",
         "size": 18, "color": COLOR_LIGHT}], space_after=8)
    add_rich_para(tf, [
        {"text": "Extreme  (440 GB+)", "size": 18, "bold": True}], space_after=2)
    add_rich_para(tf, [
        {"text": "Optimal도 hit ≈ 0 — eviction 1순위", "size": 18,
         "color": COLOR_LIGHT}])
    add_rect(s, Inches(0.5), Inches(5.0), Inches(7.8), Inches(2.0),
             fill=COLOR_BG_BAND)
    tfb = add_textbox(s, Inches(0.7), Inches(5.1), Inches(7.4), Inches(1.8),
                      anchor="middle")
    add_rich_para(tfb, [
        {"text": "교훈 — distance만 보고 evict하면 promising 구간을 놓친다.\n",
         "size": 18},
        {"text": "Optimal과의 격차를 좁히려면 ", "size": 18},
        {"text": "구간별 hit 확률을 모델링", "size": 18, "bold": True, "color": COLOR_ACCENT},
        {"text": "해야 한다.", "size": 18},
    ])
    add_footer(s, 20)


# ---- Slide 21: Ghost cache + bucketing ------------------------------------
def slide_21():
    s = add_slide()
    add_header_band(s, "Eviction 알고리즘 — Ghost cache + bucket",
                    kicker="MECHANISM 2 / 3")
    # Step list
    steps = [
        ("①", "Promising 영역을 m개의 fine-grained bucket으로 나눔"),
        ("②", "각 bucket의 hit rate를 ghost cache 위에서 Belady 시뮬레이션으로 측정"),
        ("③", "사용자별 과거 KV access 분포로, 다음 access가 각 bucket에 떨어질 확률을 추정"),
        ("④", "compute가 보낸 답변 길이로 reuse distance 하한을 정해 더 작은 bucket의 확률을 0으로 truncate"),
        ("⑤", "Equation 2로 overall hit potential을 계산해 가장 낮은 KV를 evict"),
    ]
    # Stretch the 5 steps over the slide height so it doesn't bottom-load
    top0 = Inches(1.6)
    row_h = Inches(1.05)
    for i, (n, t) in enumerate(steps):
        y = top0 + row_h * i
        ntb = add_textbox(s, Inches(0.5), y, Inches(0.9), Inches(0.9), anchor="middle")
        add_rich_para(ntb, [
            {"text": n, "size": 28, "bold": True, "color": COLOR_LIGHT}],
            align="center")
        tf = add_textbox(s, Inches(1.5), y + Inches(0.05), Inches(11.4), Inches(0.9),
                         anchor="middle")
        add_rich_para(tf, [{"text": t, "size": 19, "color": COLOR_TEXT}])
    add_footer(s, 21)


# ---- Slide 22: Equation 2 -------------------------------------------------
def slide_22():
    s = add_slide()
    add_header_band(s, "Eviction 결정식 — Overall hit potential",
                    kicker="MECHANISM 2 / 3")
    # Equation box
    add_rect(s, Inches(0.5), Inches(1.5), Inches(12.3), Inches(1.6),
             fill=COLOR_BG_BAND)
    tf_eq = add_textbox(s, Inches(0.7), Inches(1.6), Inches(12), Inches(1.4),
                        anchor="middle")
    add_rich_para(tf_eq, [
        {"text": "Overall_potential = prob_small · 1.0  +  prob_extreme · 0.0  +  Σᵢ prob_promising(i) · hit_promising(i)",
         "size": 20, "mono": True, "bold": True},
    ], align="center", space_after=4)
    add_rich_para(tf_eq, [
        {"text": "Equation (2). hit potential이 가장 낮은 KV를 evict",
         "size": 14, "italic": True, "color": COLOR_LIGHT}], align="center")
    # Decomposition
    items = [
        ("prob_small",        "다음 access가 perf layer 안에 들어올 확률 — hit 확률 1.0"),
        ("prob_promising(i)", "promising bucket i에 떨어질 확률 (총 m개 bucket)"),
        ("hit_promising(i)",  "ghost cache의 Belady 시뮬레이션이 알려주는 bucket i의 hit rate"),
        ("prob_extreme",      "perf layer로 다시 돌아오지 않음 — hit 확률 0"),
    ]
    top0 = Inches(3.5)
    row_h = Inches(0.7)
    for i, (term, desc) in enumerate(items):
        y = top0 + row_h * i
        tf = add_textbox(s, Inches(0.7), y, Inches(12), Inches(0.6))
        add_rich_para(tf, [
            {"text": "▸  ", "size": 18, "bold": True, "color": COLOR_ACCENT},
            {"text": term, "size": 18, "bold": True, "mono": True, "color": COLOR_PRIMARY},
            {"text": "    ", "size": 18},
            {"text": desc, "size": 18},
        ])
    # Note about ghost cache
    add_rect(s, Inches(0.5), Inches(6.4), Inches(12.3), Inches(0.7),
             fill=COLOR_BG_BAND)
    tfn = add_textbox(s, Inches(0.7), Inches(6.45), Inches(12), Inches(0.6),
                      anchor="middle")
    add_rich_para(tfn, [
        {"text": "Note. Ghost cache는 백그라운드에서 Belady 시뮬레이션을 수행 — eviction 결정 단계의 추가 비용은 ",
         "size": 14},
        {"text": "0.35 ms", "size": 14, "bold": True, "color": COLOR_ACCENT},
        {"text": "에 그침 (자세한 비교는 평가 슬라이드에서)", "size": 14},
    ])
    add_footer(s, 22)


# ---- Slide 23: Tensor cost efficiency -------------------------------------
def slide_23():
    s = add_slide()
    add_header_band(s, "Mechanism 3 — 어떤 tensor를 캐싱할 것인가",
                    kicker="MECHANISM 3 / 3")
    add_image_fit(s, fig_path(14), Inches(0.5), Inches(1.3), Inches(7.5), Inches(4.5),
                  caption="Figure 14. (a) tensor별 size와 절약 가능한 GFLOPs, (b) cost efficiency")
    tf = add_textbox(s, Inches(8.3), Inches(1.4), Inches(4.8), Inches(5.5))
    add_rich_para(tf, [
        {"text": "왜 KV tensor가 최선이 아닌가", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    add_rich_para(tf, [
        {"text": "▸ KV tensor가 직접 필요하지만 ", "size": 18},
        {"text": "size가 크다", "size": 18, "bold": True},
    ], space_after=6)
    add_rich_para(tf, [
        {"text": "Cost Efficiency", "size": 18, "bold": True, "color": COLOR_PRIMARY}],
        space_after=2)
    add_rich_para(tf, [
        {"text": "= Saved compute / Required space  (GFLOPs/MB)",
         "size": 18, "mono": True}], space_after=8)
    add_rich_para(tf, [
        {"text": "Tensor 6 (정규화된 activation)", "size": 18, "bold": True,
         "color": COLOR_ACCENT}], space_after=2)
    add_rich_para(tf, [
        {"text": "▸ 51 GFLOPs/MB — KV tensor(30.5)의 1.67배",
         "size": 18}], space_after=2)
    add_rich_para(tf, [
        {"text": "▸ KV tensor로 변환하는 데 ", "size": 18},
        {"text": "GPU 1 step", "size": 18, "bold": True},
        {"text": "이면 충분", "size": 18},
    ])
    add_footer(s, 23)


# ---- Slide 24: MHA vs GQA -------------------------------------------------
def slide_24():
    s = add_slide()
    add_header_band(s, "Storage-efficient tensor caching — 적용 범위",
                    kicker="MECHANISM 3 / 3")
    # Two columns — slim
    add_rect(s, Inches(0.5), Inches(1.4), Inches(6.2), Inches(3.4),
             fill=COLOR_BG_BAND)
    tfL = add_textbox(s, Inches(0.7), Inches(1.55), Inches(5.8), Inches(3.1))
    add_rich_para(tfL, [
        {"text": "MHA 기반 모델", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=4)
    for t in [
        "Llama · Qwen · Bloom · OPT · Baichuan",
        "head마다 K, V가 분리 → KV가 큼",
        "tensor 6 캐싱이 적은 공간으로 많은 compute를 절약",
    ]:
        add_rich_para(tfL, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_rich_para(tfL, [
        {"text": "→ Bidaw는 ", "size": 18},
        {"text": "tensor 6를 캐싱", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ])

    add_rect(s, Inches(6.9), Inches(1.4), Inches(5.9), Inches(3.4),
             fill=COLOR_BG_BAND)
    tfR = add_textbox(s, Inches(7.1), Inches(1.55), Inches(5.5), Inches(3.1))
    add_rich_para(tfR, [
        {"text": "GQA 기반 모델", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=4)
    for t in [
        "여러 query head가 K, V를 공유 → KV tensor 자체가 작음",
        "tensor 6의 cost-efficiency 이점이 사라짐",
    ]:
        add_rich_para(tfR, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=4)
    add_rich_para(tfR, [
        {"text": "→ GQA에서는 ", "size": 18},
        {"text": "KV tensor를 그대로 캐싱", "size": 18, "bold": True, "color": COLOR_ACCENT},
    ])
    add_footer(s, 24)


# ---- Slide 25: Implementation notes ---------------------------------------
def slide_25():
    s = add_slide()
    add_header_band(s, "구현 노트 — vLLM 위에 얹는 네 가지 기법",
                    kicker="IMPLEMENTATION")
    items = [
        ("Continuous batching",
         "일찍 끝난 요청을 배치에서 바로 빼고 새 요청을 곧장 받아들임 (ORCA 계열과 호환)"),
        ("Mix-grained PagedAttention",
         "history/query 토큰은 256토큰의 큰 블록, response 토큰은 16토큰의 작은 블록으로 관리 → CPU-GPU 대역폭 활용도 향상, 단편화 감소"),
        ("Low-priority CUDA stream",
         "storage-efficient tensor를 KV tensor로 바꾸는 작업을 별도 스트림에서 실행 → 유휴 SM을 활용하고 실제 추론 latency에 영향 없음"),
        ("Inclusive caching",
         "eviction 시점에 capacity layer에 이미 사본이 있어 추가 write 트래픽이 거의 없음 (FlashGen 계열과 동일)"),
    ]
    top0 = Inches(1.3)
    row_h = Inches(1.4)
    for i, (head, body) in enumerate(items):
        y = top0 + row_h * i
        add_rect(s, Inches(0.5), y, Inches(0.18), Inches(1.1), fill=COLOR_ACCENT)
        tf = add_textbox(s, Inches(0.9), y + Inches(0.05), Inches(11.8), Inches(1.1))
        add_rich_para(tf, [
            {"text": head, "size": 20, "bold": True, "color": COLOR_PRIMARY}],
            space_after=4)
        add_rich_para(tf, [{"text": body, "size": 18}])
    add_footer(s, 25)


# ---- Slide 26: Eval setup -------------------------------------------------
def slide_26():
    s = add_slide()
    add_header_band(s, "실험 환경 및 비교 대상", kicker="EVALUATION")
    # Two columns
    add_rect(s, Inches(0.5), Inches(1.3), Inches(6.2), Inches(5.6),
             fill=COLOR_BG_BAND)
    tfL = add_textbox(s, Inches(0.7), Inches(1.4), Inches(5.8), Inches(5.4))
    add_rich_para(tfL, [
        {"text": "Hardware / Software", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=6)
    for t in [
        ("GPU",        "NVIDIA A800 80GB"),
        ("Host mem",   "200 GB (perf layer)"),
        ("Storage",    "SATA SSD 4장 RAID-5, 1.5 GB/s"),
        ("PCIe",       "Gen 4 (~30 GB/s)"),
        ("Models",     "OPT-6.7B/13B/30B, Qwen-7B/14B"),
        ("Workloads",  "자체 100만 라운드 trace, ShareGPT (Poisson 시뮬)"),
    ]:
        add_rich_para(tfL, [
            {"text": t[0] + ":  ", "size": 18, "bold": True, "color": COLOR_PRIMARY},
            {"text": t[1], "size": 18}], space_after=4)

    add_rect(s, Inches(6.9), Inches(1.3), Inches(5.9), Inches(5.6),
             fill=COLOR_BG_BAND)
    tfR = add_textbox(s, Inches(7.1), Inches(1.4), Inches(5.5), Inches(5.4))
    add_rich_para(tfR, [
        {"text": "Baselines", "size": 20, "bold": True, "color": COLOR_PRIMARY}
    ], space_after=6)
    for t in [
        ("vLLM",            "Recompute (KV caching 없음)"),
        ("CachedAttention", "Queue-enhanced LRU + 2-tier"),
        ("FlashGen",        "Inclusive caching + GPU-fit scheduling"),
        ("Optimal",         "모든 KV가 perf layer에 있는 상한선"),
        ("Bidaw",           "이 논문"),
    ]:
        add_rich_para(tfR, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18, "bold": True},
            {"text": "  " + t[1], "size": 14, "color": COLOR_LIGHT}], space_after=4)
    add_footer(s, 26)


# ---- Slide 27: Overall performance ----------------------------------------
def slide_27():
    s = add_slide()
    add_header_band(s, "Overall performance — 모델 5종 동시 평가",
                    kicker="EVALUATION")
    add_image_fit(s, fig_path(15), Inches(0.3), Inches(1.3), Inches(12.7), Inches(3.7),
                  caption="Figure 15. 사용자 도착률 vs 평균 응답 latency, 모델 5종")
    tf = add_textbox(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.7))
    for t in [
        ("Bidaw — 응답 latency ", "최대 3.58배 감소 (vs CachedAttention/FlashGen)"),
        ("Bidaw — throughput ", "1.43~1.83배 향상 (동일 latency 기준)"),
        ("Optimal과의 격차 ",   "거의 없음 — perf-layer-only 수준에 근접"),
        ("Note ",              "Bidaw는 lossless — 답변 정확도는 FlashGen 등과 같음"),
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18, "bold": True},
            {"text": t[1], "size": 18}], space_after=4)
    add_footer(s, 27)


# ---- Slide 28: Memory sensitivity + miss rate -----------------------------
def slide_28():
    s = add_slide()
    add_header_band(s, "Memory sensitivity & Eviction miss rate",
                    kicker="EVALUATION")
    add_image_fit(s, fig_path(16), Inches(0.3), Inches(1.3), Inches(7.0), Inches(2.7),
                  caption="Figure 16. host memory 120~200GB 범위에서의 latency")
    add_image_fit(s, fig_path(18), Inches(7.6), Inches(1.3), Inches(5.5), Inches(2.7),
                  caption="Figure 18. (a) memory size · (b) workload pressure")
    tf = add_textbox(s, Inches(0.5), Inches(4.4), Inches(12.3), Inches(2.7))
    add_rich_para(tf, [
        {"text": "Memory sensitivity (Fig. 16)", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    for t in [
        "host memory를 120GB까지 줄여도 Bidaw는 baseline 200GB 수준의 latency",
        "동일 메모리에서 1.75~2.19배 더 많은 사용자/분 처리 — 메모리가 작을수록 격차가 더 벌어짐",
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t, "size": 18}], space_after=2)
    add_rich_para(tf, [
        {"text": "Eviction miss rate (Fig. 18)", "size": 18, "bold": True,
         "color": COLOR_PRIMARY}], space_after=4)
    for t in [
        ("queue-enhanced (CachedAttention)",  "보다 miss rate -57.6%"),
        ("LFU/LRU/FIFO 같은 일반 정책",       "보다 miss rate -69.9%"),
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18},
            {"text": "  " + t[1], "size": 18, "bold": True},
        ], space_after=2)
    add_footer(s, 28)


# ---- Slide 29: Tail latency, ablation, overhead ---------------------------
def slide_29():
    s = add_slide()
    add_header_band(s, "Tail latency · Ablation · Overhead",
                    kicker="EVALUATION")
    add_image_fit(s, fig_path(22), Inches(0.3), Inches(1.3), Inches(6.5), Inches(3.0),
                  caption="Figure 22. Tail latency P90 / P95 / P99 (OPT-30B)")
    add_image_fit(s, fig_path(21), Inches(7.0), Inches(1.3), Inches(3.0), Inches(3.0),
                  caption="Figure 21. Ablation")
    add_image_fit(s, fig_path(20), Inches(10.2), Inches(1.3), Inches(2.9), Inches(3.0),
                  caption="Figure 20. Overhead")
    tf = add_textbox(s, Inches(0.5), Inches(4.6), Inches(12.3), Inches(2.5))
    for t in [
        ("Tail latency", "CachedAttention 대비 P90 −52.96% / P95 −49.30% / P99 −47.03%"),
        ("Ablation",     "Scheduling +1.58배, Eviction +1.25배, Tensor caching +1.10배"),
        ("Overhead",     "Scheduling 0.62 ms, Eviction 0.35 ms, KV transform <0.1 s"),
    ]:
        add_rich_para(tf, [
            {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
            {"text": t[0], "size": 18, "bold": True, "color": COLOR_PRIMARY},
            {"text": "    " + t[1], "size": 18}], space_after=6)
    add_footer(s, 29)


# ---- Slide 30: Conclusion -------------------------------------------------
def slide_30():
    s = add_slide()
    add_header_band(s, "정리 · 한계 · 시사점", kicker="CONCLUSION")
    # Three boxes
    boxes = [
        ("기여",
         [
             "compute와 storage 사이 양방향 정보 공유라는 설계 원칙을 제시",
             "I/O-aware scheduling과 previous-answer-based eviction 두 메커니즘",
             "MHA에서 storage-efficient tensor 캐싱으로 공간과 연산을 함께 절약",
             "모델 5종 평균 latency 3.58배, throughput 1.83배 — Optimal에 근접",
         ]),
        ("한계",
         [
             "한 사용자 대화 내부의 KV 재사용만 다룸 — 사용자 간 공유는 범위 밖",
             "GQA에서는 storage-efficient tensor의 이점이 사라짐",
             "ShareGPT처럼 timestamp가 없는 trace에서는 eviction 효과가 약해짐",
             "단일 GPU 노드 평가 — disaggregated · 멀티노드는 future work",
         ]),
        ("논의",
         [
             "대화 시스템에서 사용자가 글을 읽는 속도가 storage 정책의 유용한 신호가 된다",
             "HRRN, Belady ghost cache 같은 고전 기법이 LLM 워크로드에서 다시 유효함을 보임",
             "ML serving과 storage의 co-design 사례 — 후속 연구가 활발해질 분야",
         ]),
    ]
    box_w = Inches(4.05)
    box_left = [Inches(0.5), Inches(4.65), Inches(8.8)]
    for i, (title, items) in enumerate(boxes):
        L = box_left[i]
        add_rect(s, L, Inches(1.3), box_w, Inches(5.6), fill=COLOR_BG_BAND)
        tf = add_textbox(s, L + Inches(0.2), Inches(1.4), box_w - Inches(0.4), Inches(5.4))
        add_rich_para(tf, [
            {"text": title, "size": 18, "bold": True, "color": COLOR_PRIMARY}
        ], space_after=8)
        for it in items:
            add_rich_para(tf, [
                {"text": "▸ ", "size": 18, "color": COLOR_ACCENT, "bold": True},
                {"text": it, "size": 14}], space_after=6)
    add_footer(s, 30)


# Build
for fn in [
    slide_01, slide_02, slide_03, slide_04, slide_05,
    slide_06, slide_07, slide_08, slide_09, slide_10,
    slide_11, slide_12, slide_13, slide_14, slide_15,
    slide_16, slide_17, slide_18, slide_19, slide_20,
    slide_21, slide_22, slide_23, slide_24, slide_25,
    slide_26, slide_27, slide_28, slide_29, slide_30,
]:
    fn()

prs.save(OUT_PATH)
print(f"Saved: {OUT_PATH}  (slides: {len(prs.slides)})")
