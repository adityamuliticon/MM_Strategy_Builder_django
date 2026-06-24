"""
Full Chatbot Flow Test — sends real prompts to all 5 strategy chatbots.
No direct API calls; every action goes through the SSE stream endpoint.

Feature coverage per module:
  USB  — create, save, deploy, modify, rename, Q&A
  ISE  — create, save,          modify, rename, backtest, Q&A
  ISB  — create, save,          modify, rename,            Q&A
  RES  — create, save, deploy, modify, rename, Q&A
  MLH  — create, save, deploy, modify, rename, backtest, Q&A
  ALL  — delete 2 strategies (via USB) at the very end

Run:
    python tests/test_full_chatbot_flow.py
    python tests/test_full_chatbot_flow.py --url http://127.0.0.1:8000
"""

import json
import re
import sys
import time
import argparse
import requests
from datetime import datetime, timedelta

# ─── Config ───────────────────────────────────────────────────────────────────
DEFAULT_BASE = "http://127.0.0.1:8000"
EMAIL        = "technical28.multiicon@gmail.com"
PASSWORD     = "Aa12345@"

_today    = datetime.today()
BT_END    = _today.strftime("%Y-%m-%d")
BT_START  = (_today - timedelta(days=30)).strftime("%Y-%m-%d")

# 5-digit tag so names don't collide across runs
RUN_TAG = str(int(time.time()))[-5:]

MODULE_URLS = {
    "USB": "/api/chat/stream",
    "ISE": "/indicator/api/chat/stream",
    "ISB": "/bridge/api/chat/stream",
    "RES": "/scalper/api/chat/stream",
    "MLH": "/hedger/api/chat/stream",
}

# Base names — AI appends its own 4-digit suffix, so we track the real name
# after parsing the preview.
BASE_NAMES = {
    "USB": f"FlowUSB{RUN_TAG}",
    "ISE": f"FlowISE{RUN_TAG}",
    "ISB": f"FlowISB{RUN_TAG}",
    "RES": f"FlowRES{RUN_TAG}",
    "MLH": f"FlowMLH{RUN_TAG}",
}

# Holds the actual names after the AI adds its suffix
ACTUAL_NAMES: dict[str, str] = {}

# ─── Creation prompts — module-specific strategy types ────────────────────────
CREATE_PROMPTS = {
    # USB: multi-leg options strategy (standard legs format)
    "USB": (
        "Please create a brand new NIFTY options strategy named {name}: "
        "1 leg, BUY CE, ATM strike, Current Week expiry, 1 lot, "
        "target ₹500 by Money, stop loss ₹300 by Money."
    ),
    # ISE: indicator-driven entry/exit signal
    "ISE": (
        "Please create a brand new indicator strategy named {name} for NIFTY NSE: "
        "buy entry signal when 14-period RSI crosses above 35, "
        "sell/exit signal when RSI crosses below 65, daily timeframe."
    ),
    # ISB: external-signal bridge (no internal signals)
    "ISB": (
        "Please create a brand new Inbound Signal Bridge strategy named {name}: "
        "symbol NIFTY NSE Options, "
        "when external webhook signal arrives execute BUY 1 lot CE ATM Current Week expiry."
    ),
    # RES: averaging/jobbing strategy (not a regular options strategy)
    "RES": (
        "Please create a brand new NIFTY NFO FUT jobbing strategy named {name}: "
        "intraday, 1 lot, BUY jobbing side, "
        "average down every 50 points, target 30 points per step, max 3 averaging steps, "
        "entry time 09:20, exit time 15:00."
    ),
    # MLH: iron condor (4-leg hedge)
    "MLH": (
        "Please create a brand new Iron Condor hedge strategy named {name} on NIFTY NSE: "
        "Leg1 SELL CE ATM+100, Leg2 BUY CE ATM+200, "
        "Leg3 SELL PE ATM-100, Leg4 BUY PE ATM-200, "
        "all Current Week expiry, 1 lot each."
    ),
}

# ─── ANSI colours ─────────────────────────────────────────────────────────────
GRN  = "\033[92m"; RED  = "\033[91m"; YEL  = "\033[93m"
CYN  = "\033[96m"; BLD  = "\033[1m";  RST  = "\033[0m"

REFUSED = "I'm built exclusively"   # refusal signature

