"""Tests for get-around proxy client."""

from __future__ import annotations

import httpx
import pytest

from get_around import GetAround, GetAroundError


def assert_json_responses_match(proxied: httpx.Response, direct: httpx.Response) -> None:
    """Assert that proxied and direct JSON responses match on all comparable attributes."""
    assert proxied.status_code == direct.status_code

    proxied_json = proxied.json()
    direct_json = direct.json()

    all_keys = set(proxied_json.keys()) | set(direct_json.keys())
    for key in all_keys:
        if key == "origin":
            # IPs differ (proxy IP vs client IP), just verify both are present
            assert proxied_json.get("origin")
            assert direct_json.get("origin")
        elif key == "headers":
            # Headers differ due to proxy infrastructure (Accept-Encoding, User-Agent, Cf-* headers, etc.)
            # Just verify both have headers and share the Host
            proxied_headers = proxied_json.get("headers", {})
            direct_headers = direct_json.get("headers", {})
            assert proxied_headers.get("Host") == direct_headers.get("Host")
            assert proxied_headers.get("X-Custom") == direct_headers.get("X-Custom")
        else:
            assert proxied_json.get(key) == direct_json.get(key), (
                f"Mismatch on key {key!r}: proxied={proxied_json.get(key)!r}, direct={direct_json.get(key)!r}"
            )


class TestGet:
    def test_basic_get(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/get")
        direct = httpx.get("https://httpbin.org/get")
        assert_json_responses_match(proxied, direct)

    def test_get_with_params(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/get", params={"foo": "bar", "baz": "1"})
        direct = httpx.get("https://httpbin.org/get", params={"foo": "bar", "baz": "1"})
        assert_json_responses_match(proxied, direct)

    def test_get_with_headers(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/get", headers={"X-Custom": "test-value"})
        direct = httpx.get("https://httpbin.org/get", headers={"X-Custom": "test-value"})
        assert_json_responses_match(proxied, direct)


class TestCompression:
    def test_gzip(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/gzip")
        direct = httpx.get("https://httpbin.org/gzip")
        assert_json_responses_match(proxied, direct)
        assert proxied.json()["gzipped"] is True

    def test_deflate(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/deflate")
        direct = httpx.get("https://httpbin.org/deflate")
        assert_json_responses_match(proxied, direct)
        assert proxied.json()["deflated"] is True


class TestPost:
    def test_post_json(self, client: GetAround) -> None:
        proxied = client.post("https://httpbin.org/post", json={"key": "value"})
        direct = httpx.post("https://httpbin.org/post", json={"key": "value"})
        assert_json_responses_match(proxied, direct)

    def test_post_form_data(self, client: GetAround) -> None:
        proxied = client.post("https://httpbin.org/post", data={"field": "data"})
        direct = httpx.post("https://httpbin.org/post", data={"field": "data"})
        assert_json_responses_match(proxied, direct)



    def test_post_with_cookies(self, client: GetAround) -> None:
        proxied = client.post("https://httpbin.org/post", json={"key": "value"}, cookies={"session": "abc123"})
        direct = httpx.post("https://httpbin.org/post", json={"key": "value"}, cookies={"session": "abc123"})
        assert_json_responses_match(proxied, direct)

    def test_post_content(self, client: GetAround) -> None:
        proxied = client.post("https://httpbin.org/post", content="raw body")
        direct = httpx.post("https://httpbin.org/post", content="raw body")
        assert_json_responses_match(proxied, direct)


class TestAuth:
    def test_basic_auth(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/basic-auth/user/pass", auth=("user", "pass"))
        direct = httpx.get("https://httpbin.org/basic-auth/user/pass", auth=("user", "pass"))
        assert_json_responses_match(proxied, direct)


class TestMethods:
    def test_put(self, client: GetAround) -> None:
        proxied = client.put("https://httpbin.org/put", json={"update": "value"})
        direct = httpx.put("https://httpbin.org/put", json={"update": "value"})
        assert_json_responses_match(proxied, direct)

    def test_patch(self, client: GetAround) -> None:
        proxied = client.patch("https://httpbin.org/patch", json={"patch": "value"})
        direct = httpx.patch("https://httpbin.org/patch", json={"patch": "value"})
        assert_json_responses_match(proxied, direct)

    def test_delete(self, client: GetAround) -> None:
        proxied = client.delete("https://httpbin.org/delete")
        direct = httpx.delete("https://httpbin.org/delete")
        assert_json_responses_match(proxied, direct)

    def test_head(self, client: GetAround) -> None:
        proxied = client.head("https://httpbin.org/get")
        direct = httpx.head("https://httpbin.org/get")
        assert proxied.status_code == direct.status_code

    def test_options(self, client: GetAround) -> None:
        proxied = client.options("https://httpbin.org/get")
        direct = httpx.options("https://httpbin.org/get")
        assert proxied.status_code == direct.status_code

    def test_request_method(self, client: GetAround) -> None:
        proxied = client.request("GET", "https://httpbin.org/get")
        direct = httpx.request("GET", "https://httpbin.org/get")
        assert_json_responses_match(proxied, direct)


class TestBypass:
    def test_bypass_without_server(self) -> None:
        client = GetAround()
        response = client.get("https://httpbin.org/get")
        direct = httpx.get("https://httpbin.org/get")
        assert_json_responses_match(response, direct)


class TestUpstreamErrors:
    def test_404_returned_not_raised(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/status/404")
        direct = httpx.get("https://httpbin.org/status/404")
        assert proxied.status_code == direct.status_code

    def test_500_returned_not_raised(self, client: GetAround) -> None:
        proxied = client.get("https://httpbin.org/status/500")
        direct = httpx.get("https://httpbin.org/status/500")
        assert proxied.status_code == direct.status_code


class TestProxyErrors:
    def test_bad_password(self) -> None:
        client = GetAround(server="https://server.example", password="wrong")
        with pytest.raises(GetAroundError):
            client.get("https://httpbin.org/get")
