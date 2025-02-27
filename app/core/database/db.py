from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from typing import AsyncGenerator


def create_engine(url, **kwargs):
    """Create an asynchronous SQLAlchemy engine."""
    return create_async_engine(url, echo=False, **kwargs)


master_db_engine = create_engine(settings.postgresql_database_master_url)
slave_db_engine = create_engine(
    settings.postgresql_database_slave_url,
    pool_size=10, max_overflow=20, pool_recycle=3600, pool_timeout=30, pool_pre_ping=True
)

# Async session factories
async_master_session = async_sessionmaker(
    bind=master_db_engine, autocommit=False, autoflush=False)
async_slave_session = async_sessionmaker(
    bind=slave_db_engine, autocommit=False, autoflush=False)


async def get_write_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    """
    async with async_master_session() as session:
        yield session


async def get_read_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    """
    async with async_slave_session() as session:
        yield session
