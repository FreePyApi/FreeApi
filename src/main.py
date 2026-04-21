import logging
import time
import importlib.util
import sys
import types
import re
import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config.config import settings
from .config.logging import configure_logging
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.docs_rate_limit import DocsRateLimitMiddleware
from .config.security import auth_guard
from .routes import (
  auth_router,
  datetime_router,
  geo_router,
  math_router,
  random_router,
  root_router,
  text_router,
  uuid_hashing_router,
  network_router,
)

configure_logging()
logger = logging.getLogger(__name__)

CURRENT_API_VERSION = settings.freeapi_current_version
CURRENT_API_PREFIX = f"/v{CURRENT_API_VERSION}"
VERSION_PATH_RE = re.compile(r"^/v\d+\.\d+\.\d+(?:/|$)")

app = FastAPI(
  title="FreeAPI",
  description="A Free and open source api for everyone.",
  version=CURRENT_API_VERSION,
  servers=[{"url": CURRENT_API_PREFIX, "description": "Latest stable API"}],
  docs_url="/docs",
  redoc_url="/redoc",
  openapi_url="/openapi.json",
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Expose static assets so favicon and other files are publicly reachable.
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

if settings.cors_origins:
  app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

if settings.rate_limit_enabled:
  app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
  )

if settings.oauth_enabled and settings.docs_rate_limit_enabled:
  app.add_middleware(
    DocsRateLimitMiddleware,
    max_requests=settings.docs_rate_limit_max_requests,
    window_seconds=settings.docs_rate_limit_window_seconds,
  )


@app.middleware("http")
async def request_context_and_logging(request: Request, call_next):
  request.state.timestamp = int(time.time())
  logger.info("request_started", extra={"request_id": f"{id(request)}"})
  try:
    response = await call_next(request)
  except Exception:
    logger.exception("request_failed")
    raise
  logger.info("request_finished", extra={"request_id": f"{id(request)}"})
  return response


@app.middleware("http")
async def module_error_code_to_status(request: Request, call_next):
  response = await call_next(request)

  # If a module returns {"error": ..., "code": ...}, use that code as HTTP status.
  if response.status_code >= 400:
    return response

  if response.media_type != "application/json":
    return response

  body = getattr(response, "body", None)
  if not body:
    return response

  try:
    payload = json.loads(body)
  except (TypeError, json.JSONDecodeError):
    return response

  if not isinstance(payload, dict):
    return response

  error = payload.get("error")
  code = payload.get("code")
  if isinstance(error, str) and isinstance(code, int) and not isinstance(code, bool) and 100 <= code <= 599:
    response.status_code = code

  return response

#########################
# Authentication Middleware
#########################
@app.middleware("http")
async def enforce_authentication(request: Request, call_next):
  denied = auth_guard(request)
  if denied is not None:
    return denied
  return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
  return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
  return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
  logger.exception("unhandled_exception")
  return JSONResponse(status_code=500, content={"detail": "Internal server error"})

