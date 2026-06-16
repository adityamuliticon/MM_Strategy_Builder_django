"""Shared Template Method base for MarketMaya API clients (USB, ISE, RES, ISB).

Each subclass must provide:
  _module_name        — class attribute: module label for log_api_call (e.g. 'USB')
  _log_prefix         — class attribute: prefix for print statements (e.g. 'MarketMaya')
  _get_url()          — returns the full endpoint URL for this module
  _build_log_entry()  — returns the dict written to saved_strategies.log
"""

from abc import ABC, abstractmethod
import time
import requests
import json
from services.session_context import log_api_call


class BaseMarketMayaService(ABC):

    @abstractmethod
    def _get_url(self):
        ...

    @abstractmethod
    def _build_log_entry(self, payload, api_status, api_code, api_response):
        ...

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
        url = None
        start = time.time()

        try:
            url = self._get_url()
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            duration_ms = (time.time() - start) * 1000
            api_code = response.status_code
            print(f"\n[{self._log_prefix}] HTTP {api_code}: {response.text[:300]}")

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
            print(f"[{self._log_prefix}] Connection error: {e}")
            result = {"status": "error", "message": api_response}

        log_api_call(
            module=self._module_name,
            call_type='save_strategy',
            endpoint=url,
            request_payload=payload,
            response_status=api_code,
            response_body=api_response,
            duration_ms=duration_ms,
            status=api_status,
        )

        log_entry = self._build_log_entry(payload, api_status, api_code, api_response)
        try:
            with open("logs/saved_strategies.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

        return result
