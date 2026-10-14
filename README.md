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
| `GET` | `/version` | Package version from `pyproject.toml` |

Errors are returned as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details (`application/problem+json`).

## Pipeline

**OpenSky → typed rows** (`opensky.py`): decodes a `/states/all` response exactly as [documented](https://openskynetwork.github.io/opensky-api/rest.html#all-state-vectors), with strict types (no string-to-number coercion). `"states": null` means no aircraft. Rows are 17 fields, or 18 with `extended=1`.

**Silver** (`silver.py`): one `Observation` per row. Pure functions, so replaying a response gives identical rows.

- `icao24` is trimmed and lowercased, and must be 6 hex digits.
- Callsign and squawk are trimmed; blank becomes null.
- Epoch seconds become UTC datetimes; every row carries the response's `snapshot_time`.
- Units move into field names: `baro_altitude_m`, `velocity_mps`, `true_track_deg`, ...
- Latitude/longitude must be in range and both present or both null.
- A row that breaks a rule is recorded in `rejected` (with its index in the response) instead of failing the batch.

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

`api-requests/` holds `.http` files for manual testing against a running server, one per blueprint. Open them with the VS Code [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) extension and click "Send Request".
