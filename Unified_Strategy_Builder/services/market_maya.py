"""USB Market Maya API client — posts strategies to the CreateUnifiedStrategy endpoint and logs results."""

from datetime import datetime
from config import Config
from services.base_market_maya import BaseMarketMayaService


class MarketMayaService(BaseMarketMayaService):
    _module_name = 'USB'
    _log_prefix = 'MarketMaya'

    def _get_url(self):
        return Config.CREATE_STRATEGY_URL

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": payload.get("strategyName", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload
        }


# Singleton instance
market_maya = MarketMayaService()
