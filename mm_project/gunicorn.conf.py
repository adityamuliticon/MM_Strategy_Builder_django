"""Gunicorn production config — gevent workers for high-concurrency queue system.

Start command:
    gunicorn mm_project.wsgi:application -c gunicorn.conf.py

How it handles 10k–100k users:
- worker_class=gevent: each connection is a greenlet (not an OS thread).
  Blocked semaphore.acquire() calls yield to other greenlets — zero thread overhead
  while waiting in queue. Gevent monkey-patches threading, so threading.Semaphore
  and threading.local() in request_queue.py / session_context.py both work correctly.
- worker_connections=10000: up to 10k simultaneous HTTP connections per worker.
- workers=1: single process → one shared RequestQueue.semaphore(50) governs all
  LLM slots globally. With multiple workers each process gets its own semaphore,
  so concurrent LLM calls = workers × 50. Keep workers=1 unless your LLM API
  has a higher rate limit.
"""

import os

bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", "1"))
worker_class = "gevent"
worker_connections = int(os.environ.get("GUNICORN_CONNECTIONS", "10000"))

# Generous timeout — LLM calls can take 10–30s; streaming holds connections longer.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
keepalive = 5

# Logging
accesslog = "-"   # stdout
errorlog  = "-"   # stdout
loglevel  = os.environ.get("GUNICORN_LOG_LEVEL", "info")
