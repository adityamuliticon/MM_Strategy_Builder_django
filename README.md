# Market Maya Strategy Builder

A pure **API backend** that powers AI-driven trading strategy creation on the **Market Maya** platform. Five strategy modules — each with its own AI orchestrator, RAG pipeline, and MCP tool layer — accept plain-English instructions via REST/SSE and translate them into Market Maya API calls. Market Maya's own UI consumes these endpoints directly.

---

## Modules

| Module | Base URL | Description |
|--------|----------|-------------|
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
- **Database**: PostgreSQL (Django ORM via `psycopg2-binary`)
- **Cache**: Redis — chat history cache-aside (TTL 24 h, max 20 messages per user/module)
- **Production Server**: Gunicorn + gevent workers

---

## Project Structure

```
MM_Strategy_Builder_django/
├── manage.py
├── requirements.txt
├── settings.py                        # Django settings
├── urls.py                            # Root URL dispatcher — all routes defined here
├── wsgi.py / asgi.py                  # WSGI / ASGI entry points
├── api_docs.py                        # ReDoc UI + OpenAPI spec views (/docs/ /openapi.json)
├── gunicorn.conf.py                   # Production server config (gevent, timeout, workers)
│
├── strategys/                         # All 5 strategy modules consolidated
│   ├── views/
│   │   ├── common.py                  # make_chat_views() factory — shared chat/stream logic
│   │   └── views.py                   # All 5 module views + strategy_counts + balance
│   ├── urls/
│   │   └── urls.py                    # All API URL patterns for all 5 modules
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
│   │   ├── tools.py                   # All MCP tool functions for all 5 modules
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
│   ├── redis_client.py                # Singleton Redis client (lazy init from Config)
│   ├── token_service.py               # Bearer token refresh + caching
│   └── crypto.py                      # Credential encryption
│
├── prompts/                           # System prompts (one per module)
│   ├── usb_prompt.py
│   ├── mlh_prompt.py
│   ├── res_prompt.py
│   ├── isb_prompt.py
│   └── ise_prompt.py
│
├── marketmaya/                        # Market Maya API client library
│   ├── config.py                      # All API keys, URLs, cost rates, lot sizes
│   ├── auth.py                        # Login + bearer token management
│   ├── operations.py                  # get_strategies, delete, modify, rename, balance
│   └── main.py
│
├── users/                             # Auth Django app
│   ├── models.py                      # AppUser + UserBearerToken (encrypted credentials)
│   ├── middleware.py                  # AuthMiddleware — returns 401 JSON for all unauth requests
│   ├── views.py                       # auth_login, auth_logout, history_api, admin_auth_login
│   └── urls.py
│
├── chat_logs/                         # Chat log tracking
│   ├── models.py                      # ChatLog, ChatMessage, APICallLog
│   ├── views.py                       # logs_api, api_logs_api (JSON only)
│   └── urls.py                        # /logs/api/  /logs/api-calls/api/
│
├── docs/                              # Reference documentation + API payloads
│   ├── openapi.yaml                   # OpenAPI 3.0 spec — served at /openapi.json
│   └── api/                           # Captured Market Maya API payload examples
│
├── tests/                             # Automated test scripts per module
│   ├── run_usb_tests.py
│   ├── run_ise_tests.py
│   ├── run_isb_tests.py
│   ├── run_res_tests.py
│   ├── run_mlh_tests.py
│   └── reports/                       # Saved test run outputs
│
└── logs/                              # Application logs (runtime output)
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 13+ (running locally or remote)
- Redis 6+ (running locally — `sudo apt install redis-server` on Ubuntu)
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
SECRET_KEY=your_django_secret
DEBUG=False

# AI — leave empty to disable AI calls during testing (no charges incurred)
RUNWARE_API_KEY=
RUNWARE_MODEL_ID=

MARKET_MAYA_BEARER_TOKEN=your_market_maya_token
MM_ENCRYPTION_KEY=your_fernet_key

# PostgreSQL
DB_NAME=mm_strategy_builder
DB_USER=postgres
DB_PASSWORD=your_pg_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional — override defaults
COST_PER_1M_INPUT_USD=0.25
COST_PER_1M_OUTPUT_USD=1.50
USD_TO_INR_RATE=95.71
```

Generate a Fernet key with:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Set Up PostgreSQL

```bash
sudo -u postgres psql -c "CREATE DATABASE mm_strategy_builder;"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'your_pg_password';"
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Build RAG Index

Run once to build the FAISS vector store from the documentation:

```bash
python -c "from utils.rag.ingest import ingest_docs; ingest_docs()"
```

### 7. Start Redis

```bash
sudo systemctl start redis-server
redis-cli ping   # should print PONG
```

### 8. Run

**Development:**
```bash
python manage.py runserver 0.0.0.0:8000
```

**Production:**
```bash
gunicorn wsgi:application -c gunicorn.conf.py
```

Once running, open `http://localhost:8000/docs/` to browse the full interactive API documentation (ReDoc).

