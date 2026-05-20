# syntax=docker/dockerfile:1

# Dockerfile for Planner Agent
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy dependency files
COPY requirements.txt* ./
COPY pyproject.toml* ./

# Install Python dependencies
RUN if [ -f requirements.txt ]; then pip install -r requirements.txt; \
    elif [ -f pyproject.toml ]; then pip install -e .; \
    else pip install fastapi uvicorn langgraph langchain langchain-mistral langfuse python-dotenv httpx pydantic; fi

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Run the application
CMD ["python", "agent/main.py"]