# ─── SSE stream helper ────────────────────────────────────────────────────────
def stream_chat(session: requests.Session, url: str, message: str, timeout=90):
    """
    POST message → parse SSE events.
    Returns (text: str, statuses: list[str], error: str|None).
    """
    try:
        r = session.post(url, json={"message": message}, stream=True, timeout=timeout)
        if r.status_code != 200:
            return "", [], f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return "", [], f"Connect error: {e}"

    text = ""
    statuses: list[str] = []
    buf = ""
    try:
        for raw in r.iter_content(chunk_size=None):
            if not raw:
                continue
            buf += raw.decode("utf-8", errors="replace")
            parts = buf.split("\n\n")
            buf = parts.pop()
            for part in parts:
                part = part.strip()
                if not part.startswith("data: "):
                    continue
                try:
                    evt = json.loads(part[6:])
                except json.JSONDecodeError:
                    continue
                t = evt.get("t")
                if t == "chunk":
                    text += evt.get("v", "")
                elif t == "status":
                    statuses.append(evt.get("v", ""))
                elif t == "done":
                    return text, statuses, None
                elif t == "error":
                    return text, statuses, evt.get("v", "AI error")
    except Exception as e:
        return text, statuses, f"Stream error: {e}"
    return text, statuses, None


# ─── Result tracker ───────────────────────────────────────────────────────────
class Results:
    def __init__(self):
        self.rows: list[tuple] = []

    def record(self, mod, step, passed, note=""):
        self.rows.append((mod, step, passed, note))
        sym = f"{GRN}✓ PASS{RST}" if passed else f"{RED}✗ FAIL{RST}"
        print(f"  [{BLD}{mod}{RST}] {sym}  {step}" + (f"  — {note}" if note else ""))

    def summary(self):
        total  = len(self.rows)
        passed = sum(1 for r in self.rows if r[2])
        failed = total - passed
        print()
        print("═" * 65)
        print(f"  {BLD}SUMMARY{RST}   {GRN}{passed} passed{RST}  /  {RED}{failed} failed{RST}  /  {total} total")
        print("═" * 65)
        if failed:
            print(f"\n  {RED}Failed steps:{RST}")
            for m, s, ok, n in self.rows:
                if not ok:
                    print(f"    [{m}] {s}  {n}")
        return failed == 0


R = Results()


# ─── Step runner ─────────────────────────────────────────────────────────────
def step(session, url, mod, name, msg, *,
         must_contain=None,
         must_not_be_empty=True,
         must_not_refuse=True,
         timeout=90,
         preview_lines=3):
    """Send msg, check response, record pass/fail. Returns (text, statuses)."""
    t0 = time.time()
    text, statuses, err = stream_chat(session, url, msg, timeout=timeout)
    elapsed = time.time() - t0

    # Connection / server error
    if err and not text.strip():
        R.record(mod, name, False, err[:120])
        return "", []

    # Empty response
    if must_not_be_empty and not text.strip():
        tools = ", ".join(statuses) if statuses else "—"
        R.record(mod, name, False, f"Empty response  tools=[{tools}]")
        return text, statuses

    # Scope refusal treated as failure
    if must_not_refuse and REFUSED in text:
        R.record(mod, name, False, f"AI refused (out-of-scope response)")
        return text, statuses

    # Required keywords
    if must_contain:
        kws = [must_contain] if isinstance(must_contain, str) else must_contain
        for kw in kws:
            if kw.lower() not in text.lower():
                preview = text[:120].replace("\n", " ")
                R.record(mod, name, False, f"Missing '{kw}' — got: {preview!r}")
                return text, statuses

    note = f"{elapsed:.1f}s"
    if statuses:
        note += f"  [{', '.join(statuses)}]"
    R.record(mod, name, True, note)

    lines = [l for l in text.splitlines() if l.strip()][:preview_lines]
    for l in lines:
        print(f"         {CYN}│{RST} {l[:95]}")

    return text, statuses


# ─── Strategy name extractor ──────────────────────────────────────────────────
def extract_name(text: str, base: str) -> str:
    """
    The AI appends a random 4-digit suffix, e.g. FlowUSB17696_3948.
    Find the longest match starting with the base prefix in the preview text.
    """
    prefix = base[:8]                         # "FlowUSB1"
    pattern = rf'\b({re.escape(prefix)}\w*)\b'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        # Return the longest match (most complete name)
        return max(matches, key=len)
    return base


