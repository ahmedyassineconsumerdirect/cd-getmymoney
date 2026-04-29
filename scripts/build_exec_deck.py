"""Build the myReclaim executive PowerPoint from scratch.

Earlier version layered custom shapes over the corporate template's
master placeholders, which leaked through ("Click to add text",
"Chapter Name", dotted decoration). This version starts from a fresh
Presentation() and draws every chrome element with custom shapes —
no template inheritance, no placeholder hints.

High-level and engaging: 11 slides, big visuals, less prose, no
BlueNavy mention.

Usage:
    python scripts/build_exec_deck.py
Output:
    myReclaim-Exec-Deck.pptx (project root)
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


# Brand palette
SC_BLUE = RGBColor(0x28, 0x63, 0xC5)
SC_BLUE_DARK = RGBColor(0x1F, 0x4F, 0x9E)
SC_BLUE_LIGHT = RGBColor(0xE6, 0xEF, 0xFA)
SC_ORANGE = RGBColor(0xFC, 0x4C, 0x0B)
SC_ORANGE_DARK = RGBColor(0xD8, 0x3E, 0x07)
SC_AMBER = RGBColor(0xFF, 0xB3, 0x52)
SC_INK = RGBColor(0x0F, 0x17, 0x2A)
SC_INK_BODY = RGBColor(0x33, 0x41, 0x55)
SC_INK_MUTED = RGBColor(0x64, 0x74, 0x8B)
SC_BG_SUBTLE = RGBColor(0xF8, 0xFA, 0xFC)
SC_BG_CARD = RGBColor(0xFF, 0xFF, 0xFF)
SC_BORDER = RGBColor(0xE2, 0xE8, 0xF0)
SC_RED = RGBColor(0xE1, 0x1D, 0x48)
SC_GREEN = RGBColor(0x05, 0x96, 0x69)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT = PROJECT_ROOT / "myReclaim-Exec-Deck.pptx"


# =========================================================================
# Drawing primitives
# =========================================================================

def add_textbox(slide, x, y, w, h, text, font_size=18, bold=False,
                color=SC_INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = "Open Sans"
    return box


def add_rect(slide, x, y, w, h, fill, line=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.5)
    shp.shadow.inherit = False
    return shp


def add_round_rect(slide, x, y, w, h, fill, line=None, radius=0.18):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = radius
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.5)
    shp.shadow.inherit = False
    return shp


def add_pill(slide, x, y, w, h, text, fill, text_color, font_size=10):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.5
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    tf = shp.text_frame
    tf.margin_left = Inches(0.05); tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.02); tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    run = p.add_run(); run.text = text
    run.font.size = Pt(font_size); run.font.bold = True
    run.font.color.rgb = text_color; run.font.name = "Open Sans"
    return shp


def add_arrow_right(slide, x, y, w, h, color):
    arr = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                  Inches(x), Inches(y), Inches(w), Inches(h))
    arr.fill.solid(); arr.fill.fore_color.rgb = color
    arr.line.fill.background()
    arr.shadow.inherit = False
    return arr


def add_chrome(slide, n, total, footer_text="myReclaim · Confidential — Consumer Direct, Inc."):
    """Top thin bar + brand wordmark + slide number. Same on every content slide."""
    add_rect(slide, 0, 0, 13.33, 0.06, SC_BLUE)
    # smartcredit wordmark
    add_textbox(slide, 0.5, 0.18, 2.5, 0.36,
                "smartcredit", font_size=16, bold=True, color=SC_INK)
    # Slide number bottom-right
    add_textbox(slide, 12.4, 7.05, 0.8, 0.3,
                f"{n} / {total}", font_size=9, color=SC_INK_MUTED, align=PP_ALIGN.RIGHT)
    add_textbox(slide, 0.5, 7.05, 8.0, 0.3,
                footer_text, font_size=9, color=SC_INK_MUTED)


def blank_slide(prs):
    """Return a blank slide. Use the simplest layout and strip its placeholders."""
    layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
    slide = prs.slides.add_slide(layout)
    # Remove any inherited placeholder shapes for a truly blank canvas
    for ph in list(slide.placeholders):
        sp = ph._element
        sp.getparent().remove(sp)
    # Background fill
    add_rect(slide, 0, 0, 13.33, 7.5, SC_BG_SUBTLE)
    return slide


# =========================================================================
# Slide builders
# =========================================================================

def slide_01_title(prs, n, total):
    s = blank_slide(prs)
    # Big blue gradient block
    add_rect(s, 0, 0, 13.33, 7.5, WHITE)
    add_rect(s, 0, 0, 13.33, 4.6, SC_BG_SUBTLE)
    add_rect(s, 0, 0, 0.7, 7.5, SC_BLUE)
    # smartcredit wordmark
    add_textbox(s, 1.0, 0.5, 4.0, 0.45,
                "smartcredit", font_size=22, bold=True, color=SC_INK)
    # Eyebrow
    add_textbox(s, 1.0, 1.7, 11, 0.4,
                "PRODUCT PROPOSAL · MONEY",
                font_size=14, bold=True, color=SC_BLUE)
    # Big title
    add_textbox(s, 1.0, 2.2, 11, 1.6,
                "myReclaim",
                font_size=110, bold=True, color=SC_INK)
    # Tagline
    add_textbox(s, 1.0, 3.95, 11, 0.7,
                "Find money the state owes our members.\nAutomatically. Free.",
                font_size=28, color=SC_INK_BODY)
    # Bottom band with author
    add_rect(s, 0, 6.7, 13.33, 0.8, SC_INK)
    add_textbox(s, 1.0, 6.92, 12, 0.4,
                "Ahmed Yassine  ·  Consumer Direct, Inc.  ·  April 2026",
                font_size=12, color=WHITE)


def slide_02_hook(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    # Eyebrow
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "THE OPPORTUNITY",
                font_size=12, bold=True, color=SC_BLUE)
    # Big stat
    add_textbox(s, 0.5, 1.4, 12.5, 2.5,
                "$70B+",
                font_size=160, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 4.0, 12.5, 0.7,
                "estimated in unclaimed property nationwide. Some of it is reported in our members' names.",
                font_size=24, bold=True, color=SC_INK)
    # 3 mini facts — sourced from NAUPA FY2024 release (Oct 2024)
    facts = [
        ("~33M", "people may have property waiting to be claimed (NAUPA)"),
        ("$2,080", "average claim paid through MissingMoney.com (median $100, FY2024)"),
        ("Unique", "combination of verified-identity matching + alerts + free claim guidance"),
    ]
    box_w = 4.0; gap = 0.15; y0 = 5.3
    for i, (big, small) in enumerate(facts):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.4, WHITE, line=SC_BORDER, radius=0.04)
        add_textbox(s, x + 0.3, y0 + 0.18, box_w - 0.6, 0.7,
                    big, font_size=36, bold=True, color=SC_ORANGE)
        add_textbox(s, x + 0.3, y0 + 0.85, box_w - 0.6, 0.5,
                    small, font_size=12, color=SC_INK_BODY)


def slide_03_what_it_is(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT IT IS",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.2,
                "myReclaim is a free SmartCredit feature\nthat finds unclaimed money owed to our members.",
                font_size=32, bold=True, color=SC_INK)

    # Side-by-side: User experience flow
    # Left: What the member sees
    y = 3.1
    add_textbox(s, 0.5, y, 6.0, 0.4,
                "WHAT THE MEMBER EXPERIENCES",
                font_size=11, bold=True, color=SC_INK_MUTED)

    steps = [
        ("1", "We notify them inside SmartCredit",
         "\"Possible match found. The state may be holding property in your name.\""),
        ("2", "They review the possible matches",
         "Holder, type, amount range — laid out as cards. The state determines eligibility."),
        ("3", "We help them file with the state",
         "Prepare claim packet · route to official state portal · track status."),
    ]
    yy = y + 0.55
    for num, title, body in steps:
        add_round_rect(s, 0.5, yy, 6.0, 0.95, WHITE, line=SC_BORDER, radius=0.04)
        add_pill(s, 0.7, yy + 0.27, 0.45, 0.45, num, SC_BLUE, WHITE, font_size=14)
        add_textbox(s, 1.4, yy + 0.13, 4.9, 0.4,
                    title, font_size=14, bold=True, color=SC_INK)
        add_textbox(s, 1.4, yy + 0.5, 4.9, 0.4,
                    body, font_size=11, color=SC_INK_BODY)
        yy += 1.05

    # Right: schematic of a result card (no real PII)
    add_textbox(s, 7.0, y, 5.8, 0.4,
                "WHAT IT FEELS LIKE",
                font_size=11, bold=True, color=SC_INK_MUTED)
    # Card
    add_round_rect(s, 7.0, y + 0.55, 5.8, 3.3, WHITE, line=SC_BORDER, radius=0.04)
    add_textbox(s, 7.25, y + 0.7, 4.0, 0.4,
                "POSSIBLE MATCH", font_size=10, bold=True, color=SC_ORANGE)
    add_textbox(s, 7.25, y + 1.05, 5.4, 0.7,
                "Credit Balance",
                font_size=18, bold=True, color=SC_INK)
    add_textbox(s, 7.25, y + 1.55, 4.0, 0.4,
                "Reported by financial institution", font_size=11, bold=True, color=SC_INK_MUTED)
    add_pill(s, 11.4, y + 1.05, 1.1, 0.32,
             "STATE", SC_BLUE_LIGHT, SC_BLUE, font_size=9)
    # Amount (range — reflects actual data ingest model where amount may be range/undisclosed)
    add_textbox(s, 7.25, y + 2.05, 5.4, 0.9,
                "$100 – $499",
                font_size=36, bold=True, color=SC_ORANGE)
    add_textbox(s, 7.25, y + 2.95, 5.4, 0.4,
                "Matched on name + prior city / address",
                font_size=10, color=SC_INK_MUTED)
    # CTA
    add_pill(s, 7.25, y + 3.35, 2.4, 0.4,
             "Continue to official claim", SC_ORANGE, WHITE, font_size=10)
    add_textbox(s, 9.85, y + 3.4, 2.9, 0.4,
                "Not me", font_size=11, bold=True, color=SC_BLUE)
    # Disclosure
    add_textbox(s, 7.0, y + 4.0, 5.8, 0.5,
                "The state determines eligibility. Official state claims are free. SmartCredit does not guarantee approval.",
                font_size=8, color=SC_INK_MUTED)


def slide_04_why_we_win(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHY WE'RE THE ONES TO BUILD THIS",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "We already have the three hardest pieces.",
                font_size=32, bold=True, color=SC_INK)

    pieces = [
        ("01",
         "Verified member identity",
         "We already know who they are — name, addresses, DOB, verified at signup and consented for monitoring. No re-collection. No new PII surface.",
         SC_BLUE),
        ("02",
         "PrivacyMaster® matching engine",
         "Already in production scanning data brokers for member info. Fuzzy + phonetic name matching at scale. Same engine — myReclaim points it at a new corpus.",
         SC_ORANGE),
        ("03",
         "Snowflake warehouse",
         "Paid for, secured, audited, dbt-modeled. Adding myReclaim is a new schema — not new infrastructure or new vendor risk.",
         SC_BLUE_DARK),
    ]
    y = 3.0; gap = 0.25
    box_w = (13.33 - 1.0 - 2 * gap) / 3
    for i, (num, head, body, color) in enumerate(pieces):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y, box_w, 3.6, WHITE, line=SC_BORDER, radius=0.03)
        # Big number
        add_textbox(s, x + 0.3, y + 0.3, box_w - 0.6, 1.0,
                    num, font_size=54, bold=True, color=color)
        add_textbox(s, x + 0.3, y + 1.45, box_w - 0.6, 0.6,
                    head, font_size=18, bold=True, color=SC_INK)
        add_textbox(s, x + 0.3, y + 2.05, box_w - 0.6, 1.4,
                    body, font_size=12, color=SC_INK_BODY)

    # Bottom line
    add_rect(s, 0.5, 6.95, 12.3, 0.0, SC_BLUE)  # spacer
    add_textbox(s, 0.5, 6.85, 12.5, 0.4,
                "Translation: every other player in this space has to build at least one of these from scratch. We don't.",
                font_size=12, bold=True, color=SC_INK_MUTED, align=PP_ALIGN.CENTER)


def slide_05_data_strategy(prs, n, total):
    """Data ingestion priority — driven by SmartCredit customer concentration.

    Top 10 states cover ~70% of the customer base. Pairs each state's
    customer count with its ingest posture. Sourced from
    Customers_by_State.csv (Apr 2026) + state matrix research.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "DATA INGESTION · CUSTOMER-DRIVEN PRIORITY",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.9,
                "Where our members live. What each state lets us do.",
                font_size=26, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.1, 12.5, 0.45,
                "Top 10 customer states cover ~70% of the SmartCredit base. Four of the top five (FL, TX, GA, NY) need a state agreement before we can ingest at scale. CA is the only top-10 state with a clean public bulk feed — that's where the prototype starts.",
                font_size=11, color=SC_INK_MUTED)

    # Top-10 table from Customers_by_State.csv + matrix posture
    rows = [
        (1,  "FL", 65400,  "MANUAL",  SC_ORANGE,     "Registered FL rep path (atty/CPA/PI, Ch. 717). No cacheable bulk dataset confirmed."),
        (2,  "TX", 61414,  "REQUEST", SC_AMBER,      "Request-based dataset; enable only after written caching/redisplay approval."),
        (3,  "CA", 44222,  "BUILD",   SC_GREEN,      "Public CSV, updated Thursdays — prototype loaded 81M rows ✓"),
        (4,  "GA", 29566,  "REQUEST", SC_AMBER,      "CDR registration + background checks → weekly delimited file (>1 GB)"),
        (5,  "NY", 22137,  "REQUEST", SC_AMBER,      "Secure-FTP owner-name file, quarterly. Excludes amounts and tax IDs."),
        (6,  "IL", 16242,  "HANDOFF", SC_INK_MUTED,  "No public bulk feed confirmed. Assisted e-file via iCash."),
        (7,  "NC", 14404,  "HANDOFF", SC_INK_MUTED,  "No clean bulk feed confirmed; annual public PDFs exist."),
        (8,  "PA", 12290,  "HANDOFF", SC_INK_MUTED,  "No public bulk feed confirmed."),
        (9,  "NJ", 11856,  "HANDOFF", SC_INK_MUTED,  "No public bulk feed confirmed."),
        (10, "SC", 10534,  "HANDOFF", SC_INK_MUTED,  "No public bulk feed confirmed."),
    ]

    # Header strip
    y0 = 2.7
    add_rect(s, 0.5, y0, 12.3, 0.32, SC_INK)
    headers = [
        ("#",         0.6,  0.5),
        ("STATE",     1.15, 0.9),
        ("CUSTOMERS", 2.1,  1.6),
        ("INGEST",    3.85, 1.4),
        ("WHAT THAT MEANS", 5.4, 7.4),
    ]
    for label, x, w in headers:
        add_textbox(s, x, y0 + 0.06, w, 0.22,
                    label, font_size=9, bold=True, color=WHITE)

    # Body rows
    y = y0 + 0.32
    row_h = 0.36
    for i, (rank, state, customers, tier, color, note) in enumerate(rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 0.5, y, 12.3, row_h, bg)
        # Highlight CA row (the only ingestable top-10 state today)
        if state == "CA":
            add_rect(s, 0.5, y, 0.12, row_h, SC_GREEN)
        # Rank
        add_textbox(s, 0.6, y + 0.08, 0.5, 0.22,
                    f"{rank}", font_size=11, bold=True, color=SC_INK_MUTED)
        # State code
        add_textbox(s, 1.15, y + 0.06, 0.9, 0.24,
                    state, font_size=14, bold=True, color=SC_INK)
        # Customer count
        add_textbox(s, 2.1, y + 0.07, 1.6, 0.22,
                    f"{customers:,}", font_size=12, bold=True, color=SC_INK)
        # Tier badge
        add_pill(s, 3.85, y + 0.06, 1.05, 0.24,
                 tier, color, WHITE, font_size=8)
        # Note
        add_textbox(s, 5.4, y + 0.08, 7.4, 0.22,
                    note, font_size=10, color=SC_INK_BODY)
        y += row_h

    # Bottom callout — strategic insight
    add_round_rect(s, 0.5, 6.65, 12.3, 0.55, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 6.72, 12, 0.32,
                "Top-10 states = 288,065 customers (~70% of base, pending base-size confirmation).",
                font_size=12, bold=True, color=WHITE)
    add_textbox(s, 0.7, 7.0, 12, 0.22,
                "CA is the only top-10 state with a confirmed public bulk feed. Sprint 2 begins TX + NY data requests and GA CDR registration; bulk availability depends on state approval, terms, and legal sign-off.",
                font_size=10, color=RGBColor(0xCC, 0xDD, 0xFF))


