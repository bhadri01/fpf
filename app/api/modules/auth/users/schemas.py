from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid

'''
=====================================================
# User Base Schema
=====================================================
'''
class UserBase(BaseModel):
    username: Optional[str] = Field(None, description="Username of the user")
    email: Optional[EmailStr] = Field(None, description="Email address of the user")
    status: Optional[str] = Field(None, description="Current status of the user")
    avatar: Optional[str] = Field(None, description="Avatar URL of the user")
    status_2fa: Optional[bool] = Field(None, description="2FA status of the user")


'''
=====================================================
# User Schema
=====================================================
'''
class UserCreate(BaseModel):
    username: str = Field(..., description="Username of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password for the user")
    role_id: uuid.UUID = Field(...,description="Role ID associated with the user")


'''
=====================================================
# User Update Schema
=====================================================
'''
class UserUpdate(UserBase, UuidModel):
    role_id: Optional[uuid.UUID] = Field(None, description="Role ID associated with the user")
    password: Optional[str] = Field(None, description="Password for the user")


'''
=====================================================
# User Role Response Schema
=====================================================
'''
class UserRoleResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Unique identifier for the role")
    name: str = Field(..., description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role")


'''
=====================================================
# User All Response Schema
=====================================================
'''
class UserAllResponse(BaseResponseModel, CreateTime, UpdateTime, UserBase, OptionalUuidModel):
    role: Optional[UserRoleResponse] = Field(None, description="Role associated with the user")


'''
=====================================================
# User Id Response Schema
=====================================================
'''
class UserIdResponse(BaseResponseModel, CreateTime, UpdateTime, UserBase, OptionalUuidModel):
    role: Optional[UserRoleResponse] = Field(None, description="Role associated with the user")
