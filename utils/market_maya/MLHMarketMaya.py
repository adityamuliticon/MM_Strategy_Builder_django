"""MLH Market Maya API client — posts multi-leg hedger strategies to CreateMultiLegCallPutStrategy and logs results."""

from datetime import datetime
from config import Config
from services.base_market_maya import BaseMarketMayaService


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
