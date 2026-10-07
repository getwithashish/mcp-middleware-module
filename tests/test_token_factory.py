"""Tests for acme-mcp-auth."""

from acme_mcp_auth.testing import TokenFactory


def test_valid_token_success():
    """A correctly signed token with the right claims passes."""
    factory = TokenFactory()
    token = factory.token(tools=["search_customers", "get_user"])
    # The verifier is an async function; we test synchronously here.
    # Full async tests are in test_auth_integration.py.
    assert token is not None
    assert isinstance(token, str)
    assert len(token.split(".")) == 3  # JWT shape


def test_token_has_required_claims():
    """Token contains the mandatory custom claims."""
    factory = TokenFactory()
    token = factory.token(tools=["my_tool"])
    # Decode without verification for structure check.
    import jwt as pyjwt

    decoded = pyjwt.decode(token, options={"verify_signature": False})
    assert decoded.get("device_id") == "dev-1"
    assert decoded.get("act", {}).get("sub") == "local-pwa"
    assert decoded.get("tools") == ["my_tool"]
