"""Button entities — điều khiển PTZ nhanh + lưu vị trí hiện tại."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_PRESETS_UPDATED
from .entity import ImouBaseEntity
from .hub import ImouOnvifHub

# Vận tốc cao + bước ngắn = mỗi lần bấm nhích nhanh, phản hồi tức thì.
SPEED = 0.8
STEP = 0.4

# key, name, icon, (pan, tilt, zoom)
_MOVES = [
    ("up", "Lên", "mdi:arrow-up-bold", (0, SPEED, 0)),
    ("down", "Xuống", "mdi:arrow-down-bold", (0, -SPEED, 0)),
    ("left", "Trái", "mdi:arrow-left-bold", (-SPEED, 0, 0)),
    ("right", "Phải", "mdi:arrow-right-bold", (SPEED, 0, 0)),
    ("zoom_in", "Zoom +", "mdi:magnify-plus", (0, 0, SPEED)),
    ("zoom_out", "Zoom −", "mdi:magnify-minus", (0, 0, -SPEED)),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ImouMoveButton(hub, entry.entry_id, key, name, icon, vec)
        for key, name, icon, vec in _MOVES
    ]
    entities.append(ImouSavePresetButton(hub, entry.entry_id))
    async_add_entities(entities)


class ImouMoveButton(ImouBaseEntity, ButtonEntity):
    def __init__(self, hub, entry_id, key, name, icon, vec):
        super().__init__(hub, entry_id)
        self._vec = vec
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry_id}_ptz_{key}"

    async def async_press(self) -> None:
        pan, tilt, zoom = self._vec
        await self.hass.async_add_executor_job(
            lambda: self._hub.move_step(pan=pan, tilt=tilt, zoom=zoom, duration=STEP)
        )


class ImouSavePresetButton(ImouBaseEntity, ButtonEntity):
    _attr_name = "Lưu vị trí hiện tại"
    _attr_icon = "mdi:content-save-move"

    def __init__(self, hub, entry_id):
        super().__init__(hub, entry_id)
        self._attr_unique_id = f"{entry_id}_save_preset"

    async def async_press(self) -> None:
        name = f"Vị trí {datetime.now():%H:%M:%S}"
        await self.hass.async_add_executor_job(
            lambda: self._hub.set_preset(name=name)
        )
        async_dispatcher_send(self.hass, SIGNAL_PRESETS_UPDATED)
