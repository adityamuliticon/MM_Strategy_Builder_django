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
- **Chat Logs**: SQLite via Django ORM (`chat_logs` app)
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism), JavaScript

---

## Project Structure

```
MM_Strategy_Builder_django/
├── manage.py
├── requirements.txt
├── config.py                      # API keys, URLs, cost rates, Django settings
│
├── mm_project/                    # Django project config
│   ├── settings.py
│   └── urls.py
│
├── services/                      # Shared backend services (all 3 modules)
│   └── market_maya_shared.py      # get_strategies, delete, modify, rename, balance
│
├── chat_logs/                     # Chat log tracking
│   └── models.py                  # ChatLog: tokens, cost (USD + INR), module, session
│
├── Unified_Strategy_Builder/      # Unified Strategy Builder (USB)
│   ├── views.py / urls.py
│   ├── core/orchestrator.py       # AI loop + system prompt + streaming
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
│   └── api/                       # Captured API payloads (modify, rename, balance, etc.)
│
├── tests/                         # Test infrastructure
│   ├── run_usb_tests.py
│   ├── run_ise_tests.py
│   ├── run_isb_tests.py
│   ├── cases/                     # Test specs per module
│   └── reports/                   # Saved test run outputs
│
└── logs/
    └── chat_history.db            # SQLite chat log database
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

Run once per module to build the FAISS vector stores from the documentation:

```bash
# Unified Strategy Builder
python -c "from Unified_Strategy_Builder.rag.ingest import ingest_docs; ingest_docs()"

# Indicator Signal Engine
python -c "from indicator_engine.rag.ingest import ingest_docs; ingest_docs()"

# Inbound Signal Bridge
python -c "from inbound_signal_bridge.rag.ingest import ingest; ingest()"
```

### 6. Run

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
6. **Logging** — Every interaction is saved to the SQLite chat log with token counts and INR cost

---

## Strategy Management Tools

All three modules expose these conversational management commands — no UI navigation needed:

| Command | What to say | Description |
|---------|-------------|-------------|
| **List strategies** | "show my strategies", "how many strategies do I have" | Fetches all strategies with search/filter support |
| **Delete strategy** | "delete strategy X" | Resolves name → hash ID automatically, then deletes |
| **Modify strategy** | "change SL of X to 3000" | Fetches current record → shows diff → saves on approval |
| **Rename strategy** | "rename X to Y" | Confirms first, then calls rename API |
| **Check balance** | "what is my balance" | Shows Balance, Hold Balance, Point Balance |

The AI follows a **confirm-before-act** pattern for all destructive or modifying operations.

---

## Chat Log

Every message across all modules is tracked in `logs/chat_history.db`:

| Field | Description |
|-------|-------------|
| `module` | USB / ISE / ISB |
| `session_id` | Browser session identifier |
| `user_message` | Full user input |
| `ai_response` | Complete AI response |
| `input_tokens` | Prompt token count |
| `output_tokens` | Completion token count |
| `cost_inr` | Calculated cost in Indian Rupees |
| `model_used` | Runware model ID |

Accessible via Django Admin at `/admin/chat_logs/chatlog/`.

---

## ISB-Specific Rules

The Inbound Signal Bridge has additional constraints enforced at the generator level:

- **Trail SL requires SL > 0** — if `sl = 0`, trail SL is automatically disabled regardless of what the AI passes
- **Capital Risk(%) qty** — the percentage value is stored in the `lot` field; the API computes actual qty at runtime
- **Capital(%) qty** — same as above; `lot` holds the percentage, `qty = 1`

---

## Streaming Resilience

All three modules handle Runware streaming failures gracefully:

- **Empty stream** — if Runware returns zero chunks, the orchestrator automatically retries using a non-streaming request on the same turn
- **Mid-stream connection drop** — wrapped in `try/except`; partial content is preserved
- **Any unhandled exception** — views use `try/finally` to guarantee the chat log is always saved and session memory always updated, even on crash

---

## Running Tests

Each module has automated test prompts covering every parameter. Run against a live server:

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
