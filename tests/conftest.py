from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from planetracker import create_app
from planetracker.opensky import STATE_FIELDS

FIXTURES = Path(__file__).parent / "fixtures"

# A raw /states/all response saved byte-for-byte from OpenSky: 82 aircraft over
# Switzerland at 2026-10-14T18:18:39Z, requested with extended=1.
SAMPLE_RESPONSE = FIXTURES / "opensky" / "states_all_switzerland_1792001919.json"

# The first row of SAMPLE_RESPONSE, used as the base for edge-case rows.
SAMPLE_ROW = [
    "4acb59", "SAS28K  ", "Sweden", 1792001917, 1792001918, 6.1802, 47.1115,
    8542.02, False, 212.5, 359.03, 9.43, None, 8999.22, "5745", False, 0, 0,
]  # fmt: skip

type RowFactory = Callable[..., list[Any]]


@pytest.fixture
def app() -> Flask:
    return create_app({"TESTING": True})


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def sample_response() -> bytes:
    return SAMPLE_RESPONSE.read_bytes()


@pytest.fixture
def make_row() -> RowFactory:
    """Build a state vector row from SAMPLE_ROW with named fields replaced."""

    def make(**overrides: Any) -> list[Any]:
        row = dict(zip(STATE_FIELDS, SAMPLE_ROW, strict=True))
        if unknown := overrides.keys() - row.keys():
            raise KeyError(f"not state vector fields: {sorted(unknown)}")
        return list((row | overrides).values())

    return make
