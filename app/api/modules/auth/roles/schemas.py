from __future__ import annotations
from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel, Field
from typing import List, Optional

'''
=====================================================
# Role Schema
=====================================================
'''

class RoleBase(BaseModel):
    name: Optional[str] = Field(None, description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role")

class RoleCreate(RoleBase):
    name: str = Field(..., description="Name of the role")

class RoleUpdate(RoleBase, UuidModel):
   pass

class RoleResponse(BaseResponseModel, CreateTime, UpdateTime, RoleBase, OptionalUuidModel):
    users: Optional[List['GeneralUserResponse']] = Field(None, description="Users associated with the role")  # ✅ Use string-based reference
    permissions: Optional[List['GeneralRolePermissionResponse']] = Field(None, description="Permissions associated with the role")  # ✅ Use string-based reference


# This response model includes users and permissions associated with the role, providing a comprehensive view of the role's associations
class GeneralRoleResponse(BaseResponseModel, CreateTime, UpdateTime, RoleBase, OptionalUuidModel):
    pass

# ✅ Import AFTER class definition
from app.api.modules.auth.users.schemas import GeneralUserResponse
from app.api.modules.auth.roles_permission.schemas import GeneralRolePermissionResponse

RoleResponse.model_rebuild()  # ✅ Resolves forward references