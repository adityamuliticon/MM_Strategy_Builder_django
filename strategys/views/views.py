from utils.orchestrator.orchestrators import (
    orchestrator,
    mlh_orchestrator,
    res_orchestrator,
    isb_orchestrator,
    ise_orchestrator,
)
from strategys.views.common import make_chat_views

# ── USB ───────────────────────────────────────────────────────────────────────
usb_chat, usb_chat_stream = make_chat_views(module='USB', orchestrator=orchestrator)

# ── MLH ───────────────────────────────────────────────────────────────────────
mlh_chat, mlh_chat_stream = make_chat_views(module='MLH', orchestrator=mlh_orchestrator)

# ── RES ───────────────────────────────────────────────────────────────────────
res_chat, res_chat_stream = make_chat_views(module='RES', orchestrator=res_orchestrator)

# ── ISB ───────────────────────────────────────────────────────────────────────
isb_chat, isb_chat_stream = make_chat_views(module='ISB', orchestrator=isb_orchestrator)

# ── ISE ───────────────────────────────────────────────────────────────────────
ise_chat, ise_chat_stream = make_chat_views(module='ISE', orchestrator=ise_orchestrator)
