from typing import Any

from fastapi import HTTPException, Request

from ..config.security import get_authenticated_user


def require_authenticated_user(request: Request) -> dict[str, Any]:
  user = get_authenticated_user(request)
  if user is None:
    raise HTTPException(status_code=401, detail="Authentication required")
  return user
