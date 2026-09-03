import os
import redis
import redis.asyncio as aioredis

# Shared state store for anything that needs to be visible to every
# app-backend replica, not just the process that created it (analysis job
# progress, live-view WebSocket fan-out). Without this, in-memory Python
# dicts/lists are per-replica and a request landing on a different replica
# than the one running a background task sees nothing.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
redis_async_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
