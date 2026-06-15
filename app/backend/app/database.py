import time

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings


def create_engine_with_retry(retries: int = 5, delay: int = 2):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DEBUG,
                future=True,
                pool_pre_ping=True,
            )
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(delay)
    raise last_exc


engine = create_engine_with_retry()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
