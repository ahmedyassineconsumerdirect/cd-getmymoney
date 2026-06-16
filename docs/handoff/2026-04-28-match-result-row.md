# Match Result Row — Developer Handoff

**Component**: `MatchResultRow`
**Page**: Results (`POST /search` htmx fragment) — see `app/templates/results.html`
**Date**: 2026-04-28
**Designer**: Ahmed Yassine
**Variant chosen**: C — Labeled key/value fields
**Status**: Ready for implementation

---

## 1. Why this design

The previous version compressed three distinct facts — reported name, address, and source — into a single dot-separated line, with the source state buried in a small uppercase pill next to the title. Users scanning a list of matches couldn't tell at a glance whether each fact applied to *them* or to the *property*, and the pill's "CA record" label didn't communicate that this came from an authoritative state database.

Variant C treats the metadata as labeled data, the way a financial statement does. It trades a small amount of visual density for clarity and audit-style trust — appropriate for a feature that asks the user "is this you?" and expects them to verify the match against their own records before clicking Claim.

---

## 2. Component anatomy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌──┐  Property type                                       $XX.XX           │
│  │ ◇│  Holder name                                       ESTIMATED          │
│  └──┘                                                                       │
│        Reported as       Owner name                       ┌──────────┐      │
│        Address on file   Street, City, State ZIP          │  Claim   │      │
│        Source            🛡 California State Records      └──────────┘      │
│                                                            Not me →         │
└─────────────────────────────────────────────────────────────────────────────┘
   ↑          ↑                                                ↑
   icon       content column (1fr)                             actions
```

Five regions:

1. **Category icon** — circular badge with property-type icon (left)
2. **Header** — property type name + holder
3. **Metadata grid** — three labeled rows (Reported as / Address on file / Source)
4. **Amount block** — dollar value + "ESTIMATED" caption
5. **Actions** — Claim button + "Not me" link

---

## 3. Visual specifications

### 3.1 Layout

| Property | Value | Token |
|---|---|---|
| Card background | `#FFFFFF` | `bg-white` |
| Card border | `0.5px solid` rgba(0,0,0,0.08) | `border border-slate-100` |
| Card border-radius | 12px | `rounded-xl` |
| Card padding | 18px 20px | `px-5 py-[18px]` |
| Card vertical gap | 12px between cards | `space-y-3` on parent |
| Grid template (≥720px) | `40px 1fr auto auto` | custom grid |
| Grid gap | 16px | `gap-4` |

The whole row is a single `<article>`. Do **not** wrap each region in its own card.

### 3.2 Category icon

| Property | Value |
|---|---|
| Diameter | 40px |
| Background | `var(--color-info-50)` — equivalent to Tailwind `bg-blue-50` |
| Icon size | 20px stroke (1.5px width) |
| Icon color | `var(--color-info-600)` — `text-blue-600` |

Icon mapping by property type code:

| Code prefix | Property family | Icon | Notes |
|---|---|---|---|
| `MS09` | Credit balance / accounts receivable | `credit-card` | |
| `MS01` | Wages / payroll / salaries | `briefcase` | |
| `UT0x` | Refunds / rebates (utilities) | `rotate-ccw` | Use green tint (`bg-green-50` / `text-green-700`) to distinguish refunds |
| `AC0x` | Checking / savings | `wallet` | |
| `IN0x` | Insurance | `shield` | |
| _default_ | Unknown | `file-text` | Falls back to gray (`bg-slate-100` / `text-slate-600`) |

The mapping table lives in `app/match.py` as `PROPERTY_TYPE_DISPLAY` — frontend reads display name + icon-key from the API response, never derives them from the raw code.

### 3.3 Typography

All sentence case. No ALL CAPS except the "ESTIMATED" caption, which is a deliberate small-caps treatment.

