"""재사용 슬라이드 레이아웃. 각 함수는 (prs, spec, resolve) 를 받아 슬라이드 1장을 만든다.

resolve(visual_id) -> {"image": Path, "video": Path | None}
"""
from lxml import etree
from PIL import Image
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from theme import (BG, BLUE, BODY_SIZE, CAPTION_SIZE, CARD, FONT, MARGIN, MUTED, RED, SLIDE_H, SLIDE_W, TITLE_SIZE,
                   WHITE, YELLOW)

CONTENT_TOP = Inches(1.45)
CAPTION_TOP = Inches(6.25)


# ───────────────────────── 기본 도우미 ─────────────────────────

def new_slide(prs, notes=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 빈 레이아웃
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = BG
    if notes:
        slide.notes_slide.notes_text_frame.text = notes.strip()
    return slide


def _set_font(run, size, color, bold=False, font=FONT, italic=False):
    f = run.font
    f.size, f.bold, f.name, f.italic = size, bold, font, italic
    f.color.rgb = color
    rpr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rpr, qn(tag))
        el.set("typeface", font)


def add_text(slide, x, y, w, h, text, size=BODY_SIZE, color=WHITE, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.15, font=FONT, italic=False):
    """text 는 str 또는 [(문자열, 색|None), ...] 의 줄 리스트. '\n' 으로 줄바꿈."""
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment, p.line_spacing = align, line_spacing
        _set_font(p.add_run(), size, color, bold, font, italic)
        p.runs[0].text = line
    return box


def add_rect(slide, x, y, w, h, color, radius=None, alpha=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE, x, y, w, h)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    shape.shadow.inherit = False
    if radius:
        shape.adjustments[0] = radius
    if alpha is not None:
        clr = shape.fill._xPr.find(qn("a:solidFill"))[0]
        etree.SubElement(clr, qn("a:alpha")).set("val", str(int(alpha * 100000)))
    return shape


def _round_picture(pic, adj=5000):
    pic.auto_shape_type = MSO_SHAPE.ROUNDED_RECTANGLE
    geom = pic._element.spPr.find(qn("a:prstGeom"))
    av = geom.find(qn("a:avLst"))
    if av is None:
        av = etree.SubElement(geom, qn("a:avLst"))
    av.clear()
    gd = etree.SubElement(av, qn("a:gd"))
    gd.set("name", "adj")
    gd.set("fmla", f"val {adj}")


