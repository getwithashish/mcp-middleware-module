"""Single entry point teams use to wire up auth."""

from dataclasses import dataclass, field
from typing import Any, List

from fastmcp.server.middleware import AuthMiddleware, Middleware

from .audit import AuditMiddleware
from .checks import tool_in_tools_claim
from .config import McpAuthSettings
from .verifier import ScopedToolTokenVerifier


@dataclass
class McpAuth:
    """Complete auth setup for a FastMCP server.

    Usage
    -----
    .. code-block:: python

        from fastmcp import FastMCP
        from mcp_middleware import McpAuth

        auth = McpAuth.from_env()

        mcp = FastMCP("my-server",
                      auth=auth.provider,
                      middleware=auth.middleware)
    """

    settings: McpAuthSettings
    provider: ScopedToolTokenVerifier = field(init=False)
    middleware: List[Middleware] = field(init=False)

    def __post_init__(self) -> None:
        self.provider = ScopedToolTokenVerifier(self.settings)
        self.middleware = [
            # Outermost: logs even authorisation denials.
            AuditMiddleware(self.settings.device_claim),
            # Per-tool authorisation check.
            AuthMiddleware(auth=tool_in_tools_claim(self.settings)),
        ]

    @classmethod
    def from_env(cls, **overrides: Any) -> "McpAuth":
        """Create ``McpAuth`` from environment variables (plus *overrides*).

        Override any field of :class:`McpAuthSettings` by keyword:

        .. code-block:: python

            auth = McpAuth.from_env(audience="remote-mcp")
        """
        return cls(McpAuthSettings(**overrides))
