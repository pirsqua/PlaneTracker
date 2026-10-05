from flask.testing import FlaskClient


def test_health_returns_ok(client: FlaskClient) -> None:
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
