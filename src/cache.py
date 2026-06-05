import hashlib
import json
from typing import Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from src.config import REDIS_URL


class Cache:
    def __init__(self) -> None:
        self._client = None

    async def connect(self) -> None:
        if aioredis is None:
            print("WARNING: redis non installe, cache desactive")
            return
        self._client = aioredis.from_url(REDIS_URL, decode_responses=True)

    def _key(self, job: str, cv_text: str) -> str:
        h = hashlib.md5((job + cv_text).encode()).hexdigest()
        return f"score:{h}"

    async def get(self, job: str, cv_text: str) -> Optional[dict]:
        if not self._client:
            return None
        val = await self._client.get(self._key(job, cv_text))
        return json.loads(val) if val else None

    async def set(self, job: str, cv_text: str, data: dict, ttl: int = 3600) -> None:
        if not self._client:
            return
        await self._client.setex(self._key(job, cv_text), ttl, json.dumps(data))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
