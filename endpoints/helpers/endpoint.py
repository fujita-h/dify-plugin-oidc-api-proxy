import json
from typing import Any, Tuple

import httpx
import werkzeug
import werkzeug.datastructures


def proxy_response(
    request: werkzeug.Request,
    method: str,
    url: str,
    headers: httpx._types.HeaderTypes | None,
    params: httpx._types.QueryParamTypes | None,
    json: Any | None,
    data: httpx._types.RequestData | None,
    files: httpx._types.RequestFiles | None,
) -> werkzeug.Response:
    is_app_call, is_stream = check_app_streaming_request(request)

    if is_app_call and is_stream:
        return proxy_stream_response(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=httpx.Timeout(None, read=300, write=10),
        )
    elif is_app_call and not is_stream:
        return proxy_blocking_response(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=httpx.Timeout(None, read=300, write=10),
        )
    else:
        return proxy_blocking_response(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=httpx.Timeout(None, read=10, write=10),
        )


def proxy_blocking_response(
    method: str,
    url: str,
    headers: httpx._types.HeaderTypes | None,
    params: httpx._types.QueryParamTypes | None,
    json: Any | None,
    data: httpx._types.RequestData | None,
    files: httpx._types.RequestFiles | None,
    timeout: httpx._types.TimeoutTypes | None,
) -> werkzeug.Response:
    with httpx.Client(timeout=timeout) as client:
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
    timeout: httpx._types.TimeoutTypes | None,
) -> werkzeug.Response:
    stream_context = httpx.stream(
        timeout=timeout, method=method, url=url, headers=headers, json=json, data=data, files=files
    )

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


def check_app_streaming_request(request: werkzeug.Request) -> Tuple[bool, bool]:
    is_app_call = False
    is_stream = False

    if request.method.lower() in ["post"]:
        if request.path in ["/chat-messages", "/workflows/run"]:
            is_app_call = True
            if request.is_json:
                json = request.get_json()
                if str(json.get("response_mode", "")).lower() == "streaming":
                    is_stream = True

    return is_app_call, is_stream


def replace_user_params(
    user: str,
    args: werkzeug.datastructures.MultiDict[str, str],
    json: Any | None,
    data: werkzeug.datastructures.ImmutableMultiDict[str, str],
) -> Tuple[
    werkzeug.datastructures.MultiDict[str, str],
    Any | None,
    werkzeug.datastructures.ImmutableMultiDict[str, str],
]:
    if not user:
        return args, json, data

    if args:
        args["user"] = user
    if json is not None:
        json["user"] = user
    if data:
        data["user"] = user

    return args, json, data
