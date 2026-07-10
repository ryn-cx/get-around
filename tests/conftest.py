from __future__ import annotations

from pathlib import Path

import pytest

from get_around import GetAround
from get_around.testing import build_client, get_credential

ENV_FILE = Path(__file__).parent.parent / ".env"


@pytest.fixture
def client() -> GetAround:
    return build_client(env_file=ENV_FILE)


@pytest.fixture
def server_url() -> str:
    return get_credential("GET_AROUND_SERVER", env_file=ENV_FILE)
