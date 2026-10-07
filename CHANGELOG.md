# Changelog

## 0.1.0 (2026-10-07)

- Initial release.
- `McpAuth` / `McpAuthSettings` entry point for FastMCP servers.
- `ScopedToolTokenVerifier`: JWT signature, issuer, audience, expiry, scope, plus
  custom claim checks (device_id, acr, actor, max token lifetime).
- `tool_in_tools_claim` check: returns 403 for tools not listed in the token's `tools` claim.
- `AuditMiddleware`: logs every tool call with sub, device_id, jti, outcome and duration.
- `TokenFactory` for testing without Keycloak.