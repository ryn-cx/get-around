"""get-around: httpx wrapper with custom proxy support."""

from __future__ import annotations

import json
from typing import Any

import httpx


class GetAroundError(Exception):
    """Raised when the proxy server itself returns an error."""


class GetAround:
    """HTTP client that routes requests through a proxy server."""

    def __init__(self, server: str, password: str) -> None:
        self.server = server
        self.password = password

    def _proxy_request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send a request through the proxy and return a reconstructed Response."""
        proxy_payload: dict[str, Any] = {
            "url": url,
            "method": method.upper(),
        }

        if "headers" in kwargs:
            proxy_payload["headers"] = kwargs.pop("headers")
        if "json" in kwargs:
            proxy_payload["data"] = kwargs.pop("json")
        if "data" in kwargs:
            proxy_payload["data"] = kwargs.pop("data")
        if "params" in kwargs:
            proxy_payload["params"] = kwargs.pop("params")
        if "cookies" in kwargs:
            proxy_payload["cookies"] = kwargs.pop("cookies")
        if "content" in kwargs:
            proxy_payload["content"] = kwargs.pop("content")
        if "auth" in kwargs:
            proxy_payload["auth"] = kwargs.pop("auth")

        timeout = kwargs.pop("timeout", 60)

        proxy_response = httpx.post(
            self.server,
            json=proxy_payload,
            headers={"X-Auth-Token": self.password},
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
            headers={"Content-Type": "application/json"},
        )

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("DELETE", url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("HEAD", url, **kwargs)

    def options(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._proxy_request("OPTIONS", url, **kwargs)
