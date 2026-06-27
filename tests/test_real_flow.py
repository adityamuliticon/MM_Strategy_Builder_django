#!/usr/bin/env python3
"""
Real end-to-end load test — 100 concurrent "what is SL" requests.

Full stack per request (no shortcuts):
  HTTP → AuthMiddleware → session → setup_user_context → thread-local →
  get_history (DB) → request_queue.acquire() → [QUEUE WAIT IF FULL] →
  orchestrator.process_message →
    ├─ RAG: _retriever().get_context()  ← local FAISS, real
    ├─ build prompt
    └─ LLM call → real Runware API call
  request_queue.release() → save_messages (DB) → ChatLog.create → JsonResponse

Real user from DB. Real Runware API. Real RAG.

Run:
    .venv/bin/python test_real_flow.py
"""

import os, sys, json, time, statistics, threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mm_project.settings")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
import warnings; warnings.filterwarnings("ignore")

import django; django.setup()
from django.conf import settings as _dj
_dj.ALLOWED_HOSTS = ["*"]

def hr(c="─", w=68): return c * w
def section(t): print(); print(hr()); print(f"  {t}"); print(hr())

# ── STEP 0 — Show Runware config ─────────────────────────────────────────────
section("STEP 0  Runware config check")
from config import Config
api_set   = bool(Config.RUNWARE_API_KEY)
model_set = bool(Config.RUNWARE_MODEL_ID)
print(f"  RUNWARE_API_KEY   = {'✓ SET (real API calls)' if api_set   else '(empty) — will fail!'}")
print(f"  RUNWARE_MODEL_ID  = {Config.RUNWARE_MODEL_ID if model_set else '(empty) — will fail!'}")
if not api_set:
    print("\n  ✗  RUNWARE_API_KEY is not set. Add it to .env and retry.")
    sys.exit(1)

# ── STEP 1 — Load real user ───────────────────────────────────────────────────
section("STEP 1  Load real user from DB")
from users.models import AppUser, UserBearerToken
users = list(AppUser.objects.all())
if not users:
    print("  ✗  No users found. Log in to the app first."); sys.exit(1)

print("  Available users:")
for i, u in enumerate(users):
    tok = UserBearerToken.objects.filter(user=u).first()
    print(f"    [{i}]  {u.email}  —  {u.id}  —  token: {'yes' if tok else 'NO'}")

choice = 0
if len(users) > 1:
    try:
        choice = int(input(f"\n  Pick user [0–{len(users)-1}] (Enter=0): ").strip() or "0")
    except ValueError:
        choice = 0

real_user    = users[choice]
token_record = UserBearerToken.objects.filter(user=real_user).first()
print(f"\n  Using : {real_user.email}")
print(f"  UUID  : {real_user.id}")
print(f"  Token : {'present ✓' if token_record else 'MISSING ✗'}")

# ── STEP 2 — Session ─────────────────────────────────────────────────────────
section("STEP 2  Create temporary session for real user")
from django.contrib.sessions.backends.db import SessionStore
sess = SessionStore()
sess["user_id"]      = str(real_user.id)
sess["display_name"] = real_user.display_name
sess.create()
SESSION_KEY = sess.session_key
print(f"  Session key : {SESSION_KEY}")
print(f"  user_id     : {sess['user_id']}")

# ── STEP 3 — Load orchestrator (NO mock — real Runware) ──────────────────────
section("STEP 3  Load USB orchestrator — real RAG + real Runware")

print("  Loading orchestrator (FAISS + embeddings)...", flush=True)
from utils.Orchestrator.orchestrators import orchestrator as usb_orch

# Quick RAG sanity check
print("  Running RAG test for 'what is SL'...", flush=True)
t0 = time.monotonic()
ctx = usb_orch._retriever().get_context("what is SL")
rag_ms = (time.monotonic() - t0) * 1000
print(f"  ✓  RAG retrieved {len(ctx)} chars in {rag_ms:.0f}ms")
print(f"  Preview: {ctx[:120].replace(chr(10),' ')[:110]}...")
print(f"  LLM    : real Runware API  ({Config.RUNWARE_MODEL_ID})")

