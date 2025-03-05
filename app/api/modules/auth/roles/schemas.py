from app.api.schemas.base_schema import BaseResponseModel, CreateTime, OptionalUuidModel, UpdateTime, UuidModel
from pydantic import BaseModel, Field
from typing import Optional

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
# Role All Response Schema
=====================================================
'''
class RoleAllResponse(BaseResponseModel, CreateTime, UpdateTime, RoleBase, OptionalUuidModel):
    pass

'''
=====================================================
# Role Id Response Schema
=====================================================
'''
class RoleIdResponse(BaseResponseModel, CreateTime, UpdateTime, RoleBase, OptionalUuidModel):
    pass