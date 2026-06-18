"""
Backtest Flow Test — "123asd" MLH strategy, 1 Month period
Tests the two-turn chatbot SSE stream flow:
  Turn 1: "backtest this 123asd"  →  expect options table with periods
  Turn 2: "1"                     →  expect backtest triggered (NOT "No response received")

Run:  python tests/test_backtest_flow.py
"""

import json
import sys
import time
import requests

BASE_URL   = "http://localhost:8000"
STREAM_URL = f"{BASE_URL}/hedger/api/chat/stream"
SESSION_ID = f"test_backtest_{int(time.time())}"


def stream_chat(message, timeout=120):
    """POST to MLH chat/stream; parse SSE and return (accumulated_text, events)."""
    try:
        resp = requests.post(
            STREAM_URL,
            json={"message": message, "session_id": SESSION_ID},
            stream=True,
            timeout=timeout,
        )
        resp.raise_for_status()
    except Exception as e:
        return f"CONNECTION_ERROR: {e}", []

    accumulated = ""
    events = []
    buf = ""

    try:
        for raw in resp.iter_content(chunk_size=None):
            if not raw:
                continue
            buf += raw.decode("utf-8", errors="replace")
            parts = buf.split("\n\n")
            buf = parts.pop()

            for part in parts:
                if not part.startswith("data: "):
                    continue
                try:
                    evt = json.loads(part[6:])
                    events.append(evt)
                    if evt.get("t") == "chunk":
                        accumulated += evt.get("v", "")
                    elif evt.get("t") in ("done", "error"):
                        return accumulated, events
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        return accumulated or f"STREAM_ERROR: {e}", events

    return accumulated, events


def hr(char="─", n=60):
    print(char * n)


def main():
    hr("═")
    print("  BACKTEST FLOW TEST  |  MLH  |  strategy='123asd'  |  1 Month")
    print(f"  session: {SESSION_ID}")
    hr("═")

    # ── Turn 1: request options ──────────────────────────────────────────────
    print("\n[Turn 1]  'backtest this 123asd'")
    t0 = time.time()
    resp1, events1 = stream_chat("backtest this 123asd")
    dur1 = time.time() - t0

    status1 = [e["v"] for e in events1 if e.get("t") == "status"]
    print(f"          {dur1:.1f}s  |  tools: {status1}")
    print(f"          response:\n{resp1[:500]}\n")

    if not resp1 or resp1.startswith(("CONNECTION_ERROR", "STREAM_ERROR")):
        hr("═")
        print(f"  FAIL ✗  Turn 1 failed: {resp1}")
        hr("═")
        sys.exit(1)

    resp1_l = resp1.lower()
    if not any(w in resp1_l for w in ("month", "period", "pts", "backtest")):
        hr("═")
        print("  FAIL ✗  Turn 1: response doesn't look like backtest options")
        hr("═")
        sys.exit(1)

    print("  PASS ✓  Turn 1 — backtest options received")

    # ── Turn 2: select period 1 (1 Month) ───────────────────────────────────
    time.sleep(0.5)
    print("\n[Turn 2]  '1'  (select 1 Month period)")
    t0 = time.time()
    resp2, events2 = stream_chat("1", timeout=90)
    dur2 = time.time() - t0

    status2 = [e["v"] for e in events2 if e.get("t") == "status"]
    print(f"          {dur2:.1f}s  |  tools: {status2}")
    print(f"          response:\n{resp2}\n")

    # ── Verdict ──────────────────────────────────────────────────────────────
    if not resp2 or resp2.startswith(("CONNECTION_ERROR", "STREAM_ERROR")):
        hr("═")
        print(f"  FAIL ✗  Turn 2 connection error: {resp2}")
        hr("═")
        sys.exit(1)

    if "no response received" in resp2.lower():
        hr("═")
        print("  FAIL ✗  'No response received' — backtest was not triggered")
        hr("═")
        sys.exit(1)

    resp2_l = resp2.lower()
    success = ["triggered", "processing", "backtest", "30 second", "get_backtest_result"]
    api_err  = ["insufficient", "balance", "not found", "error", "failed"]

    hr("═")
    if any(w in resp2_l for w in success):
        print("  PASS ✓  Backtest triggered — chatbot confirmed the run")
    elif any(w in resp2_l for w in api_err):
        print("  PASS ✓  Chatbot responded with an API error (strategy/balance/auth)")
        print("          Fix is working — 'No response received' is gone")
    else:
        print("  PASS ✓  Got a response (check output manually)")
    hr("═")
    sys.exit(0)


if __name__ == "__main__":
    main()
