from typing import List
from sqlalchemy import String, select
from sqlalchemy.orm import relationship
from app.core.database.base_model import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

'''
=====================================================
# Role table
=====================================================
'''

class Role(Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)
    users = relationship("User", back_populates="role", lazy='raise')
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan", lazy='raise')
    role_redirection = relationship("RoleRedirection", back_populates="role", cascade="all, delete-orphan", lazy='raise')
    
    __allowed__ = True


    @classmethod
    async def create(cls, session: AsyncSession, data_list: List[any]):
        for data in data_list:
            data.name = data.name.upper()
            data.description = data.description or "Default description"
        return data_list
    
    @classmethod
    async def update(cls, session: AsyncSession, data_list: List[any]):
        for data in data_list:
            existing_role = await session.execute(select(Role).where(Role.id == data.id))
            existing_role = existing_role.scalar_one_or_none()
            if existing_role and existing_role.name.upper() in ["PUBLIC", "SUPERADMIN"]:
                raise ValueError(f"Cannot modify reserved role: {existing_role.name}")
            data.name = data.name.upper()
            data.description = data.description or "Default description"
        return data_list

'''
=====================================================
# Role table definition and operations
=====================================================
'''
@event.listens_for(Role.__table__, 'after_create')
def insert_initial_roles(target, connection, **kw):
    session = Session(bind=connection)
    session.add_all([
        Role(name='PUBLIC', description='Public role with limited access'),
        Role(name='SUPERADMIN', description='Superadmin role with full access')
    ])
    session.commit()
    session.close()