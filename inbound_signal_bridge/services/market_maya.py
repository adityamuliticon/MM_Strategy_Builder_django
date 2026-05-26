import requests
import json
from config import Config


class ISBMarketMayaService:
    def __init__(self):
        self.token = Config.MARKET_MAYA_BEARER_TOKEN
        if self.token and not self.token.startswith("Bearer "):
            self.token = f"Bearer {self.token}"
        self.url = "https://api.marketmaya.com/api/mainStrategy/createCustomTradeStrategy"

    def deploy_strategy(self, payload):
        from datetime import datetime

        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        api_status = None
        api_code = None
        api_response = None

        try:
            response = requests.post(self.url, json=payload, headers=headers, timeout=30)
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
            api_status = "connection_error"
            api_response = str(e)
            print(f"[ISB MarketMaya] Connection error: {e}")
            result = {"status": "error", "message": api_response}

        try:
            with open("logs/deployed_strategies.log", "a") as f:
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


isb_market_maya = ISBMarketMayaService()
