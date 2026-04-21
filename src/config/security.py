import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from html import escape
from typing import Any, Optional
import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import settings
from .api_keys import authenticate_bearer_token, create_api_key

logger = logging.getLogger(__name__)

PRODUCTION_ENVS = {"prod", "production"}
PUBLIC_PATH_PREFIXES = (
  "/",
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
AUTH_HA_STATE_COOKIE_NAME = "freeapi_auth_ha_state"
AUTH_STATE_TTL_SECONDS = 10 * 60 # 10 minutes

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
  # Always use a stable redirect path so the callback doesn't change per-version.
  # Use the request base URL (scheme + host) and append the fixed path.
  base = str(request.base_url).rstrip('/')
  return f"{base}/auth/callback"


def get_oauth_ha_redirect_uri(request: Request) -> str:
  base = str(request.base_url).rstrip('/')
  return f"{base}/auth/callback/ha"

def get_oauth_scopes() -> str:
  return get_env("OAUTH_SCOPES", "read:user user:email") or "read:user user:email"

def is_public_path(path: str) -> bool:
  return any(path == prefix or path.startswith(prefix + "/") for prefix in PUBLIC_PATH_PREFIXES)

def _extract_unversioned_path(path: str) -> str:
  """Extract path without version prefix. E.g., /v1.0.0/docs -> /docs"""
  match = re.match(r'^/v\d+\.\d+\.\d+(/.*)?$', path)
  if match:
    return match.group(1) or '/'
  return path

def _is_unversioned_public_path(path: str) -> bool:
  """Check if path (including versioned paths) is public."""
  # Direct check for public paths
  if is_public_path(path):
    return True
  # Check unversioned path
  unversioned = _extract_unversioned_path(path)
  return is_public_path(unversioned)

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
    bearer_token = _get_bearer_token(request)
    if bearer_token is None:
      return None
    user = authenticate_bearer_token(bearer_token)
    if user is not None:
      request.state.auth_method = "bearer"
      return user
    request.state.bearer_auth_failed = True
    return None

  try:
    payload = deserialize_auth_payload(raw_cookie)
  except (BadSignature, SignatureExpired, ValueError, TypeError):
    bearer_token = _get_bearer_token(request)
    if bearer_token is None:
      return None
    user = authenticate_bearer_token(bearer_token)
    if user is not None:
      request.state.auth_method = "bearer"
      return user
    request.state.bearer_auth_failed = True
    return None

  current_timestamp = getattr(request.state, "timestamp", int(time.time()))
  if payload.get("expires_at") and int(payload["expires_at"]) < int(current_timestamp):
    return None

  user = payload.get("user")
  if isinstance(user, dict):
    request.state.auth_method = "cookie"
    return user

  bearer_token = _get_bearer_token(request)
  if bearer_token is None:
    return None
  user = authenticate_bearer_token(bearer_token)
  if user is not None:
    request.state.auth_method = "bearer"
    return user
  request.state.bearer_auth_failed = True
  return None

def build_authorize_url(request: Request, state: str, redirect_uri: str | None = None) -> str:
  query = urllib.parse.urlencode({
    "client_id": get_oauth_client_id(),
    "redirect_uri": redirect_uri or get_oauth_redirect_uri(request),
    "response_type": "code",
    "scope": get_oauth_scopes(),
    "state": state,
  })
  return f"{get_oauth_authorize_url()}?{query}"

def exchange_code_for_token(request: Request, code: str, redirect_uri: str | None = None) -> dict[str, Any]:
  payload = urllib.parse.urlencode({
    "client_id": get_oauth_client_id(),
    "client_secret": get_oauth_client_secret(),
    "code": code,
    "redirect_uri": redirect_uri or get_oauth_redirect_uri(request),
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
    logger.debug("OAuth token exchange returned non-json response: %s", response_body)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth token response was invalid") from exc

  if not isinstance(token_data, dict) or not token_data.get("access_token"):
    logger.debug("OAuth token response missing access_token: %s", response_body)
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


def _validate_ha_callback_url(url: str) -> str:
  parsed = urllib.parse.urlparse(url)
  if parsed.scheme not in {"http", "https"} or not parsed.netloc:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Home Assistant callback URL")
  return url


def _serialize_ha_state(ha_callback: str) -> str:
  payload = {
    "nonce": secrets.token_urlsafe(32),
    "ha_callback": _validate_ha_callback_url(ha_callback),
  }
  return get_serializer().dumps(payload)


def _deserialize_ha_state(raw_value: str) -> dict[str, Any]:
  data = get_serializer().loads(raw_value, max_age=AUTH_STATE_TTL_SECONDS)
  if not isinstance(data, dict):
    raise BadSignature("invalid Home Assistant auth state payload")
  callback = data.get("ha_callback")
  if not isinstance(callback, str):
    raise BadSignature("missing Home Assistant callback URL")
  data["ha_callback"] = _validate_ha_callback_url(callback)
  return data


def build_ha_login_response(request: Request, ha_callback: str) -> RedirectResponse:
  if not is_oauth_enabled():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth is not configured")

  state = _serialize_ha_state(ha_callback)
  authorize_url = build_authorize_url(request, state, redirect_uri=get_oauth_ha_redirect_uri(request))
  response = RedirectResponse(authorize_url, status_code=status.HTTP_302_FOUND)
  response.set_cookie(
    key=AUTH_HA_STATE_COOKIE_NAME,
    value=state,
    httponly=True,
    secure=cookie_secure(),
    samesite="lax",
    max_age=AUTH_STATE_TTL_SECONDS,
    path="/",
  )
  return response


def build_ha_callback_response(request: Request, code: str, state: str) -> HTMLResponse:
  if not is_oauth_enabled():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth is not configured")

  expected_state = request.cookies.get(AUTH_HA_STATE_COOKIE_NAME)
  if not expected_state or not secrets.compare_digest(expected_state, state):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

  state_payload = _deserialize_ha_state(state)
  token_data = exchange_code_for_token(request, code, redirect_uri=get_oauth_ha_redirect_uri(request))
  access_token = token_data.get("access_token")
  user = fetch_user_profile(access_token)
  api_key_data = create_api_key(user=user, description="Home Assistant integration", expires_at=None)
  ha_callback = state_payload["ha_callback"]
  api_key = api_key_data["api_key"]

  html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>FreeAPI Home Assistant Login</title>
  </head>
  <body>
    <form id="freeapi-ha-bridge" method="post" action="{escape(ha_callback, quote=True)}">
      <input type="hidden" name="api_key" value="{escape(api_key, quote=True)}">
    </form>
    <p>Completing sign-in with Home Assistant...</p>
    <script>document.getElementById("freeapi-ha-bridge").submit();</script>
  </body>
</html>"""
  response = HTMLResponse(content=html, status_code=status.HTTP_200_OK)
  response.delete_cookie(AUTH_HA_STATE_COOKIE_NAME, path="/")
  return response

def build_logout_response() -> RedirectResponse:
  response = RedirectResponse(url="/docs", status_code=status.HTTP_302_FOUND)
  response.delete_cookie(AUTH_COOKIE_NAME, path="/")
  response.delete_cookie(AUTH_STATE_COOKIE_NAME, path="/")
  return response

def auth_guard(request: Request) -> Optional[RedirectResponse]:
  if not is_oauth_enabled():
    return None
  
  path = request.url.path
  
  # Allow all public paths including docs, openapi.json (both versioned and unversioned)
  if _is_unversioned_public_path(path):
    return None

  user = get_authenticated_user(request)
  if user is None:
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

  request.state.user = user
  return None


def _get_bearer_token(request: Request) -> Optional[str]:
  authorization = request.headers.get("authorization") or request.headers.get("Authorization")
  if not authorization:
    return None

  scheme, _, token = authorization.partition(" ")
  if scheme.lower() != "bearer" or not token.strip():
    return None

  return token.strip()
