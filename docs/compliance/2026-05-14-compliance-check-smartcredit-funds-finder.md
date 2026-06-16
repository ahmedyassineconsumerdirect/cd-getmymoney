# Compliance Check: CD Funds Finder → smartcredit.com

**Date:** 2026-05-14
**Requested by:** Ahmed Yassine (Consumer Direct)
**Reference spec:** [`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](../planning/2026-04-27-cd-funds-finder-design.md)

## Feature parameters

| Field | Value |
|---|---|
| Audience | Authenticated SmartCredit members only |
| Existing internal precedent | Privacy Master / Privacy Scan (member-initiated data-broker matching with "not mine" / "remove" workflow) |
| Storage model | Pre-computed nightly member ↔ possible-match table |
| Notifications | Email and/or SMS planned (Phase 1) |
| Matching keys | First name + last name + state + city |
| Results framing | "Possible match" — never "found money" |
| **v1 scope (LOCKED)** | **Present potential matches only.** No fee (ever, in any form), no claim filing, no POA, no claim handling, no agreement signed by the member. Member files directly on the state's own portal. |
| Claim path | Deep-link to the state's official portal (claimit.ca.gov for CA; the member's home-state portal for other states). No fee; no claim handling. |
| Initial state coverage | California (SCO bulk files from claimit.ca.gov / sco.ca.gov). Other states: deep-link only, no data ingestion required. |

## Summary

> **Scope decision (locked 2026-06-02):** v1 will **present potential matches only** — no fee, no filing, no POA, no claim handling. This is the lowest-risk posture and it collapses the bulk of the finder/locator-statute surface (see "Effect of the display-only scope decision" below). It does **not** resolve three residual items that are independent of display: the FCRA matching question (§ FCRA row), per-state data-acquisition restrictions, and the §5/UDAAP presentation requirements (framing, non-affiliation disclaimer, accuracy).

**Assessment: Proceed with conditions.**

Four structural decisions in the design materially reduce the regulatory surface area:

1. **"Possible match" framing** keeps the feature away from the most acute UDAAP/FTC §5 risk that would attach to "we found money for you."
2. **The Privacy Master / Privacy Scan precedent** gives the program an internal legal pattern to extend — same regulatory shape as the existing broker-removal feature: match member identity against external public/semi-public records, present as candidates, let the member act or dismiss.
3. **Matching only on first + last + state + city** means no new sensitive PII is processed (no DOB, no SSN, no addresses beyond what's already on the state's own public portal).
4. **Deep-link only** — no fee, no claim handling — keeps the feature structurally outside most state finder/locator statutes.

Three items deserve special focus as launch gates:

- **TCPA / CAN-SPAM consent** for the email/SMS notification channel. SMS "you have a possible match" alerts are promotional in nature and require prior express written consent under FCC marketing rules. Wrong here = $500–$1,500 per text in TCPA private actions.
- **Match-quality presentation.** First + last + state + city against millions of records will generate many candidate matches for common names ("John Smith in San Diego, CA" — possibly hundreds of distinct individuals). The "possible match" framing is necessary but not sufficient; presentation must show the candidate count and acknowledge ambiguity.
- **The pre-computed nightly match table** is a new GLBA-covered store (member identity ↔ possible property record). Encryption at rest, access logging, DSR workflow coverage, and SOC 2 scope expansion all apply.

### Effect of the display-only scope decision

Locking v1 to "present matches only, no fee, no filing" neutralizes the highest-severity items in this review:

| Risk class | Why display-only resolves it |
|---|---|
| **State finder/locator fee caps & 24-month void clauses** (CA §1582, GA, etc.) | These hook on a *fee* for recovery. No UP-tied fee = nothing to cap or void. |
| **FL §717.135 licensed-profession channel** | Regulates *paid claimant's representatives*. Not a paid rep ⇒ likely outside the statute. **Moves FL from "exclude" to "deep-link likely OK"** — pending counsel confirmation and the residual "informing" hook below. |
| **PI-license gates for paid recovery (TX/AZ/NC)** | Same — gated on paid claim representation. |
| **TSR §310.4(a)(3) advance-fee ban** | No fee for recovery, so the advance-fee prohibition does not attach. |
| **File-on-behalf tort + false-claim criminal exposure** | Member signs and files directly; no agency relationship, no sworn statement made by us. |

**What display-only does NOT resolve** (independent of what we present — still tracked below):

1. **FCRA matching question** — risk attaches to *matching member NPI against UP records*, regardless of what is then displayed. Top open legal question.
2. **"Informing a claimant" hooks** — e.g., TX §74.507 triggers on *informing* a potential claimant, not on charging a fee. Thin residual; confirm with counsel before TX.
3. **Per-state data-acquisition restrictions** — SC/WA/AZ/VA non-commercial-use statutes and PA's anti-bot policy limit how data is *obtained*, not how it is shown. Deep-link (don't ingest) in those states.
4. **§5 / UDAAP presentation rules** — "possible match" framing, non-affiliation disclaimer, false-positive/common-name handling all apply *because* we display.

---

## SmartCredit context (extracted from smartcredit.com)

| Item | Observation |
|---|---|
| Platform | "Powered by the ConsumerDirect® Platform" — Consumer Direct is the FCRA-covered parent entity |
| Visible feature set (public) | Credit reports/scores/monitoring (3-bureau), Identity Theft Insurance, Credit Dispute, Money Manager, Action Buttons (patented), Loan Marketplace (MyLoNa) |
| Existing privacy-side feature | Privacy Master / Privacy Scan — sits inside authenticated app; legal pattern Funds Finder will mirror |
| Educational pages | "Who's Looking", Credit 101, Debt 101 — informational only |
| Existing disclosures | Service Agreement, Terms of Use, Privacy Policy, Security; CCPA-compliant cookie preferences; multilingual (EN/ES/FR/JA) |
| Existing disclaimer pattern | "Any credit scores, score changes or available plus points shown or inferred are estimates only. Individual results and speed of results may vary, and results are not guaranteed." — directly transferable shape for "Possible match" results |

There is a clear product slot for Funds Finder — "another action SmartCredit members can take, surfaced inside the authenticated app, deep-linked to the action portal" — that mirrors both Privacy Master (broker removal) and the credit-dispute flow (deep-link to bureaus). Funds Finder fits this product grammar, which reduces novelty risk.

---

## Applicable Regulations and Policies

| Regulation / Policy | Relevance | Key Requirements |
|---|---|---|
| **State Unclaimed Property Acts (UPA) — finder/locator provisions** | CA CCP §1582 caps finder fees at 10% after 12 months post-escheat; TX Prop. Code §74.507 caps at 10%; NY ABP §1416 caps at 15%; FL F.S. §717.135 caps at 20%. Some states regulate even fee-free locator activity. | Counsel opinion that a **free, member-only, deep-linking, dismiss-able "possible match"** service is outside each state's locator definition. CA first; TX, NY, FL before respective rollouts. |
| **FCRA (15 U.S.C. §1681 et seq.)** | Member data obtained under §1681b(a)(2) permissible purpose. Unclaimed-property search is not a "consumer report" use. **The Privacy Master / Privacy Scan precedent likely already establishes the secondary-use posture.** | Confirm Privacy Master's authorization scope covers Funds Finder. If yes, no new consent flow needed. |
| **GLBA Privacy Rule (16 CFR Part 313) + Safeguards Rule (16 CFR Part 314)** | Consumer Direct is a "financial institution." The pre-computed nightly match table is NPI (member identity ↔ possible property record). | Update privacy notice. Apply Safeguards Rule controls (encryption, access controls, audit logging) to the match table. |
| **CCPA / CPRA** | Member CA PI is processed. No "sale"; no "share" for cross-context advertising. The new stored match table must be covered by DSR workflows. | Privacy notice category update. Wire the match table into existing access/deletion/correction request flows. |
| **CFPA / Dodd-Frank §1031 (UDAAP)** | "Possible match" framing addresses the principal risk. Residual: presenting many candidates for common names without confidence cues could still mislead. | Test results UX with a high-volume common name. Add visible confidence/ambiguity language and a "Not mine" dismiss affordance per candidate. |
| **FTC Act §5** | Backstop for UDAAP. | Same as CFPA. |
| **TCPA + state mini-TCPA (FL FTSA, OK)** | Email/SMS "you have a possible match" notifications are promotional. SMS requires prior express written consent for marketing under FCC rules. | **Launch gate.** Confirm members specifically opted in. Honor STOP/opt-out. Maintain consent audit trail. |
| **CAN-SPAM** | Email notifications must include sender ID, physical address, and an opt-out link honored ≤10 business days. | Inherit from existing SmartCredit email infrastructure. Add a specific "Funds Finder alerts" opt-out category. |
| **State omnibus privacy laws (VCDPA, CPA, CTDPA, UCPA, TDPSA, OR, MT, etc.)** | Triggered as state coverage expands. | Inherit from existing program. Add the new processing purpose to per-state notices where required. |
| **State CRO/CSO laws** | TX, IL, OK, GA regulate credit-services organizations. | Confirm no amendment to existing registrations triggered. |
| **California SCO bulk-data terms of use** | Ingesting https://claimit.ca.gov/upd-property-records/. | Confirm terms allow ingestion + presentation. CA unclaimed property is public record per Gov. Code §6253, but ToS may layer in restrictions. |
| **Federal source data terms (future)** | Treasury, PBGC, FDIC, HUD-FHA, DOL EBSA, NCUA. PBGC and FDIC are historically the most restrictive. | Out of scope for the California launch; flag for the 2027 federal-sources milestone. |
| **State seal / agency-mark usage** | Deep-link to claimit.ca.gov is fine; rendering the SCO seal is not. | UX audit; explicit non-affiliation disclaimer. |

---

## Requirements

| # | Requirement | Status | Action Needed |
|---|---|---|---|
| 1 | Confirm CA SCO bulk-file ToS permits ingestion, storage, and presentation to authenticated members | **Unknown** | Legal review of sco.ca.gov / claimit.ca.gov terms; written inquiry to SCO if ambiguous. |
| 2 | Counsel opinion that CCP §1582 (and surrounding) does not regulate a free, member-only, deep-linking, dismiss-able service | **Likely Met (display-only scope)** | Display-only/no-fee posture removes the fee-cap hook in most states. Remaining counsel scope narrows to the "informing a claimant" hooks (e.g., TX §74.507). Confirm before TX; FL likely outside §717.135 absent a fee. |
| 3 | Privacy Master / Privacy Scan authorization language covers Funds Finder processing (secondary use of member identity for external-records matching) | **Likely Met** | Privacy/Legal review of existing Privacy Master member-facing consent + service agreement. If language is feature-specific, extend it. |
| 4 | Privacy notice categorical update to disclose Funds Finder processing | **Not Met** | Add to existing GLBA + CCPA notices. Likely a small delta given the Privacy Master parallel. |
| 5 | Results UX presents candidates clearly, with no implied certainty and no implied government affiliation | **Partially Met** | Final copy review. Require "possible" in every match presentation; show match-count caveats for common names ("47 records that may match someone named John Smith in San Diego, CA — verify on claimit.ca.gov"). |
| 6 | "Not mine / dismiss" affordance per candidate (mirroring Privacy Master) | **Not Specified in spec** | Add. (a) reduces false-positive friction, (b) gives member agency, (c) extends the Privacy Master pattern, (d) creates labeled-data signal for matcher improvement. |
| 7 | Pre-computed match table — encryption at rest, access controls, audit logging | **Not Met** | InfoSec to extend Safeguards Rule controls already covering member NPI. |
| 8 | Match table covered by DSR workflows (CCPA/CPRA, VCDPA, CPA, etc.) | **Not Met** | Engineering + Privacy: ensure access/delete/correct requests reach the match table. |
| 9 | Email/SMS notification consent — granular "Funds Finder alerts" opt-in (TCPA prior express written consent for SMS marketing; CAN-SPAM for email) | **Not Met** | Granular preference category, default-off, per-channel, STOP/opt-out honored, audit trail. |
| 10 | Notification copy review (UDAAP, §5, TCPA classification) | **Not Met** | Subject lines and SMS body must use "possible match" framing; must not imply funds are guaranteed or that action is urgent. |
| 11 | DPIA / PIA covering Funds Finder processing | **Not Met** | Privacy Office. Likely short given the Privacy Master analog. |
| 12 | SOC 2 scope expansion: match table + matching service added to in-scope inventory | **Not Met** | SOC 2 program owner; next audit window. |
| 13 | Member T&Cs delta: warranty disclaimer on match accuracy, "we don't file claims, charge no fee, take no POA" language | **Not Met** | Legal to draft. Pattern from existing "credit scores are estimates" disclaimer is directly transferable. The locked display-only scope makes this language straightforward (state plainly what we do *not* do). |
| 14 | UX audit: no state seals, no "official" framing, explicit "not affiliated with any government agency" notice | **Not Met** | Design + Legal review. |
| 15 | Vendor / sub-processor scope: Snowflake DPA already covers Consumer Direct processing | **Met (likely)** | Confirm scope; add any new dependency (dbt Cloud, scheduled-job platform) to sub-processor list. |
| 16 | Audit logging for the matching service (who queried whose data and when) | **Not Met** | Required under GLBA Safeguards Rule monitoring provisions. |
| 17 | Per-state kill-switch — disable Funds Finder per state if a regulatory issue arises | **Not Specified** | Engineering: feature flag per state, no-deploy toggle. |

---

## Risk Areas

| Risk | Severity | Mitigation |
|---|---|---|
| State locator-statute applicability — a state interprets the feature as an unregistered "heir finder" service despite being free | **Medium** (was High; reduced by display-only/no-fee scope) | Most statutes hook on a fee for recovery; the locked no-fee scope removes that hook. Residual: "informing a claimant" hooks (TX §74.507). Outside-counsel opinion narrowed to those; per-state kill-switch retained. |
| TCPA / SMS-marketing consent — member receives an unconsented "possible match" SMS | **High** | Specific opt-in for "Funds Finder alerts." Default-off, per-channel, STOP-handling, audit trail. TCPA private actions: $500–$1,500 per text. |
| False-positive UDAAP exposure — member acts on a candidate that isn't actually theirs | **Medium** | "Possible match" framing addresses the worst of it. Add explicit match-count language for common names and a "Not mine" dismiss affordance per candidate. |
| Common-name candidate inflation in dense markets — dozens-to-hundreds of candidates for a single member | **Medium** | City-level disambiguation hints; offer an optional disambiguator (street, year of birth) at member's choice; never require disclosure of new PII. |
| Data-source ToS violation (sco.ca.gov bulk files) — undisclosed restrictions on commercial use or republication | **Medium** | Document terms in writing now. If ambiguous, request written clarification from SCO. Comply with any attribution requirements. |
| Privacy notice mismatch — new processing purpose not reflected in member-facing privacy policy at launch | **Medium** | Privacy Master precedent covers most of the language; small delta. Hard launch gate. |
| Match table as new GLBA-covered store — encryption, access logging, DSR coverage gap | **Medium** | Extend existing Safeguards Rule controls; wire DSR workflows; add to SOC 2 scope. |
| CAN-SPAM email notification compliance | **Medium** | Inherit existing email infrastructure. Add specific opt-out category. |
| Implied government affiliation — UI inadvertently suggests SmartCredit is a state partner or claim processor | **Medium** | UX audit; explicit non-affiliation disclaimer; no state seals; avoid words like "official" or "authorized." |
| FCRA secondary-use gap — member data collected for credit monitoring used for non-credit purpose | **Low** | Privacy Master establishes the pattern. Confirm authorization scope with counsel. |
| Member-claim fraud enablement — surfaced match aids fraudulent claim filing | **Low** | We surface only what's already public on the state portal; the state's own portal handles ID verification. |
| Notification fatigue (UX/non-legal but related) — too many "possible match" alerts produce broad opt-outs that hurt other compliance metrics | **Medium** | Cap frequency; consolidate; respect preferences. |
| Federal source restrictions (future) — PBGC/FDIC data may have republication restrictions | **Medium (future)** | Re-run this compliance check before the 2027 federal-sources milestone. |
| Data staleness — member sees a match for a record the state has since paid out | **Low** | Weekly refresh; visible "Data last refreshed" indicator; state portal is authoritative. |

---

## Recommended Actions (priority order)

1. **Apply the Privacy Master / Privacy Scan legal precedent.** Have Privacy/Legal confirm in a one-page memo that the existing authorization, privacy notice, and member T&Cs language for Privacy Master extends to Funds Finder. If yes, this collapses requirements 3, 4, and 13 into a small delta.
2. **Outside-counsel opinion on California finder/locator framework** (CCP §1582 and surrounding) for a free, member-only, deep-linking, dismiss-able service. Repeat per state before each rollout.
3. **Confirm CA SCO bulk-file ToS** in writing — both sco.ca.gov and claimit.ca.gov.
4. **Wire up notification consent properly.** Add a "Funds Finder alerts" preference, default-off, granular per-channel (email vs SMS), with STOP-handling and audit trail. Highest-risk new item from the notification scope.
5. **Lock the match-presentation copy.** Every match displayed must include the word "possible" or "may match." Show candidate count for common names. Add a "Not mine" dismiss affordance per candidate (Privacy Master parity).
6. **Extend Safeguards Rule controls to the match table.** Encryption at rest, access logging, audit trail. Add to SOC 2 scope.
7. **DSR workflow update** so access/deletion requests reach the match table.
8. **DPIA / PIA** — likely short given the Privacy Master precedent.
9. **UX audit** for state-affiliation language and marks. Add "Not affiliated with or endorsed by any government agency" disclaimer near results and in notifications.
10. **Build the per-state kill-switch** before launch.

---

## Approvals Needed

| Approver | Why | Status |
|---|---|---|
| In-house counsel — Privacy | Privacy Master precedent extension memo, privacy notice delta, DPIA | Pending |
| Outside counsel (unclaimed-property specialist) | CA finder/locator statute opinion | Pending |
| In-house counsel — Consumer / Regulatory | UDAAP copy review, T&Cs delta, TCPA/CAN-SPAM notification compliance | Pending |
| Privacy Office | DPIA/PIA sign-off | Pending |
| InfoSec / CISO | Match-table security review + SOC 2 scope expansion | Pending |
| Product Marketing | "Possible match" copy and notification subject lines | Pending |
| Member Services | Runbook for "is this really mine?" / "how do I dismiss" questions | Pending |
| Engineering | Per-state kill-switch, notification preference plumbing, DSR coverage | Pending |

---

## Slide 7 — suggested language for the exec deck

The deck's "Compliance moat" slide can read credibly with this framing:

> **Favorable compliance posture, pending counsel sign-off**
>
> - Free + deep-link to the state portal = no claim handling, no finder fee, structurally outside most state locator statutes
> - "Possible match" framing + member dismiss affordance — same legal pattern as our existing Privacy Master broker-matching feature
> - Reuses existing SmartCredit identity controls and notification consent infrastructure — no new PII surface, no new auth
> - Source data is public record (CA Gov. Code §6253); we link claims back to the state's own portal
>
> Counsel review in flight for each state before rollout.

This is defensible in front of an executive audience without overclaiming.

---

## Out-of-scope reminders

Re-run this compliance check before:

- Adding TX, NY, FL, or any expansion state
- Adding any federal source (Treasury, PBGC, FDIC, HUD, DOL, NCUA)
- Surfacing any field beyond what's already on the state's public portal
- Changing the matching keys (adding DOB, partial SSN, address)
- Changing the framing from "possible match" to anything more assertive
- Removing the deep-link model in favor of an in-app claim flow

> **Important:** This is structured pre-launch compliance triage, not legal advice. Items flagged here should be reviewed by qualified counsel before launch.
