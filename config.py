"""Central configuration — all API keys, endpoint URLs, and cost-tracking constants for the entire project."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API Keys
    RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
    RUNWARE_MODEL_ID = os.getenv("RUNWARE_MODEL_ID")
    MARKET_MAYA_BEARER_TOKEN = os.getenv("MARKET_MAYA_BEARER_TOKEN")  # fallback if auto-login fails

    # Market Maya login credentials for auto token refresh
    MARKET_MAYA_EMAIL    = os.getenv("MARKET_MAYA_EMAIL", "")
    MARKET_MAYA_PASSWORD = os.getenv("MARKET_MAYA_PASSWORD", "")
    MM_LOGIN_URL = "https://webapi.marketmaya.com/api/auth/clientLogin"

    # Fernet key for encrypting stored user passwords — generate with:
    # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    MM_ENCRYPTION_KEY = os.getenv("MM_ENCRYPTION_KEY", "")
    
    # Runware usually uses OpenAI-compatible endpoints
    RUNWARE_BASE_URL = "https://api.runware.ai/v1" # Adjust if different
    
    # Market Maya API Endpoints
    MARKET_MAYA_BASE_URL = "https://webapi.marketmaya.com/api"
    CREATE_STRATEGY_URL = f"{MARKET_MAYA_BASE_URL}/mainStrategy/CreateUnifiedStrategy"
    GET_STRATEGIES_URL = "https://api.marketmaya.com/api/V3/mainStrategy/getClientMyStrategy"
    DELETE_STRATEGY_URL = "https://api.marketmaya.com/api/mainStrategy/delete"
    GET_STRATEGY_RECORD_URL = "https://webapi.marketmaya.com/api/mainStrategy/getCustomTradeRecord"
    MODIFY_STRATEGY_URL = "https://api.marketmaya.com/api/mainStrategy/createCustomTradeStrategy"
    RENAME_STRATEGY_URL = "https://api.marketmaya.com/api/mainStrategy/updateStrategyName"
    GET_BALANCE_URL = "https://api.marketmaya.com/api/client/v2/getPointBalance"
    CREATE_SCALPING_STRATEGY_URL = "https://api.marketmaya.com/api/mainStrategy/createScalpingStrategy"
    CREATE_MULTI_LEG_HEDGER_URL = "https://api.marketmaya.com/api/mainStrategy/CreateMultiLegCallPutStrategy"

    # Deploy / Undeploy
    GET_CHARGES_URL = "https://api.marketmaya.com/api/transaction/getCharges"
    DEPLOY_STRATEGY_URL = "https://webapi.marketmaya.com/api/mainStrategy/deploy"
    CHECK_PENDING_PAYMENTS_URL = "https://api.marketmaya.com/api/mainStrategy/checkPendingPayments"
    UNDEPLOY_STRATEGY_URL = "https://webapi.marketmaya.com/api/mainStrategy/undeploy"

    # Backtest (ISE and MIH and RES)
    BACKTEST_OPTIONS_URL = "https://api.marketmaya.com/api/subscription/getBacktestOptions"
    DEDUCT_BACKTEST_POINTS_URL = "https://api.marketmaya.com/api/subscription/deductBacktestPoints"
    GET_BACKTEST_RESULT_URL = "https://webapi.marketmaya.com/api/mainStrategy/getBackTestResult"
    GET_STRATEGY_DETAIL_URL = "https://webapi.marketmaya.com/api/mainStrategy/getClientMyStrategyDetail"
    GET_DAY_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getDayTradeHistory"
    GET_MONTH_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getMonthTradeHistory"
    GET_YEAR_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getYearTradeHistory"
    
    # RAG Settings
    DOCS_PATH = "docs"
    VECTOR_STORE_PATH = "utils/rag/store/faiss_index"

    # Token pricing (update these to match your Runware model's actual rates)
    # Cost per 1 million tokens in USD
    COST_PER_1M_INPUT_TOKENS_USD  = float(os.getenv("COST_PER_1M_INPUT_USD",  "0.25"))
    COST_PER_1M_OUTPUT_TOKENS_USD = float(os.getenv("COST_PER_1M_OUTPUT_USD", "1.50"))
    # USD → INR conversion rate
    USD_TO_INR_RATE = float(os.getenv("USD_TO_INR_RATE", "95.71"))

    # Django — H-2: SECRET_KEY must be set; DEBUG must be explicitly enabled in .env
    _secret = os.getenv("SECRET_KEY", "")
    if not _secret:
        raise RuntimeError(
            "SECRET_KEY is not set. Add SECRET_KEY=<random-string> to your .env file. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(50))\""
        )
    SECRET_KEY = _secret
    DEBUG = os.getenv("DEBUG", "False") == "True"