def slide_06_architecture(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "DATA INGESTION ARCHITECTURE",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.8,
                "From state portals to the SmartCredit dashboard.",
                font_size=28, bold=True, color=SC_INK)

    arch = [
        ("State data\nsources", ["CA bulk CSV", "TX requested file",
                                  "NY SFTP quarterly", "GA registered file"],
         SC_BLUE),
        ("S3 landing", ["Versioned by date",
                         "ETag-aware fetch",
                         "Schema-change quarantine"],
         SC_ORANGE),
        ("Snowflake", ["Snowpipe auto-ingest",
                        "NAUPA III canonical schema",
                        "dbt models · row lineage"],
         SC_BLUE_DARK),
        ("myReclaim", ["Member identity → match",
                        "Results card list",
                        "State claim deep-link",
                        "Notification engine"],
         SC_BLUE),
    ]
    y = 2.6
    box_w = 2.85
    margin = 0.5
    spacing = 0.35
    for i, (title, items, color) in enumerate(arch):
        x = margin + i * (box_w + spacing)
        # card
        add_round_rect(s, x, y, box_w, 3.3, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y, box_w, 0.18, color)
        add_pill(s, x + 0.15, y + 0.32, 0.45, 0.45,
                 str(i + 1), color, WHITE, font_size=14)
        add_textbox(s, x + 0.7, y + 0.35, box_w - 0.7, 0.7,
                    title, font_size=15, bold=True, color=SC_INK)
        body = "\n".join("•  " + it for it in items)
        add_textbox(s, x + 0.25, y + 1.3, box_w - 0.4, 1.9,
                    body, font_size=11, color=SC_INK_BODY)
        if i < len(arch) - 1:
            add_arrow_right(s, x + box_w + 0.05, y + 1.4,
                            spacing - 0.1, 0.5, SC_INK_MUTED)

    # Bottom callout
    add_round_rect(s, 0.5, 6.2, 12.3, 0.85, SC_BG_CARD, line=SC_BORDER, radius=0.03)
    add_textbox(s, 0.7, 6.3, 12, 0.4,
                "Why Snowflake?",
                font_size=14, bold=True, color=SC_BLUE)
    add_textbox(s, 0.7, 6.65, 12, 0.4,
                "We already operate it. Adding myReclaim is a schema, not new infrastructure. Encryption, audit, dbt are already there.",
                font_size=12, color=SC_INK_BODY)


