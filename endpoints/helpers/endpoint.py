import json
from typing import Any

import httpx
import werkzeug


def proxy_response(
    method: str,
    url: str,
    headers: httpx._types.HeaderTypes | None,
    params: httpx._types.QueryParamTypes | None,
    json: Any | None,
    data: httpx._types.RequestData | None,
    files: httpx._types.RequestFiles | None,
) -> werkzeug.Response:
    with httpx.Client() as client:
        response = client.request(
            method=method, url=url, headers=headers, params=params, json=json, data=data, files=files
        )

        return werkzeug.Response(
            response=response.content,
            status=response.status_code,
            content_type=response.headers.get("Content-Type"),
        )


def proxy_stream_response(
    method: str,
    url: str,
    headers: httpx._types.HeaderTypes | None,
    params: httpx._types.QueryParamTypes | None,
    json: Any | None,
    data: httpx._types.RequestData | None,
    files: httpx._types.RequestFiles | None,
) -> werkzeug.Response:
    stream_context = httpx.stream(method=method, url=url, headers=headers, json=json, data=data, files=files)

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

    return werkzeug.Response(
        generate(),
        status=stream_response.status_code,
        content_type=stream_response.headers.get("Content-Type"),
    )


def OidcApiProxyErrorResponse(message: str, error_code: int = 500) -> werkzeug.Response:
    return werkzeug.Response(
        json.dumps({"error": message}),
        status=error_code,
        content_type="application/json",
    )
