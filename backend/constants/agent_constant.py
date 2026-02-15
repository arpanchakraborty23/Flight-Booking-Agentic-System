import operator
from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict, NotRequired


class AgentState(TypedDict):
    """
    State schema for the Flight Booking Agent graph.

    memory uses Annotated[..., operator.add] so each node can return
    memory: [new_entry] and it gets APPENDED (not replaced).
    """
    query: str
    memory: Annotated[List[Dict[str, str]], operator.add]
    response: NotRequired[str]
    route_decision: NotRequired[str]
    search_params: NotRequired[Dict[str, Any]]
    ranked_flights: NotRequired[List[Dict[str, Any]]]
