from __future__ import annotations

import os

import pytest
from dotenv import load_dotenv

from get_around import GetAround

load_dotenv()


@pytest.fixture
def client() -> GetAround:
    server = os.environ["GET_AROUND_SERVER"]
    password = os.environ["GET_AROUND_PASSWORD"]
    return GetAround(server=server, password=password)
