from sqlalchemy import UUID, DateTime, String, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.filtering import parse_filter_query, parse_filters, resolve_and_join_column
from typing import Any, List, Optional
from fastapi import HTTPException
import uuid


Base = declarative_base()


@as_declarative()
class Base:
    '''
    =====================================================
    # Base model to include default columns for all tables.
    =====================================================
    '''
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.timezone('Asia/Kolkata', func.now()))
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.timezone('Asia/Kolkata', func.now()), onupdate=func.timezone('Asia/Kolkata', func.now()))
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Track the creator
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Track the updater
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Soft delete column

    '''
    =====================================================
    # Bulk insert multiple records
    =====================================================
    '''
    @classmethod
    async def create(cls, session: AsyncSession, data_list: List[Any]):
        if not data_list:
            raise ValueError("No data provided to create records.")

        # 🔥 Ensure data is converted to dictionaries before passing to ORM
        objects = [cls(**(data.dict() if hasattr(data, "dict") else data)) for data in data_list]

        session.add_all(objects)
        await session.commit()

        return len(objects)
    
    '''
    =====================================================
    # Bulk update multiple records, each with different values.
    =====================================================
    '''
    @classmethod
    async def update(cls, session: AsyncSession, data_list: List[dict]):
        if not data_list:
            raise ValueError("No data provided to update records.")

        updated_count = 0

        for data_obj in data_list:
            # ✅ Convert Pydantic model to dictionary
            data = data_obj.dict(exclude_unset=True) if hasattr(data_obj, "dict") else data_obj

            obj_id = data.pop("id", None)  # Extract object ID
            if not obj_id:
                continue  # Skip if no ID provided

            # ✅ Perform update dynamically
            stmt = (
                update(cls)
                .where(cls.id == obj_id)
                .values(**data)
                .execution_options(synchronize_session=False)
            )

            result = await session.execute(stmt)
            if result.rowcount > 0:
                updated_count += 1

        await session.commit()
        return updated_count

    '''
    =====================================================
    # Soft delete records by updating deleted_at timestamp instead of deleting them.
    =====================================================
    '''
    @classmethod
    async def soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        if not ids:
            raise ValueError("No IDs provided to delete records.")

        # Exclude already soft-deleted records
        stmt = (
            update(cls)
            .where(cls.id.in_(ids), cls.deleted_at.is_(None))
            .values(deleted_at=func.now())  # Soft delete by setting timestamp
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount 
    
    '''
    =====================================================
    # Permanently delete records from the database.
    =====================================================
    '''
    @classmethod
    async def hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        if not ids:
            return 0  # No IDs provided

        stmt = delete(cls).where(cls.id.in_(ids))
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount

    '''
    =====================================================
    # Get only non-deleted (active) record by ID with optional include feature.
    =====================================================
    '''
    @classmethod
    async def get_record_by_id(cls, session: AsyncSession, record_id: uuid.UUID):
        query = select(cls).where(cls.deleted_at.is_(None), cls.id == record_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    '''
    =====================================================
    # Build and execute dynamic queries with filtering, sorting, search, and relationships.
    # Automatically excludes soft-deleted records.
    =====================================================
    '''
    @classmethod
    async def get_records(
        cls,
        filters: Optional[str] = None,
        sort: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List:
        query = select(cls).where(cls.deleted_at.is_(None))

        parsed_filters = parse_filter_query(filters)
        if parsed_filters:
            filter_expr, query = parse_filters(cls, parsed_filters, query)
            if filter_expr is not None:
                query = query.where(filter_expr)

        if search:
            search_expression = [
                column.ilike(f"%{search}%")
                for column in cls.__table__.columns
                if isinstance(column.type, String)
            ]
            if search_expression:
                query = query.where(or_(*search_expression))

        if sort:
            try:
                sort_field, sort_direction = sort.split(":")
            except ValueError:
                sort_field, sort_direction = sort, "asc"

            column = getattr(cls, sort_field, None)
            if column is None:
                nested_keys = sort_field.split("__")
                if len(nested_keys) > 1:
                    joins = {}
                    column, query = resolve_and_join_column(cls, nested_keys, query, joins)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid sort field: {sort_field}"
                    )

            query = query.order_by(
                asc(column) if sort_direction.lower() == "asc" else desc(column)
            )

        return query