"""Presentation helpers: human-readable labels, pretty case, NAUPA decoding.

The CA SCO data exposes raw codes ("MS09: CREDIT BAL - ACCTS RECEIVABLE") and
ALL-CAPS holder strings ("CITIBANK N A"). This module decodes those into
member-facing labels with categorical icons and proper title casing.
"""
from __future__ import annotations
import os
import re

from app.state_data import STATES


# NAUPA-ish category map. Codes vary slightly by state; the prefix group
# is always reliable. Keys are exact codes; the fallback uses the 2-char
# prefix.
CATEGORY_BY_CODE: dict[str, tuple[str, str, str]] = {
    # (icon_key, friendly_label, accent_color)
    # MS — Misc / Credit / Wages
    "MS01": ("briefcase", "Unpaid Wages", "blue"),
    "MS02": ("briefcase", "Commissions Owed", "blue"),
    "MS03": ("briefcase", "Pension or Retirement", "indigo"),
    "MS09": ("wallet", "Credit Balance", "blue"),
    "MS17": ("wallet", "Unidentified Deposit", "blue"),
    # UT — Utility
    "UT01": ("zap", "Utility Deposit", "amber"),
    "UT02": ("zap", "Membership Fee Refund", "amber"),
    "UT03": ("rotate", "Utility Refund", "green"),
    "UT04": ("zap", "Capital-Credit Distribution", "amber"),
    # IN — Insurance
    "IN01": ("shield", "Insurance Refund", "indigo"),
    "IN02": ("shield", "Life Insurance Proceeds", "indigo"),
    "IN03": ("shield", "Insurance Claim Payment", "indigo"),
    "IN05": ("shield", "Insurance Premium Refund", "indigo"),
    "IN06": ("shield", "Disbursement", "indigo"),
    # AC — Account credit
    "AC01": ("wallet", "Checking Account", "blue"),
    "AC02": ("wallet", "Savings Account", "blue"),
    "AC03": ("wallet", "Matured CD", "blue"),
    # SC — Securities
    "SC01": ("chart", "Stock Dividend", "violet"),
    "SC02": ("chart", "Bond Interest", "violet"),
    "SC04": ("chart", "Equity Securities", "violet"),
    # CK / SV — checking, savings
    "CK01": ("wallet", "Checking", "blue"),
    "SV01": ("wallet", "Savings", "blue"),
    # TR — trust
    "TR01": ("archive", "Trust Distribution", "violet"),
    # CT — court / govt
    "CT01": ("scales", "Court Deposit", "slate"),
    # ED — education
    "ED01": ("book", "Education Savings", "indigo"),
}

CATEGORY_BY_PREFIX: dict[str, tuple[str, str, str]] = {
    "MS": ("wallet", "Credit / Miscellaneous", "blue"),
    "UT": ("zap", "Utility", "amber"),
    "IN": ("shield", "Insurance", "indigo"),
    "AC": ("wallet", "Account Balance", "blue"),
    "SC": ("chart", "Securities", "violet"),
    "CK": ("wallet", "Checking", "blue"),
    "SV": ("wallet", "Savings", "blue"),
    "TR": ("archive", "Trust", "violet"),
    "CT": ("scales", "Court / Government", "slate"),
    "ED": ("book", "Education", "indigo"),
    "HS": ("shield", "Health Savings", "indigo"),
    "WG": ("briefcase", "Wages", "blue"),
}


def friendly_property(value: str | None) -> dict:
    """Decode a CA SCO property_type ('MS09: CREDIT BAL - ACCTS RECEIVABLE')
    into {icon, label, sub, color}."""
    if not value:
        return {"icon": "dollar", "label": "Unclaimed property", "sub": "", "color": "blue"}

    m = re.match(r"^([A-Z]{2}\d{1,2}):\s*(.*)$", value.strip())
    if m:
        code, desc = m.group(1), m.group(2).strip()
        sub = _title_case_keep_short(desc)
        if code in CATEGORY_BY_CODE:
            icon, label, color = CATEGORY_BY_CODE[code]
            return {"icon": icon, "label": label, "sub": sub, "color": color}
        prefix = code[:2]
        if prefix in CATEGORY_BY_PREFIX:
            icon, label, color = CATEGORY_BY_PREFIX[prefix]
            return {"icon": icon, "label": label, "sub": sub, "color": color}
        return {"icon": "dollar", "label": "Unclaimed property", "sub": sub, "color": "slate"}

    # No code — just the description
    return {"icon": "dollar", "label": _title_case_keep_short(value), "sub": "", "color": "blue"}


