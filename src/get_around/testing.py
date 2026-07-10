from __future__ import annotations

from pathlib import Path

import keyring

from get_around import GetAround

KEYRING_SERVICE = "get-around"


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
        msg = f"Missing credential {name!r}; run: keyring set {service} {name}"
        raise RuntimeError(msg)
    return value


def build_client(
    service: str = KEYRING_SERVICE,
    env_file: Path | None = None,
) -> GetAround:
    return GetAround(
        server=get_credential("GET_AROUND_SERVER", service, env_file),
        password=get_credential("GET_AROUND_PASSWORD", service, env_file),
    )
