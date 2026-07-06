from datetime import datetime
from marketmaya.auth import Auth
from marketmaya.operations import Operations
from marketmaya.config import Config
from services.base_market_maya import BaseMarketMayaService


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


class GenericMarketMayaService(BaseMarketMayaService):
    """Single reusable service for MLH, RES, ISB, ISE — only constructor args differ."""

    def __init__(self, module_name: str, log_prefix: str, url: str,
                 strategy_type: str, name_key: str, use_utc: bool = False):
        self._module_name = module_name
        self._log_prefix = log_prefix
        self._url = url
        self._strategy_type = strategy_type
        self._name_key = name_key
        self._use_utc = use_utc

    def _get_url(self):
        return self._url

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        ts = datetime.utcnow().isoformat() if self._use_utc else datetime.now().isoformat()
        return {
            "timestamp": ts,
            "strategy_type": self._strategy_type,
            "strategy_name": payload.get(self._name_key, "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload,
        }

    def deploy(self, payload):
        result = self.save_strategy(payload)
        if result.get("status") == "success":
            return {"status": "success", "code": 200, "response": result.get("data")}
        return {
            "status": result.get("status", "error"),
            "code": result.get("code", 0),
            "response": result.get("message", ""),
        }


# ── Module instances (imported by utils/mcp/tools.py) ────────────────────────

market_maya = MarketMaya(
    module="USB",
    save_url=Config.CREATE_STRATEGY_URL,
)

mlh_market_maya = GenericMarketMayaService(
    module_name="MLH",
    log_prefix="MLH MarketMaya",
    url=Config.CREATE_MULTI_LEG_HEDGER_URL,
    strategy_type="multi_leg_hedger",
    name_key="strategyName",
    use_utc=True,
)

res_market_maya = GenericMarketMayaService(
    module_name="RES",
    log_prefix="RES MarketMaya",
    url=Config.CREATE_SCALPING_STRATEGY_URL,
    strategy_type="rapid_execution_scalper",
    name_key="strategy_name",
)

isb_market_maya = GenericMarketMayaService(
    module_name="ISB",
    log_prefix="ISB MarketMaya",
    url=Config.MODIFY_STRATEGY_URL,
    strategy_type="inbound_signal_bridge",
    name_key="strategy_name",
)

ise_market_maya = GenericMarketMayaService(
    module_name="ISE",
    log_prefix="ISE MarketMaya",
    url=f"{Config.MARKET_MAYA_BASE_URL}/mainStrategy/createIndicatorStrategy",
    strategy_type="indicator_signal_engine",
    name_key="strategyName",
)