| Element | Size | Weight | Color | Tailwind |
|---|---|---|---|---|
| Property type | 16px | 500 | `text-slate-900` | `text-base font-medium` |
| Holder name | 14px | 400 | `text-slate-900` | `text-sm` |
| Key label (e.g. "Reported as") | 12px | 400 | `text-slate-400` | `text-xs text-slate-400` |
| Key value | 13px | 400 | `text-slate-900` | `text-[13px]` |
| Source value | 13px | 400 | `text-slate-900` | `text-[13px]` |
| Source shield icon | 13×13px | — | `text-emerald-700` (#0F6E56) | inline SVG |
| Amount | 22px | 500 | `#D85A30` (coral-600) | `text-[22px] font-medium text-[#D85A30]` |
| ESTIMATED caption | 11px | 400 | `text-slate-400` | `text-[11px] tracking-[0.04em] uppercase` |
| Claim button | 14px | 500 | `text-white` on `#D85A30` | see button section |
| "Not me →" | 12px | 400 | `text-blue-600` | `text-xs text-blue-600` |

Line-height defaults: `1.4` for headers, `1.5` for body text. Don't override per element.

### 3.4 Metadata grid

The three-row labeled grid is the heart of this variant.

| Property | Value |
|---|---|
| Grid template | `auto 1fr` (key column hugs content, value fills rest) |
| Row gap | 4px |
| Column gap | 16px |
| Margin-top from holder | 8px |

Key labels use **the exact strings**:

- `Reported as` (the owner's name as it appears in CA records)
- `Address on file` (the last-known address from CA records)
- `Source` (the originating dataset)

Do not invent variations like "Name on record" or "Listed under". The user research that drives this microcopy — particularly "Address on file" rather than "Address" — is meant to signal that the state has this data, not the user.

### 3.5 Source badge

The Source value renders as: `[shield icon] California State Records`

| Property | Value |
|---|---|
| Shield icon | 13×13px filled, `#0F6E56` (emerald-700) |
| Icon-to-text gap | 6px |
| Text | "California State Records" — see §6.4 for multi-state |

The shield is filled (not stroked). It's the only filled icon in the row — the visual weight is deliberate, calling out the trust signal without needing a colored badge background.

### 3.6 Amount block

Right-aligned, two-line stack:

| Line | Style |
|---|---|
| `$83.19` | 22px / 500 / `#D85A30`, `line-height: 1` |
| `ESTIMATED` | 11px / 400 / `text-slate-400`, `letter-spacing: 0.04em`, `margin-top: 4px` |

When the source provides a range (`amount_min` ≠ `amount_max`), display as `$XX.XX–$YY.YY` and **change the caption to `RANGE`** (still uppercase, same style). Frontend decides which caption based on whether min equals max.

### 3.7 Claim button

| Property | Value |
|---|---|
| Background | `#D85A30` (coral-600) |
| Text | `#FFFFFF`, 14px, weight 500 |
| Padding | 8px 20px |
| Border-radius | 999px (full pill) |
| Border | none |
| Min-width | 92px (so "Claim" and longer states like "Claiming…" don't reflow) |

States covered in §4.

### 3.8 "Not me →" link

| Property | Value |
|---|---|
| Display | block, centered under button |
| Margin-top | 6px |
| Font | 12px / 400 |
| Color | `text-blue-600` |
| Decoration | none (underline on hover only) |

The arrow is a plain `→` glyph, **not** an SVG. The space between "me" and the arrow is a regular space (not non-breaking) — line breaks here are acceptable on narrow screens.

---

## 4. Interaction states

### 4.1 Card

| State | Treatment |
|---|---|
| Default | as specified in §3.1 |
| Hover | `border-color: rgba(0,0,0,0.16)` (~`border-slate-200`); 150ms ease |
| Focus-within | same as hover, plus 2px `box-shadow: 0 0 0 3px rgba(55,138,221,0.2)` (info focus ring) |

Do **not** apply hover styles on touch devices. Use `@media (hover: hover)` to gate.

### 4.2 Claim button

| State | Background | Text | Notes |
|---|---|---|---|
| Default | `#D85A30` | `#FFFFFF` | |
| Hover | `#C24B23` | `#FFFFFF` | 100ms ease |
| Active | `#A83F1C` | `#FFFFFF` | scale(0.98) |
| Focus-visible | default + `box-shadow: 0 0 0 3px rgba(216,90,48,0.3)` | | |
| Disabled | `#F0B69E` | `#FFFFFF` | `cursor: not-allowed` |
| Loading | `#D85A30` + 14px spinner replacing label | `#FFFFFF` | label = "Claiming…" if spinner can't be done |

Submitting takes the user to `claimit.ca.gov` via a deep-link — there is **no async claim flow** in the prototype. The button is effectively a styled `<a>` opening in a new tab. Loading state only matters if production wraps it in a tracked redirect.

### 4.3 "Not me" link

| State | Treatment |
|---|---|
| Default | `text-blue-600` |
| Hover | `text-blue-700`, underline |
| Active | `text-blue-800` |
| Focus-visible | underline + 2px focus ring (`outline-offset: 2px`) |

Clicking "Not me" hides this row from the list with a 200ms `opacity` fade and removes it from local results state. In the prototype it's not persisted; in production, log a `dismissed_match` event with `record_id`.

### 4.4 Whole row

The card itself is **not** clickable. Clicks go through to the Claim button or "Not me" link. This keeps screen-reader navigation predictable — no nested interactive regions.

---

## 5. Content specifications

### 5.1 Character limits and truncation

| Field | Soft limit | Hard cap | Truncation |
|---|---|---|---|
| Property type | 32 | 60 | `text-overflow: ellipsis` on overflow, with `title` attr fallback |
| Holder name | 60 | 120 | one-line ellipsis |
| Reported-as name | 80 | 200 | one-line ellipsis |
| Address on file | 80 | 200 | one-line ellipsis |
| Source label | 32 | 50 | should never overflow; ellipsis as defensive measure |
| Amount string | — | 13 chars (`$999,999.99`) | never truncate; let the column grow |

Long values use a single-line ellipsis — **not** a multi-line clamp. Showing half an address creates more confusion than a truncated one with hover-to-expand.

### 5.2 Localization

CA records are English-only, but the UI shell is localizable. Treat all four labels (`Reported as`, `Address on file`, `Source`, `ESTIMATED`/`RANGE`) as i18n strings. Don't concatenate label + value at build time; let the template interpolate.

When future state expansion adds non-Latin character data (e.g. names in Cyrillic if a member has a Russian-government data source), the grid behavior is identical — character-width metrics are CSS, not content.

### 5.3 Empty / missing data

The match service guarantees `record_id`, `holder_name`, `owner_name`, `amount_max`, `property_type`, and `source_state`. The other fields can be null.

| Field | If missing | Display |
|---|---|---|
| Reported as | never null | — |
| Address on file | null | hide entire row (label + value), don't show "—" |
| Source | never null | — |
| Amount range | min == max | show single value with "ESTIMATED" |
| Holder name | rare, unknown holder | show "Unknown holder" in `text-slate-400` italic |

When `Address on file` is hidden, the metadata grid collapses to two rows. The card height shrinks accordingly — no padding adjustment needed because the flexible row gap handles it.

### 5.4 Loading state (initial fetch)

The page renders three skeleton rows while the htmx request is in flight. Skeletons match the row's grid:

- Icon: 40px circle, `bg-slate-100`
- Property type line: 140px × 16px, `bg-slate-100`, `rounded`
- Holder line: 100px × 14px, `bg-slate-100`, `rounded`, `mt-1`
- Three metadata-grid rows: 80px label + 200px value bars
- Amount: 70px × 22px bar
- Button: 84px × 36px pill

Use the same shimmer animation as the SmartCredit dashboard cards (1.4s linear infinite). If shimmer infrastructure isn't available, plain pulse is acceptable.

### 5.5 Empty results state

When zero matches return, **don't render any rows**. Show the existing empty-state component with copy:

> We didn't find anything in California — we're expanding to all 50 states.

That component is out of scope for this handoff but already exists in `app/templates/results.html`.

### 5.6 Error state

If the htmx request fails:

- Don't render rows
- Show inline error: "We couldn't load matches. Try again." with a retry button
- Use `bg-red-50 border-red-200 text-red-900`
- Retry button reissues the same htmx call

### 5.7 Disclaimers

The "ESTIMATED" caption is the legal disclaimer for amount accuracy. Do not add tooltips, asterisks, or footnotes attached to the amount itself. The page-level disclaimer ("Amounts shown are CA's reported estimates and may differ from the actual claim payout") lives once at the top of the results section, not per row.

---

## 6. Edge cases

### 6.1 Very long names

Names like "Christopher Alexander Wellington-Smythe III" exceed the 80-char soft limit. They truncate with ellipsis, and the full value is in the `title` attribute. On hover the browser tooltip shows the full name; on touch devices we accept the truncation (no native tap-tooltip).

### 6.2 International names

Names in non-Latin scripts (Cyrillic, Arabic, CJK) render in the same font stack — system fonts handle these. Right-to-left scripts: the metadata grid is **not** rtl-aware in the prototype. Since CA data is English-only this isn't a near-term concern, but flag it for production.

### 6.3 Multi-state futureproofing

When the roadmap reaches Q4 2026 (TX added) and beyond:

| State | Source label |
|---|---|
| CA | California State Records |
| TX | Texas State Records |
| NY | New York State Records |
| _other_ | "{State name} State Records" |

Source label is generated server-side as `f"{state_name} State Records"` from a `STATE_DISPLAY` map keyed on the two-letter code. The shield icon and color stay constant across states — the visual treatment is the trust mark, the text carries the specificity.

### 6.4 Multiple records from the same holder

If a member has two records from Citibank N A, render two separate cards. Don't group — each record has its own `record_id` and may have a different reported-name or address (which is the entire signal users need to confirm "yes, that's me when I lived at the old apartment").

### 6.5 Slow network

Skeletons appear within 50ms of the search submit. If the response takes >10s, the skeleton stays — show a small "Still searching…" caption above the skeleton list. Do not show a spinner replacing the skeletons.

### 6.6 Dollar amount edge cases

| Case | Display |
|---|---|
| $0.00 | render as `$0.00` (don't hide; it's a valid record) |
| ≥$1,000 | thousands separator: `$1,234.56` |
| ≥$1,000,000 | render as `$1,234,567.89` — column grows; don't abbreviate to "$1.2M" |
| Negative | should never occur from CA data; if seen, render as `$0.00` and log |

---

## 7. Accessibility

### 7.1 Semantic structure

The results list is a `<ul>` with each row as `<li><article>…</article></li>`. The `<article>` has `aria-labelledby` pointing at the property-type heading id.

```html
<ul class="space-y-3">
  <li>
    <article aria-labelledby="match-12345">
      <h3 id="match-12345" class="sr-only">Credit balance from Citibank N A, $83.19</h3>
      …
    </article>
  </li>
</ul>
```

The `sr-only` heading combines all the row's signal into one phrase — screen-reader users get the gist before tabbing into the labeled fields.

### 7.2 Focus order

Tab order within a row: **Claim button → "Not me" link**. The card body itself is not focusable. Within the page, focus moves row by row in DOM order.

### 7.3 Labels

| Element | Label |
|---|---|
| Claim button | `aria-label="Claim ${propertyType} from ${holder} for ${amount}"` |
| "Not me" link | `aria-label="Mark ${propertyType} from ${holder} as not yours"` |
| Source shield icon | `aria-hidden="true"` (decorative; the text says it) |
| Category icon | `aria-hidden="true"` (decorative; the heading says it) |

### 7.4 Color contrast

| Pairing | Ratio | WCAG |
|---|---|---|
| `text-slate-900` on white | 16.1:1 | AAA |
| `text-slate-400` on white | 4.6:1 | AA (below AAA — labels are 12px, not large text) |
| `#D85A30` on white (amount) | 4.5:1 | AA |
| White on `#D85A30` (button) | 4.5:1 | AA |
| `text-blue-600` on white ("Not me") | 5.9:1 | AA |
| `text-emerald-700` on white (shield) | 6.3:1 | AAA |

Key labels at `text-slate-400` are AA-compliant for normal-sized text but not AAA. If accessibility audit pushes for AAA across the board, change to `text-slate-500` (7.0:1).

### 7.5 Keyboard interactions

- `Tab` / `Shift+Tab` — move between Claim and "Not me" across rows
- `Enter` / `Space` on Claim — activates link (opens claimit.ca.gov in new tab)
- `Enter` / `Space` on "Not me" — dismisses the row, focus moves to the next row's Claim button (or empty-state if last)

### 7.6 Reduced motion

Honor `prefers-reduced-motion: reduce` for:
- Card hover transition → instant
- "Not me" dismiss fade → instant removal
- Skeleton shimmer → static `bg-slate-100`

### 7.7 Screen reader announcements

- After "Not me" dismiss: announce `"Removed. ${remainingCount} matches left."` via a `role="status"` polite live region above the list.
- After search loads: announce `"${count} matches found, totaling ${formattedTotal}."` once the skeleton is replaced.

---

## 8. Responsive behavior

### 8.1 Breakpoints

| Range | Layout |
|---|---|
| ≥720px | Default 4-column grid (icon / content / amount / actions) |
| 480–719px | 3-column: icon stays at 40px, amount and actions stack into a single right column |
| <480px | Single column: icon and header on row 1, metadata grid full-width on row 2, amount + button side-by-side at the bottom |

### 8.2 Mobile (<480px) details

- Card padding shrinks to `14px 16px`
- Metadata grid stays as `auto 1fr` — labels do not stack above values (the visual rhythm is more important than space saved)
- Amount block becomes left-aligned, on the same row as the button
- "Not me" link moves under the metadata grid as a small text button, not under Claim

### 8.3 Container queries

If the row ever lives in a sidebar or modal (e.g. a "matches you've claimed" history panel), use `@container` rather than `@media` for the breakpoints above. Wrap the list in a `container-type: inline-size` parent.

---

## 9. Reference HTML (Tailwind + htmx)

```html
<article
  class="grid grid-cols-[40px_1fr_auto_auto] gap-4 items-start bg-white border border-slate-100 rounded-xl px-5 py-[18px] hover:border-slate-200 transition-colors"
  aria-labelledby="match-{{ record_id }}"
>
  <h3 id="match-{{ record_id }}" class="sr-only">
    {{ property_type_display }} from {{ holder_name }}, {{ amount_display }}
  </h3>

  <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600" aria-hidden="true">
    {% include 'icons/' + icon_key + '.svg' %}
  </div>

  <div class="min-w-0">
    <div class="text-base font-medium text-slate-900 truncate" title="{{ property_type_display }}">
      {{ property_type_display }}
    </div>
    <div class="text-sm text-slate-900 truncate" title="{{ holder_name }}">
      {{ holder_name }}
    </div>

    <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 mt-2">
      <dt class="text-xs text-slate-400">Reported as</dt>
      <dd class="text-[13px] text-slate-900 truncate" title="{{ owner_name }}">{{ owner_name }}</dd>

      {% if address_display %}
      <dt class="text-xs text-slate-400">Address on file</dt>
      <dd class="text-[13px] text-slate-900 truncate" title="{{ address_display }}">{{ address_display }}</dd>
      {% endif %}

      <dt class="text-xs text-slate-400">Source</dt>
      <dd class="text-[13px] text-slate-900 flex items-center gap-1.5">
        <svg width="13" height="13" viewBox="0 0 14 14" fill="#0F6E56" aria-hidden="true">
          <path d="M7 0.7l5 2v3.5c0 3-2 5.5-5 7-3-1.5-5-4-5-7V2.7l5-2zm-0.7 7.7L9.8 5l-1-1L6.3 6.4 5 5l-1 1 2.3 2.4z"/>
        </svg>
        <span>{{ source_display }}</span>
      </dd>
    </dl>
  </div>

  <div class="text-right">
    <div class="text-[22px] font-medium leading-none" style="color:#D85A30">{{ amount_display }}</div>
    <div class="text-[11px] text-slate-400 tracking-[0.04em] uppercase mt-1">
      {{ 'Range' if has_range else 'Estimated' }}
    </div>
  </div>

  <div>
    <a
      href="{{ claim_url }}"
      target="_blank"
      rel="noopener"
      class="inline-block min-w-[92px] text-center text-white text-sm font-medium px-5 py-2 rounded-full hover:brightness-95 active:brightness-90"
      style="background:#D85A30"
      aria-label="Claim {{ property_type_display }} from {{ holder_name }} for {{ amount_display }}"
    >
      Claim
    </a>
    <button
      type="button"
      class="block w-full text-center text-xs text-blue-600 hover:text-blue-700 hover:underline mt-1.5"
      hx-post="/dismiss/{{ record_id }}"
      hx-target="closest article"
      hx-swap="outerHTML swap:200ms"
      aria-label="Mark {{ property_type_display }} from {{ holder_name }} as not yours"
    >
      Not me →
    </button>
  </div>
</article>
```

---

## 10. Open questions

1. **Range vs. single amount caption** — the design uses "ESTIMATED" for single values and "RANGE" for ranges. Is the single-word switch clear enough, or should ranges show "ESTIMATED RANGE" for consistency? (Recommend: keep "RANGE" — shorter, clearer, and the dollar string itself signals it.)
2. **"Not me" persistence** — prototype only hides client-side. Confirm production wants this persisted as a `dismissed_match` event in Snowflake.
3. **Multi-record from same holder** — §6.4 keeps them as separate cards. If user research shows people prefer them grouped under a holder header, we revisit.
4. **Source-label localization** — when the UI ships in Spanish, "California State Records" needs translation. Localize the label, not the agency name (i.e. "Registros del Estado de California", not "California Registros del Estado").

---

## 11. Files touched

- `app/templates/results.html` — replace existing row partial with §9 reference
- `app/templates/_match_row.html` — new partial extracted from results.html for clarity
- `app/static/icons/{credit-card,briefcase,wallet,rotate-ccw,shield,file-text}.svg` — verify these exist
- `app/match.py` — extend `Match` dataclass with `icon_key`, `property_type_display`, `source_display`, `address_display`, `amount_display`, `has_range`
