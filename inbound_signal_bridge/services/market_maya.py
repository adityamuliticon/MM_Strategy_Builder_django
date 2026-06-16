"""ISB Market Maya API client — posts inbound signal bridge strategies to createCustomTradeStrategy and logs results."""

from datetime import datetime
from config import Config
from services.base_market_maya import BaseMarketMayaService


class ISBMarketMayaService(BaseMarketMayaService):
    _module_name = 'ISB'
    _log_prefix = 'ISB MarketMaya'

    def _get_url(self):
        # ISB uses createCustomTradeStrategy for both create and modify operations
        return Config.MODIFY_STRATEGY_URL

    def _build_log_entry(self, payload, api_status, api_code, api_response):
        return {
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "inbound_signal_bridge",
            "strategy_name": payload.get("strategy_name", "Unknown"),
            "api_status": api_status,
            "api_code": api_code,
            "api_response": api_response,
            "payload": payload
        }


# Singleton instance
isb_market_maya = ISBMarketMayaService()
