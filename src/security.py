import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import settings

PRODUCTION_ENVS = {"prod", "production"}
PUBLIC_PATH_PREFIXES = (
  "/docs",
  "/redoc",
  "/openapi.json",
  "/status",
  "/github",
  "/favicon.ico",
  "/favicon.svg",
  "/assets",
  "/auth",
)

AUTH_COOKIE_NAME = "freeapi_auth"
AUTH_STATE_COOKIE_NAME = "freeapi_auth_state"
AUTH_STATE_TTL_SECONDS = 10 * 60

def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
  value = os.getenv(name)
  if value is None or value == "":
    return default
  return value

def get_env_flag(name: str, default: str = "development") -> str:
  return (get_env(name, default) or default).strip().lower()

def is_rate_limit_enabled() -> bool:
  return settings.rate_limit_enabled

def is_oauth_enabled() -> bool:
  return settings.oauth_enabled

def cookie_secure() -> bool:
  return settings.production

def get_serializer() -> URLSafeTimedSerializer:
  secret = get_env("SESSION_SECRET") or get_env("AUTH_COOKIE_SECRET") or get_env("OAUTH_CLIENT_SECRET") or "freeapi-session-secret"
  return URLSafeTimedSerializer(secret_key=secret, salt="freeapi-auth-cookie")

def get_oauth_client_id() -> str:
  return get_env("OAUTH_CLIENT_ID") or ""

def get_oauth_client_secret() -> str:
  return get_env("OAUTH_CLIENT_SECRET") or ""

def get_oauth_authorize_url() -> str:
  return get_env("OAUTH_AUTHORIZE_URL", "https://github.com/login/oauth/authorize") or "https://github.com/login/oauth/authorize"

def get_oauth_token_url() -> str:
  return get_env("OAUTH_TOKEN_URL", "https://github.com/login/oauth/access_token") or "https://github.com/login/oauth/access_token"

def get_oauth_userinfo_url() -> str:
  return get_env("OAUTH_USERINFO_URL", "https://api.github.com/user") or "https://api.github.com/user"

def get_oauth_redirect_uri(request: Request) -> str:
  configured = get_env("OAUTH_REDIRECT_URI")
  if configured:
    return configured
  return str(request.url_for("auth_callback"))

def get_oauth_scopes() -> str:
  return get_env("OAUTH_SCOPES", "read:user user:email") or "read:user user:email"

def is_public_path(path: str) -> bool:
  return any(path == prefix or path.startswith(prefix + "/") for prefix in PUBLIC_PATH_PREFIXES)

def serialize_auth_payload(payload: dict[str, Any]) -> str:
  return get_serializer().dumps(payload)

def deserialize_auth_payload(raw_value: str) -> dict[str, Any]:
  data = get_serializer().loads(raw_value, max_age=None)
  if not isinstance(data, dict):
    raise BadSignature("invalid auth cookie payload")
  return data

def get_authenticated_user(request: Request) -> Optional[dict[str, Any]]:
  raw_cookie = request.cookies.get(AUTH_COOKIE_NAME)
  if not raw_cookie:
    return None

  try:
    payload = deserialize_auth_payload(raw_cookie)
  except (BadSignature, SignatureExpired, ValueError, TypeError):
    return None

  current_timestamp = getattr(request.state, "timestamp", int(time.time()))
  if payload.get("expires_at") and int(payload["expires_at"]) < int(current_timestamp):
    return None

  user = payload.get("user")
  return user if isinstance(user, dict) else None

def build_authorize_url(request: Request, state: str) -> str:
  query = urllib.parse.urlencode({
    "client_id": get_oauth_client_id(),
    "redirect_uri": get_oauth_redirect_uri(request),
    "response_type": "code",
    "scope": get_oauth_scopes(),
    "state": state,
  })
  return f"{get_oauth_authorize_url()}?{query}"

