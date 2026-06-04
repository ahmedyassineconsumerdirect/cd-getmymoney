"""Get My Money Back assistant backend (MaxAI).

Two backends behind one service:

* **Demo** (default): a knowledge-driven guide built from app/assistant_kb.py.
  Works with zero configuration and is fully compliant — every answer keeps the
  "potential match / claim free with the state / no finder's fee / not
  affiliated" framing. This is what runs in the prototype.

* **Live Pine AI**: when a member connects a Pine account, we authenticate with
  Pine's built-in email-code flow (POST /api/v2/auth/email/{request,verify}) and,
  if the `pine-assistant` SDK is installed, relay messages to a real Pine session
  (AsyncPineAI over REST + Socket.IO). Any failure degrades gracefully to Demo.

The Pine REST/auth contract is documented in
github.com/19PINE-AI/pine-mcp-server and the pine-assistant SDK.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path

import httpx

from app.assistant_kb import KB
from app.db import get_connection
from app.match import DemoFuzzyMatcher
from app import presentation

PINE_BASE_URL = os.environ.get("PINE_BASE_URL", "https://www.19pine.ai").rstrip("/")
PINE_API = f"{PINE_BASE_URL}/api"

log = logging.getLogger("maxai")

# Pre-issued service creds (optional). If present we start in live mode.
ENV_TOKEN = os.environ.get("PINE_ACCESS_TOKEN")
ENV_USER_ID = os.environ.get("PINE_USER_ID")

# The member's saved Pine confirmation code. There is no in-app "connect" flow;
# the code is persisted here, and if Pine reports it expired we prompt for a new
# one in the server terminal (see prompt_for_code_if_expired). MaxAI works fully
# without it — the live Pine relay just stays off until a valid code is present.
_CODE_FILE = Path(__file__).resolve().parent.parent / "data" / "internal" / "maxai_pine_code.txt"
_DEFAULT_CODE = "6643"


def save_confirmation_code(code: str) -> None:
    try:
        _CODE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CODE_FILE.write_text((code or "").strip())
    except Exception:
        log.warning("MaxAI: could not persist confirmation code to %s", _CODE_FILE)


def load_confirmation_code() -> str | None:
    code = os.environ.get("PINE_CONFIRMATION_CODE")
    if code:
        return code.strip()
    try:
        if _CODE_FILE.exists():
            return _CODE_FILE.read_text().strip() or None
    except Exception:
        pass
    return None


# Persist the provided code on first run so it survives restarts.
if not load_confirmation_code():
    save_confirmation_code(_DEFAULT_CODE)


# --- Persisted Pine session (access token + user id) --------------------
# A completed login (scripts/pine_login.py) is stored here so the live Pine
# search survives restarts. ENV vars still win if set.
import json as _json  # noqa: E402

_TOKEN_FILE = _CODE_FILE.parent / "maxai_pine_token.json"
_PENDING_FILE = _CODE_FILE.parent / "maxai_pine_pending.json"


def save_tokens(access_token: str, user_id: str, email: str | None = None) -> None:
    try:
        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_FILE.write_text(_json.dumps(
            {"access_token": access_token, "user_id": user_id, "email": email}))
    except Exception:
        log.warning("MaxAI: could not persist Pine token to %s", _TOKEN_FILE)


def load_tokens() -> dict | None:
    try:
        if _TOKEN_FILE.exists():
            d = _json.loads(_TOKEN_FILE.read_text())
            if d.get("access_token") and d.get("user_id"):
                return d
    except Exception:
        pass
    return None


def save_pending(email: str, request_token: str) -> None:
    _PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PENDING_FILE.write_text(_json.dumps({"email": email, "request_token": request_token}))


def load_pending() -> dict | None:
    try:
        if _PENDING_FILE.exists():
            return _json.loads(_PENDING_FILE.read_text())
    except Exception:
        pass
    return None


def prompt_for_code_if_expired(reason: str = "") -> None:
    """Surface a clear terminal prompt when the saved code needs refreshing."""
    log.warning(
        "MaxAI: Pine confirmation code needs refreshing%s. "
        "Update it via:  echo <new-code> > %s   (or set PINE_CONFIRMATION_CODE). "
        "MaxAI keeps working in the meantime.",
        f" ({reason})" if reason else "", _CODE_FILE,
    )


# ---------------------------------------------------------------------------
# Demo knowledge brain
# ---------------------------------------------------------------------------
# State names (lower) -> code, for "other state" detection in the assistant.
from app.state_data import STATES  # noqa: E402

_STATE_NAME_TO_CODE = {v["name"].lower(): code for code, v in STATES.items()}
# Longest names first so "west virginia" matches WV before bare "virginia" (VA).
_STATE_NAMES_BY_LEN = sorted(_STATE_NAME_TO_CODE.items(), key=lambda kv: -len(kv[0]))


def _norm(s: str) -> str:
    """Lowercase and turn any punctuation (hyphens, apostrophes, etc.) into
    spaces so 'already-claimed' and 'already claimed' match alike."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()