_KEEP_UPPER = {"NA", "USA", "LLC", "LLP", "INC", "CO", "IRA", "PNC", "JP", "AT", "AAA", "BNP",
               "CD", "BOA", "TIAA", "ASCAP", "BMI", "RBC"}


def pretty_holder(value: str | None) -> str:
    """Title-case a holder name but keep entity suffixes formatted nicely.
    'CITIBANK N A' -> 'Citibank, N.A.'
    'WELLS FARGO BANK NA (CALIFORNIA FOREIGN)' -> 'Wells Fargo Bank, N.A.'
    """
    if not value:
        return "Unknown holder"
    s = value.strip()
    # Strip parenthetical qualifiers like "(CALIFORNIA FOREIGN)" — noise to a member
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    # Tokenize, rebuild
    tokens = s.split()
    out: list[str] = []
    for i, tok in enumerate(tokens):
        clean = re.sub(r"[^A-Z0-9]", "", tok)
        if clean in _KEEP_UPPER:
            # Format common suffixes
            if clean == "NA":
                out.append("N.A.")
            elif clean == "INC":
                out.append("Inc.")
            elif clean == "CO":
                out.append("Co.")
            else:
                out.append(clean)
        elif clean.isdigit():
            out.append(clean)
        else:
            out.append(tok.capitalize())
    # Ensure entity suffix is preceded by a comma for banks
    s = " ".join(out)
    s = re.sub(r"\s+(N\.A\.|Inc\.|LLC|LLP|Co\.)$", r", \1", s)
    return s


def pretty_name(value: str | None) -> str:
    """Title-case a person name; keep 1-letter middle initials capitalized."""
    if not value:
        return ""
    return _title_case_keep_short(value)


def pretty_city(value: str | None) -> str:
    if not value:
        return ""
    return _title_case_keep_short(value)


def _title_case_keep_short(value: str) -> str:
    """Title-case but keep tokens that are 1-letter (initials) or in KEEP_UPPER."""
    tokens = value.strip().split()
    out: list[str] = []
    for tok in tokens:
        clean = re.sub(r"[^A-Z0-9]", "", tok.upper())
        if len(clean) <= 1:
            out.append(tok.upper())
        elif clean in _KEEP_UPPER:
            out.append(clean)
        elif clean.isdigit():
            out.append(clean)
        else:
            # Preserve hyphenated parts: "ESPERANZA" -> "Esperanza"
            out.append("-".join(part.capitalize() for part in tok.split("-")))
    return " ".join(out)


# Inline SVGs (Lucide-style line icons, 24x24, currentColor stroke).
ICONS: dict[str, str] = {
    "wallet": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-2"/><path d="M3 7h18a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H3"/><circle cx="17" cy="12" r="1"/></svg>',
    "briefcase": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>',
    "rotate": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 14l4-4 4 4 5-6"/></svg>',
    "archive": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="5" x="2" y="3" rx="1"/><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/><path d="M10 12h4"/></svg>',
    "scales": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M2 16l3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2a4 4 0 0 0 4-4"/><path d="M21 7h-2a4 4 0 0 1-4-4"/></svg>',
    "book": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
    "dollar": '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
}


# Tailwind-class tints per accent color
TINT_BG: dict[str, str] = {
    "blue":   "bg-brand-light",
    "amber":  "bg-amber-50",
    "green":  "bg-emerald-50",
    "indigo": "bg-indigo-50",
    "violet": "bg-violet-50",
    "slate":  "bg-slate-100",
}
TINT_FG: dict[str, str] = {
    "blue":   "text-brand",
    "amber":  "text-amber-600",
    "green":  "text-emerald-600",
    "indigo": "text-indigo-600",
    "violet": "text-violet-600",
    "slate":  "text-slate-600",
}


def render_icon(icon_key: str, color: str = "blue") -> str:
    """Return HTML for the icon-in-tinted-circle component."""
    svg = ICONS.get(icon_key, ICONS["dollar"])
    bg = TINT_BG.get(color, "bg-brand-light")
    fg = TINT_FG.get(color, "text-brand")
    return f'<div class="w-12 h-12 rounded-full {bg} {fg} flex items-center justify-center shrink-0">{svg}</div>'


# =========================================================================
# Handoff-spec helpers (docs/handoff/2026-04-28-match-result-row.md)
# =========================================================================

# Maps NAUPA-ish code prefix → handoff-spec icon key (file-text default).
# Spec §3.2 defines these icon files in app/templates/icons/.
_SPEC_ICON_BY_PREFIX: dict[str, str] = {
    "MS": "credit-card",   # default for MS family — overridden per code below
    "UT": "rotate-ccw",    # utility refunds
    "AC": "wallet",
    "CK": "wallet",
    "SV": "wallet",
    "IN": "shield",
    "SC": "credit-card",
    "TR": "shield",
    "WG": "briefcase",
    "ED": "shield",
}
_SPEC_ICON_BY_CODE: dict[str, str] = {
    "MS01": "briefcase",   # wages/payroll
    "MS02": "briefcase",
    "MS03": "shield",      # pension/retirement
    "MS09": "credit-card", # credit balance / accts receivable
}


