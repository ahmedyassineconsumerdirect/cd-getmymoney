"""Build the GetMyMoney executive PowerPoint from scratch.

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
    implementation-guideline/GetMyMoney-Exec-Deck.pptx
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
OUT = PROJECT_ROOT / "implementation-guideline" / "GetMyMoney-Exec-Deck.pptx"


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


def add_chrome(slide, n, total, footer_text="GetMyMoney · Confidential — Consumer Direct, Inc."):
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
                "GetMyMoney",
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
                "WHAT IS UNCLAIMED PROPERTY?",
                font_size=12, bold=True, color=SC_BLUE)
    # Plain-English definition (the hero of the slide)
    add_textbox(s, 0.5, 1.3, 12.5, 1.2,
                "Money owed to you that the company holding it lost track of.",
                font_size=34, bold=True, color=SC_INK)
    # Sub-explanation
    add_textbox(s, 0.5, 2.6, 12.5, 1.1,
                "When a bank, employer, insurer, or utility can't reach the owner of an account or balance for a "
                "set period (typically 1–3 years), state law requires them to turn it over to the state. "
                "It sits there — in the owner's name — until someone claims it.",
                font_size=15, color=SC_INK_BODY)

    # Common sources — concrete examples so it clicks
    add_textbox(s, 0.5, 4.0, 12.5, 0.3,
                "COMMON SOURCES",
                font_size=10, bold=True, color=SC_BLUE)
    sources = [
        ("Bank accounts",       "Dormant savings, checking, CDs"),
        ("Uncashed paychecks",  "Final wages, commissions, bonuses"),
        ("Refunds & deposits",  "Utility, rent, insurance, retail"),
        ("Investments",         "Stock dividends, matured bonds, IRAs"),
    ]
    box_w = 3.0; gap = 0.13; y0 = 4.4
    for i, (title, body) in enumerate(sources):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.25, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y0, box_w, 0.08, SC_BLUE)
        add_textbox(s, x + 0.25, y0 + 0.22, box_w - 0.5, 0.35,
                    title, font_size=14, bold=True, color=SC_INK)
        add_textbox(s, x + 0.25, y0 + 0.62, box_w - 0.5, 0.55,
                    body, font_size=11, color=SC_INK_BODY)

    # Scale anchor — keep the $ context, but as a footnote not the hero
    add_round_rect(s, 0.5, 6.0, 12.3, 0.55, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 6.07, 12, 0.4,
                "Nationwide: $70B+ sitting with state treasurers · ~33M Americans have property waiting (NAUPA, FY2024)",
                font_size=12, bold=True, color=WHITE)


def slide_03_what_it_is(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT IT IS",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.2,
                "GetMyMoney is a free SmartCredit feature\nthat finds unclaimed money owed to our members.",
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
        ("3", "We hand them off to the state",
         "Deep-link to the official state claim portal with step-by-step instructions for filing."),
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
         "Already in production scanning data brokers for member info. Fuzzy + phonetic name matching at scale. Same engine — GetMyMoney points it at a new corpus.",
         SC_ORANGE),
        ("03",
         "Snowflake warehouse",
         "Paid for, secured, audited, dbt-modeled. Adding GetMyMoney is a new schema — not new infrastructure or new vendor risk.",
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

    Top 10 states cover ~68% of net actives (201,829 of 297,096). Pairs
    each state's net-actives count with its ingest posture. Sourced from
    SC Net Actives by State.csv (Apr 2026) + state matrix research.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "DATA INGESTION · CUSTOMER-DRIVEN PRIORITY",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.9,
                "No data feed = no alert. To notify a member, we need the data first.",
                font_size=22, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.1, 12.5, 0.45,
                "Top 10 = ~68% of SC net actives. CA · TX · GA · NY · FL = 5 paths to data (CSV, SIFT, DOR file, OSC SFTP, Sunshine Law PRR) → 158,054 members (~53% of base) actively alertable. IL/NC/NJ/OH need state outreach to confirm. PA, SC, WA, AZ, MA, MI are blind spots — no feed available + scraping is blocked or unlawful.",
                font_size=11, color=SC_INK_MUTED)

    # Top-10 table — verified data-feed posture (May 2026 portal/ToS survey)
    # FEED/PRR = data acquirable → active alert possible.
    # OUTREACH = no feed surfaced; written request to treasurer untested.
    # BLIND = no feed AND scraping blocked/unlawful → cannot alert these members.
    rows = [
        (1,  "FL", 48436,  "PRR",      SC_ORANGE,     "Ch. 119 Sunshine Law PRR → owner-name list from DFS. Recurring possible."),
        (2,  "TX", 45670,  "FEED",     SC_AMBER,      "SIFT bulk feed via PI license + written request to Comptroller."),
        (3,  "CA", 31110,  "FEED",     SC_GREEN,      "Free public CSV updated Thursdays — already ingested (92.4M rows) ✓"),
        (4,  "GA", 18837,  "FEED",     SC_AMBER,      "Weekly delimited file via written DOR request."),
        (5,  "NY", 15001,  "FEED",     SC_AMBER,      "Secure-FTP quarterly TXT via OSC. PII stays internal."),
        (6,  "IL", 10536,  "OUTREACH", SC_INK_MUTED,  "No feed surfaced. Need to ask iL Treasurer for a bulk option."),
        (7,  "NC",  9549,  "OUTREACH", SC_INK_MUTED,  "No feed surfaced. Need to ask NC Treasurer."),
        (8,  "NJ",  8526,  "OUTREACH", SC_INK_MUTED,  "No feed surfaced. Need to ask NJ Treasury."),
        (9,  "PA",  8172,  "BLIND",    SC_RED,        "Anti-bot/anti-AI policy + no feed → can't acquire data. Members invisible."),
        (10, "SC",  5992,  "BLIND",    SC_RED,        "§30-2-50 bars commercial use of owner data + no feed → can't acquire."),
    ]

    # Header strip
    y0 = 2.7
    add_rect(s, 0.5, y0, 12.3, 0.32, SC_INK)
    headers = [
        ("#",         0.6,  0.5),
        ("STATE",     1.15, 0.9),
        ("NET ACTIVES", 2.1, 1.6),
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
    add_textbox(s, 0.7, 6.7, 12, 0.28,
                "5 paths to data (CA · TX · GA · NY · FL) = 158K members (~53% of base) actively alertable. PA & SC are blind spots — those members never see a match.",
                font_size=11, bold=True, color=WHITE)
    add_textbox(s, 0.7, 6.95, 12, 0.22,
                "CA live today. TX/GA/NY unlock via written state request. FL via Ch. 119 PRR. IL/NC/NJ need treasurer outreach to confirm path.",
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
        ("GetMyMoney", ["Member identity → match",
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
                "We already operate it. Adding GetMyMoney is a schema, not new infrastructure. Encryption, audit, dbt are already there.",
                font_size=12, color=SC_INK_BODY)


def slide_privacy_master(prs, n, total):
    """Background on PrivacyMaster — the trust precedent for GetMyMoney."""
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
        ("WHAT GETMYMONEY REUSES",
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
                "GetMyMoney is not a new product surface.",
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
                "SmartCredit's PII matching engine already auto-scans data brokers, businesses, and government sites for member info. Members get an alert and choose Remove or Keep. GetMyMoney points the same engine at state unclaimed-property records — same auto-scan, same alert, same trust envelope.",
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
                "TOMORROW · GetMyMoney",
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
                "GetMyMoney is not a new product surface — it's a different outcome from the same security envelope members already opted into.",
                font_size=12, bold=True, color=WHITE)


def slide_customer_match_results(prs, n, total):
    """Live match against SC net actives in CA — name only (the ceiling).

    Aggregate $ and record counts are intentionally not headlined: they're
    inflated by common-name collisions. Coverage % is the honest takeaway;
    the next slide adds city for the defensible view.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT WE'D FIND TODAY · NAME ONLY",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.95,
                "We matched 31,110 net actives CA · SmartCredit against all four CA unclaimed tiers (92.4M records).",
                font_size=20, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.2, 12.5, 0.45,
                "Matching on name only.",
                font_size=10, color=SC_INK_MUTED)

    # Headline metrics row — same shape as slide 7, name-only numbers
    headlines = [
        ("23,166", "net actives matched (name only)",       SC_BLUE),
        ("74.5%",  "of 31,110 net actives CA · SmartCredit", SC_BLUE),
        ("2.3M",   "property records matched",               SC_ORANGE),
        ("$172M",  "estimated value across all matches",     SC_ORANGE),
    ]
    box_w = 2.95; gap = 0.15; y0 = 2.85
    for i, (big, small, color) in enumerate(headlines):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.55, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y0, box_w, 0.15, color)
        add_textbox(s, x + 0.2, y0 + 0.3, box_w - 0.4, 0.85,
                    big, font_size=36, bold=True, color=color)
        add_textbox(s, x + 0.2, y0 + 1.1, box_w - 0.4, 0.4,
                    small, font_size=10, color=SC_INK_BODY)

    # Single centered table — net actives by total $ owed (name only)
    add_textbox(s, 2.5, 4.65, 8.3, 0.35,
                "NET ACTIVES BY TOTAL OWED (name only)", font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 2.5, 4.97, 8.3, 0.3,
                "Each net active placed in one bucket by the SUM of their matched records. Add up to 23,166.",
                font_size=10, color=SC_INK_MUTED)

    bucket_rows = [
        ("$0–$9.99",     "2,774",  "$9K",     "$3",      SC_INK_MUTED),
        ("$10–$99.99",   "4,526",  "$198K",   "$44",     SC_GREEN),
        ("$100–$499.99", "4,317",  "$1.06M",  "$245",    SC_AMBER),
        ("$500+",        "11,549", "$171M",   "$14,814", SC_BLUE),
    ]
    y = 5.4
    row_h = 0.34
    add_rect(s, 2.5, y, 8.3, 0.28, SC_INK)
    bucket_cols = [
        ("Total owed",       2.6,  1.9),
        ("Net actives",      4.7,  1.6),
        ("Bucket total",     6.5,  1.9),
        ("$ per net active", 8.6,  2.1),
    ]
    for label, x, w in bucket_cols:
        add_textbox(s, x, y + 0.05, w, 0.22, label, font_size=10, bold=True, color=WHITE)
    y += 0.28
    for i, (bucket_range, custs, total_, per_cust, color) in enumerate(bucket_rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 2.5, y, 8.3, row_h, bg)
        add_textbox(s, 2.6, y + 0.07, 1.9, 0.24, bucket_range, font_size=11, bold=True, color=color)
        add_textbox(s, 4.7, y + 0.07, 1.6, 0.24, custs, font_size=11, color=SC_INK_BODY)
        add_textbox(s, 6.5, y + 0.07, 1.9, 0.24, total_, font_size=11, bold=True, color=color)
        add_textbox(s, 8.6, y + 0.07, 2.1, 0.24, per_cust, font_size=11, color=color)
        y += row_h

    # Bottom callout — flag that name-only is the ceiling
    add_round_rect(s, 0.5, 7.0, 12.3, 0.45, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 7.05, 12, 0.32,
                "Name-only is the upper bound — common names inflate the totals. Next slide adds city for the defensible view.",
                font_size=11, bold=True, color=WHITE)


