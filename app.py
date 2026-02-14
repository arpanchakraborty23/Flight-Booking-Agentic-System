import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

load_dotenv()

from backend.agent.agent import Agent

# ──────────────────────────────────────────────
# App & Agent Initialization
# ──────────────────────────────────────────────
app = FastAPI(title="Flight Booking System", version="2.0")

# CORS (allow frontend dev servers if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="templates", html=True), name="static")

# Initialize agent once (shared across requests)
agent = Agent()


# ──────────────────────────────────────────────
# Request / Response Models
# ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    route_decision: str | None = None
    search_params: dict | None = None
    ranked_flights: list | None = None


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Sends the user message through the LangGraph agent and returns the response.
    """
    thread_id = req.thread_id or str(uuid.uuid4())

    result = agent.run_agent(query=req.message, thread_id=thread_id)

    return ChatResponse(
        response=result.get("response", "Sorry, something went wrong."),
        thread_id=thread_id,
        route_decision=result.get("route_decision"),
        search_params=result.get("search_params"),
        ranked_flights=result.get("ranked_flights"),
    )


@app.get("/api/stream")
async def stream_chat(message: str, thread_id: str = None):
    """
    Streaming chat endpoint.
    Returns the response token-by-token via Server-Sent Events (SSE).
    """
    thread_id = thread_id or str(uuid.uuid4())

    def event_generator():
        for token in agent.stream_response(query=message, thread_id=thread_id):
            # SSE format
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/memory")
async def get_memory(thread_id: str):
    """Retrieve conversation memory for a given thread."""
    memory = agent.get_memory(thread_id)
    return {"thread_id": thread_id, "memory": memory}


@app.get("/api/new-session")
async def new_session():
    """Generate a new thread ID for a fresh conversation."""
    return {"thread_id": str(uuid.uuid4())}


if __name__ == "__main__":
    uvicorn.run(app=app, port=8000, host="0.0.0.0")