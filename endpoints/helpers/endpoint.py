import json

from werkzeug import Response


def OidcApiProxyErrorResponse(message: str, error_code: int = 500) -> Response:
    return Response(
        json.dumps({"error": message}),
        status=error_code,
        content_type="application/json",
    )