def _score(text_norm: str, triggers: list[str]) -> int:
    """How strongly a (normalized) message matches an intent's trigger phrases."""
    score = 0
    for t in triggers:
        t = _norm(t)
        if not t:
            continue
        if t in text_norm:
            # multi-word phrase match counts more than a single keyword
            score += 2 if " " in t else 1
    return score


def _detect_other_state(text_lc: str) -> str | None:
    """Return a full state name (not CA) mentioned in the message, if any."""
    for name, code in _STATE_NAMES_BY_LEN:
        if code == "CA":
            continue
        if re.search(rf"\b{re.escape(name)}\b", text_lc):
            return STATES[code]["name"]
    return None


# Phrases that mean "run an unclaimed-property search for me".
_SEARCH_TRIGGERS = (
    "find my", "find unclaimed", "search for", "search my", "look up", "lookup",
    "look for", "do i have", "any money", "any unclaimed", "any funds",
    "owed to me", "money in my name", "property in my name", "run a search",
    "search california", "treasure", "is there money", "check for",
)

# Tokens stripped when isolating a person/business name from a message.
_NAME_STOP = {
    "find", "search", "lookup", "look", "up", "my", "me", "for", "the", "a", "an",
    "unclaimed", "property", "properties", "money", "funds", "fund", "in", "of",
    "ca", "california", "do", "i", "im", "have", "has", "any", "owed", "to",
    "please", "name", "names", "is", "am", "under", "named", "check", "treasure",
    "hunt", "can", "you", "help", "mine", "see", "if", "there", "whats", "what",
    "about", "and", "on", "with", "state", "records", "want", "like", "would",
    "could", "show", "tell", "give", "run", "go", "lets", "let", "us", "hi",
    "hello", "hey", "thanks", "thank", "owe", "this", "that", "it", "im",
    # question / command words that aren't names
    "how", "why", "when", "where", "who", "which", "does", "did", "your",
    "file", "claim", "get", "got", "need", "should", "will",
}
_QUESTION_LEADS = ("what", "how", "why", "when", "where", "who", "is ", "are ",
                   "does ", "do ", "can ", "should ", "will ", "which", "?")


def _looks_like_question(text: str) -> bool:
    t = text.strip().lower()
    return "?" in t or t.startswith(_QUESTION_LEADS)


def extract_name(text: str) -> tuple[list[str] | None, str | None]:
    """Pull a likely person/business name and optional city from a message.

    Returns (name_tokens, city). name_tokens is None when nothing name-like is
    found. Heuristic — adequate for the demo; production would use a form like
    Pine's, or the member's known SmartCredit identity.
    """
    city = None
    m = re.search(r"\bin\s+([A-Za-z][A-Za-z .'\-]+?)(?=\s*,?\s*(?:ca|california)\b|[?.!,]|$)",
                  text, re.I)
    if m:
        cand = m.group(1).strip(" .,")
        # A state name after "in" is a state, not a city (handled separately).
        if (cand.lower() not in ("california", "ca", "the state", "my name", "my area")
                and cand.lower() not in _STATE_NAME_TO_CODE):
            city = cand
    city_tokens = {t.lower() for t in re.findall(r"[A-Za-z']+", city)} if city else set()

    # Keep single-letter middle initials (e.g. the "B" in "David B Coulter"),
    # which help rank the closest match — but drop single-letter stopwords.
    toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", text)
    name_toks = [t for t in toks
                 if t.lower() not in _NAME_STOP and t.lower() not in city_tokens]
    name_toks = name_toks[:4]
    if len(name_toks) >= 2:
        return name_toks, city
    return None, city


