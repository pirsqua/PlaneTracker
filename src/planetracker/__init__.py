"""PlaneTracker Flask application."""

from collections.abc import Mapping
from typing import Any

from flask import Flask

from planetracker import errors, health
from planetracker.config import DefaultConfig


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    """Build and configure a Flask app.

    Config is layered, lowest to highest priority:
      1. DefaultConfig (code)
      2. FLASK_* environment variables (and .env / .flaskenv via the flask CLI)
      3. the ``config`` mapping passed in (used by tests)
    """
    # This API serves no static files, so drop the default /static/<path> route.
    app = Flask(__name__, static_folder=None)

    app.config.from_object(DefaultConfig)
    app.config.from_prefixed_env()
    if config is not None:
        app.config.from_mapping(config)

    app.logger.setLevel(app.config["LOG_LEVEL"])

    errors.register(app)
    app.register_blueprint(health.bp)

    return app