---

## How It Works

1. **Input** — Client sends a plain-English message via `POST /api/chat` or `/api/chat/stream`
2. **RAG** — Retriever queries the shared FAISS index for relevant parameter rules
3. **Preview** — AI generates structured Markdown tables matching the Market Maya UI tabs
4. **Confirmation** — Client sends a confirmation message (e.g., `"confirm"`)
5. **Deployment** — Generator builds the production payload, Market Maya client POSTs to the API
6. **Logging** — Every interaction is saved to PostgreSQL with token counts and INR cost

---

## API Reference

All endpoints return JSON. All endpoints except `/auth/login/` and `/auth/logout/` require a valid session (obtained via `/auth/login/`). Unauthenticated requests receive `401 {"error": "Not authenticated"}`.

---

### Authentication

#### `POST /auth/login/`
Log in with Market Maya credentials. Creates a session and stores the bearer token.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "yourpassword"
}
```

**Response `200`:**
```json
{
  "status": "ok",
  "display_name": "John"
}
```

**Response `401`:**
```json
{ "error": "Invalid email or password" }
```

---

#### `POST /auth/logout/`
Clears the session.

**Response `200`:**
```json
{ "status": "logged_out" }
```

---

### Chat — Unified Strategy Builder (USB)

#### `POST /api/chat`
Blocking chat. Waits for the full AI response before returning.

**Request body:**
```json
{ "message": "BankNifty ATM straddle, 1 lot each leg, MIS, combined SL 5000" }
```

**Response `200`:**
```json
{
  "status": "success",
  "message": "Here is the strategy preview:\n\n| Leg | Symbol | ..."
}
```

---

#### `POST /api/chat/stream`
Server-Sent Events streaming. Returns a stream of `data: {...}` events.

**Request body:**
```json
{ "message": "BankNifty ATM straddle, 1 lot each leg, MIS, combined SL 5000" }
```

**Response** — `Content-Type: text/event-stream`

Each event is one of:

| Event `t` | Payload | Meaning |
|-----------|---------|---------|
| `chunk` | `{"t": "chunk", "v": "Here is..."}` | Incremental text token |
| `done` | `{"t": "done", "in_tok": 120, "out_tok": 340, "task_id": "..."}` | Stream complete |
| `error` | `{"t": "error", "v": "⚠️ Connection error..."}` | Stream failed |

---

### Chat — Indicator Signal Engine (ISE)

#### `POST /indicator/api/chat`
Same request/response as USB chat.

#### `POST /indicator/api/chat/stream`
Same SSE stream as USB stream.

---

### Chat — Inbound Signal Bridge (ISB)

#### `POST /bridge/api/chat`
Same request/response as USB chat.

#### `POST /bridge/api/chat/stream`
Same SSE stream as USB stream.

---

### Chat — Rapid Execution Scalper (RES)

#### `POST /scalper/api/chat`
Same request/response as USB chat.

#### `POST /scalper/api/chat/stream`
Same SSE stream as USB stream.

---

### Chat — Multi-Leg Hedger (MLH)

#### `POST /hedger/api/chat`
Same request/response as USB chat.

#### `POST /hedger/api/chat/stream`
Same SSE stream as USB stream.

---

### Strategy Data

#### `GET /api/strategy-counts/`
Returns the number of saved strategies per module for the authenticated user.

**Response `200`:**
```json
{
  "usb": 5,
  "ise": 2,
  "isb": 1,
  "res": 0,
  "mlh": 3
}
```

---

#### `GET /api/balance/`
Returns the authenticated user's current Market Maya point balance.

**Response `200`:**
```json
{ "point_balance": 247.5 }
```

**Response `200` (on API error):**
```json
{ "point_balance": null }
```

---

#### `GET /api/history/`
Returns the last 100 chat messages for a given user and module.

**Query params:**

| Param | Default | Example |
|-------|---------|---------|
| `module` | `USB` | `?module=ISE` |

**Response `200`:**
```json
{
  "history": [
    { "role": "user",      "content": "BankNifty straddle...", "ts": "2026-06-30T10:00:00+05:30" },
    { "role": "assistant", "content": "Here is the preview...", "ts": "2026-06-30T10:00:02+05:30" }
  ]
}
```

---

### System

#### `GET /api/queue-stats/`
Returns the current state of the global LLM request queue (semaphore that limits concurrent AI calls).

**Response `200`:**
```json
{
  "waiting": 0,
  "active": 1,
  "total_processed": 142
}
```

---

### Logs

#### `GET /logs/api/`
Returns chat logs with optional filtering. Max 500 records per call.

**Query params:**

| Param | Description | Example |
|-------|-------------|---------|
| `module` | Filter by module | `?module=USB` |
| `date_from` | Start date (inclusive) | `?date_from=2026-06-01` |
| `date_to` | End date (inclusive) | `?date_to=2026-06-30` |

**Response `200`:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2026-06-30T10:00:00+05:30",
      "module": "USB",
      "session_id": "abc123_USB",
      "user_message": "BankNifty straddle...",
      "ai_response": "Here is the preview...",
      "input_tokens": 120,
      "output_tokens": 340,
      "total_tokens": 460,
      "cost_usd": 0.00054,
      "cost_inr": 0.0517,
      "model_used": "google:gemini@3.1-flash-lite"
    }
  ],
  "totals": {
    "total_requests": 1,
    "total_input_tokens": 120,
    "total_output_tokens": 340,
    "total_tokens": 460,
    "total_cost_inr": 0.0517,
    "total_cost_usd": 0.00054
  }
}
```