def demo_reply(message: str, context: dict | None = None) -> dict:
    """Pick the best-matching KB intent and return a member-facing answer."""
    text_lc = message.lower().strip()
    if not text_lc:
        return {"text": KB["greeting"], "suggestions": KB["suggested_prompts"][:4]}
    text_norm = _norm(message)

    best, best_score = None, 0
    for intent in KB["intents"]:
        s = _score(text_norm, intent["triggers"])
        if s > best_score:
            best, best_score = intent, s

    # A specific non-CA state in the question? Nudge toward the handoff.
    other = _detect_other_state(text_lc)
    if other and best_score < 3:
        return {
            "text": (
                f"I search California's records directly. For {other}, you can file free at the "
                f"official {other} unclaimed-property portal — pick {other} on the search page for the "
                f"link and step-by-step instructions. If you connect MaxAI (the Connect MaxAI link at the "
                f"top of this chat), I can also search {other} live for you."
            ),
            "suggestions": ["How do I file in California?", "Is this really free?", "What is unclaimed property?"],
        }

    if best is None or best_score == 0:
        return {
            "text": (
                "I can help you understand your potential unclaimed-property matches and how to "
                "claim them. Try asking how to file in California, what the New / Potential / Already-claimed "
                "sections mean, whether it's really free, or what documents you'll need. You can also "
                "search your name on the main page — anything found is yours to claim free at claimit.ca.gov."
            ),
            "suggestions": KB["suggested_prompts"][:4],
        }

    return {"text": best["answer"], "suggestions": KB["suggested_prompts"][:4]}


# ---------------------------------------------------------------------------
# Pine built-in email-code auth (real REST calls)
# ---------------------------------------------------------------------------
class PineError(Exception):
    pass


def _unwrap(resp: httpx.Response) -> dict:
    resp.raise_for_status()
    body = resp.json()
    # Pine wraps as {"status":"success","data":{...}}
    if isinstance(body, dict) and "data" in body and "status" in body:
        return body["data"] or {}
    return body


def pine_request_code(email: str) -> str:
    """POST /api/v2/auth/email/request -> request_token."""
    with httpx.Client(base_url=PINE_API, timeout=20.0) as c:
        data = _unwrap(c.post("/v2/auth/email/request", json={"email": email}))
    token = data.get("request_token")
    if not token:
        raise PineError("Pine did not return a request token.")
    return token


def pine_verify_code(email: str, code: str, request_token: str) -> dict:
    """POST /api/v2/auth/email/verify -> {access_token, id(user_id), email}."""
    with httpx.Client(base_url=PINE_API, timeout=20.0) as c:
        data = _unwrap(
            c.post(
                "/v2/auth/email/verify",
                json={"email": email, "code": code, "request_token": request_token},
            )
        )
    if not data.get("access_token") or not data.get("id"):
        raise PineError("Pine verification did not return an access token.")
    return {"access_token": data["access_token"], "user_id": data["id"], "email": data.get("email", email)}


def _sdk_available() -> bool:
    try:
        import pine_assistant  # noqa: F401
        return True
    except Exception:
        return False


def _device_id() -> str:
    return os.environ.get("PINE_DEVICE_ID", "smartcredit-getmymoneyback")


def _run_async(coro, timeout: float):
    """Run an AsyncPineAI coroutine from a sync route, bounded by a timeout.
    Returns the result, or None on any error/timeout (caller falls back)."""
    try:
        return asyncio.run(asyncio.wait_for(coro, timeout=timeout))
    except Exception as e:
        log.warning("MaxAI: Pine call failed/timed out: %s", e)
        return None


