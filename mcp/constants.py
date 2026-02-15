from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict, NotRequired
import operator


class AgentState(TypedDict):
    """
    State schema for the Flight Search Agent.
    
    memory uses Annotated[..., operator.add] so each call can return
    memory: [new_entry] and it gets APPENDED (not replaced).
    """
    query: str
    memory: Annotated[List[Dict[str, str]], operator.add]
    response: NotRequired[str]
    search_params: NotRequired[Dict[str, Any]]
    ranked_flights: NotRequired[List[Dict[str, Any]]]
