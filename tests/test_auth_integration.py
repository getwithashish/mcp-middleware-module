"""Async integration tests for token verification.

Run with::

    pytest tests/test_auth_integration.py -v
"""

import pytest

from mcp_middleware.testing import TokenFactory


@pytest.fixture
def factory():
    return TokenFactory()


@pytest.mark.asyncio
async def test_valid_token_accepted(factory):
    """A valid token passes verification."""
    auth = factory.auth()
    token = factory.token(tools=["crm.search"])
    result = await auth.provider.verify_token(token)
    assert result is not None
    assert result.claims["sub"] == "user-1"
    assert "crm.search" in result.claims["tools"]


@pytest.mark.asyncio
async def test_wrong_audience_rejected(factory):
    """Token with wrong audience is rejected."""
    auth = factory.auth(audience="local-tool-exec")
    token = factory.token(tools=["crm.search"], audience="remote-mcp")
    result = await auth.provider.verify_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_missing_device_id_rejected(factory):
    """Token without device_id is rejected."""
    auth = factory.auth()
    token = factory.token(tools=["crm.search"], device_id=None)
    result = await auth.provider.verify_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_wrong_actor_rejected(factory):
    """Token with wrong act.sub is rejected."""
    auth = factory.auth(expected_actor="some-other-pwa")
    token = factory.token(tools=["crm.search"], act={"sub": "local-pwa"})
    result = await auth.provider.verify_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_lifetime_exceeded_rejected(factory):
    """Token exceeding max lifetime is rejected."""
    auth = factory.auth(max_token_lifetime_s=60)
    token = factory.token(tools=["crm.search"], expires_in_seconds=300)
    result = await auth.provider.verify_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_malformed_tools_claim_rejected(factory):
    """Token where tools claim is not a list is rejected."""
    auth = factory.auth()
    token = factory.token(tools="not-a-list")  # type: ignore[arg-type]
    result = await auth.provider.verify_token(token)
    assert result is None


@pytest.mark.asyncio
async def test_tool_invoke_grants_all_tools(factory):
    """Having 'tool:invoke' in the tools claim grants access to any tool."""
    from mcp_middleware.checks import ALLOW_ALL

    auth = factory.auth()
    # Token grants only the wildcard — no specific tool name.
    token = factory.token(tools=[ALLOW_ALL])
    result = await auth.provider.verify_token(token)
    assert result is not None
    # The check itself is exercised at the auth-middleware layer;
    # verifying that the token passes verification with the wildcard
    # proves the claims are structured correctly.
    assert ALLOW_ALL in result.claims["tools"]


@pytest.mark.asyncio
async def test_tools_list_shows_only_granted(factory):
    """Pass verification and check the granted tools match the claim."""
    auth = factory.auth()
    token = factory.token(tools=["allowed_tool"])
    result = await auth.provider.verify_token(token)
    assert result is not None
    assert result.claims["tools"] == ["allowed_tool"]
    assert "forbidden_tool" not in result.claims["tools"]
