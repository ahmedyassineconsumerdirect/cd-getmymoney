"""Build the myReclaim executive PowerPoint from the CD-Presentation template.

Loads the corporate template, removes its sample slides, then programmatically
adds the executive pitch deck slides (intro, opportunity, state matrix,
Snowflake architecture, privacy-match reuse, sprint plan, ask).

Usage:
    python scripts/build_exec_deck.py
Output:
    deck/exec/myReclaim-Exec-Deck.pptx
"""
from pathlib import Path
from copy import deepcopy

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

# Brand palette
SC_BLUE = RGBColor(0x28, 0x63, 0xC5)
SC_BLUE_DARK = RGBColor(0x1F, 0x4F, 0x9E)
SC_ORANGE = RGBColor(0xFC, 0x4C, 0x0B)
SC_AMBER = RGBColor(0xFF, 0xB3, 0x52)
SC_INK = RGBColor(0x0F, 0x17, 0x2A)
SC_INK_BODY = RGBColor(0x33, 0x41, 0x55)
SC_INK_MUTED = RGBColor(0x64, 0x74, 0x8B)
SC_BG_SUBTLE = RGBColor(0xF8, 0xFA, 0xFC)
SC_BG_CARD = RGBColor(0xFF, 0xFF, 0xFF)
SC_BORDER = RGBColor(0xE2, 0xE8, 0xF0)
SC_RED = RGBColor(0xE1, 0x1D, 0x48)
SC_GREEN = RGBColor(0x05, 0x96, 0x69)


TEMPLATE = Path(__file__).resolve().parent.parent / "deck" / "exec" / "template_source.pptx"
OUT = Path(__file__).resolve().parent.parent / "deck" / "exec" / "myReclaim-Exec-Deck.pptx"


def remove_all_slides(prs):
    """Remove every slide from the presentation. Layouts/masters preserved.

    Three things must happen:
    1. Drop slide entries from <p:sldIdLst> in presentation.xml
    2. Pop the slide relationships from presentation.xml.rels
    3. Mark the slide parts for removal from the package
    """
    # Step 1 — drop sldIdLst entries
    sld_id_lst = prs.slides._sldIdLst
    rels = prs.part.rels
    rIds_to_drop = []
    for sld_id in list(sld_id_lst):
        rId = sld_id.attrib[qn("r:id")]
        rIds_to_drop.append(rId)
        sld_id_lst.remove(sld_id)

    # Step 2 — pop the slide relationships
    parts_to_drop = []
    for rId in rIds_to_drop:
        if rId in rels:
            rel = rels[rId]
            parts_to_drop.append(rel.target_part)
            rels.pop(rId)

    # Step 3 — drop the slide parts from the package
    package = prs.part.package
    for part in parts_to_drop:
        # Recursively drop the part and its rels
        if hasattr(package, "_parts") and part.partname in package._parts:
            del package._parts[part.partname]


def post_process_zip(pptx_path: Path):
    """Remove orphaned slide parts (the original template slides) from the
    .pptx zip. Without this, duplicate slide names trip PowerPoint warnings.

    A .pptx is a zip; we read it, identify referenced slides via
    presentation.xml.rels, and write only the referenced ones back.
    """
    import shutil
    import tempfile
    import zipfile

    print(f"  post-processing zip to remove orphan slides...")
    referenced_slides: set[str] = set()
    referenced_rels_files: set[str] = set()

    with zipfile.ZipFile(pptx_path, "r") as src:
        with src.open("ppt/_rels/presentation.xml.rels") as f:
            content = f.read().decode("utf-8")
        # Targets look like Target="slides/slide1.xml" relative to ppt/
        import re
        for m in re.finditer(r'Target="(slides/slide\d+\.xml)"', content):
            slide_path = "ppt/" + m.group(1)
            referenced_slides.add(slide_path)
            referenced_rels_files.add(
                slide_path.replace("slides/", "slides/_rels/") + ".rels"
            )

    with zipfile.ZipFile(pptx_path, "r") as src:
        all_names = set(src.namelist())
    all_slide_files = {
        n for n in all_names
        if n.startswith("ppt/slides/slide") and n.endswith(".xml")
    }
    all_slide_rels = {
        n for n in all_names
        if n.startswith("ppt/slides/_rels/slide") and n.endswith(".xml.rels")
    }
    drop = (all_slide_files - referenced_slides) | (all_slide_rels - referenced_rels_files)
    print(f"    referenced: {len(referenced_slides)} slide files; pruning {len(drop)} orphans")

    if not drop:
        return

    fd, tmp_path = tempfile.mkstemp(suffix=".pptx")
    Path(tmp_path).unlink()  # mkstemp creates the file; ZipFile wants to write fresh
    with zipfile.ZipFile(pptx_path, "r") as src, \
         zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as dst:
        seen: set[str] = set()
        for item in src.infolist():
            if item.filename in drop:
                continue
            # Skip duplicates (zip can have multiple entries with same name —
            # keep the LAST one, which is what we just wrote).
            # We achieve this by reading all entries and only emitting the
            # last occurrence of each name.
            seen.add(item.filename)
        # Now do the real copy, last-write-wins for duplicate names.
        last_index_for_name = {}
        for i, item in enumerate(src.infolist()):
            if item.filename in drop:
                continue
            last_index_for_name[item.filename] = i

        for i, item in enumerate(src.infolist()):
            if item.filename in drop:
                continue
            if last_index_for_name[item.filename] != i:
                continue
            data = src.read(item.filename)
            dst.writestr(item, data)
    shutil.move(tmp_path, pptx_path)
    print(f"    done")


def add_slide(prs, layout_name=None, layout_idx=None):
    """Add a slide using a layout by name (preferred) or index."""
    if layout_name:
        for layout in prs.slide_layouts:
            if layout.name == layout_name:
                return prs.slides.add_slide(layout)
    return prs.slides.add_slide(prs.slide_layouts[layout_idx or 0])


