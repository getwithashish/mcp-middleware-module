"""mcp-middleware: Keycloak scoped-token auth for FastMCP servers."""

from .config import McpAuthSettings
from .integration import McpAuth

__all__ = ["McpAuth", "McpAuthSettings"]
__version__ = "0.1.0"
