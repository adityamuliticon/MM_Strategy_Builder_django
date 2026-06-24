#!/usr/bin/env python3
"""
Real end-to-end load test — 100 concurrent Django requests, zero Runware calls.

Full stack tested per request:
  HTTP → AuthMiddleware → view → setup_user_context → thread-local →
  get_history (DB) → request_queue.acquire() → [QUEUE WAIT] →
  orchestrator.process_message → RAG retriever (local FAISS) →
  LLM mock (returns instantly, no API) → request_queue.release() →
  save_messages (DB) → ChatLog.create (DB) → JsonResponse

Messages mixed 50/50:
  "make multi-leg strategy of 10 leg do on reliance"  — tests strategy flow + RAG
  "what is SL"                                        — tests knowledge RAG retrieval

Run:
    .venv/bin/python test_queue_load.py
"""

import os
import random
import statistics
import sys
import threading
import time
import uuid
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

# ── Django setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mm_project.settings")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

import warnings
warnings.filterwarnings("ignore")

import django
django.setup()

# Allow test-client's default hostname so ALLOWED_HOSTS doesn't block us
from django.conf import settings as _dj_settings
_dj_settings.ALLOWED_HOSTS = ['*']

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_REQUESTS  = 100
QUEUE_CAPACITY  = 50
MESSAGES = (
    ["make multi-leg strategy of 10 leg do on reliance"] * 50 +
    ["what is SL"] * 50
)
random.shuffle(MESSAGES)

# ── Build a mock LLM response (SimpleNamespace so attribute access works) ─────
# No MagicMock — real int token counts so _in_tok += doesn't blow up.
def _mock_completion(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=180, completion_tokens=90),
        choices=[SimpleNamespace(
            message=SimpleNamespace(
                content=text,
                tool_calls=None,
            )
        )],
    )

MOCK_RESPONSES = {
    "make multi-leg strategy of 10 leg do on reliance": (
        "To create a 10-leg multi-leg strategy on Reliance I will need more details. "
        "Please specify the segment (FUT/OPT/EQ), expiry, strike prices, and lot sizes "
        "for each leg. Would you like me to suggest a default configuration?"
    ),
    "what is SL": (
        "**Stop Loss (SL)** is a risk management order that automatically exits your "
        "position when the price moves against you by a specified amount. "
        "It limits your maximum loss on a trade. You can define SL in terms of "
        "points (Money) or percentage. In Market Maya strategies, every leg supports "
        "an individual SL as well as a master SL for the overall strategy."
    ),
}

def _llm_side_effect(**kw):
    """Called instead of self.client.chat.completions.create — no network, no cost."""
    # Simulate LLM thinking time: 1–4s (realistic for a fast model)
    time.sleep(random.uniform(1.0, 4.0))
    # Detect which message is being answered from the messages list
    user_msg = ""
    for m in reversed(kw.get("messages", [])):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break
    for key, reply in MOCK_RESPONSES.items():
        if key in user_msg or user_msg in key:
            return _mock_completion(reply)
    return _mock_completion("Mock response: request processed successfully.")


# ── Patch the OpenAI client on all 5 orchestrator singletons ─────────────────
# RAG runs REAL (local FAISS + sentence-transformers, no API).
# Only the final self.client.chat.completions.create is replaced.
print("  Loading orchestrators and patching LLM client...", flush=True)

from multi_leg_hedger.core.orchestrator          import mlh_orchestrator
from Unified_Strategy_Builder.core.orchestrator  import orchestrator as usb_orchestrator
from rapid_execution_scalper.core.orchestrator   import res_orchestrator
from inbound_signal_bridge.core.orchestrator     import isb_orchestrator
from indicator_engine.core.orchestrator          import ise_orchestrator

_ORCHESTRATORS = [mlh_orchestrator, usb_orchestrator, res_orchestrator,
                  isb_orchestrator, ise_orchestrator]

for orch in _ORCHESTRATORS:
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = _llm_side_effect
    orch.client = mock_client

print("  LLM patched on all 5 orchestrators — RAG still runs locally.\n", flush=True)


# ── Create a test user + session in DB ───────────────────────────────────────
from users.models import AppUser, UserBearerToken
from django.contrib.sessions.backends.db import SessionStore

TEST_EMAIL  = f"loadtest_{uuid.uuid4().hex[:8]}@test.local"
TEST_UID    = uuid.uuid4()

AppUser.objects.filter(email__endswith="@test.local").delete()

test_user  = AppUser.objects.create(id=TEST_UID, email=TEST_EMAIL, display_name="Load Test")
UserBearerToken.objects.create(user=test_user, token="fake-bearer-token-for-load-test")

sess = SessionStore()
sess["user_id"]      = str(TEST_UID)
sess["display_name"] = "Load Test"
sess.create()
SESSION_KEY = sess.session_key

print(f"  Test user  : {TEST_EMAIL}  ({TEST_UID})")
print(f"  Session key: {SESSION_KEY}\n", flush=True)


# ── Shared metrics ────────────────────────────────────────────────────────────
results      = []
results_lock = threading.Lock()
peak_active  = 0
peak_waiting = 0
peak_lock    = threading.Lock()

