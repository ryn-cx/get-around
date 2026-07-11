from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, Unpack, overload

import httpx
import keyring

from get_around.copy_params import copy_method_params

KEYRING_SERVICE = "get-around"

if TYPE_CHECKING:
    import ssl
    from collections.abc import Callable, Mapping

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


class GetAround:
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
    def __init__(self, *, server: str, **kwargs: Unpack[_ClientKwargs]) -> None: ...
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

    def close(self) -> None:
        """Close transport and proxies."""
        self.client.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        if self.server is None or self.proxy is not None:
            return self.client.request(method, url, **kwargs)

        target = httpx.URL(url)
        params = kwargs.pop("params", None)
        if params is not None:
            target = target.copy_merge_params(params)

        headers = httpx.Headers(kwargs.pop("headers", None))
        if self.client_id is not None or self.client_secret is not None:
            if self.client_id is None:
                msg = "client_id is required when client_secret is set"
                raise ValueError(msg)
            if self.client_secret is None:
                msg = "client_secret is required when client_id is set"
                raise ValueError(msg)
            headers["CF-Access-Client-Id"] = self.client_id
            headers["CF-Access-Client-Secret"] = self.client_secret

        response = self.client.request(
            method, f"{self.server}?{target}", headers=headers, **kwargs
        )
        response.request.url = target
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


def _env_file_values(env_file: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_file.exists():
        return values
    for line in env_file.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_credential(
    name: str,
    service: str = KEYRING_SERVICE,
    env_file: Path | None = None,
) -> str:
    env_path = env_file if env_file is not None else Path.cwd() / ".env"
    value = keyring.get_password(service, name) or _env_file_values(env_path).get(name)
    if value is None:
        msg = f"Missing credential {name!r}; run: keyring set {service} {name} or set it in the .env file."
        raise RuntimeError(msg)
    return value


def build_client_automatically(
    service: str = KEYRING_SERVICE,
    env_file: Path | None = None,
) -> GetAround:
    return GetAround(
        server=get_credential("GET_AROUND_SERVER", service, env_file),
        client_id=get_credential("CF_ACCESS_CLIENT_ID", service, env_file),
        client_secret=get_credential("CF_ACCESS_CLIENT_SECRET", service, env_file),
    )