def slide_privacy_master(prs, n, total):
    """Background on PrivacyMaster — the trust precedent for myReclaim."""
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "THE TRUST PRECEDENT",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "We already do this — for a different problem.",
                font_size=30, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.15, 12.5, 0.5,
                "PrivacyMaster® is a SmartCredit member feature that auto-scans data brokers, businesses, and government sites for member information. When found, the member chooses Remove or Keep. We monitor compliance until the data is gone.",
                font_size=12, color=SC_INK_MUTED)

    # Three-column anatomy
    cols = [
        ("WHAT IT DOES TODAY",
         [("Auto-scan", "Hundreds of broker, business, and govt sources, on a schedule"),
          ("Alert", "Member gets notified inside SmartCredit when a match appears"),
          ("Choice", "Member instructs Remove or Keep on each finding"),
          ("Compliance", "We track the broker's removal timeline, 1–45 days")],
         SC_BLUE),
        ("WHAT MEMBERS TRUST US WITH",
         [("Identity", "Name, addresses, DOB, family — already in their SmartCredit profile"),
          ("Auto-monitoring", "Scanning happens whether or not they activate the feature"),
          ("Acting on findings", "Authorized to send Remove requests on their behalf"),
          ("Value", "Equivalent standalone services charge $15–$20 / month")],
         SC_ORANGE),
        ("WHAT myRECLAIM REUSES",
         [("Identity", "Same profile — no re-collection"),
          ("Auto-scan model", "Same scheduled scan, just a different corpus"),
          ("Alert pattern", "Same in-product notification UX"),
          ("Member choice", "Remove / Keep becomes Claim / Not me")],
         SC_BLUE_DARK),
    ]
    y = 2.8
    box_w = (13.33 - 1.0 - 2 * 0.2) / 3
    for i, (head, rows, color) in enumerate(cols):
        x = 0.5 + i * (box_w + 0.2)
        add_round_rect(s, x, y, box_w, 3.4, WHITE, line=SC_BORDER, radius=0.03)
        add_rect(s, x, y, box_w, 0.18, color)
        add_textbox(s, x + 0.25, y + 0.35, box_w - 0.5, 0.4,
                    head, font_size=11, bold=True, color=color)
        yy = y + 0.85
        for label, body in rows:
            add_textbox(s, x + 0.25, yy, 1.3, 0.3,
                        label, font_size=10, bold=True, color=SC_INK)
            add_textbox(s, x + 0.25, yy + 0.28, box_w - 0.5, 0.45,
                        body, font_size=9.5, color=SC_INK_BODY)
            yy += 0.62

    # Bottom callout
    add_round_rect(s, 0.5, 6.4, 12.3, 0.65, SC_BG_CARD, line=SC_BLUE, radius=0.03)
    add_textbox(s, 0.7, 6.5, 12, 0.32,
                "myReclaim is not a new product surface.",
                font_size=14, bold=True, color=SC_BLUE)
    add_textbox(s, 0.7, 6.78, 12, 0.3,
                "It's a different outcome from the same security envelope members have already opted into. Same engine, same alert pattern, new corpus, new value.",
                font_size=11, color=SC_INK_BODY)


