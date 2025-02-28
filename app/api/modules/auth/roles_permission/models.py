from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UUID, ForeignKey, String
from app.core.database.base_model import Base
from sqlalchemy.orm import relationship
import uuid

'''
=====================================================
# RolePermission table
=====================================================
'''
class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True),ForeignKey("roles.id"), nullable=False)
    route: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    role = relationship("Role", back_populates="permissions", lazy='raise')
    __allowed__ = True