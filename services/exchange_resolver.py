"""
Exchange/Segment resolver for Market Maya payloads.

Implements the MM Underlying Symbol & Exchange/Segment Selection rules
(9-rule precedence — first match wins):

  1. Non-equity conflict (e.g. NIFTY on BSE)       → raise ValueError, ask user
  2. Equity & equity derivatives                    → always NSE / NFO (Rule 11, auto-correct)
  3. Explicit exchange given by user (if valid)     → honour it, selects family
  4. Symbol's native family (from instrument master)→ MCX / CDS / NSE-only / BSE-only
  5. Asset-class keyword in segment                 → EQ → NSE; INDEX → NSE or BSE
  6. Default (symbol only, no asset class)          → FUT on F&O exchange (NFO fallback)

Segment codes accepted by Market Maya:
  Underlying : EQ | INDEX | FUT        (OPT is NEVER valid for an underlying)
  Leg        : EQ | FUT | OPT          (INDEX is never valid for a leg)

"Stock" / "STOCK" is NOT a valid segment — normalise to EQ.
"""

# ─────────────────────────────── symbol sets ──────────────────────────────────

NSE_ONLY = frozenset({
    "NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY",
})

BSE_ONLY = frozenset({
    "SENSEX", "BANKEX",
})

MCX_SET = frozenset({
    "CRUDEOIL", "CRUDEOILM",
    "GOLD", "GOLDM", "GOLDPETAL", "GOLDGUINEA",
    "SILVER", "SILVERM", "SILVERMIC",
    "NATURALGAS", "NATGASMINI",
    "COPPER",
    "ZINC", "ZINCMINI",
    "LEAD", "LEADMINI",
    "ALUMINIUM", "ALUMINIMINI",
    "NICKEL", "NICKELMINI",
    "CRUDEOIL1", "COTTON", "KAPAS",
    "MENTHAOIL", "CARDAMOM", "PEPPER",
    "CASTORSEED", "COTTONSEED", "COTTONSEEDOILCAKE",
})

CDS_SET = frozenset({
    "USDINR", "EURINR", "GBPINR", "JPYINR",
    "EURUSD", "GBPUSD", "USDJPY",
    "AUDINR", "CHFINR", "CADINR",
})

# ─────────────────────────────── exchange maps ────────────────────────────────

# Rule 11: equity derivatives are always NFO, not BFO.
# BSE / BFO are only valid for BSE-family INDEX derivatives (SENSEX, BANKEX).
_EQUITY_TO_DERIV = {
    "NSE":    "NFO",
    "NSE-EQ": "NFO",
    "BSE":    "NFO",   # equity hard-rule — BSE equity F&O → NFO
    "BSE-EQ": "NFO",
    "BFO":    "NFO",   # equity hard-rule — BFO equity options → NFO
    "NFO":    "NFO",
}

_CANONICAL = {
    "NSE-EQ": "NSE",
    "NSE-FO": "NFO",
    "BSE-EQ": "BSE",
    "BSE-FO": "BFO",
    "NSEEQ":  "NSE",
    "BSEEQ":  "BSE",
    "NFO": "NFO",
    "BFO": "BFO",
    "MCX": "MCX",
    "CDS": "CDS",
    "NSE": "NSE",
    "BSE": "BSE",
}


def _canonicalize(exchange: str) -> str:
    return _CANONICAL.get(exchange.upper(), exchange.upper())


def _norm_seg_underlying(seg: str) -> str:
    """Normalise a raw segment string for an UNDERLYING resolution."""
    s = seg.upper().strip()
    if s in ("STOCK", "EQUITY", "CASH"):
        return "EQ"
    if s in ("EQ", "INDEX", "FUT", "OPT"):
        return s
    return "FUT"   # unknown → default to futures


def _norm_seg_leg(seg: str) -> str:
    """Normalise a raw segment string for a LEG resolution.
    INDEX is not valid for legs — converted to FUT.
    """
    s = seg.upper().strip()
    if s in ("STOCK", "EQUITY", "CASH"):
        return "EQ"
    if s == "INDEX":
        return "FUT"
    if s in ("EQ", "FUT", "OPT"):
        return s
    return "FUT"


# ─────────────────────────────── public API ───────────────────────────────────

