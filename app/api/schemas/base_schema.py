from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


'''
=====================================================
# Base schema for UUID model
=====================================================
'''
class UuidModel(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the model")

class OptionalUuidModel(BaseModel):
    id: Optional[UUID] = Field(None, description="Unique identifier for the model")

'''
=====================================================
# Schema for Create, Update, Delete Time
=====================================================
'''
class CreateTime(BaseModel):
    created_at: Optional[datetime] = Field(None, description="Timestamp of when the role was created")

class UpdateTime(BaseModel):
    updated_at: Optional[datetime] = Field(None, description="Timestamp of the last update to the role")

class DeleteTime(BaseModel):
    deleted_at: Optional[datetime] = Field(None, description="Timestamp of when the role was deleted")

'''
=====================================================
# Schema for tracking user actions (Create, Update, Delete)
=====================================================
'''
class CreateBy(BaseModel):
    created_by: Optional[str] = Field(None, description="User who created the role")

class UpdateBy(BaseModel):
    updated_by: Optional[str] = Field(None, description="User who last updated the role")
    
class DeleteBy(BaseModel):
    deleted_by: Optional[str] = Field(None, description="User who deleted the role")

'''
=====================================================
# Base response model configuration
=====================================================
'''
class BaseResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


'''
=====================================================
# Base response model configuration
=====================================================
'''
T = TypeVar("T")
class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int