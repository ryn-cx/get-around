"""Tests for get-around proxy client."""

from __future__ import annotations

import re
from pathlib import Path

import httpx

from get_around import GetAround

_CALL_OVERLOAD_RE = re.compile(r":(\d+): error:.*\[call-overload\]")


def call_overload_error_lines(code: str, tmp_path: Path) -> set[int]:
    """Type-check code with mypy and return the line numbers flagged as call-overload."""
    from mypy import api

    snippet = tmp_path / "snippet.py"
    snippet.write_text(code)
    stdout, _stderr, _status = api.run(
        [str(snippet), "--no-incremental", "--no-error-summary"],
    )
    return {
        int(match.group(1))
        for line in stdout.splitlines()
        if (match := _CALL_OVERLOAD_RE.search(line))
    }


def assert_json_responses_match(
    proxied: httpx.Response, direct: httpx.Response
) -> None:
    """Assert that proxied and direct JSON responses match as much as possible."""
    assert proxied.status_code == direct.status_code
    assert proxied.url == direct.url

    proxied_json = proxied.json()
    direct_json = direct.json()

    all_keys = set(proxied_json.keys()) | set(direct_json.keys())
    for key in all_keys:
        if key == "headers":
            proxied_headers = proxied_json.get("headers", {})
            direct_headers = direct_json.get("headers", {})
            assert proxied_headers.get("host") == direct_headers.get("host")
            assert proxied_headers.get("x-custom") == direct_headers.get("x-custom")
        else:
            assert proxied_json.get(key) == direct_json.get(key)


