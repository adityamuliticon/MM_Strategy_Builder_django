# Market Maya Strategy Builder

An AI-powered trading strategy builder for the **Market Maya API**. Five strategy plugins — each with its own AI orchestrator, RAG pipeline, and MCP tool layer — let traders describe strategies in plain English and deploy them directly to Market Maya with a single confirmation.

---

## Plugins

| Plugin | URL | Description |
|--------|-----|-------------|
| **Unified Strategy Builder (USB)** | `/` | Multi-leg options/futures strategies — straddles, strangles, iron condors, covered calls, range breakouts, BTST/STBT |
| **Indicator Signal Engine (ISE)** | `/indicator/` | Indicator-driven strategies — SuperTrend, MA CrossOver, RSI, MACD, Bollinger Bands, candlestick patterns — plus **Backtest** |
| **Inbound Signal Bridge (ISB)** | `/bridge/` | Webhook/TradingView signal execution — configure legs once, fire all on every inbound signal |
| **Rapid Execution Scalper (RES)** | `/scalper/` | Step-based averaging and jobbing strategies that add position size at regular price intervals |
| **Multi-Leg Hedger (MLH)** | `/hedger/` | Multi-leg option strategies with three modes: Normal, Range Breakout, and BTST/STBT |

---

## Tech Stack

- **Backend**: Django (Python)
- **AI**: Runware AI (OpenAI-compatible API)
- **Vector DB**: FAISS + HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- **Protocol**: Model Context Protocol (MCP)
- **Chat Logs**: SQLite via Django ORM (`chat_logs` app)
- **Production Server**: Gunicorn + gevent workers
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism, dark/light mode), JavaScript (SSE streaming)

---

## Project Structure

```
MM_Strategy_Builder_django/
├── manage.py
├── requirements.txt
├── config.py                          # API keys, URLs, cost rates, lot sizes
│
├── mm_project/                        # Django project configuration
│   ├── settings.py
│   ├── urls.py                        # Root URL dispatcher — all routes defined here
│   ├── views.py
│   ├── wsgi.py / asgi.py
│   └── gunicorn.conf.py               # Production server config (gevent, timeout, workers)
│
├── strategys/                         # All 5 strategy plugins consolidated
│   ├── views/
│   │   ├── common.py                  # make_chat_views() factory — shared chat/stream logic
│   │   └── views.py                   # All 5 plugin views (usb_index, mlh_index, etc.)
│   ├── urls/
│   │   └── urls.py                    # All 17 URL patterns for all 5 plugins
│   └── market_maya/
│       └── market_maya.py             # All 5 Market Maya API clients (USB, MLH, RES, ISB, ISE)
│
├── utils/                             # Shared infrastructure
│   ├── orchestrator/
│   │   ├── base_orchestrator.py       # Template method: process_message + stream_message
│   │   ├── strategies_orchestrator.py # Concrete orchestrator with Runware AI + MCP routing
│   │   └── orchestrators.py           # 5 singleton orchestrator instances
│   ├── generators/
│   │   ├── base_generator.py
│   │   ├── usb_generator.py           # V3 payload builder for USB
│   │   ├── mlh_generator.py
│   │   ├── res_generator.py
│   │   ├── isb_generator.py
│   │   ├── ise_generator.py
│   │   └── indicator_master.json      # Indicator names → MM API IDs + parameter definitions
│   ├── validation/
│   │   ├── base_validator.py
│   │   ├── usb_validator.py
│   │   ├── mlh_validator.py
│   │   ├── res_validator.py
│   │   ├── isb_validator.py
│   │   └── ise_validator.py
│   ├── mcp/
│   │   ├── tools.py                   # All MCP tool functions for all 5 plugins
│   │   └── handlers.py                # MCP tool dispatch handlers
│   └── rag/
│       ├── ingest.py                  # Build FAISS index from docs
│       ├── retriever.py               # Query FAISS at inference time
│       └── store/faiss_index/         # Persisted vector index
│
├── services/                          # Shared Django-layer services
│   ├── base_market_maya.py            # BaseMarketMayaService — base class for all MM clients
│   ├── deploy.py                      # Strategy deployment / undeploy
│   ├── backtest.py                    # get_backtest_options, run_backtest, get_backtest_result
│   ├── exchange_resolver.py           # Exchange/segment rules engine
│   ├── request_queue.py               # Global semaphore — limits concurrent LLM API calls
│   ├── session_context.py             # Per-user session memory
│   ├── view_helpers.py                # setup_user_context, get_history, save_messages
│   ├── token_service.py               # Bearer token refresh + caching
│   └── crypto.py                      # Credential encryption
│
├── prompts/                           # System prompts (one per plugin)
│   ├── usb_prompt.py
│   ├── mlh_prompt.py
│   ├── res_prompt.py
│   ├── isb_prompt.py
│   └── ise_prompt.py
│
├── marketmaya/                        # Market Maya API client library
│   ├── auth.py                        # Login + bearer token management
│   ├── operations.py                  # get_strategies, delete, modify, rename, balance
│   └── main.py
│
├── users/                             # Auth Django app
│   ├── models.py                      # UserBearerToken — encrypted credentials + cached data
│   ├── middleware.py                  # AuthMiddleware — protects all routes
│   ├── views.py                       # Login / logout
│   └── urls.py
│
├── chat_logs/                         # Chat log tracking
│   ├── models.py                      # ChatLog: tokens, cost (USD + INR), module, session
│   ├── views.py                       # Analytics dashboard + JSON API
│   └── urls.py                        # /logs/  /logs/api/
│
├── static/
│   ├── css/style.css                  # Dark/light theme variables and component styles
│   └── js/
│       ├── chat.js                    # SSE streaming client, message rendering
│       └── theme.js                   # Dark/light mode toggle with localStorage persistence
│
├── templates/                         # HTML templates (one per plugin + shared pages)
│   ├── index.html                     # USB
│   ├── indicator_engine.html          # ISE
│   ├── inbound_signal_bridge.html     # ISB
│   ├── rapid_execution_scalper.html   # RES
│   ├── multi_leg_hedger.html          # MLH
│   ├── chat_logs.html                 # Analytics dashboard
│   └── login.html / admin_panel.html
│
├── docs/                              # Reference documentation + API payloads
│   └── api/                           # Captured Market Maya API payload examples
│
├── tests/                             # Automated test scripts per plugin
│   ├── run_usb_tests.py
│   ├── run_ise_tests.py
│   ├── run_isb_tests.py
│   ├── run_res_tests.py
│   ├── run_mlh_tests.py
│   └── reports/                       # Saved test run outputs
│
└── logs/
    └── chat_history.db                # SQLite chat log database
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Market Maya Bearer Token
- Runware AI API Key

### 2. Install

```bash
git clone <repo-url>
cd MM_Strategy_Builder_django

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure

