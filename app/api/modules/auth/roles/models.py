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


    '''
    =====================================================
    # Before Create method for Role table
    =====================================================
    '''
    @classmethod
    async def create(cls, session: AsyncSession, data_list: List[any]):
        print("Before Role created")
        for data in data_list:
            data.name = data.name.upper()
            data.description = data.description or "Default description"
        return await super().create(session, data_list)
    
    '''
    =====================================================
    # Before Update method for Role table
    =====================================================
    '''
    @classmethod
    async def update(cls, session: AsyncSession, data_list: List[any]):
        for data in data_list:
            # Check if the role is reserved
            existing_role = await session.execute(select(Role).where(Role.id == data.id))
            existing_role = existing_role.scalar_one_or_none()
            if existing_role and existing_role.name.upper() in ["PUBLIC", "SUPERADMIN"]:
                raise ValueError(f"Cannot modify reserved role: {existing_role.name}")
            data.name = data.name.upper()
            data.description = data.description or "Default description"
        return await super().update(session, data_list)

'''
=====================================================
# Role table definition and operations
=====================================================
'''
@event.listens_for(Role.__table__, 'after_create')
def insert_initial_roles(target, connection, **kw):
    session = Session(bind=connection)
    session.add_all([
        Role(name='PUBLIC', description='Role with limited access for general users'),
        Role(name='SUPERADMIN', description='Role with full access for super administrators'),
    ])
    session.commit()
    session.close()