"""JWT verification with custom claim checks (401 layer)."""

import logging
from typing import Any, Optional

from fastmcp.server.auth import AccessToken
from fastmcp.server.auth.providers.jwt import JWTVerifier

from .config import McpAuthSettings

log = logging.getLogger("acme_mcp_auth")


class ScopedToolTokenVerifier(JWTVerifier):
    """Verify a Keycloak-issued JWT and enforce custom claim rules.

    Delegates signature, issuer, audience, expiry, and scope to
    :class:`fastmcp.server.auth.providers.jwt.JWTVerifier`, then adds:

    * ``device_id`` claim present
    * ``acr`` in allowed list (if configured)
    * ``act.sub`` matches expected actor (if configured)
    * ``tools`` claim is a list of strings
    * Token lifetime (``exp - iat``) does not exceed *max_token_lifetime_s*

    Failures return ``None`` (401), not an exception.
    """

    def __init__(self, settings: McpAuthSettings) -> None:
        key_args: dict = (
            {"public_key": settings.public_key}
            if settings.public_key
            else {"jwks_uri": settings.resolved_jwks_uri}
        )
        super().__init__(
            **key_args,
            issuer=settings.issuer,
            audience=settings.audience,
            algorithm=settings.algorithm,
            required_scopes=settings.required_scopes or None,
        )
        self._s = settings

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify *token* and return an :class:`AccessToken` or ``None``."""
        access: Optional[AccessToken] = await super().verify_token(token)
        if access is None:
            return None

        claims = access.claims
        settings = self._s

        # ── device_id ─────────────────────────────────────────────────
        if not claims.get(settings.device_claim):
            log.warning("token rejected: missing device_id sub=%s", claims.get("sub"))
            return None

        # ── acr ───────────────────────────────────────────────────────
        if settings.allowed_acr and claims.get("acr") not in settings.allowed_acr:
            log.warning(
                "token rejected: acr %r not in %s sub=%s",
                claims.get("acr"),
                settings.allowed_acr,
                claims.get("sub"),
            )
            return None

        # ── actor ─────────────────────────────────────────────────────
        if settings.expected_actor is not None:
            actual_actor = (claims.get("act") or {}).get("sub")
            if actual_actor != settings.expected_actor:
                log.warning(
                    "token rejected: unexpected actor %r (expected %r) sub=%s",
                    actual_actor,
                    settings.expected_actor,
                    claims.get("sub"),
                )
                return None

        # ── tools claim ───────────────────────────────────────────────
        tools = claims.get(settings.tools_claim)
        if not isinstance(tools, list) or not all(isinstance(t, str) for t in tools):
            log.warning(
                "token rejected: tools claim missing or malformed sub=%s",
                claims.get("sub"),
            )
            return None

        # ── max token lifetime ────────────────────────────────────────
        iat, exp = claims.get("iat"), claims.get("exp")
        if not iat or not exp or exp - iat > settings.max_token_lifetime_s + settings.clock_skew_s:
            log.warning(
                "token rejected: lifetime exceeds %ss sub=%s",
                settings.max_token_lifetime_s,
                claims.get("sub"),
            )
            return None

        return access
