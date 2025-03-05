from sqlalchemy import UUID, Boolean, String, ForeignKey, select
from app.api.modules.auth.roles.models import Role
from app.utils.password_utils import get_password_hash
from app.utils.avatar import generate_pixel_avatar
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.base_model import Base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from pydantic import BaseModel
from typing import List
import uuid


'''
=====================================================
# UserStatus Enum List
=====================================================
'''
class UserStatus(PyEnum):
    PENDING = "pending"
    PAUSED = "paused"
    BLOCKED = "blocked"
    ACTIVE = "active"

'''
=====================================================
# User table
=====================================================
'''
class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=UserStatus.PENDING.value, nullable=False)
    avatar = mapped_column(String, nullable=True)
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users", lazy='selectin')
    api_keys = relationship("APIKey", back_populates="user", lazy='raise')
    
    # 2FA fields
    status_2fa: Mapped[bool] = mapped_column(Boolean, default=False)
    secret_2fa: Mapped[str] = mapped_column(String, nullable=True)
    
    __allowed__ = True

    '''
    =====================================================
    # Create method for User table
    =====================================================
    '''
    @classmethod
    async def create(cls, session: AsyncSession, data_list: List[any]):
        processed_data = []
        for data in data_list:
            if isinstance(data, BaseModel):  # Convert Pydantic to dictionary
                data = data.model_dump(exclude_unset=True)
            # 🔥 Hash password & generate avatar
            if len(data["password"]) < 8:
                raise ValueError("Password must be at least 8 characters long")
            data["password"] = get_password_hash(data["password"])
            data["avatar"] = generate_pixel_avatar(data["email"])
            data["status"] = UserStatus.PENDING.value
            if "role_id" not in data:
                default_role = await session.execute(
                    select(Role).where(Role.name == "USER")
                )
                default_role = default_role.scalars().first()
                if not default_role:
                    raise ValueError("Default role 'User' not found")
                data["role_id"] = default_role.id

            processed_data.append(data)

        return await super().create(session, processed_data) 
    
    '''
    =====================================================
    # Before Update method for User table
    =====================================================
    '''

    @classmethod
    async def update(cls, session: AsyncSession, data_list: List[any]):
        processed_data = []
        
        for data in data_list:
            # ✅ Convert Pydantic model to dictionary if necessary
            if isinstance(data, BaseModel):
                data = data.model_dump(exclude_unset=True)

            obj_id = data.pop("id", None)  # Extract object ID
            if not obj_id:
                continue  # Skip if no ID provided

            # ✅ Modify fields before updating
            if "password" in data and data["password"]:
                if len(data["password"]) < 8:
                    raise ValueError("Password must be at least 8 characters long")
                data["password"] = get_password_hash(data["password"])

            processed_data.append({"id": obj_id, **data})

        return await super().update(session, processed_data)
