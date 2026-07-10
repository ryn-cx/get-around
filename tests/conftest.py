from __future__ import annotations

from pathlib import Path

import pytest

from get_around import GetAround
from get_around.testing import build_client

ENV_FILE = Path(__file__).parent.parent / ".env"


@pytest.fixture
def client() -> GetAround:
    return build_client(env_file=ENV_FILE)
