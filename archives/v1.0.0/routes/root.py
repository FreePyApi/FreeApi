from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..config.config import settings
from ..config.api_keys import is_api_key_auth_enabled

router = APIRouter()
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@router.get("/", tags=["Root"])
def root() -> dict[str, Any]:
  version = settings.freeapi_current_version
  return {
    "message": "Welcome to the FreeAPI!",
    "version": f"v{version}",
    "documentation": f"/v{version}/docs",
  }


@router.get("/favicon.ico", include_in_schema=False, tags=["Assets"])
def favicon_ico():
  return FileResponse(ASSETS_DIR / "favicon.png")


@router.get("/favicon.svg", include_in_schema=False, tags=["Assets"])
def favicon_svg():
  return FileResponse(ASSETS_DIR / "favicon.svg")


@router.get("/status", tags=["Status"])
def get_status() -> dict[str, Any]:
  return {"status": "running", "version": settings.freeapi_current_version}


@router.get("/live", tags=["Status"])
def live() -> dict[str, Any]:
  return {"status": "alive"}


@router.get("/ready", tags=["Status"])
def ready() -> dict[str, Any]:
  return {
    "status": "ready",
    "version": settings.freeapi_current_version,
    "oauth_enabled": settings.oauth_enabled,
    "rate_limit_enabled": settings.rate_limit_enabled,
    "api_key_auth_enabled": is_api_key_auth_enabled(),
  }


@router.get("/github", tags=["Organization"])
def get_github() -> dict[str, Any]:
  return {
    "github_repo": "https://github.com/FreePyApi/FreeApi",
    "github_organization": "https://github.com/FreePyApi",
  }