---

#### `GET /logs/api-calls/api/`
Returns Market Maya API call logs with optional filtering. Max 500 records per call.

**Query params:**

| Param | Description | Example |
|-------|-------------|---------|
| `module` | Filter by module | `?module=ISE` |
| `call_type` | Filter by call type | `?call_type=create_strategy` |
| `status` | Filter by status | `?status=success` |
| `session_id` | Filter by session (partial match) | `?session_id=abc123` |
| `date_from` | Start date | `?date_from=2026-06-01` |
| `date_to` | End date | `?date_to=2026-06-30` |

**Response `200`:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2026-06-30T10:00:00+05:30",
      "module": "USB",
      "call_type": "create_strategy",
      "endpoint": "https://webapi.marketmaya.com/api/mainStrategy/CreateUnifiedStrategy",
      "method": "POST",
      "response_status": 200,
      "duration_ms": 340,
      "status": "success",
      "session_id": "abc123_USB",
      "request_payload": "...",
      "response_body": "..."
    }
  ],
  "total": 1
}
```

---

### Admin

#### `POST /admin-auth/`
Admin login with username + password.

**Request body:**
```json
{ "username": "aditya", "password": "12345" }
```

**Response `200`:**
```json
{ "status": "ok" }
```

**Response `401`:**
```json
{ "error": "Invalid credentials" }
```

---

#### `POST /admin-logout/`
Clears the admin session.

**Response `200`:**
```json
{ "status": "logged_out" }
```

---

### All Endpoints at a Glance

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/login/` | No | Log in, get session |
| `POST` | `/auth/logout/` | No | Clear session |
| `POST` | `/api/chat` | Yes | USB — blocking chat |
| `POST` | `/api/chat/stream` | Yes | USB — SSE streaming chat |
| `POST` | `/indicator/api/chat` | Yes | ISE — blocking chat |
| `POST` | `/indicator/api/chat/stream` | Yes | ISE — SSE streaming chat |
| `POST` | `/bridge/api/chat` | Yes | ISB — blocking chat |
| `POST` | `/bridge/api/chat/stream` | Yes | ISB — SSE streaming chat |
| `POST` | `/scalper/api/chat` | Yes | RES — blocking chat |
| `POST` | `/scalper/api/chat/stream` | Yes | RES — SSE streaming chat |
| `POST` | `/hedger/api/chat` | Yes | MLH — blocking chat |
| `POST` | `/hedger/api/chat/stream` | Yes | MLH — SSE streaming chat |
| `GET` | `/api/strategy-counts/` | Yes | Strategy counts per module |
| `GET` | `/api/balance/` | Yes | Market Maya point balance |
| `GET` | `/api/history/` | Yes | Chat history for user/module |
| `GET` | `/api/queue-stats/` | Yes | LLM request queue status |
| `GET` | `/logs/api/` | Yes | Chat logs (filterable JSON) |
| `GET` | `/logs/api-calls/api/` | Yes | API call logs (filterable JSON) |
| `POST` | `/admin-auth/` | No | Admin login |
| `POST` | `/admin-logout/` | No | Admin logout |

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
1. Client: `"backtest my BankNifty SuperTrend strategy"`
2. AI calls `get_backtest_options` → returns period selection table with point costs
3. Client: `"run 6 months"`
4. AI calls `run_backtest` → deducts points, polls until complete (~10–15s), returns results

**View stored results (free):**
1. Client: `"show backtest result for my strategy"`
2. AI calls `get_backtest_result` → returns stored analysis with 7 Markdown tables

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

## Module-Specific Notes

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

## Redis Cache

Chat history is served from Redis on every request — PostgreSQL is only hit on a cache miss.

| Setting | Value |
|---------|-------|
| Key pattern | `chat_history:{user_id}:{module}` |
| TTL | 86 400 s (24 hours) |
| Max messages per key | 20 (oldest trimmed automatically) |

**Flow:**
- `get_history()` — checks Redis first; on miss, fetches from PostgreSQL and warms the cache
- `save_messages()` — writes to PostgreSQL, then pushes both messages to the Redis list via pipeline
- **Graceful degradation** — all Redis operations are wrapped in `try/except`; if Redis is unavailable the app transparently falls back to PostgreSQL with no downtime

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

*Built for Traders by Aditya.*
