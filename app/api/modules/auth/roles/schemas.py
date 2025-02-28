from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel, Field
from typing import List, Optional

'''
=====================================================
# Role Base Schema
=====================================================
'''
class RoleBase(BaseModel):
    name: Optional[str] = Field(None, description="Name of the role")
    description: Optional[str] = Field(None, description="Description of the role")

'''
=====================================================
# Role Create Schema
=====================================================
'''
class RoleCreate(RoleBase):
    name: str = Field(..., description="Name of the role")

'''
=====================================================
# Role Update Schema
=====================================================
'''
class RoleUpdate(RoleBase, UuidModel):
   pass

'''
=====================================================
# Role Response Schema
=====================================================
'''
class RoleResponse(BaseResponseModel, CreateTime, UpdateTime, RoleBase, OptionalUuidModel):
    pass