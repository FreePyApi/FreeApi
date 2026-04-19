import os
from dataclasses import dataclass, field
from typing import Optional


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
  value = os.getenv(name)
  if value is None or value == "":
    return default
  return value


def _as_bool(value: Optional[str], default: bool = False) -> bool:
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on", "prod", "production"}


@dataclass(frozen=True)
class Settings:
  env: str = field(default_factory=lambda: _get_env("ENV", "development") or "development")
  freeapi_current_version: str = field(default_factory=lambda: _get_env("FREEAPI_CURRENT_VERSION", "1.0.0") or "1.0.0")
  log_level: str = field(default_factory=lambda: _get_env("LOG_LEVEL", "INFO") or "INFO")
  cors_origins: list[str] = field(default_factory=lambda: [origin.strip() for origin in (_get_env("CORS_ORIGINS", "") or "").split(",") if origin.strip()])
  rate_limit_enabled: bool = field(default_factory=lambda: _as_bool(_get_env("RATE_LIMIT_ENABLED"), default=_get_env("ENV", "development") in {"prod", "production"}))
  rate_limit_max_requests: int = field(default_factory=lambda: int(_get_env("RATE_LIMIT_MAX_REQUESTS", "120") or 120))
  rate_limit_window_seconds: int = field(default_factory=lambda: int(_get_env("RATE_LIMIT_WINDOW_SECONDS", "60") or 60))
  docs_rate_limit_enabled: bool = field(default_factory=lambda: True)
  docs_rate_limit_max_requests: int = field(default_factory=lambda: int(_get_env("DOCS_RATE_LIMIT_MAX_REQUESTS", "60") or 60))
  docs_rate_limit_window_seconds: int = field(default_factory=lambda: int(_get_env("DOCS_RATE_LIMIT_WINDOW_SECONDS", "10") or 10))
  oauth_client_id: str = field(default_factory=lambda: _get_env("OAUTH_CLIENT_ID", "") or "")
  oauth_client_secret: str = field(default_factory=lambda: _get_env("OAUTH_CLIENT_SECRET", "") or "")
  session_secret: str = field(default_factory=lambda: _get_env("SESSION_SECRET", "") or "")
  preferred_time_server: str = field(default_factory=lambda: _get_env("PREFERED_TIME_SERVER", "pool.ntp.org") or "pool.ntp.org")
  redis_url: str = field(default_factory=lambda: _get_env("REDIS_URL", "") or "")
  metrics_enabled: bool = field(default_factory=lambda: _as_bool(_get_env("METRICS_ENABLED"), default=True))

  @property
  def production(self) -> bool:
    return self.env.strip().lower() in {"prod", "production"}

  @property
  def oauth_enabled(self) -> bool:
    return bool(self.oauth_client_id and self.oauth_client_secret)


settings = Settings()