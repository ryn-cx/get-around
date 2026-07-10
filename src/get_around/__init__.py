"""get-around: httpx wrapper with custom proxy support."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any, TypedDict, Unpack, overload

import httpx
from httpx._auth import FunctionAuth
from httpx._client import USE_CLIENT_DEFAULT, UseClientDefault

from get_around.copy_params import copy_method_params

if TYPE_CHECKING:
    import ssl
    from collections.abc import Callable, Mapping
    from types import TracebackType

    from httpx._client import EventHook
    from httpx._types import (
        AuthTypes,
        CertTypes,
        CookieTypes,
        HeaderTypes,
        QueryParamTypes,
        TimeoutTypes,
    )


class _ClientKwargs(TypedDict, total=False):
    auth: AuthTypes | None
    params: QueryParamTypes | None
    headers: HeaderTypes | None
    cookies: CookieTypes | None
    verify: ssl.SSLContext | str | bool
    cert: CertTypes | None
    trust_env: bool
    http1: bool
    http2: bool
    mounts: Mapping[str, httpx.BaseTransport | None] | None
    timeout: TimeoutTypes
    follow_redirects: bool
    limits: httpx.Limits
    max_redirects: int
    event_hooks: Mapping[str, list[EventHook]] | None
    base_url: httpx.URL | str
    transport: httpx.BaseTransport | None
    default_encoding: str | Callable[[bytes], str]


class GetAroundError(Exception):
    """Raised when the proxy server itself returns an error."""


def _build_auth(auth: AuthTypes | UseClientDefault | None) -> httpx.Auth | None:
    if isinstance(auth, UseClientDefault) or auth is None:
        return None
    if isinstance(auth, tuple):
        return httpx.BasicAuth(username=auth[0], password=auth[1])
    if isinstance(auth, httpx.Auth):
        return auth
    if callable(auth):
        return FunctionAuth(func=auth)
    msg = f"Invalid auth argument: {auth!r}"
    raise TypeError(msg)


class GetAround:
    """HTTP client that routes requests through a proxy server."""

    @overload
    def __init__(
        self,
        *,
        server: str,
        client_id: str,
        client_secret: str,
        **kwargs: Unpack[_ClientKwargs],
    ) -> None: ...
    @overload
    def __init__(self, *, proxy: str, **kwargs: Unpack[_ClientKwargs]) -> None: ...
    @overload
    def __init__(self, **kwargs: Unpack[_ClientKwargs]) -> None: ...
    def __init__(
        self,
        *,
        server: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        proxy: str | None = None,
        **kwargs: Unpack[_ClientKwargs],
    ) -> None:
        self.server = server
        self.client_id = client_id
        self.client_secret = client_secret
        self.proxy = proxy
        self.client = httpx.Client(proxy=proxy, **kwargs)

    def __enter__(self) -> GetAround:
        self.client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.client.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self.client.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        if self.server is None or self.proxy is not None:
            return self.client.request(method, url, **kwargs)

        if self.client_id is None:
            msg = "client_id is required to reach the proxy server"
            raise ValueError(msg)
        if self.client_secret is None:
            msg = "client_secret is required to reach the proxy server"
            raise ValueError(msg)

        # These need to be popped before kwargs is passed to build_request.
        auth = kwargs.pop("auth", USE_CLIENT_DEFAULT)
        raw_follow_redirects = kwargs.pop("follow_redirects", USE_CLIENT_DEFAULT)
        timeout = kwargs.pop("timeout", USE_CLIENT_DEFAULT)
        request = self.client.build_request(method, url, **kwargs)

        built_auth = (
            self.client.auth
            if isinstance(auth, UseClientDefault)
            else _build_auth(auth)
        )
        if built_auth:
            request = next(built_auth.auth_flow(request))
        request.read()

        # follow_redirects needs to be made serializable.
        follow_redirects = (
            self.client.follow_redirects
            if isinstance(raw_follow_redirects, UseClientDefault)
            else raw_follow_redirects
        )
        proxy_payload: dict[str, Any] = {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "body": base64.b64encode(request.content).decode("ascii"),
            "followRedirects": follow_redirects,
        }

        proxy_response = self.client.post(
            self.server,
            json=proxy_payload,
            headers={
                "CF-Access-Client-Id": self.client_id,
                "CF-Access-Client-Secret": self.client_secret,
            },
            timeout=timeout,
        )

        # Raise on internal get-around-server errors.
        if proxy_response.status_code != 200:  # noqa: PLR2004
            msg = f"Proxy error: {proxy_response.status_code}"
            raise GetAroundError(msg)

        proxy_result = proxy_response.json()

        headers = {key: value for key, value in proxy_result["headers"].items()}

        # Recreate the response from get-around-server.
        response = httpx.Response(
            status_code=proxy_result["statusCode"],
            content=base64.b64decode(proxy_result["body"]),
            headers=headers,
            request=request,
        )
        response.elapsed = proxy_response.elapsed
        return response

    @copy_method_params(httpx.Client.request)
    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return self._request(method, url, **kwargs)

    @copy_method_params(httpx.Client.get)
    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", url, **kwargs)

    @copy_method_params(httpx.Client.post)
    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", url, **kwargs)

    @copy_method_params(httpx.Client.put)
    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("PUT", url, **kwargs)

    @copy_method_params(httpx.Client.patch)
    def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("PATCH", url, **kwargs)

    @copy_method_params(httpx.Client.delete)
    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("DELETE", url, **kwargs)

    @copy_method_params(httpx.Client.head)
    def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("HEAD", url, **kwargs)

    @copy_method_params(httpx.Client.options)
    def options(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("OPTIONS", url, **kwargs)