def _pluck_text(obj, _depth: int = 0) -> str | None:
    """Best-effort: pull a human-readable message string out of a ChatEvent.data
    or a history envelope (shape varies), checking the usual content keys."""
    if isinstance(obj, str):
        s = obj.strip()
        return s or None
    if isinstance(obj, dict) and _depth < 4:
        for k in ("content", "text", "message", "body", "reply", "answer", "markdown"):
            if k in obj:
                t = _pluck_text(obj[k], _depth + 1)
                if t:
                    return t
    return None


def _is_message_text(t: str | None, query: str) -> bool:
    """Keep real assistant prose; drop control tokens like 'waiting_input'/'chat'
    and echoes of the user's own message."""
    if not t or t == query.strip():
        return False
    return " " in t and len(t) >= 12


def _autofill_form(fields: list, name_parts: list[str], extra: str = "") -> dict:
    """Build a form response from the search context so MaxAI can submit Pine's
    forms automatically (keeping everything in the chat). Prefilled values win;
    name fields use the searched name; optional narrowing fields (cities/zips/
    alternate names) are left blank so the search just runs statewide."""
    first = name_parts[0] if name_parts else ""
    last = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    full = " ".join(name_parts)
    fd: dict[str, str] = {}
    for f in fields or []:
        if not isinstance(f, dict):
            continue
        nm = f.get("name") or ""
        if not nm:
            continue
        pre = f.get("prefilled")
        if pre:
            fd[nm] = pre
            continue
        lab = (f.get("label") or nm).lower()
        if "first" in lab:
            fd[nm] = first
        elif "last" in lab:
            fd[nm] = last
        elif "name" in lab:
            fd[nm] = full
        else:
            fd[nm] = extra if extra else ""  # cities/zips/alt names -> blank (statewide)
    return fd


# Event types we can act on without bothering the member.
_TEXT_EVENTS = ("session:text", "session:rich_content")
_FORM_EVENTS = ("session:form_to_user", "session:ask_for_location", "session:location_selection")
# Interactive steps that genuinely need the human (OTP, human verification, calls).
_NEEDS_USER_EVENTS = ("session:interactive_auth_confirmation", "session:three_way_call",
                      "session:computer_use_intervention")


async def _async_pine_turn(sid: str | None, msg: str, name_parts: list[str],
                           token: str, user_id: str, deadline_s: float = 42.0) -> dict | None:
    """One inline turn against the live backend, keeping the whole conversation
    in this chat. Streams events; AUTO-SUBMITS Pine's forms (it asked us to
    confirm details / add optional cities) using the searched name, then keeps
    listening for the result — so the chat never gets stuck waiting on a form.
    Steps that truly need the human (OTP, "verify you're human") are surfaced
    inline as `pending`. Bounded by deadline so a long browser run can't hang."""
    from pine_assistant import AsyncPineAI  # type: ignore
    client = AsyncPineAI(access_token=token, user_id=user_id,
                         base_url=PINE_BASE_URL, device_id=_device_id())
    await client.connect()
    parts: list[str] = []
    pending: str | None = None
    loop = asyncio.get_event_loop()
    deadline = loop.time() + deadline_s
    try:
        if not sid:
            session = await client.sessions.create()
            sid = session.get("id") if isinstance(session, dict) else getattr(session, "id", None)
        if not sid:
            return None
        await client.join_session(sid)

        async def _drain(gen) -> str:
            """Drain one event stream. Returns 'auto' (we answered a form — listen
            again), 'pending' (need the member), or 'end'."""
            nonlocal pending
            async for ev in gen:
                etype = str(getattr(ev, "type", ""))
                data = getattr(ev, "data", None)
                mid = getattr(ev, "message_id", None)
                if etype in _TEXT_EVENTS:
                    t = _pluck_text(data)
                    if _is_message_text(t, msg):
                        parts.append(t)
                elif etype in _FORM_EVENTS:
                    if isinstance(data, dict):
                        m2u = data.get("message_to_user")
                        if isinstance(m2u, str) and len(m2u) >= 12 and m2u not in parts:
                            # keep Pine's note brief; we still auto-handle the form
                            parts.append(m2u)
                        fields = ((data.get("form") or {}).get("fields")) if isinstance(data.get("form"), dict) else None
                        try:
                            client.send_form_response(sid, mid, _autofill_form(fields or [], name_parts))
                        except Exception:
                            pass
                    return "auto"
                elif etype in _NEEDS_USER_EVENTS:
                    if isinstance(data, dict):
                        pending = data.get("message_to_user") or "This step needs you to verify it directly."
                    return "pending"
            return "end"

        # First turn sends the message; subsequent rounds just listen for what
        # Pine does after our auto form-submit.
        result = await asyncio.wait_for(_drain(client.chat(sid, msg)),
                                        timeout=max(2.0, deadline - loop.time()))
        rounds = 0
        while result == "auto" and rounds < 5 and loop.time() < deadline:
            rounds += 1
            try:
                result = await asyncio.wait_for(_drain(client.listen(sid)),
                                                timeout=max(2.0, deadline - loop.time()))
            except asyncio.TimeoutError:
                break

        # De-dupe, cap length.
        seen, uniq = set(), []
        for p in parts:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        text = "\n\n".join(uniq).strip()
        if len(text) > 1200:
            text = text[:1200].rstrip() + "…"
        return {"text": text, "session_id": sid, "pending": pending}
    except asyncio.TimeoutError:
        text = "\n\n".join(dict.fromkeys(parts)).strip()
        return {"text": text, "session_id": sid, "pending": pending}
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