def slide_pii_matching(prs, n, total):
    """The PII matching engine — same engine, same UX, different mission.

    Combines key trust-precedent points from the previous PrivacyMaster
    slide so this slide stands alone.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "THE PII MATCHING ENGINE",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Same engine members already trust. New mission.",
                font_size=28, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.15, 12.5, 0.45,
                "SmartCredit's PII matching engine already auto-scans data brokers, businesses, and government sites for member info. Members get an alert and choose Remove or Keep. myReclaim points the same engine at state unclaimed-property records — same auto-scan, same alert, same trust envelope.",
                font_size=11, color=SC_INK_MUTED)

    # Two cards: today / tomorrow with arrow between
    y = 2.95; col_w = 5.6; gap = 0.7

    # TODAY card
    add_round_rect(s, 0.5, y, col_w, 3.5, WHITE, line=SC_BORDER, radius=0.03)
    add_rect(s, 0.5, y, col_w, 0.18, SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.32, col_w - 0.4, 0.4,
                "TODAY · DATA-BROKER SCRUB",
                font_size=11, bold=True, color=SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.78, col_w - 0.4, 0.7,
                "Find data brokers exposing the member",
                font_size=17, bold=True, color=SC_INK)
    rows_today = [
        ("Input",         "SmartCredit member identity"),
        ("Engine",        "Fuzzy + phonetic name match (PII)"),
        ("Corpus",        "Hundreds of broker, business, gov sources"),
        ("Pattern",       "Auto-scan → alert → member chooses"),
        ("Member action", "Remove  /  Keep"),
    ]
    yy = y + 1.55
    for label, body in rows_today:
        add_textbox(s, 0.7, yy, 1.4, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, 2.15, yy, col_w - 1.7, 0.3, body, font_size=10.5, color=SC_INK_BODY)
        yy += 0.36

    # Arrow
    add_arrow_right(s, 0.5 + col_w + 0.15, y + 1.5, gap - 0.3, 0.6, SC_ORANGE)
    add_textbox(s, 0.5 + col_w + 0.05, y + 2.15, gap, 0.3,
                "same engine", font_size=9, bold=True, color=SC_ORANGE,
                align=PP_ALIGN.CENTER)

    # TOMORROW card
    x2 = 0.5 + col_w + gap
    add_round_rect(s, x2, y, col_w, 3.5, WHITE, line=SC_BLUE, radius=0.03)
    add_rect(s, x2, y, col_w, 0.18, SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.32, col_w - 0.4, 0.4,
                "TOMORROW · myReclaim",
                font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.78, col_w - 0.4, 0.7,
                "Find unclaimed money owed to the member",
                font_size=17, bold=True, color=SC_INK)
    rows_tomorrow = [
        ("Input",         "Same SmartCredit member identity"),
        ("Engine",        "Same PII matcher — no rebuild"),
        ("Corpus",        "State unclaimed-property records"),
        ("Pattern",       "Auto-scan → alert → member chooses"),
        ("Member action", "Claim  /  Not me"),
    ]
    yy = y + 1.55
    for label, body in rows_tomorrow:
        add_textbox(s, x2 + 0.2, yy, 1.4, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, x2 + 1.65, yy, col_w - 1.7, 0.3, body, font_size=10.5, color=SC_INK_BODY)
        yy += 0.36

    # Bottom callout
    add_round_rect(s, 0.5, 6.65, 12.3, 0.5, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 6.72, 12, 0.36,
                "myReclaim is not a new product surface — it's a different outcome from the same security envelope members already opted into.",
                font_size=12, bold=True, color=WHITE)


def slide_customer_match_results(prs, n, total):
    """Live match against the SmartCredit active-CA customer base.

    Numbers come from scripts/customer_match_fast.py run on Apr 29 2026
    against all four CA tiers (92.4M rows).
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT WE'D FIND TODAY · LIVE MATCH",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.95,
                "We matched 30,862 active CA customers against all four CA unclaimed tiers (92.4M records).",
                font_size=22, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.2, 12.5, 0.45,
                "Method: exact name match (FIRST LAST or LAST FIRST) — same matching logic the prototype uses, run via the indexed equality path. The state determines actual eligibility per record.",
                font_size=11, color=SC_INK_MUTED)

    # Headline metrics row — slightly compressed to make room for methodology
    headlines = [
        ("21,864",        "customers with ≥1 name match", SC_BLUE),
        ("70.8%",         "upper bound (name-only)",       SC_BLUE),
        ("9,054",         "high-confidence (1–5 records)", SC_GREEN),
        ("$324M",         "max value across all matches",  SC_ORANGE),
    ]
    box_w = 2.95; gap = 0.15; y0 = 2.7
    for i, (big, small, color) in enumerate(headlines):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.20, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y0, box_w, 0.13, color)
        add_textbox(s, x + 0.2, y0 + 0.22, box_w - 0.4, 0.7,
                    big, font_size=32, bold=True, color=color)
        add_textbox(s, x + 0.2, y0 + 0.85, box_w - 0.4, 0.32,
                    small, font_size=10, color=SC_INK_BODY)

    # Methodology row — how we matched + what production adds
    add_textbox(s, 0.5, 4.05, 12.5, 0.32,
                "HOW WE MATCHED · TRANSPARENCY", font_size=11, bold=True, color=SC_BLUE)
    method_cols = [
        ("Normalize",
         "UPPER(TRIM(name)). Collapse internal whitespace. Both customer and unclaimed-record names go through identical normalization.",
         SC_BLUE),
        ("Build key",
         "Per customer: \"FIRST LAST\" and \"LAST FIRST\". Both orderings tried — CA records use both styles.",
         SC_BLUE),
        ("Equality join",
         "owner_name_normalized = key. Uses ix_owner_normalized — 0.7s for 30,862 × 92.4M rows.",
         SC_GREEN),
        ("Production adds",
         "Phonetic (Soundex/Metaphone) · middle-name · last-4 SSN · DOB. Cuts false positives ~5×.",
         SC_ORANGE),
    ]
    mw = 2.95; mg = 0.15; my = 4.4
    for i, (label, body, color) in enumerate(method_cols):
        x = 0.5 + i * (mw + mg)
        add_round_rect(s, x, my, mw, 0.65, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, my, 0.10, 0.65, color)
        add_textbox(s, x + 0.20, my + 0.05, mw - 0.3, 0.22,
                    label, font_size=10, bold=True, color=color)
        add_textbox(s, x + 0.20, my + 0.27, mw - 0.3, 0.36,
                    body, font_size=8.5, color=SC_INK_BODY)

    # Distribution table — separates likely-true matches from common-name collisions
    add_textbox(s, 0.5, 5.2, 6.0, 0.32,
                "MATCH DISTRIBUTION", font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 5.50, 6.0, 0.28,
                "Distinct names cluster in the 1–5 record bucket — high-confidence matches.",
                font_size=10, color=SC_INK_MUTED)

    dist_rows = [
        ("1 record",        "3,266",   "$239K",  SC_GREEN, "High confidence"),
        ("2–5 records",     "5,788",   "$1.21M", SC_GREEN, "High confidence"),
        ("6–20 records",    "4,393",   "$3.50M", SC_AMBER, "Mixed — needs review"),
        ("20+ records",     "8,417",   "$319M",  SC_INK_MUTED, "Common-name collisions"),
    ]
    y = 5.85
    row_h = 0.27
    # Header row
    add_rect(s, 0.5, y, 6.0, 0.24, SC_INK)
    for label, x, w in [("Bucket", 0.6, 1.7), ("Customers", 2.4, 1.0), ("$ value", 3.55, 1.0), ("Note", 4.7, 1.7)]:
        add_textbox(s, x, y + 0.04, w, 0.18, label, font_size=9, bold=True, color=WHITE)
    y += 0.24
    for i, (bucket, custs, val, color, note) in enumerate(dist_rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 0.5, y, 6.0, row_h, bg)
        add_textbox(s, 0.6, y + 0.04, 1.7, 0.20, bucket, font_size=10, bold=True, color=SC_INK)
        add_textbox(s, 2.4, y + 0.04, 1.0, 0.20, custs, font_size=10, color=SC_INK_BODY)
        add_textbox(s, 3.55, y + 0.04, 1.0, 0.20, val, font_size=10, bold=True, color=color)
        add_textbox(s, 4.7, y + 0.04, 1.7, 0.20, note, font_size=9, color=SC_INK_MUTED)
        y += row_h

    # Per-tier breakdown
    add_textbox(s, 6.8, 5.2, 6.0, 0.32,
                "MATCHES BY TIER", font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 6.8, 5.50, 6.0, 0.28,
                "Tier 04 ($500+) carries 53% of the value despite 2% of records.",
                font_size=10, color=SC_INK_MUTED)
    tier_rows = [
        ("Tier 01",  "$0–$9.99",      "2,283,461", "$5.8M",   SC_INK_MUTED),
        ("Tier 02",  "$10–$99.99",    "1,622,140", "$57.9M",  SC_AMBER),
        ("Tier 03",  "$100–$499.99",  "425,201",   "$87.5M",  SC_ORANGE),
        ("Tier 04",  "$500+",         "97,787",    "$173.1M", SC_BLUE),
    ]
    y = 5.85
    add_rect(s, 6.8, y, 6.0, 0.24, SC_INK)
    for label, x, w in [("Tier", 6.9, 1.0), ("Range", 7.95, 1.4), ("Records", 9.45, 1.5), ("$ value", 11.05, 1.5)]:
        add_textbox(s, x, y + 0.04, w, 0.18, label, font_size=9, bold=True, color=WHITE)
    y += 0.24
    for i, (tier, rng, recs, val, color) in enumerate(tier_rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 6.8, y, 6.0, row_h, bg)
        add_textbox(s, 6.9, y + 0.04, 1.0, 0.20, tier, font_size=10, bold=True, color=color)
        add_textbox(s, 7.95, y + 0.04, 1.4, 0.20, rng, font_size=9, color=SC_INK_BODY)
        add_textbox(s, 9.45, y + 0.04, 1.5, 0.20, recs, font_size=10, color=SC_INK_BODY)
        add_textbox(s, 11.05, y + 0.04, 1.5, 0.20, val, font_size=10, bold=True, color=color)
        y += row_h

    # Bottom callout — the honest framing
    add_round_rect(s, 0.5, 7.10, 12.3, 0.36, SC_BLUE, radius=0.10)
    add_textbox(s, 0.7, 7.15, 12, 0.28,
                "70.8% is the upper bound. NAUPA baseline is ~14% of Americans. With the production PII matcher, expect 20–30% of our CA base.",
                font_size=11, bold=True, color=WHITE)


