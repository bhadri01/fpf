from __future__ import annotations
from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel
from typing import Optional
from pydantic import Field
import uuid

'''
=====================================================
# RolePermission Schema
=====================================================
'''

class RolePermissionBase(BaseModel):
    role_id: Optional[uuid.UUID] = Field(None, description="The unique identifier for the role")
    route: Optional[str] = Field(None, description="The route for which the permission is granted")
    method: Optional[str] = Field(None, description="The HTTP method for which the permission is granted")

class RolePermissionCreate(BaseModel):
    role_id: uuid.UUID = Field(..., description="The unique identifier for the role")
    route: str = Field(..., description="The route for which the permission is granted")
    method: str = Field(..., description="The HTTP method for which the permission is granted")

class RolePermissionUpdate(RolePermissionBase, UuidModel):
    pass

class RolePermissionResponse(BaseResponseModel, CreateTime, UpdateTime, RolePermissionBase, OptionalUuidModel):
    role: Optional['GeneralRoleResponse'] = Field(None, description="The role associated with the permission")  # ✅ Use string-based reference

class GeneralRolePermissionResponse(BaseResponseModel, CreateTime, UpdateTime, RolePermissionBase, OptionalUuidModel):
    pass

# ✅ Import AFTER class definition
from app.api.modules.auth.roles.schemas import GeneralRoleResponse

RolePermissionResponse.model_rebuild()  # ✅ Resolves forward references