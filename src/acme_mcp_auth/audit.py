"""Audit-logging middleware for FastMCP tool calls."""

import logging
import time

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware, MiddlewareContext

log = logging.getLogger("acme_mcp_auth.audit")


class AuditMiddleware(Middleware):
    """Log every tool call with sub, device_id, outcome and duration.

    Does **not** log the token or call arguments — only metadata.
    This middleware runs outermost so it also captures denials raised
    by inner middleware (e.g. authorisation failures).
    """

    def __init__(self, device_claim: str = "device_id") -> None:
        self.device_claim = device_claim

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next,
    ):
        tok = get_access_token()
        claims = tok.claims if tok else {}
        start = time.perf_counter()
        outcome = "error"

        try:
            result = await call_next(context)
            outcome = "ok"
            return result
        except Exception as exc:
            outcome = type(exc).__name__
            raise
        finally:
            log.info(
                "tool_call",
                extra={
                    "tool": context.message.name,
                    "sub": claims.get("sub"),
                    "device_id": claims.get(self.device_claim),
                    "jti": claims.get("jti"),
                    "outcome": outcome,
                    "ms": round((time.perf_counter() - start) * 1000, 1),
                },
            )
