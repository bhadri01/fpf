from sqlalchemy import UUID, DateTime, asc, delete, desc, func, or_, select, update
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.filtering import parse_filters
from typing import Any, Dict, List, Optional
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
        before_create = await cls.before_create(session, data_list)  

        if not before_create:
            return []  # Return empty list if no data provided

        # 🔥 Ensure data is converted to dictionaries before passing to ORM
        objects = [cls(**(data.dict() if hasattr(data, "dict") else data)) for data in before_create]

        session.add_all(objects)
        await session.commit()

        for obj in objects:
            await session.refresh(obj)
        
        # 🔥 Call model-specific after_create() (defined in User, Role, etc.)
        await cls.after_create(session, objects)
        return objects

    @classmethod
    async def before_create(cls, session: AsyncSession, data_list: List[Any]) -> List[Dict[str, Any]]:
        # This method should be overridden in child classes to perform any pre-processing
        return data_list
    
    @classmethod
    async def after_create(cls, session: AsyncSession, data_list: List[Any]) -> List[Dict[str, Any]]:
        # This method should be overridden in child classes to perform any post-processing
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
        before_update = await cls.before_update(session, update_data_list)

        updated_count = 0

        for data_obj in before_update:
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

        # 🔥 Call model-specific after_update() (defined in User, Role, etc.)
        await cls.after_update(session, before_update)
        
        return updated_count  # ✅ Return number of updated records
    
    @classmethod
    async def before_update(cls, session: AsyncSession, data_list: List[any]):
        # This method should be overridden in child classes to perform any pre-processing
        return data_list
    
    @classmethod
    async def after_update(cls, session: AsyncSession, data_list: List[any]):
        # This method should be overridden in child classes to perform any post-processing
        return data_list
    

    '''
    =====================================================
    # Soft delete records by updating deleted_at timestamp instead of deleting them.
    =====================================================
    '''
    @classmethod
    async def bulk_soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        before_delete_ids = await cls.before_soft_delete(session, ids)
        if not before_delete_ids:
            return 0  # No IDs provided

        # Exclude already soft-deleted records
        stmt = (
            update(cls)
            .where(cls.id.in_(before_delete_ids), cls.deleted_at.is_(None))
            .values(deleted_at=func.now())  # Soft delete by setting timestamp
            .execution_options(synchronize_session=False)
        )
        result = await session.execute(stmt)
        await session.commit()

        await cls.after_soft_delete(session, before_delete_ids)
        return result.rowcount 
    
    @classmethod
    async def before_soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        # This method should be overridden in child classes to perform any pre-processing
        return ids
    
    @classmethod
    async def after_soft_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        # This method should be overridden in child classes to perform any post-processing
        return ids

    '''
    =====================================================
    # Permanently delete records from the database.
    =====================================================
    '''
    @classmethod
    async def bulk_hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        before_delete_ids = await cls.before_hard_delete(session, ids)
        if not before_delete_ids:
            return 0  # No IDs provided

        stmt = delete(cls).where(cls.id.in_(before_delete_ids))
        result = await session.execute(stmt)
        await session.commit()

        await cls.after_hard_delete(session, before_delete_ids)
        return result.rowcount

    @classmethod
    async def before_hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        # This method should be overridden in child classes to perform any pre-processing
        return ids

    @classmethod
    async def after_hard_delete(cls, session: AsyncSession, ids: List[uuid.UUID]):
        # This method should be overridden in child classes to perform any post-processing
        return ids
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
        
        # Exclude deleted records
        query = select(cls).where(cls.deleted_at.is_(None))

        # 1️⃣ Apply Filters (Supports Nested Relationships)
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

        # 2️⃣ Global Search (Across Text Fields)
        if search:
            search_expression = [
                column.ilike(f"%{search}%") for column in cls.__table__.columns if column.type.python_type == str
            ]
            if search_expression:
                query = query.where(or_(*search_expression))

        # 3️⃣ Sorting
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
