import asyncio
import time
from typing import Dict

from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import settings

class RateLimitMiddleware:
  def __init__(self, app: ASGIApp, *, max_requests: int = 60, window_seconds: int = 60):
    self.app = app
    self.max_requests = max_requests
    self.window_seconds = window_seconds
    self._clients: Dict[str, Dict[str, float]] = {}
    self._lock = asyncio.Lock()
    self._redis_client = None
    self._redis_lock = asyncio.Lock()

  async def _get_redis_client(self):
    if not settings.redis_url:
      return None

    async with self._redis_lock:
      if self._redis_client is not None:
        return self._redis_client

      try:
        import redis.asyncio as redis_asyncio

        self._redis_client = redis_asyncio.from_url(settings.redis_url, decode_responses=True)
      except Exception:
        self._redis_client = None

      return self._redis_client

  async def _get_redis_count(self, ip: str) -> int | None:
    redis_client = await self._get_redis_client()
    if redis_client is None:
      return None

    key = f"rate_limit:{ip}"
    try:
      count = await redis_client.incr(key)
      if count == 1:
        await redis_client.expire(key, self.window_seconds)
      return int(count)
    except Exception:
      return None

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope.get("type") != "http":
      await self.app(scope, receive, send)
      return

    client = scope.get("client")
    ip = client[0] if client else "unknown"
    count = await self._get_redis_count(ip)
    if count is None:
      now = time.monotonic()

      async with self._lock:
        expired_clients = [client_ip for client_ip, data in self._clients.items() if now - data["start"] > self.window_seconds]
        for client_ip in expired_clients:
          del self._clients[client_ip]

        data = self._clients.get(ip)
        if not data:
          # store count and window_start
          self._clients[ip] = {"count": 1.0, "start": now}
        else:
          # reset window if expired
          if now - data["start"] > self.window_seconds:
            self._clients[ip] = {"count": 1.0, "start": now}
          else:
            data["count"] += 1.0

        count = int(self._clients[ip]["count"])

    if count > self.max_requests:
      # Rate limit exceeded, return 429
      from starlette.responses import JSONResponse

      body = {"detail": "Rate limit exceeded. Try again later."}
      response = JSONResponse(body, status_code=429)
      await response(scope, receive, send)
      return

    await self.app(scope, receive, send)
