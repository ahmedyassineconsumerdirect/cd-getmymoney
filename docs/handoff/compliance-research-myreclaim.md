# Compliance Research — myReclaim (Unclaimed-Property Feature on SmartCredit.com)

**To:** Consumer Direct Internal Legal
**From:** Compliance research (AI-generated draft for legal validation)
**Date:** 2026-05-08
**Subject:** Federal and state regulatory landscape for surfacing NAUPA / state unclaimed-property ("missing money") matches inside SmartCredit, with consumer claim assistance.
**Status:** Draft. All risk ratings preliminary. Open questions for legal flagged inline. Citations are entry points — verify before relying.

> **⚠️ Correction notice (2026-06-09):** a primary-source verification pass found several items below superseded or misread — see `docs/compliance/2026-06-09-deck-slides-5-8-9-legal-verification.md` before relying on this memo. Headlines: **GA** article rewritten by SB 103 eff. 7/1/2024 (§44-12-224 hold-funds text repealed; bulk data now CDR-registration-gated); **TX §74.507** hooks on a fee, not on "informing" (§9's reading is wrong); **NY §1416 has no 24-month restriction**; **CA §1582** voids agreements only between holder report and delivery (no "12-month" rule); **WA has no commercial-use bar** (RCW 63.29.350 repealed 1/1/2023); **FL's** live hook for a free alert product is §717.1322(1)(j) *compensated notification*, not §717.135.

---

## 0. Threshold Framing

Two structural facts drive most of the analysis:

1. **The feature lives inside a credit-monitoring product.** A reasonable consumer who sees a dollar figure inside a UI labeled "SmartCredit" and adjacent to credit data will infer the data was sourced and validated to credit-bureau standards. That inference creates §5 FTC Act / §1031 CFPA deception risk even where no FCRA accuracy duty technically attaches.
2. **The matching engine ingests NPI to query an external database.** Even if the UP source data is "public record," the *act of matching* uses GLBA-protected NPI (SSN, name, address, possibly DOB / financial-account fragments). That activity is "use" of NPI under Reg P §1016.3(u) and triggers Safeguards Rule scope.

There are two architectural decisions that, together, halve the legal surface:

- **"Guide to file" vs "file on behalf"** — guide-only avoids TSR §310.4(a)(3), most state finder-statute hooks, almost all assisted-claim tort exposure, and KYC/AML scrutiny.
- **Bundled subscription with no UP-tied fee** vs **percent-of-recovery** — bundled avoids ROSCA / negative-option exposure for the UP feature itself and is the only posture that plausibly clears all 50 state finder statutes; but the bundle theory is *not* a clean win on plain text and requires careful product engineering (see §3 and §10).

The recommended v1 posture is at the end (§11). Read the regime sections first.

---

## PART I — FEDERAL & CROSS-CUTTING REGIMES

## 1. FCRA (15 U.S.C. §1681 et seq.) and Regulation V (12 C.F.R. Part 1022)

### What the law requires

- **§1681a(d)(1)** — "consumer report" = communication of information by a CRA bearing on credit worthiness, character, etc., used or expected to be used for §1681b permissible purposes.
- **§1681a(f)** — CRA = entity that, for monetary fees, regularly engages in assembling or evaluating consumer credit information *or other information on consumers* for the purpose of furnishing consumer reports to third parties.
- **§1681e(b)** — accuracy: "reasonable procedures to assure maximum possible accuracy." Read both factually and impressionistically.
- **§1681i** — dispute / reinvestigation rights.
- **§1681m** — adverse action.
- **CFPB Spring 2024 Supervisory Highlights (Issue 32)** — heavy focus on §1681e(b) "maximum possible accuracy."
- **Data-broker rulemaking history:** CFPB's December 2024 NPRM that would have swept identifiers into "consumer report" was **withdrawn May 15, 2025 (90 FR 20893)**. The withdrawal preserves the narrower pre-existing reading but the agency did not disclaim the theory.
- **FCRA preemption:** CFPB's October 28, 2025 interpretive rule (90 FR 46091) *broadens* §1681t(b)(1) preemption.

### Application to myReclaim

Threshold: is UP-match data, surfaced by SmartCredit, "consumer report information"?

- **Likely not under text:** UP data does not bear on credit worthiness; it is surfaced direct-to-consumer (akin to a §1681g file disclosure, not a §1681b report).
- **Possibly under regulator theory:** §1681a(f)'s "or other information on consumers" hook + the (withdrawn-but-not-disclaimed) data-broker-NPRM theory could be invoked supervisorially against a CRA-reseller co-mingling UP data with credit-data infrastructure.
- **Bundling risk is the real exposure:** even if §1681e(b) does not directly attach, the consumer expectation of CRA-grade accuracy is enforceable under FTC §5 / CFPA §1031.
- **Reseller obligations** independently attach to any upstream CRA-reseller data feed used in the matching pipeline — those duties don't extend to the UP data itself but do govern whatever identity-verification feed makes the match possible.

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 1.1 | "Bundling-creates-expectation" deception risk: surfacing UP data inside the credit-monitoring UI without conspicuous disclosure that it is *not* part of the credit file and *not* held to FCRA accuracy standards | **MED-HIGH** |
| 1.2 | §1681e(b) by-analogy supervisory pressure | **MED** |
| 1.3 | Mishandled-dispute risk if users try to "dispute" inside SmartCredit and there is no clear pathway | **MED** |
| 1.4 | §1681m adverse-action exposure if a third party ever obtains the data and uses it adversely | **LOW** |

### Open questions

1. Does Consumer Direct's CRA-reseller status sweep UP data into "consumer report information" by virtue of co-mingling in shared infrastructure? **Most consequential FCRA question.**
2. Will the matching engine ever store UP-match outcomes in any record that touches the credit file or §1681b-furnished data?
3. Will any partner / affiliate / claims-recovery vendor ever receive UP-match data in a way that creates §1681m exposure?
4. Should we voluntarily extend §1681i-style dispute mechanics as a defensive UDAAP posture, even if not legally required?
5. Watch for any 2026 reproposal of the data-broker rule under a new CFPB director.

---

## 2. GLBA / Reg P (12 C.F.R. Part 1016) and FTC Safeguards Rule (16 C.F.R. Part 314)

### What the law requires

- SmartCredit is a "financial institution" under GLBA §6809(3); SSN + credit data + financial-account info are NPI under §6809(4) and Reg P §1016.3(q).
- **Reg P §1016.6** — privacy notices.
- **Reg P §1016.10–13** — opt-out for sharing NPI with non-affiliated third parties.
- **§1016.13 / §1016.14** exceptions — consumer consent; "as necessary to effect, administer, or enforce a transaction the consumer requests."
- **§502(c)** — redisclosure / reuse limit.
- **FCRA affiliate-marketing opt-out (§1681s-3)** — independent of GLBA.
- **FTC Safeguards Rule** as amended Nov. 13, 2023 (88 FR 77499, eff. May 13, 2024): notification-event reporting (≥500 consumers, 30 days), and the §314.4 written infosec program, MFA, encryption, vendor management, IR plan.

### Application to myReclaim

Two distinct flows:

- **Flow A — SmartCredit → external UP source for matching.** NPI sent outward.
  - State DB recipient: probably falls within §1016.14 transaction-necessity exception with §1016.13 belt-and-suspenders consent.
  - NAUPA / MissingMoney via vendor: non-affiliated third party; need DPA + §502(c) redisclosure limit.
- **Flow B — Match outcome stored at Consumer Direct.** Becomes NPI itself; in scope of Safeguards Rule §314.2(d).

**Privacy-notice update is non-negotiable** before launch — current SmartCredit GLBA notice almost certainly does not contemplate matching against external UP databases.

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 2.1 | Failure to update Reg P privacy notice prior to launch | **MED-HIGH** |
| 2.2 | Vendor-management / DPA gap with NAUPA aggregator or state APIs | **MED** |
| 2.3 | FCRA §1681s-3 affiliate-marketing opt-out exposure if any Consumer Direct affiliate uses UP-match data to market services | **MED** |
| 2.4 | Substantive §502(a) prohibition (likely satisfied by §1016.13/§1016.14) | **LOW** |
| 2.5 | Safeguards-Rule notification-event readiness (IR plan covers new flow) | **LOW-MED** |

### Open questions

1. Architectural: does the matching service run *inside* SmartCredit (NPI never leaves) or *at the aggregator* (NPI sent out)? Determines Reg P treatment.
2. If we send hashed identifiers, does that move us out of NPI sharing? (FTC's reading suggests no — hashing not exempted under amended Safeguards Rule.)
3. Just-in-time consent layer specifically for UP matching — recommend yes.
4. Affiliate channel for recovery service: §1681s-3 opt-out almost certainly triggered; design notice + opt-out now.

---

## 3. CFPB UDAAP (12 U.S.C. §§5531, 5536) & FTC Act §5 (15 U.S.C. §45)

This is the regime with the highest applied risk.

### What the law requires

- **§1031 CFPA** prohibits unfair/deceptive/abusive acts by covered persons offering consumer financial products. SmartCredit's credit monitoring is covered (12 U.S.C. §5481(15)(A)(vii)).
- **FTC §5** — unfair or deceptive practices, regardless of CFPA jurisdiction.
- **Deception:** misleading representation/omission, material to a reasonable-consumer decision.
- **Unfairness:** substantial injury, not reasonably avoidable, not outweighed by benefits.
- **Abusiveness (§1031(d)):** materially interferes with understanding; or takes unreasonable advantage of consumer reliance on the covered person to act in their interests. (See CFPB April 3, 2023 Policy Statement on Abusiveness.)
- **CFPB Circular 2023-01 (Jan. 19, 2023):** unlawful negative-option marketing — three risk categories (clear-and-conspicuous disclosure of material terms; informed consent; simple cancellation).
- **ROSCA (15 U.S.C. §§8401–8405)** §8403: negative-option internet charges require clear disclosure, express informed consent, simple cancellation. FTC enforces; CFPB reaches same conduct via §1031.
- **FTC Click-to-Cancel Rule (89 FR 90476, Oct. 2024)** was **vacated in its entirety by the Eighth Circuit on July 8, 2025 (Custom Communications, Inc. v. FTC, No. 24-3137)**. The 2024 rule is **not currently in force.** The 1973 Negative Option Rule (16 C.F.R. Part 425) and ROSCA remain. FTC reopened rulemaking late 2025 / early 2026.
- **Reference enforcement:**
  - *FTC v. Credit Karma, LLC* (final consent Jan. 2023; $3M) — deceptive "pre-approved" claims on a credit-monitoring platform. Direct precedent: probabilistic claims rendered as definite findings on a credit platform are deceptive.
  - *CFPB v. TransUnion* (2022 + 2024 supplemental) — dark-pattern enrollment in subscription credit-monitoring. (Note: 2017 consent order termination filed Nov. 2025.)
  - *FTC v. Credit Bureau Center, LLC* (refunds Nov. 2024) — fake rental ads + deceptive "free credit report" funnel.

### Application to myReclaim

Specific concern map:

1. **"We found $X for you" headline claims** on probabilistic matches — *Credit Karma* on point. **HIGH §5/UDAAP risk.** Mitigation: every match presented as "potential" with confidence indicator + state-direct-verification disclosure.
2. **Implied government affiliation** — surfacing data styled with state seals or "official-looking" UI is per-se §5 risk in the UP-finder context. Mitigation: prominent "SmartCredit is not affiliated with any state government" disclaimer.
3. **"Free finder" hook → auto-renewing subscription** — *Credit Karma + TransUnion + ROSCA* archetype. Every Circular 2023-01 risk category lights up. **HIGH risk.**
4. **Click-to-Cancel status:** vacated; build to that standard anyway because (a) re-promulgation is likely within planning horizon, (b) state laws (CA Bus. & Prof. §17602; NY GBL §527-a; etc.) impose comparable rules now.
5. **Abusiveness prong:** "tool to help you find your money" framing is fiduciary-flavored; monetization the user did not understand could be abusive even if not deceptive.
6. **Dark patterns** — pre-checked boxes, asymmetric cancel UX, friction-laden cancel funnels, false urgency ("claim before it expires" — UP doesn't typically expire) all map to specific enforcement themes.

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 3.1 | Definitive-amount claims on probabilistic matches (*Credit Karma* analogy) | **HIGH** |
| 3.2 | Negative-option / auto-renew funnel anchored on UP hook | **HIGH** |
| 3.3 | Implied government affiliation in marketing or UI | **HIGH** |
| 3.4 | Urgency / "you may lose this money" framing — most state UP regimes hold funds in perpetuity, false scarcity is classic §5 deception | **MED-HIGH** |
| 3.5 | Abusiveness exposure under §1031(d)(2)(C) reliance prong | **MED** |
| 3.6 | Affiliate / influencer marketing of the feature (see §4) | **MED** |
| 3.7 | Direct exposure under FTC Click-to-Cancel Rule (vacated; ROSCA + state laws fill the gap) | **LOW (post-vacatur)** |

### Open questions

1. Will any version of the funnel charge users incrementally for the UP feature (vs. bundling)? If yes, full ROSCA stack.
2. What confidence threshold are matches presented at? Below ~95%, "we found" is unsubstantiated under *Pfizer*.
3. Are we using state UP APIs / aggregators that contractually require disclaimers / official-portal links? May overlap with substantiation defense.
4. Voluntarily adopt vacated Click-to-Cancel standards? Recommended given likely re-promulgation + state law floor.

---

## 4. Advertising Substantiation & FTC Endorsement Guides (16 C.F.R. Part 255)

### What the law requires

- **Substantiation doctrine** (FTC 1984 Policy Statement; *In re Pfizer*, 81 F.T.C. 23 (1972)): reasonable basis at the time of claim. *Pfizer* factors: type of product/claim; consumer benefit; ease of substantiation; consequences of falsity; expert standard.
- **FTC Endorsement Guides, revised final June 29, 2023, effective July 26, 2023** (88 FR 48092):
  - "Endorsement" expanded broadly.
  - Material connections: disclose where a "significant minority" (FTC suggests 10% or less can be significant) wouldn't expect them.
  - "Clear and conspicuous" = "difficult to miss" and "unavoidable" in interactive media.
  - Influencer, advertiser, and intermediary liability all explicit.
- **April 13, 2023 FTC Notice of Penalty Offenses** to ~670 companies — aggressive substantiation enforcement posture.

### Application to myReclaim

- **"You may have unclaimed money"** — substantiation defense exists if matching algorithm has documented accuracy benchmarks and language is hedged ("may" / "potential"). Flat "you have $X waiting" without verification is unsubstantiated absent ~100% match confidence.
- **Aggregate / statistical claims** ("1 in 5 Americans has unclaimed property"; "$X billion lost") — must be sourced, current, methodologically sound. NAUPA stats can substantiate if cited accurately.
- **Endorsement & affiliate channels** — material-connection disclosures on every affiliate placement; influencer endorsements must reflect actual experience; 2023 Guides eliminate small-print disclosure defense.
- **Consumer testimonials** ("I found $4,200!") — must be representative or carry typicality disclosure; reflect honest opinion; disclose any material connection.

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 4.1 | Unsubstantiated "you have unclaimed money" claims absent verified match | **HIGH** |
| 4.2 | Influencer / affiliate disclosures not meeting 2023 "unavoidable" standard | **HIGH** |
| 4.3 | Testimonial typicality — featuring "$10K found" without representative-results disclaimer | **MED** |
| 4.4 | "Lost money" statistics without sourcing | **MED** |

### Open questions

1. Confidence threshold + methodology + sampling protocol for the matching engine — get documented and timestamped before launch (this *is* the substantiation file).
2. Influencer / affiliate channels in launch plan? Draft disclosure language and noncompliance enforcement protocol now.
3. Testimonial vetting — track actual recovered amounts to substantiate any displayed testimonial.

---

## 5. TSR (16 C.F.R. Part 310) and TCPA (47 U.S.C. §227)

### What the law requires

- **TSR §310.4(a)(3)** — prohibits requesting/receiving payment for goods or services represented to recover or assist return of money paid for / promised to a consumer in a previous transaction, **until 7 business days after delivery** to the consumer. **The 2010 amendments (75 FR 48458, Aug. 10, 2010) eliminated the requirement that the prior loss arise from telemarketing** — recovery of any prior loss is in scope. Licensed-attorney exception only.
- **Inbound exemption (§310.6(b)(5)) does NOT apply** to recovery transactions per the 2010 amendments.
- **TCPA §227** + 47 C.F.R. Part 64.1200: prior express written consent for marketing autodialed/prerecorded calls/texts to wireless; prior express consent for informational.
- **FCC "one-to-one" consent rule** (89 FR 5098, Jan. 26, 2024): consent must be granted to one identified seller at a time. Vacated in part by *Insurance Marketing Coalition Ltd. v. FCC*, 122 F.4th 1322 (11th Cir. Jan. 24, 2025). **Status mid-2026: in flux post-IMC vacatur — do not rely on broad lead-generator consents.**
- **TCPA revocation:** new rules effective **April 11, 2025** (47 C.F.R. §64.1200(a)(10)) — revocation in any reasonable manner; defined keywords (stop, quit, revoke, opt out, cancel, unsubscribe, end) treated as explicit revocation; 10-business-day SLA. Limited waiver extended to Jan. 31, 2027 (FCC Second Extension Order, DA 26-12, Jan. 6, 2026).

### Application to myReclaim

- **Critical:** Does UP qualify as "money paid for by, or promised to" a consumer in a previous transaction? **Strong textual case yes** — UP arises from prior payroll, dormant accounts, escrow refunds, insurance proceeds; 2010 amendments expressly captured non-telemarketing recovery; finders are the canonical example.
- **Consequence:** if SmartCredit ever telemarkets the UP-finder service (outbound calls/SMS, or inbound with outbound conversion follow-up), §310.4(a)(3) bars **any fee** until 7 business days after the money is delivered. This kills any percentage-of-recovery model that takes its cut at filing time.
- **TCPA exposure:** any SMS / autodialed-voice outreach about "found money" requires prior express written consent (likely treated as marketing). Statutory damages $500–$1,500 per call/text under §227(b)(3).
- **Revocation infrastructure:** build per §64.1200(a)(10) now.

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 5.1 | TSR §310.4(a)(3) advance-fee ban likely reaches UP-recovery monetization. Pure-subscription-bundle posture mitigates; percent-of-recovery does not | **HIGH** |
| 5.2 | TCPA exposure on outbound SMS / call about "found money" without proper consent | **HIGH** |
| 5.3 | One-to-one consent ambiguity post-IMC — get express written consent specifically naming Consumer Direct / SmartCredit + UP feature | **MED-HIGH** |
| 5.4 | Revocation processing — coded keyword handler + 10-business-day SLA | **MED** |

### Open questions

1. **Critical:** how is SmartCredit compensated for the feature? Any percent-of-recovery / upfront-fee model is bet-the-feature §310.4(a)(3) risk. Recommend pure subscription bundle with consumer-facing "we don't charge a finder's fee."
2. Is the activity ever telemarketing? Pure web/email may avoid TSR; any outbound voice/SMS conversion pulls it in.
3. Compliant TCPA consent specifically for UP messaging at signup / opt-in.
4. Any FTC guidance distinguishing "consumer-self-service tools" from "finder services"?

---

## 6. CCPA / CPRA + 19+ State Comprehensive Privacy Laws

### What the law requires

- **CCPA (Cal. Civ. Code §§1798.100–.199.100), as amended by CPRA**, regs at 11 C.C.R. §§7000–7102.
- **Sensitive PI (§1798.140(ae))** includes SSN, driver's license, account login + access code, precise geolocation, racial/ethnic origin, etc. AB 947 (Jan. 1, 2024) added immigration status. **SmartCredit holds SSN and financial-account info — definitionally SPI.**
- **Right to limit SPI (§1798.121)** — "Limit the Use of My Sensitive Personal Information" link required.
- **CPPA Final Regulations (adopted July 24, 2025; OAL approval Sept. 22, 2025):**
  - Annual cybersecurity audit phased in (April 1, 2028 for >$100M revenue).
  - Risk assessments for "significant risk" processing (submissions due April 1, 2028).
  - ADMT opt-outs.
- **State patchwork:** CA, CO, CT, VA, UT, TX (TDPSA, eff. 7/1/2024 — opt-in for SPI under §541.101(b)(2)), IA, IN, TN, MT, OR, DE, FL, NH, NJ, KY, MD, MN, RI, NE — total 19+ state comprehensive laws as of late 2024.
- **GLBA exception** (CCPA §1798.145(e)) is *data-level*, not entity-level — non-GLBA flows (marketing of feature, retention metadata, analytics) remain CCPA-covered.
- **Deceased persons:** CCPA "consumer" = "natural person who is a California resident" — rights generally terminate at death; other state laws vary.

### Application to myReclaim

- UP matching processes SPI; non-GLBA-flow aspects are CCPA-covered.
- Risk-assessment trigger: matching SPI against external databases is "significant risk" — written risk assessment recommended even before 4/1/2028 deadline.
- Right to limit SPI: UP matching probably falls within "services reasonably expected" under §1798.121(a) *if* user opts in to feature; UX must respect SPI-limit signals.
- **Notice at collection** (§1798.100(a)) — at or before collection of SPI for the new UP-match purpose. Dovetails with §2 Reg P notice update.
- **Cross-state opt-outs:** most state laws require honoring Global Privacy Control. UP-match data flow to a third-party aggregator could be "sharing" even without monetary consideration in some states.
- **Decedent matches:** UP databases routinely contain decedent property. Surfacing decedent matches to non-authorized users is privacy + tort risk (see §7). Recommend suppression for v1.
- **Texas TDPSA** (eff. 7/1/2024) — affirmative opt-in for SPI under §541.101(b)(2).

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 6.1 | State-by-state notice + opt-out compliance for the UP feature; gaps create per-state private rights of action and AG enforcement | **MED-HIGH** |
| 6.2 | Decedent-data exposure if matching surfaces deceased relative's UP without authority verification | **MED** |
| 6.3 | GPC / SPI-limit signal handling must wire through to the feature | **MED** |
| 6.4 | Risk-assessment documentation gap (CPPA rules) | **MED** |
| 6.5 | TDPSA opt-in for SPI in TX | **LOW-MED** |

### Open questions

1. Does Consumer Direct meet thresholds in each of the 19+ state laws? Likely yes most; verify.
2. State-by-state launch list, with heightened-SSN states (NY SHIELD Act, MA 201 CMR 17.00) flagged.
3. Decedent matching policy — surface or suppress for v1.
4. Is UP-match flow "automated decisionmaking" under CPPA's ADMT rules? Probably not (matching, not eligibility), but document.

---

## 7. Tort Exposure

### What the law requires

- **Negligent misrepresentation** (Restatement (Second) §552): commercial purveyor of false information for guidance of others; reasonable foreseeable damages.
- **Defamation by implication / false light** (Restatement §652E): publicizing false-light matter highly offensive to a reasonable person, with knowledge or reckless disregard. ~30 states recognize false light.
- **Aiding-and-abetting fraud / civil conspiracy** if UP-matching service helps a bad actor file a false claim.
- **State UP-finder statutes with private rights of action**, plus general UDAP.

### Application to myReclaim

- **Wrong match → wasted notarization, postage, time:** consumer has out-of-pocket damages. Negligent-misrepresentation is viable even without FCRA. Class-action mechanics + state UDAP statutory minimums ($500–$2,000 per violation in many states) make aggregate exposure meaningful.
- **Surfacing wrong person's name (spouse, parent, namesake):** defamation-by-implication risk if surfacing implies financial irresponsibility (e.g., "unclaimed escrow refund from foreclosure" implies a foreclosure).
- **Assisted-claim filing liability:** state UP claim forms require sworn declaration under penalty of perjury. "Filing for you" + fraudulent claim → aiding-and-abetting exposure to the state and to the rightful owner (conversion).
- **Architectural distinction:** "we file for you" creates substantially more vicarious exposure than "we guide you to file."

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 7.1 | Negligent-misrepresentation class action on systemic match-quality issues (mitigation: substantiation file + verify-with-state disclosure + confidence indicator) | **MED** |
| 7.2 | Aiding fraudulent claim if user files inaccurately and we facilitated; higher in "we file for you" model | **MED** |
| 7.3 | Defamation / false-light — limited because audience is the consumer themselves; publication element weak | **LOW-MED** |
| 7.4 | Conversion exposure to rightful owner if wrong claim succeeds | **LOW** |

### Open questions

1. File-for-user vs guide-to-file? See §8.
2. Vendor reps & warranties on match quality + indemnification for false-positive damages.
3. Tort indemnity + limitation-of-liability clauses in TOS — extend beyond credit data.
4. State-by-state, are there "false UP claim" criminal statutes that run to a facilitator? (See §10; 2024 E.D. Cal. Tennessee Woman case shows criminal UP-fraud charges are live.)

---

## 8. Identity Verification & Claim Formalities

### What state UP statutes require (federal-level summary; state matrix in §10)

- Sworn claim form (typically notarized).
- Government-issued photo ID.
- Proof of last-known-address tied to the property record.
- For amounts above thresholds, additional documentation or in-person verification.
- For decedent property: certified death certificate + letters testamentary or affidavit of heirship.
- POA generally accepted but most state UP-finder statutes specifically regulate finder POAs (fee caps + filed disclosure agreements).
- **NIST SP 800-63-4 (April 2025)** — IAL2 generally appropriate. SmartCredit's KBA-based identity proofing likely already operates at IAL2.
- **Federal:** SSA SSN-verification API restricted to authorized parties; SmartCredit cannot use without specific authorization.

### Application to myReclaim

- **"We'll file it for you":** notarization or RON integration (Notarize.com, BlueNotary). Lob (per project memory) handles mailed letters but not notarization — separate vendor needed. POA must comply with each state's finder statute. Consumer Direct becomes agent with full liability for accuracy of sworn statement. **High tort exposure model.**
- **"We'll guide you to file":** SmartCredit produces personalized checklist, links to state portal, generates pre-filled "draft" forms, refers to notary. Liability shifts to consumer because consumer signs and submits. **Lower tort, lower TSR, lower finder-statute exposure.**
- **Identity verification continuity:** the same proofing done for SmartCredit account creation does **not** substitute for state-side verification. Don't market as if it does.
- **Decedent claims:** different and more complex flow. **Defer to Phase 2.**

### Risk-rated findings

| # | Finding | Risk |
|---|---|---|
| 8.1 | "File for you" without full SOP buildout (notarization vendor, state-specific POA, anti-fraud, KYC) — concentrated tort + criminal exposure | **HIGH** |
| 8.2 | "Guide to file" with inaccurate or out-of-date guidance | **MED** |
| 8.3 | Decedent matches without authority-verification protocol | **MED** |
| 8.4 | Identity-verification fraud — malicious user successfully claiming someone else's property | **LOW-MED** |

### Open questions

1. **Top-priority architectural decision:** "file for you" vs "guide to file." Recommend guide-only for v1.
2. Notarization workflow if file-for-you is ever added: which RON vendor, integration, cost allocation.
3. Decedent matches: surface or suppress for v1.
4. Consumer Direct is not an MSB, but assisting in fund recovery at scale could create FinCEN scrutiny; flag for AML counsel.

---

## PART II — STATE LAW

## 9. State Paid-Finder / Locator Statutes — Master Table

The single most important legal question for myReclaim is **statutory characterization**: nearly every state has a "paid-finder," "locator," "fee-for-recovery," or "abandoned property location service" statute triggered by **the act of charging consumers, in any form, in connection with locating or assisting in the recovery of unclaimed property** held by a state administrator. Most were drafted in the contingency-fee era (10–15% caps), but the operative hooks are broader:

- "agreement to locate, deliver, recover, or assist in the recovery" (CA, NY, NC, VA, CO, IL, WI, MN, MA, MO, MI, MD, GA, OH, DC)
- "fee or compensation for locating property" (VA §55.1-2542; MN ch. 345; OH §169.13)
- "service for a fee providing assistance to consumers for the purposes of locating and/or retrieving property" (NY APL §1416)

A **flat SmartCredit subscription that includes UP-finding** is, on plain text, "an agreement … for a fee … to locate, deliver, recover, or assist in recovery." A flat fee does not automatically take SmartCredit outside these statutes, and in many states (TX, CA, NY, OH, GA, NC, MA, MD, MI, MN, CO, WI, DC) the statute either **voids** any fee for property reported within 24 months, or **caps** the fee at a percentage of recovery — neither of which a flat subscription cleanly satisfies.

### Master table (verify each row against current statute text)

| State | Statute | Fee Cap | Dormancy / Timing Bar | Written Agt Rqd | Registration / License | Subscription model caught? |
|---|---|---|---|---|---|---|
| **CA** | Cal. Code Civ. Proc. **§1582** | 10% of recovered property | §1582 invalidates agreements between report-date and payment-to-owner. AB 2280 (2022) reduced record-access bar to 1 year post-publication. | Yes; signed by owner after disclosure of nature/value/holder | SCO investigator guidance | **Likely yes** — §1582 hook is "agreement to locate, deliver, recover, or assist in recovery." |
| **NY** | N.Y. Aban. Prop. Law **§1416** | 15% of recoverable property | Comptroller policy / APLSP rules | Yes; notarized; bold 12-pt disclosure that owner can claim free from OSC | "Abandoned Property Location Service Provider" (APLSP) registration with OSC | **HIGH-risk yes** — covers "any service for a fee providing assistance to consumers for the purposes of locating and/or retrieving property." |
| **TX** | Tex. Prop. Code **§74.507**; PI license under Tex. Occ. Code Ch. 1702 | 10% (services *include* expenses) | Industry sources cite 24-month bar via §74.508 — verify | Yes | TX DPS Private Security Bureau **PI license required** | **Likely yes** — "informs a potential claimant" reaches non-contingency activity. |
| **FL** | Fla. Stat. **§717.135** | 30% of claimed amount (raised post-2020) | Recovery-agreement / purchase-agreement model only | Yes; statutory form | Only **FL-licensed attorneys, FL CPAs, or FL-licensed PIs (Ch. 493)** may register as claimant's representatives | **Likely yes — and statutorily impossible to comply.** Three-profession channel. **HIGH for FL specifically.** |
| **IL** | 765 ILCS **1026/15-1301** *et seq.* (RUUPA Article 13) | 10% | 24-month bar from receipt by Treasurer | Yes | **IL Treasurer license + $100,000 fidelity bond** | **HIGH-risk yes.** |
| **PA** | 72 P.S. **§1301.11(g)** + **§1301.11a** | 15% (legislation pending to drop to 10%) | Verify | Yes; signed and acknowledged | **Certificate of Registration from PA Treasurer**; criminal-history attestation | **HIGH-risk yes** unless excepted (§1301.11(g) carve-out for fixed-fee/hourly engagements not contingent on recovery — *possible path*, needs PA-specific opinion). |
| **OH** | Ohio Rev. Code **§169.13** | No express %; statute voids covered agreements within 2 yrs | **24-month void** from report (§169.03(C)); **criminal — 1st-deg misdemeanor first offense, 5th-deg felony thereafter** | Implicit | Not licensed via UP regime | **HIGH-risk yes** for property reported within 24 months — **criminal exposure**. |
| **NJ** | N.J.S.A. **46:30B-106** (current section to verify) | Industry source: 20% within first 2 yrs, 25% thereafter (verify; unusually high) | 2-yr restriction | Yes | Registration required | **HIGH-risk yes**; cap is on % of recovery, not helpful for flat fee. |
| **MA** | M.G.L. **c. 200A §13** | 10% | **24-month void** from receipt by Treasurer; owner info to heir-finders not released until 24 months post-receipt | Yes; statutory disclosures | **Heir-finder registration with Treasurer**; $75/yr/report-year fee | **HIGH-risk yes.** 93A class-action friendly. |
| **GA** | O.C.G.A. **§44-12-224** | 10% of recovered property | **24-month** unenforceable from delivery to commissioner | Yes | Not licensed via UP regime | **HIGH-risk yes.** Notable: "All funds … shall be paid or delivered directly to the owner" — explicit no-fund-holding rule. |
| **WA** | RCW **63.29.350** (repealed 2022); replaced under new Ch. 63.30 RCW (eff. Jan. 1, 2023) | Old: 5% (lowest in country); enforcement via WA CPA Ch. 19.86 (per-se UDAP) | Verify replacement under Ch. 63.30 | Yes (under predecessor) | Verify status | **HIGH-risk yes.** 5% cap historically lowest; CPA hook = per-se "unfair or deceptive." Confirm 63.30 carries forward. |
| **CO** | C.R.S. **§38-13-1301** to **§38-13-1304** (RUUPA) | 10% | **24-month** unenforceable post-delivery | Yes; signed by owner | Listed on Treasurer Finder list | **HIGH-risk yes.** |
| **AZ** | A.R.S. **§44-313 / §44-327** (Title 44 Ch. 3, Revised AZ UP Act) | Industry source: 30% cap; locator must disclose 20% benchmark (verify) | 2-yr restriction | Yes | **Currently licensed PI required** | **HIGH-risk yes.** PI license is absolute gate. |
| **MI** | M.C.L. **§567.256** (Act 29 of 1995) + **§567.256a** | No express %; common-law/general principles | **24-month** unenforceable from payment | Yes | None via UP regime | **HIGH-risk yes** for first 24 months. |
| **NC** | N.C.G.S. **§116B-78** | **Lesser of $1,000 or 20%** | 24-month void from delivery to Treasurer | Yes; **notarized** by both owner and rep | **Annual $100 NC Treasurer registration + PI license through NC Private Protective Services Board (since Jan. 1, 2022)** | **HIGH-risk yes.** Dual licensing. $1K hard cap unusual. |
| **VA** | Va. Code **§55.1-2542** | 10% (after 36-month mark only) | **36-month absolute bar — strictest dormancy gate of any state** | Implicit | Not licensed | **HIGH-risk yes.** VA users see matches we cannot legally monetize for 36 months. |
| **MN** | Minn. Stat. **Ch. 345** | 10% | 24-month bar | Yes | None via UP regime | **HIGH-risk yes.** |
| **MO** | Mo. Rev. Stat. **Ch. 447** (esp. §447.581 — verify) | Treasurer-approved fee agreement required | 90-day record-access bar for fee-charging locators | Yes; submitted for Treasurer pre-approval | **Recovery-rep registration; standard fee agreement subject to Treasurer approval** | **HIGH-risk yes.** Pre-approval is invasive. |
| **WI** | Wis. Stat. **§177.1301** *et seq.* (RUUPA) | 10% | 24-month void from delivery | Yes; standard RUUPA disclosures incl. value before/after fee | Complaints route to DATCP | **HIGH-risk yes.** |
| **MD** | Md. Code Comm. Law **§17-325** | Implicit; no express % | **24-month** unenforceable | Implicit | Not licensed | **HIGH-risk yes** for first 24 months. |
| **DC** | D.C. Code **§41-163.01** (RUUPA) | Standard RUUPA 10% (verify) | Standard RUUPA 24-month (verify) | Yes | Verify | **HIGH-risk yes.** |
| **SC** | S.C. Code **§27-18-360** (Uniform Unclaimed Property Act, Title 27 Ch. 18) | **15%** of value returned to owner | **24-month void** from payment/delivery to administrator under §27-18-200 | Implicit | None via UP regime; SC Treasurer requires "reasonable assurance" records won't be used commercially before releasing owner names | **HIGH-risk yes.** Broad hook: "It is unlawful for any person to seek or receive … any fee or compensation for locating or purporting to locate any property…" **Criminal misdemeanor:** fine ≥ amount sought, up to 10× the fee, **or up to 30 days imprisonment**, or both. |

**Penalty patterns:** void contracts (universal); civil fines + AG injunctive (most); **criminal misdemeanor / felony in OH, PA (post-2015), and SC §27-18-360 (up to 30 days)**; UDAP per-se (WA 19.86; MA 93A).

### Subscription-model question

Plain-text reading of the 21 jurisdictions surveyed shows the statutory hooks are not contingency-specific:

- CCP §1582(a): "An agreement to locate, deliver, recover, or assist in the recovery of property…" — silent on consideration form.
- NY APL §1416: "any service for a fee providing assistance to consumers for the purposes of locating and/or retrieving property…" — captures fee-for-service of any pricing form.
- OH §169.13: "All agreements to pay a fee, compensation, commission, or other remuneration to locate, deliver, recover, or assist in the recovery of unclaimed funds…" — "or other remuneration" is intentionally catch-all.
- TX §74.507: "A person who informs a potential claimant that the claimant may be entitled to claim property … may not contract for or receive… more than 10%…" — operative trigger is *informing*.
- VA §55.1-2542: "It is unlawful for any person to seek or receive… for a fee or compensation for locating property…"

| Theory | Argument | Counter | Net Risk |
|---|---|---|---|
| **A. Subscription unrelated to UP recovery** — UP-finder is a free embedded informational feature | Consumer pays nothing *for* recovery; statutes target recovery-based monetization | Marketing copy will reference UP recovery; AG can subpoena product analytics showing UP drives conversion/retention; that is "remuneration to assist in recovery" or "service for a fee" | **MED-LOW** if (a) UP feature is genuinely free, (b) no upsell tied to recovery, (c) prominent state-direct disclosure on every match |
| **B. Subscription is in part for UP recovery assistance** — pricing decks or attribution treat UP as a paid feature | Honest characterization | Triggers every state; cannot satisfy 10–15% caps because cap is computed against recovery; **voids contract in every state with a void-clause** (CA, OH, GA, MA, NC, IL, WI, CO, MN, MD, MI, DC) | **HIGH** |
| **C. Recovery-time fee, %-based, within state caps + 24-month gates** | Compliant pathway in registered/licensed states | Requires registration in IL, PA, NC, FL, MA, NY, TX (PI), AZ (PI), MO; bonding in IL; FL channels through 3 professions only (likely insurmountable) | **MED**, operationally heavy; FL is hard block |

**Recommendation flag:** Theory A is **not a clean win** under plain text, but is defensible if the product is engineered so that:

1. UP search runs for *every* SmartCredit subscriber automatically — not gated by tier or upsell.
2. Each match shows prominent "free on state site" language meeting NY APL §1416 12-pt-bold standard everywhere.
3. SmartCredit never executes any agreement, POA, or claim form on behalf of the consumer.
4. **No** recovery-tied compensation, ever, in any form (incl. affiliate, referral, success-bonus).
5. No fees collected after the consumer has been notified of a match (critical in CA §1582(a)).

If any of these break, you are back at HIGH risk.

---

## 10. State UDAP, Data Sourcing, MTL, State Privacy

### 10.1 State UDAP statutes that frequently catch finder operations

| Statute | Key features | Hook |
|---|---|---|
| **Cal. Bus. & Prof. §17200 / §17500** | Unlawful, unfair, fraudulent + false advertising; 4-yr SOL; AG, DA, city attorney standing; restitution + injunctive | Lockyer/Connell 2001 alert is the template — official-looking solicitations, pre-payment, failure to disclose state-direct route |
| **NY GBL §349 / §350** | Deceptive acts + false advertising; AG and **private right of action** ($50 stat. damages or actual; trebled to $1,000 cap; attorneys' fees) | Frequently bundled with APL §1416 violations |
| **MA G.L. c. 93A** | UDAP; **treble damages** for willful; 30-day demand-letter mechanic | Pairs with Ch. 200A §13 — class-action friendly |
| **FL FDUTPA (§501.201)** | UDAP | Combines with §717.135 |
| **IL ICFA (815 ILCS 505)** | UDAP; AG + private | Pairs with RUUPA finder licensing |
| **TX DTPA (Bus. & Comm. Code §17.41)** | Deceptive trade; **economic + mental anguish damages**, treble for knowing | Pairs with §74.507 |
| **WA CPA (Ch. 19.86)** | Per RCW 63.29.350 (predecessor), excessive UP fee was **per se** unfair/deceptive | Statutorily cross-wired |

**No major state-AG finder action since 2020 surfaced in research** — most recent published activity is consumer alerts and the 2023–24 *MoneyGram* multistate (escheat-side, not finder-side). **CA SCO maintains a "Consumer Fraud Alerts" page** that periodically warns about specific finder operations — being named is operationally damaging absent litigation. **Open question:** check Westlaw / Lexis for recent AG settlements in OH, NC, PA, IL where finders operated unlicensed.

### 10.2 Data Sourcing & Licensing

#### MissingMoney.com / NAUPA

- **Operator:** Kelmar Associates LLC, on behalf of NAUPA (since November 2022; previously CheckFree/Fiserv from 1999–2022).
- Endorsed by NAUPA + NAST. Search covers 49 states + DC + PR + Alberta (HI does not participate).
- **No publicly cached commercial-use license, API, or data-license program** based on Wikipedia, NAUPA press releases, and Kelmar's own site. Site explicitly described as "without commercial pressure" / "no advertisements" / "no fee" — closed government-endorsed search portal not licensed for redistribution.
- **Risk:** any "use of MissingMoney.com data" by SmartCredit would require either a license (none published) or scraping the search UI / hitting state databases directly.
- **Trademark / endorsement risk:** displaying MissingMoney/NAUPA logos or implying official endorsement is **HIGH risk**.
- **Open question:** has Kelmar published a data-licensing program or API tier? Direct outreach may be warranted.

#### State UP Databases — automated-query posture (verified May 2026)

Four-bucket classification of state portals for myReclaim's automated matching engine:

**(a) Closed by operational block** — Cloudflare / WAF / CAPTCHA actively block non-browser fetchers:

| State | Block mechanism | Quote / detail |
|---|---|---|
| **PA** | **Explicit anti-bot/anti-AI policy + reCAPTCHA** | "The Pennsylvania Treasury Department has determined that the use of bots or AI (Artificial Intelligence) to request claim information or to submit a claim makes it impossible to properly confirm a claimant's identity… the Department will not respond to requests for claim information or claim submissions which are identified as having been made via a bot or AI." Search page presents reCAPTCHA. **Most restrictive of any state.** |
| **TX** | Cloudflare 403 on `/app/claim-search` | Bulk dataset gated behind written request to `up.dbrequests@cpa.texas.gov` requiring company info **and Texas PI license number** if applicable. SIFT (Secure Information File Transfer) is the only authorized channel. |
| **MA** | Cloudflare 403 on `/app/claim-search` and `/app/faq-general` | Kelmar SPA behind WAF |
| **MI** | Cloudflare 403 on `/app/claim-search` | New Kelmar SPA (relaunched May 2025) behind WAF |
| **GA** | Cloudflare timeout on `/app/claim-search` | Kelmar SPA behind Cloudflare |
| **MissingMoney.com** (baseline) | Cloudflare + AI bot blocklist | `robots.txt` blocks GPTBot, ClaudeBot, CCBot, Bytespider, Amazonbot, Applebot-Extended, Google-Extended, meta-externalagent via Cloudflare-managed rules; sets `ai-train=no`. `/en/terms`, `/app/faq-general`, `/en/about-us` all return HTTP 403 to programmatic fetch. |

**(b) Closed by statute** — portal itself may be reachable, but the statute prohibits commercial use of owner-name records:

| State | Statute | Effect |
|---|---|---|
| **SC** | **SC Code §30-2-50** (Family Privacy Protection Act) + Treasurer policy | Prohibits obtaining PI from a state agency for "the purpose of selling or marketing a consumer product or service" (telephone, mail, email). SC Treasurer requires **written assurance that records will not be used for a commercial purpose** before releasing the names/addresses list. Independent of §27-18-360's finder-fee rules. |
| **WA** | RCW non-commercial-list provisions | DOR is statutorily prohibited from releasing lists for commercial purposes; requestors must submit a **Declaration of Non-Commercial Purpose**. Custom compilations may carry a fee. |
| **AZ** | A.R.S. DOR policy | "The Department will not release information about property until it has received a signed claim form and evidence of ownership" — info isn't released until ownership is proven, which forecloses bulk match-and-notify. |
| **VA** | Va. Code §55.1-2542 | **Class 1 misdemeanor** for finder fees in the first 3 years; 10% cap thereafter. |

**(c) Gray zone** — no posted ToS prohibition, no aggressive Cloudflare 403 on the landing page, but no authorized API or bulk feed either: **FL, NY, IL, NC, NJ, OH**. Programmatic use sits in a CFAA gray zone — data is public record under each state's UPL, but the portals are SPAs not engineered for machine access, and CFAA risk attaches once a WAF challenge fires.

**(d) Authorized bulk path** — explicit, documented, machine-consumable feed:

| State | Path | Cost |
|---|---|---|
| **CA SCO** | Free weekly CSV at [sco.ca.gov/upd_download_property_records.html](https://www.sco.ca.gov/upd_download_property_records.html), five files split by value range plus "All properties", refreshed Thursdays | Free; no posted commercial-use restriction or attribution requirement |
| **TX** | Bulk dataset via written request to `up.dbrequests@cpa.texas.gov` (SIFT channel) | Free with PI license + written application |
| **GA** | DOR sells a list of all UP owners (price/format by request) | Purchased |

**California is the only state with a fully open, commercial-use-permissible bulk path.**

**Engineering posture for myReclaim:**

1. **Ingest CA's free CSV** for CA matches (current prototype path).
2. **Apply for TX bulk feed** under a registered Texas PI license if TX coverage is in scope.
3. **For all other states, do not server-side scrape.** Deep-link the member into the state portal rather than querying it programmatically.
4. **For SC, WA, AZ, VA specifically: do not match-and-notify** without legal review of the relevant non-commercial-use statute, even if the portal is reachable.
5. **PA is a hard stop** — the express anti-AI policy creates direct evidentiary exposure if Consumer Direct ever queried PA's portal with an AI/bot label in headers or logs.

**CFAA / state computer-trespass exposure:**
- *Van Buren v. United States*, 593 U.S. 374 (2021): CFAA "exceeds authorized access" limited to gates-up/gates-down barriers — does not criminalize ToS violations on public sites.
- *hiQ Labs v. LinkedIn*, 31 F.4th 1180 (9th Cir. 2022): scraping public data **not** a CFAA violation.
- **Net for SmartCredit:** scraping a public state UP UI is **LOW** federal CFAA risk.
- **State computer-trespass statutes** (CA Penal Code §502; TX Penal Code §33.02) generally interpreted in parallel post-Van Buren but state-AG-prosecutable. **Risk: LOW–MED.**
- **Contract claims** (breach of click-through ToS) and **copyright** (in compilations of public-domain data — *Feist* limits) remain available against scrapers.

#### "Official-source" / Endorsement Risk

**HIGH-risk concrete exposure.** State AGs (notably CA, MA, NY) have repeatedly targeted UP solicitations using "official-looking" letterhead, .gov-adjacent URL conventions, or implying state endorsement. Displaying state data with state seal, or in chrome resembling the state portal, is per-se UDAP. Required disclaimers on every match screen:

- "This information was sourced from [state]'s public unclaimed-property database. SmartCredit is not affiliated with or endorsed by [state] or any state agency."
- "You can search and claim property directly, free of charge, at [state's URL]."
- For NY users specifically: bold 12-pt warning per APL §1416(2)(c).

### 10.3 Claim Formalities

| Requirement | Pattern | SmartCredit implication |
|---|---|---|
| **Notarization** | Required in CA (≥$1,000 cash; all securities/SDB), NC (both owner and rep), GA POA, NY ≥$1,000 small-estate, MA, MO (recovery-rep agreements). Many states allow non-notarized for small claims. | RON integration (BlueNotary, Notarize) is **operationally required** for any "we'll handle filing" flow. **MED.** |
| **Government ID + SSN documentation** | Universal. CA requires proof-of-SSN doc with claim; AZ optional with denial risk; NJ requires both. | Triggers state privacy law + GLBA Safeguards. Consumers must explicitly upload, not pull from credit-bureau cache. |
| **Original signature vs e-signature** | Most states accept e-sig under modest values; some require wet sig + notarization above thresholds or for securities/SDB. CA and NC conservative. | Build for wet-sig print-and-mail fallback for high-value or securities. |
| **POA when filing on behalf** | Most states accept a statutory UP-specific POA (GA Form UP-1061, AL Limited POA, PA UP POA per 20 Pa.C.S. §5601). CA limits POAs to financial-affairs POAs accompanied by doctor's incapacity letter — very restrictive. | "We file on your behalf" is a tighter fit than "we guide you to file." For CA, POA-filing essentially blocked for healthy adults. **MED.** |
| **Estate / deceased-owner** | Universally different. Court-appointed executor/admin preferred. Small-estate affidavits with state caps (GA $15K; NV $25K; NY $1K). NC: POA-for-living-relative does **not** authorize claiming deceased's UP. | Estate flows are a **distinct legal track** — should NOT auto-flow through the same engine. **HIGH** if mishandled (filing as wrong party = false-claim exposure under **31 U.S.C. §3729 / state false-claims acts**, basis for the 2024 E.D. Cal. *Tennessee Woman* false-UP-claim guilty plea). |

**v1 recommendation:** surface match + link user to state's claim form **without filing on behalf**. "Filing on behalf" → v2, scoped initially to live owners only, individually-owned property only, claims under $1,000 cash, with state-by-state RON integration.

### 10.4 Money-Transmitter

Default best answer: **don't hold funds.** Direct flow of state UP payment → consumer (state-issued check / ACH) avoids MTL almost entirely.

If SmartCredit ever holds funds in transit:
- 49 states + DC have MTL statutes; most require licensure + bonding for "receiving money for transmission."
- Agent-of-payee exemption (CA, TX, others) generally requires written agreement designating the entity as agent — fragile under most state readings.
- **CSBS Money Transmission Modernization Act** (~24 states adopted as of 2026) provides some uniformity but does not automatically exempt UP-recovery flows.
- **GA §44-12-224** *expressly* requires that "all funds … located by a person to be compensated by the payment of such a fee shall be paid or delivered directly to the owner" — Georgia statutorily forbids holding funds. Equivalent provisions in several other states.

**Risk: HIGH** if SmartCredit holds funds; **LOW** if state pays consumer direct. **Recommend: never hold funds.** Confirm with legal that even "we charge our fee from your bank account 7 days after you confirm receipt" doesn't get caught (should be ordinary debit-authorization but verify per-state).

### 10.5 State Privacy Laws Affecting the Matching Step

SSN-based matching is the most regulated activity under state privacy law.

| State | Treats SSN as "sensitive"? | Pre-processing requirement |
|---|---|---|
| CA (CCPA/CPRA) | Yes (sensitive PI) | Right to **limit use and disclosure**; right to delete still applies; data-protection assessment required |
| CO (CPA) | Yes | **Opt-in consent** required for SPI processing |
| CT (CTDPA) | Yes | **Opt-in consent** |
| VA (VCDPA) | Yes | **Opt-in consent**; data-protection assessment |
| UT (UCPA) | Yes | Opt-out (lighter) |
| TX (TDPSA, eff. July 2024) | Yes | Opt-in for sensitive |
| OR (OCPA) | Yes | Opt-in |
| DE (DPDPA) | Yes | Opt-in |
| MT, IA, IN, TN, NH, NJ, MN, RI, MD, NE, KY (varying effective 2024–2026) | Most treat SSN as sensitive | Opt-in increasingly the norm |

Plus **state SSN-restriction statutes** (CA, AR, AZ, CT, IL, MD, MI, MN, MO, OK, TX, VA) restricting public posting, unencrypted transmission, etc.

**Practical implications:**

1. Privacy-notice update: every state with comprehensive privacy law requires the notice to disclose purposes of SPI processing. Add UP-matching with specificity. **LOW (work item).**
2. **Opt-in capture** for CO/CT/VA/TX/OR/DE residents specific to UP-matching, before running the match. Existing credit-monitoring consent does not extend.
3. Right to delete: stored matches must be deletable.
4. **Consumer Health Data laws** (WA My Health My Data, NV SB 370, CT SB 3) — likely **not** triggered.
5. **Data-broker registration:** CA, VT, OR, TX. SmartCredit likely already on these for credit monitoring; UP-matching unlikely to add but verify.

**Risk: MED.** Privacy compliance is well-trodden; the **opt-in** requirement in CO/CT/VA/TX/OR/DE is a real gating item that needs product engineering.

---

## 11. Consolidated Risk Register

| # | Finding | Risk | Section |
|---|---|---|---|
| 1 | "Bundling-creates-expectation" deception risk | **MED-HIGH** | §1 |
| 2 | Reg P privacy-notice update before launch | **MED-HIGH** | §2 |
| 3 | NPI sharing with non-affiliated aggregator (NAUPA / vendor) | **MED** | §2 |
| 4 | Definitive-amount claims on probabilistic matches (*Credit Karma*) | **HIGH** | §3 |
| 5 | Negative-option / auto-renew funnel anchored on UP hook | **HIGH** | §3 |
| 6 | Implied government affiliation in UI/marketing | **HIGH** | §3, §10.2 |
| 7 | False-urgency framing ("you may lose this money") | **MED-HIGH** | §3 |
| 8 | Unsubstantiated "you may have unclaimed money" claims | **HIGH** | §4 |
| 9 | Influencer / affiliate disclosures not meeting "unavoidable" standard | **HIGH** | §4 |
| 10 | TSR §310.4(a)(3) advance-fee ban reaches UP recovery | **HIGH** | §5 |
| 11 | TCPA exposure on outbound SMS/call about found money | **HIGH** | §5 |
| 12 | One-to-one consent ambiguity post-IMC | **MED-HIGH** | §5 |
| 13 | State-by-state notice + opt-out compliance | **MED-HIGH** | §6 |
| 14 | Negligent-misrepresentation class action on systemic match-quality | **MED** | §7 |
| 15 | "File for you" tort + criminal exposure | **HIGH** | §8 |
| 16 | Decedent matching without authority verification | **MED** | §6, §8, §10.3 |
| 17 | Flat-subscription model on its face caught by paid-finder statutes in all surveyed states | **HIGH** | §9 |
| 18 | Florida channels paid claim-assistance through 3 licensed professions only — SmartCredit cannot register | **HIGH (FL)** | §9 |
| 19 | TX, AZ, NC require **PI license** | **HIGH (TX/AZ/NC)** | §9 |
| 20 | OH §169.13 carries criminal penalty for finder activity within 24 months of report | **HIGH (OH)** | §9 |
| 21 | IL, PA, MA, NC, MO require registration; IL bonding $100K | **HIGH** | §9 |
| 22 | WA had 5% cap + per-se UDAP cross-wiring; replacement Ch. 63.30 status uncertain | **HIGH (WA)** | §9 |
| 23 | NY APL §1416 captures any "service for a fee providing assistance" — broadest hook in country | **HIGH (NY)** | §9 |
| 24 | Holding consumer funds en route triggers MTL in every state | **HIGH (mitigation: don't hold funds)** | §10.4 |
| 25 | UDAP exposure (CA 17200, NY GBL 349/350, MA 93A, FL FDUTPA, IL ICFA, TX DTPA) survives finder-statute analysis | **MED-HIGH** | §10.1 |
| 26 | MissingMoney.com has no published commercial-use license / API | **MED** | §10.2 |
| 27 | State-database scraping post-*Van Buren* — federal CFAA LOW; state computer-trespass + contract + copyright remain | **LOW–MED** | §10.2 |
| 28 | CO/CT/VA/TX/OR/DE require **opt-in** for SSN as sensitive PI | **MED** | §10.5 |
| 29 | Notarization gates in CA / NC / NY (≥$1,000) for "filed on behalf" | **MED** | §10.3 |
| 30 | Estate / deceased-owner mis-filing → criminal false-claim exposure | **HIGH** | §10.3 |

---

## 12. Open Questions for Legal (Consolidated)

### Most consequential

1. **FCRA characterization.** Does Consumer Direct's CRA-reseller status sweep UP data into "consumer report information" by virtue of co-mingled infrastructure? Outside FCRA counsel.
2. **Subscription-model characterization.** Has any state AG or court ruled on whether a flat-subscription credit-monitoring service that surfaces UP matches (and offers no separate UP fee) is a "service for a fee providing assistance to consumers for the purposes of locating and/or retrieving property" under NY APL §1416, or "an agreement to assist in recovery" under CCP §1582? **No case law found on point. Single most important open question for myReclaim.**
3. **Architectural decision: file-for-you vs guide-to-file.** Recommend guide-only for v1.
4. **Compensation model.** Any percent-of-recovery / upfront-fee model is bet-the-feature §310.4(a)(3) risk. Recommend pure subscription bundle with consumer-facing "we don't charge a finder's fee."

### State-statute verifications

5. PA §1301.11(g) carve-out: is fixed-fee, hourly, not-contingent-on-discovery genuinely exempted from PA's finder regime?
6. Florida: any path for non-attorney/CPA/PI to surface UP matches and offer ANY claim assistance? Read is no — verify.
7. Washington Ch. 63.30 replacement for repealed RCW 63.29.350 — does it carry forward the 5% cap and CPA cross-wiring?
8. CA AB 2280 (2022) — confirm current §1582 text vs the older "24-month" industry shorthand.
9. Texas §74.508 — verify 24-month finder bar and exact text.
10. NJ §46:30B-106 — verify fee-cap structure (industry source said 20%/25%, unusually high).
11. Arizona §44-313 vs §44-327 — confirm which section governs the fee cap.
12. State Treasurer "consumer fraud alert" pages (CA SCO, NY OSC, IL, PA, NC) — review for SmartCredit-adjacent named operators in past 24 months.

### Data licensing

13. **MissingMoney.com / Kelmar:** does an unpublished commercial program exist? Direct outreach.
14. State UP bulk-data programs — beyond CA, are any others available?

### Privacy / process

15. Architectural: matching service runs *inside* SmartCredit (NPI never leaves) or *at the aggregator* (NPI sent out)?
16. Just-in-time consent layer for UP matching — recommend yes.
17. State-by-state launch list, with heightened-SSN states (NY SHIELD Act, MA 201 CMR 17.00) flagged.
18. Decedent matching policy — surface or suppress for v1.

---

## 13. Recommended v1 Posture

Cleanest legal posture for v1:

1. **UP search is a free embedded informational feature** of SmartCredit — never tier-gated, never up-sold, never marketed as a recovery service. **Scope is alert + deep-link only.** We surface the match and embed a link to the state's official portal — the member files there directly. We never generate pre-filled forms, never take a POA, never handle claim documents, never assist with the filing.
2. **Match display:** state name, property type, dormancy date, value range (if state discloses), and **deep link to state's official claim portal**. No claim filing, no POA, no pre-filled forms, no agreement signed by user.
3. **Per-match disclaimer:** "Sourced from [state]'s public unclaimed-property database. SmartCredit is not affiliated with or endorsed by [state]. You can claim this property directly, free of charge, at [state URL]." For NY users, render the §1416 12-pt-bold variant.
4. **No definitive-amount claims** — every match labeled "potential," with confidence indicator, "verify directly with state" line.
5. **Match-confidence-aware UI** — never show "you have $X." Show "potential match — verify directly with [state]."
6. **Bundle, don't surcharge** — no incremental or contingent fees for UP recovery. Bundle into existing SmartCredit value prop. Avoids ROSCA-funnel and §310.4(a)(3).
7. **Substantiation file built before launch** — matching algorithm, accuracy benchmarks, false-positive rate, sampling methodology, timestamps.
8. **Updated GLBA privacy notice + just-in-time consent** before any user is matched.
9. **TCPA / TSR perimeter:** confine outreach about found money to channels with documented prior express written consent, one-to-one specificity. Build §64.1200(a)(10) revocation now.
10. **Decedent suppression for v1.** Phase 2 work item.
11. **Data sourcing:** prefer state direct (CA bulk CSV; per-state search calls). Avoid MissingMoney.com unless license obtained from Kelmar/NAUPA. No NAUPA / MissingMoney trademark display.
12. **Funds:** never held by SmartCredit — state pays consumer direct.
13. **Mailed letter rail (Lob).** Mailed letters that promote UP recovery are the **highest-risk artifact** under "official-looking solicitation" UDAP theory. Letter design must be reviewed by legal with the state-AG-targeted-template patterns (CA Lockyer/Connell 2001 alert; MA AG and MN AG warnings) in front of them. Avoid state seals, .gov-adjacent return addresses, "Important Notice from Your State" framing.
14. **State exclusions for v1:** consider excluding **FL** entirely (the licensed-profession channel makes any UP feature legally risky); consider gating **TX, AZ, NC** to read-only display absent a PI-license partner.
15. **Open-issue tracker.** The questions in §12 are not rhetorical — they need legal answers tracked and closed before launch sign-off.

---

## Sources

### Statutes & Regulations (Federal)

- [15 U.S.C. §1681a](https://www.law.cornell.edu/uscode/text/15/1681a) — definitions
- [FCRA (FTC, May 2023 PDF)](https://www.ftc.gov/system/files/ftc_gov/pdf/fcra-may2023-508.pdf)
- [15 U.S.C. §1681e](https://www.law.cornell.edu/uscode/text/15/1681e)
- [12 C.F.R. Part 1016 (Reg P)](https://www.consumerfinance.gov/rules-policy/regulations/1016/)
- [16 C.F.R. Part 314 (Safeguards Rule)](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-C/part-314)
- [16 C.F.R. §310.4 (TSR)](https://www.law.cornell.edu/cfr/text/16/310.4)
- [16 C.F.R. Part 255 (Endorsement Guides)](https://www.ecfr.gov/current/title-16/chapter-I/subchapter-B/part-255)
- [Endorsement Guides 2023 final rule (Federal Register, July 26, 2023)](https://www.federalregister.gov/documents/2023/07/26/2023-14795/guides-concerning-the-use-of-endorsements-and-testimonials-in-advertising)
- [Safeguards Rule 2023 amendments (Federal Register, Nov. 13, 2023)](https://www.federalregister.gov/documents/2023/11/13/2023-24412/standards-for-safeguarding-customer-information)

### CFPB Guidance & Enforcement

- [CFPB Circular 2023-01 (Negative Option)](https://www.consumerfinance.gov/compliance/circulars/consumer-financial-protection-circular-2023-01-unlawful-negative-option-marketing-practices/)
- [CFPB Policy Statement on Abusiveness (April 2023)](https://www.consumerfinance.gov/compliance/supervisory-guidance/policy-statement-on-abusiveness/)
- [CFPB Spring 2024 Supervisory Highlights, Issue 32](https://files.consumerfinance.gov/f/documents/cfpb_supervisory-highlights_issue-32_2024-04.pdf)
- [CFPB FCRA File Disclosure advisory opinion (Jan. 2024)](https://www.federalregister.gov/documents/2024/01/23/2024-00786/fair-credit-reporting-file-disclosure)
- [CFPB FCRA Background Screening advisory opinion (Jan. 2024)](https://www.federalregister.gov/documents/2024/01/23/2024-00788/fair-credit-reporting-background-screening)
- [CFPB Data Broker Rule NPRM (Dec. 2024)](https://www.federalregister.gov/documents/2024/12/13/2024-28690/protecting-americans-from-harmful-data-broker-practices-regulation-v)
- [CFPB Data Broker Rule Withdrawal (May 2025)](https://www.federalregister.gov/documents/2025/05/15/2025-08644/protecting-americans-from-harmful-data-broker-practices-regulation-v-withdrawal-of-proposed-rule)
- [CFPB FCRA Preemption Interpretive Rule (Oct. 2025)](https://www.federalregister.gov/documents/2025/10/28/2025-19671/fair-credit-reporting-act-preemption-of-state-laws)
- [CFPB FCRA Preemption Flip Analysis (Nov. 2025)](https://www.consumerfinancialserviceslawmonitor.com/2025/11/the-cfpbs-fcra-preemption-flip-what-it-means-for-consumer-reporting/)

### FTC Enforcement

- [FTC Credit Karma Final Order (Jan. 2023)](https://www.ftc.gov/news-events/news/press-releases/2023/01/ftc-finalizes-order-requiring-credit-karma-pay-3-million-halt-deceptive-pre-approved-claims)
- [FTC Credit Karma Complaint (Sept. 2022)](https://www.ftc.gov/news-events/news/press-releases/2022/09/ftc-takes-action-stop-credit-karma-tricking-consumers-allegedly-false-pre-approved-credit-offers)
- [FTC Credit Bureau Center Refunds (Nov. 2024)](https://www.ftc.gov/news-events/news/press-releases/2024/11/ftc-sends-refunds-consumers-harmed-credit-bureau-centers-fake-rental-property-ads-deceptive-promises)
- [FTC MoneyGram Refunds (Feb. 2023)](https://www.ftc.gov/news-events/news/press-releases/2023/02/more-115-million-refunds-sent-consumers-result-ftc-doj-charges-moneygram-failed-crack-down-scams)
- [FTC Substantiation Policy Statement (1984)](https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation)
- [Click-to-Cancel Vacatur — Latham & Watkins](https://www.lw.com/en/insights/eighth-circuit-vacates-ftc-click-to-cancel-rule-days-before-compliance-deadline)
- [Click-to-Cancel Vacatur — Sidley](https://www.sidley.com/en/insights/newsupdates/2025/07/us-ftc-click-to-cancel-rule-struck-down)
- [FTC Negative Option Rulemaking Restart — Gibson Dunn](https://www.gibsondunn.com/ftc-restarts-negative-option-rulemaking-after-eighth-circuit-vacatur-enforcement-under-rosca-continues/)

### TCPA / FCC

- [FCC TCPA Revocation Rules](https://www.fcc.gov/document/tcpa-rules-revoking-consent-unwanted-robocallsrobotexts)
- [FCC One-to-One Consent Implementation](https://www.americascreditunions.org/blogs/compliance/tcpa-one-one-consent-rule-effective-january-2025)
- [FCC TCPA Limited Waiver Extension (Jan. 2026)](https://docs.fcc.gov/public/attachments/DA-26-12A1.pdf)

### CCPA/CPRA & State Privacy

- [California AG Privacy / CCPA Hub](https://oag.ca.gov/privacy/ccpa)
- [CPPA Final Regulations](https://cppa.ca.gov/regulations/ccpa_updates.html)
- [CCPA Cybersecurity Audit Rule Analysis — Ropes & Gray (Jan. 2026)](https://www.ropesgray.com/en/insights/alerts/2026/01/californias-ccpa-cybersecurity-audit-rule-takes-effect-what-businesses-need-to-know)
- [CPPA Final Rules — Morgan Lewis (Aug. 2025)](https://www.morganlewis.com/pubs/2025/08/cppa-board-finalizes-new-rules-on-admt-cybersecurity-audits-and-risk-assessments)
- [Privacy Law Recap 2024 — Perkins Coie](https://perkinscoie.com/insights/update/privacy-law-recap-2024-state-consumer-privacy-laws)
- [State Privacy Laws 2025-26 Tracker — Bloomberg Law](https://pro.bloomberglaw.com/insights/privacy/state-privacy-legislation-tracker/)
- [Sensitive PI emerging requirements — Benesch](https://www.beneschlaw.com/insight/privacy-points-2023-different-sensitive-personal-information-rights-requirements-emerge-in-new-us-state-data-protection-laws/)
- [GAO — SSN Federal & State Restrictions](https://www.gao.gov/assets/a112177.html)

### State Paid-Finder Statutes

- [Cal. Code Civ. Proc. §1582 (FindLaw)](https://codes.findlaw.com/ca/code-of-civil-procedure/ccp-sect-1582/)
- [SCO Investigator Guidance](https://sco.ca.gov/upd_investigator_about.html)
- [N.Y. Aban. Prop. Law §1416 (FindLaw)](https://codes.findlaw.com/ny/abandoned-property-law/abp-sect-1416/)
- [NY OSC APLSP Requirements (PDF)](https://www.osc.ny.gov/files/unclaimed-funds/claimants/pdf/aplsp-requirements-and-procedures.pdf)
- [Tex. Prop. Code §74.507 (Justia 2024)](https://law.justia.com/codes/texas/property-code/title-6/chapter-74/subchapter-f/section-74-507/)
- [Tex. Prop. Code Ch. 74](https://statutes.capitol.texas.gov/docs/PR/htm/PR.74.htm)
- [Texas DPS Heir-Finder Page](https://www.dps.texas.gov/section/private-security/heir-finders-and-investigations-related-unclaimed-accounts)
- [Fla. Stat. §717.135 (current)](https://www.leg.state.fl.us/Statutes/index.cfm?App_mode=Display_Statute&URL=0700-0799/0717/Sections/0717.135.html)
- [765 ILCS 1026 (RUUPA)](https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=3794&ChapterID=62)
- [IL Treasurer Finder License](https://www.illinoistreasurer.gov/unclaimed-property-finder-applications/)
- [PA Treasury Finders](https://www.patreasury.gov/unclaimed-property/finders/)
- [PA Unclaimed Property Law (PDF)](https://www.patreasury.gov/pdf/unclaimed-property/UnclaimedProperty-Law.pdf)
- [Ohio Rev. Code §169.13](https://codes.ohio.gov/ohio-revised-code/section-169.13)
- [NJ Treasury Unclaimed Property Statute (PDF)](https://www.nj.gov/treasury/unclaimed-property/pdf/UPStatute.pdf)
- [M.G.L. c. 200A](https://malegislature.gov/Laws/GeneralLaws/PartII/TitleII/Chapter200A)
- [960 CMR 4.00 (MA Treasurer regulations)](https://www.mass.gov/doc/960-cmr-4-procedures-for-the-administration-of-abandoned-property/download)
- [O.C.G.A. — Ga. UCP FAQs](https://dor.georgia.gov/general-unclaimed-property-faqs)
- [RCW 63.29.350 (Justia 2022)](https://law.justia.com/codes/washington/2022/title-63/chapter-63-29/section-63-29-350/)
- [Wash. RCW Ch. 63.29 (full)](https://app.leg.wa.gov/rcw/default.aspx?cite=63.29&full=true)
- [C.R.S. §38-13-1304 (Justia 2022)](https://law.justia.com/codes/colorado/2022/title-38/article-13/part-13/section-38-13-1304/)
- [Colorado Treasurer Finder Info](https://unclaimedproperty.colorado.gov/app/finder-info)
- [A.R.S. Title 44 Ch. 3 RAUPA](https://az.elaws.us/ars/title44_chapter3)
- [AZ DOR Heir Finder Information](https://azdor.gov/unclaimed-property/owners-file-claim/heir-finder-information)
- [M.C.L. §567.256](https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-567-256)
- [N.C.G.S. §116B-78](https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_116B/GS_116B-78.html)
- [NC Property Finder Information](https://www.nccash.gov/property-finder-information)
- [Va. Code §55.1-2542](https://law.lis.virginia.gov/vacode/title55.1/chapter25/section55.1-2542/)
- [Minn. Stat. Ch. 345](https://www.revisor.mn.gov/statutes/cite/345)
- [Mo. Rev. Stat. §447.547](https://revisor.mo.gov/main/OneSection.aspx?section=447.547)
- [15 CSR 50-3.090 (MO recovery rep regs)](https://www.law.cornell.edu/regulations/missouri/15-CSR-50-3-090)
- [Wis. Stat. §177.1301](https://law.justia.com/codes/wisconsin/chapter-177/section-177-1301/)
- [Maryland UCP General Information](http://comptroller.marylandtaxes.gov/Public_Services/Unclaimed_Property/General_Information/)
- [DC Code Title 41 Ch. 1A RUUPA](https://code.dccouncil.gov/us/dc/council/code/titles/41/chapters/1A)
- [S.C. Code §27-18-360 (Justia 2025)](https://law.justia.com/codes/south-carolina/title-27/chapter-18/)
- [S.C. Code Title 27 Ch. 18 (SC Legislature)](https://www.scstatehouse.gov/code/t27c018.php)
- [SC Treasurer — Unclaimed Property](https://treasurer.sc.gov/what-we-do/for-citizens/unclaimed-property-program/)

### State UDAP & Enforcement

- [Cal. Bus. & Prof. §17200 (LegInfo)](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=17200.&lawCode=BPC)
- [N.Y. GBL §349 (FindLaw)](https://codes.findlaw.com/ny/general-business-law/gbs-sect-349/)
- [Mastering MGL c. 93A — Greenberg Traurig](https://www.gtlaw.com/en/insights/2024/4/published-articles/mastering-massachusetts-general-laws-chapter-93a-the-massachusetts-consumer-protection-act-part-iii)
- [CA AG/Controller 2001 Alert](https://oag.ca.gov/news/press-releases/attorney-general-lockyer-and-controller-connell-issue-alert-unclaimed-property)
- [CA SCO Consumer Fraud Alerts](https://www.sco.ca.gov/upd_consumer_fraud_alerts.html)
- [E.D. Cal. — TN Woman Pleads Guilty to False UP Claims](https://www.justice.gov/usao-edca/pr/tennessee-woman-pleads-guilty-filing-false-claims-unclaimed-property)

### Data Sourcing & Licensing

- [MissingMoney.com](https://missingmoney.com/)
- [MissingMoney.com — Wikipedia](https://en.wikipedia.org/wiki/MissingMoney.com)
- [NAUPA — relaunch announcement](https://unclaimed.org/nast-and-naupa-relaunch-missingmoney-com/)
- [Kelmar Associates](https://www.kelmarassoc.com/)
- [CA SCO — Bulk CSV download](https://www.sco.ca.gov/upd_download_property_records.html)
- [hiQ v. LinkedIn — Goodwin analysis](https://www.goodwinlaw.com/en/insights/blogs/2022/04/ninth-circuit-web-scraping-does-not-violate-cfaa)
- [Van Buren — Apify analysis](https://blog.apify.com/van-buren-v-united-states/)
- [White & Case — hiQ post-Van Buren](https://www.whitecase.com/insight-our-thinking/web-scraping-website-terms-and-cfaa-hiqs-preliminary-injunction-affirmed-again)

### Claim Formalities

- [CA SCO — Claiming Guidelines (PDF)](https://www.sco.ca.gov/files-upd/guide_upd_claiming.pdf)
- [NY OSC — Deceased & Estate Claims](https://www.osc.ny.gov/unclaimed-funds/claimants/claims-deceased-owners-and-estates)
- [WI DOR — Heirship Claims](https://www.revenue.wi.gov/Pages/FAQS/ucp-heirs.aspx)
- [Ohio — Claiming for Deceased](https://com.ohio.gov/divisions-and-programs/unclaimed-funds/claiming-funds/claimant-resources/claiming-on-behalf-of-deceased-person)
- [NJ Claim Documentation](https://www.nj.gov/treasury/unclaimed-property/claimdocumentation.shtml)
- [AZ Claim Filing](https://azdor.gov/unclaimed-property/owners-file-claim/filing-claim)
- [NV Small Estate Affidavit (PDF)](https://www.nevadatreasurer.gov/uploadedFiles/treasurer.nv.gov/content/Unclaimed_Property/Forms/Claimant/UP-45_Small_Estate_Affadavit-Interactive.pdf)
- [FL Estate Affidavit (PDF)](https://fltreasurehunt.gov/files/Estate-Affidavit.pdf)

### Substantiation & Endorsement

- [FTC Pfizer / Substantiation Background — Lexology](https://www.lexology.com/library/detail.aspx?g=45fb4464-d88e-40f1-b1fc-d46d4d062f5c)
- [FTC Notice of Penalty Offenses — Buchanan Ingersoll & Rooney](https://www.bipc.com/ftc-issues-notice-of-penalty-offenses-companies-on-notice-to-substantiate-product-and-advertising-claims)
- [How to Substantiate Advertising Claims — Davis Wright Tremaine (2024)](https://www.dwt.com/insights/2024/03/how-to-substantiate-advertising-claims)

### Industry / Tort

- [Lexology — UP Hot Topics 2025](https://www.lexology.com/library/detail.aspx?g=bd843e87-dfbb-4fc8-aef4-e93f9e418a01)
- [Texas AG — 30-State MoneyGram Settlement](https://www.texasattorneygeneral.gov/news/releases/attorney-general-ken-paxton-announces-30-state-settlement-end-interstate-unclaimed-property-0)
- [Baker Tilly — UP State-by-State Guide](https://www.bakertilly.com/insights/unclaimed-property-state-by-state-guide)
- [McDermott — RUUPA finalized](https://www.mcdermottlaw.com/insights/unclaimed-property-act-finalized/)
- [ABA Business Law — RUUPA constitutional issues](https://www.americanbar.org/groups/business_law/resources/business-law-today/2018-february/the-revised-uniform-unclaimed-property-act/)
- [False Light — LII / Cornell](https://www.law.cornell.edu/wex/false_light)
- [Aspen Policy Academy — Posthumous Data Privacy (2024)](https://aspenpolicyacademy.org/wp-content/uploads/2024/11/phosthmous-data-privacy-v6.pdf)

---

*End of memo. AI-generated draft for legal validation. Verify all citations and risk ratings before relying. Open questions in §12 should be tracked and closed before launch sign-off.*
