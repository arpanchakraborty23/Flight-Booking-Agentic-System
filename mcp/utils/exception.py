"""MCP Server Exception Handler - Self-contained error handling"""

import sys
import traceback
from typing import Any


class MCPException(Exception):
    """Base exception for MCP server"""
    
    def __init__(self, error: Any, sys_module: Any = None):
        """
        Initialize MCPException.
        
        Args:
            error: The original exception or error message
            sys_module: sys module (for compatibility)
        """
        self.error = error
        self.error_message = str(error)
        self.traceback = traceback.format_exc()
        
        super().__init__(self.error_message)
    
    def __str__(self) -> str:
        return f"MCPException: {self.error_message}\n{self.traceback}"
