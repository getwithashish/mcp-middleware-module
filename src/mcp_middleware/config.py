"""Environment-driven settings for mcp-middleware."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class McpAuthSettings(BaseSettings):
    """Settings loaded from environment variables with ``MCP_AUTH_`` prefix.

    Usage
    -----
    >>> from mcp_middleware import McpAuthSettings
    >>> settings = McpAuthSettings()  # reads from environment / .env
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_AUTH_", env_file=".env", extra="ignore"
    )

    # ── Token validation ──────────────────────────────────────────────
    issuer: str
    """Keycloak issuer URL, e.g. ``https://kc.example.com/realms/acme``."""

    audience: str
    """Token audience — ``"remote-mcp"`` or ``"local-tool-exec"``."""

    jwks_uri: str | None = None
    """JWKS endpoint; derived from *issuer* if not set:
    ``<issuer>/protocol/openid-connect/certs``."""

    public_key: str | None = None
    """Inline RSA public key (PEM) — for tests only, override *jwks_uri*."""

    algorithm: str = "RS256"
    """JWT signing algorithm."""

    # ── Scope / claim checks ──────────────────────────────────────────
    required_scopes: list[str] = []
    """List of required OAuth2 scopes (e.g. ``[\"mcp.tools\"]``)."""

    allowed_acr: list[str] = []
    """Allowed Authentication Context Reference values. Empty = skip check."""

    expected_actor: str | None = "local-pwa"
    """Expected ``act.sub`` value in the token. ``None`` = skip check."""

    tools_claim: str = "tools"
    """Claim name that holds the list of granted tool names."""

    device_claim: str = "device_id"
    """Claim name that holds the device identifier."""

    # ── Time / tolerance ──────────────────────────────────────────────
    max_token_lifetime_s: int = 300
    """Max seconds between ``iat`` and ``exp`` (defence in depth)."""

    clock_skew_s: int = 30
    """Allowed clock skew in seconds."""

    # ── Behaviour ─────────────────────────────────────────────────────
    allow_non_tool_components: bool = False
    """Allow resources/prompts even when the token has no ``tools`` claim
    for them. ``False`` => fail closed for all component types."""

    # ── Derived ───────────────────────────────────────────────────────
    @property
    def resolved_jwks_uri(self) -> str:
        """JWKS URI derived from *issuer* when *jwks_uri* is not explicitly set."""
        return self.jwks_uri or (
            f"{self.issuer.rstrip('/')}/protocol/openid-connect/certs"
        )
