# acme-mcp-auth

**Keycloak scoped-token authentication for FastMCP servers.**  
A shared Python package that enforces JWT-based, tool-scoped access so every
MCP server in your organisation uses the same auth contract.

---

## Contract

| Aspect | Behaviour |
|---|---|
| **Transport** | HTTP only. FastMCP skips auth in STDIO mode — a startup assertion should prevent production STDIO use. |
| **401** | Token missing, expired, wrong audience, missing `device_id`, wrong `act.sub`, or lifetime > 300 s → `invalid_token` error. |
| **403** | Token is valid but the called tool is not in the `tools` claim → `AuthorizationError` with the tool name. |
| **`tools/list`** | Returns only the tools the caller's token grants (hidden server-side). |
| **Resources / Prompts** | Denied by default (`allow_non_tool_components=False`). |
| **Audit log** | Every `tool_call` is logged (sub, device_id, jti, outcome, duration). No token or arguments are logged. |
| **Non-repudiation** | Audit records carry `jti` so a call can be traced to a specific token. |

> **Important:** tool names in the `tools` claim **must match** the FastMCP
> tool names exactly (case-sensitive). Use a naming convention like
> `crm.search_customers` and sync with Keycloak client roles.

---

## Usage

### Install

```bash
# From a private package index (recommended)
uv add acme-mcp-auth --index https://pypi.example.com/simple

# Or as a git dependency (quick start)
uv add "acme-mcp-auth @ git+ssh://git@github.com/getwithashish/acme-mcp-auth@v0.1.0"
```

### Wire it up

```python
from fastmcp import FastMCP
from acme_mcp_auth import McpAuth

auth = McpAuth.from_env()

mcp = FastMCP(
    "crm-tools",
    auth=auth.provider,          # token verification (401)
    middleware=auth.middleware,   # per-tool check + audit logging (403)
)

@mcp.tool
def search_customers(q: str) -> list[dict]:
    """Search the CRM."""
    return [{"id": 1, "name": "Acme Corp"}]

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
```

### Environment variables

Set these per server. Only `MCP_AUTH_ISSUER` and `MCP_AUTH_AUDIENCE` are
required; everything else has a safe default.

| Variable | Default | Description |
|---|---|---|
| `MCP_AUTH_ISSUER` | *(required)* | Keycloak issuer, e.g. `https://kc.example.com/realms/acme` |
| `MCP_AUTH_AUDIENCE` | *(required)* | `"remote-mcp"` or `"local-tool-exec"` |
| `MCP_AUTH_JWKS_URI` | `<issuer>/protocol/openid-connect/certs` | JWKS endpoint |
| `MCP_AUTH_PUBLIC_KEY` | — | RSA public key PEM (tests only) |
| `MCP_AUTH_ALGORITHM` | `RS256` | JWT signing algorithm |
| `MCP_AUTH_REQUIRED_SCOPES` | `[]` | Required OAuth2 scopes |
| `MCP_AUTH_ALLOWED_ACR` | `[]` | Allowed ACR values (empty = skip) |
| `MCP_AUTH_EXPECTED_ACTOR` | `local-pwa` | Expected `act.sub` (`null` = skip) |
| `MCP_AUTH_TOOLS_CLAIM` | `tools` | Claim with the granted tool list |
| `MCP_AUTH_DEVICE_CLAIM` | `device_id` | Claim with the device identifier |
| `MCP_AUTH_MAX_TOKEN_LIFETIME_S` | `300` | Max seconds between `iat` and `exp` |
| `MCP_AUTH_CLOCK_SKEW_S` | `30` | Allowed clock skew |
| `MCP_AUTH_ALLOW_NON_TOOL_COMPONENTS` | `false` | Allow resources/prompts |

---

## Testing without Keycloak

The package ships `TokenFactory` so teams can write integration tests without
a running Keycloak:

```python
from acme_mcp_auth.testing import TokenFactory

factory = TokenFactory()
auth = factory.auth()                          # McpAuth wired to test key
token = factory.token(tools=["search_customers"])

# The token can now be used to call the server under test.
```

Test cases we cover in this repository (and you should too):

- Valid token is accepted
- Wrong `aud` → rejected
- Missing `device_id` → rejected
- Wrong `act.sub` → rejected
- Lifetime > 300 s → rejected
- Calling a tool not in `tools` → 403
- `tools/list` shows only granted tools

---

## Sharing with teams

| Option | When to use | Install command |
|---|---|---|
| **Private index** (recommended) | Standard for several teams | `uv add acme-mcp-auth --index https://…/simple` |
| **Git tag** | Before an index exists | `uv add "acme-mcp-auth @ git+ssh://git@github.com/…@v0.1.0"` |

### CI publishing

Pushing a tag `vX.Y.Z` runs lint, tests and `uv build`, then publishes to the
package index. Nobody publishes from a laptop.

### Versioning (security contract)

| Change | Version bump |
|---|---|
| New check that could reject previously-passing tokens | **Major** |
| New optional settings | **Minor** |
| Fixes | **Patch** |

Consumers use a compatible-release range, e.g. `acme-mcp-auth~=1.2`. Enable
Renovate or Dependabot so security fixes reach every repo quickly.

### Code ownership

The `CODEOWNERS` file grants the platform/security team review over
`verifier.py` and `checks.py` — any change to the auth logic requires their
approval.

---

## Things to watch

1. **HTTP transport only** — FastMCP skips auth in STDIO mode. Assert at startup.
2. **Tool name matching** — names in the `tools` claim must match
   `component.name` exactly. Consider a CLI tool to print a server's registered
   names for cross-referencing against Keycloak client roles.
3. **Token passthrough** — a remote MCP server must not forward the incoming
   token to other services. Do its own token exchange if an outbound call is
   needed.
4. **Revocation delay** — device-status checks run only at token-exchange time.
   A revoked device keeps working for up to 300 s (the token lifetime). This is
   an accepted risk — document it.

---

## Development

```bash
git clone https://github.com/getwithashish/acme-mcp-auth.git
cd acme-mcp-auth
uv venv && source .venv/bin/activate
uv sync --all-extras

pytest -v
ruff check src tests
mypy src
```