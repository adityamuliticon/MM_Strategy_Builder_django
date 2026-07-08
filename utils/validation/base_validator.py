"""Base class for all strategy validators."""


class BaseValidator:
    VALID_EXCHANGES = {"NSE", "NFO", "BFO", "BSE", "MCX", "CDS"}
    VALID_SEGMENTS  = {"FUT", "OPT", "EQ"}
    VALID_CONTRACTS = {"NEAR", "NEXT", "FAR"}
    VALID_EXPIRIES  = {"MONTHLY", "WEEKLY"}