def slide_claim_integration(prs, n, total):
    """Filing the Claim — three concrete delivery models, verified against
    each state's regulator program (Apr 2026)."""
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "FILING THE CLAIM",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.95,
                "Three channels. E-file preferred. Mail when required. Rep when approved.",
                font_size=22, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.15, 12.5, 0.5,
                "Most states support online claim initiation, but some claims still require document upload, notarization, mailed forms, or manual review. v1 is assisted e-file. Mail packets via our ActionLetters service when states require physical paperwork. Filing on the member's behalf is a state-by-state regulatory unlock — not a technical one.",
                font_size=11, color=SC_INK_MUTED)

    # Three columns: today (e-file), today (mail fallback), tomorrow (rep filing)
    box_w = 4.0
    gap = 0.15
    y = 2.85
    box_h = 4.0   # bumped from 3.6 to give rows enough breathing room

    cards = [
        # v1 — Assisted e-file
        {"title": "v1 · DEFAULT",
         "subtitle": "Assisted e-file",
         "color": SC_GREEN,
         "rows": [
             ("Who submits", "The member"),
             ("How",         "We prep the packet · user submits via state portal"),
             ("We track",    "Claim ID + status entered by member or updated manually until state APIs exist"),
             ("Status",      "Ships Sprint 1 · every state with online filing"),
         ]},
        # v1 — Mail-packet fallback (already have this rail)
        {"title": "v1 · FALLBACK",
         "subtitle": "Mail packet via ActionLetters",
         "color": SC_AMBER,
         "rows": [
             ("Who submits", "Member; we generate the packet + mailing instructions"),
             ("How",         "If ActionLetters mails directly, legal must confirm it isn't representative filing"),
             ("When",        "States requiring notarized physical paperwork"),
             ("Status",      "Available now · same rail as credit-dispute mailers"),
         ]},
        # v2 — Representative filing
        {"title": "v2 · UNLOCK",
         "subtitle": "Registered representative",
         "color": SC_BLUE,
         "rows": [
             ("Who submits", "SmartCredit, on the member's behalf"),
             ("Where",       "GA (CDR) · FL (Ch. 717) · OH (Finder) · MI (locator)"),
             ("Fee",         "GA caps reps at 30% · we charge $0"),
             ("Status",      "Sprint 4+ once first state approves"),
         ]},
    ]
    for i, card in enumerate(cards):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y, box_w, box_h, WHITE, line=SC_BORDER, radius=0.03)
        add_rect(s, x, y, box_w, 0.18, card["color"])
        add_textbox(s, x + 0.25, y + 0.32, box_w - 0.5, 0.36,
                    card["title"], font_size=11, bold=True, color=card["color"])
        add_textbox(s, x + 0.25, y + 0.7, box_w - 0.5, 0.55,
                    card["subtitle"], font_size=14, bold=True, color=SC_INK)
        # Each row: label band (0.22 high) + body band (0.52 high) = 0.74 row pitch
        yy = y + 1.5
        for label, body in card["rows"]:
            add_textbox(s, x + 0.25, yy, 1.5, 0.22,
                        label, font_size=9, bold=True, color=SC_BLUE)
            add_textbox(s, x + 0.25, yy + 0.24, box_w - 0.5, 0.5,
                        body, font_size=10, color=SC_INK_BODY)
            yy += 0.6

    # Bottom callout
    add_round_rect(s, 0.5, 7.0, 12.3, 0.4, SC_BLUE, radius=0.1)
    add_textbox(s, 0.7, 7.05, 12, 0.32,
                "Members never pay. We never take a cut. Free reduces finder-fee risk — but representative filing still requires state-by-state approval, registration, and legal sign-off.",
                font_size=10, bold=True, color=WHITE)


