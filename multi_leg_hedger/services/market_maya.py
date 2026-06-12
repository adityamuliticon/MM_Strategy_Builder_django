"""MLH Market Maya API client — posts multi-leg hedger strategies to CreateMultiLegCallPutStrategy and logs results."""

import json
import requests
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)
LOG_FILE = "logs/saved_strategies.log"


class MLHMarketMayaService:
    def deploy(self, payload):
        from services.token_service import get_auth_header
        url = Config.CREATE_MULTI_LEG_HEDGER_URL
        headers = {
            "Authorization": get_auth_header(),
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            status = "success" if resp.status_code == 200 else "error"
            try:
                api_resp = resp.json()
            except Exception:
                api_resp = resp.text
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "strategy_type": "multi_leg_hedger",
                "strategy_name": payload.get("strategyName", ""),
                "payload": payload,
                "api_status": status,
                "api_code": resp.status_code,
                "api_response": api_resp,
            }
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            return {"status": status, "code": resp.status_code, "response": api_resp}
        except Exception as e:
            logger.error(f"MLH deploy error: {e}")
            return {"status": "error", "code": 0, "response": str(e)}


mlh_market_maya = MLHMarketMayaService()
