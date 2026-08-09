"""Thực thể cơ sở — gắn device_info chung."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .hub import ImouOnvifHub


class ImouBaseEntity(Entity):
    """Base có device_info từ hub."""

    _attr_has_entity_name = True

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        self._hub = hub
        self._entry_id = entry_id

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
