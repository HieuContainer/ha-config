"""Text entity — nhập tên rồi lưu vị trí PTZ hiện tại thành preset."""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_PRESETS_UPDATED
from .entity import ImouBaseEntity
from .hub import ImouOnvifHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ImouSavePresetText(hub, entry.entry_id)])


class ImouSavePresetText(ImouBaseEntity, TextEntity):
    """Nhập tên (Enter) → lưu vị trí hiện tại thành preset cùng tên."""

    _attr_name = "Lưu vị trí đặt tên"
    _attr_icon = "mdi:content-save-plus"
    _attr_native_max = 32
    _attr_native_min = 0
    _attr_mode = "text"

    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id)
        self._attr_unique_id = f"{entry_id}_save_preset_named"
        self._attr_native_value = ""

    async def async_set_value(self, value: str) -> None:
        name = (value or "").strip()
        if not name:
            self._attr_native_value = ""
            self.async_write_ha_state()
            return
        await self.hass.async_add_executor_job(
            lambda: self._hub.set_preset(name=name)
        )
        self._attr_native_value = name
        self.async_write_ha_state()
        async_dispatcher_send(self.hass, SIGNAL_PRESETS_UPDATED)
