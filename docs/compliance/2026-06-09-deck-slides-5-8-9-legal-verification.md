# Legal verification — GetMyMoney exec deck, slides 5 / 8 / 9

**Date:** 2026-06-09
**Scope assumption (locked):** alert + possible-match display + deep-link only. No UP-tied fee, no filing on behalf, no POA, no holding funds. Bundled in the flat SmartCredit subscription.
**Method:** every legal claim on slides 5, 8, 9 checked against current primary sources (statutes, state agency pages, agency request programs). Sources linked per item.

## Verdict summary

| Slide claim | Verdict |
|---|---|
| 5 · FL Ch. 119 PRR → owner-name list | ✅ Accurate, with caveats (no $ amounts, no SSNs/property IDs) |
| 5 · TX SIFT bulk feed "via PI license" | ⚠️ Mechanism right; "via PI license" wrong |
| 5 · CA free public CSV, Thursdays | ✅ Accurate (attribute to sco.ca.gov) |
| 5 · GA weekly file "via written DOR request" | ❌ Wrong — CDR-registration-gated since 7/1/2024 |
| 5 · NY OSC quarterly SFTP, no amounts/tax IDs | ✅ Accurate |
| 5/9 · PA blind (anti-bot/AI) | ✅ Accurate w/ caveat |
| 5/9 · SC blind (§30-2-50) | ✅ Accurate w/ caveat (bars *solicitation*, not all use) |
| 9 · WA blind (statute bars commercial use) | ❌ Wrong — no such statute; WA is an opportunity |
| 9 · AZ blind (statute bars commercial use) | ❌ Wrong statute theory; "no feed" half holds |
| 9 · MA/MI blind (Cloudflare) | ⚠️ Bot-blocking real; vendor is CloudFront/Akamai, not Cloudflare |
| 5/9 · OH "unknown — no feed surfaced" | ❌ Wrong — ORC §169.06 public list + registered-finder regime exists |
| 8 · FL "no Ch. 717 registration needed — not filing" | ⚠️ Conclusion defensible; *reasoning* wrong — misses §717.1322(1)(j) |
| 8 · TX "PI license may apply to the data request — confirm w/ Comptroller" | ❌ Wrong hook, wrong agency (DPS; §1702.324(b)(5) exemption) |
| 8 · CA "lowest-friction state" | ✅ Accurate |
| 8 · GA "no CDR registration needed under alert-only" | ⚠️ Conduct OK; parenthetical wrong; **no registration = no data** |
| 9 · TSR §310.4(a)(3) eliminated | ✅ Outcome right; it never applied (no fee *and* no telemarketing) |
| 9 · GA §44-12-224 "forbids holding funds" | ❌ Quotes text **repealed 7/1/2024** (SB 103) |
| 9 · Open question: NY APL §1416 / CCP §1582 vs flat subscription | ⚠️ Right question, NY-only; CA §1582 is clean; "24-month" (NY) and "12-month" (CA) figures don't exist |

## What changes under alert + deep-link only

### Strengthened (better than the deck says)

- **TX** — §74.507's operative clauses all hook on a *fee contracted for or received from the claimant* (10% cap) or a percentage-fee filing bar. Free informing with no agreement gives the statute nothing to operate on. The handoff memo's "operative trigger is informing" reading is wrong. The PI-license question attaches to locator *activity*, not the bulk-data request (Comptroller hands the file to unlicensed requesters; license number requested "if applicable"), and Tex. Occ. Code §1702.324(b)(5) exempts review of public information *regardless of compensation* — confirm with **Texas DPS Private Security**, not the Comptroller.
- **WA** — RCW 63.30.300 *mandates* a public searchable owner database; no commercial-use bar exists. Only fee-based locate agreements are regulated (RCW 63.30.780/.790, 5% cap — irrelevant to our scope). Old RCW 63.29.350 was repealed 1/1/2023. WA's 4,000+ members shouldn't be written off as legally blind; data acquisition is an operational question, not a legal one.
- **OH** — not "unknown": ORC §169.06 requires a public owner list (and an in-office alphabetical list ≥$10); §169.13/§169.16 run a registered-finder regime whose hook is *remuneration for recovery assistance*. Alert-only with no UP fee is arguably outside it; counsel sign-off needed on the bundling question. OH belongs in "data obtainable, finder rules apply."
- **CA** — §1582 only invalidates *agreements for compensation*; a free alert + deep-link has nothing in scope. Residual is B&P §17533.6 (no implied state affiliation) — already mitigated in product copy.

### Weakened (worse than the deck says)

