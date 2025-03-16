from fastapi import APIRouter, HTTPException, Query, Depends, Path, Request, status
from app.api.schemas.base_schema import Page
from app.core.database.db import get_read_session, get_write_session
from app.generator.utils.generate_file import csv_file_response
from app.generator.utils.pagination import paginate_query
from app.generator.schema.registry import get_schemas
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.base_model import Base
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from app.core.redis import redis_cache
from typing import Optional, List
from uuid import UUID
import pandas as pd
import hashlib



def create_crud_routes(model: Base) -> APIRouter:

    SchemaCreate, SchemaUpdate, SchemaAllResponse, SchemaIdResponse = get_schemas(model)
    router = APIRouter(tags=[model.__name__.capitalize()])
    '''
    =====================================================
    # Routes for Download Data as CSV
    =====================================================
    '''
    @router.get("/download", response_class=FileResponse, name=model.__name__.capitalize())
    async def download_all(
        request: Request,
        filters: Optional[str] = Query(
            None, description="A JSON string representing filter conditions."),
        sort: Optional[str] = Query(
            None, description="A string representing sort field and direction in the format 'field:direction'."),
        search: Optional[str] = Query(
            None, description="A string for global search across string fields."),
        session: AsyncSession = Depends(get_read_session),
        file_format: str = Query(
            "csv", description="The format of the downloaded file (csv or excel)."),
    ):
        """
        download all records with optional filtering, sorting, and searching to a file (CSV or Excel).
        """
        cache_key = f"{model.__name__.lower()}_list_{hashlib.md5(str(filters).encode()).hexdigest()}_{sort}_{search}_{file_format}_download"

        # Check if download data is cached in Redis
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            return csv_file_response(cached_data, model.__name__.lower())

        query = await model.get_records(filters, sort, search)
        results = await session.execute(query)
        result = results.scalars().all()
        # Convert records to DataFrame
        df = pd.DataFrame(jsonable_encoder(result))
        # Reorder columns based on model definition
        model_columns = [column.name for column in model.__table__.columns]
        first_columns = ['id']
        last_columns = ['created_at', 'updated_at',
                        'deleted_at', 'created_by', 'updated_by', 'deleted_by']
        middle_columns = [
            col for col in model_columns if col not in first_columns + last_columns]
        ordered_columns = first_columns + middle_columns + last_columns
        df = df[ordered_columns]

        data_dict = jsonable_encoder(df.to_dict(orient="records"))
        await redis_cache.set(cache_key, data_dict, ttl=300)
        return csv_file_response(data_dict, model.__name__.lower())

    '''
    =====================================================
    # Routes for retrieving data from the database
    =====================================================
    '''
    @router.get("", response_model=Page[SchemaAllResponse], name=model.__name__.capitalize())
    async def read_all(
        request: Request,
        filters: Optional[str] = Query(
            None, description="A JSON string representing filter conditions.",
            json_schema_extra={
            "example": '',  # Multi-line example
            # Hint for rendering (Swagger UI may need customization)
            "style": ""
            }),
        sort: Optional[str] = Query(
            None, description="A string representing sort field and direction in the format 'field:direction'."),
        search: Optional[str] = Query(
            None, description="A string for global search across string fields."),
        page: int = Query(1, description="Page number"),
        size: int = Query(50, description="Number of items per page"),
        session: AsyncSession = Depends(get_read_session),
    ):
        """
        Retrieve paginated records with optional filtering, sorting, and searching.
        """

        cache_key = f"{model.__name__.lower()}_list_{hashlib.md5(str(filters).encode()).hexdigest()}_{sort}_{search}_page_{page}_size_{size}"
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            return cached_data  # Return cached paginated response

        query = await model.get_records(filters, sort, search)
        response_data = await paginate_query(session, query, page, size)
        response_dict = jsonable_encoder(
            response_data, exclude_unset=True, exclude_none=True)

        await redis_cache.set(cache_key, response_dict, ttl=300)
        return response_dict

    '''
    =====================================================
    # Route for retrieving a single record by ID
    =====================================================
    '''
    @router.get("/{id}", response_model=SchemaIdResponse, status_code=status.HTTP_200_OK, name=model.__name__.capitalize())
    async def read_one(
        request: Request,
        id: str = Path(..., description="The ID of the record to retrieve."),
        session: AsyncSession = Depends(get_read_session),
    ):
        """
        Retrieve a single record by its ID.
        """
        cache_key = f"{model.__name__.lower()}_detail_{id}"
        cached_data = await redis_cache.get(cache_key)
        if cached_data:
            return cached_data  # Return cached response

        data = await model.get_record_by_id(session, id)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"{model.__name__} with ID {id} not found")
        result_dict = jsonable_encoder(
            data, exclude_unset=True, exclude_none=True)
        await redis_cache.set(cache_key, result_dict, ttl=300)
        return result_dict

    '''
    =====================================================
    # Routes for creating new records in the database
    =====================================================
    '''
    @router.post("", status_code=status.HTTP_201_CREATED, name=model.__name__.capitalize())
    async def bulk_create(
        request: Request,
        items: List[SchemaCreate],
        session: AsyncSession = Depends(get_write_session),
    ):
        """
        Create multiple new records in bulk and invalidate cached list.
        """
        count = await model.create(session, items)

        # ✅ Batch cache deletion
        await redis_cache.delete_pattern(f"{model.__name__.lower()}_list_*")
        return {
            "detail": "Data created successfully",
            "count": count,
        }

    '''
    =====================================================
    # Route for updating multiple records in bulk
    =====================================================
    '''
    @router.put("", status_code=status.HTTP_200_OK, name=model.__name__.capitalize())
    async def bulk_update(
        request: Request,
        items: list[SchemaUpdate],
        session: AsyncSession = Depends(get_write_session),
    ):
        """
        Update multiple existing records in bulk.
        """
        if not items:
            raise HTTPException(
                status_code=400, detail="No data provided for update"
            )

        ids = [item.id for item in items]

        count = await model.update(session, items)
        if count == 0:
            raise HTTPException(
                status_code=404, detail="No matching records found for update"
            )

        # Batch Redis cache deletion for updated items
        cache_keys = [f"{model.__name__.lower()}_detail_{id}_*" for id in ids]
        await redis_cache.delete_many(cache_keys)
        await redis_cache.delete_pattern(f"{model.__name__.lower()}_list_*")

        return {"detail": "Data updated successfully", "count": count}

    '''
    =====================================================
    # Route for deleting multiple records in bulk
    =====================================================
    '''
    @router.delete("", status_code=status.HTTP_200_OK, name=model.__name__.capitalize())
    async def bulk_delete(
        request: Request,
        ids: list[UUID],
        hard_delete: bool = Query(
            False, description="Set to True for hard delete (only allowed for SUPERADMIN)"),
        session: AsyncSession = Depends(get_write_session),
    ):
        """
        Delete multiple records by their IDs.
        Soft delete by default, hard delete only if the user is SUPERADMIN.
        """
        if not ids:
            raise HTTPException(
                status_code=400, detail="No IDs provided for deletion")

        # Get user role from request

        if hard_delete:
            if not hasattr(request.state, 'user') or not hasattr(request.state.user, 'role'):
                raise HTTPException(
                    status_code=403, detail="User role information is missing")
            user_role = request.state.user.role.name
            if user_role != "SUPERADMIN":
                raise HTTPException(
                    status_code=403, detail="Only SUPERADMIN can perform hard delete")

            result = await model.hard_delete(session, ids)
        else:
            result = await model.soft_delete(session, ids)

        if result == 0:
            raise HTTPException(
                status_code=404, detail="No matching records found")

        cache_keys = [f"{model.__name__.lower()}_detail_{id}_*" for id in ids]
        await redis_cache.delete_many(cache_keys)
        await redis_cache.delete_pattern(f"{model.__name__.lower()}_list_*")

        return {"detail": "Data deleted successfully", "count": result}

    return router