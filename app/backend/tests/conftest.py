import asyncio
import os

import pytest
import pytest_asyncio

# Configure the test environment BEFORE any application module is imported so
# that the global SQLAlchemy engine and session factory are wired against the
# in-memory SQLite database used by the test suite.
# These values are forced (not defaulted) so the tests are independent of the
# caller's environment variables (Docker Compose, CI, local .env, etc.).
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-at-least-32-characters-long!"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ.setdefault("ADMIN_USERNAME", "admin")
# ADMIN_PASSWORD_HASH defaults in app.config to the bcrypt hash of "admin".

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Import the database module first so we can replace its engine and session
# factory before the rest of the application imports them.
from app import database as _db_module

_test_engine = create_async_engine(
    os.environ["DATABASE_URL"],
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    future=True,
    echo=False,
)

_db_module.engine = _test_engine
_db_module.AsyncSessionLocal = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Now import the FastAPI application. Routers and services will pick up the
# patched engine/session factory because they import them from app.database.
from main import app
from app.database import Base, engine, AsyncSessionLocal, get_db


class _NoLifespanASGI:
    """Wrap the real ASGI app and short-circuit lifespan events.

    httpx 0.27's ASGITransport does not accept a ``lifespan=`` argument and
    always runs lifespan. We intercept those messages so the real startup
    hooks (Alembic, default settings seeding, etc.) are not executed against
    the test SQLite database.
    """

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
            return
        await self._app(scope, receive, send)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Provide a dedicated event loop for the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create all SQLAlchemy tables on the shared in-memory SQLite engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine):
    """Yield an async SQLAlchemy session and clean up rows after each test."""
    async with AsyncSessionLocal() as session:
        yield session
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture
async def client(async_engine):
    """Async HTTPX client for the FastAPI app.

    Lifespan events are disabled so the real startup hooks (Alembic, default
    settings seeding, etc.) do not run against the test database.
    """
    from httpx import AsyncClient, ASGITransport

    async def _override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=_NoLifespanASGI(app))
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_token(client):
    """Authenticate as the default admin and return a JWT access token."""
    response = await client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
