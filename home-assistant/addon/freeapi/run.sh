#!/bin/sh
set -eu

OPTIONS_FILE="/data/options.json"
ENV_FILE="/tmp/freeapi.env"

if [ -f "$OPTIONS_FILE" ]; then
  python - "$OPTIONS_FILE" "$ENV_FILE" <<'PY'
import json
import pathlib
import shlex
import sys

options_path = pathlib.Path(sys.argv[1])
env_path = pathlib.Path(sys.argv[2])

options = {}
if options_path.exists():
    with options_path.open("r", encoding="utf-8") as f:
        options = json.load(f)

pairs = {
    "ENV": "production",
    "FREEAPI_CURRENT_VERSION": str(options.get("api_version", "1.0.1")),
    "CORS_ORIGINS": str(options.get("cors_origins", "")),
    "RATE_LIMIT_ENABLED": str(options.get("rate_limit_enabled", True)).lower(),
    "RATE_LIMIT_MAX_REQUESTS": str(options.get("rate_limit_max_requests", 120)),
    "RATE_LIMIT_WINDOW_SECONDS": str(options.get("rate_limit_window_seconds", 60)),
    "POSTGRES_URL": str(options.get("postgres_url", "")),
    "REDIS_URL": str(options.get("redis_url", "")),
    "OAUTH_CLIENT_ID": str(options.get("oauth_client_id", "")),
    "OAUTH_CLIENT_SECRET": str(options.get("oauth_client_secret", "")),
    "SESSION_SECRET": str(options.get("session_secret", "")),
    "API_KEY_PEPPER": str(options.get("api_key_pepper", "")),
}

env_file_text = options.get("env_file") or ""
for line in str(env_file_text).splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    key = key.strip()
    if key:
        pairs[key] = value.strip()

with env_path.open("w", encoding="utf-8") as f:
    for key, value in pairs.items():
        f.write(f"{key}={shlex.quote(value)}\n")
PY

  # shellcheck source=/dev/null
  . "$ENV_FILE"
fi

PORT="8000"
if [ -f "$OPTIONS_FILE" ]; then
  PORT="$(python - "$OPTIONS_FILE" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = json.load(f)
print(int(data.get("port", 8000)))
PY
)"
fi

exec uvicorn src.main:app --host 0.0.0.0 --port "$PORT"
