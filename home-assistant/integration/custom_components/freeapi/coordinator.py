from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FreeApiClient
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN


_LOGGER = logging.getLogger(__name__)


class FreeApiDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
  def __init__(self, hass: HomeAssistant, client: FreeApiClient, entry: ConfigEntry) -> None:
    self.client = client
    self.entry = entry
    poll_interval = int(entry.options.get(CONF_POLL_INTERVAL, entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)))
    super().__init__(
      hass,
      logger=_LOGGER,
      name=f"{DOMAIN}_{entry.entry_id}",
      update_interval=timedelta(seconds=max(10, poll_interval)),
    )

  async def _async_update_data(self) -> dict[str, Any]:
    try:
      return await self.client.get_status()
    except Exception as exc:
      raise UpdateFailed(str(exc)) from exc
