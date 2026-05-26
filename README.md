# Market Maya Strategy Builder

An AI-powered trading strategy builder for the **Market Maya API**. Three isolated strategy modules — each with its own AI orchestrator, RAG pipeline, and MCP tool layer — let traders describe strategies in plain English and deploy them directly to Market Maya with a single confirmation.

---

## Modules

| Module | URL | Description |
|--------|-----|-------------|
| **Unified Strategy Builder (USB)** | `/` | Multi-leg options strategies — straddles, strangles, hedges, complex payoffs |
| **Indicator Signal Engine (ISE)** | `/indicator/` | Indicator-driven strategies — SuperTrend, MA CrossOver, RSI, MACD, Bollinger Bands, candlestick patterns |
| **Inbound Signal Bridge (ISB)** | `/bridge/` | Webhook/TradingView signal execution — configure legs once, fire all on every inbound signal |

Each module is fully isolated: separate Django app, FAISS vector store, session memory, and Market Maya service instance.

---

## Tech Stack

- **Backend**: Django (Python)
- **AI**: Runware API (OpenAI-compatible)
- **Vector DB**: FAISS + HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- **Protocol**: Model Context Protocol (MCP)
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism), JavaScript

---

## Project Structure

```
MM_Strategy_Builder_django/
├── manage.py
├── requirements.txt
├── config.py                      # API keys, paths, Django settings
│
├── mm_project/                    # Django project config
│   ├── settings.py
│   └── urls.py
│
├── Unified_Strategy_Builder/      # Unified Strategy Builder (USB)
│   ├── views.py / urls.py
│   ├── core/orchestrator.py       # AI loop + system prompt
│   ├── mcp/handlers.py, tools.py  # Tool routing + deployment
│   ├── rag/ingest.py, retriever.py, store/
│   └── services/generator.py, market_maya.py, validator.py
│
├── indicator_engine/              # Indicator Signal Engine (ISE)
│   └── (same structure)
│
├── inbound_signal_bridge/         # Inbound Signal Bridge (ISB)
│   └── (same structure)
│
├── static/css/ + static/js/       # Shared UI assets
├── templates/                     # HTML templates per module
│
├── docs/                          # Reference material
│   ├── MM - Unified Strategy Builder Plugin.md
│   ├── MM - Indicator Signal Engine.md
│   ├── MM - Inbound Signal Bridge.md
│   ├── swagger.json
│   └── api/                       # Sample payloads
│
├── tests/                         # Test infrastructure
│   ├── run_usb_tests.py
│   ├── run_ise_tests.py
│   ├── run_isb_tests.py
│   ├── cases/                     # 20-prompt test specs per module
│   └── reports/                   # Saved test run outputs
│
└── logs/
    └── deployed_strategies.log    # All deployments across modules
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Market Maya Bearer Token
- Runware API Key

### 2. Install

```bash
git clone <repo-url>
cd MM_Strategy_Builder_django

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

Create a `.env` file in the project root:

```env
RUNWARE_API_KEY=your_runware_key
RUNWARE_MODEL_ID=your_model_id
MARKET_MAYA_BEARER_TOKEN=your_market_maya_token
SECRET_KEY=your_django_secret
```

### 4. Build RAG Indexes

Run once per module to build the FAISS vector stores from the documentation:

```bash
# Unified Strategy Builder
python -c "from Unified_Strategy_Builder.rag.ingest import ingest_docs; ingest_docs()"

# Indicator Signal Engine
python -c "from indicator_engine.rag.ingest import ingest_docs; ingest_docs()"

# Inbound Signal Bridge
python -c "from inbound_signal_bridge.rag.ingest import ingest; ingest()"
```

### 5. Run

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000` — navigate between modules from the sidebar.

---

## How It Works

1. **Input** — User describes a strategy in natural language (e.g., *"BankNifty ATM straddle, 1 lot each leg, MIS, combined SL ₹5000"*)
2. **RAG** — System retrieves relevant parameter rules from the module's FAISS index
3. **Preview** — AI generates structured Markdown tables matching the Market Maya UI tabs
4. **Confirmation** — User reviews and approves
5. **Deployment** — `generator.py` builds the production payload, `market_maya.py` POSTs to the API

All deployments are logged to `logs/deployed_strategies.log` with full payload and API response.

---

## Running Tests

Each module has 20 automated test prompts covering every parameter. Run against a live server:

```bash
# Start server first
python manage.py runserver 0.0.0.0:8000

# Run tests (from project root)
python tests/run_usb_tests.py
python tests/run_ise_tests.py
python tests/run_isb_tests.py
```

Reports are saved to `tests/reports/`.

---

## License

Internal Use Only. Confidential and Proprietary.

---

*Built for Traders by Aditya & Antigravity AI.*
