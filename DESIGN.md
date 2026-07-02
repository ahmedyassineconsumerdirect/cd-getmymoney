---
version: "2.0"
name: SmartCredit — Get My Money Back
description: >-
  Visual identity for SmartCredit's "Get My Money Back" (myReclaim) feature —
  a trustworthy consumer-fintech experience that helps everyday people find
  unclaimed money held by the state and file to claim it for free. v2 tokens
  are captured from the live smartcredit.com theme (2026-07-02).
colors:
  brand: "#2863C5"          # --cd-blue
  brand-dark: "#1F4F9E"
  brand-grad: "#498EF3"     # logo gradient top (wordmark: 498EF3 → 2863C5)
  brand-light: "#E6EFFA"
  brand-highlight: "#E5F7FE"
  cta: "#FC4C0B"            # --cd-attention — one per view
  cta-dark: "#D63F09"
  sun: "#FFB648"            # hand-drawn underline, ✦ New badges
  money: "#499F7C"          # ALL dollar amounts — smartcredit success green
  money-dark: "#16A35C"
  danger: "#D83E3E"
  ink-heading: "#0F1222"    # --cd-text-black
  ink-body: "#4A4A4A"
  ink-muted: "#777E90"
  surface: "#FFFFFF"
  surface-subtle: "#F8FAFC"
  surface-footer: "#F3F6FF" # pale-blue marketing footer
  border: "#E5E7EB"
  border-strong: "#D1D5DB"
typography:
  family: Open Sans (400 / 600 / 700 / 800)
  display: { fontSize: 52px, fontWeight: 700, lineHeight: 1.1, letterSpacing: "-0.01em" }
  h2: { fontSize: 26px, fontWeight: 700 }
  h3: { fontSize: 15px, fontWeight: 700 }
  body: { fontSize: 15px, fontWeight: 400, lineHeight: 1.6 }
  label: { fontSize: 11px, fontWeight: 700, letterSpacing: "0.16em", uppercase: true }
  amount: { fontSize: 22px, fontWeight: 800, color: money }
rounded: { input: 12px, card: 16px, modal: 16px, pill: 9999px }
shadows:
  card: "0 0 8px 2px rgba(0,0,0,0.06)"
  card-hover: "0 6px 20px rgba(0,0,0,0.10)"
  card-lg: "0 16px 48px rgba(0,0,0,0.12)"
  bar: "0 4px 24px rgba(15,18,34,0.10)"
focus: "border #2863C5 + glow 0 0 8px #94B1E2 (inputs); 2px #2863C5 outline (focus-visible)"
---

## Overview

SmartCredit "Get My Money Back" helps ordinary, non-expert consumers discover
money the government is holding for them and guides them to claim it **for
free, directly with the state**. The emotional target is **calm, credible
excitement** — a real regulated financial product, never a sweepstakes or a
"we'll get your money for a cut" middleman.

v2 direction: **SmartCredit branding with a Google feel.** The page has one
job — search — and the layout says so.

## Signature

Two elements carry the identity; everything else stays quiet:

1. **The search bar.** A single unified white pill (shadow `bar`, hairline
   border, brand focus ring) holding first name · last name · city · state and
   one orange Search button. Centered, oversized, unmissable — the Google
   move, dressed as SmartCredit.
2. **The yellow squiggle.** smartcredit.com's hand-drawn `#FFB648` underline,
   drawn under the word "money" in the headline. Use it exactly once.

## Layout

Radically centered, single column, `max-w-3xl` for search/results (4xl for the
supporting card grid). Hero = eyebrow → headline with squiggle → one-line
reassurance → the bar → a ✓-row of three trust points. Results swap in
directly below the bar (htmx `#results`). Supporting content (commonly
unclaimed chips, Review/Claim/Monitor cards) sits far below the fold, quiet.
No floating search launcher — the only floating element is the MaxAI FAB
(bottom-right).

