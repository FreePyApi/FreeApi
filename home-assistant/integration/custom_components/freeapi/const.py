DOMAIN = "freeapi"

CONF_MODE = "mode"
MODE_SELF_HOSTED = "self_hosted"
MODE_OFFICIAL = "official"

CONF_BASE_URL = "base_url"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USE_HTTPS = "use_https"
CONF_API_VERSION = "api_version"

CONF_AUTH_MODE = "auth_mode"
AUTH_MODE_API_KEY = "api_key"
AUTH_MODE_OAUTH2 = "oauth2"

CONF_API_KEY = "api_key"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_AUTHORIZE_URL = "authorize_url"
CONF_TOKEN_URL = "token_url"
CONF_SCOPES = "scopes"
CONF_REDIRECT_URI = "redirect_uri"

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_TYPE = "token_type"

CONF_VERIFY_SSL = "verify_ssl"
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_OFFICIAL_BASE_URL = "https://freeapi.szabee.me"
DEFAULT_API_VERSION = "1.0.1"
DEFAULT_POLL_INTERVAL = 60
DEFAULT_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
DEFAULT_TOKEN_URL = "https://github.com/login/oauth/access_token"
DEFAULT_SCOPES = "read:user user:email"

PLATFORMS = ["sensor"]

SERVICE_CALL_ENDPOINT = "call_endpoint"
HA_OAUTH_CALLBACK_PATH = "/api/freeapi/oauth/callback"
