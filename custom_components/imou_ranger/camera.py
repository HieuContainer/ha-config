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
    async_add_entities([ImouRangerCamera(hub, entry.entry_id)])


class ImouRangerCamera(Camera):
    """Camera Imou Ranger 2 (ONVIF/RTSP)."""

    _attr_has_entity_name = True
    _attr_name = None  # dùng tên thiết bị
    _attr_supported_features = CameraEntityFeature.STREAM

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        super().__init__()
        self._hub = hub
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_camera"

    @property
    def device_info(self) -> DeviceInfo:
        info = self._hub.info or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=info.get("model") or "Imou Ranger 2",
            manufacturer=info.get("manufacturer") or "Imou",
            model=info.get("model"),
            sw_version=info.get("firmware"),
            serial_number=info.get("serial"),
        )

    async def stream_source(self) -> str | None:
        # subtype=1 = luồng phụ (độ phân giải thấp) → độ trễ thấp, mượt khi
        # điều khiển PTZ trong mạng nội bộ. Có kèm credential cho ffmpeg/go2rtc.
        return await self.hass.async_add_executor_job(
            lambda: self._hub.get_rtsp_url(1, True)
        )

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        # Ảnh tĩnh lấy từ luồng phụ cho nhanh.
        return await self.hass.async_add_executor_job(self._hub.get_snapshot, 1)

    @property
    def extra_state_attributes(self):
        info = self._hub.info or {}
        return {
            "manufacturer": info.get("manufacturer"),
            "model": info.get("model"),
            "firmware": info.get("firmware"),
            "serial": info.get("serial"),
            "host": self._hub.host,
        }
