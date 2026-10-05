# PlaneTracker

A Flask API over OpenSky aircraft data, built in small slices:

| Layer | Storage | Job |
|---|---|---|
| Bronze | S3 (local files in dev) | Raw OpenSky responses, replayable |
| Silver | PostgreSQL | Normalized aircraft observations (history) |
| Gold: current | MongoDB | One document per recent aircraft, geo-searchable |
| Gold: stats | PostgreSQL | Daily aggregates derived from Silver |
| API | Flask | Serves Gold views and Silver history |

## Setup

```bash
uv sync
cp .env.example .env   # optional local overrides
```

## Run

```bash
uv run flask run --debug
```

`.flaskenv` sets `FLASK_APP`, so `--app` isn't needed. Then:

```bash
curl http://127.0.0.1:5000/health
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check: `{"status": "ok"}` |

Errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details (`application/problem+json`).

## Configuration

Settings are layered: defaults in `src/planetracker/config.py`, then `FLASK_*` environment variables (including `.env`), then any mapping passed to `create_app()`.

| Variable | Default | Description |
|---|---|---|
| `FLASK_LOG_LEVEL` | `INFO` | App logger level |

## Development

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy
```
