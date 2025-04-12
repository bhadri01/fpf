"""
This module initializes the API by importing the necessary models and their configurations.
"""

# Import models

from ..modules.auth.roles.models import Role
from ..modules.auth.roles_permission.models import RolePermission
from ..modules.auth.users.models import User
from ..modules.auth.authentication.models import APIKey
from ..modules.auth.dropdown_script.Dropdown_Models.country_state_district.models import Country,State,District

__all__ = ["Role", "User", "RolePermission", "APIKey","Country","State","District"]