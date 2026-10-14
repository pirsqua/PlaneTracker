"""Health and version endpoints."""

from importlib import metadata

from flask import Blueprint

# Read from the installed package metadata, which is built from pyproject.toml.
# Computed once at import: the version can't change while the process runs.
_VERSION = metadata.version("planetracker")

bp = Blueprint("health", __name__)


@bp.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@bp.get("/version")
def version() -> dict[str, str]:
    return {"version": _VERSION}
