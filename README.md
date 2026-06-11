# Market Maya Strategy Builder

An AI-powered trading strategy builder for the **Market Maya API**. Five isolated strategy plugins — each with its own AI orchestrator, RAG pipeline, and MCP tool layer — let traders describe strategies in plain English and deploy them directly to Market Maya with a single confirmation.

---

## Plugins

| Plugin | URL | Description |
|--------|-----|-------------|
| **Unified Strategy Builder (USB)** | `/` | Multi-leg options/futures strategies — straddles, strangles, iron condors, covered calls, range breakouts, BTST/STBT |
| **Indicator Signal Engine (ISE)** | `/indicator/` | Indicator-driven strategies — SuperTrend, MA CrossOver, RSI, MACD, Bollinger Bands, candlestick patterns — plus **Backtest** |
| **Inbound Signal Bridge (ISB)** | `/bridge/` | Webhook/TradingView signal execution — configure legs once, fire all on every inbound signal |
| **Rapid Execution Scalper (RES)** | `/scalper/` | Step-based averaging and jobbing strategies that add position size at regular price intervals |
| **Multi-Leg Hedger (MLH)** | `/hedger/` | Multi-leg option strategies with three modes: Normal, Range Breakout, and BTST/STBT |

Each plugin is fully isolated: separate Django app, FAISS vector store, session memory, and Market Maya service instance.

---

## Tech Stack

- **Backend**: Django (Python)
- **AI**: Runware AI (OpenAI-compatible API)
- **Vector DB**: FAISS + HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- **Protocol**: Model Context Protocol (MCP)
- **Chat Logs**: SQLite via Django ORM (`chat_logs` app)
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism, dark/light mode), JavaScript (SSE streaming)

---

## Project Structure

```
MM_Strategy_Builder_django/
├── manage.py
├── requirements.txt
├── config.py                          # API keys, URLs, cost rates, lot sizes, strategy type IDs
│
├── mm_project/                        # Django project configuration
│   ├── settings.py
│   ├── urls.py                        # Root URL dispatcher for all 5 plugins
│   └── views.py                       # Cross-plugin endpoints: strategy counts, balance
│
├── services/                          # Shared services (all 5 plugins)
│   ├── exchange_resolver.py           # Exchange/segment rules engine
│   ├── market_maya_shared.py          # Shared MM API: list, delete, modify, rename, balance
│   └── deploy.py                      # Strategy deployment service
│
├── chat_logs/                         # Chat log tracking (all plugins)
│   ├── models.py                      # ChatLog: tokens, cost (USD + INR), module, session
│   ├── views.py                       # Analytics dashboard + JSON API
│   └── urls.py                        # /logs/  /logs/api/
│
├── Unified_Strategy_Builder/          # Plugin 1: USB
│   ├── views.py / urls.py
│   ├── core/orchestrator.py           # AI loop + system prompt + streaming
│   ├── mcp/handlers.py, tools.py      # Tool routing + deployment
│   ├── rag/ingest.py, retriever.py, store/
│   └── services/generator.py, market_maya.py, validator.py
│
├── indicator_engine/                  # Plugin 2: ISE
│   ├── (same sub-structure as USB)
│   └── services/
│       ├── backtest.py                # get_backtest_options, run_backtest (polls until complete)
│       └── indicator_master.json      # Indicator names → MM API IDs + parameter definitions
│
├── inbound_signal_bridge/             # Plugin 3: ISB (same sub-structure)
│
├── rapid_execution_scalper/           # Plugin 4: RES (same sub-structure)
│
├── multi_leg_hedger/                  # Plugin 5: MLH (same sub-structure)
│
├── static/
│   ├── css/style.css                  # Dark/light theme variables and component styles
│   └── js/
│       ├── chat.js                    # SSE streaming client, message rendering
│       └── theme.js                   # Dark/light mode toggle with localStorage persistence
│
├── templates/                         # HTML templates (one per plugin + chat logs)
│   ├── index.html                     # USB
│   ├── indicator_engine.html          # ISE
│   ├── inbound_signal_bridge.html     # ISB
│   ├── rapid_execution_scalper.html   # RES
│   ├── multi_leg_hedger.html          # MLH
│   └── chat_logs.html                 # Analytics dashboard
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

# Optional — override defaults
COST_PER_1M_INPUT_USD=0.25
COST_PER_1M_OUTPUT_USD=1.50
USD_TO_INR_RATE=95.71
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Build RAG Indexes

Run once per plugin to build the FAISS vector stores from the documentation:

```bash
python -c "from Unified_Strategy_Builder.rag.ingest import ingest_docs; ingest_docs()"
python -c "from indicator_engine.rag.ingest import ingest_docs; ingest_docs()"
python -c "from inbound_signal_bridge.rag.ingest import ingest; ingest()"
python -c "from rapid_execution_scalper.rag.ingest import ingest_docs; ingest_docs()"
python -c "from multi_leg_hedger.rag.ingest import ingest_docs; ingest_docs()"
```

### 6. Run

```bash
python manage.py runserver 0.0.0.0:8000
```

Open `http://localhost:8000` — navigate between plugins from the sidebar.

---

## How It Works

