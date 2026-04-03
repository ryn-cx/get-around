"""get-around: httpx wrapper with custom proxy support."""

from __future__ import annotations

import json
from typing import Any

import httpx

from get_around.copy_params import copy_method_params


class GetAroundError(Exception):
    """Raised when the proxy server itself returns an error."""


class GetAround:
    """HTTP client that routes requests through a proxy server."""

    def __init__(self, server: str | None = None, password: str | None = None) -> None:
        self.server = server
        self.password = password

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        if self.server is None:
            return httpx.request(method, url, **kwargs)

        proxy_payload: dict[str, Any] = {"url": url, "method": method.upper()}

        if "headers" in kwargs:
            proxy_payload["headers"] = kwargs.pop("headers")
        if "json" in kwargs:
            proxy_payload["data"] = kwargs.pop("json")
        if "data" in kwargs:
            proxy_payload["form"] = kwargs.pop("data")
        if "params" in kwargs:
            proxy_payload["params"] = kwargs.pop("params")
        if "cookies" in kwargs:
            proxy_payload["cookies"] = kwargs.pop("cookies")
        if "content" in kwargs:
            proxy_payload["content"] = kwargs.pop("content")
        if "auth" in kwargs:
            proxy_payload["auth"] = kwargs.pop("auth")

        timeout = kwargs.pop("timeout", 60)

        assert self.server is not None
        assert self.password is not None

        proxy_response = httpx.post(
            self.server,
            json=proxy_payload,
            headers={"Authorization": f"Bearer {self.password}"},
            timeout=timeout,
        )

        if proxy_response.status_code != 200:  # noqa: PLR2004
            msg = f"Proxy error: {proxy_response.status_code}"
            raise GetAroundError(msg)

        proxy_result = proxy_response.json()

        body = proxy_result["body"]
        if not isinstance(body, str):
            body = json.dumps(body)

        return httpx.Response(
            status_code=proxy_result["statusCode"],
            content=body.encode("utf-8"),
            headers=proxy_result["headers"],
        )

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
