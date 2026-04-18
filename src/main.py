from fastapi import Body, FastAPI, Request, HTTPException, Query, Path as ParamPath
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import importlib.util
import os
from pathlib import Path
import re
from typing import Optional

from .middleware.rate_limit import RateLimitMiddleware
from .security import (
  auth_guard,
  build_callback_response,
  build_login_response,
  build_logout_response,
  get_authenticated_user,
  is_oauth_enabled,
  is_rate_limit_enabled,
)

CURRENT_API_VERSION = os.getenv("FREEAPI_CURRENT_VERSION", "1.0.0")
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

if is_rate_limit_enabled():
  app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)

#########################
# Authentication Middleware
#########################
@app.middleware("http")
async def enforce_authentication(request: Request, call_next):
  denied = auth_guard(request)
  if denied is not None:
    return denied
  return await call_next(request)

#########################
# Root and Utility Endpoints
#########################
@app.get("/", tags=["Root"])
def root():
  return {"message": "Welcome to the FreeAPI!", "version": f"v{CURRENT_API_VERSION}", "documentation": f"{CURRENT_API_PREFIX}/docs" }

@app.get("/favicon.ico", include_in_schema=False, tags=["Assets"])
def favicon_ico():
  return FileResponse(ASSETS_DIR / "favicon.png")


@app.get("/favicon.svg", include_in_schema=False, tags=["Assets"])
def favicon_svg():
  return FileResponse(ASSETS_DIR / "favicon.svg")

@app.get("/status", tags=["Status"])
def get_status():
  return {"status": "running"}

# Organization
@app.get("/github", tags=["Organization"])
def get_github():
  return {"github_repo": "https://github.com/FreePyApi/FreeApi", "github_organization": "https://github.com/FreePyApi" }

#########################
# Authentication Endpoints
#########################
@app.get("/auth/status", tags=["Auth"])
def auth_status():
  return {
    "enabled": is_oauth_enabled(),
    "provider": "github",
  }


@app.get("/auth/login", tags=["Auth"])
def auth_login(request: Request):
  return build_login_response(request)


@app.get("/auth/callback", tags=["Auth"])
def auth_callback(request: Request, code: str, state: str):
  return build_callback_response(request, code=code, state=state)


@app.post("/auth/logout", tags=["Auth"])
def auth_logout():
  return build_logout_response()


@app.get("/auth/me", tags=["Auth"])
def auth_me(request: Request):
  user = get_authenticated_user(request)
  if user is None:
    raise HTTPException(status_code=401, detail="Authentication required")
  return {"authenticated": True, "user": user}

#########################
# TEXT
#########################
from .modules import text as mtext # We give modules an M prefix

# Counting
@app.post("/text/count", tags=["Text/Counting"])
def text_count(text: str = Body(..., min_length=1, max_length=10000)):
  return mtext.count(text)

@app.post("/text/count/words", tags=["Text/Counting"])
def text_count_words(text: str = Body(..., min_length=1, max_length=10000)):
  return mtext.count_words(text)

@app.post("/text/count/characters", tags=["Text/Counting"])
def text_count_characters(text: str = Body(..., min_length=1, max_length=10000)):
  return mtext.count_characters(text)

@app.post("/text/count/sentences", tags=["Text/Counting"])
def text_count_sentences(text: str = Body(..., min_length=1, max_length=10000)):
  return mtext.count_sentences(text)

@app.post("/text/count/paragraphs", tags=["Text/Counting"])
def text_count_paragraphs(text: str = Body(..., min_length=1, max_length=10000)):
  return mtext.count_paragraphs(text)

# Password
@app.post("/text/password/strength", tags=["Text/Password"])
def text_password_strength(password: str = Body(..., embed=True, min_length=4, max_length=1024)):
  return mtext.password_strength(password)

@app.post("/text/password/generate", tags=["Text/Password"])
def text_password_generate(length: int = Query(12, ge=4, le=256), charset: Optional[str] = Query(None, max_length=500)):
  return mtext.generate_password(length=length, charset=charset)

@app.get("/text/password/disclaimer", tags=["Text/Password"])
def text_password_disclaimer():
  return mtext.password_disclaimer()

# Formatting
@app.post("/text/formatting/slugify", tags=["Text/Formatting"])
def text_format_slugify(text: str = Body(..., min_length=1, max_length=2000)):
  return mtext.slugify(text=text)