- **GA** — SB 103 (eff. 7/1/2024) rewrote the article. §44-12-239(a) gates *all* department UP data behind CDR registration: $1,200 / 4 years, photo ID, background checks. The GORA path is foreclosed (§44-12-225 confidentiality + §50-18-72(a)(1) exemption). Even a registered CDR may distribute the data only "for the purpose of soliciting owners … to offer claim services" (§44-12-239.1(b)) — awkward for a product that offers *no* claim services. **GA's 18,837 members should move from "alertable" to "deep-link only" unless we register as a CDR and counsel clears the use-restriction.** Slide 5's "5 paths = 158K members (~53%)" becomes **4 paths ≈ 139K (~45%)**.
- **FL** — the deck's "we're not filing on behalf of anyone" is the wrong test. §717.1322(1)(j) sanctions *"requesting or receiving compensation for notifying a person of his or her unclaimed property"* unless the notifier is a FL attorney, FL CPA, or Ch. 493 PI — no filing, no POA required, and corporations can't register at all. Whether a UP alert bundled in a *paid* subscription is "compensation for notifying" is a genuine gray area ($500–$2,000 per act; Rule 69I-20.076 F.A.C.). The no-UP-fee architecture is the *defense*, not a safe harbor — this needs counsel before FL, and it is the same shape as the NY §1416 question. Data caveats: §717.1400 gates *dollar amounts* behind registration, so the PRR list arrives **without amounts** (like NY); SSNs/property identifiers are exempt (§717.117(11)(b)); Ch. 119 doesn't support standing requests — re-request each cycle.
- **NY** — APL §1416 defines covered services as "any service **for a fee** providing assistance … for the purposes of locating" — the flat subscription *is* a fee, so the definitional ambiguity is real (this is the deck's load-bearing open question, correctly identified, but it's NY-specific, with FL §717.1322(1)(j) as its sibling). All operative requirements presuppose a per-recovery agreement filed with claims, which never happens under self-file — so practical exposure is weak. **No 24-month restriction exists in §1416** — delete it.

### Citation/fact corrections for the next deck build (`scripts/build_exec_deck.py`)

1. Slide 5 GA row: "FEED · weekly delimited file via written DOR request" → "CDR-GATED · weekly file requires CDR registration ($1,200/4 yr + background checks); counsel to clear §44-12-239.1(b) use restriction".
2. Slide 5 TX row: drop "via PI license" → "bulk file via email request to Comptroller (SIFT delivery); PI license number only 'if applicable'".
3. Slide 5/9: move WA out of "statute bars commercial use" (no such statute); AZ's bar is also wrong — AZ regulates paid locators (§44-327, *not* §44-318); its blindness is purely "no feed" (A.R.S. §39-121.03 commercial public-records request unexplored).
4. Slide 5/9: OH from "UNKNOWN" → "data path exists (ORC §169.06); finder regime hooks on remuneration — counsel to confirm bundle posture".
5. Slide 8 FL: replace "No Ch. 717 registration needed — we're not filing on behalf of anyone" with "Registration unavailable to corporations and not required for free alerts — but §717.1322(1)(j) reaches *compensated notification*; counsel to bless the no-UP-fee bundle posture before FL".
6. Slide 8 TX: "confirm with Comptroller" → "confirm §1702.324(b)(5) public-records exemption with Texas DPS".
7. Slide 9: GA §44-12-224 quote is repealed text — current law (§44-12-220) has the state disburse, deducting a registered CDR's fee share; reframe as "funds always flow through the state — we are never in the money path".
8. Slide 9: "Cloudflare-blocked" → "bot-protected portals (CloudFront/Akamai)"; MI FOIA path not yet ruled out.
9. Slide 9 open question: delete "24-month" (NY) — doesn't exist; CA's actual rule: agreements invalid only between holder report and delivery to Controller, valid immediately after (10% cap) — the deck's "12 months" tracks the *records-confidentiality* rule in §1582(b), not agreement validity.
10. Slide 9 TSR: "eliminates TSR §310.4(a)(3)" → "TSR advance-fee rule inapplicable (no fee, no telemarketing)".
11. Handoff memo line ~398: correct the §74.507 reading — "informing" defines who is covered; the operative restriction is the fee (10% cap + percentage-fee filing bar).

### The one product-shaping takeaway

Under alert + deep-link only, the recurring legal pattern across FL (§717.1322(1)(j)), NY (§1416), GA (§44-12-239.2(a)(10)), and OH (finder definition) is the same single question: **is a free UP alert inside a paid subscription "compensation for notifying"?** That — not finder-fee caps, which all hook on fees we don't charge — is the one issue outside counsel must answer, and the answer likely transfers across all four states. CA, TX, and WA don't even pose it.

## Addendum (same day): bulk-data availability + refresh cadence, top 10

Follow-up verification for the "can we get bulk data, and how often does it update" question (scope: possible matches + deep link, no fee):

