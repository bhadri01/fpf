"""
This module initializes the API by importing the necessary models and their configurations.
"""

# Import models

from app.api.auth.models import Role, User

# Import model configurations
from app.api.auth.configs import role_required_roles, user_required_roles

model_configs = {
    "Role": role_required_roles,
    "User": user_required_roles
}
