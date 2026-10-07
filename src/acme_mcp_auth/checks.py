"""Per-tool authorization check (403 layer)."""

from fastmcp.exceptions import AuthorizationError
from fastmcp.server.auth import AuthCheck, AuthContext
from fastmcp.tools import Tool

from .config import McpAuthSettings


def tool_in_tools_claim(settings: McpAuthSettings) -> AuthCheck:
    """Return an :class:`AuthCheck` that permits only tools in the token's ``tools`` claim.

    * Non-``Tool`` components (resources, prompts) are denied by default;
      set ``allow_non_tool_components = True`` to let them through.
    * If no token is present the check fails closed.
    """

    def check(ctx: AuthContext) -> bool:
        if ctx.token is None:
            raise AuthorizationError("Authentication required")

        # For non-tool components, apply the opt-in gate.
        if not isinstance(ctx.component, Tool):
            if settings.allow_non_tool_components:
                return True
            raise AuthorizationError(
                f"Component type {type(ctx.component).__name__} is not allowed"
            )

        granted: list[str] = ctx.token.claims.get(settings.tools_claim) or []
        if ctx.component.name not in granted:
            raise AuthorizationError(
                f"Tool {ctx.component.name!r} is not granted in the token's "
                f"'{settings.tools_claim}' claim"
            )
        return True

    return check