@app.post("/text/formatting/camel_case", tags=["Text/Formatting"])
def text_camel_case(text: str = Body(..., min_length=1, max_length=2000)):
  return mtext.camel_case(text=text)

@app.post("/text/formatting/pascal_case", tags=["Text/Formatting"])
def text_pascal_case(text: str = Body(..., min_length=1, max_length=2000)):
  return mtext.pascal_case(text=text)

# Other
@app.get("/text/lorem_ipsum/{length}", tags=["Text/Other"])
def text_lorem_ipsum(length: int = ParamPath(..., ge=1, le=1000)):
  return mtext.lorem_ipsum(length=length)

#########################
# DateTime
#########################
from .modules import datetime as mdatetime
from time import time

@app.get("/datetime/unix", tags=["DateTime"])
def get_unix_timestamp():
  return mdatetime.unix_timestamp()

@app.get("/datetime/format", tags=["DateTime"])
def format_time(timestamp: Optional[int] = None, format: str = Query("%Y-%m-%d %H:%M:%S", max_length=100), timezone: str = Query("UTC", max_length=50)):
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.format_time(timestamp, format, timezone)

@app.get("/datetime/timezones", tags=["DateTime"])
def get_timezones():
  return mdatetime.get_timezones()

@app.get("/datetime/convert/timezone", tags=["DateTime"])
def convert_timezone(timestamp: Optional[int] = None, from_tz: str = Query("UTC", max_length=50), to_tz: str = Query("UTC", max_length=50)):
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.convert_timezone(timestamp, from_tz, to_tz)

@app.get("/datetime/time_difference", tags=["DateTime"])
def time_difference(timestamp1: int = Query(...), timestamp2: int = Query(...)):
  return mdatetime.time_difference(timestamp1, timestamp2)

@app.get("/datetime/is_leap_year", tags=["DateTime"])
def is_leap_year(year: int = Query(..., ge=1, le=9999)):
  return mdatetime.is_leap_year(year)

@app.get("/datetime/day_of_week", tags=["DateTime"])
def day_of_week(timestamp: Optional[int] = None, timezone: str = Query("UTC", max_length=50)):
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.day_of_week(timestamp, timezone)

@app.get("/datetime/summer_time", tags=["DateTime"])
def summer_time(timestamp: Optional[int] = None, timezone: str = Query("UTC", max_length=50)):
  if timestamp is None:
    timestamp = int(time())
  return mdatetime.summer_time(timestamp, timezone)

#########################
# Geo
#########################
from .modules import geo as mgeo

@app.post("/geo/geocode", tags=["Geo"])
def geo_geocode(address: str = Body(..., min_length=1, max_length=500)):
  return mgeo.geocode(address=address)

@app.post("/geo/is_sea", tags=["Geo"])
def geo_is_sea(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)):
  return mgeo.is_sea(latitude=latitude, longitude=longitude)

@app.post("/geo/get_timezone", tags=["Geo"])
def geo_get_tz(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)):
  return mgeo.get_timezone(latitude=latitude, longitude=longitude)

@app.post("/geo/get_address", tags=["Geo"])
def geo_get_addr(latitude: float = Body(..., ge=-90, le=90), longitude: float = Body(..., ge=-180, le=180)):
  return mgeo.get_address(latitude=latitude, longitude=longitude)

#########################
# UUID and Hashing
#########################
from .modules import uuid_hashing as muuid_hashing
@app.get("/uuid/generate/{version}", tags=["UUID and Hashing"])
def uuid_generate(version: int = ParamPath(..., ge=1, le=5)):
  return muuid_hashing.generate_uuid(version=version)

@app.get("/uuid/validate", tags=["UUID and Hashing"])
def uuid_validate(uuid_string: str = Query(..., min_length=1, max_length=100)):
  return muuid_hashing.validate_uuid(uuid_string=uuid_string)

@app.get("/uuid/decode", tags=["UUID and Hashing"])
def uuid_decode(uuid_string: str = Query(..., min_length=1, max_length=200)):
  return muuid_hashing.decode_uuid(uuid_string=uuid_string)

