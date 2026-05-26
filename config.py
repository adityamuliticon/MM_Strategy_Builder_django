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
    
    # RAG Settings
    DOCS_PATH = "docs"
    VECTOR_STORE_PATH = "chat/rag/store/faiss_index"

    # Django
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = True
