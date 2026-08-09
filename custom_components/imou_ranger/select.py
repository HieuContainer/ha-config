"""Select entities — đi tới vị trí và xóa vị trí (preset)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_PRESETS_UPDATED
from .entity import ImouBaseEntity
from .hub import ImouOnvifHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ImouGotoPresetSelect(hub, entry.entry_id),
        ImouRemovePresetSelect(hub, entry.entry_id),
    ])


class _ImouPresetSelectBase(ImouBaseEntity, SelectEntity):
    """Base: nạp danh sách preset, tự làm mới khi có tín hiệu thay đổi."""

    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id)
        self._presets = []
        self._current = None

    def _token_by_name(self, name):
        for p in self._presets:
            if p["name"] == name:
                return p["token"]
        return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PRESETS_UPDATED, self._handle_update
            )
        )
        # Nạp danh sách ngay khi khởi động, không chờ chu kỳ polling.
        try:
            await self.async_update()
            self.async_write_ha_state()
        except Exception:  # noqa: BLE001
            pass

    @callback
    def _handle_update(self) -> None:
        # Có preset mới/bị xóa → nạp lại danh sách ngay lập tức.
        self.async_schedule_update_ha_state(force_refresh=True)

    @property
    def options(self):
        return [p["name"] for p in self._presets]

    async def async_update(self):
        self._presets = await self.hass.async_add_executor_job(self._hub.get_presets)


class ImouGotoPresetSelect(_ImouPresetSelectBase):
    _attr_name = "Đi tới vị trí"
    _attr_icon = "mdi:map-marker"

    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id)
        self._attr_unique_id = f"{entry_id}_preset_select"

    @property
    def current_option(self):
        return self._current

    async def async_select_option(self, option: str) -> None:
        token = self._token_by_name(option)
        if token is None:
            return
        await self.hass.async_add_executor_job(self._hub.goto_preset, token)
        self._current = option
        self.async_write_ha_state()


class ImouRemovePresetSelect(_ImouPresetSelectBase):
    _attr_name = "Xóa vị trí"
    _attr_icon = "mdi:map-marker-remove"

    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id)
        self._attr_unique_id = f"{entry_id}_preset_remove"

    @property
    def current_option(self):
        # Không giữ lựa chọn — luôn là lời nhắc chọn để xóa.
        return None

    async def async_select_option(self, option: str) -> None:
        token = self._token_by_name(option)
        if token is None:
            return
        await self.hass.async_add_executor_job(self._hub.remove_preset, token)
        # Báo cho các entity khác (select đi tới) làm mới danh sách.
        async_dispatcher_send(self.hass, SIGNAL_PRESETS_UPDATED)
