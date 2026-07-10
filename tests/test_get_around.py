"""Tests for get-around relay client."""

from __future__ import annotations


import httpx

from get_around import GetAround


def assert_json_responses_match(
    relayed: httpx.Response, direct: httpx.Response
) -> None:
    """Assert that relayed and direct JSON responses match as much as possible."""
    assert relayed.status_code == direct.status_code
    assert relayed.url == direct.url

    relayed_json = relayed.json()
    direct_json = direct.json()

    all_keys = set(relayed_json.keys()) | set(direct_json.keys())
    for key in all_keys:
        if key == "headers":
            relayed_headers = relayed_json.get("headers", {})
            direct_headers = direct_json.get("headers", {})
            assert relayed_headers.get("host") == direct_headers.get("host")
            assert relayed_headers.get("x-custom") == direct_headers.get("x-custom")
        else:
            assert relayed_json.get(key) == direct_json.get(key)


class TestGet:
    def test_basic_get(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/get")
        direct = httpx.get("https://postman-echo.com/get")
        assert_json_responses_match(relayed, direct)

    def test_get_with_params(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/get", params={"key": "value"})
        direct = httpx.get("https://postman-echo.com/get", params={"key": "value"})
        assert_json_responses_match(relayed, direct)

    def test_get_with_headers(self, client: GetAround) -> None:
        relayed = client.get(
            "https://postman-echo.com/get", headers={"X-Custom": "custom"}
        )
        direct = httpx.get(
            "https://postman-echo.com/get", headers={"X-Custom": "custom"}
        )
        assert_json_responses_match(relayed, direct)


class TestCompression:
    def test_gzip(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/gzip")
        direct = httpx.get("https://postman-echo.com/gzip")
        assert_json_responses_match(relayed, direct)

    def test_deflate(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/deflate")
        direct = httpx.get("https://postman-echo.com/deflate")
        assert_json_responses_match(relayed, direct)


class TestPost:
    def test_post_json(self, client: GetAround) -> None:
        relayed = client.post("https://postman-echo.com/post", json={"key": "value"})
        direct = httpx.post("https://postman-echo.com/post", json={"key": "value"})
        assert_json_responses_match(relayed, direct)

    def test_post_form_data(self, client: GetAround) -> None:
        relayed = client.post("https://postman-echo.com/post", data={"field": "data"})
        direct = httpx.post("https://postman-echo.com/post", data={"field": "data"})
        assert_json_responses_match(relayed, direct)

    def test_post_with_cookies(self, client: GetAround) -> None:
        relayed = client.post(
            "https://postman-echo.com/post",
            json={"key": "value"},
            cookies={"key": "value"},
        )
        direct = httpx.post(
            "https://postman-echo.com/post",
            json={"key": "value"},
            cookies={"key": "value"},
        )
        assert_json_responses_match(relayed, direct)

    def test_post_content(self, client: GetAround) -> None:
        relayed = client.post("https://postman-echo.com/post", content="content")
        direct = httpx.post("https://postman-echo.com/post", content="content")
        assert_json_responses_match(relayed, direct)


class TestAuth:
    def test_basic_auth(self, client: GetAround) -> None:
        relayed = client.get(
            "https://postman-echo.com/basic-auth", auth=("postman", "password")
        )
        direct = httpx.get(
            "https://postman-echo.com/basic-auth", auth=("postman", "password")
        )
        assert_json_responses_match(relayed, direct)


class TestMethods:
    def test_put(self, client: GetAround) -> None:
        relayed = client.put("https://postman-echo.com/put", json={"key": "value"})
        direct = httpx.put("https://postman-echo.com/put", json={"key": "value"})
        assert_json_responses_match(relayed, direct)

    def test_patch(self, client: GetAround) -> None:
        relayed = client.patch("https://postman-echo.com/patch", json={"key": "value"})
        direct = httpx.patch("https://postman-echo.com/patch", json={"key": "value"})
        assert_json_responses_match(relayed, direct)

    def test_delete(self, client: GetAround) -> None:
        relayed = client.delete("https://postman-echo.com/delete")
        direct = httpx.delete("https://postman-echo.com/delete")
        assert_json_responses_match(relayed, direct)

    def test_head(self, client: GetAround) -> None:
        relayed = client.head("https://postman-echo.com/get")
        direct = httpx.head("https://postman-echo.com/get")
        assert relayed.status_code == direct.status_code

    def test_options(self, client: GetAround) -> None:
        relayed = client.options("https://postman-echo.com/get")
        direct = httpx.options("https://postman-echo.com/get")
        assert relayed.status_code == direct.status_code

    def test_request_method(self, client: GetAround) -> None:
        relayed = client.request("GET", "https://postman-echo.com/get")
        direct = httpx.request("GET", "https://postman-echo.com/get")
        assert_json_responses_match(relayed, direct)


class TestBypass:
    def test_bypass_without_server(self) -> None:
        client = GetAround()
        relayed = client.get("https://postman-echo.com/ip")
        direct = httpx.get("https://postman-echo.com/ip")
        assert_json_responses_match(relayed, direct)
        assert relayed.json()["ip"] == direct.json()["ip"]


class TestRelay:
    def test_egress_ip_differs_from_direct(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/ip")
        direct = httpx.get("https://postman-echo.com/ip")
        assert relayed.json()["ip"] != direct.json()["ip"]


class TestRedirects:
    REDIRECT_URL = "https://postman-echo.com/redirect-to?url=https://postman-echo.com/get&status_code=302"

    def test_follow_redirects(self, client: GetAround) -> None:
        relayed = client.get(self.REDIRECT_URL, follow_redirects=True)
        direct = httpx.get(self.REDIRECT_URL, follow_redirects=True)
        assert relayed.status_code == direct.status_code == 200


class TestUpstreamErrors:
    def test_4xx_returned(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/status/404")
        direct = httpx.get("https://postman-echo.com/status/404")
        assert relayed.status_code == direct.status_code

    def test_5xx_returned(self, client: GetAround) -> None:
        relayed = client.get("https://postman-echo.com/status/500")
        direct = httpx.get("https://postman-echo.com/status/500")
        assert relayed.status_code == direct.status_code


class TestBadCredentials:
    def test_bad_credentials(self, server_url: str) -> None:
        client = GetAround(server=server_url, client_id="wrong", client_secret="wrong")
        response = client.get("https://postman-echo.com/get")
        assert response.status_code == 302
        assert "cloudflareaccess.com" in response.headers["location"]


class TestClientParameterForwarding:
    def test_forwarding_proxy(self) -> None:
        client = GetAround(proxy="http://127.0.0.1:1")
        assert client.proxy == "http://127.0.0.1:1"

    def test_forwarding_headers(self) -> None:
        client = GetAround(headers={"X-Custom": "test"})
        assert client.client.headers["X-Custom"] == "test"
