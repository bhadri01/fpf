from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.modules.auth.roles_permission.models import RolePermission
from app.core.redis import redis_cache

PERMISSION_CACHE_KEY = "permission_cache"  # Redis key to store permissions


async def load_permissions(db: AsyncSession):
    """
    Load permissions from the database and store them in Redis cache.
    """
    query = select(RolePermission).options(selectinload(RolePermission.role))
    result = await db.execute(query)
    permissions = result.scalars().all()

    temp_cache = {}  # Temporary dictionary to store permissions before pushing to Redis

    for permission in permissions:
        role = permission.role.name
        route = permission.route
        method = permission.method

        if role not in temp_cache:
            temp_cache[role] = {}
        if route not in temp_cache[role]:
            temp_cache[role][route] = []
        if method not in temp_cache[role][route]:
            temp_cache[role][route].append(method)

    # Store in Redis with an expiration of 10 minutes (600 seconds)
    await redis_cache.set(PERMISSION_CACHE_KEY, temp_cache, ttl=600)
