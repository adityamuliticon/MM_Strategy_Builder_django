"""ISB Market Maya API client — posts inbound signal bridge strategies to createCustomTradeStrategy and logs results."""

import time
import requests
import json
from datetime import datetime
from config import Config
from services.session_context import log_api_call


class ISBMarketMayaService:
    def __init__(self):
        # ISB uses createCustomTradeStrategy for both create and modify operations
        self.url = Config.MODIFY_STRATEGY_URL

    def save_strategy(self, payload):
        from services.token_service import get_auth_header
        headers = {
            "Authorization": get_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        api_status = None
        api_code = None
        api_response = None
        start = time.time()

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
            duration_ms = (time.time() - start) * 1000
            api_code = response.status_code
            print(f"\n[ISB MarketMaya] HTTP {api_code}: {response.text[:300]}")

            if response.status_code == 200:
                api_status = "success"
                try:
                    api_response = response.json()
                except Exception:
                    api_response = response.text
                result = {"status": "success", "data": api_response}
            else:
                api_status = "error"
                api_response = response.text
                result = {"status": "error", "code": api_code, "message": api_response}

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            api_status = "connection_error"
            api_response = str(e)
            print(f"[ISB MarketMaya] Connection error: {e}")
            result = {"status": "error", "message": api_response}

        log_api_call(
            module='ISB',
            call_type='save_strategy',
            endpoint=self.url,
            request_payload=payload,
            response_status=api_code,
            response_body=api_response,
            duration_ms=duration_ms,
            status=api_status,
        )

        try:
            with open("logs/saved_strategies.log", "a") as f:
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "strategy_type": "inbound_signal_bridge",
                    "strategy_name": payload.get("strategy_name", "Unknown"),
                    "api_status": api_status,
                    "api_code": api_code,
                    "api_response": api_response,
                    "payload": payload
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

        return result


# Singleton instance
isb_market_maya = ISBMarketMayaService()