def slide_08_roadmap(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "ROADMAP",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.9,
                "First state live in ~6 weeks.",
                font_size=32, bold=True, color=SC_INK)

    sprints = [
        ("Sprint 1", "California foundation",
         "CA ingest · Snowflake schema · matcher integration · alert UX",
         SC_GREEN),
        ("Sprint 2", "Permission outreach",
         "Texas data request · NY SFTP request · FL partnership conversations",
         SC_AMBER),
        ("Sprint 3", "Texas + New York live",
         "NY SFTP ingest (quarterly) · TX file ingest if approved",
         SC_AMBER),
        ("Sprint 4", "Georgia path",
         "CDR registration · background checks · legal approval · ingest",
         SC_AMBER),
        ("Sprint 5", "Florida path",
         "Partnership with registered claimant rep, OR written permission",
         SC_RED),
        ("Ongoing",  "Search-only handoff",
         "IL · PA · NJ · SC · AL · LA · VA · AZ · MD · TN · MS · NC",
         SC_INK_MUTED),
    ]
    y = 2.45
    row_h = 0.74
    for sprint, title, body, color in sprints:
        add_round_rect(s, 0.5, y, 12.3, row_h - 0.1, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, 0.5, y, 0.18, row_h - 0.1, color)
        add_textbox(s, 0.85, y + 0.08, 1.7, 0.3,
                    sprint, font_size=11, bold=True, color=color)
        add_textbox(s, 0.85, y + 0.32, 2.5, 0.32,
                    title, font_size=13, bold=True, color=SC_INK)
        add_textbox(s, 3.45, y + 0.2, 9.0, 0.4,
                    body, font_size=11, color=SC_INK_BODY)
        y += row_h


def slide_09_compliance(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "COMPLIANCE POSTURE",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Free + deep-link = no new regulatory exposure.",
                font_size=28, bold=True, color=SC_INK)

    items = [
        ("FCRA-safe",
         "Unclaimed-property search isn't a credit-reporting activity.",
         SC_GREEN),
        ("No finder license",
         "We don't take a fee on claims, so the 30-state finder regime doesn't apply.",
         SC_GREEN),
        ("No new PII surface",
         "Reuses identity records members already consented to.",
         SC_GREEN),
        ("State data ToS",
         "Restricted states are gated behind registration or skipped entirely.",
         SC_AMBER),
        ("State files claims",
         "Member is deep-linked to the state portal. We never hold claim funds.",
         SC_GREEN),
        ("Legal sign-off",
         "Every state ingestion has a legal review gate before going live.",
         SC_BLUE),
    ]
    cols = 3
    col_w = 4.0; gap_x = 0.15
    row_h = 1.55; gap_y = 0.2
    y0 = 2.6
    margin = 0.5
    for i, (head, body, color) in enumerate(items):
        col = i % cols; row = i // cols
        x = margin + col * (col_w + gap_x)
        y = y0 + row * (row_h + gap_y)
        add_round_rect(s, x, y, col_w, row_h, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y, 0.16, row_h, color)
        # Checkmark glyph
        add_textbox(s, x + 0.3, y + 0.18, 0.5, 0.5,
                    "✓", font_size=24, bold=True, color=color)
        add_textbox(s, x + 0.85, y + 0.22, col_w - 1.0, 0.45,
                    head, font_size=14, bold=True, color=SC_INK)
        add_textbox(s, x + 0.85, y + 0.7, col_w - 1.0, 0.8,
                    body, font_size=11, color=SC_INK_BODY)


