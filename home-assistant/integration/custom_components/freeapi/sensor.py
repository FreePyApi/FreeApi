from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FreeApiDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
  coordinator: FreeApiDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
  async_add_entities([FreeApiStatusSensor(coordinator, entry)])


class FreeApiStatusSensor(CoordinatorEntity[FreeApiDataUpdateCoordinator], SensorEntity):
  _attr_has_entity_name = True

  def __init__(self, coordinator: FreeApiDataUpdateCoordinator, entry: ConfigEntry) -> None:
    super().__init__(coordinator)
    self._attr_unique_id = f"{entry.entry_id}_status"
    self._attr_name = "Status"

  @property
  def native_value(self) -> str:
    status = (self.coordinator.data or {}).get("status")
    return str(status or "unknown")

  @property
  def extra_state_attributes(self) -> dict[str, str]:
    data = self.coordinator.data or {}
    attrs: dict[str, str] = {}
    for key in ("version", "oauth_enabled", "rate_limit_enabled"):
      if key in data:
        attrs[key] = str(data.get(key))
    return attrs
