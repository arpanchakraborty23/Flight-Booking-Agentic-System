# ✈️ Travel Agent System - Custom Travel Planning from Company Catalog

An AI-powered travel planning system that provides custom travel booking experiences through multi-modal interfaces (voice and web). The system leverages agentic AI to search flights, plan itineraries, and assist users through natural conversations.

![Python](https://img.shields.io/badge/Python-3.14+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.129+-green?logo=fastapi)
![LiveKit](https://img.shields.io/badge/LiveKit-Voice_AI-orange)
![React](https://img.shields.io/badge/React-19+-blue?logo=react)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)

---

## 🎯 Overview

This Travel Agent System is a comprehensive AI-powered platform that enables users to book custom travel through natural conversations. The system combines:

- **Voice Interaction**: Real-time voice conversations using LiveKit AI
- **Web Interface**: Modern React-based UI for visual interactions
- **Agent Orchestration**: Multiple specialized AI agents working together
- **Flight Search**: Integration with Amadeus API for real-time flight data
- **Multi-language Support**: English, Bengali, and Hindi language capabilities

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    User Browser / Web Interface                         │
│                          (Port 8000:3000)                               │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               │ HTTP / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Frontend API Service                               │
│                    (Flask/FastAPI - Containerized)                      │
│                                                                         │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐      │
│  │  Web UI    │  │LiveKit   │  │Planner   │  │   Voice Agent  │      │
│  │  Routes    │◄─│Session   │─►│Agent API │◄─│   Integration  │      │
│  │            │  │Manager   │  │(Port 8082)│  │(LiveKit WS)    │      │
│  └────────────┘  └──────────┘  └──────────┘  └────────────────┘      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐     ┌──────────────┐      ┌──────────────┐
│  Voice Agent  │     │  Planner Agent │      │   MCP Server │
│  (Port 8081)  │     │  (Port 8082)   │      │  (Port 8083) │
│               │     │                │      │              │
│ LiveKit Agent │     │ LangGraph      │      │ Amadeus API  │
│ VAD Support   │     │ Multi-LLM      │      │ Integration  │
│ MongoDB/Redis │     │ Flight Routing │      │ Tool Calls   │
└───────────────┘     └──────────────┘      └──────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌─────────┴─────────┐
                    ▼                   ▼
          ┌──────────────┐    ┌─────────────┐
          │  MongoDB     │    │   Redis     │
          │  (Sessions)  │    │  (Cache)    │
          └──────────────┘    └─────────────┘
```

### Component Responsibilities

**Frontend API (Port 8000)**
- Serves React/Next.js web application
- Manages LiveKit room connections and tokens
- Routes requests to appropriate backend services
- Integrates all agent services into unified interface

**Voice Agent (Port 8081)**
- Handles real-time voice interactions via LiveKit
- Voice Activity Detection (VAD) for natural conversations
- Multi-language support (English, Bengali, Hindi)
- Session management with MongoDB/Redis

**Planner Agent (Port 8082)**
- Flight search and itinerary planning
- Routes user queries to appropriate services
- Multi-LLM support (OpenAI, Anthropic, Mistral)
- Agent orchestration and workflow management

**MCP Server (Port 8083)**
- Provides tool-calling interface
- Integrates with Amadeus API for flight data
- Handles real-time flight search queries
- Converts prices (EUR → INR)

---

## ✨ Key Features

### 🎤 Multi-Modal Interaction
- **Voice**: Natural conversations through LiveKit AI
- **Web UI**: Modern React interface with real-time updates
- **Chat**: Text-based interaction support

### 🧠 Intelligent Agent System
- **Query Routing**: Automatically classifies and routes user intent
- **Flight Search**: Real-time flight data from Amadeus API
- **Itinerary Planning**: Custom travel planning based on preferences
- **Conversation Memory**: Maintains context across interactions

### 🌍 Multi-Language Support
- English
- Bengali
- Hindi

### 📊 Comprehensive Search
- Real-time flight availability
- Price comparison
- Route optimization
- Travel time calculations

### 🎛️ Customization
- Company catalog integration
- Custom branding support
- Configurable UI themes
- Agent behavior customization

---

## 🚀 Technology Stack

| Category | Technology |
|----------|------------|
| **Frontend** | React 19, Next.js 15, TypeScript |
| **Backend** | Python 3.14+, FastAPI, Flask |
| **Voice AI** | LiveKit Agents, VAD, WebRTC |
| **Agent Framework** | LangGraph, LangChain |
| **LLMs** | OpenAI GPT, Anthropic Claude, Mistral AI |
| **API Integration** | Amadeus Flight API |
| **Database** | MongoDB, Redis |
| **Observability** | Langfuse, Logging |
| **Deployment** | Docker, Docker Compose, AWS |
| **Styling** | Tailwind CSS, shadcn/ui |

---

## 📦 Prerequisites

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **Git**
- **API Keys** (see Configuration section)

---

## 🛠️ Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/arpanchakraborty23/Flight-Booking-Agentic-System.git
cd Flight-Booking-Agentic-System
```

### 2. Create Environment File

```bash
cp .env.example .env
```

### 3. Configure API Keys

Edit `.env` file with your API keys:

```env
# Amadeus Flight API
Amadeus_API_Key=your_amadeus_key
Amadeus_API_Secret=your_amadeus_secret

# Mistral AI (Planner Agent)
MISTRAL_API_KEY=your_mistral_key

# OpenAI API (Planner Agent)
OPENAI_API_KEY=your_openai_key

# Anthropic API (Planner Agent)
ANTHROPIC_API_KEY=your_anthropic_key

# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret

# Database (Optional - for production)
MONGODB_URI=mongodb://mongo:27017/travel-agent
REDIS_URL=redis://redis:6379

# Langfuse Observability (Optional)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

### 4. Build and Run

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 5. Access the Application

- **Web UI**: http://localhost:8000
- **Voice Agent**: http://localhost:8081
- **Planner Agent Health**: http://localhost:8082/health
- **MCP Server Health**: http://localhost:8083/health

---

## 📖 Detailed Component Setup

### Frontend Development

```bash
cd frontend
pnpm install
pnpm dev
```

Access: http://localhost:3000

### Voice Agent Development

```bash
cd voice_agent
uv sync
uv run python src/agent.py dev
```

### Planner Agent Development

```bash
cd planner_agent
uv sync
uv run python app.py
```

---

## 🌍 Development Commands

### GitHub Actions

```bash
# Run tests locally
act -j test

# Build containers
act -j build

# Deploy (requires AWS configuration)
act -j deploy
```

### Database Management

```bash
# MongoDB Shell
docker exec -it mongo mongosh

# Redis CLI
docker exec -it redis redis-cli
```

### Testing

```bash
# Test API endpoints
curl http://localhost:8000/health

# Test voice agent
curl http://localhost:8081/health

# Test planner agent
curl http://localhost:8082/health

# Test MCP server
curl http://localhost:8083/health
```

---

## 📡 API Endpoints

### Frontend API (Port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main web interface |
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Send message to agent |
| `GET` | `/api/stream` | Stream agent responses |
| `GET` | `/api/memory` | Get conversation history |
| `GET` | `/api/new-session` | Create new session |

### Voice Agent (Port 8081)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/connect` | Connect to LiveKit room |
| `POST` | `/start` | Start voice session |

### Planner Agent (Port 8082)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Query planner agent |
| `POST` | `/search` | Search flights |
| `POST` | `/plan` | Plan itinerary |

### MCP Server (Port 8083)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/tools` | Execute tool calls |
| `POST` | `/search/flights` | Search Amadeus flights |

---

## 🔧 Configuration

### Web UI Configuration

Edit `frontend/app-config.ts`:

```typescript
export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'Your Travel Company',
  pageTitle: 'Custom Travel Booking',
  pageDescription: 'Plan your custom travel with AI assistance',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/your-logo.svg',
  accent: '#002cf2',
  accentDark: '#1fd5f9',
  startButtonText: 'Start Planning',

  audioVisualizerType: 'bar',
  agentName: 'travel-assistant',
};
```

### Voice Agent Configuration

Edit `voice_agent/.env`:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-url
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret

# Language Support
DEFAULT_LANGUAGE=en  # en, bn, hi

# Features
ENABLE_VAD=true
ENABLE_NOISE_CANCELLATION=true
```

### Planner Agent Configuration

Edit `planner_agent/.env`:

```env
# LLM Configuration
PRIMARY_LLM=mistral  # mistral, openai, anthropic
MISTRAL_API_KEY=your_mistral_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Amadeus API
Amadeus_API_Key=your_amadeus_key
Amadeus_API_Secret=your_amadeus_secret

# Advanced Settings
MEMORY_TYPE=inmemory  # inmemory, sqlite, postgres
ENABLE_LANGFUSE=true
```

---

## 🚀 Deployment

### AWS Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete AWS deployment guide.

Quick steps:

```bash
# Build containers
docker-compose build

# Push to ECR (Amazon Container Registry)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag images
docker tag voice-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/travel-agent:voice-latest
docker tag planner-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/travel-agent:planner-latest

# Push to registry
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/travel-agent:voice-latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/travel-agent:planner-latest
```

### Local Production

```bash
# Use production docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or build individually
docker build -t travel-frontend .
docker build -t travel-voice ./voice_agent
docker build -t travel-planner ./planner_agent
docker build -t travel-mcp ./mcp
```

---

## 📚 Project Structure

```
Flight-Booking-Agentic-System/
├── frontend/                      # React/Next.js web interface
│   ├── app/                       # Next.js app router
│   ├── components/                # Reusable UI components
│   ├── hooks/                     # Custom React hooks
│   ├── lib/                       # Utility functions
│   └── app-config.ts             # Application configuration
│
├── voice_agent/                   # LiveKit voice agent
│   ├── src/
│   │   └── agent.py              # Main voice agent logic
│   ├── pyproject.toml            # Python dependencies
│   └── .env.example              # Environment variables template
│
├── planner_agent/                 # Flight planning agent
│   ├── backend/
│   │   ├── agent/                # Agent orchestration
│   │   ├── nodes/                # LangGraph nodes
│   │   └── prompts/              # LLM prompts
│   ├── constants/                # Configuration constants
│   ├── utils/                    # Utility functions
│   └── app.py                    # FastAPI server
│
├── mcp/                           # MCP server for tool calling
│   ├── tools/                    # Available tools
│   ├── utils/                    # Utility modules
│   └── Dockerfile                # Container image
│
├── docs/                         # Documentation
│   ├── CONTAINER-ARCHITECTURE.md # Container architecture overview
│   └── DEPLOYMENT.md            # AWS deployment guide
│
├── docker-compose.yml            # Main compose configuration
├── Dockerfile                    # Frontend API container
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

---

## 🔍 Troubleshooting

### Common Issues

**Voice Agent Not Connecting**
```bash
# Check LiveKit credentials
docker exec voice-agent env | grep LIVEKIT

# Test WebSocket connection
curl -i -N \
  --header "Connection: Upgrade" \
  --header "Upgrade: websocket" \
  --header "Host: localhost:8081" \
  --header "Origin: http://localhost:8081" \
  http://localhost:8081/
```

**Planner Agent Fails**
```bash
# Check API keys
docker exec planner-agent env | grep API_KEY

# Test API call
curl -X POST http://localhost:8082/health
```

**MCP Server Issues**
```bash
# Check Amadeus API connectivity
docker exec mcp-server curl -I https://api.amadeus.com

# Test MCP tools
curl -X POST http://localhost:8083/health
```

**Container Won't Start**
```bash
# View detailed logs
docker-compose logs -f <service-name>

# Check container status
docker ps -a

# Clean and rebuild
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up -d
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variable
echo "DEBUG=true" >> .env

# Restart services
docker-compose restart

# Watch logs with debug info
docker-compose logs -f | grep DEBUG
```

---

## 📖 Additional Documentation

- [Component Architecture](docs/CONTAINER-ARCHITECTURE.md) - Detailed container architecture
- [AWS Deployment Guide](docs/DEPLOYMENT.md) - Complete deployment instructions
- [Voice Agent README](voice_agent/README.md) - Voice agent specific documentation
- [Planner Agent README](planner_agent/README.md) - Planner agent documentation
- [Frontend README](frontend/README.md) - Frontend development guide

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed for educational and development purposes.

---

## 🙏 Acknowledgments

- **LiveKit** for voice AI infrastructure
- **Amadeus** for flight data API
- **Mistral AI, OpenAI, Anthropic** for LLM capabilities
- **LangGraph/LangChain** for agent framework
- **Docker** for containerization

---

**Built with ❤️ for modern travel planning**

For questions or support, please open an issue in the repository.
