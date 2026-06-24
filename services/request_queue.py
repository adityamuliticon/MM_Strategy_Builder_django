"""Sliding-window LLM concurrency limiter.

MAX_CONCURRENT slots run simultaneously. Each slot releases the instant its
request finishes — the next queued request starts without waiting for others.
This is the sliding window: 50 running, rest queued, zero idle slots.

Usage — non-streaming (context manager):
    with request_queue:
        result = orchestrator.process_message(msg, history)

Usage — streaming (manual, must release in finally):
    start = request_queue.acquire()
    def stream():
        try:
            yield ...
        finally:
            request_queue.release(start)
"""

import collections
import threading
import time

MAX_CONCURRENT = 50


class RequestQueue:
    def __init__(self, max_concurrent: int = MAX_CONCURRENT):
        self._sem = threading.BoundedSemaphore(max_concurrent)
        self._lock = threading.Lock()
        self._active = 0
        self._waiting = 0
        self._processed = 0
        self._durations: collections.deque = collections.deque(maxlen=200)
        self._tl = threading.local()  # per-thread start time for __enter__/__exit__

    # ── Core acquire / release ─────────────────────────────────────────────────

    def acquire(self) -> float:
        """Block until a slot is free. Returns a start_time token for release()."""
        with self._lock:
            self._waiting += 1
        self._sem.acquire()           # yields (gevent) or blocks until free
        with self._lock:
            self._waiting -= 1
            self._active += 1
        return time.monotonic()

    def release(self, start_time: float) -> None:
        """Release the slot immediately. Always call this in a finally block."""
        duration = time.monotonic() - start_time
        with self._lock:
            self._active -= 1
            self._processed += 1
            self._durations.append(duration)
        self._sem.release()           # wakes the next waiting request instantly

    # ── Context manager (non-streaming) ───────────────────────────────────────

    def __enter__(self):
        self._tl.start = self.acquire()
        return self

    def __exit__(self, *_):
        self.release(self._tl.start)

    # ── Stats ──────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        with self._lock:
            avg = (sum(self._durations) / len(self._durations)) if self._durations else 5.0
            w = self._waiting
            return {
                "capacity": MAX_CONCURRENT,
                "active": self._active,
                "waiting": w,
                "processed": self._processed,
                "avg_duration_s": round(avg, 1),
                "est_wait_s": round((w / MAX_CONCURRENT) * avg, 1) if w else 0,
            }


# Singleton — imported by all views
request_queue = RequestQueue(MAX_CONCURRENT)