def resolve_exchange_segment(symbol: str, segment: str,
                              explicit_exchange: str = "") -> tuple[str, str]:
    """
    Resolve the correct (exchange, segment) for a strategy's UNDERLYING.

    Args:
        symbol:           Underlying symbol, e.g. "NIFTY", "RELIANCE", "CRUDEOIL"
        segment:          Segment hint from LLM: "FUT", "OPT", "EQ", "INDEX", "Stock", …
        explicit_exchange: Exchange hint from LLM (may be empty string)

    Returns:
        (exchange, segment) with Market Maya-accepted values.
        Possible returns: (NSE, EQ), (NSE, INDEX), (BSE, INDEX),
                          (NFO, FUT), (BFO, FUT), (MCX, FUT), (CDS, FUT)
        Note: OPT is never returned — underlying segment is always FUT for
        derivative-based strategies. The caller is responsible for using OPT
        in individual *leg* segments via resolve_leg_exchange().

    Raises:
        ValueError: On a non-equity conflict (Rule 1).
                    Equity conflicts are auto-corrected per Rule 11.
    """
    sym  = symbol.upper().strip()
    seg  = _norm_seg_underlying(segment)
    exch = _canonicalize(explicit_exchange) if explicit_exchange else ""

    # ── Rule 0: MCX (self-contained) ─────────────────────────────────────────
    if sym in MCX_SET:
        if exch and exch != "MCX":
            raise ValueError(
                f"Symbol {sym} belongs to MCX but exchange '{exch}' was specified. "
                "Did you mean MCX?"
            )
        return ("MCX", "FUT")   # underlying is always FUT; legs use OPT separately

    # ── Rule 0: CDS (self-contained) ─────────────────────────────────────────
    if sym in CDS_SET:
        if exch and exch != "CDS":
            raise ValueError(
                f"Symbol {sym} belongs to CDS but exchange '{exch}' was specified. "
                "Did you mean CDS?"
            )
        return ("CDS", "FUT")   # underlying is always FUT; legs use OPT separately

    # ── NSE-only index symbols ────────────────────────────────────────────────
    if sym in NSE_ONLY:
        if seg == "EQ":
            raise ValueError(
                f"{sym} is an index, not equity. "
                "Please clarify: did you mean FUT, OPT, or INDEX (spot)?"
            )
        if exch and exch not in ("NFO", "NSE"):
            raise ValueError(
                f"{sym} is NSE-family (derivatives on NFO) "
                f"but exchange '{exch}' was specified. Please clarify."
            )
        if seg == "INDEX":
            return ("NSE", "INDEX")   # spot index underlying
        return ("NFO", "FUT")         # underlying is always FUT; legs use OPT separately

    # ── BSE-only index symbols ────────────────────────────────────────────────
    if sym in BSE_ONLY:
        if seg == "EQ":
            raise ValueError(
                f"{sym} is an index, not equity. "
                "Please clarify: did you mean FUT, OPT, or INDEX (spot)?"
            )
        if exch and exch not in ("BFO", "BSE"):
            raise ValueError(
                f"{sym} is BSE-family (derivatives on BFO) "
                f"but exchange '{exch}' was specified. Please clarify."
            )
        if seg == "INDEX":
            return ("BSE", "INDEX")   # spot index underlying
        return ("BFO", "FUT")         # underlying is always FUT; legs use OPT separately

    # ── EQ segment — Rule 11: equity is always NSE (auto-correct, no error) ──
    if seg == "EQ":
        return ("NSE", "EQ")

    # ── INDEX segment on unknown symbol — NSE by default ─────────────────────
    if seg == "INDEX":
        if exch == "BSE":
            return ("BSE", "INDEX")
        return ("NSE", "INDEX")

    # ── FUT / OPT on unknown (equity) symbol ─────────────────────────────────
    # Rule 11: equity F&O is always NFO.
    # _EQUITY_TO_DERIV maps BSE/BFO → NFO so equity hard-rule is automatic.
    # Underlying segment is always FUT regardless of whether strategy uses options.
    if exch:
        mapped = _EQUITY_TO_DERIV.get(exch, exch)
        if mapped in ("BSE", "BFO"):
            mapped = "NFO"
        return (mapped or "NFO", "FUT")

    return ("NFO", "FUT")


def resolve_leg_exchange(symbol: str, segment: str,
                          exchange_hint: str) -> tuple[str, str]:
    """
    Resolve (exchange, segment) for an individual trading leg.

    Accepts either the leg's own exchange field or the parent strategy's
    resolved exchange as exchange_hint. Known symbol sets always override
    the hint.  INDEX is never valid for a leg — it is converted to FUT.

    Args:
        symbol:        Leg symbol, e.g. "BANKNIFTY", "RELIANCE", "CRUDEOIL"
        segment:       Leg segment hint: "FUT", "OPT", "EQ", "Stock", "INDEX", …
        exchange_hint: Leg's explicit exchange OR parent strategy exchange.
                       Pass "" when not available — defaults to "NFO".

    Returns:
        (exchange, segment) — segment is always EQ, FUT, or OPT.
    """
    sym  = symbol.upper().strip()
    seg  = _norm_seg_leg(segment)   # INDEX → FUT here
    exch = _canonicalize(exchange_hint) if exchange_hint else ""

    # Known symbol sets always win
    if sym in MCX_SET:
        return ("MCX", "OPT" if seg == "OPT" else "FUT")

    if sym in CDS_SET:
        return ("CDS", "OPT" if seg == "OPT" else "FUT")

    if sym in NSE_ONLY:
        return ("NFO", "OPT" if seg == "OPT" else "FUT")

    if sym in BSE_ONLY:
        return ("BFO", "OPT" if seg == "OPT" else "FUT")

    # EQ leg — Rule 11: always NSE
    if seg == "EQ":
        return ("NSE", "EQ")

    # FUT / OPT leg — apply equity hard-rule via _EQUITY_TO_DERIV
    mapped = _EQUITY_TO_DERIV.get(exch, exch) if exch else ""
    if mapped in ("BSE", "BFO"):
        mapped = "NFO"
    return (mapped or "NFO", seg)
