from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import (
  AUTH_MODE_API_KEY,
  AUTH_MODE_OAUTH2,
  CONF_API_KEY,
  CONF_API_VERSION,
  CONF_AUTH_MODE,
  CONF_BASE_URL,
  CONF_MODE,
  CONF_POLL_INTERVAL,
  CONF_USE_HTTPS,
  CONF_VERIFY_SSL,
  DEFAULT_API_VERSION,
  DEFAULT_OFFICIAL_BASE_URL,
  DEFAULT_POLL_INTERVAL,
  DOMAIN,
  HA_OAUTH_CALLBACK_PATH,
  MODE_OFFICIAL,
  MODE_SELF_HOSTED,
)


def _compose_base_url(host: str, port: int, use_https: bool) -> str:
  scheme = "https" if use_https else "http"
  return f"{scheme}://{host}:{port}"


async def _validate_status(base_url: str, verify_ssl: bool, authorization: str | None = None) -> bool:
  headers = {"Accept": "application/json"}
  if authorization:
    headers["Authorization"] = authorization

  async with aiohttp.ClientSession() as session:
    async with session.get(
      f"{base_url.rstrip('/')}/status",
      headers=headers,
      ssl=verify_ssl,
      timeout=aiohttp.ClientTimeout(total=10),
      allow_redirects=True,
    ) as response:
      return response.status < 400


def _build_home_assistant_callback_url(flow: config_entries.ConfigFlow) -> str:
  base_url = get_url(flow.hass, prefer_external=True)
  return f"{base_url.rstrip('/')}{HA_OAUTH_CALLBACK_PATH}?flow_id={flow.flow_id}"


class FreeApiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  VERSION = 1

  def __init__(self) -> None:
    self._data: dict[str, Any] = {}

  async def async_step_user(self, user_input: dict[str, Any] | None = None):
    if user_input is not None:
      self._data.update(user_input)
      mode = user_input[CONF_MODE]
      if mode == MODE_SELF_HOSTED:
        return await self.async_step_self_hosted()
      return await self.async_step_official()

    schema = vol.Schema(
      {
        vol.Required(CONF_MODE, default=MODE_SELF_HOSTED): vol.In([MODE_SELF_HOSTED, MODE_OFFICIAL]),
      }
    )
    return self.async_show_form(step_id="user", data_schema=schema)

  async def async_step_self_hosted(self, user_input: dict[str, Any] | None = None):
    errors: dict[str, str] = {}
    if user_input is not None:
      host = user_input[CONF_HOST].strip()
      port = int(user_input[CONF_PORT])
      use_https = bool(user_input[CONF_USE_HTTPS])
      verify_ssl = bool(user_input[CONF_VERIFY_SSL])
      api_key = (user_input.get(CONF_API_KEY) or "").strip()
      base_url = _compose_base_url(host, port, use_https)
      authorization = f"Bearer {api_key}" if api_key else None
      try:
        ok = await _validate_status(base_url, verify_ssl=verify_ssl, authorization=authorization)
      except Exception:
        ok = False
      if not ok:
        errors["base"] = "cannot_connect"
      else:
        self._data.update(
          {
            CONF_BASE_URL: base_url,
            CONF_API_KEY: api_key,
            CONF_API_VERSION: user_input.get(CONF_API_VERSION, DEFAULT_API_VERSION),
            CONF_VERIFY_SSL: verify_ssl,
            CONF_POLL_INTERVAL: int(user_input.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)),
            CONF_AUTH_MODE: AUTH_MODE_API_KEY if api_key else AUTH_MODE_API_KEY,
          }
        )
        title = f"FreeAPI ({host}:{port})"
        return self.async_create_entry(title=title, data=self._data)

    schema = vol.Schema(
      {
        vol.Required(CONF_HOST, default="freeapi"): str,
        vol.Required(CONF_PORT, default=8000): int,
        vol.Required(CONF_USE_HTTPS, default=False): bool,
        vol.Required(CONF_VERIFY_SSL, default=True): bool,
        vol.Optional(CONF_API_KEY, default=""): str,
        vol.Required(CONF_API_VERSION, default=DEFAULT_API_VERSION): str,
        vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(int, vol.Range(min=10, max=3600)),
      }
    )
    return self.async_show_form(step_id="self_hosted", data_schema=schema, errors=errors)

  async def async_step_official(self, user_input: dict[str, Any] | None = None):
    if user_input is not None:
      self._data.update(user_input)
      if user_input[CONF_AUTH_MODE] == AUTH_MODE_API_KEY:
        return await self.async_step_official_api_key()
      return await self.async_step_official_oauth_app()

    schema = vol.Schema(
      {
        vol.Required(CONF_BASE_URL, default=DEFAULT_OFFICIAL_BASE_URL): str,
        vol.Required(CONF_VERIFY_SSL, default=True): bool,
        vol.Required(CONF_AUTH_MODE, default=AUTH_MODE_OAUTH2): vol.In([AUTH_MODE_OAUTH2, AUTH_MODE_API_KEY]),
        vol.Required(CONF_API_VERSION, default=DEFAULT_API_VERSION): str,
        vol.Required(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(int, vol.Range(min=10, max=3600)),
      }
    )
    return self.async_show_form(step_id="official", data_schema=schema)

  async def async_step_official_api_key(self, user_input: dict[str, Any] | None = None):
    errors: dict[str, str] = {}
    if user_input is not None:
      api_key = (user_input.get(CONF_API_KEY) or "").strip()
      base_url = (self._data.get(CONF_BASE_URL) or DEFAULT_OFFICIAL_BASE_URL).strip()
      verify_ssl = bool(self._data.get(CONF_VERIFY_SSL, True))
      try:
        ok = await _validate_status(base_url, verify_ssl=verify_ssl, authorization=f"Bearer {api_key}")
      except Exception:
        ok = False
      if not ok:
        errors["base"] = "cannot_connect"
      else:
        self._data[CONF_API_KEY] = api_key
        title = "FreeAPI (Official)"
        return self.async_create_entry(title=title, data=self._data)

    schema = vol.Schema({vol.Required(CONF_API_KEY): str})
    return self.async_show_form(step_id="official_api_key", data_schema=schema, errors=errors)

  async def async_step_official_oauth_app(self, user_input: dict[str, Any] | None = None):
    if user_input is not None:
      api_key = (user_input.get(CONF_API_KEY) or "").strip()
      if api_key:
        self._data[CONF_API_KEY] = api_key
        self._data[CONF_AUTH_MODE] = AUTH_MODE_API_KEY
        return self.async_external_step_done(next_step_id="official_oauth_finish")

    try:
      ha_callback = _build_home_assistant_callback_url(self)
    except NoURLAvailableError:
      return self.async_show_form(
        step_id="official_oauth_app",
        data_schema=vol.Schema({}),
        errors={"base": "missing_home_assistant_url"},
      )

    base_url = (self._data.get(CONF_BASE_URL) or DEFAULT_OFFICIAL_BASE_URL).rstrip("/")
    query = urlencode({"ha_callback": ha_callback})
    authorize_url = f"{base_url}/auth/login/ha?{query}"
    return self.async_external_step(step_id="official_oauth_app", url=authorize_url)

  async def async_step_official_oauth_finish(self, user_input: dict[str, Any] | None = None):
    base_url = (self._data.get(CONF_BASE_URL) or DEFAULT_OFFICIAL_BASE_URL).strip()
    verify_ssl = bool(self._data.get(CONF_VERIFY_SSL, True))
    api_key = (self._data.get(CONF_API_KEY) or "").strip()
    try:
      ok = await _validate_status(base_url, verify_ssl=verify_ssl, authorization=f"Bearer {api_key}")
    except Exception:
      ok = False

    if not ok:
      return self.async_abort(reason="oauth_exchange_failed")

    title = "FreeAPI (Official OAuth2)"
    return self.async_create_entry(title=title, data=self._data)

  @staticmethod
  def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return FreeApiOptionsFlow(config_entry)


class FreeApiOptionsFlow(config_entries.OptionsFlow):
  def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
    self._config_entry = config_entry

  async def async_step_init(self, user_input: dict[str, Any] | None = None):
    if user_input is not None:
      return self.async_create_entry(title="", data=user_input)

    schema = vol.Schema(
      {
        vol.Required(
          CONF_POLL_INTERVAL,
          default=self._config_entry.options.get(
            CONF_POLL_INTERVAL,
            self._config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
          ),
        ): vol.All(int, vol.Range(min=10, max=3600)),
        vol.Required(
          CONF_API_VERSION,
          default=self._config_entry.options.get(
            CONF_API_VERSION,
            self._config_entry.data.get(CONF_API_VERSION, DEFAULT_API_VERSION),
          ),
        ): str,
      }
    )
    return self.async_show_form(step_id="init", data_schema=schema)
