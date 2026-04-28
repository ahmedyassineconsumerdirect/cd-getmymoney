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
    # smartcredit BETA wordmark
    add_textbox(slide, 0.5, 0.18, 2.0, 0.36,
                "smartcredit", font_size=16, bold=True, color=SC_INK)
    add_textbox(slide, 1.85, 0.22, 0.9, 0.3,
                "BETA", font_size=11, bold=True, color=SC_BLUE)
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
    # smartcredit BETA mark
    add_textbox(s, 1.0, 0.5, 3.0, 0.45,
                "smartcredit", font_size=22, bold=True, color=SC_INK)
    add_textbox(s, 2.85, 0.55, 1.0, 0.4,
                "BETA", font_size=14, bold=True, color=SC_BLUE)
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
                "$70 billion",
                font_size=160, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 4.0, 12.5, 0.7,
                "is sitting in U.S. state treasuries — money our members are owed.",
                font_size=28, bold=True, color=SC_INK)
    # 3 mini facts
    facts = [
        ("1 in 7", "Americans has unclaimed property in their name"),
        ("~$200", "average household balance, growing every year"),
        ("0", "credit-monitoring competitors offer this today"),
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
         "\"You may have $X waiting. We found it for you.\""),
        ("2", "They review the matches",
         "Holder, amount, type — laid out as cards."),
        ("3", "They claim with the state",
         "One click → official state claim portal."),
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
                "MATCH FOUND", font_size=10, bold=True, color=SC_ORANGE)
    add_textbox(s, 7.25, y + 1.05, 5.4, 0.7,
                "Credit Balance",
                font_size=18, bold=True, color=SC_INK)
    add_textbox(s, 7.25, y + 1.55, 4.0, 0.4,
                "Holder financial institution", font_size=11, bold=True, color=SC_INK_MUTED)
    add_pill(s, 11.4, y + 1.05, 1.1, 0.32,
             "STATE", SC_BLUE_LIGHT, SC_BLUE, font_size=9)
    # Big amount
    add_textbox(s, 7.25, y + 2.05, 5.4, 0.9,
                "$ —",
                font_size=44, bold=True, color=SC_ORANGE)
    add_textbox(s, 7.25, y + 2.95, 5.4, 0.4,
                "Reported in member's name · last known city",
                font_size=10, color=SC_INK_MUTED)
    # CTA
    add_pill(s, 7.25, y + 3.35, 1.7, 0.4,
             "Claim →", SC_ORANGE, WHITE, font_size=11)
    add_textbox(s, 9.2, y + 3.4, 3.5, 0.4,
                "Not me", font_size=11, bold=True, color=SC_BLUE)


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
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "HOW WE GET THE DATA",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 0.9,
                "There's no MissingMoney API. We go state by state.",
                font_size=28, bold=True, color=SC_INK)
    add_textbox(s, 0.5, 2.1, 12.5, 0.5,
                "21 states ranked by data accessibility, member coverage, and legal posture. Four tiers, one playbook.",
                font_size=14, color=SC_INK_MUTED)

    # 4 tier swim lanes
    tiers = [
        ("BUILD",   "Public bulk — ingest now",
         ["CA"],
         "California publishes a full CSV on sco.ca.gov, refreshed weekly.",
         SC_GREEN),
        ("REQUEST", "Permission required",
         ["TX", "NY", "GA", "OH", "MI"],
         "Formal request to the state treasurer / department, plus ToS for caching and redisplay.",
         SC_AMBER),
        ("HANDOFF", "Deep-link only",
         ["IL", "PA", "NJ", "SC", "AL", "LA", "VA", "AZ", "MD", "TN", "MS", "MO", "NC"],
         "No public bulk. Surface in the UI, deep-link to the state's claim portal.",
         SC_INK_MUTED),
        ("BLOCKED", "Don't ingest",
         ["FL", "WA"],
         "FL portal explicitly forbids automation. WA prohibits commercial redistribution by statute.",
         SC_RED),
    ]
    y = 2.85
    row_h = 1.0
    for tier_name, desc, states, body, color in tiers:
        # Card
        add_round_rect(s, 0.5, y, 12.3, row_h - 0.1, WHITE, line=SC_BORDER, radius=0.03)
        # Color rail
        add_rect(s, 0.5, y, 0.18, row_h - 0.1, color)
        # Tier badge
        add_pill(s, 0.85, y + 0.18, 1.3, 0.36, tier_name, color, WHITE, font_size=11)
        add_textbox(s, 0.85, y + 0.55, 2.0, 0.32,
                    desc, font_size=11, color=SC_INK_MUTED)
        # State chips
        x = 2.6
        for state_code in states:
            chip_w = 0.42
            add_round_rect(s, x, y + 0.32, chip_w, 0.36,
                           WHITE, line=color, radius=0.2)
            add_textbox(s, x, y + 0.36, chip_w, 0.3,
                        state_code, font_size=10, bold=True,
                        color=color, align=PP_ALIGN.CENTER)
            x += chip_w + 0.08
        # Body
        add_textbox(s, 2.6, y + 0.7, 10.0, 0.3,
                    body, font_size=10, color=SC_INK_BODY)
        y += row_h


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