def _pine_turn(sid: str | None, msg: str, name_parts: list[str],
               token: str, user_id: str) -> dict | None:
    """Sync wrapper: one inline turn against the live backend. None on failure."""
    if not _sdk_available():
        return None
    return _run_async(_async_pine_turn(sid, msg, name_parts, token, user_id), timeout=55)


# ---------------------------------------------------------------------------
# Assistant service (prototype: single in-memory connection)
# ---------------------------------------------------------------------------
class AssistantService:
    """Holds the (optional) connected Pine account for the prototype.

    Single-user in-memory state is fine for the local demo. Production would key
    this by SmartCredit member and persist tokens in the member vault.
    """

    def __init__(self) -> None:
        saved = load_tokens() or {}
        self._token = ENV_TOKEN or saved.get("access_token")
        self._user_id = ENV_USER_ID or saved.get("user_id")
        self._email: str | None = saved.get("email")
        self._code = load_confirmation_code()  # saved; no in-app connect flow
        self._pending: dict[str, str] = {}  # email -> request_token
        self._pending_search = False         # asked for a name, awaiting it
        self._pending_state: str | None = None  # target state code for that name (None=CA)
        self._pine_session_id: str | None = None  # active live-search thread, for inline follow-ups
        self._matcher: DemoFuzzyMatcher | None = None
        self._expiry_prompted = False

    def _refresh_creds(self) -> None:
        """Pick up a login completed via scripts/pine_login.py without a restart."""
        if self._token and self._user_id:
            return
        saved = load_tokens()
        if saved:
            self._token = saved["access_token"]
            self._user_id = saved["user_id"]
            self._email = saved.get("email")
            self._expiry_prompted = False

    @property
    def connected(self) -> bool:
        return bool(self._token and self._user_id)

    def status(self) -> dict:
        self._refresh_creds()
        return {
            "mode": "live" if self.connected else "demo",
            "email": self._email,
            "sdk": _sdk_available(),
            "has_code": bool(self._code),
        }

    def greeting(self) -> dict:
        return {"text": KB["greeting"], "suggestions": KB["suggested_prompts"]}

    # -- unclaimed-property search ----------------------------------------
    def _get_matcher(self) -> DemoFuzzyMatcher:
        if self._matcher is None:
            self._matcher = DemoFuzzyMatcher(get_connection(read_only=True))
        return self._matcher

    def _serialize(self, matches: list, limit: int = 6) -> list[dict]:
        out = []
        for m in matches[:limit]:
            out.append({
                "owner": presentation.pretty_name(m.owner_name),
                "holder": presentation.pretty_holder(m.holder_name),
                "amount": m.amount_display,
                "property_type": m.property_type_display,
                "address": m.address_display,
                "status": m.status,
                "status_label": m.status_label,
                "status_badge_class": m.status_badge_class,
                "status_dot": m.status_dot,
                "claimable": m.claimable,
                "claim_url": m.claim_url,
            })
        return out

    def _do_search(self, name_toks: list[str], city: str | None,
                   target_state: str | None = None, target_name: str | None = None) -> dict:
        # A specific non-CA state -> only a connected Pine account can search it
        # (we hold local data for CA only).
        if target_state and target_state != "CA":
            return self._search_other_state(name_toks, city, target_state, target_name)

        first = name_toks[0]
        last = " ".join(name_toks[1:]) if len(name_toks) > 1 else ""
        name_disp = " ".join(t.capitalize() for t in name_toks)
        matcher = self._get_matcher()
        matches = matcher.find_matches(first_name=first, last_name=last,
                                       city=city or None, state="CA")
        fell_back = False
        if city and not matches:
            matches = matcher.find_matches(first_name=first, last_name=last, state="CA")
            fell_back = True

        claimable = [m for m in matches if m.claimable]
        total = sum((m.amount_max or 0) for m in claimable)
        counts = {
            "new": sum(1 for m in matches if m.status == "new"),
            "active": sum(1 for m in matches if m.status == "active"),
            "claimed": sum(1 for m in matches if m.status == "claimed"),
        }

        if not claimable:
            # No claimable matches. Note if some were previously claimed.
            claimed_only = len(matches) > 0
            extra = (f" I did find {len(matches)} record(s) previously reported in your name, "
                     "but they've already been claimed.") if claimed_only else ""
            result = {
                "text": (
                    f"I searched California's records for **{name_disp}**"
                    f"{f' in {city}' if city else ''} and didn't find a claimable match yet.{extra} "
                    "Try a name variant or fewer details — coverage grows weekly, and I can "
                    "alert you the moment something appears in your name."
                ),
                "suggestions": ["Search a different name", "What is unclaimed property?",
                                "Why might a match not be mine?", "Is this really free?"],
                "mode": "live" if self.connected else "demo",
            }
        else:
            lead = ""
            if fell_back:
                lead = f"I didn't find a match in {city}, so I searched all of California. "
            money = f" worth about **${total:,.2f}** in claimable funds" if total else ""
            n = len(claimable)
            plural = "es" if n != 1 else ""
            text = (
                f"{lead}I searched California's records for **{name_disp}** and found "
                f"**{n}** potential match{plural}{money}. Here are the top ones — "
                "tap **Claim** to file free at claimit.ca.gov. These are *potential* matches; "
                "the state confirms ownership when you file, and SmartCredit never charges a fee."
            )
            result = {
                "text": text,
                "search": {
                    "query": name_disp,
                    "city": None if fell_back else city,
                    "total_claimable": float(total),
                    "counts": counts,
                    "shown": min(n, 6),
                    "total": n,
                    "matches": self._serialize(claimable),
                },
                "suggestions": ["How do I file my claim in California?", "What documents will I need?",
                                "Why might a match not be mine?", "Search a different name"],
                "mode": "live" if self.connected else "demo",
            }

        # California is searched against our own instant local data — Pine is
        # reserved for states we don't index (see _search_other_state).
        return result

    def _search_other_state(self, name_toks: list[str], city: str | None,
                            code: str, state_name: str | None) -> dict:
        """Search a non-CA state. Possible only when connected. The whole
        conversation stays inline in this chat (no external link)."""
        name_disp = " ".join(t.capitalize() for t in name_toks)
        info = STATES.get(code, {})
        state_name = state_name or info.get("name") or code
        portal = info.get("portal_url") or "the official state portal"
        if not self.connected:
            return self._other_state_handoff(code, state_name)

        q = (
            f"Search {state_name} unclaimed property on the official portal {portal} "
            f"for the name '{name_disp}'" + (f" in {city}" if city else "") +
            ". List any potential matches with the holder/company, amount, property type, "
            "and reported address. Do not start or file any claim."
        )
        turn = _pine_turn(None, q, name_toks, self._token, self._user_id)
        if turn and turn.get("session_id"):
            self._pine_session_id = turn["session_id"]
            reply = (turn.get("text") or "").strip()
            pend = (turn.get("pending") or "").strip()
            if pend:
                return {"text": (f"{reply}\n\n" if reply else "") +
                        f"⚠️ {pend}\n\nReply here once that's done and I'll keep going.",
                        "mode": "live",
                        "suggestions": ["What did you find?", "How do I file?", "Search a different state"]}
            if reply:
                return {"text": reply, "mode": "live",
                        "suggestions": ["What did you find?", "Search a different state", "Is this really free?"]}
            # Connected and a session opened, but no reply streamed in time.
            return {
                "text": (f"I'm searching {state_name}'s official records for **{name_disp}** now — "
                         f"I've confirmed your details for you. This can take a moment; ask me "
                         f"\"what did you find?\" in a few seconds and I'll share the results here."),
                "mode": "live",
                "suggestions": ["What did you find?", "How do I file?", "Is this really free?"],
            }
        # Couldn't reach the live search — fall back to the portal handoff.
        if not self._expiry_prompted:
            self._expiry_prompted = True
            prompt_for_code_if_expired("live state search unavailable")
        return self._other_state_handoff(
            code, state_name, note="I couldn't reach the live search just now. ")

    def _pine_followup(self, message: str) -> dict:
        """Relay a follow-up answer into the active live-search thread, inline."""
        turn = _pine_turn(self._pine_session_id, message, [], self._token, self._user_id)
        reply = (turn or {}).get("text", "").strip() if turn else ""
        pend = (turn or {}).get("pending") if turn else None
        if pend:
            return {"text": (f"{reply}\n\n" if reply else "") +
                    f"⚠️ {pend}\n\nReply here once that's done and I'll keep going.",
                    "mode": "live",
                    "suggestions": ["What did you find?", "How do I file?", "Search a different state"]}
        if reply:
            return {"text": reply, "mode": "live",
                    "suggestions": ["What did you find?", "Search a different state", "Is this really free?"]}
        return {
            "text": "I'm still working on that search — give me a moment, then ask \"what did you find?\".",
            "mode": "live",
            "suggestions": ["What did you find?", "Search California instead", "How do I file?"],
        }

    def _other_state_handoff(self, code: str, state_name: str, note: str = "") -> dict:
        info = STATES.get(code, {})
        portal = info.get("portal_url") or "https://unclaimed.org/search/"
        steps = info.get("steps") or []
        text = (f"{note}I search California directly, so I can't scan {state_name} from our own records "
                f"— but you can search it free at the official {state_name} portal: {portal}")
        if steps:
            text += f"\n\nHow to file in {state_name}:\n" + "\n".join(
                f"{i + 1}. {s}" for i, s in enumerate(steps[:5]))
        if not self.connected:
            text += (f"\n\nTip: connect MaxAI (the **Connect MaxAI** link at the top of this chat) and I "
                     f"can search {state_name} live for you.")
        return {
            "text": text,
            "suggestions": ["Search California instead", "How do I file?", "Is this really free?"],
            "mode": "live" if self.connected else "demo",
        }

    def _ask_for_name(self, target_state: str | None = None, target_name: str | None = None) -> dict:
        self._pending_search = True
        self._pending_state = target_state
        where = target_name or "California"
        return {
            "text": (
                f"I can search {where}'s unclaimed-property records for you. "
                "What's the **full name** to search? A **city** helps me narrow it "
                "(e.g. \"Ahmed Yassine in Irvine\"). I'll only show *potential* matches — "
                "you confirm and claim them free with the state."
            ),
            "suggestions": ["Ahmed Yassine in Irvine", "What is unclaimed property?", "Is this really free?"],
            "mode": "live" if self.connected else "demo",
        }

    # -- main routing ------------------------------------------------------
    def reply(self, message: str, context: dict | None = None) -> dict:
        # Pick up a login completed out-of-band (scripts/pine_login.py).
        self._refresh_creds()
        text_lc = message.lower()
        text_norm = _norm(message)
        name_toks, city = extract_name(message)
        has_trigger = any(t in text_norm for t in _SEARCH_TRIGGERS)
        other_state = _detect_other_state(text_lc)  # a non-CA state mentioned, if any
        wants_search = has_trigger or (
            other_state and re.search(r"unclaimed|propert|money|fund|owed|search|find|claim|treasure", text_norm))

        # 1) We just asked for a name and got one -> search (in the target state).
        #    Skip if the follow-up is itself a question (topic change), so we
        #    don't treat question words as a name.
        if self._pending_search and name_toks and not _looks_like_question(message) and not has_trigger:
            st = self._pending_state
            self._pending_search = False
            self._pending_state = None
            return self._do_search(name_toks, city, target_state=st,
                                   target_name=(STATES.get(st, {}).get("name") if st else None))

        # 2) Search for a specific non-CA state. A connected Pine account can do
        #    it (Pine drives any state's portal); otherwise hand off to that
        #    state's official portal.
        if other_state and wants_search:
            code = _STATE_NAME_TO_CODE.get(other_state.lower())
            self._pending_search = False
            if self.connected:
                if name_toks:
                    return self._do_search(name_toks, city, target_state=code, target_name=other_state)
                return self._ask_for_name(target_state=code, target_name=other_state)
            return self._other_state_handoff(code, other_state)

        # 3) Explicit California search request (leaves any live-search thread).
        if has_trigger:
            self._pending_search = False
            self._pine_session_id = None
            if name_toks:
                return self._do_search(name_toks, city)
            return self._ask_for_name()

        # 4) Bare name with no question -> treat as a California search.
        if name_toks and not _looks_like_question(message):
            self._pine_session_id = None
            return self._do_search(name_toks, city)

        # 5) Confident knowledge-base question -> answer instantly from the KB,
        #    even mid-thread (so "how do I file?" always works).
        best, best_score = None, 0
        for intent in KB["intents"]:
            s = _score(text_norm, intent["triggers"])
            if s > best_score:
                best, best_score = intent, s
        if best_score >= 2:
            self._pending_search = False
            return {"text": best["answer"], "suggestions": KB["suggested_prompts"][:4],
                    "mode": "live" if self.connected else "demo"}

        # 6) Inside an active live-search thread -> relay this answer inline.
        if self.connected and self._pine_session_id:
            self._pending_search = False
            return self._pine_followup(message)

        # 7) General Q&A from the knowledge base (instant — no live round-trip).
        self._pending_search = False
        out = demo_reply(message, context)
        out["mode"] = "live" if self.connected else "demo"
        return out

    def connect_request(self, email: str) -> dict:
        email = (email or "").strip()
        if "@" not in email:
            raise PineError("Please enter a valid email address.")
        token = pine_request_code(email)
        self._pending[email] = token
        return {"ok": True, "email": email}

    def connect_verify(self, email: str, code: str) -> dict:
        email = (email or "").strip()
        request_token = self._pending.get(email)
        if not request_token:
            raise PineError("No pending verification — request a code first.")
        creds = pine_verify_code(email, code.strip(), request_token)
        self._token = creds["access_token"]
        self._user_id = creds["user_id"]
        self._email = creds["email"]
        self._expiry_prompted = False
        self._pending.pop(email, None)
        save_tokens(self._token, self._user_id, self._email)  # survive restarts
        return {"ok": True, "mode": "live", "email": self._email}

    def disconnect(self) -> dict:
        # Forget the saved session too, or _refresh_creds()/load_tokens() would
        # silently re-connect on the next status() poll. Env creds (operator
        # "pre-issued" path) deliberately survive a disconnect.
        for f in (_TOKEN_FILE, _PENDING_FILE):
            try:
                f.unlink()
            except Exception:
                pass
        self._token, self._user_id, self._email = ENV_TOKEN, ENV_USER_ID, None
        self._pine_session_id = None
        return {"ok": True, "mode": "live" if self.connected else "demo"}


# Module-level singleton used by the routes.
assistant = AssistantService()
