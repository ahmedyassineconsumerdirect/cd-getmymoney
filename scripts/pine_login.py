"""Connect MaxAI to a real Pine account (two non-interactive steps).

Pine uses an email-code login: you request a code (Pine emails it to you), then
verify it. This persists the resulting access token to
data/internal/maxai_pine_token.json, which MaxAI picks up automatically — after
that, a search in the chat also runs a live Pine search on the official portal.

Usage:
    .venv/bin/python scripts/pine_login.py request you@email.com
    # ...check your inbox for the code Pine emails you...
    .venv/bin/python scripts/pine_login.py verify 123456

    .venv/bin/python scripts/pine_login.py status     # show current connection
    .venv/bin/python scripts/pine_login.py logout      # forget the saved token
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import pine


def _request(email: str) -> int:
    token = pine.pine_request_code(email)
    pine.save_pending(email, token)
    print(f"✓ Code requested. Pine emailed a login code to {email}.")
    print("  Next:  .venv/bin/python scripts/pine_login.py verify <code-from-email>")
    return 0


def _verify(code: str) -> int:
    pending = pine.load_pending()
    if not pending:
        print("No pending login. Run:  pine_login.py request <email>", file=sys.stderr)
        return 1
    creds = pine.pine_verify_code(pending["email"], code, pending["request_token"])
    pine.save_tokens(creds["access_token"], creds["user_id"], creds["email"])
    try:
        pine._PENDING_FILE.unlink()
    except Exception:
        pass
    print(f"✓ Connected as {creds['email']}. MaxAI will now run live Pine searches.")
    print("  (No restart needed — the running app picks up the token on the next message.)")
    return 0


def _status() -> int:
    saved = pine.load_tokens()
    if saved:
        print(f"Connected: {saved.get('email') or '(token present)'}")
    else:
        print("Not connected. Run:  pine_login.py request <email>")
    return 0


def _logout() -> int:
    for f in (pine._TOKEN_FILE, pine._PENDING_FILE):
        try:
            f.unlink()
        except Exception:
            pass
    print("✓ Forgot the saved Pine token. MaxAI is back to local search only.")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    try:
        if cmd == "request" and len(argv) >= 2:
            return _request(argv[1].strip())
        if cmd == "verify" and len(argv) >= 2:
            return _verify(argv[1].strip())
        if cmd == "status":
            return _status()
        if cmd == "logout":
            return _logout()
    except pine.PineError as e:
        print(f"Pine error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        return 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
