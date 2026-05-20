# ✈️ Flight Booking Agentic System

An AI-powered flight search and booking assistant built with **LangGraph**, **Mistral AI**, and **Amadeus API**. The agent uses a multi-node graph architecture to route queries, search real flights, rank results, and maintain conversation memory across turns.

![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129+-green?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-1.0+-purple)
![Mistral](https://img.shields.io/badge/Mistral_AI-LLM-orange)
![Amadeus](https://img.shields.io/badge/Amadeus-Flight_API-yellow)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI (app.py)                       │
│         POST /api/chat  │  GET /api/stream               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│                  LangGraph Agent                         │
│                                                          │
│   START                                                  │
│     │                                                    │
│     ▼                                                    │
│   route_node ──── (general) ──► memory_node ──► END      │
│     │                                                    │
│     │ (research)                                         │
│     ▼                                                    │
│   research_node ──► response_node ──► memory_node ──► END│
│                                                          │
│   Checkpointer: InMemorySaver (thread-based memory)      │
└─────────────────────────────────────────────────────────┘
```

### Node Descriptions

| Node | File | Purpose |
|------|------|---------|
| **route_node** | `backend/nodes/route.py` | Classifies user query → `general`, `research`, or `booking` |
| **research_node** | `backend/nodes/research.py` | Extracts search params via LLM → calls Amadeus API → ranks flights |
| **response_node** | `backend/agent/agent.py` | Formats ranked flights into a user-friendly response via LLM |
| **memory_node** | `backend/agent/agent.py` | Saves `{user, assistant}` turns to conversation memory |

---

## Project Structure

```
Flight-Booking-Agentic-System/
├── app.py                          # FastAPI server with API endpoints
├── main.py                         # CLI test script for the agent
├── pyproject.toml                  # Python dependencies
├── .env                            # Environment variables (API keys)
│
├── backend/
│   ├── agent/
│   │   ├── __init__.py             # Exports Agent class
│   │   └── agent.py                # Main Agent class — graph builder, nodes, invocation
│   ├── nodes/
│   │   ├── route.py                # RouteAgent — query classification via LLM
│   │   └── research.py             # ResearchAgent — param extraction, Amadeus API, ranking
│   └── prompts/
│       └── __init__.py             # All LLM prompts (route, search, rank, response)
│
├── constants/
│   └── agent_constant.py           # AgentState TypedDict with memory reducer
│
├── utils/
│   ├── logger.py                   # Logging setup (UTF-8, file + console)
│   └── exception.py                # Custom exception handler
│
├── templates/
│   └── index.html                  # Chat frontend UI (dark theme)
│
└── logs/                           # Auto-generated log files
```

---

## Features

### 🧠 Conversation Memory
- Uses LangGraph's `InMemorySaver` checkpointer for thread-level persistence
- Each conversation turn (`{user query, assistant response}`) is saved via the `memory_node`
- Memory is included in the route prompt so the agent maintains context across turns
- Memory uses `Annotated[List[Dict], operator.add]` reducer for automatic appending

### ⚡ Three Invocation Modes

| Method | Description | Use Case |
|--------|-------------|----------|
| `run_agent(query, thread_id)` | Full response, waits for completion | API / backend calls |
| `stream_agent(query, thread_id)` | Yields `(node_name, state_update)` per node | Debug / progress tracking |
| `stream_response(query, thread_id)` | Yields response token-by-token | Chat UI / real-time display |

### 🔍 Smart Routing
- **General**: Greetings, vague queries → conversational response
- **Research**: Specific flight details (origin + destination) → Amadeus API search
- **Booking**: Confirmation of a specific flight → booking flow (planned)

### 💰 Price Conversion
- Amadeus test API returns prices in EUR
- Automatic EUR → INR conversion at `1 EUR = 107.37 INR`
- Both `total` and `grandTotal` are converted

### 📊 Observability
- **Langfuse** integration for LLM tracing and monitoring
- Automatically reads `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_BASE_URL` from environment
- Graceful fallback — runs without observability if keys are missing

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the chat UI |
| `POST` | `/api/chat` | Send message → get agent response + flights |
| `GET` | `/api/stream?message=...&thread_id=...` | SSE streaming response |
| `GET` | `/api/memory?thread_id=...` | Retrieve conversation history |
| `GET` | `/api/new-session` | Generate a fresh thread ID |

### POST /api/chat

**Request:**
```json
{
  "message": "Flights from Kolkata to Mumbai on 15th March",
  "thread_id": "optional-existing-thread-id"
}
```

**Response:**
```json
{
  "response": "Here are the best flights for your trip...",
  "thread_id": "abc-123-def",
  "route_decision": "research",
  "search_params": {
    "origin": "CCU",
    "destination": "BOM",
    "departure_date": "2026-03-15"
  },
  "ranked_flights": [...]
}
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/arpanchakraborty23/Flight-Booking-Agentic-System.git
cd Flight-Booking-Agentic-System
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

Or using `uv`:
```bash
uv sync
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required
MISTRAL_API_KEY="your-mistral-api-key"
Amadeus_API_Key="your-amadeus-api-key"
Amadeus_API_Secret="your-amadeus-api-secret"

# Optional (Langfuse observability)
LANGFUSE_SECRET_KEY="sk-lf-..."
LANGFUSE_PUBLIC_KEY="pk-lf-..."
LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

**Get API Keys:**
- **Mistral AI**: [console.mistral.ai](https://console.mistral.ai/)
- **Amadeus**: [developers.amadeus.com](https://developers.amadeus.com/) (free test account)
- **Langfuse** (optional): [cloud.langfuse.com](https://cloud.langfuse.com/)

### 5. Run the Application

**Web server:**
```bash
python app.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

**CLI test:**
```bash
python main.py
```

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.14+** | Runtime |
| **FastAPI** | Web framework & API server |
| **LangGraph** | Stateful agent graph orchestration |
| **LangChain** | LLM abstraction layer |
| **Mistral AI** | Large Language Model (chat completions) |
| **Amadeus API** | Real-time flight search data |
| **Langfuse** | LLM observability & tracing |
| **Jinja2** | HTML templating |
| **Uvicorn** | ASGI server |

---

## LLM Prompts

All prompts are centralized in `backend/prompts/__init__.py`:

| Prompt | Purpose |
|--------|---------|
| `ROUTE_PROMPT` | Classifies user intent (general / research / booking) |
| `SEARCH_PARAMS_PROMPT` | Extracts IATA codes, dates, adults from user query |
| `RANK_FLIGHTS_PROMPT` | Ranks flight offers based on user preferences |
| `RESPONSE_FORMAT_PROMPT` | Formats ranked flights into a conversational response |

---

## Key Design Decisions

1. **LangGraph over LangChain Agents** — Explicit graph-based control flow instead of ReAct-style tool calling. More predictable and debuggable.
2. **Memory via Checkpointer** — Thread-scoped `InMemorySaver` for development. Can be swapped for SQLite/PostgreSQL in production.
3. **EUR → INR Conversion** — Amadeus test API doesn't support INR, so conversion is done in code after API response.
4. **Resilient Ranking** — If the ranking LLM call fails, original API results are returned unranked instead of crashing.
5. **Prompt Centralization** — All prompts in one module for easy tuning without touching node logic.

---

## Future Enhancements

- [ ] **Booking Node** — Complete the booking flow with passenger details
- [ ] **Persistent Memory** — Replace `InMemorySaver` with SQLite/PostgreSQL checkpointer
- [ ] **True Token Streaming** — Stream directly from LLM instead of word-by-word simulation
- [ ] **Return Flight Support** — Handle round-trip flight searches
- [ ] **Multi-language Support** — Add Hindi and other language prompts
- [ ] **Authentication** — User login and booking history

---

## License

This project is for educational and development purposes.
