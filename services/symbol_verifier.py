"""
Symbol verification against Market Maya APIs.

Called automatically before every strategy save to catch:
  1. Wrong symbol name  — e.g. TATAMOTER vs TATAMOTORS
  2. Invalid ATM offset — e.g. atm=131 when valid values are 100, 150, 200...

Three APIs:
  getSymbolProperty  — does this exact exchange+segment+symbol exist?
  getSPSymbolCombo   — if not, what symbols ARE valid for this exchange+segment?
  getDynamicATM      — what ATM offset values are available for this symbol?
"""

import difflib

import requests

from marketmaya.auth import Auth
from marketmaya.config import Config


# ── Raw API callers ────────────────────────────────────────────────────────────

def _post(url: str, payload: dict) -> tuple:
    """POST with auth headers. Returns (data, error_str)."""
    try:
        resp = requests.post(url, json=payload, headers=Auth.headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"HTTP {resp.status_code}"
    except Exception as e:
        return None, str(e)


def check_symbol(exchange: str, segment: str, symbol: str) -> dict:
    """
    Check if exchange+segment+symbol combo is tradable.
    Returns {"exist": bool|None, "property": dict|None, "error": str|None}
    exist=None means the API call failed — caller should skip, not block.
    """
    data, err = _post(
        Config.SYMBOL_PROPERTY_URL,
        {"exchange": exchange, "segment": segment, "symbol": symbol.upper()},
    )
    if err:
        print(f"[SymbolVerifier] check_symbol error for {symbol}: {err}")
        return {"exist": None, "property": None, "error": err}
    return {"exist": data.get("exist", False), "property": data.get("property"), "error": None}


def get_symbols_for_combo(exchange: str, segment: str) -> list:
    """Return all valid symbol names for the given exchange+segment pair."""
    data, err = _post(Config.SYMBOL_COMBO_URL, {"exchange": exchange, "segment": segment})
    if err or not isinstance(data, list):
        return []
    return data


def get_atm_prices(exchange: str, segment: str, symbol: str) -> list:
    """
    Return the list of valid ATM offset values for this symbol.
    e.g. [200, 150, 100, 50, 0, -50, -100, -150, -200]
    Each value is an integer offset from current ATM. Only these exact values
    are accepted by Market Maya — any other value is rejected.
    """
    data, err = _post(
        Config.SYMBOL_ATM_URL,
        {"exchange": exchange, "segment": segment, "symbol": symbol.upper()},
    )
    if err or not isinstance(data, list):
        return []
    return [int(v) for v in data]


# ── Fuzzy symbol matching ──────────────────────────────────────────────────────

def _find_close_matches(user_symbol: str, valid_symbols: list, n: int = 5) -> list:
    """
    Find valid symbols closest to the user's (possibly misspelled) input.
    Three-tier fallback:
      1. difflib similarity — catches letter swaps, missing chars (TATAMOTER → TATAMOTORS)
      2. user input is a substring of a valid symbol (TATA → TATAMOTORS, TATASTEEL…)
      3. valid symbol starts with the first 4 chars of user input
    """
    needle = user_symbol.upper()
    close = difflib.get_close_matches(needle, valid_symbols, n=n, cutoff=0.6)
    if close:
        return close
    sub = [s for s in valid_symbols if needle in s]
    if sub:
        return sub[:n]
    prefix = [s for s in valid_symbols if s.startswith(needle[:4])]
    return prefix[:n]


# ── Error message builders ─────────────────────────────────────────────────────

def _symbol_error_msg(symbol: str, exchange: str, segment: str, alternatives: list) -> str:
    if not alternatives:
        return (
            f"Symbol '{symbol}' does not exist in {exchange}/{segment}. "
            "Please verify the symbol name."
        )
    if len(alternatives) == 1:
        ratio = difflib.SequenceMatcher(None, symbol.upper(), alternatives[0]).ratio()
        if ratio > 0.8:
            return (
                f"Symbol '{symbol}' not found. "
                f"Did you mean **{alternatives[0]}**? "
                "Please confirm or correct the symbol name."
            )
    alt_list = ", ".join(alternatives)
    return (
        f"Symbol '{symbol}' does not exist in {exchange}/{segment}. "
        f"Similar valid symbols: {alt_list}. "
        "Please use the exact symbol name."
    )


def _atm_error_msg(label: str, atm_value: int, symbol: str, exchange: str, segment: str, valid_atm: list) -> str:
    nearest = sorted(valid_atm, key=lambda x: abs(x - atm_value))[:5]
    nearest_str = ", ".join(str(v) for v in sorted(nearest))
    return (
        f"{label}: ATM offset **{atm_value}** is not valid for {symbol} ({exchange}/{segment}). "
        f"Nearest valid ATM offsets: {nearest_str}. "
        "Please use one of these values."
    )


# ── Main verification entry point ──────────────────────────────────────────────

def verify_strategy_symbols(symbol_specs: list) -> dict:
    """
    Verify all symbol specs before saving a strategy.

    Args:
        symbol_specs: list of dicts, each with:
            exchange  (str)
            segment   (str)
            symbol    (str)
            atm       (int|None) — ATM offset used in this leg; None = no ATM check
            leg_index (int|str, optional) — for error messages

    Each unique (exchange, segment, symbol) combo is resolved once (cached).
    ATM validation is done per-leg against the retrieved ATM list.

    Returns on success:
        {
            "valid": True,
            "symbols_info": [
                {
                    "symbol": "RELIANCE",
                    "exchange": "NFO",
                    "segment": "OPT",
                    "lot_size": 250,
                    "strike_price_gap": 20,
                    "valid_atm_offsets": [200, 150, 100, 50, 0, -50, -100, -150, -200]
                },
                ...  (one entry per unique symbol, de-duplicated)
            ]
        }

    Returns on failure:
        {
            "valid": False,
            "error": "Symbol verification failed:\n• ...\n• ...",
            "details": [...]
        }
    """
    errors = []
    symbols_info = []
    # Cache keyed on (exchange, segment, symbol) — avoids repeat API calls for
    # the same symbol across multiple legs (e.g. 4 RELIANCE legs → 1 API call)
    _cache = {}

    for spec in symbol_specs:
        exchange  = (spec.get("exchange") or "").strip().upper()
        segment   = (spec.get("segment") or "").strip().upper()
        symbol    = (spec.get("symbol") or "").strip().upper()
        atm_value = spec.get("atm")        # None if ATM check not needed for this leg
        leg_index = spec.get("leg_index", "")
        label     = f"Leg {leg_index}" if leg_index != "" else "symbol"

        if not symbol:
            continue

        cache_key = (exchange, segment, symbol)

        # ── Resolve symbol (once per unique combo) ─────────────────────────
        if cache_key not in _cache:
            result = check_symbol(exchange, segment, symbol)

            if result["error"]:
                # Network error — skip silently, do not block save
                _cache[cache_key] = None
            elif result["exist"]:
                atm_prices = get_atm_prices(exchange, segment, symbol)
                _cache[cache_key] = {
                    "exist":      True,
                    "property":   result["property"] or {},
                    "atm_prices": atm_prices,
                }
            else:
                valid_symbols = get_symbols_for_combo(exchange, segment)
                _cache[cache_key] = {
                    "exist":        False,
                    "alternatives": _find_close_matches(symbol, valid_symbols),
                }

        cached = _cache[cache_key]

        if cached is None:
            # API unreachable for this symbol — skip
            continue

        # ── Symbol existence check ─────────────────────────────────────────
        if not cached["exist"]:
            errors.append({
                "symbol": symbol, "exchange": exchange, "segment": segment,
                "leg_label": label,
                "message": _symbol_error_msg(symbol, exchange, segment, cached["alternatives"]),
            })
            continue   # no point checking ATM if symbol doesn't exist

        # ── ATM offset validation ──────────────────────────────────────────
        if atm_value is not None:
            atm_prices = cached["atm_prices"]
            if atm_prices and atm_value not in atm_prices:
                errors.append({
                    "symbol": symbol, "exchange": exchange, "segment": segment,
                    "leg_label": label,
                    "message": _atm_error_msg(label, atm_value, symbol, exchange, segment, atm_prices),
                })

        # ── Record symbol info (once per unique symbol) ────────────────────
        if not any(
            s["symbol"] == symbol and s["exchange"] == exchange and s["segment"] == segment
            for s in symbols_info
        ):
            prop = cached["property"]
            atm_prices = cached["atm_prices"]
            symbols_info.append({
                "symbol":            symbol,
                "exchange":          exchange,
                "segment":           segment,
                "lot_size":          prop.get("lot_size"),
                "strike_price_gap":  prop.get("strike_price_gap"),
                "valid_atm_offsets": atm_prices,
            })

    if errors:
        lines = [e["message"] for e in errors]
        return {
            "valid":   False,
            "error":   "Symbol verification failed:\n" + "\n".join(f"• {m}" for m in lines),
            "details": errors,
        }

    return {"valid": True, "symbols_info": symbols_info}
