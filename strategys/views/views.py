from django.http import JsonResponse
from django.utils.timezone import now

from utils.orchestrator.orchestrators import (
    orchestrator,
    mlh_orchestrator,
    res_orchestrator,
    isb_orchestrator,
    ise_orchestrator,
)
from strategys.views.common import make_chat_views
from marketmaya.config import Config
from marketmaya.operations import Operations

get_strategies = Operations.get_strategies
get_balance    = Operations.get_balance

_STRATEGY_TYPE_IDS = Config.STRATEGY_TYPE_IDS
_ID_TO_KEY = {v: k for k, v in _STRATEGY_TYPE_IDS.items()}

# ── USB ───────────────────────────────────────────────────────────────────────
usb_chat, usb_chat_stream = make_chat_views(module='USB', orchestrator=orchestrator)


def strategy_counts_view(request):
    result = get_strategies(take=1000)
    if result.get("status") != "success":
        return JsonResponse({k: None for k in _STRATEGY_TYPE_IDS})

    counts = {k: 0 for k in _STRATEGY_TYPE_IDS}
    strategies = result.get("strategies", [])
    for s in strategies:
        key = _ID_TO_KEY.get(s.get("master_id", ""))
        if key:
            counts[key] += 1

    if strategies and not any(counts.values()):
        plugin_counts = {}
        for s in strategies:
            p = s.get("plugin", "unknown")
            plugin_counts[p] = plugin_counts.get(p, 0) + 1
        print(f"[strategy_counts] master_id unrecognised. Plugin breakdown: {plugin_counts}")

    user_id = request.session.get('user_id')
    if user_id:
        from users.models import UserBearerToken
        UserBearerToken.objects.filter(user_id=user_id).update(
            cached_strategy_counts=counts,
            data_cached_at=now(),
        )

    return JsonResponse(counts)


def balance_view(request):
    result = get_balance()
    if result.get("status") == "success":
        point_balance = result["point_balance"]
        user_id = request.session.get('user_id')
        if user_id:
            from users.models import UserBearerToken
            UserBearerToken.objects.filter(user_id=user_id).update(
                cached_point_balance=point_balance,
                data_cached_at=now(),
            )
        return JsonResponse({"point_balance": point_balance})
    return JsonResponse({"point_balance": None})

# ── MLH ───────────────────────────────────────────────────────────────────────
mlh_chat, mlh_chat_stream = make_chat_views(module='MLH', orchestrator=mlh_orchestrator)

# ── RES ───────────────────────────────────────────────────────────────────────
res_chat, res_chat_stream = make_chat_views(module='RES', orchestrator=res_orchestrator)

# ── ISB ───────────────────────────────────────────────────────────────────────
isb_chat, isb_chat_stream = make_chat_views(module='ISB', orchestrator=isb_orchestrator)

# ── ISE ───────────────────────────────────────────────────────────────────────
ise_chat, ise_chat_stream = make_chat_views(module='ISE', orchestrator=ise_orchestrator)
