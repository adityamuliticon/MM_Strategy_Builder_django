"""Cross-plugin views: strategy counts badge API and other project-level endpoints."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from services.market_maya_shared import get_strategies

STRATEGY_TYPE_IDS = {
    "usb": "7D0enBHWMRaf4ebeKaB0$OOMQaC0$aC0$",
    "ise": "QFwz7gYjmmabUT8SBvZQGgaC0$aC0$",
    "isb": "XBZs7OE0aMivKaB0$aA0$Wej3PcwaC0$aC0$",
    "res": "YioJhK5IqBULe8fPLMnXaAaC0$aC0$",
    "mlh": "RF8IGNzSfYMaB0$ENiAa4FpGwaC0$aC0$",
}


def _fetch_count(key, type_id):
    result = get_strategies(take=1, strategy_master_ids=[type_id])
    if result.get("status") == "success":
        return key, result["total"]
    return key, None


def strategy_counts_view(request):
    counts = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_count, k, v): k for k, v in STRATEGY_TYPE_IDS.items()}
        for future in as_completed(futures):
            key, count = future.result()
            counts[key] = count
    return JsonResponse(counts)
