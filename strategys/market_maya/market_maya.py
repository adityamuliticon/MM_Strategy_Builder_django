from datetime import datetime
from marketmaya import MarketMaya
from config import Config
from services.base_market_maya import BaseMarketMayaService

# ── USB ───────────────────────────────────────────────────────────────────────
market_maya = MarketMaya(
    module="USB",
    save_url=Config.CREATE_STRATEGY_URL,
)

# ── MLH ───────────────────────────────────────────────────────────────────────
class MLHMarketMayaService(BaseMarketMayaService):
    _module_name = 'MLH'
    _log_prefix = 'MLH MarketMaya'

    def _get_url(self):
        return Config.CREATE_MULTI_LEG_HEDGER_URL

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy_type": "multi_leg_hedger",
            "strategy_name": payload.get("strategyName", ""),
            "payload": payload,
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
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


mlh_market_maya = MLHMarketMayaService()

# ── RES ───────────────────────────────────────────────────────────────────────
class RESMarketMayaService(BaseMarketMayaService):
    _module_name = 'RES'
    _log_prefix = 'RES MarketMaya'

    def _get_url(self):
        return Config.CREATE_SCALPING_STRATEGY_URL

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "rapid_execution_scalper",
            "strategy_name": payload.get("strategy_name", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload,
        }


res_market_maya = RESMarketMayaService()

# ── ISB ───────────────────────────────────────────────────────────────────────
class ISBMarketMayaService(BaseMarketMayaService):
    _module_name = 'ISB'
    _log_prefix = 'ISB MarketMaya'

    def _get_url(self):
        return Config.MODIFY_STRATEGY_URL

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "inbound_signal_bridge",
            "strategy_name": payload.get("strategy_name", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload,
        }


isb_market_maya = ISBMarketMayaService()

# ── ISE ───────────────────────────────────────────────────────────────────────
class ISEMarketMayaService(BaseMarketMayaService):
    _module_name = 'ISE'
    _log_prefix = 'ISE MarketMaya'

    def _get_url(self):
        return f"{Config.MARKET_MAYA_BASE_URL}/mainStrategy/createIndicatorStrategy"

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "indicator_signal_engine",
            "strategy_name": payload.get("strategyName", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload,
        }


ise_market_maya = ISEMarketMayaService()
