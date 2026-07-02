"""Cross-plugin views: strategy counts badge API and other project-level endpoints."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from django.http import JsonResponse
from marketmaya.config import Config
from marketmaya.operations import Operations

get_strategies = Operations.get_strategies
STRATEGY_TYPE_IDS = Config.STRATEGY_TYPE_IDS


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