Create a `.env` file in the project root:

```env
RUNWARE_API_KEY=your_runware_key
RUNWARE_MODEL_ID=your_model_id
MARKET_MAYA_BEARER_TOKEN=your_market_maya_token
SECRET_KEY=your_django_secret

# Optional — override defaults
COST_PER_1M_INPUT_USD=0.25
COST_PER_1M_OUTPUT_USD=1.50
USD_TO_INR_RATE=95.71
```

> Leave `RUNWARE_API_KEY` and `RUNWARE_MODEL_ID` empty to disable AI calls during testing (no charges incurred).

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Build RAG Index

Run once to build the FAISS vector store from the documentation:

```bash
python -c "from utils.rag.ingest import ingest_docs; ingest_docs()"
```

### 6. Run

**Development:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Production:**
```bash
gunicorn mm_project.wsgi:application -c mm_project/gunicorn.conf.py
```

Open `http://localhost:8000` — navigate between plugins from the sidebar.

---

## How It Works

1. **Input** — User describes a strategy in natural language (e.g., *"BankNifty ATM straddle, 1 lot each leg, MIS, combined SL ₹5000"*)
2. **RAG** — Retriever queries the shared FAISS index for relevant parameter rules
3. **Preview** — AI generates structured Markdown tables matching the Market Maya UI tabs
4. **Confirmation** — User reviews and approves (confirm / yes / proceed / save)
5. **Deployment** — `generator.py` builds the production payload, `market_maya.py` POSTs to the API
6. **Logging** — Every interaction is saved to SQLite with token counts and INR cost

---

## Strategy Management

All plugins expose these conversational commands — no UI navigation needed:

| Command | What to say | Description |
|---------|-------------|-------------|
| **List strategies** | "show my strategies" | Fetches all strategies with name/type search support |
| **Delete strategy** | "delete strategy X" | Resolves name → hash ID, confirms, then deletes |
| **Modify strategy** | "change SL of X to 3000" | Fetches current record → shows diff → saves on approval |
| **Rename strategy** | "rename X to Y" | Confirms first, then calls rename API |
| **Check balance** | "what is my balance" | Shows Balance, Hold Balance, Point Balance |
| **Deploy strategy** | "deploy strategy X" | Deploys a saved strategy to live trading |