def slide_10_built(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT'S ALREADY BUILT",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Working prototype. Real California data. Running today.",
                font_size=28, bold=True, color=SC_INK)

    # Big metrics
    metrics = [
        ("38M+",  "records indexed", SC_BLUE),
        ("$11B",  "in unclaimed property", SC_ORANGE),
        ("113s",  "to bulk-load 34M rows", SC_BLUE_DARK),
        ("<1s",   "to match a member by name", SC_AMBER),
    ]
    y0 = 2.7; box_w = 2.95; margin = 0.5; gap = 0.2
    for i, (big, small, color) in enumerate(metrics):
        x = margin + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.7, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y0, box_w, 0.15, color)
        add_textbox(s, x + 0.2, y0 + 0.35, box_w - 0.4, 0.95,
                    big, font_size=44, bold=True, color=color)
        add_textbox(s, x + 0.2, y0 + 1.3, box_w - 0.4, 0.4,
                    small, font_size=11, color=SC_INK_BODY)

    # What's running
    y2 = 4.7
    add_textbox(s, 0.5, y2, 12.5, 0.4,
                "WHAT'S RUNNING TODAY", font_size=11, bold=True, color=SC_BLUE)
    items = [
        "Web app — SmartCredit-themed search UI matching the production visual language",
        "Data — California State Controller bulk CSVs in DuckDB (Snowflake-shaped SQL)",
        "Match service — pluggable Protocol; production swaps in Privacy Master matcher",
        "Admin page — real ingestion stats, file load history, row counts",
    ]
    yy = y2 + 0.4
    for it in items:
        add_textbox(s, 0.7, yy, 12.0, 0.4,
                    "✓  " + it, font_size=12, color=SC_INK_BODY)
        yy += 0.32

    add_round_rect(s, 0.5, 6.55, 12.3, 0.5, SC_BLUE, radius=0.1)
    add_textbox(s, 0.7, 6.6, 12, 0.4,
                "Demo available now — ask any question, we'll search live.",
                font_size=12, bold=True, color=WHITE)


def slide_11_ask(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "THE ASK",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Approve the program. Staff it. Ship.",
                font_size=32, bold=True, color=SC_INK)

    # Resource ask
    add_round_rect(s, 0.5, 2.7, 6.0, 4.0, SC_BLUE, radius=0.04)
    add_textbox(s, 0.7, 2.95, 5.6, 0.5,
                "RESOURCE REQUEST", font_size=12, bold=True,
                color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 3.5, 5.6, 0.7,
                "1 data engineer", font_size=24, bold=True, color=WHITE)
    add_textbox(s, 0.7, 4.15, 5.6, 0.7,
                "1 product engineer", font_size=24, bold=True, color=WHITE)
    add_textbox(s, 0.7, 5.0, 5.6, 0.6,
                "~6 weeks to first state live",
                font_size=20, bold=True, color=WHITE)
    add_textbox(s, 0.7, 5.55, 5.6, 0.4,
                "~6 months to top-10 state coverage",
                font_size=14, color=RGBColor(0xCC, 0xDD, 0xFF))
    add_textbox(s, 0.7, 6.0, 5.6, 0.5,
                "No new infrastructure — Snowflake already paid for.",
                font_size=12, color=RGBColor(0xCC, 0xDD, 0xFF))

    # Outcomes
    add_textbox(s, 7.0, 2.7, 5.8, 0.4,
                "WHAT WE GET", font_size=12, bold=True, color=SC_BLUE)
    outcomes = [
        ("A first-of-its-kind feature", "No credit-monitoring competitor offers this."),
        ("Retention lift",                "Every found-money notification is a \"wow\" from us."),
        ("Acquisition hook",              "\"You may have unclaimed money. Free to find out.\""),
        ("Defensible moat",               "12+ months of state work others would have to repeat."),
    ]
    yy = 3.2
    for head, body in outcomes:
        add_round_rect(s, 7.0, yy, 5.8, 0.78, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, 7.0, yy, 0.16, 0.78, SC_ORANGE)
        add_textbox(s, 7.3, yy + 0.08, 5.4, 0.32,
                    head, font_size=14, bold=True, color=SC_INK)
        add_textbox(s, 7.3, yy + 0.42, 5.4, 0.34,
                    body, font_size=11, color=SC_INK_BODY)
        yy += 0.88

    add_rect(s, 0.5, 6.85, 12.3, 0.0, SC_INK)


def slide_compliance_guardrails(prs, n, total):
    """Compliance guardrails — explicit Will / Will Not commitments."""
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "COMPLIANCE GUARDRAILS",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.95,
                "Free for members. State-approved where required.",
                font_size=26, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.15, 12.5, 0.45,
                "Verified-identity matching, member consent, official state filing channels — and a clear list of things we will not do.",
                font_size=12, color=SC_INK_MUTED)

    # Two columns: WILL DO / WILL NOT DO
    will = [
        "Use official state files or state-approved data access only",
        "Get explicit member consent before matching and claim prep",
        "Route members to official state claim portals for v1",
        "Track claim ID + status inside SmartCredit (manual entry)",
        "File on members' behalf only where registered or approved",
        "Source-by-source data-use permissions; legal review per state",
    ]
    will_not = [
        "Scrape state portals or MissingMoney.com",
        "Guarantee a claim belongs to the member",
        "Charge a success fee or take a cut",
        "Submit claims without fresh user authorization",
        "Re-use credit-report-derived data without legal sign-off",
        "Store sensitive claim documents unless required and approved",
    ]

    y0 = 2.85; col_w = 6.0; gap = 0.3
    # Will-do card
    add_round_rect(s, 0.5, y0, col_w, 4.05, WHITE, line=SC_BORDER, radius=0.03)
    add_rect(s, 0.5, y0, col_w, 0.18, SC_GREEN)
    add_textbox(s, 0.7, y0 + 0.32, col_w - 0.4, 0.4,
                "WHAT WE WILL DO",
                font_size=12, bold=True, color=SC_GREEN)
    yy = y0 + 0.85
    for item in will:
        add_textbox(s, 0.85, yy, 0.3, 0.3, "✓",
                    font_size=14, bold=True, color=SC_GREEN)
        add_textbox(s, 1.2, yy + 0.02, col_w - 1.0, 0.5,
                    item, font_size=11, color=SC_INK_BODY)
        yy += 0.5

    # Will-not-do card
    x2 = 0.5 + col_w + gap
    add_round_rect(s, x2, y0, col_w, 4.05, WHITE, line=SC_BORDER, radius=0.03)
    add_rect(s, x2, y0, col_w, 0.18, SC_RED)
    add_textbox(s, x2 + 0.2, y0 + 0.32, col_w - 0.4, 0.4,
                "WHAT WE WILL NOT DO",
                font_size=12, bold=True, color=SC_RED)
    yy = y0 + 0.85
    for item in will_not:
        add_textbox(s, x2 + 0.15, yy, 0.3, 0.3, "✗",
                    font_size=14, bold=True, color=SC_RED)
        add_textbox(s, x2 + 0.5, yy + 0.02, col_w - 0.7, 0.5,
                    item, font_size=11, color=SC_INK_BODY)
        yy += 0.5

    # Bottom callout
    add_round_rect(s, 0.5, 7.05, 12.3, 0.4, SC_INK, radius=0.07)
    add_textbox(s, 0.7, 7.10, 12, 0.32,
                "Every state ingestion has a legal review gate. Every claim has a fresh consent. Every data source has documented terms.",
                font_size=11, bold=True, color=WHITE)