# ─── Login ────────────────────────────────────────────────────────────────────
def login(base_url: str) -> requests.Session:
    s = requests.Session()
    try:
        r = s.post(f"{base_url}/auth/login/",
                   json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    except Exception as e:
        print(f"{RED}✗{RST} Login request failed: {e}"); sys.exit(1)

    if r.status_code != 200 or r.json().get("status") != "ok":
        print(f"{RED}✗{RST} Login failed: {r.text[:200]}"); sys.exit(1)

    print(f"{GRN}✓{RST} Logged in as {r.json().get('display_name', EMAIL)}")
    return s


# ─── Per-module flows ─────────────────────────────────────────────────────────

def test_usb(session, base_url):
    mod = "USB"; url = base_url + MODULE_URLS[mod]
    base = BASE_NAMES[mod]
    print(f"\n{'─'*65}\n  {BLD}{mod}{RST}   base name: {base}\n{'─'*65}")

    # 1. CREATE — expect markdown preview tables
    t, _ = step(session, url, mod, "1. Create (preview)",
                CREATE_PROMPTS[mod].format(name=base),
                must_contain="---", timeout=90)
    name = extract_name(t, base)
    ACTUAL_NAMES[mod] = name
    print(f"         {YEL}→ actual name: {name}{RST}")
    if not t.strip(): return

    # 2. SAVE
    step(session, url, mod, "2. Save",
         "yes save it",
         must_contain="Strategy Saved Successfully", timeout=60)

    # 3. DEPLOY — turn 1: get settings table
    d, _ = step(session, url, mod, "3. Deploy (get settings)",
                f"deploy strategy {name}",
                must_contain=["Balance", "pts"], timeout=60)
    # turn 2: confirm
    if d.strip() and REFUSED not in d:
        step(session, url, mod, "3. Deploy (confirm proceed)",
             "proceed",
             must_contain=["deployed", "Deploy", "successfully"], timeout=60)

    # 4. MODIFY
    step(session, url, mod, "4. Modify",
         f"modify strategy {name}, change lot size to 2",
         must_not_be_empty=True, timeout=60)

    # 5. RENAME — turn 1: request, turn 2: confirm
    r1, _ = step(session, url, mod, "5. Rename (request)",
                 f"rename {name} to {name}_R",
                 must_not_be_empty=True, timeout=60)
    if r1.strip() and REFUSED not in r1:
        step(session, url, mod, "5. Rename (confirm yes)",
             "yes do the rename",
             must_not_be_empty=True, timeout=60)
        ACTUAL_NAMES[mod] = f"{name}_R"

    # 6. Q&A
    step(session, url, mod, "6. Q&A",
         "what are the entry and exit conditions for this strategy?",
         must_not_be_empty=True, timeout=60)


def test_ise(session, base_url):
    mod = "ISE"; url = base_url + MODULE_URLS[mod]
    base = BASE_NAMES[mod]
    print(f"\n{'─'*65}\n  {BLD}{mod}{RST}   base name: {base}\n{'─'*65}")

    # 1. CREATE
    t, _ = step(session, url, mod, "1. Create (preview)",
                CREATE_PROMPTS[mod].format(name=base),
                must_contain="---", timeout=90)
    name = extract_name(t, base)
    ACTUAL_NAMES[mod] = name
    print(f"         {YEL}→ actual name: {name}{RST}")
    if not t.strip(): return

    # 2. SAVE
    step(session, url, mod, "2. Save",
         "yes save it",
         must_contain="Strategy Saved Successfully", timeout=60)

    # 3. MODIFY (ISE has no deploy tool)
    step(session, url, mod, "3. Modify",
         f"modify strategy {name}, change RSI period to 21",
         must_not_be_empty=True, timeout=60)

    # 4. RENAME
    r1, _ = step(session, url, mod, "4. Rename (request)",
                 f"rename {name} to {name}_R",
                 must_not_be_empty=True, timeout=60)
    if r1.strip() and REFUSED not in r1:
        step(session, url, mod, "4. Rename (confirm yes)",
             "yes do the rename",
             must_not_be_empty=True, timeout=60)
        ACTUAL_NAMES[mod] = f"{name}_R"

    # 5. BACKTEST — use original saved name (before rename)
    b1, _ = step(session, url, mod, "5. Backtest (trigger)",
                 f"run backtest for {name} from {BT_START} to {BT_END}",
                 must_not_be_empty=True, timeout=90)
    if b1.strip() and REFUSED not in b1:
        print(f"         {YEL}Waiting 35s for backtest engine...{RST}")
        time.sleep(35)
        step(session, url, mod, "5. Backtest (get result)",
             f"show me the backtest result for {name}",
             must_not_be_empty=True, timeout=60)

    # 6. Q&A
    step(session, url, mod, "6. Q&A",
         "which indicator does this strategy use and what are its parameters?",
         must_not_be_empty=True, timeout=60)


def test_isb(session, base_url):
    mod = "ISB"; url = base_url + MODULE_URLS[mod]
    base = BASE_NAMES[mod]
    print(f"\n{'─'*65}\n  {BLD}{mod}{RST}   base name: {base}\n{'─'*65}")

    # 1. CREATE
    t, _ = step(session, url, mod, "1. Create (preview)",
                CREATE_PROMPTS[mod].format(name=base),
                must_contain="---", timeout=90)
    name = extract_name(t, base)
    ACTUAL_NAMES[mod] = name
    print(f"         {YEL}→ actual name: {name}{RST}")
    if not t.strip(): return

    # 2. SAVE
    step(session, url, mod, "2. Save",
         "yes save it",
         must_contain="Strategy Saved Successfully", timeout=60)

    # 3. MODIFY (ISB has no deploy tool)
    step(session, url, mod, "3. Modify",
         f"modify strategy {name}, change to 2 lots",
         must_not_be_empty=True, timeout=60)

    # 4. RENAME
    r1, _ = step(session, url, mod, "4. Rename (request)",
                 f"rename {name} to {name}_R",
                 must_not_be_empty=True, timeout=60)
    if r1.strip() and REFUSED not in r1:
        step(session, url, mod, "4. Rename (confirm yes)",
             "yes do the rename",
             must_not_be_empty=True, timeout=60)
        ACTUAL_NAMES[mod] = f"{name}_R"

    # 5. Q&A
    step(session, url, mod, "5. Q&A",
         "how does this strategy receive its trading signals?",
         must_not_be_empty=True, timeout=60)


def test_res(session, base_url):
    mod = "RES"; url = base_url + MODULE_URLS[mod]
    base = BASE_NAMES[mod]
    print(f"\n{'─'*65}\n  {BLD}{mod}{RST}   base name: {base}\n{'─'*65}")

    # 1. CREATE (averaging/jobbing — RES-specific format)
    t, _ = step(session, url, mod, "1. Create (preview)",
                CREATE_PROMPTS[mod].format(name=base),
                must_contain="---", timeout=90)
    name = extract_name(t, base)
    ACTUAL_NAMES[mod] = name
    print(f"         {YEL}→ actual name: {name}{RST}")
    if not t.strip(): return

    # 2. SAVE
    step(session, url, mod, "2. Save",
         "yes save it",
         must_contain="Strategy Saved Successfully", timeout=60)

    # 3. DEPLOY
    d, _ = step(session, url, mod, "3. Deploy (get settings)",
                f"deploy strategy {name}",
                must_contain=["Balance", "pts"], timeout=60)
    if d.strip() and REFUSED not in d:
        step(session, url, mod, "3. Deploy (confirm proceed)",
             "proceed",
             must_contain=["deployed", "Deploy", "successfully"], timeout=60)

    # 4. MODIFY
    step(session, url, mod, "4. Modify",
         f"modify strategy {name}, change to 2 lots",
         must_not_be_empty=True, timeout=60)

    # 5. RENAME
    r1, _ = step(session, url, mod, "5. Rename (request)",
                 f"rename {name} to {name}_R",
                 must_not_be_empty=True, timeout=60)
    if r1.strip() and REFUSED not in r1:
        step(session, url, mod, "5. Rename (confirm yes)",
             "yes do the rename",
             must_not_be_empty=True, timeout=60)
        ACTUAL_NAMES[mod] = f"{name}_R"

    # 6. Q&A
    step(session, url, mod, "6. Q&A",
         "what is the averaging step size and target for this strategy?",
         must_not_be_empty=True, timeout=60)


def test_mlh(session, base_url):
    mod = "MLH"; url = base_url + MODULE_URLS[mod]
    base = BASE_NAMES[mod]
    print(f"\n{'─'*65}\n  {BLD}{mod}{RST}   base name: {base}\n{'─'*65}")

    # 1. CREATE
    t, _ = step(session, url, mod, "1. Create (preview)",
                CREATE_PROMPTS[mod].format(name=base),
                must_contain="---", timeout=90)
    name = extract_name(t, base)
    ACTUAL_NAMES[mod] = name
    print(f"         {YEL}→ actual name: {name}{RST}")
    if not t.strip(): return

    # 2. SAVE
    step(session, url, mod, "2. Save",
         "yes save it",
         must_contain="Strategy Saved Successfully", timeout=60)

    # 3. DEPLOY
    d, _ = step(session, url, mod, "3. Deploy (get settings)",
                f"deploy strategy {name}",
                must_contain=["Balance", "pts"], timeout=60)
    if d.strip() and REFUSED not in d:
        step(session, url, mod, "3. Deploy (confirm proceed)",
             "proceed",
             must_contain=["deployed", "Deploy", "successfully"], timeout=60)

    # 4. MODIFY
    step(session, url, mod, "4. Modify",
         f"modify strategy {name}, change all legs to 2 lots",
         must_not_be_empty=True, timeout=60)

    # 5. RENAME
    r1, _ = step(session, url, mod, "5. Rename (request)",
                 f"rename {name} to {name}_R",
                 must_not_be_empty=True, timeout=60)
    if r1.strip() and REFUSED not in r1:
        step(session, url, mod, "5. Rename (confirm yes)",
             "yes do the rename",
             must_not_be_empty=True, timeout=60)
        ACTUAL_NAMES[mod] = f"{name}_R"

    # 6. BACKTEST (use original name, before rename)
    b1, _ = step(session, url, mod, "6. Backtest (trigger)",
                 f"run backtest for {name} from {BT_START} to {BT_END}",
                 must_not_be_empty=True, timeout=90)
    if b1.strip() and REFUSED not in b1:
        print(f"         {YEL}Waiting 35s for backtest engine...{RST}")
        time.sleep(35)
        step(session, url, mod, "6. Backtest (get result)",
             f"show me the backtest result for {name}",
             must_not_be_empty=True, timeout=60)

    # 7. Q&A
    step(session, url, mod, "7. Q&A",
         "how many legs does this strategy have and what are their positions?",
         must_not_be_empty=True, timeout=60)


# ─── End-of-run: delete 2 strategies via USB chatbot ─────────────────────────

def test_delete_two(session, base_url):
    url = base_url + MODULE_URLS["USB"]
    print(f"\n{'─'*65}\n  {BLD}DELETE{RST}   (delete 2 strategies via USB chatbot)\n{'─'*65}")

    # List all strategies
    lst, _ = step(session, url, "USB", "List all strategies",
                  "show me all my saved strategies",
                  must_not_be_empty=True, timeout=60, preview_lines=12)
    if not lst.strip():
        print(f"  {YEL}⚠ Cannot proceed — list failed{RST}")
        return

    # Pick the 2 flow-test strategies to delete
    # Use renamed names if rename succeeded, otherwise original
    del1 = ACTUAL_NAMES.get("USB", BASE_NAMES["USB"])
    del2 = ACTUAL_NAMES.get("MLH", BASE_NAMES["MLH"])

    for label, dname in [("A", del1), ("B", del2)]:
        # turn 1: ask to delete
        ask, _ = step(session, url, "USB", f"Delete {label} (ask): {dname}",
                      f"delete strategy {dname}",
                      must_contain=["delete", "sure", "confirm", "permanently"],
                      timeout=60)
        # turn 2: confirm
        if ask.strip() and REFUSED not in ask:
            step(session, url, "USB", f"Delete {label} (confirm)",
                 "yes delete it confirmed",
                 must_contain=["delet", "success", "removed"],
                 timeout=60)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Full chatbot flow test for all 5 modules")
    parser.add_argument("--url", default=DEFAULT_BASE, help="Django server base URL")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print()
    print("═" * 65)
    print(f"  {BLD}FULL CHATBOT FLOW TEST — ALL 5 MODULES{RST}")
    print(f"  server : {base}")
    print(f"  run tag: {RUN_TAG}")
    print(f"  backtest window: {BT_START} → {BT_END}")
    print("═" * 65)
    print()

    session = login(base)

    test_usb(session, base)
    test_ise(session, base)
    test_isb(session, base)
    test_res(session, base)
    test_mlh(session, base)

    test_delete_two(session, base)

    passed = R.summary()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