## Color rules

- **One orange per view.** Home: the Search button. Detail modal: "Continue to
  the state portal". Everywhere else, actions are brand blue (`#2863C5` solid
  pills — the member app's own primary) or text links.
- **Money is always green `#499F7C`** — amounts in cards, the sticky summary
  total, assistant search cards. Never orange, never blue, never `#D85A30`
  (retired).
- Sun `#FFB648` only for the squiggle and ✦ New badges.
- Claimed/history content is grayscale + line-through amounts.

## Key components

- **Sticky summary bar** (results): sticks under the 60px header; label,
  green extrabold total, match count, "100% free to claim directly with the
  state."
- **Match card**: 16px-radius borderless white card — icon tile (rounded-xl,
  brand-light), holder (bold) + property type stacked, ✦ New chip, green
  right-aligned amount with ESTIMATED/RANGE caption, "Address on file" inset
  sub-panel (left border brand), footer row: Details + How to file links left,
  Not me + blue "Claim with the state →" pill right.
- **Claim-detail modal**: ESTIMATED VALUE, HOLDER/SOURCE, PROPERTY DETAILS,
  LAST KNOWN ADDRESS, then "Next steps to receive funds" 3-step timeline
  (Verify identity → File on the portal → Receive funds, ~30–180 days) with a
  connector line, orange portal CTA, compliance line.
- **Sections**: title + count pill (brand-light); "History & resolved items"
  demoted (muted, 80% opacity).
- **"Why is this here?" card**: brand-light aside explaining unclaimed
  property in three sentences.
- **Skeletons, not theater**: loading = three shimmer rows + "Searching
  California's official records…". Never fake pipeline steps, never invented
  progress. Errors get a card with a plain explanation + Try again.
- **State select** groups options honestly: "Searchable today" (California)
  vs "Guided filing" (everything else).
- **Top nav**: 60px white bar, gradient lowercase wordmark + BETA, bureau
  partner strip (TU `#00A6CA` · EXP `#044993` · EQ `#971D31`), muted inactive
  items, Money active.
- **Footer**: pale blue `#F3F6FF`, compliance text, "© smartcredit".

## Accessibility floor

Labels associated with every input (`for`/`id`, sr-only in the bar); visible
focus (`focus-visible` outline + smartcredit input glow); `role="status"`
live region announces result counts, dismissals, and errors; modal is
`role="dialog" aria-modal` with Esc/scrim close and focus restore; animations
gated behind `prefers-reduced-motion`.

## Product & compliance rules (every screen, every future mock)

The app is **guide-to-file only**: SmartCredit never files, submits, holds
funds, or charges a fee.

- ❌ "Direct submission to …" — we never submit claims.
- ❌ "Claim All" — each property is filed individually on the state portal.
- ❌ "Our specialists can guide you through the documentation process."
- ❌ "Zero commission" — don't imply a commission model exists; say
  "Always free — you file directly with the state."
- ❌ "VERIFIED MATCH" / "EXACT MATCH" — always "potential match"; the state
  determines eligibility and ownership.
- ❌ Promising outcomes ("you have $X waiting") — amounts are state-reported
  estimates.
- ❌ State seals, "official/authorized", or anything implying government
  affiliation; keep the non-affiliation disclaimer on every surface.
- ✅ "Submit your claim via California's secure state site."
- ✅ Modal/portal CTA: "Continue to the state portal →".
- Required copy inventory: footer non-affiliation block; results "state
  determines eligibility" + estimates line + common-name caution (≥20
  matches); per-amount ESTIMATED caption; unsupported-state free-note; MaxAI
  footer disclosure. Keep `DISABLED_STATES` kill-switch behavior.

## Don'ts

No sweepstakes/urgency/casino styling; no countdowns or confetti. No second
orange. No heavy drop shadows or sharp corners. No fake progress. No dead
navigation (inactive nav items render as muted text, not links).
