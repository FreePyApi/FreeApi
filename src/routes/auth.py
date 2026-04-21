from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Request

from ..config.api_keys import create_api_key, delete_api_key, is_api_key_auth_enabled, list_api_keys
from ..config.security import (
  build_callback_response,
  build_ha_callback_response,
  build_ha_login_response,
  build_login_response,
  build_logout_response,
  is_oauth_enabled,
)
from ..models.auth import ApiKeyCreateRequest
from ..services.auth import require_authenticated_user

router = APIRouter()


@router.get("/auth/status", tags=["Auth"])
def auth_status() -> dict[str, Any]:
  return {
    "enabled": is_oauth_enabled(),
    "provider": "github",
    "api_key_auth_enabled": is_api_key_auth_enabled(),
  }


@router.get("/auth/login", tags=["Auth"])
def auth_login(request: Request):
  return build_login_response(request)


@router.get("/auth/login/ha", tags=["Auth"])
def auth_login_ha(request: Request, ha_callback: str):
  return build_ha_login_response(request, ha_callback=ha_callback)


@router.get("/auth/callback", tags=["Auth"])
def auth_callback(request: Request, code: str, state: str):
  return build_callback_response(request, code=code, state=state)


@router.get("/auth/callback/ha", tags=["Auth"])
def auth_callback_ha(request: Request, code: str, state: str):
  return build_ha_callback_response(request, code=code, state=state)


@router.post("/auth/logout", tags=["Auth"])
def auth_logout():
  return build_logout_response()


@router.get("/auth/me", tags=["Auth"])
def auth_me(request: Request) -> dict[str, Any]:
  user = require_authenticated_user(request)
  return {"authenticated": True, "user": user}


@router.post("/auth/api-keys", tags=["Auth"])
def auth_create_api_key(request: Request, payload: ApiKeyCreateRequest) -> dict[str, Any]:
  user = require_authenticated_user(request)
  return create_api_key(user=user, description=payload.description, expires_at=payload.expires_at)


@router.get("/auth/api-keys", tags=["Auth"])
def auth_list_api_keys(request: Request) -> dict[str, Any]:
  user = require_authenticated_user(request)
  return list_api_keys(user=user)


@router.delete("/auth/api-keys/{key_uuid}", tags=["Auth"])
def auth_delete_api_key(request: Request, key_uuid: uuid.UUID) -> dict[str, Any]:
  user = require_authenticated_user(request)
  return delete_api_key(user=user, key_uuid=key_uuid)
