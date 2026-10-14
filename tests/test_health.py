import tomllib
from pathlib import Path

from flask.testing import FlaskClient

PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


def test_health_returns_ok(client: FlaskClient) -> None:
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_version_matches_pyproject(client: FlaskClient) -> None:
    expected = tomllib.loads(PYPROJECT.read_text())["project"]["version"]

    resp = client.get("/version")

    assert resp.status_code == 200
    assert resp.get_json() == {"version": expected}
