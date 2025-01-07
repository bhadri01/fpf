from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import add_pagination
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db_session
from app.utils.filtering import parse_filters
from app.utils.security import get_current_active_user_with_roles
from typing import Type, Optional, Dict, List
from fastapi import status
import json


def create_crud_routes(
    model: Type,
    schema_create: Type,
    schema_update: Type,
    schema_response: Type,
    tags: Optional[list] = None,
    required_roles: Optional[Dict[str, List[str]]] = None,
) -> APIRouter:
    router = APIRouter(tags=tags or [model.__name__.capitalize()])

    def parse_filter_query(filters: Optional[str]) -> Optional[dict]:
        if filters:
            try:
                return json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid filter JSON")
        return None

    @router.get("", response_model=Page[schema_response])
    async def read_all(
        filters: Optional[str] = Query(None),
        sort: Optional[str] = Query(None),
        session: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_active_user_with_roles(
            required_roles.get("read_all", []))),
    ):
        try:
            # Parse filters
            parsed_filters = parse_filter_query(filters)
            filter_expression = parse_filters(
                model, parsed_filters) if parsed_filters else None

            # Base query
            query = select(model)
            if filter_expression is not None:
                query = query.where(filter_expression)

            # Handle sorting
            if sort:
                try:
                    sort_field, sort_direction = sort.split(":")
                    if sort_direction.lower() not in ["asc", "desc"]:
                        raise ValueError(
                            "Invalid sort direction. Use 'asc' or 'desc'.")
                    column = getattr(model, sort_field, None)
                    if column is None:
                        raise ValueError(f"Invalid sort field: {sort_field}")
                    query = query.order_by(
                        asc(column) if sort_direction.lower() == "asc" else desc(column))
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=str(e))

            # Use pagination library for consistent paginated responses
            return await paginate(session, query)
        except SQLAlchemyError as e:
            error_message = str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else str(e)
            if "DETAIL:" in error_message:
                error_message = error_message.replace("DETAIL:", "").strip()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{id}", response_model=schema_response, status_code=status.HTTP_200_OK)
    async def read_one(
        id: str,
        session: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_active_user_with_roles(
            required_roles.get("read_one", []))),
    ):
        try:
            query = select(model).where(model.id == id)
            result = await session.execute(query)
            data = result.scalar_one_or_none()
            if not data:
                raise HTTPException(status_code=404, detail="Data not found")
            return data
        except SQLAlchemyError as e:
            error_message = str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else str(e)
            if "DETAIL:" in error_message:
                error_message = error_message.replace("DETAIL:", "").strip()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("", status_code=status.HTTP_201_CREATED)
    async def create(
        item: schema_create,
        session: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_active_user_with_roles(
            required_roles.get("create", []))),
    ):
        try:
            obj = model(**item.dict())
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return {"detail": "Data created successfully"}
        except SQLAlchemyError as e:
            error_message = str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else str(e)
            if "DETAIL:" in error_message:
                error_message = error_message.replace("DETAIL:", "").strip()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/{id}", status_code=status.HTTP_200_OK)
    async def update(
        id: str,
        item: schema_update,
        session: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_active_user_with_roles(
            required_roles.get("update", []))),
    ):
        try:
            query = select(model).where(model.id == id)
            result = await session.execute(query)
            db_obj = result.scalar_one_or_none()
            if not db_obj:
                raise HTTPException(status_code=404, detail="Data not found")

            update_data = item.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_obj, key, value)

            await session.commit()
            await session.refresh(db_obj)
            return {"detail": "Data updated successfully"}
        except SQLAlchemyError as e:
            error_message = str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else str(e)
            if "DETAIL:" in error_message:
                error_message = error_message.replace("DETAIL:", "").strip()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/{id}", status_code=status.HTTP_200_OK)
    async def delete(
        id: str,
        session: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_active_user_with_roles(
            required_roles.get("delete", []))),
    ):
        try:
            query = select(model).where(model.id == id)
            result = await session.execute(query)
            db_obj = result.scalar_one_or_none()
            if not db_obj:
                raise HTTPException(status_code=404, detail="Data not found")

            await session.delete(db_obj)
            await session.commit()
            return {"detail": "Data deleted successfully"}
        except SQLAlchemyError as e:
            error_message = str(e).split("\n")[1] if len(str(e).split("\n")) > 1 else str(e)
            if "DETAIL:" in error_message:
                error_message = error_message.replace("DETAIL:", "").strip()
            raise HTTPException(status_code=500, detail=error_message)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return add_pagination(router)