def property_type_display(value: str | None) -> dict:
    """Decode a CA SCO property_type into {icon_key, label}.

    Returns the handoff-spec icon key (one of credit-card / briefcase /
    wallet / rotate-ccw / shield / file-text) plus a friendly label.
    """
    if not value:
        return {"icon_key": "file-text", "label": "Unclaimed property"}

    fp = friendly_property(value)
    # Find icon key — the existing CATEGORY_BY_CODE used different keys
    # ("wallet", "briefcase", etc.); spec's set is a superset / aliasing.
    m = re.match(r"^([A-Z]{2})(\d{1,2})?", value.strip())
    if m:
        prefix = m.group(1)
        code = (prefix + (m.group(2) or "")).upper()
        if code in _SPEC_ICON_BY_CODE:
            icon_key = _SPEC_ICON_BY_CODE[code]
        elif prefix in _SPEC_ICON_BY_PREFIX:
            icon_key = _SPEC_ICON_BY_PREFIX[prefix]
        else:
            icon_key = "file-text"
    else:
        icon_key = "file-text"
    return {"icon_key": icon_key, "label": fp["label"]}


# Source display per state — handoff §6.3 says
# "{State name} State Records" with the shield as the trust mark.
_STATE_NAMES: dict[str, str] = {
    "CA": "California",
    "TX": "Texas",
    "NY": "New York",
    "FL": "Florida",
    "GA": "Georgia",
    "IL": "Illinois",
    "OH": "Ohio",
    "PA": "Pennsylvania",
    "NJ": "New Jersey",
    "MA": "Massachusetts",
    "AZ": "Arizona",
    "MI": "Michigan",
    "MD": "Maryland",
    "TN": "Tennessee",
    "VA": "Virginia",
    "NC": "North Carolina",
    "SC": "South Carolina",
    "AL": "Alabama",
    "LA": "Louisiana",
    "MS": "Mississippi",
    "MO": "Missouri",
    "WA": "Washington",
}


def source_display(state_code: str | None) -> str:
    """Per handoff §6.3 — formats as '{State} State Records'."""
    code = (state_code or "CA").upper()
    name = _STATE_NAMES.get(code, code)
    return f"{name} State Records"


# Per-state claim portal URLs. The first version uses landing pages
# only; future iteration can add property-detail deep links per state.
_STATE_CLAIM_URLS: dict[str, str] = {
    "CA": "https://claimit.ca.gov/",
    "TX": "https://www.claimittexas.gov/",
    "NY": "https://www.osc.ny.gov/unclaimed-funds",
    "FL": "https://www.fltreasurehunt.gov/",
    "GA": "https://gaclaims.unclaimedproperty.com/",
    "IL": "https://icash.illinoistreasurer.gov/",
    "OH": "https://unclaimedfunds.ohio.gov/",
    "PA": "https://unclaimedproperty.patreasury.gov/",
    "NJ": "https://unclaimedfunds.nj.gov/",
    "AZ": "https://azdor.gov/unclaimed-property",
    "MI": "https://unclaimedproperty.michigan.gov/",
    "MD": "https://www.claimitmd.gov/",
    "TN": "https://unclaimedproperty.tn.gov/",
    "VA": "https://www.vamoneysearch.gov/",
    "NC": "https://www.nccash.com/",
    "SC": "https://southcarolina.findyourunclaimedproperty.com/",
    "AL": "https://treasury.alabama.gov/unclaimed-property/",
    "LA": "https://unclaimedproperty.la.gov/",
    "MS": "https://treasury.ms.gov/for-governments/unclaimed-property/",
    "MO": "https://treasurer.mo.gov/UCP/",
    "WA": "https://ucp.dor.wa.gov/",
    "MA": "https://findmassmoney.com/",
}


def claim_url(state_code: str | None, property_id: str | None = None) -> str:
    """Return the official state portal URL for filing a claim.

    The handoff spec §4.2 calls this a "deep-link" — for the prototype
    we link to each state's claim landing page. Property-detail deep
    links (where supported) are a follow-up.
    """
    code = (state_code or "CA").upper()
    info = STATES.get(code, {})
    return info.get("portal_url") or _STATE_CLAIM_URLS.get(code, "https://unclaimed.org/search/")


# =========================================================================
# State coverage + filing handoff (unsupported-state UI)
# =========================================================================