The AI follows a **confirm-before-act** pattern for all destructive or modifying operations.

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/strategy-counts/` | Strategy counts for all 5 plugins |
| `GET /api/balance/` | Current Market Maya point balance |
| `GET /api/queue-stats/` | Global LLM request queue status |
| `POST /api/chat` | Blocking chat (per plugin prefix) |
| `POST /api/chat/stream` | SSE streaming chat (per plugin prefix) |

---

## Exchange & Segment Rules

The exchange resolver (`services/exchange_resolver.py`) encodes all Market Maya exchange/segment rules:

| Asset | Exchange | Segment |
|-------|----------|---------|
| NIFTY / BANKNIFTY / FINNIFTY index | NSE | INDEX |
| NIFTY / BANKNIFTY / FINNIFTY futures | NFO | FUT |
| NIFTY / BANKNIFTY options | NFO | OPT |
| SENSEX / BANKEX index | BSE | INDEX |
| SENSEX / BANKEX futures | BFO | FUT |
| SENSEX / BANKEX options | BFO | OPT |
| Equity stocks | NFO | FUT |
| Equity stocks (with "equity"/"cash"/"EQ") | NSE | EQ |
| MCX commodities (GOLD, SILVER, CRUDEOIL…) | MCX | FUT / OPT |
| CDS currencies (USDINR, EURINR…) | CDS | FUT / OPT |

---

## Backtest (ISE Only)

### Conversational Flow

**Run a new backtest (charges points):**
1. User: *"backtest my BankNifty SuperTrend strategy"*
2. AI calls `get_backtest_options` → displays period selection table with point costs
3. User: *"run 6 months"*
4. AI calls `run_backtest` → deducts points, polls until complete (~10–15s), displays results

**View stored results (free):**
1. User: *"show backtest result for my strategy"*
2. AI calls `get_backtest_result` → reads stored analysis, displays 7 Markdown tables

### Point Costs

| Period | Points |
|--------|--------|
| 1 Month | 0 (free) |
| 6 Months | 18 |
| 1 Year | 36.5 |
| 2 Years | 73 |
| 3 Years | 109.5 |
| All Data (from 2017-02-01) | 340.4 |

---

## Plugin-Specific Notes

### ISB — Inbound Signal Bridge
- **Trail SL requires SL > 0** — if `sl = 0`, trail SL is automatically disabled at the generator level
- **Capital Risk(%) qty** — percentage stored in the `lot` field; API computes actual qty at runtime

### RES — Rapid Execution Scalper
- Defines a **main symbol** and a configurable number of **steps** (each adds a leg at a fixed price interval)
- Supports **Scalper** and **Jobbing** sub-modes

### MLH — Multi-Leg Hedger
- Three modes: **Normal**, **Range Breakout**, **BTST/STBT**
- Supports up to 10 independent option legs per strategy

---

## Chat Log

Every message across all plugins is tracked in `logs/chat_history.db`:

| Field | Description |
|-------|-------------|
| `module` | USB / ISE / ISB / RES / MLH |
| `session_id` | Browser session identifier |
| `user_message` | Full user input |
| `ai_response` | Complete AI response |
| `input_tokens` | Prompt token count |
| `output_tokens` | Completion token count |
| `cost_inr` | Calculated cost in Indian Rupees |
| `model_used` | Runware model ID |

Accessible at `/logs/` (dashboard) or `/logs/api/` (JSON API).

---

## Streaming Resilience

- **Empty stream** — if Runware returns zero chunks, the orchestrator retries with a non-streaming request
- **Mid-stream drop** — wrapped in `try/except`; partial content is preserved
- **Any exception** — `try/finally` guarantees chat log is always saved and session memory always updated

---

## Running Tests

```bash
# Start server first
python manage.py runserver 0.0.0.0:8000

# Run tests (from project root)
python tests/run_usb_tests.py
python tests/run_ise_tests.py
python tests/run_isb_tests.py
python tests/run_res_tests.py
python tests/run_mlh_tests.py
```

Reports are saved to `tests/reports/`.

---

## License

Internal Use Only. Confidential and Proprietary.

---

*Built for Traders by Aditya & Antigravity AI.*
