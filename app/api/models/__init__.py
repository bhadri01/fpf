"""
This module initializes the API by importing the necessary models and their configurations.
"""

# Import models

from ..modules.auth.roles.models import Role
from ..modules.auth.roles_permission.models import RolePermission
from ..modules.auth.users.models import User
from ..modules.auth.authentication.models import APIKey

__all__ = ["Role", "User", "RolePermission", "APIKey"]