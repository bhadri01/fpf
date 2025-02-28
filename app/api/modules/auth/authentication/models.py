from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database.base_model import Base
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship

'''
=====================================================
# APIKey table
=====================================================
'''
class APIKey(Base):
    __tablename__ = "api_keys"

    user_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    user = relationship("User", back_populates="api_keys")
    __allowed__ = True

'''
=====================================================
# RolePermission table
=====================================================
'''
class RoleRedirection(Base):
    __tablename__ = "role_redirection"
    role_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), unique=True, nullable=False)
    redirect: Mapped[str] = mapped_column(String, nullable=False)
    role = relationship("Role", back_populates="role_redirection")
    __allowed__ = True