# States whose data myReclaim currently indexes. Everything else gets a
# guide-to-file handoff to the state's own official portal (compliant:
# display-only deep link, no fee, no representation).
SUPPORTED_STATES: set[str] = {"CA"}

# Per-state kill switch (compliance requirement #17): DISABLED_STATES="CA,TX"
# turns a state's search off at runtime — it falls back to the guide-to-file
# handoff — without a deploy, if a regulatory issue arises in that state.
_DISABLED_STATES = {
    s.strip().upper()
    for s in os.environ.get("DISABLED_STATES", "").split(",")
    if s.strip()
}
SUPPORTED_STATES -= _DISABLED_STATES

# Every known US state/DC code — used to whitelist the state form value so
# only trusted, table-sourced names ever reach the handoff template.
ALL_STATE_CODES: set[str] = set(STATES.keys())

# Generic, portal-agnostic filing steps — fallback when a state has no
# researched step list in app/state_data.py.
_GENERIC_STEPS: list[str] = [
    "Open your state's official unclaimed-property portal (linked below).",
    "Search your name — include former names, middle initials, and any prior cities.",
    "Open each result and confirm the reported owner, address, and amount look like you.",
    "Start a claim and verify your identity (photo ID, SSN, and proof of address as prompted).",
    "Upload any requested documents, submit, and save your claim/confirmation number.",
    "Track your claim's status on the same portal until the state pays you directly.",
]


def state_info(state_code: str | None) -> dict:
    """Everything the unsupported-state handoff panel needs for one state.

    Sourced from the researched app/state_data.py table (50 states + DC), with
    safe fallbacks for anything missing.
    """
    code = (state_code or "").upper()
    s = STATES.get(code, {})
    name = s.get("name") or _STATE_NAMES.get(code) or code
    return {
        "code": code,
        "name": name,
        "agency": s.get("agency") or f"the {name} unclaimed-property program",
        "portal_url": s.get("portal_url") or _STATE_CLAIM_URLS.get(code) or "https://unclaimed.org/search/",
        "steps": s.get("steps") or _GENERIC_STEPS,
        "processing_time": s.get("processing_time") or "30–90 days",
        "free_note": s.get("free_note") or "Claiming directly with the state is always free.",
        "supported": code in SUPPORTED_STATES,
    }


# Snapshot-diff status -> member-facing badge. Sourced from property_status
# (scripts/build_ca_snapshot.py). 'active' is the implicit default.
# Legal: every claimable result is a "Potential match" (never definitive).
# 'new' is the same potential match, just flagged with a small "New" badge.
STATUS_DISPLAY: dict[str, dict] = {
    "new": {
        "label": "Potential match",
        "section": "new",
        "badge_class": "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
        "dot": "bg-emerald-500",
        "claimable": True,
        "is_new": True,
    },
    "active": {
        "label": "Potential match",
        "section": "active",
        "badge_class": "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
        "dot": "bg-emerald-500",
        "claimable": True,
        "is_new": False,
    },
    "claimed": {
        "label": "Already claimed",
        "section": "claimed",
        "badge_class": "bg-slate-100 text-slate-500 ring-1 ring-slate-200",
        "dot": "bg-slate-400",
        "claimable": False,
        "is_new": False,
    },
}


def status_display(status: str | None) -> dict:
    """Decode a property_status value into a member-facing badge dict."""
    return STATUS_DISPLAY.get((status or "active"), STATUS_DISPLAY["active"])


def amount_display(amount_min: float | None, amount_max: float | None) -> tuple[str, bool]:
    """Return (display_str, has_range) per handoff §3.6."""
    lo = amount_min if amount_min is not None else None
    hi = amount_max if amount_max is not None else None
    if lo is None and hi is None:
        return ("Undisclosed", False)
    if lo is None:
        return (f"${hi:,.2f}", False)
    if hi is None:
        return (f"${lo:,.2f}", False)
    if abs(lo - hi) < 0.005:
        return (f"${hi:,.2f}", False)
    return (f"${lo:,.2f}–${hi:,.2f}", True)


def address_display(addr: str | None, city: str | None,
                    state: str | None, zip_: str | None) -> str:
    """Compose a one-line address string with proper case.

    Returns empty string if all parts missing — caller hides the row.
    """
    parts: list[str] = []
    if addr:
        parts.append(_title_case_keep_short(addr))
    locality_bits: list[str] = []
    if city:
        locality_bits.append(_title_case_keep_short(city))
    if state:
        locality_bits.append(state.upper())
    if zip_:
        locality_bits.append(zip_.strip())
    if locality_bits:
        parts.append(" ".join(locality_bits) if state else ", ".join(locality_bits))
    return ", ".join(parts) if parts else ""