def clear_placeholder_text(ph):
    """Empty an existing placeholder so we can write fresh."""
    if ph.has_text_frame:
        ph.text_frame.clear()


def set_text(text_frame, text, font_size=None, bold=False, color=None, align=None, font_name=None):
    """Replace the first paragraph of a text_frame with one styled run."""
    text_frame.clear()
    p = text_frame.paragraphs[0]
    if align:
        p.alignment = align
    run = p.add_run()
    run.text = text
    if font_size:
        run.font.size = Pt(font_size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    if font_name:
        run.font.name = font_name


def add_textbox(slide, x_in, y_in, w_in, h_in, text, font_size=18, bold=False,
                color=SC_INK, align=PP_ALIGN.LEFT, font_name=None,
                anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x_in), Inches(y_in), Inches(w_in), Inches(h_in))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    set_text(tf, text, font_size=font_size, bold=bold, color=color, align=align, font_name=font_name)
    return box


def add_filled_rect(slide, x_in, y_in, w_in, h_in, fill_color, line_color=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(x_in), Inches(y_in),
                                 Inches(w_in), Inches(h_in))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(0.5)
    shp.shadow.inherit = False
    return shp


def add_pill(slide, x_in, y_in, w_in, h_in, text, fill_color, text_color, font_size=10):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(x_in), Inches(y_in),
                                 Inches(w_in), Inches(h_in))
    shp.adjustments[0] = 0.5  # max rounding -> pill
    shp.fill.solid(); shp.fill.fore_color.rgb = fill_color
    shp.line.fill.background()
    tf = shp.text_frame
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02); tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    set_text(tf, text, font_size=font_size, bold=True, color=text_color, align=PP_ALIGN.CENTER)
    return shp


def add_corner_chrome(slide, slide_num, total):
    """Top-left brand mark, top-right title, bottom slide number — runs on every slide."""
    # Top thin bar
    add_filled_rect(slide, 0, 0, 13.33, 0.06, SC_BLUE)
    # smartcredit BETA mark, top-left
    add_textbox(slide, 0.5, 0.18, 4.5, 0.4,
                "smartcredit", font_size=18, bold=True, color=SC_INK,
                align=PP_ALIGN.LEFT)
    add_textbox(slide, 1.85, 0.22, 1.0, 0.3,
                "BETA", font_size=12, bold=True, color=SC_BLUE,
                align=PP_ALIGN.LEFT)
    # Slide number bottom-right
    add_textbox(slide, 12.5, 7.05, 0.7, 0.3,
                f"{slide_num} / {total}", font_size=9, color=SC_INK_MUTED,
                align=PP_ALIGN.RIGHT)
    # Footer left
    add_textbox(slide, 0.5, 7.05, 6.0, 0.3,
                "myReclaim · Confidential — Consumer Direct, Inc.",
                font_size=9, color=SC_INK_MUTED)


# =========================================================================
# Slide builders
# =========================================================================

def slide_01_title(prs, n, total):
    s = add_slide(prs, "Title Slide")
    # Big background bar
    add_filled_rect(s, 0, 0, 13.33, 7.5, SC_BG_SUBTLE)
    # Accent block
    add_filled_rect(s, 0, 0, 0.8, 7.5, SC_BLUE)
    # Big brand wordmark
    add_textbox(s, 1.5, 1.2, 11, 0.5,
                "SMARTCREDIT  ·  PRODUCT PROPOSAL",
                font_size=14, bold=True, color=SC_BLUE,
                align=PP_ALIGN.LEFT)
    # Title (the feature name)
    add_textbox(s, 1.5, 1.9, 11, 1.8,
                "myReclaim",
                font_size=84, bold=True, color=SC_INK,
                align=PP_ALIGN.LEFT)
    # Tagline
    add_textbox(s, 1.5, 3.7, 11, 1.0,
                "Find money the state owes our members — automatically.",
                font_size=28, bold=False, color=SC_INK_BODY,
                align=PP_ALIGN.LEFT)
    # Sub-tagline
    add_textbox(s, 1.5, 4.7, 11, 0.5,
                "A new feature for SmartCredit · Powered by our existing identity-matching engine",
                font_size=14, color=SC_INK_MUTED,
                align=PP_ALIGN.LEFT)
    # Date / author block
    add_textbox(s, 1.5, 6.3, 8, 0.4,
                "Executive proposal · April 2026 · Prepared by Ahmed Yassine",
                font_size=12, color=SC_INK_MUTED,
                align=PP_ALIGN.LEFT)


def slide_02_what_it_is(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "WHAT IT IS",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "myReclaim is a free SmartCredit feature that finds unclaimed money owed to our members.",
                font_size=28, bold=True, color=SC_INK)

    # 3-column value props
    cols = [
        ("Automatic discovery", "We already have the member's identity. We match it against state unclaimed-property records — no search effort required.", SC_BLUE),
        ("Free for members", "We don't charge the member. We deep-link to the state's official claim portal. No finder-service regulation.", SC_ORANGE),
        ("Defensible moat", "There is no MissingMoney API. Every other player either makes the user search or charges 10–25% of the recovery. We do neither.", SC_AMBER),
    ]
    col_w = 3.95
    col_x_start = 0.5
    gap = 0.25
    for i, (head, body, accent) in enumerate(cols):
        x = col_x_start + i * (col_w + gap)
        # card
        add_filled_rect(s, x, 2.6, col_w, 3.5, SC_BG_CARD, line_color=SC_BORDER)
        # accent strip
        add_filled_rect(s, x, 2.6, col_w, 0.12, accent)
        add_textbox(s, x + 0.3, 2.85, col_w - 0.6, 0.6,
                    head, font_size=20, bold=True, color=SC_INK)
        add_textbox(s, x + 0.3, 3.55, col_w - 0.6, 2.4,
                    body, font_size=13, color=SC_INK_BODY)

    # Bottom callout
    add_filled_rect(s, 0.5, 6.3, 12.3, 0.5, SC_BLUE)
    add_textbox(s, 0.7, 6.36, 12, 0.4,
                "Why \"myReclaim\"? It fits the SmartCredit naming family (myLO, myCredit) and tells the user exactly what the feature does — reclaim what's already theirs.",
                font_size=12, color=RGBColor(0xFF, 0xFF, 0xFF))