| State | Bulk possible? | Mechanism | Updates | Notes |
|---|---|---|---|---|
| CA | ✅ Yes | Free public CSV, sco.ca.gov | **Weekly (Thursdays)** — confirmed verbatim | New records arrive in annual holder waves (Nov 1 notice / Jun 1–15 remit) |
| TX | ✅ Yes | Email request → SIFT delivery | **Monthly** (first 7 working days; 2019 Comptroller statement — reconfirm on request) | Annual holder reports due Jul 1 |
| NY | ✅ Yes | OSC owner-name file request form → secure FTP | **On demand** ("retrieve the file as often as you like"); **"quarterly" is NOT on OSC's page — earlier claim retracted; confirm cadence with OUF** | No amounts/tax IDs; excludes <$20, no-name/foreign-address, pre-1985 |
| FL | ✅ Yes | Ch. 119 PRR to DFS | **Per request** (point-in-time extract; no documented recurring program) | Annual holder reports due before May 1 → pull after the May wave; no $ amounts |
| GA | ⚠️ Gated | CDR-registered download | **Weekly** — confirmed ("database file is updated once a week") | CDR: $1,200/4 yr + background checks |
| IL | ❌ No | None | — | DB statutorily FOIA-exempt (765 ILCS 1026/15-1401(b)); Treasurer: "does not provide bulk data files, database exports, or API access" — **even licensed finders get no data**. data.illinois.gov has no UP dataset (Socrata catalog checked) |
| NC | ✅ Conditional | Statutory annual electronic list (G.S. 116B-62) — published as PDF volumes on nccourts.gov | **Annual** (as of Jun 30, distributed by Jul 31) | Newly reported names only (non-cumulative — accumulate yearly); names+addresses, no amounts; fuller historical file possibly via Ch. 132 request after the 12-month confidentiality window (discretionary) |
| NJ | ✅ Conditional | OPRA request to Treasury UPA (agency FAQ explicitly routes bulk-list requests through OPRA) | **On demand** (7-business-day response; realistic annual/semiannual re-pull; holder reports due Oct 31) | N.J.S.A. 46:30B-76 makes name+address affirmatively public; **everything else confidential** (-76.1). 2024 OPRA amendments: commercial-purpose certification + service charge required — request as commercial, budget the fee |
| PA | ❌ No | None | — | Anti-bot/anti-AI policy; only low-fidelity advertised name lists |
| SC | ❌ No | None | — | §30-2-50 solicitation bar + no feed |

Net: bulk data possible in **6 of the top 10** (CA·TX·NY·FL direct; NC·NJ conditional) = **158,292 members (~53%)**; GA gated; IL/PA/SC deep-link only. Slides 5/8/9 updated accordingly (slide 5 now carries BULK? + UPDATES columns).

## Addendum 2 (2026-06-10): full 50-state + DC + territories sweep

Member-weighted (distribution CSV, Jun 2026): **22 YES states = 74.3% of members · 34 NO jurisdictions = 25.7%.** Seven false negatives caught vs. the April matrix:

**New YES (mechanism · cadence · cost):**
- **WI** — free public Excel download `revenue.wi.gov/Documents/HeirFinderCD.xlsx` (verified by download: names, addresses, amounts, holder) · annual · $0. Best-in-class.
- **MD** — official Comptroller download by letter request (FAQ Q16) · ~annual · **$4**. Names + addresses + claim number; no amounts/holder.
- **LA** — Treasury owner CD for locators (archived FAQ; reconfirm logistics) · per request · ~$50; broad LA public-records fallback; LA Wallet precedent of state-fed matching.
- **NV** — Investigator list, written request + ID · Jan + Jul · $25 CD-R (PDF!) · **≥$5,000 properties, >24 mo only**. (Almost certainly CK's "CD with data in a PDF.")
- **MO** — RSMo §447.560 makes owner names/addresses *statutorily public*; Sunshine request + annual county new-owner lists online.
- **IN** — no standing file; negotiated/APRA dump (CK got one circa 2017); post-2021 RUUPA confidentiality untested — test request.
- **CT** — FOIA to Treasurer; proven by CT Mirror 2022 ($200, ~300k-page PDF) · full list generated biennially · ≥$50 only.
- Plus matrix-confirmed: **AR** ($250/yr Finder File, any requester, amounts incl.) · **CO** ($305 Excel-on-CD, Jan, amounts suppressed, <$500 removed) · **OR** (Finder's List ≥$150/request, OAR 170-140-0020, no public republication — internal matching OK) · **WY** ($1,000, Jan + Jul, full amounts — richest small-state file) · **ND** (apparent-owner list by request, no values) · **WV** (FOIA list, name/city/state only) · **MI** (statutory locator file, MCL 567.256a — **≥$10k + 24 mo records only**) · **OH** (registered-finder portal).

**Confirmed NO (hard cites):** **WA** — flipped back to NO: RCW 42.56.070(8) bars commercial list release; state's asset-locator page says so verbatim (the RCW 63.30.300 public-search mandate ≠ bulk export). **VA** §55.1-2538 confidentiality (+ citizens-only FOIA). **AL** §35-12-94 — criminal-grade bar on publishing/divulging absent Treasurer authorization. **TN** §66-29-178 + locators must be TN-licensed PIs. **MS** Treasurer Rule 7.1 confidentiality; newspaper notice only. **PR** — OCIF, no published list; MissingMoney only. Plus prior: IL (FOIA-exempt), PA, SC, UT, MA, AZ; small "no program" states: OK KY MN KS NM DE RI DC IA HI NE ID NH AK MT ME SD VT + VI GU AS AE.

Deck slide 5 is now a YES/NO bubble chart (sized by member share); slide 6 headline = 7 of top 10 (~60%); slide 9 gates re-bucketed (LIVE / YES / BARRED / NO PATH).

> Pre-launch triage, not legal advice. Statutes verified against primary sources 2026-06-09; GA verified against SB 103 as enacted.
