from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.orm import validates
from enum import Enum as PyEnum
from app.utils.security import get_password_hash
from sqlalchemy.orm import Mapped, mapped_column


class UserStatus(PyEnum):
    PENDING = "pending_confirmation"
    PAUSED = "paused"
    BLOCKED = "blocked"
    ACTIVE = "active"


class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    users = relationship("User", back_populates="role")

    @validates('name')
    def convert_upper(self, key, value):
        return value.upper()


class User(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    _password: Mapped[str] = mapped_column("password", String, nullable=False)
    status: Mapped[str] = mapped_column(String, default=UserStatus.PENDING.value, nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role = relationship("Role", back_populates="users", lazy="joined")

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, plain_password):
        self._password = get_password_hash(plain_password)
