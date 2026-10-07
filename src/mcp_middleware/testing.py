"""Test helpers — produce valid tokens without a running Keycloak.

Usage
-----
.. code-block:: python

    from mcp_middleware.testing import TokenFactory

    factory = TokenFactory()
    auth = factory.auth()                     # McpAuth wired to the test key
    token = factory.token(tools=["my_tool"])  # signed JWT

    # Simulate a different audience:
    auth2 = factory.auth(audience="local-tool-exec")
    token2 = factory.token(tools=["my_tool"], audience="local-tool-exec")
"""

from fastmcp.server.auth.providers.jwt import RSAKeyPair

from .config import McpAuthSettings
from .integration import McpAuth

ISS = "https://test-issuer"
AUD = "remote-mcp"


class TokenFactory:
    """Mint test JWTs signed by an ephemeral RSA key pair.

    The default *audience* is ``"remote-mcp"``.  All tokens include:

    * ``device_id``
    * ``act.sub`` = ``"local-pwa"``
    * ``tools`` = the list you pass
    """

    def __init__(self, audience: str = AUD):
        self.kp = RSAKeyPair.generate()
        self.audience = audience

    def auth(self, **overrides: object) -> McpAuth:
        """Return an :class:`McpAuth` that verifies against the test key."""
        base: dict[str, object] = dict(
            issuer=ISS,
            audience=self.audience,
            public_key=self.kp.public_key,
        )
        base.update(overrides)
        return McpAuth(McpAuthSettings(**base))  # type: ignore[arg-type]

    def token(self, tools: list[str], **claims: object) -> str:
        """Return a signed JWT string.

        Parameters
        ----------
        tools:
            List of granted tool names (placed in the ``tools`` claim).
        claims:
            Additional claims to include (e.g. ``iat=…``, ``exp=…``).
        """
        base: dict = {
            "device_id": "dev-1",
            "act": {"sub": "local-pwa"},
            self.auth().settings.tools_claim: tools,
        }
        base.update(claims)
        return self.kp.create_token(
            subject="user-1",
            issuer=ISS,
            audience=self.audience,
            expires_in_seconds=300,
            additional_claims=base,
        )
