"""Render HTTP errors as JSON (RFC 9457 problem details) instead of HTML."""

import json

from flask import Flask
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response


def handle_http_exception(error: HTTPException) -> Response:
    # get_response() keeps headers the error sets, e.g. Allow on a 405.
    response = error.get_response()
    response.data = json.dumps(
        {
            "type": "about:blank",
            "title": error.name,
            "status": error.code,
            "detail": error.description,
        }
    )
    response.content_type = "application/problem+json"
    return response


def register(app: Flask) -> None:
    # Unhandled exceptions reach this handler as a generic 500 InternalServerError,
    # so internal details are never sent to the client. With debug on, Flask
    # re-raises them instead so the interactive debugger can show the traceback.
    app.register_error_handler(HTTPException, handle_http_exception)
