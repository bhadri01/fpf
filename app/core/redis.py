import redis.asyncio as redis
import json
import asyncio  # ✅ Import asyncio for concurrent operations
from app.core.config import settings

# Redis Configuration
REDIS_URL = settings.redis_url  # Example: "redis://localhost:6379"


class RedisCache:
    def __init__(self):
        self.redis = None

    async def connect(self):
        """Establish Redis connection."""
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    async def get(self, key):
        """Retrieve value from Redis."""
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set(self, key, value, ttl=600):
        """Store value in Redis with expiration."""
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key):
        """Delete a single key from Redis."""
        await self.redis.delete(key)

    async def delete_many(self, keys: list):
        """Delete multiple keys by pattern concurrently."""
        if keys:
            tasks = []
            for pattern in keys:
                async for key in self.redis.scan_iter(pattern):
                    tasks.append(self.redis.delete(key))
                await asyncio.gather(*tasks)

    async def delete_pattern(self, pattern):
        """Delete all keys matching a pattern using SCAN."""
        async for key in self.redis.scan_iter(pattern):
            await self.redis.delete(key)

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


# Create a global RedisCache instance
redis_cache = RedisCache()