@app.post("/hash/string", tags=["UUID and Hashing"])
def hash_string(text: str = Body(..., min_length=1, max_length=5000), algorithm: str = Body("sha256", min_length=1, max_length=50)):
  return muuid_hashing.hash_string(text=text, algorithm=algorithm)

@app.post("/hash/base64/encode", tags=["UUID and Hashing"])
def base64_encode(text: str = Body(..., min_length=1, max_length=10000)):
  return muuid_hashing.base64_encode(text=text)

@app.post("/hash/base64/decode", tags=["UUID and Hashing"])
def base64_decode(encoded_text: str = Body(..., min_length=1, max_length=10000)):
  return muuid_hashing.base64_decode(encoded_text=encoded_text)

#########################
# Math
#########################
from .modules import math as mmath

@app.post("/math/units/convert", tags=["Math", "Units"])
def convert_units(value: float = Body(...), conversion_type: str = Body(..., min_length=1, max_length=200), return_format: str = Body(..., min_length=1, max_length=50)):
  return mmath.convert_units(value=value, conversion_type=conversion_type, return_format=return_format)

@app.get("/math/units/types", tags=["Math", "Units"])
def get_conversion_types():
  return mmath.get_conversion_types()

@app.get("/math/units/names", tags=["Math", "Units"])
def get_unit_names():
  return mmath.get_unit_names()

@app.get("/math/check/prime", tags=["Math"])
def check_prime(number: int = Query(..., ge=0)):
  return mmath.check_prime(number=number)

@app.get("/math/check/odd_even", tags=["Math"])
def check_odd_even(number: int = Query(...)):
  return mmath.check_odd_even(number=number)

@app.get("/math/factorial", tags=["Math"])
def factorial(n: int = Query(..., ge=0, le=1000)):
  return mmath.factorial(n=n)

@app.get("/math/random_number", tags=["Math"])
def random_number(min: int = Query(0, ge=-2147483648), max: int = Query(100, ge=-2147483648)):
  if max < min:
    raise HTTPException(status_code=400, detail="max must be >= min")
  return mmath.random_number(min=min, max=max)

@app.get("/math/fibonacci", tags=["Math"])
def fibonacci(n: int = Query(..., ge=0, le=10000)):
  return mmath.fibonacci(n=n)

#########################
# Versioned Gateway Logic
#########################
def _load_archive_apps(archive_root: Path) -> list[tuple[str, FastAPI]]:
  loaded_apps: list[tuple[str, FastAPI]] = []
  if not archive_root.is_dir():
    return loaded_apps

  for version_dir in sorted(archive_root.iterdir()):
    if not version_dir.is_dir() or not VERSION_PATH_RE.match(f"/{version_dir.name}/"):
      continue

    version_prefix = f"/{version_dir.name}"
    if version_prefix == CURRENT_API_PREFIX:
      continue

    main_file = version_dir / "main.py"
    if not main_file.is_file():
      continue

    module_name = f"archive_{version_dir.name.replace('.', '_')}_main"
    spec = importlib.util.spec_from_file_location(module_name, main_file)
    if spec is None or spec.loader is None:
      continue

    module = importlib.util.module_from_spec(spec)
    try:
      spec.loader.exec_module(module)
    except Exception:
      continue

    archive_app = getattr(module, "app", None)
    if isinstance(archive_app, FastAPI):
      loaded_apps.append((version_prefix, archive_app))

  return loaded_apps


def _build_versioned_gateway(current_app: FastAPI) -> FastAPI:
  gateway_app = FastAPI(
    title="FreeAPI Gateway",
    description="Version gateway for FreeAPI.",
    version=CURRENT_API_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
  )

  @gateway_app.middleware("http")
  async def redirect_to_latest_version(request: Request, call_next):
    path = request.url.path
    if VERSION_PATH_RE.match(path):
      return await call_next(request)

    target_path = f"{CURRENT_API_PREFIX}{path}" if path != "/" else f"{CURRENT_API_PREFIX}/"
    query = request.url.query
    if query:
      target_path = f"{target_path}?{query}"

    return RedirectResponse(url=target_path, status_code=307)

  gateway_app.mount(CURRENT_API_PREFIX, current_app)

  archive_root = BASE_DIR.parent / "archive"
  for version_prefix, archive_app in _load_archive_apps(archive_root):
    gateway_app.mount(version_prefix, archive_app)

  return gateway_app


app = _build_versioned_gateway(app)