app.include_router(root_router)
app.include_router(auth_router)
app.include_router(text_router)
app.include_router(datetime_router)
app.include_router(geo_router)
app.include_router(uuid_hashing_router)
app.include_router(math_router)
app.include_router(random_router)
app.include_router(network_router)
#########################
# Versioned Gateway Logic
#########################
def _load_archive_apps(archive_root: Path) -> list[tuple[str, FastAPI]]:
  loaded_apps: list[tuple[str, FastAPI]] = []
  if not archive_root.is_dir():
    return loaded_apps

  # Ensure a private top-level package exists so relative imports inside archives work
  base_pkg_name = "freeapi_archives"
  if base_pkg_name not in sys.modules:
    base_pkg = types.ModuleType(base_pkg_name)
    base_pkg.__path__ = [str(archive_root)]
    sys.modules[base_pkg_name] = base_pkg

  for version_dir in sorted(archive_root.iterdir()):
    if not version_dir.is_dir() or not VERSION_PATH_RE.match(f"/{version_dir.name}/"):
      continue

    version_prefix = f"/{version_dir.name}"
    if version_prefix == CURRENT_API_PREFIX:
      continue

    modules_dir = version_dir / "modules"
    routes_dir = version_dir / "routes"
    assets_dir = version_dir / "assets"
    if not modules_dir.is_dir() or not routes_dir.is_dir() or not assets_dir.is_dir():
      continue

    # Create a package name safe for Python identifiers (replace dots with underscores)
    package_name = f"{base_pkg_name}.{version_dir.name.replace('.', '_')}"

    # Ensure a package module exists so relative imports inside the archive work.
    # Keep BASE_DIR as a fallback so shared modules like config/services/models can
    # be reused without duplicating them inside each archive version.
    if package_name not in sys.modules:
      pkg = types.ModuleType(package_name)
      pkg.__path__ = [str(version_dir), str(BASE_DIR)]
      sys.modules[package_name] = pkg

    routes_package_name = f"{package_name}.routes"
    if routes_package_name not in sys.modules:
      routes_pkg = types.ModuleType(routes_package_name)
      routes_pkg.__path__ = [str(routes_dir)]
      sys.modules[routes_package_name] = routes_pkg

    archive_app = FastAPI(
      title=f"FreeAPI {version_dir.name}",
      description=f"Archived API version {version_dir.name}",
      version=version_dir.name.lstrip("v"),
      docs_url="/docs",
      redoc_url="/redoc",
      openapi_url="/openapi.json",
    )

    # Expose archived static assets as /vX.Y.Z/assets/*
    archive_app.mount("/assets", StaticFiles(directory=assets_dir), name=f"assets_{version_dir.name.replace('.', '_')}")

    try:
      for route_file in sorted(routes_dir.glob("*.py")):
        if route_file.name == "__init__.py":
          continue

        module_full_name = f"{routes_package_name}.{route_file.stem}"
        spec = importlib.util.spec_from_file_location(module_full_name, route_file)
        if spec is None or spec.loader is None:
          continue

        module = importlib.util.module_from_spec(spec)
        module.__package__ = routes_package_name
        sys.modules[module_full_name] = module
        spec.loader.exec_module(module)

        router = getattr(module, "router", None)
        if isinstance(router, APIRouter):
          archive_app.include_router(router)
    except Exception:
      logger.exception("failed_to_load_archive_app", extra={"archive_version": version_dir.name})
      for module_name in list(sys.modules.keys()):
        if module_name.startswith(f"{package_name}."):
          sys.modules.pop(module_name, None)
      sys.modules.pop(package_name, None)
      continue

    loaded_apps.append((version_prefix, archive_app))

  return loaded_apps

def _resolve_archive_root() -> Path:
  for archive_dir_name in ("archive", "archives"):
    archive_root = BASE_DIR.parent / archive_dir_name
    if archive_root.is_dir():
      return archive_root

  return BASE_DIR.parent / "archive"

