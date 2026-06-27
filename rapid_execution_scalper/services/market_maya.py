"""RES Market Maya API client — posts scalping strategies to createScalpingStrategy and logs results."""

from datetime import datetime
from config import Config
from services.base_import BaseMarketMayaService


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
