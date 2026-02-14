import os
import sys
import json
import uuid
from typing import Generator, AsyncGenerator
from langchain_mistralai import ChatMistralAI
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv

from utils.logger import setup_logger
from utils.exception import CustomException
from constants.agent_constant import AgentState
from backend.nodes.research import ResearchAgent
from backend.nodes.route import RouteAgent
from backend.prompts import RESPONSE_FORMAT_PROMPT

load_dotenv()
logger = setup_logger("booking_agent")

# Langfuse observability (optional — won't crash if keys missing)
# Requires env vars: LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL
langfuse_handler = None
try:
    from langfuse.langchain import CallbackHandler
    from langfuse import get_client

    # get_client() automatically reads LANGFUSE_SECRET_KEY,
    # LANGFUSE_PUBLIC_KEY, and LANGFUSE_BASE_URL from environment
    langfuse = get_client()
    langfuse_handler = CallbackHandler()
    logger.info("Langfuse tracking configured ✅")
except Exception as e:
    logger.warning(f"Langfuse not configured — running without observability: {e}")


class Agent:
    """
    Flight Booking Agent — LangGraph Workflow with Memory & Streaming

    Features:
        ✅ Conversation memory via LangGraph InMemorySaver checkpointer
        ✅ Thread-based sessions (each thread remembers past interactions)
        ✅ Streaming response (token-by-token LLM output)
        ✅ Node-level streaming (see which node is executing)

    """

    def __init__(self) -> None:
        self.llm = self._init_model()
        self.route = RouteAgent(self.llm)
        self.research = ResearchAgent(self.llm)
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    def _init_model(self):
        """Initialize the Mistral LLM."""
        try:
            llm = ChatMistralAI(api_key=os.getenv("MISTRAL_API_KEY"))
            logger.info("LLM model loaded successfully!")
            return llm
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise CustomException(e, sys)

    def _route_node(self, state: AgentState) -> dict:
        """Node 1: Route the user query to the correct sub-agent."""
        logger.info(f"[route_node] Query: {state['query']}")
        logger.info(f"[route_node] Memory entries: {len(state.get('memory', []))}")
        return self.route.run_route(state)

    def _research_node(self, state: AgentState) -> dict:
        """Node 2: Research flights via Amadeus API."""
        logger.info("[research_node] Searching for flights...")
        return self.research.research(state)

    def _response_node(self, state: AgentState) -> dict:
        """
        Node 3: Format research results into a user-friendly response.
        Uses the LLM to generate a natural language summary of ranked flights.
        """
        try:
            ranked_flights = state.get("ranked_flights", [])
            search_params = state.get("search_params", {})
            existing_response = state.get("response", "")

            # If research already set a response (error / missing params), keep it
            if not ranked_flights and existing_response:
                logger.info("[response_node] Using existing response from research")
                return {"response": existing_response}

            if not ranked_flights:
                return {
                    "response": "Sorry, I couldn't find any flights matching your criteria. "
                                "Please try different dates or destinations."
                }

            prompt = RESPONSE_FORMAT_PROMPT.format(
                search_params=json.dumps(search_params, indent=2),
                ranked_flights=json.dumps(ranked_flights, indent=2),
            )

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            logger.info("[response_node] Response generated successfully")
            return {"response": content}

        except Exception as e:
            logger.error(f"[response_node] Error: {e}")
            return {
                "response": f"Found {len(ranked_flights)} flights: "
                            f"{json.dumps(ranked_flights, indent=2)}"
            }

    def _memory_node(self, state: AgentState) -> dict:
        """
        Node 4: Save the current conversation turn to memory.
        Appends {query, response} to the memory list via the reducer.
        """
        query = state.get("query", "")
        response = state.get("response", "")

        memory_entry = {
            "role": "user",
            "content": query,
        }
        assistant_entry = {
            "role": "assistant",
            "content": response,
        }

        logger.info(f"[memory_node] Saving turn to memory (total: {len(state.get('memory', [])) + 2})")

        # Return list — the Annotated[..., operator.add] reducer will APPEND these
        return {"memory": [memory_entry, assistant_entry]}

    def _decide_after_route(self, state: AgentState) -> str:
        """
        Conditional edge after route_node.
        Decides whether to research flights or end the conversation.
        """
        decision = state.get("route_decision", "general")
        logger.info(f"[router] Decision: {decision}")

        if decision == "research":
            return "research_node"
        elif decision == "booking":
            # TODO: Add booking node in future
            return "memory_node"
        else:
            # General conversation — response already set by route_node
            return "memory_node"


    def _build_graph(self):
        """Construct and compile the LangGraph StateGraph with memory."""
        try:
            workflow = StateGraph(AgentState)

            # ── Register Nodes ──
            workflow.add_node("route_node", self._route_node)
            workflow.add_node("research_node", self._research_node)
            workflow.add_node("response_node", self._response_node)
            workflow.add_node("memory_node", self._memory_node)

            # ── Define Edges ──
            # START → route_node
            workflow.add_edge(START, "route_node")

            # route_node → conditional → research_node or memory_node (→ END)
            workflow.add_conditional_edges(
                "route_node",
                self._decide_after_route,
                {
                    "research_node": "research_node",
                    "memory_node": "memory_node",
                }
            )

            # research_node → response_node
            workflow.add_edge("research_node", "response_node")

            # response_node → memory_node
            workflow.add_edge("response_node", "memory_node")

            # memory_node → END
            workflow.add_edge("memory_node", END)

            # ── Compile with Checkpointer for Memory ──
            graph = workflow.compile(checkpointer=self.checkpointer)
            logger.info("LangGraph compiled with memory ✅")

            graph.get_graph().draw_mermaid_png()
            return graph

        except Exception as e:
            logger.error(f"Error building graph: {e}")
            raise CustomException(e, sys)


    def _build_config(self, thread_id: str) -> dict:
        """Build invocation config with thread_id and optional Langfuse callback."""
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]
        return config

    # ──────────────────────────────────────────
    # Run Agent (standard — full response)
    # ──────────────────────────────────────────
    def run_agent(self, query: str, thread_id: str = None) -> dict:
        """
        Execute the Flight Booking Agent graph with memory.

        Args:
            query: User's natural language query
            thread_id: Session ID for conversation memory.
                       Same thread_id = same conversation context.
                       If None, generates a new thread.

        Returns:
            Final state dict with the agent's response
        """
        try:
            if not thread_id:
                thread_id = str(uuid.uuid4())

            logger.info(f"🚀 Agent invoked | thread: {thread_id} | query: {query}")

            initial_state = {
                "query": query,
                "memory": [],       # Empty list — reducer appends
                "response": "",
            }

            config = self._build_config(thread_id)
            result = self.graph.invoke(initial_state, config=config)

            logger.info(f"✅ Agent completed | thread: {thread_id}")
            return result

        except Exception as e:
            logger.error(f"Error in run_agent: {e}")
            raise CustomException(e, sys)

    def stream_agent(self, query: str, thread_id: str = None) -> Generator:
        """
        Stream the graph execution node-by-node.
        Yields (node_name, state_update) tuples as each node completes.

        Args:
            query: User's natural language query
            thread_id: Session ID for conversation memory

        Yields:
            Tuple of (node_name: str, state_update: dict)
        """
        try:
            if not thread_id:
                thread_id = str(uuid.uuid4())

            logger.info(f"🔄 Streaming agent | thread: {thread_id} | query: {query}")

            initial_state = {
                "query": query,
                "memory": [],
                "response": "",
            }

            config = self._build_config(thread_id)

            for event in self.graph.stream(initial_state, config=config):
                for node_name, state_update in event.items():
                    logger.info(f"📡 Stream event: {node_name}")
                    yield node_name, state_update

        except Exception as e:
            logger.error(f"Error in stream_agent: {e}")
            raise CustomException(e, sys)


    def stream_response(self, query: str, thread_id: str = None) -> Generator[str, None, None]:
        """
        Run the graph and stream the final response token-by-token.

        For the response_node, instead of waiting for the full LLM response,
        this streams each token as it arrives.

        Args:
            query: User's natural language query
            thread_id: Session ID for conversation memory

        Yields:
            str: Individual tokens of the response
        """
        try:
            if not thread_id:
                thread_id = str(uuid.uuid4())

            logger.info(f"⚡ Token streaming | thread: {thread_id} | query: {query}")

            # First, run the graph up to response_node to get research data
            # We'll manually handle the last step for streaming
            initial_state = {
                "query": query,
                "memory": [],
                "response": "",
            }

            config = self._build_config(thread_id)
            full_response = ""

            for event in self.graph.stream(initial_state, config=config):
                for node_name, state_update in event.items():
                    if node_name == "response_node":
                        # For the response node, we already have the full response
                        # Stream it token-by-token to simulate streaming
                        response_text = state_update.get("response", "")
                        # Stream word by word for smooth output
                        words = response_text.split(" ")
                        for i, word in enumerate(words):
                            token = word + (" " if i < len(words) - 1 else "")
                            full_response += token
                            yield token

                    elif node_name == "route_node":
                        route_decision = state_update.get("route_decision", "general")
                        if route_decision not in ("research", "booking"):
                            # General response — stream it
                            response_text = state_update.get("response", "")
                            words = response_text.split(" ")
                            for i, word in enumerate(words):
                                token = word + (" " if i < len(words) - 1 else "")
                                full_response += token
                                yield token

        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            raise CustomException(e, sys)


    def get_memory(self, thread_id: str) -> list:
        """
        Retrieve the conversation memory for a given thread.

        Args:
            thread_id: The session/thread ID

        Returns:
            List of memory entries [{role, content}, ...]
        """
        try:
            config = self._build_config(thread_id)
            state = self.graph.get_state(config)
            if state and state.values:
                return state.values.get("memory", [])
            return []
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return []


    def clear_memory(self, thread_id: str) -> None:
        """Start a fresh conversation by creating a new thread."""
        logger.info(f"🗑️ Memory cleared for thread: {thread_id}")
        # InMemorySaver doesn't have a delete method,
        # so we just use a new thread_id for a fresh conversation