def _build_versioned_gateway(current_app: FastAPI) -> FastAPI:
  gateway_app = FastAPI(
    title="FreeAPI Gateway",
    description="Version gateway for FreeAPI.",
    version=CURRENT_API_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
  )

  # Expose a small set of unversioned auth endpoints on the gateway so
  # external OAuth providers can use a stable `/auth/*` redirect URI
  # without being redirected to a versioned path.
  @gateway_app.get("/auth/status", tags=["Auth"])
  def gateway_auth_status(request: Request):
    from .config.security import is_oauth_enabled
    from .config.api_keys import is_api_key_auth_enabled
    return {
      "enabled": is_oauth_enabled(),
      "provider": "github",
      "api_key_auth_enabled": is_api_key_auth_enabled(),
    }

  @gateway_app.get("/auth/login", tags=["Auth"])
  def gateway_auth_login(request: Request):
    from .config.security import build_login_response
    return build_login_response(request)

  @gateway_app.get("/auth/login/ha", tags=["Auth"])
  def gateway_auth_login_ha(request: Request, ha_callback: str):
    from .config.security import build_ha_login_response
    return build_ha_login_response(request, ha_callback=ha_callback)

  @gateway_app.get("/auth/callback", tags=["Auth"])
  def gateway_auth_callback(request: Request, code: str, state: str):
    from .config.security import build_callback_response
    return build_callback_response(request, code=code, state=state)

  @gateway_app.get("/auth/callback/ha", tags=["Auth"])
  def gateway_auth_callback_ha(request: Request, code: str, state: str):
    from .config.security import build_ha_callback_response
    return build_ha_callback_response(request, code=code, state=state)

  @gateway_app.post("/auth/logout", tags=["Auth"])
  def gateway_auth_logout(request: Request):
    from .config.security import build_logout_response
    return build_logout_response()

  @gateway_app.get("/auth/me", tags=["Auth"])
  def gateway_auth_me(request: Request):
    from .config.security import get_authenticated_user
    user = get_authenticated_user(request)
    if user is None:
      raise HTTPException(status_code=401, detail="Authentication required")
    return {"authenticated": True, "user": user}

  @gateway_app.middleware("http")
  async def redirect_to_latest_version(request: Request, call_next):
    path = request.url.path

    # If path already contains a full semantic version (/vX.Y.Z), pass through.
    if VERSION_PATH_RE.match(path):
      return await call_next(request)

    # Build a list of available full-version prefixes (e.g. /v1.0.0, /v1.2.3)
    available = [CURRENT_API_PREFIX] + [vp for vp, _ in getattr(gateway_app, "_mounted_archives", [])]

    def parse_version_prefix(p: str):
      # p is like '/v1.2.3' -> return (major, minor, patch) or None
      m = re.match(r"^/v(\d+)\.(\d+)\.(\d+)$", p)
      if not m:
        return None
      return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    versions = []
    for p in available:
      v = parse_version_prefix(p)
      if v is not None:
        versions.append((v[0], v[1], v[2], p))

    # Helper to find the latest full version matching major and optional minor
    def find_latest(major: int, minor: Optional[int] = None) -> Optional[str]:
      candidates = [t for t in versions if t[0] == major and (minor is None or t[1] == minor)]
      if not candidates:
        return None
      # sort by (major, minor, patch)
      candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
      return candidates[0][3]

    # Match /v<major> or /v<major>.<minor>
    m_major_minor = re.match(r"^/v(\d+)\.(\d+)(/.*)?$", path)
    m_major = re.match(r"^/v(\d+)(/.*)?$", path)

    target_prefix = None
    remainder = path
    if m_major_minor:
      major = int(m_major_minor.group(1))
      minor = int(m_major_minor.group(2))
      remainder = m_major_minor.group(3) or "/"
      target_prefix = find_latest(major, minor)
    elif m_major:
      major = int(m_major.group(1))
      remainder = m_major.group(2) or "/"
      # avoid matching full vX.Y.Z (handled above)
      if re.match(r"^/v\d+\.\d+\.\d+(/.*)?$", path):
        return await call_next(request)
      target_prefix = find_latest(major, None)

    # If we found a target prefix for the short version, redirect there.
    if target_prefix:
      # ensure trailing slash handling
      target_path = f"{target_prefix}{remainder}" if remainder != "/" else f"{target_prefix}/"
      query = request.url.query
      if query:
        target_path = f"{target_path}?{query}"
      return RedirectResponse(url=target_path, status_code=307)

    # Fallback: redirect unversioned root to current API prefix
    # Do not redirect OAuth auth paths (e.g. /auth/*) so external providers
    # that use a stable unversioned redirect URI (like /auth/callback)
    # will reach the unversioned handler instead of being rewritten.
    if path == "/" or (not path.startswith("/v") and not path.startswith("/auth")):
      target_path = f"{CURRENT_API_PREFIX}{path}" if path != "/" else f"{CURRENT_API_PREFIX}/"
      query = request.url.query
      if query:
        target_path = f"{target_path}?{query}"
      return RedirectResponse(url=target_path, status_code=307)

    # No matching version found; let the app handle (likely 404)
    return await call_next(request)

  gateway_app.mount(CURRENT_API_PREFIX, current_app)

  archive_root = _resolve_archive_root()
  mounted = _load_archive_apps(archive_root)
  # keep a reference of mounted archives for middleware decisions
  setattr(gateway_app, "_mounted_archives", mounted)
  for version_prefix, archive_app in mounted:
    gateway_app.mount(version_prefix, archive_app)

  return gateway_app

app = _build_versioned_gateway(app)