def slide_03_opportunity(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "THE OPPORTUNITY",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "$70B sits with U.S. states unclaimed. The average household has ~$200.",
                font_size=26, bold=True, color=SC_INK)

    # Big number block
    add_filled_rect(s, 0.5, 2.2, 6.0, 4.0, SC_BLUE)
    add_textbox(s, 0.7, 2.5, 5.6, 1.6,
                "$70B+", font_size=96, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF))
    add_textbox(s, 0.7, 4.2, 5.6, 0.6,
                "in unclaimed property held by U.S. states",
                font_size=18, color=RGBColor(0xFF, 0xFF, 0xFF))
    add_textbox(s, 0.7, 4.8, 5.6, 0.4,
                "Source: NAUPA / state treasurers",
                font_size=11, color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 5.5, 5.6, 0.5,
                "~$200 avg. household balance · grows with every dormant account, refund, or uncashed check",
                font_size=12, color=RGBColor(0xCC, 0xDD, 0xFF))

    # Why we win column
    add_textbox(s, 7.0, 2.2, 5.8, 0.4,
                "WHY SMARTCREDIT WINS", font_size=12, bold=True, color=SC_BLUE)
    bullets = [
        ("3M+", "members already identity-verified inside SmartCredit"),
        ("Existing", "name-matching engine built for data-broker scrubs"),
        ("Existing", "Snowflake warehouse with PII handling controls"),
        ("Trusted", "credit-monitoring brand — the natural place to surface a financial discovery"),
    ]
    y = 2.7
    for kicker, body in bullets:
        add_filled_rect(s, 7.0, y, 5.8, 0.7, SC_BG_CARD, line_color=SC_BORDER)
        add_textbox(s, 7.15, y + 0.08, 1.6, 0.55,
                    kicker, font_size=18, bold=True, color=SC_ORANGE)
        add_textbox(s, 8.7, y + 0.13, 4.1, 0.55,
                    body, font_size=12, color=SC_INK_BODY)
        y += 0.85

    add_textbox(s, 0.5, 6.6, 12.3, 0.3,
                "Translation: we are the only org in this space that already has the user identified, the warehouse to ingest the data, and the matching engine to do the work.",
                font_size=11, color=SC_INK_MUTED, align=PP_ALIGN.LEFT)