# ── STEP 4 — 100 concurrent requests ─────────────────────────────────────────
section("STEP 4  Fire 100 concurrent requests of 'what is SL'")

from django.test import Client
from chat_logs.models import ChatLog, ChatMessage
from services.request_queue import request_queue as live_queue

TOTAL        = 100
MESSAGE      = "what is SL"
results      = []
results_lock = threading.Lock()
peak_active  = 0
peak_waiting = 0
peak_lock    = threading.Lock()

def _track():
    global peak_active, peak_waiting
    s = live_queue.stats
    with peak_lock:
        if s["active"]  > peak_active:  peak_active  = s["active"]
        if s["waiting"] > peak_waiting: peak_waiting = s["waiting"]

db_before_msgs = ChatMessage.objects.filter(user_id=str(real_user.id)).count()
db_before_logs = ChatLog.objects.filter(user_id=str(real_user.id)).count()

def fire(req_id):
    t_submit = time.monotonic()
    http = 0; ok = False; snippet = ""; error = ""
    try:
        c = Client()
        c.cookies["sessionid"] = SESSION_KEY
        resp = c.post("/api/chat",
                      data=json.dumps({"message": MESSAGE}),
                      content_type="application/json",
                      HTTP_HOST="localhost")
        http = resp.status_code
        _track()
        if http == 200:
            body = json.loads(resp.content)
            ok   = body.get("status") == "success"
            snippet = body.get("message", "")[:80].replace("\n"," ")
        else:
            error = resp.content.decode()[:60]
    except Exception as exc:
        error = str(exc)[:60]

    record = {
        "id": req_id, "http": http, "ok": ok,
        "total_s": round(time.monotonic() - t_submit, 3),
        "snippet": snippet, "error": error,
    }
    with results_lock:
        results.append(record)
    return record

print(f"  Firing {TOTAL} requests simultaneously...\n")
t_wall_start = time.monotonic()

with ThreadPoolExecutor(max_workers=TOTAL) as pool:
    futures = [pool.submit(fire, i+1) for i in range(TOTAL)]
    last_done = -1
    while True:
        done = sum(1 for f in futures if f.done())
        s    = live_queue.stats
        if done != last_done:
            bar  = "█" * int(done/TOTAL*30) + "░" * (30 - int(done/TOTAL*30))
            print(f"\r  [{bar}] {done:3d}/{TOTAL}"
                  f"  active={s['active']:2d}  waiting={s['waiting']:3d}"
                  f"  processed={s['processed']:3d}",
                  end="", flush=True)
            last_done = done
        if done >= TOTAL: break
        time.sleep(0.5)

t_wall = time.monotonic() - t_wall_start
print(f"\r  {'█'*30} {TOTAL}/{TOTAL}  DONE" + " "*35)

# ── STEP 5 — Analysis ─────────────────────────────────────────────────────────
section("STEP 5  Results")

ok_list   = [r for r in results if r["ok"]]
fail_list = [r for r in results if not r["ok"]]
totals    = [r["total_s"] for r in ok_list]

def p(data, pct):
    if not data: return 0.0
    s = sorted(data)
    return round(s[min(int(len(s)*pct/100), len(s)-1)], 3)

print(f"  Total requests  : {TOTAL}")
print(f"  Succeeded       : {len(ok_list)}")
print(f"  Failed          : {len(fail_list)}")
print(f"  Wall-clock time : {t_wall:.2f}s")
print(f"  Throughput      : {TOTAL/t_wall:.1f} req/s")
print()
if totals:
    col = 10
    print(f"  {'Metric':<18}  {'Total time':>{col}}")
    print(f"  {'──────':<18}  {'──────────':>{col}}")
    for lbl, val in [
        ("Min",          min(totals)),
        ("Max",          max(totals)),
        ("Mean",         statistics.mean(totals)),
        ("Median (p50)", p(totals, 50)),
        ("p75",          p(totals, 75)),
        ("p90",          p(totals, 90)),
        ("p95",          p(totals, 95)),
        ("p99",          p(totals, 99)),
        ("Std dev",      statistics.stdev(totals) if len(totals) > 1 else 0),
    ]:
        print(f"  {lbl:<18}  {val:>{col}.3f}s")

