# get-around

**The httpx you already know — now it goes anywhere.** `get-around` is a drop-in
wrapper around [httpx](https://www.python-httpx.org/) that transparently tunnels every
request through a proxy, and gives you back the exact `httpx.Response` you'd get without
one. Same API, same objects, new reach. There is no step two.

Point it at a Cloudflare Access–protected Worker, a plain HTTP proxy, or nothing at all —
and the rest of your code never has to know the difference.

## Why you'll reach for it

- **A true drop-in.** `GetAround` mirrors httpx's request surface exactly — `request`,
  `get`, `post`, `put`, `patch`, `delete`, `head`, `options` — and returns real
  `httpx.Response` objects. Swap `httpx` for `GetAround` and your call sites don't move.
- **Three modes, one class.** Route through a **Cloudflare Worker proxy**
  (`server` + `client_id` + `client_secret`), a **standard HTTP/HTTPS proxy** (`proxy`),
  or go **direct** (no arguments) — behaving identically to plain httpx.
- **Modes that can't be mixed up.** The constructor is defined with typed `@overload`
  signatures, so passing an illegal combination (say, `server` *and* `proxy`) is a type
  error your editor and mypy catch before you ever run it.
- **Editor-perfect signatures.** Each verb method is decorated to copy httpx's exact typed
  parameters, so autocomplete and type checking on `client.post(...)` are as rich as
  httpx's own — while the implementation just forwards `**kwargs`.
- **Auth that just travels.** Hand it httpx-style `auth` — a `(user, pass)` tuple, an
  `httpx.Auth`, or a callable — and it's normalized and baked into the request before it's
  serialized across the wire, so Basic auth and friends work through the proxy untouched.
- **Compression handled for free.** gzip and deflate responses come back transparently
  decoded, exactly as httpx would give them to you — verified by the test suite.
- **Errors that stay honest.** Upstream `404`s and `500`s come back as normal responses,
  just like httpx. Only a failure in the *proxy infrastructure itself* raises
  `GetAroundError` — so you never confuse "the site said no" with "the proxy broke."

## One import away

```python
from get_around import GetAround

# Route through a Cloudflare Access–protected Worker proxy
client = GetAround(
    server="https://proxy-server",
    client_id="<service-token-client-id>",
    client_secret="<service-token-client-secret>",
)

response = client.get("https://httpbin.org/get", params={"foo": "bar"})
response = client.post("https://httpbin.org/post", json={"key": "value"})

# ...or a standard HTTP proxy
client = GetAround(proxy="http://127.0.0.1:8080")
response = client.get("https://httpbin.org/get")

# ...or nothing at all — plain httpx behavior
client = GetAround()
response = client.get("https://httpbin.org/get")
```

The Cloudflare proxy mode talks to its companion Worker,
[get-around-server](https://github.com/ryn-cx/get-around-server) — a stateless edge relay
protected by Cloudflare Access.

## Tested against the real thing

The test suite doesn't mock — it proves parity. Every request is fired **both** through
the `GetAround` proxy **and** directly through plain httpx, then the two JSON responses are
asserted to match key-for-key. That differential check covers GET with params and headers,
POST with JSON/form/cookies/raw bodies, HTTP Basic auth, every HTTP verb, gzip and deflate
decoding, redirect following, and direct (bypass) mode.

It goes further: the mutual exclusivity of the three modes is verified by **invoking mypy
at test time** — asserting that illegal constructor combinations produce a `call-overload`
type error while the three valid ones type-check clean. The guarantee isn't just claimed;
it's checked by the type checker inside the tests.

## Install

Requires **Python ≥ 3.14**. The only runtime dependency is `httpx`.

```sh
uv add git+https://github.com/ryn-cx/get-around.git
```

Building a Cloudflare-proxy client from stored credentials? Install the `testing` extra for
keyring-backed helpers (`build_client`, `get_credential`) that pull secrets from your OS
keyring with a `.env` fallback.

---

Familiar API. Longer reach. Reach for `get-around`.
