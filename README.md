# Get Around

A drop-in [httpx](https://www.python-httpx.org/) wrapper that transparently routes
requests through a cloudflare worker based relay server.

`GetAround` mirrors httpx's request API (`get`, `post`, `put`, `patch`, `delete`,
`head`, `options`, `request`) and returns standard `httpx.Response` objects.

## Proxy server

The `server` you pass to `GetAround` is a cloudflare worker running
[ryn-cx/get-around-server](https://github.com/ryn-cx/get-around-server) and the
`client_id` and `client_secret` are the service tokens to access the worker. For more
information see [ryn-cx/get-around-server](https://github.com/ryn-cx/get-around-server).

## Installation

```sh
uv add git+https://github.com/ryn-cx/get-around.git
```

## Usage
```python
from get_around import GetAround

# Route requests through get-around-server, (this can also include additional kwargs for httpx.Client).
client = GetAround(
    server="https://get-around-server",
    client_id="<service-token-client-id>",
    client_secret="<service-token-client-secret>",
)


# Every method matches httpx's signature and returns an httpx.Response.
response = client.get("https://postman-echo.com/get", params={"foo": "bar"})
response = client.post("https://postman-echo.com/post", json={"key": "value"})
response = client.put("https://postman-echo.com/put", json={"key": "value"})
response = client.patch("https://postman-echo.com/patch", json={"key": "value"})
response = client.delete("https://postman-echo.com/delete")
response = client.head("https://postman-echo.com/get")
response = client.options("https://postman-echo.com/get")
response = client.request("GET", "https://postman-echo.com/get")


```