print()
print(f"  Peak concurrent active  : {peak_active}  (limit=50)")
print(f"  Peak queued waiting     : {peak_waiting}")
print(f"  Final queue state       : {live_queue.stats}")

# Histogram
print()
print(hr())
print("  TOTAL TIME PER REQUEST DISTRIBUTION")
print(hr())
buckets = [(0,2),(2,5),(5,10),(10,15),(15,20),(20,30),(30,45),(45,60),(60,999)]
labels  = ["<2s","2-5s","5-10s","10-15s","15-20s","20-30s","30-45s","45-60s","60s+"]
for (lo, hi), lbl in zip(buckets, labels):
    cnt = sum(1 for t in totals if lo <= t < hi)
    bar = "█" * int(cnt / max(len(totals), 1) * 38)
    pct = cnt / max(len(totals), 1) * 100
    print(f"  {lbl:<8}  {bar:<38}  {cnt:>3} ({pct:5.1f}%)")

# Sample responses — show what RAG+LLM actually returned
print()
print(hr())
print("  SAMPLE RESPONSES (first 5 successful)")
print(hr())
for r in sorted(ok_list, key=lambda x: x["id"])[:5]:
    print(f"  Req #{r['id']:3d}  [{r['total_s']:.1f}s]  {r['snippet']}")

# Top 5 slowest
print()
print(hr())
print("  TOP 5 SLOWEST REQUESTS")
print(hr())
for r in sorted(ok_list, key=lambda x: x["total_s"], reverse=True)[:5]:
    print(f"  #{r['id']:<5}  {r['total_s']:.3f}s   {r['snippet']}")

if fail_list:
    print()
    print(hr())
    print("  FAILED REQUESTS")
    print(hr())
    for r in fail_list:
        print(f"  #{r['id']:<5}  HTTP={r['http']}  {r['error']}")

# ── STEP 6 — DB verification ──────────────────────────────────────────────────
section("STEP 6  Database verification")
db_after_msgs = ChatMessage.objects.filter(user_id=str(real_user.id)).count()
db_after_logs = ChatLog.objects.filter(user_id=str(real_user.id)).count()
new_msgs = db_after_msgs - db_before_msgs
new_logs = db_after_logs - db_before_logs
print(f"  ChatMessage rows added : {new_msgs}  (expected: {len(ok_list)*2}  = 2 per request)")
print(f"  ChatLog rows added     : {new_logs}  (expected: {len(ok_list)})")

# ── STEP 7 — Integrity checks ─────────────────────────────────────────────────
section("STEP 7  Integrity checks")
checks = [
    ("Runware API key set",             api_set,                         f"model={Config.RUNWARE_MODEL_ID}"),
    ("All requests returned HTTP 200",  len(fail_list) == 0,             f"failed={len(fail_list)}"),
    ("Queue never exceeded 50 slots",   peak_active <= 50,               f"peak={peak_active}"),
    ("All slots released after test",   live_queue.stats["active"] == 0, f"active={live_queue.stats['active']}"),
    ("RAG retrieved context",           bool(ctx.strip()),               f"{len(ctx)} chars in {rag_ms:.0f}ms"),
    ("ChatMessage rows correct",        new_msgs == len(ok_list) * 2,    f"{new_msgs} rows"),
    ("ChatLog rows correct",            new_logs == len(ok_list),        f"{new_logs} rows"),
]
all_pass = all(ok for _, ok, _ in checks)
for lbl, passed, detail in checks:
    print(f"  {'✓' if passed else '✗'}  {lbl:<44}  {detail}")

print()
if all_pass:
    print("  ✓  ALL CHECKS PASSED")
    print()
    print(f"  Wall time  : {t_wall:.2f}s total for {TOTAL} requests")
    print(f"  Throughput : {TOTAL/t_wall:.1f} req/s")
    print(f"  RAG        : {rag_ms:.0f}ms per retrieval (local FAISS)")
    print(f"  DB writes  : {new_msgs} ChatMessage + {new_logs} ChatLog rows written correctly")
else:
    print("  ✗  SOME CHECKS FAILED")
print(hr("═"))

# ── Cleanup session (keep real user's chat history) ───────────────────────────
sess.delete()
print(f"\n  Session deleted. User chat history preserved.\n")
