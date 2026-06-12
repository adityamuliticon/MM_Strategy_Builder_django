"""MLH Market Maya API client — posts multi-leg hedger strategies to CreateMultiLegCallPutStrategy and logs results."""

import time
import json
import requests
import logging
from datetime import datetime
from config import Config
from services.session_context import log_api_call

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

        api_status = None
        api_code = None
        api_resp = None
        start = time.time()

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            duration_ms = (time.time() - start) * 1000
            api_code = resp.status_code
            api_status = "success" if resp.status_code == 200 else "error"
            try:
                api_resp = resp.json()
            except Exception:
                api_resp = resp.text
            result = {"status": api_status, "code": api_code, "response": api_resp}

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            api_status = "connection_error"
            api_resp = str(e)
            logger.error(f"MLH deploy error: {e}")
            result = {"status": "error", "code": 0, "response": api_resp}

        log_api_call(
            module='MLH',
            call_type='deploy',
            endpoint=url,
            request_payload=payload,
            response_status=api_code,
            response_body=api_resp,
            duration_ms=duration_ms,
            status=api_status,
        )

        try:
            with open(LOG_FILE, "a") as f:
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "strategy_type": "multi_leg_hedger",
                    "strategy_name": payload.get("strategyName", ""),
                    "payload": payload,
                    "api_status": api_status,
                    "api_code": api_code,
                    "api_response": api_resp,
                }
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"File logging error: {e}")

        return result


mlh_market_maya = MLHMarketMayaService()
