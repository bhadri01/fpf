from app.api.modules.auth.roles_permission.schemas import RolePermissionCreate, RolePermissionUpdate, RolePermissionAllResponse, RolePermissionIdResponse
from app.api.modules.auth.roles.schemas import RoleCreate, RoleUpdate, RoleAllResponse, RoleIdResponse
from app.api.modules.auth.users.schemas import UserAllResponse, UserCreate, UserIdResponse, UserUpdate

'''
=====================================================
-----------------------------------------------------------------
| ModelCreate | ModelUpdate | ModelAllResponse | ModelIdResponse |
|-------------|-------------|------------------|-----------------|
| POST /event | PUT /event  | GET /event       | GET /event/{id} |
------------------------------------------------------------------
# Follow the above pattern to add new schemas
=====================================================
'''

schema_names = {
    "Role": [RoleCreate, RoleUpdate, RoleAllResponse, RoleIdResponse],
    "RolePermission": [RolePermissionCreate, RolePermissionUpdate, RolePermissionAllResponse, RolePermissionIdResponse],
    "User": [UserCreate, UserUpdate, UserAllResponse, UserIdResponse],
}
