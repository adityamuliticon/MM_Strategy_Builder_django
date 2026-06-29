"""ISB strategy validator — checks required fields and ISB-specific leg constraints."""

from utils.validation.BaseValidator import BaseValidator

VALID_SEGMENTS = {"FUT", "OPT", "EQ"}
VALID_EXCHANGES = {"NSE", "NFO", "BFO", "BSE", "MCX", "CDS"}
VALID_CONTRACTS = {"NEAR", "NEXT", "FAR"}
VALID_EXPIRIES = {"MONTHLY", "WEEKLY"}
VALID_QTY_DIST = {"Fix", "Capital(%)", "Capital Risk(%)", "Allocation Method 1"}
VALID_PRODUCTS = {"MIS", "NRML", "CNC"}


class ISBValidator(BaseValidator):

    def validate_strategy(self, strategy_json):
        errors = []

        name = strategy_json.get("strategyName", "")
        if not name or len(name) < 3:
            errors.append("strategyName must be at least 3 characters.")
        if len(name) > 100:
            errors.append("strategyName must be at most 100 characters.")

        product = strategy_json.get("productType", "NRML")
        if product not in VALID_PRODUCTS:
            errors.append(f"productType must be one of {VALID_PRODUCTS}.")

        max_pos = strategy_json.get("maxPosition", 0)
        if not isinstance(max_pos, (int, float)) or max_pos < 0:
            errors.append("maxPosition must be 0 or a positive integer.")

        max_alloc = strategy_json.get("maxCapitalAllocation", 100)
        if not isinstance(max_alloc, (int, float)) or max_alloc < 1 or max_alloc > 100:
            errors.append("maxCapitalAllocation must be between 1 and 100.")

        exit_min = strategy_json.get("exitMinutes", 15)
        if not isinstance(exit_min, (int, float)) or exit_min < 1:
            errors.append("exitMinutes must be a positive number.")

        legs = strategy_json.get("legs", [])
        if not legs:
            errors.append("At least one symbol leg is required.")

        for i, leg in enumerate(legs, 1):
            prefix = f"Leg {i}"

            exchange = str(leg.get("exchange", "NFO")).upper()
            if exchange not in VALID_EXCHANGES:
                errors.append(f"{prefix}: exchange must be one of {VALID_EXCHANGES}.")

            segment = str(leg.get("segment", "FUT"))
            seg_norm = segment.upper()
            if seg_norm in ("STOCK", "EQ"):
                seg_norm = "EQ"
            if seg_norm not in VALID_SEGMENTS:
                errors.append(f"{prefix}: segment must be FUT, OPT, or EQ.")

            contract = str(leg.get("contract", "NEAR")).upper()
            if contract not in VALID_CONTRACTS:
                errors.append(f"{prefix}: contract must be NEAR, NEXT, or FAR.")

            expiry = str(leg.get("expiry", "MONTHLY")).upper()
            if expiry not in VALID_EXPIRIES:
                errors.append(f"{prefix}: expiry must be MONTHLY or WEEKLY.")

            if seg_norm == "OPT":
                opt_type = str(leg.get("optionType", "")).upper()
                if opt_type not in ("CE", "PE"):
                    errors.append(f"{prefix}: optionType must be CE or PE for OPT segment.")

            qty_dist = str(leg.get("qtyDistribution", "Fix"))
            if qty_dist not in VALID_QTY_DIST:
                errors.append(f"{prefix}: qtyDistribution must be one of {VALID_QTY_DIST}.")

            lot = leg.get("lot", 1)
            if not isinstance(lot, (int, float)) or lot <= 0:
                errors.append(f"{prefix}: lot must be a positive number.")

            if qty_dist == "Capital Risk(%)" and int(leg.get("sl", 0)) == 0:
                errors.append(f"{prefix}: Capital Risk(%) requires a non-zero SL value.")

        return errors


isb_validator = ISBValidator()
