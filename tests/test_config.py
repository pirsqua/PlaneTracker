import logging

import pytest

from planetracker import create_app


def test_default_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLASK_LOG_LEVEL", raising=False)

    app = create_app()

    assert app.config["LOG_LEVEL"] == "INFO"
    assert app.logger.level == logging.INFO


def test_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLASK_LOG_LEVEL", "DEBUG")

    app = create_app()

    assert app.config["LOG_LEVEL"] == "DEBUG"
    assert app.logger.level == logging.DEBUG


def test_explicit_config_overrides_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLASK_LOG_LEVEL", "DEBUG")

    app = create_app({"LOG_LEVEL": "WARNING"})

    assert app.config["LOG_LEVEL"] == "WARNING"
