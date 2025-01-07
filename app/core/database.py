from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.declarative import as_declarative
import uuid

Base = declarative_base()


@as_declarative()
class Base:
    """
    Base model to include default columns for all tables.
    """
    id = mapped_column(String(32), primary_key=True,
                       default=lambda: str(uuid.uuid4().hex))
    created_at = mapped_column(
        DateTime, nullable=False, server_default=func.now())
    updated_at = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = mapped_column(String, nullable=True)  # Track the creator
    updated_by = mapped_column(String, nullable=True)  # Track the updater


def create_engine(url, **kwargs):
    """Create an asynchronous SQLAlchemy engine."""
    return create_async_engine(url, echo=False, **kwargs)


db_engine = create_engine(settings.postgresql_database)

# Async session factory
async_session = async_sessionmaker(
    bind=db_engine, autocommit=False, autoflush=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session.
    """
    async with async_session() as session:
        yield session