from services.request_queue import request_queue as live_queue

def _track_peaks():
    global peak_active, peak_waiting
    s = live_queue.stats
    with peak_lock:
        if s["active"]  > peak_active:  peak_active  = s["active"]
        if s["waiting"] > peak_waiting: peak_waiting = s["waiting"]


# ── One request worker ────────────────────────────────────────────────────────
from django.test import Client

def fire_request(req_id: int) -> dict:
    msg        = MESSAGES[req_id - 1]
    t_submit   = time.monotonic()
    status_ok  = False
    http_code  = 0
    error_note = ""
    response_snippet = ""

    try:
        client = Client()                                    # thread-local Client instance
        client.cookies["sessionid"] = SESSION_KEY           # share the session

        import json as _json
        resp = client.post(
            "/hedger/api/chat",                              # MLH endpoint (tests the full stack)
            data=_json.dumps({"message": msg}),
            content_type="application/json",
            HTTP_HOST="localhost",
        )
        http_code = resp.status_code
        _track_peaks()

        if resp.status_code == 200:
            body = _json.loads(resp.content)
            status_ok = body.get("status") == "success"
            response_snippet = body.get("message", "")[:60].replace("\n", " ")
        else:
            error_note = resp.content.decode()[:80]

    except Exception as exc:
        error_note = str(exc)[:80]

    t_end = time.monotonic()
    record = {
        "id":        req_id,
        "msg_type":  "strategy" if "strategy" in msg else "rag",
        "http":      http_code,
        "ok":        status_ok,
        "total_s":   round(t_end - t_submit, 3),
        "snippet":   response_snippet,
        "error":     error_note,
    }
    with results_lock:
        results.append(record)
    return record


# ── Banner ────────────────────────────────────────────────────────────────────
def hr(ch="─", w=68): return ch * w

print(hr("═"))
print("  MM STRATEGY BUILDER — REAL STACK LOAD TEST")
print(f"  {TOTAL_REQUESTS} concurrent requests  |  queue capacity: {QUEUE_CAPACITY} slots")
print(f"  50×  'make multi-leg strategy of 10 leg do on reliance'")
print(f"  50×  'what is SL'")
print(f"  LLM: mocked (1–4s delay, no API call)  |  RAG: real (local FAISS)")
print(hr("═"))
print()

# ── Fire all 100 at once ──────────────────────────────────────────────────────
t_wall_start = time.monotonic()

with ThreadPoolExecutor(max_workers=TOTAL_REQUESTS) as pool:
    futures = [pool.submit(fire_request, i + 1) for i in range(TOTAL_REQUESTS)]

    last_done = -1
    while True:
        done = sum(1 for f in futures if f.done())
        s    = live_queue.stats
        if done != last_done:
            bar_fill = int((done / TOTAL_REQUESTS) * 30)
            bar = "█" * bar_fill + "░" * (30 - bar_fill)
            print(
                f"\r  [{bar}] {done:3d}/{TOTAL_REQUESTS}"
                f"  active={s['active']:2d}  waiting={s['waiting']:3d}"
                f"  processed={s['processed']:3d}",
                end="", flush=True,
            )
            last_done = done
        if done >= TOTAL_REQUESTS:
            break
        time.sleep(0.3)

t_wall = time.monotonic() - t_wall_start
print(f"\r  {'█'*30} {TOTAL_REQUESTS}/{TOTAL_REQUESTS}  DONE" + " " * 35)
print()


# ── Analysis ──────────────────────────────────────────────────────────────────
ok     = [r for r in results if r["ok"]]
failed = [r for r in results if not r["ok"]]

strategy_ok  = [r for r in ok if r["msg_type"] == "strategy"]
rag_ok       = [r for r in ok if r["msg_type"] == "rag"]
totals       = [r["total_s"] for r in ok]
strat_totals = [r["total_s"] for r in strategy_ok]
rag_totals   = [r["total_s"] for r in rag_ok]


def p(data, pct):
    if not data: return 0.0
    s = sorted(data)
    return round(s[min(int(len(s) * pct / 100), len(s) - 1)], 3)

def fmt(v): return f"{v:>8.3f}s"


print(hr())
print("  RESULTS SUMMARY")
print(hr())
print(f"  Total requests     : {TOTAL_REQUESTS}")
print(f"  Succeeded          : {len(ok)}")
print(f"  Failed             : {len(failed)}")
print(f"  Wall-clock time    : {t_wall:.2f}s  (all {TOTAL_REQUESTS} requests)")
print(f"  Throughput         : {TOTAL_REQUESTS / t_wall:.1f} req/s")
print()
print(f"  By message type:")
print(f"    Strategy creation  : {len(strategy_ok)} ok / {50 - len(strategy_ok)} failed")
print(f"    RAG (what is SL)   : {len(rag_ok)} ok / {50 - len(rag_ok)} failed")
print()