def slide_04_competitive(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "COMPETITIVE LANDSCAPE",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "What's available today — and the gap myReclaim fills.",
                font_size=26, bold=True, color=SC_INK)

    # Build a 4-column comparison table-like grid
    headers = ["", "MissingMoney.com", "BlueNavy", "myReclaim (us)"]
    rows = [
        ("Coverage",      "49 states, search only",   "2 states (CA, GA)",   "All 50 + federal (planned)"),
        ("Knows user?",   "No — user types it in",     "No — uses skip-trace", "Yes — we are SmartCredit"),
        ("User effort",   "Manual search per state",   "Inbound contact",       "Automatic notification"),
        ("Cost to user",  "Free",                       "10–25% of recovery",   "Free (member benefit)"),
        ("Operator",      "NAUPA / Kelmar",             "Recovery firm",         "Consumer Direct"),
        ("Regulation",    "None",                       "Finder-service in 30+ states", "None — deep-link to state"),
    ]

    # Column geometry
    col_xs = [0.5, 3.7, 6.9, 10.1]
    col_ws = [3.1, 3.1, 3.1, 2.7]
    row_h = 0.55
    y0 = 2.3

    # header row
    for x, w, head in zip(col_xs, col_ws, headers):
        if head == "myReclaim (us)":
            add_filled_rect(s, x, y0, w, row_h, SC_BLUE)
            add_textbox(s, x + 0.1, y0 + 0.1, w - 0.2, row_h - 0.1,
                        head, font_size=13, bold=True,
                        color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
        elif head:
            add_filled_rect(s, x, y0, w, row_h, SC_INK)
            add_textbox(s, x + 0.1, y0 + 0.1, w - 0.2, row_h - 0.1,
                        head, font_size=13, bold=True,
                        color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    # data rows
    for i, row in enumerate(rows):
        y = y0 + (i + 1) * row_h
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        for j, (x, w, val) in enumerate(zip(col_xs, col_ws, row)):
            add_filled_rect(s, x, y, w, row_h, bg, line_color=SC_BORDER)
            color = SC_BLUE if j == 3 else SC_INK_BODY
            bold = j == 0 or j == 3
            size = 12 if j == 0 else 11
            add_textbox(s, x + 0.15, y + 0.12, w - 0.3, row_h - 0.15,
                        val, font_size=size, bold=bold, color=color, align=PP_ALIGN.LEFT)

    add_filled_rect(s, 0.5, 6.3, 12.3, 0.5, SC_BLUE)
    add_textbox(s, 0.7, 6.37, 12, 0.4,
                "There is no MissingMoney API. The only path to scale is state-by-state. We are uniquely positioned to walk it.",
                font_size=12, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True)


def slide_05_strategy_section(prs, n, total):
    s = add_slide(prs, "Section Header")
    add_filled_rect(s, 0, 0, 13.33, 7.5, SC_BLUE)
    add_textbox(s, 0.5, 2.4, 12.3, 0.6,
                "PART II", font_size=14, bold=True,
                color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.LEFT)
    add_textbox(s, 0.5, 3.0, 12.3, 1.6,
                "How we get the data.",
                font_size=64, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.LEFT)
    add_textbox(s, 0.5, 4.7, 12.3, 0.8,
                "A state-by-state strategy ranked by data accessibility, member coverage, and legal posture.",
                font_size=20,
                color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.LEFT)
    add_textbox(s, 0.5, 7.05, 12.3, 0.3,
                f"{n} / {total}", font_size=10,
                color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.RIGHT)


def state_priority_slide(prs, n, total, title, subtitle, rows):
    """Reusable state-matrix slide."""
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "DATA-SOURCE STRATEGY",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.55,
                title, font_size=24, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 1.6, 12.5, 0.35,
                subtitle, font_size=12, color=SC_INK_MUTED)

    # Table header
    cols = [
        ("#",                     0.45,  0.4),
        ("State",                 0.85,  0.7),
        ("Data status",           1.55,  3.6),
        ("Approval needed?",      5.15,  2.6),
        ("Recommendation",        7.75,  5.05),
    ]
    y0 = 2.05
    header_h = 0.45
    for label, x, w in cols:
        add_filled_rect(s, x, y0, w, header_h, SC_INK)
        add_textbox(s, x + 0.1, y0 + 0.1, w - 0.2, header_h - 0.1,
                    label, font_size=11, bold=True,
                    color=RGBColor(0xFF, 0xFF, 0xFF))

    # Body rows
    row_h_default = 0.9
    y = y0 + header_h
    for i, (rank, state, status, approval, recommendation, badge_color) in enumerate(rows):
        row_h = row_h_default
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        for label, x, w in cols:
            add_filled_rect(s, x, y, w, row_h, bg, line_color=SC_BORDER)
        # rank pill
        add_pill(s, cols[0][1] + 0.05, y + 0.27, cols[0][2] - 0.1, 0.36,
                 str(rank), SC_BLUE, RGBColor(0xFF, 0xFF, 0xFF), font_size=12)
        # state
        add_textbox(s, cols[1][1] + 0.1, y + 0.18, cols[1][2] - 0.2, row_h - 0.2,
                    state, font_size=18, bold=True, color=SC_INK)
        # data status
        add_textbox(s, cols[2][1] + 0.1, y + 0.1, cols[2][2] - 0.2, row_h - 0.15,
                    status, font_size=10, color=SC_INK_BODY)
        # approval (with colored badge)
        add_pill(s, cols[3][1] + 0.1, y + 0.12, 1.0, 0.28,
                 badge_color[0], badge_color[1], RGBColor(0xFF, 0xFF, 0xFF), font_size=9)
        add_textbox(s, cols[3][1] + 0.1, y + 0.45, cols[3][2] - 0.2, row_h - 0.5,
                    approval, font_size=10, color=SC_INK_BODY)
        # recommendation
        add_textbox(s, cols[4][1] + 0.1, y + 0.1, cols[4][2] - 0.2, row_h - 0.15,
                    recommendation, font_size=10, color=SC_INK_BODY)
        y += row_h


def slide_06_states_top(prs, n, total):
    rows = [
        (1, "FL", "No safe automated bulk ingest. Florida portal is intentionally manual; automation may revoke access.",
         "Yes — claimant rep must be FL attorney, CPA, or licensed PI registered with the dept.",
         "Don't scrape. v1: official claim handoff. v2: register a partner or written permission.",
         ("BLOCKED", SC_RED)),
        (2, "TX", "Request-based dataset on data.gov. Provide name, company, mailing address, phone, TX PI license # if applicable.",
         "Yes — formal request required.",
         "High-priority request. Ask explicitly to cache, match against members, and redisplay limited fields.",
         ("REQUEST", SC_AMBER)),
        (3, "CA", "Best public bulk source. Full CSVs at sco.ca.gov/upd_download_property_records, refreshed every Thursday.",
         "No pre-approval shown; legal review still recommended for caching/redisplay.",
         "Build first. Weekly HTTP download → S3 → Snowpipe → Snowflake. Already prototyped.",
         ("GO", SC_GREEN)),
        (4, "GA", "Downloadable rich database (>1GB delimited text), updated weekly, with full property/owner/holder fields.",
         "Yes — CDR registration + background check.",
         "High value: GA is in our top member-density states. Don't ingest until we register or partner.",
         ("REGISTER", SC_AMBER)),
        (5, "NY", "Requestable secure-FTP file, zipped delimited TXT, updated quarterly. Excludes dollar amounts and tax IDs.",
         "Yes — request required. Location-service rules apply if we ever charge.",
         "Good 2nd or 3rd. Use for matching; UI shows \"amount unavailable\" for NY records.",
         ("REQUEST", SC_AMBER)),
    ]
    state_priority_slide(prs, n, total,
                          title="Top 5 priority states",
                          subtitle="Largest combined opportunity from member coverage, data accessibility, and political feasibility.",
                          rows=rows)


def slide_07_states_mid(prs, n, total):
    rows = [
        (6, "IL", "Public search/claim site only. No bulk feed confirmed — site updates owner names weekly.",
         "Not confirmed.",
         "Contact IL Treasurer for matching agreement; otherwise official handoff.",
         ("CONTACT", SC_INK_MUTED)),
        (7, "NC", "Annual unclaimed-property listings published by last name, but as PDFs.",
         "No approval shown for PDFs; not a clean feed.",
         "Skip PDF parsing — request structured data from NC Treasurer.",
         ("LOW-FIT", SC_INK_MUTED)),
        (8, "PA", "Public search/claim portal. No bulk download or API confirmed.",
         "Not confirmed.",
         "Official handoff. Contact PA Treasury for terms.",
         ("CONTACT", SC_INK_MUTED)),
        (9, "NJ", "Public search/claim portal. No bulk download or API confirmed.",
         "Not confirmed.",
         "Official handoff. Contact NJ Unclaimed Property Administration.",
         ("CONTACT", SC_INK_MUTED)),
        (10, "SC", "Public search/claim portal. No bulk download or API confirmed.",
         "Not confirmed.",
         "Official handoff. Contact SC Treasurer for bulk-data permission.",
         ("CONTACT", SC_INK_MUTED)),
    ]
    state_priority_slide(prs, n, total,
                          title="Tier 2 — handoff or partner",
                          subtitle="States 6–10. No public bulk feeds today; data access requires outreach to the treasurer's office.",
                          rows=rows)


def slide_08_states_bottom(prs, n, total):
    rows = [
        (11, "AL", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact AL Treasury.", ("CONTACT", SC_INK_MUTED)),
        (12, "OH", "Registered finder portal with owner-identifying info — replaces former CD distribution.",
         "Yes — registered professional finder path.",
         "Ingest only after we qualify or partner with a registered finder.",
         ("REGISTER", SC_AMBER)),
        (13, "LA", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact LA Treasury.", ("CONTACT", SC_INK_MUTED)),
        (14, "VA", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact VA Treasury.", ("CONTACT", SC_INK_MUTED)),
        (15, "AZ", "Points users to MissingMoney as authorized site. No state bulk feed.",
         "Locator rules may apply if we charge.",
         "Handoff or pursue MissingMoney/Kelmar/AZ permission.",
         ("CONTACT", SC_INK_MUTED)),
        (16, "MI", "Limited electronic data for locators — accounts dormant 24+ months and ≥$10K.",
         "Yes — registered locator, high-value only.",
         "High-value matching only. Not for broad coverage.",
         ("REGISTER", SC_AMBER)),
    ]
    state_priority_slide(prs, n, total,
                          title="Tier 3 — handoff, register, or pass",
                          subtitle="States 11–16. Mix of contact-required portals, registered-finder regimes, and limited high-value-only programs.",
                          rows=rows)


def slide_09_states_pass(prs, n, total):
    rows = [
        (17, "MD", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact Maryland Comptroller.", ("CONTACT", SC_INK_MUTED)),
        (18, "TN", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact TN Treasury.", ("CONTACT", SC_INK_MUTED)),
        (19, "MS", "Public portal. No bulk confirmed.", "Not confirmed.",
         "Handoff. Contact MS Treasury.", ("CONTACT", SC_INK_MUTED)),
        (20, "MO", "Annual county owner lists with names + last-known addresses. Search portal uses reCAPTCHA — do not automate.",
         "County lists appear public; not a structured feed.",
         "Possible low-fidelity ingestion from county lists. Better: request structured data.",
         ("LOW-FIT", SC_INK_MUTED)),
        (21, "WA", "State law prohibits sale or distribution of the unclaimed-property owner list for commercial purposes.",
         "Effectively blocked unless specific legal basis or agreement.",
         "Do NOT ingest for commercial matching without written legal approval.",
         ("BLOCKED", SC_RED)),
    ]
    state_priority_slide(prs, n, total,
                          title="Tier 4 — handoff only or blocked",
                          subtitle="States 17–21. WA is effectively closed for commercial matching; the rest are official-handoff candidates.",
                          rows=rows)


def slide_10_architecture(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "DATA INGESTION ARCHITECTURE",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.7,
                "How the data flows from state portals into Snowflake.",
                font_size=24, bold=True, color=SC_INK)

    # Architecture pipeline
    box_y = 2.2
    box_h = 1.0
    boxes = [
        ("State data sources",
         "CA bulk CSV (Thursdays)\nTX request file\nNY SFTP (quarterly)\nGA registered file\n+ partner channels",
         SC_BLUE, 0.5, 2.4),
        ("Landing zone (S3)",
         "Versioned by\nyyyy=YYYY/mm=MM/dd=DD\nETag-aware fetch\nQuarantine on schema change",
         SC_BLUE_DARK, 3.2, 2.4),
        ("Snowflake (raw)",
         "Snowpipe auto-ingest\nExternal stages\nNAUPA III canonical\nRow versioning",
         SC_INK, 5.9, 2.4),
        ("Snowflake (mart)",
         "dbt models\ncanonical_unclaimed\ndim_member_match_keys\nrow-level dedupe",
         SC_BLUE_DARK, 8.6, 2.4),
        ("myReclaim API",
         "Member lookup\nResults + claim links\nCovered states display\nNotification engine",
         SC_BLUE, 11.3, 1.6),
    ]
    # Wider boxes - recompute
    n_boxes = 4
    margin = 0.5
    spacing = 0.3
    total_w = 13.33 - 2 * margin
    box_w = (total_w - (n_boxes - 1) * spacing) / n_boxes
    arch = [
        ("State data sources",
         ["CA bulk CSV (weekly)",
          "TX requested file",
          "NY SFTP quarterly",
          "GA registered file",
          "+ partner channels"]),
        ("Landing zone (S3)",
         ["Versioned by date",
          "ETag-aware fetch",
          "Schema-change quarantine",
          "Per-source bucket prefixes"]),
        ("Snowflake (raw → mart)",
         ["Snowpipe auto-ingest",
          "NAUPA III canonical schema",
          "dbt models for normalize/dedupe",
          "Row-level lineage"]),
        ("myReclaim API + UX",
         ["Member identity → match service",
          "Results card list (already prototyped)",
          "Per-state claim deep-link",
          "Notification engine (email/push)"]),
    ]
    accent_colors = [SC_BLUE, SC_ORANGE, SC_BLUE_DARK, SC_BLUE]
    for i, (title, items) in enumerate(arch):
        x = margin + i * (box_w + spacing)
        # card
        add_filled_rect(s, x, box_y, box_w, 3.4, SC_BG_CARD, line_color=SC_BORDER)
        # accent strip
        add_filled_rect(s, x, box_y, box_w, 0.18, accent_colors[i])
        # number badge
        add_pill(s, x + 0.15, box_y + 0.32, 0.4, 0.4,
                 str(i + 1), accent_colors[i], RGBColor(0xFF, 0xFF, 0xFF), font_size=14)
        add_textbox(s, x + 0.65, box_y + 0.32, box_w - 0.7, 0.5,
                    title, font_size=14, bold=True, color=SC_INK)
        # bullets
        body_text = "\n".join("• " + it for it in items)
        add_textbox(s, x + 0.2, box_y + 0.95, box_w - 0.3, 2.4,
                    body_text, font_size=11, color=SC_INK_BODY)
        # arrow
        if i < len(arch) - 1:
            ax = x + box_w + 0.04
            ay = box_y + 1.55
            arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                      Inches(ax), Inches(ay),
                                      Inches(spacing - 0.08), Inches(0.3))
            arr.fill.solid(); arr.fill.fore_color.rgb = SC_INK_MUTED
            arr.line.fill.background()

    # Bottom callout
    add_filled_rect(s, 0.5, 5.95, 12.3, 1.2, SC_BG_SUBTLE, line_color=SC_BORDER)
    add_textbox(s, 0.7, 6.05, 12, 0.4,
                "Why Snowflake?", font_size=14, bold=True, color=SC_BLUE)
    add_textbox(s, 0.7, 6.45, 12, 0.7,
                "We already operate it. Adding myReclaim is a new schema, not new infrastructure. PII-handling controls, encryption, audit logging, and dbt are all in place from day one — no greenfield buildout.",
                font_size=11, color=SC_INK_BODY)


def slide_11_match_reuse(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "REUSING WHAT WE'VE ALREADY BUILT",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.7,
                "Our privacy name-matching engine becomes the heart of myReclaim.",
                font_size=24, bold=True, color=SC_INK)

    # Two-column comparison: Today (Privacy Master) → myReclaim
    col_w = 5.9
    gap = 0.5
    y = 2.0
    # Privacy Master card
    add_filled_rect(s, 0.5, y, col_w, 4.5, SC_BG_CARD, line_color=SC_BORDER)
    add_filled_rect(s, 0.5, y, col_w, 0.18, SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.3, col_w - 0.4, 0.5,
                "TODAY — Privacy Master", font_size=12, bold=True, color=SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.75, col_w - 0.4, 0.6,
                "Find data brokers exposing member info",
                font_size=18, bold=True, color=SC_INK)
    pm_inputs = [
        ("Input", "Member identity (name, addresses, age, DOB)"),
        ("Engine", "CD's existing fuzzy-match service\n(Soundex / Metaphone / token / address normalization)"),
        ("Output", "Match candidates from data-broker corpus\nWith confidence score per record"),
        ("Action", "Member sees \"X brokers expose your info\" → Remove / Keep"),
    ]
    yy = y + 1.5
    for label, body in pm_inputs:
        add_textbox(s, 0.7, yy, 1.2, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, 1.95, yy, col_w - 1.5, 0.65,
                    body, font_size=11, color=SC_INK_BODY)
        yy += 0.7

    # Arrow between cards
    arr = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                              Inches(0.5 + col_w + 0.05),
                              Inches(y + 1.9),
                              Inches(gap - 0.1), Inches(0.7))
    arr.fill.solid(); arr.fill.fore_color.rgb = SC_ORANGE
    arr.line.fill.background()

    # myReclaim card
    x2 = 0.5 + col_w + gap
    add_filled_rect(s, x2, y, col_w, 4.5, SC_BG_CARD, line_color=SC_BLUE)
    add_filled_rect(s, x2, y, col_w, 0.18, SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.3, col_w - 0.4, 0.5,
                "TOMORROW — myReclaim", font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.75, col_w - 0.4, 0.6,
                "Find unclaimed money owed to the member",
                font_size=18, bold=True, color=SC_INK)
    mr_inputs = [
        ("Input", "Same member identity — pre-populated from profile"),
        ("Engine", "Same CD fuzzy-match service\n(Plug-in via the MatchService Protocol)"),
        ("Output", "Match candidates from state unclaimed-property corpus\nWith confidence score per record"),
        ("Action", "Member sees \"You may have $X waiting\" → Claim → state portal"),
    ]
    yy = y + 1.5
    for label, body in mr_inputs:
        add_textbox(s, x2 + 0.2, yy, 1.2, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, x2 + 1.45, yy, col_w - 1.5, 0.65,
                    body, font_size=11, color=SC_INK_BODY)
        yy += 0.7

    # Bottom callout
    add_filled_rect(s, 0.5, 6.65, 12.3, 0.4, SC_BLUE)
    add_textbox(s, 0.7, 6.7, 12, 0.32,
                "Same engine. Same identity layer. Same pipeline shape. The only new thing is the corpus we match against — and the value we hand back to the member.",
                font_size=11, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))


def slide_12_sprint_plan(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "DELIVERY PLAN",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.7,
                "Six sprint blocks. First state live within ~6 weeks.",
                font_size=24, bold=True, color=SC_INK)

    sprints = [
        ("Sprint 1",     "CA + Foundation",
         ["California ingestion (CSV → S3 → Snowpipe)",
          "Snowflake schema (NAUPA III canonical)",
          "Match service integration (CD's existing engine)",
          "Member-facing alert UX in SmartCredit dashboard"],
         SC_BLUE, "GO"),
        ("Sprint 2",     "Permission outreach",
         ["Texas: file the data request (PI license, intended use, redistribution rights)",
          "New York: file SFTP request through OSC",
          "Begin Florida partnership conversations"],
         SC_AMBER, "REQUEST"),
        ("Sprint 3",     "TX + NY ingest",
         ["NY SFTP ingestion — quarterly schedule",
          "TX file ingestion (if approved)",
          "UI: \"Amount unavailable\" rendering for NY records"],
         SC_AMBER, "BUILD"),
        ("Sprint 4",     "GA path",
         ["Claimant Designated Representative (CDR) registration",
          "Background-check process",
          "Legal approval for caching/redisplay",
          "Ingest GA delimited file once approved"],
         SC_AMBER, "LEGAL"),
        ("Sprint 5",     "FL path",
         ["Florida partnership with registered claimant rep, OR",
          "Written permission for limited redistribution",
          "Strict no-scraping policy"],
         SC_RED,    "CAUTION"),
        ("Ongoing",      "Search-only handoff for the rest",
         ["IL, PA, NJ, SC, AL, LA, VA, AZ, MD, TN, MS, WA covered via deep-link to state portal",
          "Outreach in parallel for any state willing to grant a feed",
          "Skip WA entirely until written legal basis"],
         SC_INK_MUTED, "HANDOFF"),
    ]

    # Render sprints as 6 stacked rows
    y = 2.0
    row_h = 0.78
    for sprint, title, items, color, badge in sprints:
        # left rail
        add_filled_rect(s, 0.5, y, 0.18, row_h - 0.1, color)
        add_filled_rect(s, 0.5, y, 12.3, row_h - 0.1, SC_BG_CARD, line_color=SC_BORDER)
        # accent rail (paint over)
        add_filled_rect(s, 0.5, y, 0.18, row_h - 0.1, color)
        # sprint label
        add_textbox(s, 0.85, y + 0.05, 1.1, 0.35,
                    sprint, font_size=11, bold=True, color=color)
        add_textbox(s, 0.85, y + 0.35, 1.7, 0.3,
                    title, font_size=13, bold=True, color=SC_INK)
        # bullets
        bullet_text = "  ·  ".join(items)
        add_textbox(s, 2.65, y + 0.1, 8.8, row_h - 0.2,
                    bullet_text, font_size=10, color=SC_INK_BODY)
        # badge
        add_pill(s, 11.6, y + 0.18, 1.1, 0.32,
                 badge, color, RGBColor(0xFF, 0xFF, 0xFF), font_size=9)
        y += row_h


def slide_13_compliance(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "COMPLIANCE POSTURE",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "Free + deep-link = no new regulatory exposure.",
                font_size=24, bold=True, color=SC_INK)

    items = [
        ("FCRA-safe",
         "Unclaimed-property search is not a credit-reporting activity. Lives outside FCRA scope.",
         SC_GREEN),
        ("No finder license needed",
         "We don't take a fee on claims. ~30 states regulate finders and cap fees at 10%. We avoid that whole regime by being a free member benefit.",
         SC_GREEN),
        ("No new PII surface",
         "myReclaim reuses the SmartCredit identity records that members have already consented to. No additional data collection.",
         SC_GREEN),
        ("State data ToS",
         "We follow each state's terms. CA bulk file is publicly published. Restricted states (FL, GA, OH, MI, WA) gated behind registration or skipped.",
         SC_AMBER),
        ("Deep-link claim",
         "Members file with the state directly. We never collect or hold their claim. Keeps us out of finder-service regulation in 30+ states.",
         SC_GREEN),
        ("Legal review gate",
         "Every state ingestion has legal sign-off before going live. Snowflake row-level lineage shows exactly where each record came from and on what date.",
         SC_BLUE),
    ]
    cols = 3
    col_w = 4.05
    row_h = 1.85
    margin_x = 0.5
    gap_x = 0.15
    y0 = 2.2
    gap_y = 0.2
    for i, (head, body, color) in enumerate(items):
        col = i % cols
        row = i // cols
        x = margin_x + col * (col_w + gap_x)
        y = y0 + row * (row_h + gap_y)
        add_filled_rect(s, x, y, col_w, row_h, SC_BG_CARD, line_color=SC_BORDER)
        add_filled_rect(s, x, y, 0.16, row_h, color)
        add_textbox(s, x + 0.3, y + 0.18, col_w - 0.4, 0.45,
                    head, font_size=15, bold=True, color=SC_INK)
        add_textbox(s, x + 0.3, y + 0.65, col_w - 0.4, row_h - 0.7,
                    body, font_size=11, color=SC_INK_BODY)


def slide_14_demo(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "WHAT'S ALREADY BUILT",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "A working prototype against 38.3M real California records — running today.",
                font_size=24, bold=True, color=SC_INK)

    # Big metric stack
    metrics = [
        ("38.3M", "records loaded", SC_BLUE),
        ("$11B+", "total value indexed", SC_ORANGE),
        ("113 sec", "to bulk-load 34M rows via DuckDB", SC_BLUE_DARK),
        ("3", "of Ahmed's records found by name search", SC_AMBER),
    ]
    y0 = 2.2
    box_w = 2.95
    margin = 0.5
    gap = 0.2
    for i, (big, small, color) in enumerate(metrics):
        x = margin + i * (box_w + gap)
        add_filled_rect(s, x, y0, box_w, 1.6, SC_BG_CARD, line_color=SC_BORDER)
        add_filled_rect(s, x, y0, box_w, 0.15, color)
        add_textbox(s, x + 0.2, y0 + 0.3, box_w - 0.4, 0.85,
                    big, font_size=36, bold=True, color=color)
        add_textbox(s, x + 0.2, y0 + 1.15, box_w - 0.4, 0.4,
                    small, font_size=11, color=SC_INK_BODY)

    # What's running
    y2 = 4.1
    add_textbox(s, 0.5, y2, 12.5, 0.4,
                "WHAT'S RUNNING TODAY", font_size=11, bold=True, color=SC_BLUE)
    items = [
        "FastAPI + Jinja + htmx web app, SmartCredit-themed (matches the BETA visual language)",
        "DuckDB local store with Snowflake-shaped SQL — queries port directly to production",
        "Fuzzy match service (token-substring with tier ranking) — pluggable; swap in CD's matcher",
        "9-slide demo deck with embedded live search on slide 4",
        "Admin page surfaces real ingestion stats and per-tier load history",
    ]
    yy = y2 + 0.4
    for it in items:
        add_textbox(s, 0.7, yy, 12.0, 0.4,
                    "✓  " + it, font_size=12, color=SC_INK_BODY)
        yy += 0.35

    add_filled_rect(s, 0.5, 6.55, 12.3, 0.5, SC_BLUE)
    add_textbox(s, 0.7, 6.6, 12, 0.4,
                "Source: github.com/ahmedyassineconsumerdirect/cd-missing-funds-finder · Branch: prototype-v1 · Demo: localhost:8088",
                font_size=11, color=RGBColor(0xFF, 0xFF, 0xFF))


def slide_15_ask(prs, n, total):
    s = add_slide(prs, "Title Only")
    add_corner_chrome(s, n, total)
    add_textbox(s, 0.5, 0.7, 12.5, 0.35,
                "THE ASK",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.05, 12.5, 0.9,
                "Approve the program and staff it.",
                font_size=28, bold=True, color=SC_INK)

    # Resource ask
    add_filled_rect(s, 0.5, 2.2, 6.0, 4.0, SC_BLUE)
    add_textbox(s, 0.7, 2.4, 5.6, 0.5,
                "RESOURCE REQUEST", font_size=12, bold=True,
                color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 2.9, 5.6, 0.7,
                "1 data engineer", font_size=24, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF))
    add_textbox(s, 0.7, 3.6, 5.6, 0.7,
                "1 product engineer", font_size=24, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF))
    add_textbox(s, 0.7, 4.4, 5.6, 0.7,
                "~6 weeks to first state live (CA)",
                font_size=18, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF))
    add_textbox(s, 0.7, 5.0, 5.6, 0.4,
                "~6 months to top-10 state coverage",
                font_size=14, color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 5.4, 5.6, 0.4,
                "Plus: legal review for each ingestion path",
                font_size=14, color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 5.85, 5.6, 0.3,
                "No new infrastructure — Snowflake already paid for.",
                font_size=11, color=RGBColor(0xCC, 0xDD, 0xFF))

    # Outcomes
    add_textbox(s, 7.0, 2.2, 5.8, 0.4,
                "EXPECTED OUTCOMES", font_size=12, bold=True, color=SC_BLUE)
    outcomes = [
        ("Member feature unique in our market", "No credit-monitoring competitor has this."),
        ("Measurable retention lift", "Every found-money notification is a \"wow\" moment from us."),
        ("Sign-up incentive for non-members", "\"You may have unclaimed money. Sign up free to find out.\""),
        ("Defensible moat", "12+ months of state ingestion work others would have to repeat."),
    ]
    yy = 2.7
    for head, body in outcomes:
        add_filled_rect(s, 7.0, yy, 5.8, 0.85, SC_BG_CARD, line_color=SC_BORDER)
        add_filled_rect(s, 7.0, yy, 0.16, 0.85, SC_ORANGE)
        add_textbox(s, 7.3, yy + 0.08, 5.4, 0.35,
                    head, font_size=13, bold=True, color=SC_INK)
        add_textbox(s, 7.3, yy + 0.42, 5.4, 0.4,
                    body, font_size=11, color=SC_INK_BODY)
        yy += 0.95

    add_filled_rect(s, 0.5, 6.6, 12.3, 0.45, SC_ORANGE)
    add_textbox(s, 0.7, 6.65, 12, 0.4,
                "Approve Sprint 1 today and the first state goes live by mid-Q3.",
                font_size=14, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF))


