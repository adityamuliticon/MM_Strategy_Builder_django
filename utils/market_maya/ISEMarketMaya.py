"""ISE Market Maya API client — posts indicator strategies to createIndicatorStrategy and logs results."""

from datetime import datetime
from config import Config
from services.base_market_maya import BaseMarketMayaService


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
            "payload": payload
        }


# Singleton instance
ise_market_maya = ISEMarketMayaService()
