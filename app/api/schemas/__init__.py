from ..modules.auth.roles_permission.schemas import RolePermissionCreate, RolePermissionUpdate, RolePermissionResponse
from ..modules.auth.roles.schemas import RoleCreate, RoleUpdate, RoleResponse
from ..modules.auth.users.schemas import UserCreate, UserUpdate, UserResponse

'''
=====================================================
# "ModelName": [ModelCreate, ModelUpdate, ModelResponse]
# Follow the above pattern to add new schemas
=====================================================
'''

schema_names = {   
    "Role": [RoleCreate, RoleUpdate, RoleResponse],
    "RolePermission": [RolePermissionCreate, RolePermissionUpdate, RolePermissionResponse],
    "User": [UserCreate, UserUpdate, UserResponse]
}