def slide_customer_match_with_city(prs, n, total):
    """Same cohort as the prior slide, but join key adds city.

    Numbers from scripts/customer_match_with_city.py — equality join
    on owner_name_normalized = LAST FIRST AND last_known_city = city.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "WHAT WE'D FIND TODAY · NAME + CITY MATCH",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.95,
                "We matched 31,110 net actives CA · SmartCredit against all four CA unclaimed tiers (92.4M records).",
                font_size=20, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.2, 12.5, 0.45,
                "Matching on name and city.",
                font_size=10, color=SC_INK_MUTED)

    # Headline metrics row — defensible numbers with city filter
    headlines = [
        ("11,958", "net actives matched (name + city)",     SC_BLUE),
        ("38.4%",  "of 31,110 net actives CA · SmartCredit", SC_BLUE),
        ("69K",    "property records matched",               SC_ORANGE),
        ("$5.04M", "estimated value across all matches",     SC_ORANGE),
    ]
    box_w = 2.95; gap = 0.15; y0 = 2.85
    for i, (big, small, color) in enumerate(headlines):
        x = 0.5 + i * (box_w + gap)
        add_round_rect(s, x, y0, box_w, 1.55, WHITE, line=SC_BORDER, radius=0.04)
        add_rect(s, x, y0, box_w, 0.15, color)
        add_textbox(s, x + 0.2, y0 + 0.3, box_w - 0.4, 0.85,
                    big, font_size=36, bold=True, color=color)
        add_textbox(s, x + 0.2, y0 + 1.1, box_w - 0.4, 0.4,
                    small, font_size=10, color=SC_INK_BODY)

    # Single centered table — net actives by total $ owed
    add_textbox(s, 2.5, 4.65, 8.3, 0.35,
                "NET ACTIVES BY TOTAL OWED (name + city)", font_size=11, bold=True, color=SC_BLUE)
    add_textbox(s, 2.5, 4.97, 8.3, 0.3,
                "Each net active placed in one bucket by the SUM of their matched records. Add up to 11,958.",
                font_size=10, color=SC_INK_MUTED)
    bucket_rows = [
        ("$0–$9.99",     "3,684",  "$11K",    "$3",      SC_INK_MUTED),
        ("$10–$99.99",   "4,395",  "$174K",   "$40",     SC_GREEN),
        ("$100–$499.99", "2,368",  "$534K",   "$225",    SC_AMBER),
        ("$500+",        "1,511",  "$4.32M",  "$2,859",  SC_BLUE),
    ]
    y = 5.4
    row_h = 0.34
    add_rect(s, 2.5, y, 8.3, 0.28, SC_INK)
    bucket_cols = [
        ("Total owed",       2.6,  1.9),
        ("Net actives",      4.7,  1.6),
        ("Bucket total",     6.5,  1.9),
        ("$ per net active", 8.6,  2.1),
    ]
    for label, x, w in bucket_cols:
        add_textbox(s, x, y + 0.05, w, 0.22, label, font_size=10, bold=True, color=WHITE)
    y += 0.28
    for i, (bucket_range, custs, total_, per_cust, color) in enumerate(bucket_rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 2.5, y, 8.3, row_h, bg)
        add_textbox(s, 2.6, y + 0.07, 1.9, 0.24, bucket_range, font_size=11, bold=True, color=color)
        add_textbox(s, 4.7, y + 0.07, 1.6, 0.24, custs, font_size=11, color=SC_INK_BODY)
        add_textbox(s, 6.5, y + 0.07, 1.9, 0.24, total_, font_size=11, bold=True, color=color)
        add_textbox(s, 8.6, y + 0.07, 2.1, 0.24, per_cust, font_size=11, color=color)
        y += row_h

    # Bottom callout — what the city filter buys us
    add_round_rect(s, 0.5, 7.0, 12.3, 0.45, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 7.05, 12, 0.32,
                "Adding city collapses 23,166 → 11,958 matched and $172M → $5.04M — the defensible floor before production PII (DOB, SSN-last-4, full address).",
                font_size=11, bold=True, color=WHITE)


def slide_next_steps(prs, n, total):
    """Next steps — engage legal to unlock the top 5 states.

    The prototype shows what's possible against CA's public CSV.
    Scaling beyond that is a regulatory unlock, not a technical one.
    Each top-5 state has a specific posture; legal's job is to open
    the right door for each.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "NEXT STEPS",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Engage legal — unlock the top 5 states where our members live.",
                font_size=26, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.2, 12.5, 0.5,
                "v1 is alert + deep-link only — we surface the match, the member files on the state's official portal. We need DATA, not filing rights. Legal's job per state: secure written caching/redisplay approval for the owner-name data, nothing more.",
                font_size=11, color=SC_INK_MUTED)

    # Top-5 action cards — each with state, posture, the specific legal ask
    rows = [
        (1, "FL", 48436, "PRR",     SC_ORANGE,
         "File Ch. 119 Sunshine Law records request to FL DFS for owner-name list (records are public under Ch. 119). Confirm fee. No Ch. 717 atty/CPA/PI registration needed — we're not filing on behalf of anyone."),
        (2, "TX", 45670, "REQUEST", SC_AMBER,
         "Submit bulk dataset request to up.dbrequests@cpa.texas.gov (company name, address, phone). Texas PI license may apply to the bulk-data request itself — confirm with Comptroller. Secure written approval for caching, matching, and redisplay."),
        (3, "CA", 31110, "BUILD",   SC_GREEN,
         "Already ingestible — free public CSV in production. Legal sign-off needed on commercial caching + in-product redisplay terms before launch. Lowest-friction state."),
        (4, "GA", 18837, "REQUEST", SC_AMBER,
         "Request the weekly delimited owner-name file from GA DOR. No CDR registration needed under alert-only (CDR is for filing on behalf). Secure written approval for caching/redisplay."),
        (5, "NY", 15001, "REQUEST", SC_AMBER,
         "Submit owner-name file request to OSC (secure-FTP TXT, quarterly). File excludes amounts and tax IDs. Get written caching/redisplay approval — member PII stays internal."),
    ]

    # Header strip
    y0 = 2.85
    add_rect(s, 0.5, y0, 12.3, 0.32, SC_INK)
    headers = [
        ("#",                0.6,  0.5),
        ("STATE",            1.15, 0.9),
        ("NET ACTIVES",      2.1,  1.6),
        ("POSTURE",          3.85, 1.05),
        ("LEGAL ACTION",     5.05, 7.7),
    ]
    for label, x, w in headers:
        add_textbox(s, x, y0 + 0.06, w, 0.22,
                    label, font_size=9, bold=True, color=WHITE)

    # Body rows
    y = y0 + 0.32
    row_h = 0.74
    for i, (rank, state, customers, tier, color, action) in enumerate(rows):
        bg = SC_BG_SUBTLE if i % 2 == 0 else SC_BG_CARD
        add_rect(s, 0.5, y, 12.3, row_h, bg)
        # Rank
        add_textbox(s, 0.6, y + 0.27, 0.5, 0.22,
                    f"{rank}", font_size=12, bold=True, color=SC_INK_MUTED)
        # State code
        add_textbox(s, 1.15, y + 0.24, 0.9, 0.28,
                    state, font_size=16, bold=True, color=SC_INK)
        # Net actives count
        add_textbox(s, 2.1, y + 0.27, 1.6, 0.22,
                    f"{customers:,}", font_size=13, bold=True, color=SC_INK)
        # Posture pill
        add_pill(s, 3.85, y + 0.24, 1.05, 0.28,
                 tier, color, WHITE, font_size=9)
        # Legal action description
        add_textbox(s, 5.05, y + 0.07, 7.7, row_h - 0.14,
                    action, font_size=10, color=SC_INK_BODY)
        y += row_h

    # Bottom callout — own this. timeline.
    add_round_rect(s, 0.5, 7.0, 12.3, 0.45, SC_BLUE, radius=0.07)
    add_textbox(s, 0.7, 7.05, 12, 0.32,
                "Owner: Legal · Goal: written data-use approval per state in 30 days · Output: go/no-go matrix to unlock the next ingest tier. We need data, not filing rights.",
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
         "Greenlight GetMyMoney. Assign 1 data engineer + 1 product engineer.",
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
                "GetMyMoney",
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


def slide_compliance_findings(prs, n, total):
    """Compliance research findings — headline conclusions from the full
    legal-team memo at docs/handoff/compliance-research-myreclaim.md.

    Spans FCRA, GLBA, FTC/CFPB UDAAP, TSR §310.4(a)(3), TCPA, 19+ state
    privacy laws, and the 50-state paid-finder patchwork. This slide
    surfaces only the load-bearing constraints + the single open question.
    """
    s = blank_slide(prs)
    add_chrome(s, n, total)

    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "COMPLIANCE RESEARCH",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.55,
                "v1 is a notification feature, not a recovery service.",
                font_size=24, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 1.85, 12.5, 0.4,
                "Three architectural decisions clear the bulk of the legal surface. The remaining constraint is data acquisition — without a feed, we can't alert a member because we don't know they have a match. Full compliance memo available from Legal.",
                font_size=10, color=SC_INK_MUTED)

    # Row 1: three non-negotiable architecture cards
    y0 = 2.4
    card_h = 1.65
    cards = [
        ("ALERT + DEEP LINK ONLY",
         "Surface the match. Embed a deep link. The member files on the state's official portal.",
         "Eliminates TSR §310.4(a)(3), FL Ch. 717 / GA CDR registration, false-claim and tort exposure. State paid-finder statutes mostly defanged.",
         SC_BLUE),
        ("BUNDLE, DON'T SURCHARGE",
         "No %-of-recovery, no upfront fee, no affiliate or success bonus. UP alerts are free in SmartCredit.",
         "Removes any \"fee for locating\" hook in state finder statutes. Avoids ROSCA negative-option stack.",
         SC_GREEN),
        ("NEVER HOLD FUNDS",
         "State pays the consumer direct. SmartCredit is never in the money path.",
         "Avoids 49-state money-transmitter licensure. GA §44-12-224 explicitly forbids holding funds.",
         SC_ORANGE),
    ]
    col_w = 4.05
    gap = 0.10
    x = 0.5
    for title, lead, why, accent in cards:
        add_round_rect(s, x, y0, col_w, card_h, WHITE, line=SC_BORDER, radius=0.05)
        add_rect(s, x, y0, col_w, 0.16, accent)
        add_textbox(s, x + 0.18, y0 + 0.24, col_w - 0.36, 0.28,
                    title, font_size=12, bold=True, color=accent)
        add_textbox(s, x + 0.18, y0 + 0.58, col_w - 0.36, 0.50,
                    lead, font_size=10.5, bold=True, color=SC_INK)
        add_textbox(s, x + 0.18, y0 + 1.12, col_w - 0.36, 0.50,
                    why, font_size=9, color=SC_INK_MUTED)
        x += col_w + gap

    # Row 2: state gates (left) + open question / top risks (right)
    y1 = 4.20
    state_w = 7.0
    gates_h = 2.35

    # State gates panel
    add_round_rect(s, 0.5, y1, state_w, gates_h, WHITE, line=SC_BORDER, radius=0.05)
    add_rect(s, 0.5, y1, state_w, 0.18, SC_INK)
    add_textbox(s, 0.7, y1 + 0.30, state_w - 0.4, 0.28,
                "STATE GATES", font_size=11, bold=True, color=SC_INK)

    gates = [
        ("CA · TX · GA · NY · FL", "ALERTABLE", SC_GREEN,
         "Data feed (or Ch. 119 PRR for FL) → match → alert + deep link."),
        ("IL · NC · NJ · OH", "UNKNOWN", SC_AMBER,
         "No feed surfaced. Treasurer outreach needed to confirm path."),
        ("PA", "BLIND", SC_RED,
         "Anti-bot/anti-AI policy + no feed → can't acquire data."),
        ("SC · WA · AZ", "BLIND", SC_RED,
         "Statute bars commercial use of owner-name data + no feed."),
        ("MA · MI", "BLIND", SC_RED,
         "Cloudflare-blocked portal + no public feed → no data path."),
    ]
    yy = y1 + 0.55
    row_h = 0.32
    for state, pill, color, body in gates:
        add_textbox(s, 0.7, yy, 2.4, row_h,
                    state, font_size=10.5, bold=True, color=SC_INK)
        add_pill(s, 3.15, yy + 0.03, 1.10, 0.26, pill, color, WHITE, font_size=8)
        add_textbox(s, 4.35, yy + 0.02, state_w - 3.95, row_h,
                    body, font_size=9, color=SC_INK_BODY)
        yy += row_h

    # Open question + top risks panel
    x2 = 0.5 + state_w + 0.15
    q_w = 12.83 - x2 - 0.5
    add_round_rect(s, x2, y1, q_w, gates_h, WHITE, line=SC_BORDER, radius=0.05)
    add_rect(s, x2, y1, q_w, 0.18, SC_ORANGE)
    add_textbox(s, x2 + 0.20, y1 + 0.26, q_w - 0.4, 0.28,
                "LOAD-BEARING OPEN QUESTION", font_size=11, bold=True, color=SC_ORANGE)
    add_textbox(s, x2 + 0.20, y1 + 0.60, q_w - 0.4, 0.70,
                "Does a flat-subscription credit-monitoring service that surfaces UP matches (with no separate UP fee) escape NY APL §1416 / CCP §1582 / equivalents?",
                font_size=10, bold=True, color=SC_INK)
    add_textbox(s, x2 + 0.20, y1 + 1.32, q_w - 0.4, 0.40,
                "No case law on point. Needs focused outside-counsel opinion before launch.",
                font_size=9, color=SC_INK_MUTED)

    add_rect(s, x2 + 0.20, y1 + 1.80, q_w - 0.4, 0.01, SC_BORDER)
    add_textbox(s, x2 + 0.20, y1 + 1.88, q_w - 0.4, 0.40,
                "Top HIGH risks: definitive-$$$ claims (Credit Karma) · implied gov't affiliation · unsubstantiated \"you may have $X\" · TCPA on found-money SMS.",
                font_size=8.5, color=SC_INK_BODY)

    # Footer callout
    add_round_rect(s, 0.5, 6.65, 12.3, 0.40, SC_INK, radius=0.07)
    add_textbox(s, 0.7, 6.72, 12, 0.30,
                "30 risk-rated findings · 18 open questions · 50-state paid-finder table · ~80 source links. Owner: Legal. Decision: ratify v1 (alert + deep-link / bundle / no-funds) + outside-counsel opinion on subscription characterization.",
                font_size=10, bold=True, color=WHITE)


# =========================================================================
# Main
# =========================================================================
def main():
    print("Building GetMyMoney exec deck (fresh, no template)...")
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # Slimmed deck (per Apr 29 review):
    #   - dropped slide_04_why_we_win, slide_privacy_master (key points
    #     incorporated into slide_pii_matching), slide_06_architecture,
    #     slide_08_roadmap, slide_09_compliance, slide_10_built,
    #     slide_11_ask, slide_12_thanks
    #   - renamed PrivacyMaster ↔ GetMyMoney to "PII Matching Engine"
    #   - revised data-strategy to "Data Ingestion"
    #   - redid claim-integration with verified state-by-state regulator facts
    #   - new closing: workflow summary
    builders = [
        slide_01_title,
        slide_02_hook,
        slide_03_what_it_is,
        slide_pii_matching,
        slide_05_data_strategy,
        slide_customer_match_results,
        slide_customer_match_with_city,
        slide_next_steps,
        slide_compliance_findings,
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
