from __future__ import annotations

from pathlib import Path

import pytest

from get_around import GetAround, build_client_automatically, get_credential

ENV_FILE = Path(__file__).parent.parent / ".env"


@pytest.fixture
def client() -> GetAround:
    return build_client_automatically()


@pytest.fixture
def server_url() -> str:
    return get_credential("GET_AROUND_SERVER")