1. **Input** — User describes a strategy in natural language (e.g., *"BankNifty ATM straddle, 1 lot each leg, MIS, combined SL ₹5000"*)
2. **RAG** — System retrieves relevant parameter rules from the plugin's FAISS index
3. **Preview** — AI generates structured Markdown tables matching the Market Maya UI tabs
4. **Confirmation** — User reviews and approves (confirm / yes / proceed / save)
5. **Deployment** — `generator.py` builds the production payload, `market_maya.py` POSTs to the API
6. **Logging** — Every interaction is saved to the SQLite chat log with token counts and INR cost

---

## Strategy Management

All plugins expose these conversational management commands — no UI navigation needed:

| Command | What to say | Description |
|---------|-------------|-------------|
| **List strategies** | "show my strategies", "how many strategies do I have" | Fetches all strategies with name/type search support |
| **Delete strategy** | "delete strategy X" | Resolves name → hash ID automatically, confirms, then deletes |
| **Modify strategy** | "change SL of X to 3000" | Fetches current record → shows diff → saves on approval |
| **Rename strategy** | "rename X to Y" | Confirms first, then calls rename API |
| **Check balance** | "what is my balance" | Shows Balance, Hold Balance, Point Balance |
| **Deploy strategy** | "deploy strategy X" | Deploys a saved strategy to live trading |

The AI follows a **confirm-before-act** pattern for all destructive or modifying operations.

---

## Cross-Plugin API Endpoints

Two endpoints at the project root serve the sidebar navigation UI:

| Endpoint | Description |
|----------|-------------|
| `GET /api/strategy-counts/` | Returns JSON with strategy counts for all 5 plugins (parallel fetch) |
| `GET /api/balance/` | Returns current Market Maya point balance |

---

## Exchange & Segment Rules

The exchange resolver (`services/exchange_resolver.py`) encodes all Market Maya exchange/segment rules:

| Asset | Exchange | Segment |
|-------|----------|---------|
| NIFTY / BANKNIFTY / FINNIFTY / MIDCPNIFTY index | NSE | INDEX |
| NIFTY / BANKNIFTY / FINNIFTY / MIDCPNIFTY futures | NFO | FUT |
| NIFTY / BANKNIFTY options | NFO | OPT |
| SENSEX / BANKEX index | BSE | INDEX |
| SENSEX / BANKEX futures | BFO | FUT |
| SENSEX / BANKEX options | BFO | OPT |
| Equity stocks (no keyword) | NFO | FUT |
| Equity stocks (with "equity"/"cash"/"EQ" keyword) | NSE | EQ |
| MCX commodities (GOLD, SILVER, CRUDEOIL, etc.) | MCX | FUT / OPT |
| CDS currencies (USDINR, EURINR, EURUSD, etc.) | CDS | FUT / OPT |

**Rule 9 — Native family:** SENSEX/BANKEX strategies use BFO/FUT for futures legs, not BSE/INDEX. The native family changes the exchange only; the segment follows from the asset type.

---

## Backtest (ISE Only)

The Indicator Signal Engine supports conversational backtesting against historical Market Maya data.

### Conversational Flow

**Run a new backtest (charges points):**
1. User: *"backtest my BankNifty SuperTrend strategy"*
2. AI calls `get_backtest_options` → displays a period selection table with point costs
3. User: *"run 6 months"*
4. AI calls `run_backtest` → deducts points, polls until `status == "Completed"` (~10–15 s), displays results

**View stored results (free, no new run):**
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

Per-day charge: 0.1 points. Use *"what is my balance"* to check points before running.

### Result Tables

`run_backtest` produces 4 tables: Backtest Summary, Trade Statistics, Profit/ROI Metrics, Day-of-Week P&L.

`get_backtest_result` produces 7 tables: Overview, Trade Analysis, Day/Month/Year Statistics, Period Comparison, Yearly P&L, Monthly P&L, Daily P&L (recent 20).

---

## Plugin-Specific Notes

### ISB — Inbound Signal Bridge

- **Trail SL requires SL > 0** — if `sl = 0`, trail SL is automatically disabled at the generator level regardless of AI output
- **Capital Risk(%) qty** — percentage stored in the `lot` field; API computes actual qty at runtime
- Supports TradingView / Pine Script alerts via the `/bridge/webhook/` endpoint

### RES — Rapid Execution Scalper

- Defines a **main symbol** (the instrument being averaged) and a configurable number of **steps** (each step adds a new leg at a fixed price interval)
- Each step can have its own qty, target, and SL relative to the step entry
- Supports **Scalper** and **Jobbing** sub-modes

### MLH — Multi-Leg Hedger

- Three trading modes: **Normal** (standard intraday/positional), **Range Breakout** (fires when price breaks a configured range), **BTST/STBT** (overnight hold)
- Supports up to 10 independent option legs per strategy
- Per-leg SL, trail SL, target, and re-entry configuration

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

All plugins handle Runware streaming failures gracefully:

- **Empty stream** — if Runware returns zero chunks, the orchestrator automatically retries using a non-streaming request on the same turn
- **Mid-stream connection drop** — wrapped in `try/except`; partial content is preserved
- **Any unhandled exception** — views use `try/finally` to guarantee the chat log is always saved and session memory always updated

---

## Running Tests

Each plugin has automated test prompts covering every parameter. Run against a live server:

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
