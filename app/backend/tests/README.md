# Backend Tests

This folder contains the pytest suite for the FastAPI backend.

## Quick start (Docker — recommended)

The project runs on Python 3.12 inside Docker. From the project root:

```bash
# Rebuild the backend image with the test dependencies
docker compose build worker

# Run the test suite
docker compose run --rm --no-deps worker python -m pytest tests/ -v
```

## Run locally

From the `app/backend` directory, with a Python environment compatible with the
pinned dependencies (Python 3.11/3.12):

```bash
python -m pytest tests/ -v
```

## Run a specific test file

```bash
python -m pytest tests/test_auth.py -v
```

## Run with coverage

```bash
coverage run -m pytest tests/ -v
coverage report
```

## Test environment

- `conftest.py` automatically configures an in-memory SQLite database
  (`sqlite+aiosqlite:///:memory:`) and disables real lifespan/startup hooks.
- The default admin credentials are `admin` / `admin`.
- The global `get_db` dependency is overridden so endpoints use the test
  session factory.

## Notes

- `pytest.ini` sets `asyncio_mode = auto` so `pytest.mark.asyncio` is optional.
- The `event_loop` fixture is provided for compatibility with older
  `pytest-asyncio` workflows.
- `httpx` is pinned to `0.27.0`, which does not support the `lifespan=` argument
  on `ASGITransport`. The `client` fixture therefore wraps the ASGI app to
  short-circuit lifespan events instead.
