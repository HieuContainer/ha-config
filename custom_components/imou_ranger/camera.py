"""Camera entity — stream RTSP + snapshot ONVIF."""
from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import ImouOnvifHub


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]
    channels = await hass.async_add_executor_job(hub.get_available_channels)

    entities = []
    if len(channels) > 1:
        for ch in channels:
            name_suffix = "Mắt Cố Định" if ch == 1 else "Mắt Xoay PTZ"
            entities.append(ImouRangerCamera(hub, entry.entry_id, channel=ch, name_suffix=name_suffix))
    else:
        entities.append(ImouRangerCamera(hub, entry.entry_id, channel=1, name_suffix=None))

    async_add_entities(entities)


class ImouRangerCamera(Camera):
    """Camera Imou Ranger / Dual Lens (ONVIF/RTSP)."""

    _attr_has_entity_name = True
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, hub: ImouOnvifHub, entry_id: str, channel: int = 1, name_suffix: str | None = None) -> None:
        super().__init__()
        self._hub = hub
        self._entry_id = entry_id
        self._channel = channel
        if name_suffix:
            self._attr_name = name_suffix
            self._attr_unique_id = f"{entry_id}_camera_ch{channel}"
        else:
            self._attr_name = None  # Dùng tên thiết bị
            self._attr_unique_id = f"{entry_id}_camera"

    @property
    def device_info(self) -> DeviceInfo:
        info = self._hub.info or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=info.get("model") or "Imou Ranger",
            manufacturer=info.get("manufacturer") or "Imou",
            model=info.get("model"),
            sw_version=info.get("firmware"),
            serial_number=info.get("serial"),
        )

    async def stream_source(self) -> str | None:
        # subtype=1 = luồng phụ H.264 (độ trễ thấp, mượt mà trên web và app)
        return await self.hass.async_add_executor_job(
            lambda: self._hub.get_rtsp_url(channel=self._channel, subtype=1, with_credentials=True)
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return await self.hass.async_add_executor_job(
            lambda: self._hub.get_snapshot(channel=self._channel, subtype=1)
        )

    @property
    def extra_state_attributes(self):
        info = self._hub.info or {}
        return {
            "channel": self._channel,
            "manufacturer": info.get("manufacturer"),
            "model": info.get("model"),
            "firmware": info.get("firmware"),
            "serial": info.get("serial"),
            "host": self._hub.host,
        }
