# MCP Flight Booking Server

Self-contained MCP (Model Context Protocol) server for flight search and booking operations. No dependencies on the backend folder - fully independent microservice.

## Features

### 🔍 Search Tool (`search_agent`)
- Extract flight search parameters using LLM
- Query Amadeus Flight Offers API
- Rank flights based on price, duration, and convenience
- Convert prices from EUR to INR

### 📅 Booking Tool (`booking_agent`)
- Create flight bookings with passenger details
- Store bookings in MongoDB (or in-memory fallback)
- Retrieve booking details by ID
- List bookings (with optional email filter)
- Cancel bookings with reason tracking

## Installation

```bash
pip install -r mcp/requirements.txt
```

### Optional: MongoDB Setup

For persistent storage, set up MongoDB:

```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally from https://www.mongodb.com/try/download/community
```

## Configuration

Create `.env` file in the `mcp/` folder:

```env
# Amadeus API (for flight search)
Amadeus_API_Key=your_amadeus_key
Amadeus_API_Secret=your_amadeus_secret

# MongoDB (optional - defaults to localhost:27017)
MONGODB_URI=mongodb://localhost:27017

# Mistral AI (for LLM)
MISTRAL_API_KEY=your_mistral_key
```

## Booking Tool Usage

### 1. Create a Booking

```python
from mcp.tools.booking import create_booking

result = create_booking(
    passenger_name="John Doe",
    passenger_email="john@example.com",
    flight_number="AI123",
    airline="Air India",
    departure_city="DEL",
    arrival_city="BOM",
    departure_date="2026-03-15",
    departure_time="10:30",
    arrival_time="12:30",
    price="₹5,430",
    adults=1,
    children=0,
    infants=0,
)
# Returns: {"success": True, "booking_id": "BK3A7F8E9C", ...}
```

### 2. Get Booking Details

```python
from mcp.tools.booking import get_booking

booking = get_booking("BK3A7F8E9C")
# Returns: {"success": True, "booking": {...}}
```

### 3. List All Bookings

```python
from mcp.tools.booking import list_bookings

# Get all bookings
all_bookings = list_bookings()

# Get bookings for a specific email
email_bookings = list_bookings(email="john@example.com", limit=5)
```

### 4. Cancel a Booking

```python
from mcp.tools.booking import cancel_booking

result = cancel_booking(
    booking_id="BK3A7F8E9C",
    reason="Changed travel plans"
)
# Returns: {"success": True, "booking_id": "BK3A7F8E9C", ...}
```

## Database Schema

### MongoDB Collection: `bookings`

```json
{
  "booking_id": "BK3A7F8E9C",
  "passenger": {
    "name": "John Doe",
    "email": "john@example.com"
  },
  "flight": {
    "number": "AI123",
    "airline": "Air India",
    "departure_city": "DEL",
    "arrival_city": "BOM",
    "departure_date": "2026-03-15",
    "departure_time": "10:30",
    "arrival_time": "12:30"
  },
  "passengers": {
    "adults": 1,
    "children": 0,
    "infants": 0
  },
  "pricing": {
    "total_price": "₹5,430",
    "currency": "INR"
  },
  "status": "CONFIRMED",
  "created_at": "2026-02-15T12:00:00",
  "updated_at": "2026-02-15T12:00:00"
}
```

## Storage Modes

1. **MongoDB Mode** (Production)
   - Persistent storage
   - Requires `MONGODB_URI` env variable
   - Auto-fallback if MongoDB unavailable

2. **In-Memory Mode** (Development)
   - No dependencies
   - Data lost on restart
   - Useful for testing

## Project Structure

```
mcp/
├── __init__.py              # Package init
├── constants.py             # Data types (AgentState)
├── logger.py               # Logging setup
├── exception.py            # Error handling
├── prompts.py              # LLM prompts
├── requirements.txt        # Dependencies
├── .env                    # Configuration
├── tools/
│   ├── __init__.py
│   ├── search.py           # Flight search tool
│   └── booking.py          # Flight booking tool
└── utils/
    ├── __init__.py
    ├── logger.py           # Logging utilities
    └── exception.py        # Exception utilities
```

## Development

All tools are self-contained with no backend folder dependencies:

- ✅ No imports from `backend/`
- ✅ Self-contained logging, exceptions, and prompts
- ✅ Fallback to in-memory storage when MongoDB unavailable
- ✅ Error handling with MCPException

## License

MIT
