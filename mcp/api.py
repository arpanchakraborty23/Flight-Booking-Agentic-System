import os
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from fastmcp import FastMCP

# MCP-internal imports
from utils.logger import setup_logger


# Import service classes from tools
from tools.booking import BookingService
from tools.search import ResearchAgent

load_dotenv()

logger = setup_logger(name="mcp_flight_booking_agent")


mcp = FastMCP(
    name="flight_booking_agent",
    version="0.1.0",
)

# Initialize service instances
booking_service = BookingService()



@mcp.tool(
    name="create_booking",
    description="Create a flight booking and store in database"
)
def create_booking(
    passenger_name: str,
    passenger_email: str,
    flight_number: str,
    airline: str,
    departure_city: str,
    arrival_city: str,
    departure_date: str,
    departure_time: str,
    arrival_time: str,
    price: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
) -> Dict[str, Any]:
    """Create a flight booking and store in MongoDB or memory."""
    return booking_service.create_booking(
        passenger_name=passenger_name,
        passenger_email=passenger_email,
        flight_number=flight_number,
        airline=airline,
        departure_city=departure_city,
        arrival_city=arrival_city,
        departure_date=departure_date,
        departure_time=departure_time,
        arrival_time=arrival_time,
        price=price,
        adults=adults,
        children=children,
        infants=infants,
    )


@mcp.tool(
    name="get_booking",
    description="Retrieve booking details by booking ID"
)
def get_booking(booking_id: str) -> Dict[str, Any]:
    """Get booking details by booking ID."""
    booking = booking_service.get_booking(booking_id)
    if booking:
        return {
            "success": True,
            "booking": booking,
        }
    return {
        "success": False,
        "message": f"Booking {booking_id} not found",
    }


@mcp.tool(
    name="list_bookings",
    description="List all bookings, optionally filtered by email"
)
def list_bookings(
    email: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """List bookings with optional email filter."""
    bookings = booking_service.list_bookings(email=email, limit=limit)
    return {
        "success": True,
        "count": len(bookings),
        "bookings": bookings,
    }


@mcp.tool(
    name="cancel_booking",
    description="Cancel a flight booking"
)
def cancel_booking(
    booking_id: str,
    reason: str = "Customer requested cancellation"
) -> Dict[str, Any]:
    """Cancel a booking."""
    return booking_service.cancel_booking(booking_id=booking_id, reason=reason)


@mcp.tool(
    name="search_flights",
    description="Search for flights based on user query"
)
def search_flights_tool(
    query: str,
    top_k: Optional[int] = 5,
    rank_results: Optional[bool] = True
) -> Dict[str, Any]:
    """Search for flights based on user query."""
    try:
        # Initialize LLM
        from langchain_mistralai import ChatMistralAI
        llm = ChatMistralAI(model_name="mistral-large-latest", api_key=os.getenv("MISTRAL_API_KEY"))
        
        # Initialize research agent
        agent = ResearchAgent(llm=llm)
        
        # Create state with query
        state: AgentState = {
            "query": query,
            "memory": []
        }
        
        # Run research
        result = agent.research(state)
        
        # Extract and limit results
        ranked_flights = result.get("ranked_flights", [])
        if top_k:
            ranked_flights = ranked_flights[:top_k]
        
        return {
            "search_params": result.get("search_params", {}),
            "ranked_flights": ranked_flights,
            "response": result.get("response", "Flights found successfully.")
        }
        
    except Exception as e:
        logger.error(f"Search agent failed: {e}")
        return {
            "search_params": {},
            "ranked_flights": [],
            "response": "Sorry, I encountered an error while searching for flights. Please try again with your travel details."
        }


if __name__ == "__main__":

    mcp.run(transport="streamable-http", host="0.0.0.0", port=10000)
