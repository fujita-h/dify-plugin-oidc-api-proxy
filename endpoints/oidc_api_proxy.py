from typing import Any, Mapping
from urllib.parse import urlparse

import httpx
from dify_plugin import Endpoint
from werkzeug import Request, Response

from endpoints.helpers.endpoint import OidcApiProxyErrorResponse
from endpoints.helpers.oidc import OpenIDConnectDiscoveryProvider


class OidcApiProxyEndpoint(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        # Get settings
        oidc_issuer = str(settings.get("oidc_issuer", ""))
        oidc_audience = str(settings.get("oidc_audience", ""))
        oidc_scope = str(settings.get("oidc_scope", ""))
        dify_api_url = str(settings.get("dify_api_url", ""))
        dify_api_key = str(settings.get("dify_api_key", ""))

        # Validate settings
        if not oidc_issuer:
            return OidcApiProxyErrorResponse("OpenID Connect Issuer is required", 503)
        if not oidc_audience:
            return OidcApiProxyErrorResponse("OpenID Connect Audience is required", 503)
        if not dify_api_url:
            return OidcApiProxyErrorResponse("Dify API URL is required", 503)
        if not dify_api_key:
            return OidcApiProxyErrorResponse("Dify API Key is required", 503)

        ##
        ## Verify OpenID Connect Access Token
        ##

        # Get access token
        access_token = r.headers.get("Authorization", "").replace("Bearer ", "")
        if not access_token:
            return OidcApiProxyErrorResponse("Access token is required", 401)

        # Verify access token
        try:
            oidc_provider = OpenIDConnectDiscoveryProvider(self.session, oidc_issuer, oidc_audience, oidc_scope)
            _ = oidc_provider.verify_access_token(access_token)
        except Exception as e:
            return OidcApiProxyErrorResponse(str(e), 401)

        ##
        ## Prepare request
        ##

        # Replace URL with Dify API URL
        if dify_api_url.endswith("/"):
            dify_api_url = dify_api_url[:-1]

        url = f"{dify_api_url}{r.full_path}"

        # Replace werkzeug headers to httpx headers,
        # with replacing host and authorization headers
        headers = {
            "Host": urlparse(dify_api_url).netloc,
            "Authorization": f"Bearer {dify_api_key}",
            "Content-Type": r.content_type or None,
        }
        json = r.get_json() if r.is_json else None

        # Forward request to Dify API with Syncronous HTTP Client
        try:
            return proxy_stream_response(r, url, headers, json)
        except Exception as e:
            print(str(e))
            return OidcApiProxyErrorResponse(str(e), 500)


def proxy_response(r: Request, url: str, headers: Mapping, json: Any | None) -> Response:
    with httpx.Client() as client:
        response = client.request(method=r.method, url=url, headers=headers, json=json)

        return Response(
            response=response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )


def proxy_stream_response(r: Request, url: str, headers: Mapping, json: Any | None) -> Response:
    stream_context = httpx.stream(method=r.method, url=url, headers=headers, json=json)

    # Manually enter the context manager to get the response
    stream_response = stream_context.__enter__()

    # Create a generator to stream the response
    def generate():
        try:
            for chunk in stream_response.iter_bytes():
                yield chunk
        finally:
            # Manually exit the context manager after the generator is exhausted
            stream_context.__exit__(None, None, None)

    return Response(
        generate(),
        status=stream_response.status_code,
        content_type=stream_response.headers.get("Content-Type"),
    )