def exchange_code_for_token(request: Request, code: str) -> dict[str, Any]:
  payload = urllib.parse.urlencode({
    "client_id": get_oauth_client_id(),
    "client_secret": get_oauth_client_secret(),
    "code": code,
    "redirect_uri": get_oauth_redirect_uri(request),
  }).encode("utf-8")

  token_request = urllib.request.Request(
    get_oauth_token_url(),
    data=payload,
    headers={
      "Accept": "application/json",
      "Content-Type": "application/x-www-form-urlencoded",
      "User-Agent": "FreeAPI",
    },
    method="POST",
  )

  try:
    with urllib.request.urlopen(token_request, timeout=15) as response:
      response_body = response.read().decode("utf-8")
  except urllib.error.HTTPError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth token exchange failed") from exc
  except urllib.error.URLError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth provider unavailable") from exc

  try:
    token_data = json.loads(response_body)
  except json.JSONDecodeError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth token response was invalid") from exc

  if not isinstance(token_data, dict) or not token_data.get("access_token"):
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth token response did not include an access token")

  return token_data

def fetch_user_profile(access_token: str) -> dict[str, Any]:
  user_request = urllib.request.Request(
    get_oauth_userinfo_url(),
    headers={
      "Authorization": f"Bearer {access_token}",
      "Accept": "application/json",
      "User-Agent": "FreeAPI",
    },
    method="GET",
  )

  try:
    with urllib.request.urlopen(user_request, timeout=15) as response:
      response_body = response.read().decode("utf-8")
  except urllib.error.HTTPError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth user lookup failed") from exc
  except urllib.error.URLError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth provider unavailable") from exc

  try:
    user_data = json.loads(response_body)
  except json.JSONDecodeError as exc:
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth user response was invalid") from exc

  if not isinstance(user_data, dict):
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth user response was invalid")

  return user_data

def create_auth_cookie_value(access_token: str, user: dict[str, Any], expires_in: Optional[int]) -> str:
  expires_at = None
  if expires_in:
    expires_at = int(time.time()) + int(expires_in)
  payload = {
    "access_token": access_token,
    "user": user,
    "expires_at": expires_at,
  }
  return serialize_auth_payload(payload)

def build_login_response(request: Request) -> RedirectResponse:
  if not is_oauth_enabled():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth is not configured")

  state = secrets.token_urlsafe(32)
  response = RedirectResponse(build_authorize_url(request, state), status_code=status.HTTP_302_FOUND)
  response.set_cookie(
    key=AUTH_STATE_COOKIE_NAME,
    value=state,
    httponly=True,
    secure=cookie_secure(),
    samesite="lax",
    max_age=AUTH_STATE_TTL_SECONDS,
    path="/",
  )
  return response

def build_callback_response(request: Request, code: str, state: str) -> RedirectResponse:
  if not is_oauth_enabled():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth is not configured")

  expected_state = request.cookies.get(AUTH_STATE_COOKIE_NAME)
  if not expected_state or expected_state != state:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

  token_data = exchange_code_for_token(request, code)
  access_token = token_data.get("access_token")
  expires_in = token_data.get("expires_in")
  user = fetch_user_profile(access_token)
  auth_cookie_value = create_auth_cookie_value(access_token, user, expires_in)

  response = RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)
  cookie_kwargs = {
    "key": AUTH_COOKIE_NAME,
    "value": auth_cookie_value,
    "httponly": True,
    "secure": cookie_secure(),
    "samesite": "lax",
    "path": "/",
  }
  if expires_in:
    cookie_kwargs["max_age"] = int(expires_in)
  response.set_cookie(**cookie_kwargs)
  response.delete_cookie(AUTH_STATE_COOKIE_NAME, path="/")
  return response

def build_logout_response() -> RedirectResponse:
  response = RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)
  response.delete_cookie(AUTH_COOKIE_NAME, path="/")
  response.delete_cookie(AUTH_STATE_COOKIE_NAME, path="/")
  return response

def auth_guard(request: Request) -> Optional[JSONResponse]:
  if not is_oauth_enabled() or is_public_path(request.url.path):
    return None

  user = get_authenticated_user(request)
  if user is None:
    return JSONResponse({"detail": "Authentication required"}, status_code=status.HTTP_401_UNAUTHORIZED)

  request.state.user = user
  return None
