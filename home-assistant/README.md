# Home Assistant support for FreeAPI

This folder contains both Home Assistant deliverables:

- Integration: home-assistant/integration/custom_components/freeapi
- Addon: home-assistant/addon/freeapi

## Integration install (HACS)

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=freeapi)

1. Add this repository as a custom HACS repository.
2. Set category to Integration.
3. Install FreeAPI.
4. Restart Home Assistant.
5. Add integration from Settings -> Devices & Services.

The integration supports:

- Self-hosted mode (addon or any reachable FreeAPI host).
- Official mode with OAuth2 or API key.

## Addon install

[![Open Add-on Store](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/?repository_url=https://github.com/FreePyApi/FreeApi)

1. Add this repository as an Add-on repository in Home Assistant.
2. Install FreeAPI addon.
3. Configure options from the addon UI.
4. Start the addon.

### Addon options

- port: Internal API port used by Uvicorn.
- api_version: Sets FREEAPI_CURRENT_VERSION.
- cors_origins: Sets CORS_ORIGINS.
- rate_limit_enabled: Sets RATE_LIMIT_ENABLED.
- rate_limit_max_requests: Sets RATE_LIMIT_MAX_REQUESTS.
- rate_limit_window_seconds: Sets RATE_LIMIT_WINDOW_SECONDS.
- postgres_url: Optional POSTGRES_URL for persistent API keys.
- redis_url: Optional REDIS_URL for rate limiting backend.
- oauth_client_id: OAUTH_CLIENT_ID for OAuth login.
- oauth_client_secret: OAUTH_CLIENT_SECRET for OAuth login.
- session_secret: SESSION_SECRET for auth cookie signing.
- api_key_pepper: API_KEY_PEPPER for API key hashing hardening.
- env_file: Additional KEY=VALUE lines loaded at startup.

## Official mode OAuth2 notes

Choose Official mode, then OAuth2 mode.
The integration opens the official FreeAPI GitHub login bridge at `/auth/login/ha`, which uses the stable official callback `/auth/callback/ha`.
After GitHub returns to the official API, FreeAPI creates a Home Assistant API key and posts it back to Home Assistant automatically.

Requirements:

- The official API must have OAuth enabled.
- Home Assistant must have an external URL configured so the browser can return to the integration callback.

## Troubleshooting

- Cannot connect: verify base URL, version, and network reachability.
- OAuth exchange failed: verify the official API has GitHub OAuth configured and Home Assistant has an external URL.
- Unauthorized: verify API key format and token validity.
- Wrong endpoint path: integration calls versioned routes under /v{api_version}/.
