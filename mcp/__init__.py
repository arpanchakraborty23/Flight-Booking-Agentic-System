"""
MCP Flight Search Server - Standalone Package

This MCP server is completely independent with no external dependencies on other folders.
All required utilities, constants, prompts, and exception handling are self-contained.

Modules:
- constants.py: AgentState and configuration types
- logger.py: Self-contained logging setup
- exception.py: MCPException for error handling
- prompts.py: LLM prompts for flight search tasks
- api.py: FastAPI server (if needed)
- tools/search.py: FastMCP tool definitions
"""

__version__ = "0.1.0"
