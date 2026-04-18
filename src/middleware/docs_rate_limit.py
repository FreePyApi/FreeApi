import time
import asyncio
from typing import Dict
from starlette.types import ASGIApp, Receive, Scope, Send


class DocsRateLimitMiddleware:
  """Rate limit middleware for documentation endpoints.
  
  Applies when OAuth is enabled to prevent abuse while keeping docs public.
  """
  
  DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}
  
  def __init__(self, app: ASGIApp, *, max_requests: int = 1, window_seconds: int = 10):
    self.app = app
    self.max_requests = max_requests
    self.window_seconds = window_seconds
    self._clients: Dict[str, Dict[str, float]] = {}
    self._lock = asyncio.Lock()

  def _is_docs_path(self, path: str) -> bool:
    """Check if the request path is a docs endpoint."""
    return path in self.DOCS_PATHS or any(path.startswith(p + "/") for p in self.DOCS_PATHS)

  async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
    if scope.get("type") != "http":
      await self.app(scope, receive, send)
      return

    path = scope.get("path", "")
    if not self._is_docs_path(path):
      # Not a docs endpoint, pass through
      await self.app(scope, receive, send)
      return

    client = scope.get("client")
    ip = client[0] if client else "unknown"
    now = time.monotonic()

    async with self._lock:
      # Clean up expired clients
      expired_clients = [client_ip for client_ip, data in self._clients.items() if now - data["start"] > self.window_seconds]
      for client_ip in expired_clients:
        del self._clients[client_ip]

      data = self._clients.get(ip)
      if not data:
        # First request in window
        self._clients[ip] = {"count": 1.0, "start": now}
      else:
        # Reset window if expired
        if now - data["start"] > self.window_seconds:
          self._clients[ip] = {"count": 1.0, "start": now}
        else:
          data["count"] += 1.0

      count = self._clients[ip]["count"]

    if count > self.max_requests:
      # Rate limit exceeded, return 429
      from starlette.responses import JSONResponse

      body = {"detail": "Rate limit exceeded for documentation. Try again later."}
      response = JSONResponse(body, status_code=429)
      await response(scope, receive, send)
      return

    await self.app(scope, receive, send)
