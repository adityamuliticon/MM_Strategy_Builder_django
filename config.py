import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
    RUNWARE_MODEL_ID = os.getenv("RUNWARE_MODEL_ID")
    MARKET_MAYA_BEARER_TOKEN = os.getenv("MARKET_MAYA_BEARER_TOKEN")
    
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

    # Backtest (ISE only)
    BACKTEST_OPTIONS_URL = "https://api.marketmaya.com/api/subscription/getBacktestOptions"
    DEDUCT_BACKTEST_POINTS_URL = "https://api.marketmaya.com/api/subscription/deductBacktestPoints"
    GET_BACKTEST_RESULT_URL = "https://webapi.marketmaya.com/api/mainStrategy/getBackTestResult"
    GET_STRATEGY_DETAIL_URL = "https://webapi.marketmaya.com/api/mainStrategy/getClientMyStrategyDetail"
    GET_DAY_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getDayTradeHistory"
    GET_MONTH_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getMonthTradeHistory"
    GET_YEAR_TRADE_HISTORY_URL = "https://webapi.marketmaya.com/api/mainStrategy/getYearTradeHistory"
    
    # RAG Settings
    DOCS_PATH = "docs"
    VECTOR_STORE_PATH = "Unified_Strategy_Builder/rag/store/faiss_index"

    # Token pricing (update these to match your Runware model's actual rates)
    # Cost per 1 million tokens in USD
    COST_PER_1M_INPUT_TOKENS_USD  = float(os.getenv("COST_PER_1M_INPUT_USD",  "0.25"))
    COST_PER_1M_OUTPUT_TOKENS_USD = float(os.getenv("COST_PER_1M_OUTPUT_USD", "1.50"))
    # USD → INR conversion rate
    USD_TO_INR_RATE = float(os.getenv("USD_TO_INR_RATE", "95.71"))

    # Django
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = True
