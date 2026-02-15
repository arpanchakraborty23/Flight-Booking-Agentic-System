# MCP Flight Booking Server

Unified MCP (Model Context Protocol) server for flight search and booking operations. This server provides a centralized API with service classes for flight search and booking functionality.

## Features

### 🔍 Search Tool (`search_flights`)
- Extract flight search parameters using LLM
- Query Amadeus Flight Offers API
- Rank flights based on price, duration, and convenience
- Convert prices from EUR to INR
- Response with ranked flight options

### 📅 Booking Tools
- **create_booking**: Create flight bookings with passenger details
- **get_booking**: Retrieve booking details by ID
- **list_bookings**: List bookings (with optional email filter)
- **cancel_booking**: Cancel bookings with reason tracking

All bookings are stored in MongoDB with automatic fallback to in-memory storage.

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

#### create_booking
Create a flight booking with passenger details.

**Parameters:**
- `passenger_name` (str): Full name of passenger
- `passenger_email` (str): Email address
- `flight_number` (str): Flight number (e.g., "AI123")
- `airline` (str): Airline name
- `departure_city` (str): City code (e.g., "DEL")
- `arrival_city` (str): City code (e.g., "BOM")
- `departure_date` (str): Date in YYYY-MM-DD format
- `departure_time` (str): Time in HH:MM format
- `arrival_time` (str): Time in HH:MM format
- `price` (str): Price (e.g., "₹5,430")
- `adults` (int): Number of adults (default: 1)
- `children` (int): Number of children (default: 0)
- `infants` (int): Number of infants (default: 0)

**Returns:**
```json
{
  "success": true,
  "booking_id": "BK3A7F8E9C",
  "passenger_name": "John Doe",
  "flight_number": "AI123",
  "departure_date": "2026-03-15",
  "status": "CONFIRMED",
  "message": "Your booking is confirmed! Booking ID: BK3A7F8E9C..."
}
```

#### get_booking
Retrieve booking details by booking ID.

**Parameters:**
- `booking_id` (str): The booking ID to retrieve

**Returns:**
```json
{
  "success": true,
  "booking": {
    "booking_id": "BK3A7F8E9C",
    "passenger": { "name": "John Doe", "email": "john@example.com" },
    "flight": { ... },
    "status": "CONFIRMED"
  }
}
```

#### list_bookings
List bookings with optional email filtering.

**Parameters:**
- `email` (str, optional): Filter by passenger email
- `limit` (int, optional): Maximum results (default: 10)

**Returns:**
```json
{
  "success": true,
  "count": 3,
  "bookings": [ ... ]
}
```

#### cancel_booking
Cancel a booking by ID.

**Parameters:**
- `booking_id` (str): The booking ID to cancel
- `reason` (str, optional): Cancellation reason

**Returns:**
```json
{
  "success": true,
  "booking_id": "BK3A7F8E9C",
  "status": "CANCELLED",
  "message": "Booking BK3A7F8E9C has been cancelled."
}
```

### Search Tool

#### search_flights
Search for flights based on user query.

**Parameters:**
- `query` (str): Natural language query (e.g., "I want to fly from Delhi to Mumbai on March 15")
- `top_k` (int, optional): Number of top results (default: 5)
- `rank_results` (bool, optional): Whether to rank results (default: true)

**Returns:**
```json
{
  "search_params": {
    "origin": "DEL",
    "destination": "BOM",
    "departure_date": "2026-03-15",
    "adults": 1
  },
  "ranked_flights": [ ... ],
  "response": "Flights found successfully."
}
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
├── api.py                  # Central MCP server with tool registrations
├── constants.py            # Data types and configurations
├── prompts.py              # LLM prompts for search and ranking
├── requirements.txt        # Dependencies
├── .env                    # Environment configuration
├── README.md               # This file
├── tools/
│   ├── __init__.py         # Exports service classes
│   ├── search.py           # ResearchAgent class for flight search
│   └── booking.py          # BookingService class for bookings
└── utils/
    ├── __init__.py
    ├── logger.py           # Logging utilities
    └── exception.py        # MCPException for error handling
```

## Architecture

The MCP server uses a clean separation of concerns:

```
api.py (MCP Tool Registrations)
  ├─ @mcp.tool("search_flights")
  │   └─ ResearchAgent (from tools.search)
  ├─ @mcp.tool("create_booking")
  │   └─ BookingService (from tools.booking)
  ├─ @mcp.tool("get_booking")
  │   └─ BookingService
  ├─ @mcp.tool("list_bookings")
  │   └─ BookingService
  └─ @mcp.tool("cancel_booking")
      └─ BookingService
```

**Service Classes:**
- `ResearchAgent`: Handles Amadeus API integration and flight ranking
- `BookingService`: Manages booking storage (MongoDB or in-memory)

## Running the Server

### Start the MCP Server

```bash
cd mcp
python api.py
```

The server will start on `http://0.0.0.0:10000` by default.

### Configure Port and Host

You can customize the server settings via environment variables:

```bash
# Set custom host and port
export HOST=127.0.0.1
export PORT=8000
python api.py
```

### Using with MCP Clients

The MCP server exposes the following tools:
- `search_flights` - Search for flights
- `create_booking` - Create a new booking
- `get_booking` - Retrieve booking details
- `list_bookings` - List all bookings
- `cancel_booking` - Cancel a booking

Connect your MCP client to `http://localhost:10000` to access these tools.

## Error Handling

The server includes robust error handling:
- **MCPException**: Custom exception for MCP-specific errors
- **Automatic Fallback**: In-memory storage if MongoDB is unavailable
- **Token Management**: Automatic Amadeus token refresh
- **Price Conversion**: EUR to INR conversion with error recovery

## Development Features

- ✅ Clean service-based architecture
- ✅ No backend dependencies
- ✅ Self-contained logging and exception handling
- ✅ Graceful fallbacks for external services
- ✅ Comprehensive error messages

## License

MIT
