# SmartCredit visual cues (extracted 2026-04-27)

- Primary color: #2863C5  (rgb(40, 99, 197) — used as `bg-cd-primary`, nav dropdown header bg, brand links, logo tint)
- Secondary/CTA color: #FC4C0B  (rgb(252, 76, 11) — all primary action buttons: "Sign Up", "Get Started Now", "Get Started")
- Accent/badge color: #FFB352  (rgb(255, 179, 82) — "Best Value" / recommended plan badge)
- Background (page): #FFFFFF  (white)
- Background (subtle section): #FBFBFB / #F4F4F6  (off-white alternating sections)
- Background (footer / modal): #F7FAFC  (rgb(247, 250, 252) — very light blue-gray)
- Text (headings): #23262F  (rgb(35, 38, 47) — near-black)
- Text (body/nav): #4A4A4A  (rgb(74, 74, 74))
- Text (muted/footer): #4A5568  (rgb(74, 85, 104))
- Link color: #2863C5  (same as primary blue)

- Font (headings): "Open Sans", "Lucida Grande", "Lucida Sans Unicode", Helvetica, Arial, Verdana, sans-serif
- Font (body): "Open Sans", "Lucida Grande", "Lucida Sans Unicode", Helvetica, Arial, Verdana, sans-serif
  — Effective stack is Open Sans throughout; fall back to system sans-serif.

- Nav structure: White background header. Left = SmartCredit logo (blue wordmark). Center = nav links (Partnerships, Pricing, Blog, Offers dropdown). Right = language selector (EN pill, gray bg), "Log In" text link, "Sign Up" pill button (orange #FC4C0B, border-radius 24px).

- Button style:
  - Primary CTA: background #FC4C0B, color white, border-radius ~48px (fully pill-shaped), font-weight 600, no border, no shadow. Example padding: 0 12px with line-height giving ~44px height.
  - Nav "Sign Up": same orange, border-radius 24px, border: 2px solid #FC4C0B.
  - Secondary / outline: not prominently used; accessibility skip-links use border: 2px solid #0038FF with border-radius 8px.

- Card pattern:
  - White card (`bg-white`), border-radius 20px (`b-rd-5` = 5 * 4px = 20px), large drop shadow: `rgba(0,0,0,0.176) 0px 16px 48px 0px`. No visible border.
  - Pricing cards sit inside this container; column layout with checkmarks for feature rows.
  - Recommended/highlighted plan uses an amber badge (#FFB352) positioned absolutely above the card header.
  - Testimonial slider uses the same white card + shadow pattern.
  - Bottom CTA band: solid #2863C5 (primary blue) full-width section with white text and orange buttons — max-width 75rem, border-radius 5px, padding 3rem.

- Section pattern: Alternating white (#FFFFFF) and off-white (#FBFBFB / #F4F4F6) full-width sections with generous vertical padding (py-5rem on xl, my-6rem on lg). No hard borders between sections — separation is purely via background color shift.

- Source: https://www.smartcredit.com/

Used to guide Tailwind config in `app/templates/base.html`.