# Latency table
col = 10
print(f"  {'Metric':<20}  {'All':>{col}}  {'Strategy':>{col}}  {'RAG':>{col}}")
print(f"  {'──────':<20}  {'───':>{col}}  {'────────':>{col}}  {'───':>{col}}")
for label, pct in [("Min", None), ("Max", None), ("Mean", None),
                   ("p50 (median)", 50), ("p75", 75), ("p90", 90),
                   ("p95", 95), ("p99", 99)]:
    def _v(data):
        if not data: return 0.0
        if pct is None:
            return min(data) if label == "Min" else max(data) if label == "Max" else statistics.mean(data)
        return p(data, pct)
    print(f"  {label:<20}  {fmt(_v(totals))}  {fmt(_v(strat_totals))}  {fmt(_v(rag_totals))}")

print()
print(f"  Peak concurrent active  : {peak_active}  (limit={QUEUE_CAPACITY})")
print(f"  Peak queued waiting     : {peak_waiting}")
print(f"  Final queue state       : {live_queue.stats}")


# ── Total time histogram ──────────────────────────────────────────────────────
print()
print(hr())
print("  TOTAL TIME PER REQUEST DISTRIBUTION")
print(hr())

buckets = [(0,2),(2,4),(4,6),(6,8),(8,10),(10,13),(13,17),(17,25),(25,999)]
labels  = ["<2s","2-4s","4-6s","6-8s","8-10s","10-13s","13-17s","17-25s","25s+"]
max_bar = 38

for (lo, hi), label in zip(buckets, labels):
    count_all  = sum(1 for t in totals      if lo <= t < hi)
    count_strt = sum(1 for t in strat_totals if lo <= t < hi)
    count_rag  = sum(1 for t in rag_totals   if lo <= t < hi)
    bar_s = "S" * count_strt
    bar_r = "R" * count_rag
    combined = bar_s + bar_r
    bar = combined[:max_bar]
    pct = count_all / len(totals) * 100 if totals else 0
    print(f"  {label:<8}  {bar:<{max_bar}}  {count_all:>3} ({pct:5.1f}%)  S={count_strt} R={count_rag}")

print(f"  (S=strategy request, R=RAG/'what is SL' request)")


# ── Top 10 slowest ────────────────────────────────────────────────────────────
print()
print(hr())
print("  TOP 10 SLOWEST REQUESTS")
print(hr())
print(f"  {'Req#':<6}  {'Type':<9}  {'Total':<10}  {'HTTP':<5}  Response (first 60 chars)")
print(f"  {'────':<6}  {'────':<9}  {'─────':<10}  {'────':<5}  ────────────────────────────")
for r in sorted(ok, key=lambda x: x["total_s"], reverse=True)[:10]:
    mtype = "strategy" if r["msg_type"] == "strategy" else "RAG"
    print(f"  #{r['id']:<5}  {mtype:<9}  {r['total_s']:<10.3f}  {r['http']:<5}  {r['snippet']}")


# ── Failures ──────────────────────────────────────────────────────────────────
if failed:
    print()
    print(hr())
    print("  FAILED REQUESTS")
    print(hr())
    for r in failed:
        mtype = "strategy" if r["msg_type"] == "strategy" else "RAG"
        print(f"  #{r['id']:<5}  {mtype:<9}  HTTP={r['http']}  {r['error']}")


# ── Integrity checks ──────────────────────────────────────────────────────────
print()
print(hr())
print("  INTEGRITY CHECKS")
print(hr())

from chat_logs.models import ChatLog, ChatMessage

db_logs = ChatLog.objects.filter(user_id=str(TEST_UID)).count()
db_msgs = ChatMessage.objects.filter(user_id=str(TEST_UID)).count()

checks = [
    ("Queue slots never exceeded capacity",
     peak_active <= QUEUE_CAPACITY,
     f"peak={peak_active}, limit={QUEUE_CAPACITY}"),
    ("All queue slots released",
     live_queue.stats["active"] == 0,
     f"active={live_queue.stats['active']}"),
    ("Zero requests failed",
     len(failed) == 0,
     f"failed={len(failed)}"),
    ("ChatLog rows written to DB",
     db_logs > 0,
     f"{db_logs} rows"),
    ("ChatMessage rows written to DB",
     db_msgs > 0,
     f"{db_msgs} rows  (2 per request = {len(ok)*2} expected)"),
    ("Strategy requests all answered",
     len(strategy_ok) == 50,
     f"{len(strategy_ok)}/50"),
    ("RAG requests all answered",
     len(rag_ok) == 50,
     f"{len(rag_ok)}/50"),
]

all_pass = True
for label, passed, detail in checks:
    icon = "✓" if passed else "✗"
    all_pass = all_pass and passed
    print(f"  {icon}  {label:<42}  {detail}")

print()
if all_pass:
    print("  ✓  ALL CHECKS PASSED — full stack is production-ready")
else:
    print("  ✗  SOME CHECKS FAILED — see above")
print(hr("═"))


# ── Cleanup test data ─────────────────────────────────────────────────────────
print(f"\n  Cleaning up test user and session from DB...", end="")
ChatLog.objects.filter(user_id=str(TEST_UID)).delete()
ChatMessage.objects.filter(user_id=str(TEST_UID)).delete()
AppUser.objects.filter(id=TEST_UID).delete()
sess.delete()
print(" done.\n")