def slide_16_thanks(prs, n, total):
    s = add_slide(prs, "Section Header")
    add_filled_rect(s, 0, 0, 13.33, 7.5, SC_INK)
    add_textbox(s, 0.5, 2.2, 12.3, 0.4,
                "myReclaim", font_size=18, bold=True, color=SC_ORANGE,
                align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 2.7, 12.3, 1.5,
                "Thank you.", font_size=80, bold=True,
                color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 4.4, 12.3, 0.6,
                "Questions? Discussion?",
                font_size=24,
                color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 5.6, 12.3, 0.4,
                "Ahmed Yassine · ahmed@consumerdirect.com",
                font_size=14,
                color=RGBColor(0xCC, 0xDD, 0xFF), align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 6.0, 12.3, 0.4,
                "Live demo: localhost:8088 · Repo: github.com/ahmedyassineconsumerdirect/cd-missing-funds-finder",
                font_size=11,
                color=RGBColor(0x99, 0xAA, 0xCC), align=PP_ALIGN.CENTER)


# =========================================================================
# Main
# =========================================================================
def main():
    print(f"Loading template: {TEMPLATE}")
    prs = Presentation(str(TEMPLATE))
    print(f"  {len(prs.slides)} sample slides will be removed")
    remove_all_slides(prs)
    print(f"  layouts available: {len(prs.slide_layouts)}")

    builders = [
        slide_01_title,
        slide_02_what_it_is,
        slide_03_opportunity,
        slide_04_competitive,
        slide_05_strategy_section,
        slide_06_states_top,
        slide_07_states_mid,
        slide_08_states_bottom,
        slide_09_states_pass,
        slide_10_architecture,
        slide_11_match_reuse,
        slide_12_sprint_plan,
        slide_13_compliance,
        slide_14_demo,
        slide_15_ask,
        slide_16_thanks,
    ]
    total = len(builders)
    for i, b in enumerate(builders, start=1):
        print(f"  building slide {i}/{total}: {b.__name__}")
        b(prs, i, total)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    post_process_zip(OUT)
    print(f"Wrote {OUT}")
    print(f"Final slide count: {len(prs.slides)}")


if __name__ == "__main__":
    main()
