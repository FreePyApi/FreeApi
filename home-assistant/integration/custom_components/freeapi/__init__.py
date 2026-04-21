from __future__ import annotations

from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FreeApiClient
from .const import DOMAIN, HA_OAUTH_CALLBACK_PATH, PLATFORMS, SERVICE_CALL_ENDPOINT
from .coordinator import FreeApiDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
  hass.data.setdefault(DOMAIN, {})
  hass.http.register_view(FreeApiOAuthCallbackView())
  return True


class FreeApiOAuthCallbackView(HomeAssistantView):
  url = HA_OAUTH_CALLBACK_PATH
  name = "api:freeapi:oauth_callback"
  requires_auth = False

  async def post(self, request: web.Request) -> web.StreamResponse:
    hass: HomeAssistant = request.app["hass"]
    data = await request.post()
    flow_id = str(data.get("flow_id") or request.query.get("flow_id") or "").strip()
    api_key = str(data.get("api_key") or "").strip()

    if not flow_id or not api_key:
      raise web.HTTPBadRequest(text="Missing OAuth callback payload")

    result = await hass.config_entries.flow.async_configure(
      flow_id,
      {"api_key": api_key},
    )
    if result.get("type") == "external_step_done":
      await hass.config_entries.flow.async_configure(flow_id, None)

    raise web.HTTPFound("/config/integrations/dashboard")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  session = async_get_clientsession(hass)
  client = FreeApiClient(session, dict(entry.data))
  coordinator = FreeApiDataUpdateCoordinator(hass, client, entry)
  await coordinator.async_config_entry_first_refresh()

  hass.data[DOMAIN][entry.entry_id] = {
    "client": client,
    "coordinator": coordinator,
    "entry": entry,
  }

  if not hass.services.has_service(DOMAIN, SERVICE_CALL_ENDPOINT):
    async def _handle_call_endpoint(call: ServiceCall) -> None:
      entry_id = call.data.get("entry_id")
      endpoint = call.data.get("endpoint")
      method = call.data.get("method", "GET")
      params = call.data.get("params")
      payload = call.data.get("payload")

      if not endpoint:
        raise HomeAssistantError("Missing endpoint")

      if entry_id:
        data = hass.data[DOMAIN].get(entry_id)
      else:
        data = next(iter(hass.data[DOMAIN].values()), None)

      if data is None:
        raise HomeAssistantError("No FreeAPI config entry available")

      await data["client"].call_endpoint(endpoint, method=method, params=params, payload=payload)

    hass.services.async_register(DOMAIN, SERVICE_CALL_ENDPOINT, _handle_call_endpoint)

  await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
  return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
  if unload_ok:
    hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_CALL_ENDPOINT):
      hass.services.async_remove(DOMAIN, SERVICE_CALL_ENDPOINT)
  return unload_ok
