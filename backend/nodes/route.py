import sys
from typing import Dict
from constants.agent_constant import AgentState
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.logger import setup_logger
from utils.exception import CustomException
from backend.prompts import ROUTE_PROMPT

logger = setup_logger(name="routing")


class RouteAgent:
    """Route the user query to the correct sub-agent."""

    def __init__(self, llm) -> None:
        self.llm = llm
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt_template = ChatPromptTemplate.from_template(ROUTE_PROMPT)
        chain = prompt_template | self.llm | StrOutputParser()
        return chain

    def _format_memory(self, memory: list) -> str:
        """Format memory entries into a readable string for the LLM prompt."""
        if not memory:
            return "No previous conversation."

        formatted = []
        for entry in memory:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def run_route(self, state: AgentState) -> Dict:
        """Routing logic — returns state update for LangGraph."""
        try:
            user_query = state["query"]
            memory = state.get("memory", [])

            # Format memory for the prompt
            memory_str = self._format_memory(memory)

            result = self.chain.invoke({"query": user_query, "memory": memory_str})

            logger.info(f"Route result: {result}")

            # Determine route decision from LLM output
            result_lower = result.strip().lower()
            if "research" in result_lower:
                route_decision = "research"
            elif "booking" in result_lower:
                route_decision = "booking"
            else:
                route_decision = "general"

            return {
                "response": result.strip(),
                "route_decision": route_decision
            }

        except Exception as e:
            logger.error(f"Error in Routing: {e}")
            raise CustomException(e, sys)
