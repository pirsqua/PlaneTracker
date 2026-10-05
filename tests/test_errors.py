from flask.testing import FlaskClient

from planetracker import create_app


def test_unknown_route_returns_json_404(client: FlaskClient) -> None:
    resp = client.get("/nope")

    assert resp.status_code == 404
    assert resp.content_type == "application/problem+json"
    body = resp.get_json()
    assert body["status"] == 404
    assert body["title"] == "Not Found"


def test_wrong_method_returns_json_405_with_allow_header(client: FlaskClient) -> None:
    resp = client.post("/health")

    assert resp.status_code == 405
    assert resp.get_json()["status"] == 405
    assert "GET" in resp.headers["Allow"]


def test_unhandled_exception_returns_generic_json_500() -> None:
    # TESTING=True would re-raise the exception into the test, so leave it off here.
    app = create_app()

    @app.get("/boom")
    def boom() -> str:
        raise RuntimeError("database password is hunter2")

    resp = app.test_client().get("/boom")

    assert resp.status_code == 500
    assert resp.get_json()["status"] == 500
    assert "hunter2" not in resp.get_data(as_text=True)