def slide_07_match_reuse(prs, n, total):
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "PRIVACYMASTER ↔ myRECLAIM",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Same engine. Same UX pattern. Inverted purpose.",
                font_size=28, bold=True, color=SC_INK)

    # Two cards: today / tomorrow with arrow between
    y = 2.7; col_w = 5.6; gap = 0.7
    # TODAY
    add_round_rect(s, 0.5, y, col_w, 3.7, WHITE, line=SC_BORDER, radius=0.03)
    add_rect(s, 0.5, y, col_w, 0.18, SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.35, col_w - 0.4, 0.45,
                "TODAY · PrivacyMaster®",
                font_size=12, bold=True, color=SC_INK_MUTED)
    add_textbox(s, 0.7, y + 0.85, col_w - 0.4, 0.7,
                "Find data brokers exposing the member",
                font_size=18, bold=True, color=SC_INK)
    rows_today = [
        ("Input",  "SmartCredit member identity"),
        ("Engine", "Fuzzy + phonetic name match"),
        ("Corpus", "Data-broker exposure database"),
        ("Member action", "Remove  /  Keep"),
    ]
    yy = y + 1.7
    for label, body in rows_today:
        add_textbox(s, 0.7, yy, 1.2, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, 1.95, yy, col_w - 1.5, 0.3, body, font_size=11, color=SC_INK_BODY)
        yy += 0.45

    # Arrow
    add_arrow_right(s, 0.5 + col_w + 0.15, y + 1.6, gap - 0.3, 0.6, SC_ORANGE)
    add_textbox(s, 0.5 + col_w + 0.05, y + 2.25, gap, 0.3,
                "same engine", font_size=9, bold=True, color=SC_ORANGE,
                align=PP_ALIGN.CENTER)

    # TOMORROW
    x2 = 0.5 + col_w + gap
    add_round_rect(s, x2, y, col_w, 3.7, WHITE, line=SC_BLUE, radius=0.03)
    add_rect(s, x2, y, col_w, 0.18, SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.35, col_w - 0.4, 0.45,
                "TOMORROW · myReclaim",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, x2 + 0.2, y + 0.85, col_w - 0.4, 0.7,
                "Find unclaimed money for the member",
                font_size=18, bold=True, color=SC_INK)
    rows_tomorrow = [
        ("Input",  "Same SmartCredit member identity"),
        ("Engine", "Same PrivacyMaster matcher"),
        ("Corpus", "State unclaimed-property records"),
        ("Member action", "Claim  /  Not me"),
    ]
    yy = y + 1.7
    for label, body in rows_tomorrow:
        add_textbox(s, x2 + 0.2, yy, 1.2, 0.3, label, font_size=10, bold=True, color=SC_BLUE)
        add_textbox(s, x2 + 1.45, yy, col_w - 1.5, 0.3, body, font_size=11, color=SC_INK_BODY)
        yy += 0.45

    # Bottom
    add_textbox(s, 0.5, 6.7, 12.3, 0.4,
                "The only new thing is the corpus. The plumbing is already in production.",
                font_size=14, bold=True, color=SC_INK_MUTED, align=PP_ALIGN.CENTER)


