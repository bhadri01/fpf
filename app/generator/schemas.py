from pydantic import BaseModel, create_model
from sqlalchemy import inspect
from datetime import datetime, timezone, timedelta
from typing import Optional

# Define IST timezone
IST = timezone(timedelta(hours=5, minutes=30))


def generate_schemas(model):
    # Inspect SQLAlchemy model columns
    mapper = inspect(model)

    # Identify all fields in the SQLAlchemy model
    fields = {
        column.key: (Optional[column.type.python_type], None) if column.nullable else (
            column.type.python_type, ...)
        for column in mapper.columns
    }

    # Exclude fields for Create and Update schemas
    exclude_fields = ["id", "created_at", "updated_at", "created_by", "updated_by"]
    create_fields = {
        key: value
        for key, value in fields.items()
        if key not in exclude_fields
    }

    update_fields = {
        key: (Optional[value[0]], None)
        for key, value in fields.items()
        if key not in exclude_fields
    }

    # Dynamically create Pydantic models for Create and Update
    SchemaCreate = create_model(f"{model.__name__}Create", **create_fields)
    SchemaUpdate = create_model(f"{model.__name__}Update", **update_fields)

    # Exclude sensitive fields from the Response schema
    response_exclude_fields = {"password", "created_by", "updated_by"}
    response_fields = {
        key: (Optional[value[0]], None)
        for key, value in fields.items()
        if key not in response_exclude_fields
    }

    # Define a base response schema
    class BaseResponse(BaseModel):
        id: Optional[str] = None
        created_at: Optional[datetime] = None
        updated_at: Optional[datetime] = None

        class Config:
            from_attributes = True
            json_encoders = {
                datetime: lambda v: v.astimezone(IST).isoformat(),
            }

    # Create the Response schema with non-sensitive fields
    SchemaResponse = create_model(
        f"{model.__name__}Response",
        __base__=BaseResponse,
        **response_fields
    )

    return SchemaCreate, SchemaUpdate, SchemaResponse
