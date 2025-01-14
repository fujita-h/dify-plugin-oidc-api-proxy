from typing import Mapping
from urllib.parse import urlparse

from dify_plugin import Endpoint
from werkzeug import Request, Response

from endpoints.helpers.endpoint import OidcApiProxyErrorResponse, proxy_response, proxy_stream_response
from endpoints.helpers.oidc import OpenIDConnectDiscoveryProvider


class OidcApiProxyEndpoint(Endpoint):
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        # Get settings
        oidc_issuer = str(settings.get("oidc_issuer", ""))
        oidc_audience = str(settings.get("oidc_audience", ""))
        oidc_scope = str(settings.get("oidc_scope", ""))
        dify_api_url = str(settings.get("dify_api_url", ""))
        dify_api_key = str(settings.get("dify_api_key", ""))

        # prepare dify api url by removing trailing slash
        if dify_api_url.endswith("/"):
            dify_api_url = dify_api_url[:-1]

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

        # prepare url
        url = f"{dify_api_url}{r.path}"

        # prepare headers
        headers = {
            "Host": urlparse(dify_api_url).netloc,
            "Authorization": f"Bearer {dify_api_key}",
            **({"Content-Type": r.headers["Content-Type"]} if r.headers.get("Content-Type") else {}),
        }

        # prepare json if request is json
        json = r.get_json() if r.is_json else None

        # prepare files if request has files
        files = [
            (file, (r.files[file].filename, r.files[file].stream, r.files[file].content_type)) for file in r.files
        ] or None

        # Forward request to Dify API with Syncronous HTTP Client
        try:
            return proxy_stream_response(
                method=r.method, url=url, headers=headers, params=r.args, json=json, data=r.form, files=files
            )
        except Exception as e:
            print(str(e))
            return OidcApiProxyErrorResponse(str(e), 500)