def slide_claim_integration(prs, n, total):
    """4-tier integration plan for actually filing claims with each state."""
    s = blank_slide(prs)
    add_chrome(s, n, total)
    add_textbox(s, 0.5, 0.85, 12.5, 0.4,
                "FILING THE CLAIM",
                font_size=12, bold=True, color=SC_BLUE)
    add_textbox(s, 0.5, 1.25, 12.5, 1.0,
                "Four ways we can deliver the money — pick the highest tier each state allows.",
                font_size=22, bold=True, color=SC_INK)

    tiers = [
        ("TIER 1",
         "Deep-link to state portal",
         "Member clicks Claim → state's official site opens with property pre-selected.",
         ["All states with online claims",
          "Zero regulatory exposure",
          "Ships with Sprint 1"],
         SC_GREEN, "SHIP NOW"),
        ("TIER 2",
         "Browser-extension form-fill",
         "A SmartCredit extension auto-fills the state's claim form from the member's profile. Member still clicks Submit.",
         ["CA · TX · NY · IL · OH · PA · NJ",
          "FL excluded (ToS forbids automation)",
          "Member-driven, no auto-submit"],
         SC_BLUE, "SPRINT 4-5"),
        ("TIER 3",
         "We file the claim for them",
         "SmartCredit registers as a claimant representative and submits paperwork on the member's behalf — high-value claims only.",
         ["GA · OH · MI (registered finder regimes)",
          "Background-check + legal-review gated",
          "$500+ records only initially"],
         SC_AMBER, "Q4 2026"),
        ("TIER 4",
         "Direct API submission",
         "If a state ever exposes a claim-submission API, we wire it up.",
         ["No state offers this today",
          "Watch NAUPA / Kelmar evolution",
          "Opportunistic — not on roadmap"],
         SC_INK_MUTED, "WATCH"),
    ]
    y = 2.5
    row_h = 1.05
    for tier, title, desc, bullets, color, badge in tiers:
        # row card
        add_round_rect(s, 0.5, y, 12.3, row_h - 0.08, WHITE, line=SC_BORDER, radius=0.03)
        add_rect(s, 0.5, y, 0.22, row_h - 0.08, color)
        # tier label
        add_textbox(s, 0.85, y + 0.1, 1.4, 0.32,
                    tier, font_size=11, bold=True, color=color)
        add_textbox(s, 0.85, y + 0.4, 2.6, 0.42,
                    title, font_size=14, bold=True, color=SC_INK)
        # description
        add_textbox(s, 3.55, y + 0.13, 5.8, 0.85,
                    desc, font_size=11, color=SC_INK_BODY)
        # bullets (right block)
        bullets_text = "  ·  ".join(bullets)
        add_textbox(s, 3.55, y + 0.65, 5.8, 0.4,
                    bullets_text, font_size=9, color=SC_INK_MUTED)
        # status badge
        add_pill(s, 9.6, y + 0.32, 1.7, 0.4,
                 badge, color, WHITE, font_size=10)
        y += row_h

    # Bottom callout
    add_filled = add_round_rect(s, 0.5, 6.85, 12.3, 0.45, SC_BLUE, radius=0.1)
    add_textbox(s, 0.7, 6.9, 12, 0.4,
                "Tier 2 is the breakthrough — \"we found money\" → \"we filled the form\" is what nobody else can ship.",
                font_size=11, bold=True, color=WHITE)


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
        "Web app — SmartCredit-themed search UI with the new BETA visual language",
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

    builders = [
        slide_01_title,
        slide_02_hook,
        slide_03_what_it_is,
        slide_04_why_we_win,
        slide_privacy_master,      # NEW: PrivacyMaster trust precedent
        slide_07_match_reuse,      # PrivacyMaster ↔ myReclaim side-by-side
        slide_05_data_strategy,
        slide_06_architecture,
        slide_claim_integration,   # 4-tier claim-filing strategy
        slide_08_roadmap,
        slide_09_compliance,
        slide_10_built,
        slide_11_ask,
        slide_12_thanks,
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
