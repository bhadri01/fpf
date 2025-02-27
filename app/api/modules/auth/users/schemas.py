from __future__ import annotations
from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

'''
=====================================================
# User Schema
=====================================================
'''

class UserBase(BaseModel):
    username: Optional[str] = Field(None, description="Username of the user")
    email: Optional[EmailStr] = Field(None, description="Email address of the user")
    status: Optional[str] = Field(None, description="Current status of the user")
    avatar: Optional[str] = Field(None, description="Avatar URL of the user")
    status_2fa: Optional[bool] = Field(None, description="2FA status of the user")

class UserCreate(BaseModel):
    username: str = Field(..., description="Username of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., min_length=8, description="Password for the user")
    role_id: uuid.UUID = Field(..., description="Role ID associated with the user")

class UserUpdate(UserBase, UuidModel):
    role_id: Optional[uuid.UUID] = Field(None, description="Role ID associated with the user")
    password: Optional[str] = Field(None, min_length=8, description="Password for the user")

class UserResponse(BaseResponseModel, CreateTime, UpdateTime, UserBase, OptionalUuidModel):
    role: Optional['GeneralRoleResponse'] = Field(None, description="Role associated with the user")  # ✅ Use string-based reference

class GeneralUserResponse(BaseResponseModel, CreateTime, UpdateTime, UserBase, OptionalUuidModel):
    pass

# ✅ Import AFTER class definition
from app.api.modules.auth.roles.schemas import GeneralRoleResponse

UserResponse.model_rebuild()  # ✅ Resolves forward references