def fit_box(img_path, x, y, w, h, crop_top=0.0):
    """이미지 비율을 지키며 (x,y,w,h) 상자 가운데에 맞춘 좌표."""
    iw, ih = Image.open(img_path).size
    ih = ih * (1 - crop_top)
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    return Emu(x + (w - pw) // 2), Emu(y + (h - ph) // 2), Emu(pw), Emu(ph)


def add_picture(slide, path, x, y, w, h, rounded=True, crop_top=0.0):
    bx, by, bw, bh = fit_box(path, x, y, w, h, crop_top)
    pic = slide.shapes.add_picture(str(path), bx, by, bw, bh)
    pic.crop_top = crop_top
    if rounded:
        _round_picture(pic)
    return pic


def add_video(slide, video, poster, x, y, w, h, duration_ms):
    bx, by, bw, bh = fit_box(poster, x, y, w, h)
    movie = slide.shapes.add_movie(str(video), bx, by, bw, bh, poster_frame_image=str(poster), mime_type="video/mp4")
    _autoplay(slide, movie.shape_id, duration_ms)
    return movie


def _autoplay(slide, spid, duration_ms):
    """add_movie 가 만든 '클릭 시 재생' 타이밍을 '슬라이드가 열리면 자동 재생'으로 교체."""
    P = "http://schemas.openxmlformats.org/presentationml/2006/main"
    xml = f"""
<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
 <p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
  <p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>
   <p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
    <p:par><p:cTn id="5" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" nodeType="afterEffect">
     <p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
      <p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr><p:cTn id="6" dur="{duration_ms}" fill="hold"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:cmd>
     </p:childTnLst></p:cTn></p:par>
   </p:childTnLst></p:cTn></p:par>
  </p:childTnLst></p:cTn></p:par>
 </p:childTnLst></p:cTn>
 <p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
 <p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
 <p:video><p:cMediaNode vol="80000"><p:cTn id="7" fill="hold" display="0"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst></p:cTn>
  <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cMediaNode></p:video>
</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>"""
    sld = slide._element
    old = sld.find(qn("p:timing"))
    if old is not None:
        sld.remove(old)
    new = etree.fromstring(xml)
    ext = sld.find(qn("p:extLst"))
    if ext is not None:
        ext.addprevious(new)
    else:
        sld.append(new)


def add_title(slide, text):
    add_rect(slide, MARGIN, Inches(0.55), Inches(0.12), Inches(0.62), YELLOW)
    add_text(slide, MARGIN + Inches(0.3), Inches(0.45), SLIDE_W - 2 * MARGIN, Inches(0.8), text,
             size=TITLE_SIZE, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def add_caption_bar(slide, text):
    w = SLIDE_W - 2 * MARGIN
    add_rect(slide, MARGIN, CAPTION_TOP, w, Inches(0.8), CARD, radius=0.18)
    add_text(slide, MARGIN + Inches(0.35), CAPTION_TOP, Inches(0.5), Inches(0.8), "💡",
             size=Pt(24), anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, MARGIN + Inches(0.95), CAPTION_TOP, w - Inches(1.2), Inches(0.8), text,
             size=CAPTION_SIZE, color=YELLOW, bold=True, anchor=MSO_ANCHOR.MIDDLE)


# ───────────────────────── 레이아웃 ─────────────────────────

def cover(prs, s, resolve):
    slide = new_slide(prs, s.get("notes"))
    img = resolve(s["visual"])["image"]
    slide.shapes.add_picture(str(img), 0, 0, SLIDE_W, SLIDE_H)
    # 왼쪽 → 오른쪽으로 옅어지는 남색 그라데이션 (제목 가독성)
    ov = add_rect(slide, 0, 0, Inches(8.5), SLIDE_H, BG)
    ov.fill._xPr.remove(ov.fill._xPr.find(qn("a:solidFill")))
    grad = etree.fromstring(
        '<a:gradFill xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" rotWithShape="1"><a:gsLst>'
        '<a:gs pos="0"><a:srgbClr val="13203B"><a:alpha val="92000"/></a:srgbClr></a:gs>'
        '<a:gs pos="55000"><a:srgbClr val="13203B"><a:alpha val="70000"/></a:srgbClr></a:gs>'
        '<a:gs pos="100000"><a:srgbClr val="13203B"><a:alpha val="0"/></a:srgbClr></a:gs>'
        '</a:gsLst><a:lin ang="0" scaled="0"/></a:gradFill>')
    ov.fill._xPr.find(qn("a:prstGeom")).addnext(grad)

    x = Inches(0.9)
    add_text(slide, x, Inches(2.0), Inches(7), Inches(0.5), s.get("meta", ""), size=Pt(18), color=MUTED)
    add_text(slide, x, Inches(2.6), Inches(7.5), Inches(1.3), s["title"], size=Pt(60), bold=True)
    add_rect(slide, x, Inches(4.05), Inches(1.2), Inches(0.08), YELLOW)
    add_text(slide, x, Inches(4.35), Inches(7), Inches(0.7), s.get("subtitle", ""), size=Pt(28), color=YELLOW)


def section(prs, s, resolve):
    slide = new_slide(prs, s.get("notes"))
    add_text(slide, Inches(1.2), Inches(2.1), Inches(6), Inches(1.2), s["number"], size=Pt(54), color=YELLOW, bold=True)
    add_text(slide, Inches(1.2), Inches(3.2), Inches(11), Inches(1.2), s["title"], size=Pt(54), bold=True)
    add_rect(slide, Inches(1.2), Inches(4.5), Inches(1.2), Inches(0.08), YELLOW)
    add_text(slide, Inches(1.2), Inches(4.8), Inches(11), Inches(0.6), s.get("subtitle", ""), size=Pt(22), color=MUTED)
    # 오른쪽 장식: 전자 점들
    for i, (cx, cy, r) in enumerate([(10.6, 1.6, 0.22), (11.5, 2.4, 0.14), (10.2, 5.6, 0.16), (11.9, 4.9, 0.26),
                                     (12.3, 1.2, 0.1), (9.6, 6.4, 0.1)]):
        add_rect(slide, Inches(cx - r * 2), Inches(cy - r * 2), Inches(r * 4), Inches(r * 4), BLUE, radius=0.5, alpha=0.15)
        add_rect(slide, Inches(cx - r), Inches(cy - r), Inches(r * 2), Inches(r * 2), BLUE, radius=0.5)


def figure_caption(prs, s, resolve):
    slide = new_slide(prs, s.get("notes"))
    add_title(slide, s["title"])
    img = resolve(s["visual"])["image"]
    add_picture(slide, img, MARGIN, CONTENT_TOP, Inches(8.0), Inches(4.55))
    bullets = s.get("bullets", [])
    if bullets:
        x, w = Inches(8.95), Inches(3.8)
        add_rect(slide, x, CONTENT_TOP, w, Inches(4.5), CARD, radius=0.06)
        y = CONTENT_TOP + Inches(0.4)
        for b in bullets:
            head, _, rest = b.partition("=")
            add_rect(slide, x + Inches(0.3), y + Inches(0.12), Inches(0.14), Inches(0.14), YELLOW, radius=0.5)
            add_text(slide, x + Inches(0.6), y, w - Inches(0.85), Inches(0.5), head.strip(), size=Pt(22), bold=True)
            add_text(slide, x + Inches(0.6), y + Inches(0.5), w - Inches(0.7), Inches(1.4), rest.strip(),
                     size=Pt(17), color=MUTED)
            y += Inches(2.0)
    add_caption_bar(slide, s["caption"])


def video_caption(prs, s, resolve):
    slide = new_slide(prs, s.get("notes"))
    add_title(slide, s["title"])
    v = resolve(s["visual"])
    add_video(slide, v["video"], v["image"], MARGIN, CONTENT_TOP, SLIDE_W - 2 * MARGIN, Inches(4.6), v["duration_ms"])
    add_caption_bar(slide, s["caption"])


def compare(prs, s, resolve):
    slide = new_slide(prs, s.get("notes"))
    add_title(slide, s["title"])
    gap = Inches(0.4)
    pw = (SLIDE_W - 2 * MARGIN - gap) // 2
    for i, side in enumerate((s["left"], s["right"])):
        x = MARGIN + i * (pw + gap)
        add_picture(slide, resolve(side["visual"])["image"], x, CONTENT_TOP, pw, Inches(3.3),
                    crop_top=side.get("crop_top", 0.0))
        add_text(slide, x, CONTENT_TOP + Inches(3.4), pw, Inches(0.45), side["label"], size=Pt(20),
                 color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    # 짝 맞추기 칩
    pairs = s["pairs"]
    cgap = Inches(0.3)
    cw = (SLIDE_W - 2 * MARGIN - cgap * (len(pairs) - 1)) // len(pairs)
    y = Inches(5.4)
    for i, (water, elec, desc) in enumerate(pairs):
        x = MARGIN + i * (cw + cgap)
        add_rect(slide, x, y, cw, Inches(1.5), CARD, radius=0.12)
        add_text(slide, x, y + Inches(0.22), cw, Inches(0.6), f"{water}  =  {elec}", size=Pt(26), bold=True,
                 color=YELLOW, align=PP_ALIGN.CENTER)
        add_text(slide, x, y + Inches(0.9), cw, Inches(0.45), desc, size=Pt(17), color=MUTED, align=PP_ALIGN.CENTER)


LAYOUTS = {f.__name__: f for f in (cover, section, figure_caption, video_caption, compare)}


def _visual(slide, v, x, y, w, h):
    """resolve 결과가 영상이면 자동재생 영상, 아니면 둥근 그림."""
    if v.get("video"):
        return add_video(slide, v["video"], v["image"], x, y, w, h, v["duration_ms"])
    return add_picture(slide, v["image"], x, y, w, h)


def _unit_card(slide, c, x, y, w, h):
    add_rect(slide, x, y, w, h, CARD, radius=0.06)
    # 물리 기호는 관례대로 세리프 이탤릭
    add_text(slide, x + Inches(0.25), y + Inches(0.15), Inches(1.3), Inches(1.3), c["symbol"], size=Pt(80),
             color=YELLOW, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, font="Cambria", italic=True)
    rx, rw = x + Inches(1.65), w - Inches(1.8)
    add_text(slide, rx, y + Inches(0.28), rw, Inches(0.5), c["name"], size=Pt(26), bold=True)
    add_text(slide, rx, y + Inches(0.8), rw, Inches(0.3), c.get("eng", ""), size=Pt(14), color=MUTED)
    add_text(slide, rx, y + Inches(1.08), rw, Inches(0.4), "단위 · " + c["unit"], size=Pt(18), color=BLUE, bold=True)
    add_rect(slide, x + Inches(0.3), y + Inches(1.6), w - Inches(0.6), Inches(0.02), MUTED, alpha=0.4)
    yy = y + Inches(1.8)
    for line in c.get("sub", []):
        add_text(slide, x + Inches(0.35), yy, w - Inches(0.6), Inches(0.4), line, size=Pt(17), color=MUTED)
        yy += Inches(0.42)
    if c.get("note"):
        add_rect(slide, x + Inches(0.3), y + Inches(2.75), Inches(0.06), h - Inches(3.0), YELLOW)
        add_text(slide, x + Inches(0.5), y + Inches(2.75), w - Inches(0.75), h - Inches(2.9), c["note"],
                 size=Pt(17), color=WHITE, line_spacing=1.25)


def _chips(slide, chips, resolve, y, h):
    gap = Inches(0.3)
    cw = (SLIDE_W - 2 * MARGIN - gap * (len(chips) - 1)) // len(chips)
    for i, ch in enumerate(chips):
        x = MARGIN + i * (cw + gap)
        add_rect(slide, x, y, cw, h, CARD, radius=0.14)
        pad = Inches(0.1)
        if ch.get("visual"):
            lw = int((h - 2 * pad) * 16 / 9)
            add_picture(slide, resolve(ch["visual"])["image"], x + pad, y + pad, lw, h - 2 * pad)
        else:
            lw = Inches(1.4)
            add_text(slide, x + pad, y, lw, h, ch["value"], size=Pt(24), bold=True,
                     color=RED if ch.get("warn") else YELLOW, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        tx = x + pad + lw + Inches(0.2)
        tw = cw - (tx - x) - Inches(0.1)
        add_text(slide, tx, y + Inches(0.2), tw, Inches(0.45), ch["title"], size=Pt(20), bold=True)
        add_text(slide, tx, y + Inches(0.64), tw, Inches(0.45), ch["desc"], size=Pt(14),
                 color=RED if ch.get("warn") else MUTED)


def concept(prs, s, resolve):
    """큰 그림/영상 + 기호·단위 카드 + 아래 칩 3개."""
    slide = new_slide(prs, s.get("notes"))
    add_title(slide, s["title"])
    vw = Inches(7.7)
    vh = int(vw * 9 / 16)
    _visual(slide, resolve(s["visual"]), MARGIN, CONTENT_TOP, vw, vh)
    cx = MARGIN + vw + Inches(0.3)
    _unit_card(slide, s["card"], cx, CONTENT_TOP, SLIDE_W - MARGIN - cx, vh)
    _chips(slide, s["chips"], resolve, CONTENT_TOP + vh + Inches(0.22), Inches(1.15))


def three_cards(prs, s, resolve):
    """세 가지 분류 카드 + 아래 눈금 막대."""
    slide = new_slide(prs, s.get("notes"))
    add_title(slide, s["title"])
    cards = s["cards"]
    gap = Inches(0.3)
    cw = (SLIDE_W - 2 * MARGIN - gap * (len(cards) - 1)) // len(cards)
    ch = Inches(4.55)
    for i, c in enumerate(cards):
        x = MARGIN + i * (cw + gap)
        add_rect(slide, x, CONTENT_TOP, cw, ch, CARD, radius=0.06)
        pad = Inches(0.15)
        iw = cw - 2 * pad
        ih = int(iw * 9 / 16)
        add_picture(slide, resolve(c["visual"])["image"], x + pad, CONTENT_TOP + pad, iw, ih)
        ty = CONTENT_TOP + pad + ih + Inches(0.15)
        add_text(slide, x + Inches(0.3), ty, cw - Inches(0.6), Inches(0.6), c["name"], size=Pt(30), bold=True)
        add_text(slide, x + Inches(0.3), ty + Inches(0.6), cw - Inches(0.6), Inches(0.35), c["eng"], size=Pt(14),
                 color=MUTED)
        add_text(slide, x + Inches(0.3), ty + Inches(1.0), cw - Inches(0.6), Inches(0.4), c["desc"], size=Pt(18),
                 color=YELLOW, bold=True)
        add_text(slide, x + Inches(0.3), ty + Inches(1.45), cw - Inches(0.6), Inches(0.6), c["ex"], size=Pt(15),
                 color=MUTED)
    # 눈금 막대: 잘 통함(노랑) → 안 통함(회색)
    by = CONTENT_TOP + ch + Inches(0.35)
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, MARGIN, by, SLIDE_W - 2 * MARGIN, Inches(0.16))
    bar.adjustments[0] = 0.5
    bar.line.fill.background()
    bar.fill.gradient()
    bar.fill.gradient_angle = 0
    stops = bar.fill.gradient_stops
    stops[0].color.rgb, stops[0].position = YELLOW, 0.0
    stops[1].color.rgb, stops[1].position = CARD, 1.0
    left, right = s["scale"]
    add_text(slide, MARGIN, by + Inches(0.25), Inches(6), Inches(0.4), "◀ " + left, size=Pt(16), color=YELLOW, bold=True)
    add_text(slide, SLIDE_W - MARGIN - Inches(6), by + Inches(0.25), Inches(6), Inches(0.4), right + " ▶", size=Pt(16),
             color=MUTED, bold=True, align=PP_ALIGN.RIGHT)


LAYOUTS.update(concept=concept, three_cards=three_cards)
