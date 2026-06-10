# get-around

A drop-in [httpx](https://www.python-httpx.org/) wrapper that transparently routes
requests through a custom proxy server.

`GetAround` mirrors httpx's request API (`get`, `post`, `put`, `patch`, `delete`,
`head`, `options`, `request`) and returns standard `httpx.Response` objects. When
configured with a proxy `server` and `password`, requests are forwarded through that
server; when no server is set, requests are sent directly.

## Proxy server

The `server` you pass to `GetAround` is a companion proxy that receives each request,
forwards it on your behalf, and returns the response. The server is available
at[ryn-cx/get-around-server](https://github.com/ryn-cx/get-around-server). Deploy it,
set a password, and point `GetAround` at its URL to route your traffic through it.

## Installation

```sh
uv add git+https://github.com/ryn-cx/get-around.git
```

## Usage

```python
from get_around import GetAround

# Route requests through a proxy server
client = GetAround(server="https://proxy-server", password="password")

response = client.get("https://httpbin.org/get", params={"foo": "bar"})

# POST with a JSON body
response = client.post("https://httpbin.org/post", json={"key": "value"})
```

Upstream HTTP errors (404, 500, etc.) are returned as normal responses, not raised.
Check `response.status_code` as you would with `httpx`.
