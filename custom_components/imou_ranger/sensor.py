"""Sensor thông tin thiết bị (info): model, firmware, serial."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import ImouBaseEntity
from .hub import ImouOnvifHub

_SENSORS = [
    ("model", "Model", "mdi:cctv"),
    ("firmware", "Firmware", "mdi:chip"),
    ("serial", "Serial", "mdi:identifier"),
    ("manufacturer", "Manufacturer", "mdi:factory"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ImouInfoSensor(hub, entry.entry_id, key, name, icon)
        for key, name, icon in _SENSORS
    )


class ImouInfoSensor(ImouBaseEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, hub, entry_id, key, name, icon):
        super().__init__(hub, entry_id)
        self._key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry_id}_{key}"

    @property
    def native_value(self):
        return (self._hub.info or {}).get(self._key)
