import httpx
from authlib.jose import jwt
from dify_plugin.core.runtime import Session

from endpoints.helpers.storage import StorageCacheProvider


class OpenIDConnectDiscoveryProvider:
    def __init__(self, session: Session, issuer: str, audience: str, scope: str | None):
        # Set session
        self.session = session

        # Set storage cache
        self.storage_cache = StorageCacheProvider(session)

        # set issuer
        if not issuer:
            raise ValueError("issuer is required")
        self.issuer = issuer

        # set audience
        if not audience:
            raise ValueError("audience is required")
        self.audience = audience

        # Parse and set scopes
        self.scopes = scope.strip().split(" ") if (scope is not None and scope != "") else []

    def verify_access_token(self, token: str):
        try:
            jwk_set = self.__get_jwk_set()
        except Exception as e:
            raise Exception(f"Failed to get jwk set: {e}") from e
        try:
            claims = jwt.decode(token, jwk_set)
        except Exception as e:
            raise Exception(f"Failed to decode and validate token: {e}") from e
        try:
            claims.validate()
        except Exception as e:
            raise Exception(f"Failed to validate token: {e}") from e

        if claims.get("iss", None) != self.issuer:
            raise Exception("Issuer mismatch")
        if claims.get("aud", None) != self.audience:
            raise Exception("Audience mismatch")
        if len(self.scopes) > 0:
            scope = claims.get("scope", None) or claims.get("scp", None)
            scopes = scope.strip().split(" ") if (scope is not None and scope != "") else []
            constains_all = set(self.scopes).issubset(scopes)
            if not constains_all:
                raise Exception("Scope mismatch")

        return claims

    def __get_openid_configuration(self):
        with httpx.Client() as client:
            response = client.get(f"{self.issuer}/.well-known/openid-configuration")
            response.raise_for_status()
            return response.json()

    def __get_jwks_uri(self):
        config = self.__get_openid_configuration()
        return config.get("jwks_uri")

    def __get_jwk_set_from_jwks_uri(self):
        jwks_uri = self.__get_jwks_uri()
        with httpx.Client() as client:
            response = client.get(jwks_uri)
            response.raise_for_status()
            jwk_set = response.json()
        return jwk_set

    def __get_jwk_set(self):
        jwk_set = self.storage_cache.get_as_json(f"{self.issuer}/jwk_set")
        if jwk_set is None:
            jwk_set = self.__get_jwk_set_from_jwks_uri()
            self.storage_cache.set_as_json(f"{self.issuer}/jwk_set", jwk_set)
        return jwk_set
