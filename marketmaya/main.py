"""Market Maya Facade — one stable entry point per module.

Pattern: Facade (structural) + Singleton (creational).

Each strategy module instantiates MarketMaya once with its own config:
    market_maya = MarketMaya(module="USB", save_url=Config.CREATE_STRATEGY_URL)

All shared operations (list, delete, modify, rename, balance, record) are
inherited for free — only save_url and module label differ per module.

Future migration path:
    USB  → done (Unified_Strategy_Builder/services/market_maya.py)
    ISE  → from marketmaya import MarketMaya; market_maya = MarketMaya(module="ISE", save_url=Config.ISE_SAVE_URL)
    ISB  → same pattern
    RES  → same pattern
    MLH  → same pattern
"""

from marketmaya.auth import Auth
from marketmaya.operations import Operations


class MarketMaya:
    """Facade: hides Auth + Operations behind a clean, stable per-module API."""

    def __init__(self, module: str, save_url: str, log_prefix: str = "MarketMaya"):
        self._module = module
        self._save_url = save_url
        self._log_prefix = log_prefix
        self._ops = Operations()

    # ── Module-specific ───────────────────────────────────────────────────────

    def save_strategy(self, payload: dict) -> dict:
        return self._ops.save_strategy(self._save_url, payload, self._module, self._log_prefix)

    # ── Shared (delegates to Operations static methods) ───────────────────────

    def get_my_strategies(self, search: str = "", take: int = 50) -> dict:
        return Operations.get_my_strategies(search, take)

    def get_strategies(self, search: str = "", skip: int = 0, take: int = 50,
                       trading_type: str = "All", strategy_master_ids=None) -> dict:
        return Operations.get_strategies(search, skip, take, trading_type, strategy_master_ids)

    def delete_strategy(self, strategy_id: str = "", strategy_name: str = "") -> dict:
        return Operations.delete_strategy(strategy_id, strategy_name)

    def get_strategy_record(self, strategy_id: str = "", strategy_name: str = "") -> dict:
        return Operations.get_strategy_record(strategy_id, strategy_name)

    def modify_strategy(self, payload: dict) -> dict:
        return Operations.modify_strategy(payload)

    def rename_strategy(self, strategy_id: str = "", strategy_name: str = "", new_name: str = "") -> dict:
        return Operations.rename_strategy(strategy_id, strategy_name, new_name)

    def get_balance(self) -> dict:
        return Operations.get_balance()