class TestGet:
    def test_basic_get(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/get")
        direct = httpx.get("https://postman-echo.com/get")
        assert_json_responses_match(proxied, direct)

    def test_get_with_params(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/get", params={"key": "value"})
        direct = httpx.get("https://postman-echo.com/get", params={"key": "value"})
        assert_json_responses_match(proxied, direct)

    def test_get_with_headers(self, client: GetAround) -> None:
        proxied = client.get(
            "https://postman-echo.com/get", headers={"X-Custom": "custom"}
        )
        direct = httpx.get(
            "https://postman-echo.com/get", headers={"X-Custom": "custom"}
        )
        assert_json_responses_match(proxied, direct)


class TestCompression:
    def test_gzip(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/gzip")
        direct = httpx.get("https://postman-echo.com/gzip")
        assert_json_responses_match(proxied, direct)

    def test_deflate(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/deflate")
        direct = httpx.get("https://postman-echo.com/deflate")
        assert_json_responses_match(proxied, direct)


class TestPost:
    def test_post_json(self, client: GetAround) -> None:
        proxied = client.post("https://postman-echo.com/post", json={"key": "value"})
        direct = httpx.post("https://postman-echo.com/post", json={"key": "value"})
        assert_json_responses_match(proxied, direct)

    def test_post_form_data(self, client: GetAround) -> None:
        proxied = client.post("https://postman-echo.com/post", data={"field": "data"})
        direct = httpx.post("https://postman-echo.com/post", data={"field": "data"})
        assert_json_responses_match(proxied, direct)

    def test_post_with_cookies(self, client: GetAround) -> None:
        proxied = client.post(
            "https://postman-echo.com/post",
            json={"key": "value"},
            cookies={"key": "value"},
        )
        direct = httpx.post(
            "https://postman-echo.com/post",
            json={"key": "value"},
            cookies={"key": "value"},
        )
        assert_json_responses_match(proxied, direct)

    def test_post_content(self, client: GetAround) -> None:
        proxied = client.post("https://postman-echo.com/post", content="content")
        direct = httpx.post("https://postman-echo.com/post", content="content")
        assert_json_responses_match(proxied, direct)


class TestAuth:
    def test_basic_auth(self, client: GetAround) -> None:
        proxied = client.get(
            "https://postman-echo.com/basic-auth", auth=("postman", "password")
        )
        direct = httpx.get(
            "https://postman-echo.com/basic-auth", auth=("postman", "password")
        )
        assert_json_responses_match(proxied, direct)


class TestMethods:
    def test_put(self, client: GetAround) -> None:
        proxied = client.put("https://postman-echo.com/put", json={"key": "value"})
        direct = httpx.put("https://postman-echo.com/put", json={"key": "value"})
        assert_json_responses_match(proxied, direct)

    def test_patch(self, client: GetAround) -> None:
        proxied = client.patch(
            "https://postman-echo.com/patch", json={"key": "value"}
        )
        direct = httpx.patch("https://postman-echo.com/patch", json={"key": "value"})
        assert_json_responses_match(proxied, direct)

    def test_delete(self, client: GetAround) -> None:
        proxied = client.delete("https://postman-echo.com/delete")
        direct = httpx.delete("https://postman-echo.com/delete")
        assert_json_responses_match(proxied, direct)

    def test_head(self, client: GetAround) -> None:
        proxied = client.head("https://postman-echo.com/get")
        direct = httpx.head("https://postman-echo.com/get")
        assert proxied.status_code == direct.status_code

    def test_options(self, client: GetAround) -> None:
        proxied = client.options("https://postman-echo.com/get")
        direct = httpx.options("https://postman-echo.com/get")
        assert proxied.status_code == direct.status_code

    def test_request_method(self, client: GetAround) -> None:
        proxied = client.request("GET", "https://postman-echo.com/get")
        direct = httpx.request("GET", "https://postman-echo.com/get")
        assert_json_responses_match(proxied, direct)


class TestBypass:
    def test_bypass_without_server(self) -> None:
        client = GetAround()
        proxied = client.get("https://postman-echo.com/ip")
        direct = httpx.get("https://postman-echo.com/ip")
        assert_json_responses_match(proxied, direct)
        assert proxied.json()["ip"] == direct.json()["ip"]


class TestRelay:
    def test_egress_ip_differs_from_direct(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/ip")
        direct = httpx.get("https://postman-echo.com/ip")
        assert proxied.json()["ip"] != direct.json()["ip"]


class TestRedirects:
    REDIRECT_URL = "https://postman-echo.com/redirect-to?url=https://postman-echo.com/get&status_code=302"

    def test_follow_redirects(self, client: GetAround) -> None:
        proxied = client.get(self.REDIRECT_URL, follow_redirects=True)
        direct = httpx.get(self.REDIRECT_URL, follow_redirects=True)
        assert proxied.status_code == direct.status_code == 200

class TestUpstreamErrors:
    def test_404_returned_not_raised(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/status/404")
        direct = httpx.get("https://postman-echo.com/status/404")
        assert proxied.status_code == direct.status_code

    def test_500_returned_not_raised(self, client: GetAround) -> None:
        proxied = client.get("https://postman-echo.com/status/500")
        direct = httpx.get("https://postman-echo.com/status/500")
        assert proxied.status_code == direct.status_code


class TestBadCredentials:
    def test_bad_credentials(self, server_url: str) -> None:
        client = GetAround(server=server_url, client_id="wrong", client_secret="wrong")
        response = client.get("https://postman-echo.com/get")
        assert response.status_code == 302
        assert "cloudflareaccess.com" in response.headers["location"]


class TestHttpProxy:
    def test_valid_argument_combinations_type_check(self, tmp_path: Path) -> None:
        errors = call_overload_error_lines(
            "from get_around import GetAround\n"
            "GetAround()\n"
            'GetAround(proxy="http://127.0.0.1:8080")\n'
            'GetAround(headers={"X-Custom": "test"})\n'
            'GetAround(server="s", client_id="c", client_secret="x")\n',
            tmp_path,
        )
        assert errors == set()

    def test_init_forwards_params_to_client(self) -> None:
        client = GetAround(headers={"X-Custom": "test"}, proxy="http://127.0.0.1:1")
        assert client.client.headers["X-Custom"] == "test"
