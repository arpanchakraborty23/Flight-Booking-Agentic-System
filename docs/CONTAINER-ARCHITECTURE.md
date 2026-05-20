# Container Architecture Summary

## Service Overview

All services run in **separate, independent containers** with clear separation of concerns:

```
┌─[ Docker Compose Network: flight-booking-network ]────────────────────┐
│                                                                       │
│  ┌─────────────────┐        ┌─────────────────┐                      │
│  │  Frontend API   │◄──────►│  Voice Agent    │                      │
│  │  (Port 8000)    │        │  (Port 8081)    │                      │
│  └─────────────────┘        └─────────────────┘                      │
│        │  ▲                        │  ▲                                 │
│        │  │ LiveKit UI            │  │ LiveKit WebSocket              │
│        ▼  │                       ▼  │                                 │
│  ┌─────────────────┐        ┌─────────────────┐                      │
│  │  planner-agent  │        │   mcp-server    │                      │
│  │  (Port 8082)    │        │  (Port 8083)    │                      │
│  └─────────────────┘        └─────────────────┘                      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Service Details

### 1. Frontend API (Port 8000)
- **Container**: `frontend-api`
- **Purpose**: Serves web UI and handles LiveKit connections
- **Key Features**:
  - LiveKit room management
  - Voice agent integration
  - Flight search UI
  - Template rendering
- **Environment**:
  - `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` 
  - `LIVEKIT_URL` (WebSocket URL)
  - Service URLs for internal communication

### 2. Voice Agent (Port 8081)
- **Container**: `voice-agent`
- **Purpose**: LiveKit voice interactions
- **Key Features**:
  - Real-time voice processing
  - VAD (Voice Activity Detection)
  - Multi-language support (English, Bengali, Hindi)
  - MongoDB/Redis session management
- **Environment**:
  - LiveKit credentials
  - Database connection strings

### 3. Planner Agent (Port 8082)
- **Container**: `planner-agent`
- **Purpose**: Route planning and flight search coordination
- **Key Features**:
  - Multi-LLM support (OpenAI, Anthropic, Mistral)
  - Flight routing logic
  - Agent orchestration
- **Environment**:
  - Multiple LLM API keys

### 4. MCP Server (Port 8083)
- **Container**: `mcp-server`
- **Purpose**: MCP protocol server
- **Key Features**:
  - Tool calling interface
  - Amadeus API integration
  - Flight data retrieval
- **Environment**:
  - Amadeus API credentials
  - Mistral API key

## LiveKit Integration

The **Frontend API** connects to LiveKit UI:

1. **Room Creation**: Frontend creates LiveKit rooms
2. **Token Generation**: Uses LiveKit API key/secret
3. **WebSocket Connection**: Connects to `LIVEKIT_URL`
4. **Voice Agent**: Joins room as participant
5. **Real-time Audio**: Bidirectional streaming

### LiveKit UI Flow

```
User Browser (Port 8000)
    │
    ├─► LiveKit JavaScript SDK
    │
    ├─► Connects to LIVEKIT_URL
    │
    └─► Joins room with token
        │
        └─► voice-agent (Port 8081) joins as AI participant
```

## Deployment Commands

```bash
# Build all containers
docker-compose build

# Run all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f frontend-api
docker-compose logs -f voice-agent
```

## Testing LiveKit Connection

1. **Access UI**: http://localhost:8000
2. **Create/connect to room**
3. **Grant microphone permissions**
4. **Start voice conversation**
5. **Monitor logs**:
   ```bash
   docker-compose logs -f voice-agent
   ```

## API Health Checks

- Frontend API: http://localhost:8000/health
- Voice Agent: http://localhost:8081/health
- Planner Agent: http://localhost:8082/health
- MCP Server: http://localhost:8083/health

## Network Communication

All services communicate through Docker's internal DNS:
- `http://frontend-api:8000`
- `http://voice-agent:8081`
- `http://planner-agent:8082`
- `http://mcp-server:8083`
