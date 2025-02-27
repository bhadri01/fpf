from math import e
from sqlalchemy import UUID, DateTime, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.filtering import parse_filters
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
import uuid
import json


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
    async def bulk_create(cls, session: AsyncSession, data_list: List[Any]):
        # 🔥 Call model-specific create() (defined in User, Role, etc.)
        updated_data = await cls.create(session, data_list)  

        if not updated_data:
            return []  # Return empty list if no data provided

        # 🔥 Ensure data is converted to dictionaries before passing to ORM
        objects = [cls(**(data.dict() if hasattr(data, "dict") else data)) for data in updated_data]

        session.add_all(objects)
        await session.commit()
        return objects

    @classmethod
    async def create(cls, session: AsyncSession, data_list: List[Any]) -> List[Dict[str, Any]]:
        """This method should be overridden in child classes"""
        return data_list
    
    '''
    =====================================================
    # Bulk update multiple records, each with different values.
    =====================================================
    '''
    @classmethod
    async def bulk_update(cls, session: AsyncSession, update_data_list: List[dict]):
        if not update_data_list:
            return 0  # No data to update
        updated_data = await cls.update(session, update_data_list)

        updated_count = 0

        for data_obj in updated_data:
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

        await session.commit()  # ✅ Commit all updates at once
        return updated_count  # ✅ Return number of updated records
    
    @classmethod
    async def update(cls, session: AsyncSession, data_list: List[any]):
        """This method should be overridden in child classes"""
        return data_list
    

    '''
    =====================================================
    # Soft delete records by updating deleted_at timestamp instead of deleting them.
    =====================================================
    '''
    @classmethod
    async def bulk_soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        updated_ids = await cls.soft_delete(session, ids)
        if not updated_ids:
            return 0  # No IDs provided

        # Exclude already soft-deleted records
        stmt = (
            update(cls)
            .where(cls.id.in_(updated_ids), cls.deleted_at.is_(None))
            .values(deleted_at=func.now())  # Soft delete by setting timestamp
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount 
    
    @classmethod
    async def soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        """This method should be overridden in child classes"""
        return ids

    '''
    =====================================================
    # Permanently delete records from the database.
    =====================================================
    '''
    @classmethod
    async def bulk_hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        updated_ids = await cls.hard_delete(session, ids)
        if not updated_ids:
            return 0  # No IDs provided

        stmt = delete(cls).where(cls.id.in_(updated_ids))
        result = await session.execute(stmt)
        await session.commit()

        return result.rowcount

    @classmethod
    async def hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        """This method should be overridden in child classes"""
        return ids
    '''
    =====================================================
    # Get only non-deleted (active) record by ID with optional include feature.
    =====================================================
    '''
    @classmethod
    async def get_record_by_id(cls, session: AsyncSession, record_id: uuid.UUID, include: Optional[List[str]] = None):
        query = select(cls).where(cls.deleted_at.is_(None), cls.id == record_id)

        # Include related fields
        if include:
            for rel in include:
                if hasattr(cls, rel):
                    query = query.options(selectinload(getattr(cls, rel)))  # ✅ Load related data
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid include field: {rel}"
                    )

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
        include: Optional[List[str]] = None,
    ) -> List:
        
        # Exclude deleted records
        query = select(cls).where(cls.deleted_at.is_(None))

        # 1️⃣ Include Related Fields
        if include:
            for rel in include:
                if hasattr(cls, rel):
                    query = query.options(selectinload(getattr(cls, rel)))
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid include field: {rel}")

        # 2️⃣ Apply Filters (Supports Nested Relationships)
        def parse_filter_query(filters: Optional[str]) -> Optional[Dict]:
            """
            Parse a JSON string representing filters into a dictionary.
            """
            if not filters:
                return None

            try:
                parsed_filters = json.loads(filters)
                if not isinstance(parsed_filters, dict):  # Ensure it's a dictionary
                    raise ValueError(
                        "Filters should be a valid JSON object (dictionary).")
                return parsed_filters
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid filter JSON: {str(e)}")

        parsed_filters = parse_filter_query(filters)
        if parsed_filters:
            query = query.where(parse_filters(
                cls, parsed_filters))  # Apply filters

        # 3️⃣ Global Search (Across Text Fields)
        if search:
            search_expression = [
                column.ilike(f"%{search}%") for column in cls.__table__.columns if column.type.python_type == str
            ]
            if search_expression:
                query = query.where(or_(*search_expression))

        # 4️⃣ Sorting
        if sort:
            try:
                sort_field, sort_direction = sort.split(":")
            except ValueError:
                sort_field, sort_direction = sort, "asc"  # Default to ascending if no direction provided

            column = getattr(cls, sort_field, None)
            if column is None:
                raise HTTPException(
                    status_code=400, detail=f"Invalid sort field: {sort_field}")

            query = query.order_by(
                asc(column) if sort_direction.lower() == "asc" else desc(column))

        return query