def slide_workflow_summary(prs, n, total):
    """Closing slide: the workflow that needs to happen, in order."""
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WORKFLOW · WHAT NEEDS TO HAPPEN NEXT",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.9,
                "From approval to first member alert.",
                font_size=28, bold=True, color=SC_INK)

    steps = [
        ("01",
         "Exec approval & resourcing",
         "Greenlight myReclaim. Assign 1 data engineer + 1 product engineer.",
         "Now",
         SC_BLUE),
        ("02",
         "California ingestion live",
         "Scheduled pull from sco.ca.gov → S3 → Snowflake. Canonical schema, dedupe, dbt models.",
         "Sprint 1 · ~6 weeks",
         SC_BLUE),
        ("03",
         "Plug in the PII matching engine",
         "Connect SmartCredit's existing identity matcher. Alert only on high-confidence matches (name + address/city/state). Suppress name-only matches.",
         "Sprint 1–2",
         SC_BLUE),
        ("04",
         "Assisted e-file + ActionLetters fallback shipped",
         "Member confirms a match. We prep packet → official state portal. Mail packet enabled only where legal approves the workflow.",
         "End of Sprint 2",
         SC_GREEN),
        ("05",
         "State outreach & registrations",
         "Request written permission for caching, matching, redisplay, retention, commercial use. File GA CDR; open TX, NY, FL conversations.",
         "Parallel · Sprint 2+",
         SC_AMBER),
        ("06",
         "Expand to top-5 states (as approved)",
         "TX + NY added pending data-request approval; GA pending CDR registration + legal sign-off. Member-driven submit via state portals.",
         "Q3–Q4 2026",
         SC_AMBER),
        ("07",
         "Tier 3 unlock — we file for the member",
         "First approved representative workflow. Show \"we filed for you\" only in states where SmartCredit (or partner) is authorized.",
         "Q4 2026 · Q1 2027",
         SC_ORANGE),
    ]

    # Layout: each row is 0.72in tall. Title and body are wide (8.7in) so
    # long step titles don't wrap into the body band. Title at y+0.06 with
    # height 0.28; body at y+0.36 with height 0.32 — ~0.04in gap, no overlap.
    y = 2.2
    row_h = 0.72
    for num, title, body, when, color in steps:
        add_round_rect(s, 0.5, y, 12.3, row_h - 0.06, WHITE, line=SC_BORDER, radius=0.03)
        add_rect(s, 0.5, y, 0.18, row_h - 0.06, color)
        # Number
        add_textbox(s, 0.85, y + 0.18, 0.65, 0.4,
                    num, font_size=18, bold=True, color=color)
        # Title — full content width so titles don't wrap
        add_textbox(s, 1.65, y + 0.06, 8.6, 0.30,
                    title, font_size=12, bold=True, color=SC_INK)
        # Body — same width as title, sits cleanly below
        add_textbox(s, 1.65, y + 0.36, 8.6, 0.32,
                    body, font_size=9.5, color=SC_INK_BODY)
        # When pill, vertically centered
        add_pill(s, 10.45, y + 0.22, 1.75, 0.30,
                 when, color, WHITE, font_size=9)
        y += row_h

    # Bottom callout (positioned just below last step)
    add_round_rect(s, 0.5, 7.27, 12.3, 0.20, SC_INK, radius=0.1)
    add_textbox(s, 0.7, 7.30, 12, 0.16,
                "First member alert in ~6 weeks. First \"we filed for you\" within ~9 months.",
                font_size=10, bold=True, color=WHITE)


def slide_12_thanks(prs, n, total):
    s = blank_slide(prs)
    add_rect(s, 0, 0, 13.33, 7.5, SC_INK)
    add_textbox(s, 0.5, 2.4, 12.3, 0.4,
                "myReclaim",
                font_size=20, bold=True, color=SC_ORANGE,
                align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 2.95, 12.3, 1.6,
                "Let's go find it.",
                font_size=88, bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 4.8, 12.3, 0.5,
                "Questions?  ·  Live demo?  ·  Sprint 1 starts Monday?",
                font_size=20, color=RGBColor(0xCC, 0xDD, 0xFF),
                align=PP_ALIGN.CENTER)
    add_textbox(s, 0.5, 6.3, 12.3, 0.4,
                "Ahmed Yassine  ·  ahmed@consumerdirect.com",
                font_size=13, color=RGBColor(0xCC, 0xDD, 0xFF),
                align=PP_ALIGN.CENTER)


# =========================================================================
# Main
# =========================================================================
def main():
    print("Building myReclaim exec deck (fresh, no template)...")
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # Slimmed deck (per Apr 29 review):
    #   - dropped slide_04_why_we_win, slide_privacy_master (key points
    #     incorporated into slide_pii_matching), slide_06_architecture,
    #     slide_08_roadmap, slide_09_compliance, slide_10_built,
    #     slide_11_ask, slide_12_thanks
    #   - renamed PrivacyMaster ↔ myReclaim to "PII Matching Engine"
    #   - revised data-strategy to "Data Ingestion"
    #   - redid claim-integration with verified state-by-state regulator facts
    #   - new closing: workflow summary
    builders = [
        slide_01_title,
        slide_02_hook,
        slide_03_what_it_is,
        slide_pii_matching,
        slide_05_data_strategy,
        slide_customer_match_results,  # NEW: live match against active CA customers
        slide_claim_integration,
        slide_compliance_guardrails,
        slide_workflow_summary,
    ]
    total = len(builders)
    for i, b in enumerate(builders, start=1):
        print(f"  slide {i}/{total}: {b.__name__}")
        b(prs, i, total)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))
    print(f"Wrote {OUT}  ({OUT.stat().st_size / 1024:.0f} KB, {len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
