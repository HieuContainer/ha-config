"Thực thể cảm biến nhị phân (Binary Sensor) cho camera Imou Ranger / Dahua.

Hỗ trợ:
- Cảm biến Chuyển động (Motion)
- Cảm biến Phát hiện Xe (Vehicle Detection)
- Cảm biến Phát hiện Người (Human Detection)
"
from __future__ import annotations

import asyncio
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hub import ImouOnvifHub

_LOGGER = logging.getLogger(__name__)

# Thời gian tự động trả về Off nếu không nhận được sự kiện Stop từ camera (giây)
AUTO_OFF_SECONDS = 15


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    "Thiết lập các binary sensor cho camera."
    hub: ImouOnvifHub = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = [
        ImouMotionBinarySensor(hub, entry.entry_id),
        ImouVehicleBinarySensor(hub, entry.entry_id),
        ImouHumanBinarySensor(hub, entry.entry_id),
    ]

    async_add_entities(entities)


class ImouBaseBinarySensor(BinarySensorEntity):
    "Cơ sở cho các cảm biến nhị phân của camera Imou."

    _attr_has_entity_name = True

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        self._hub = hub
        self._entry_id = entry_id
        self._attr_is_on = False
        self._auto_off_handle: asyncio.TimerHandle | None = None

    @property
    def device_info(self) -> DeviceInfo:
        info = self._hub.info or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=info.get(model) or Imou Ranger,
            manufacturer=info.get(manufacturer) or Imou,
            model=info.get(model),
            sw_version=info.get(firmware),
            serial_number=info.get(serial),
        )

    async def async_added_to_hass(self) -> None:
        "Đăng ký nhận sự kiện khi entity được thêm vào HA."
        self._hub.register_event_callback(self._handle_event)

    async def async_will_remove_from_hass(self) -> None:
        "Hủy đăng ký nhận sự kiện."
        self._hub.unregister_event_callback(self._handle_event)
        self._cancel_auto_off()

    def _cancel_auto_off(self) -> None:
        if self._auto_off_handle:
            self._auto_off_handle.cancel()
            self._auto_off_handle = None

    def _reset_auto_off(self) -> None:
        self._cancel_auto_off()
        self._auto_off_handle = self.hass.loop.call_later(
            AUTO_OFF_SECONDS, self._auto_off_callback
        )

    @callback
    def _auto_off_callback(self) -> None:
        if self._attr_is_on:
            self._attr_is_on = False
            self.async_write_ha_state()

    def _handle_event(self, code: str, action: str, index: int) -> None:
        "Xử lý sự kiện nhận được từ stream (được override ở class con)."
        raise NotImplementedError


class ImouMotionBinarySensor(ImouBaseBinarySensor):
    "Cảm biến phát hiện chuyển động chung."

    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_translation_key = motion
    _attr_name = Chuyển động

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        super().__init__(hub, entry_id)
        self._attr_unique_id = f{entry_id}_motion

    def _handle_event(self, code: str, action: str, index: int) -> None:
        if code in [
            VideoMotion,
            SmartMotionHuman,
            SmartMotionVehicle,
            CrossLineDetection,
            CrossRegionDetection,
        ]:
            new_state = action.lower() == start
            if new_state != self._attr_is_on or new_state:
                self._attr_is_on = new_state
                if new_state:
                    self._reset_auto_off()
                else:
                    self._cancel_auto_off()
                self.schedule_update_ha_state()


class ImouVehicleBinarySensor(ImouBaseBinarySensor):
    "Cảm biến phát hiện xe ô tô / xe máy."

    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_icon = mdi:car
    _attr_name = Phát hiện xe

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        super().__init__(hub, entry_id)
        self._attr_unique_id = f{entry_id}_vehicle

    def _handle_event(self, code: str, action: str, index: int) -> None:
        if code in [SmartMotionVehicle]:
            new_state = action.lower() == start
            if new_state != self._attr_is_on or new_state:
                self._attr_is_on = new_state
                if new_state:
                    self._reset_auto_off()
                else:
                    self._cancel_auto_off()
                self.schedule_update_ha_state()


class ImouHumanBinarySensor(ImouBaseBinarySensor):
    "Cảm biến phát hiện người (Human Detection)."

    _attr_device_class = BinarySensorDeviceClass.MOTION
    _attr_icon = mdi:account-alert
    _attr_name = Phát hiện người

    def __init__(self, hub: ImouOnvifHub, entry_id: str) -> None:
        super().__init__(hub, entry_id)
        self._attr_unique_id = f{entry_id}_human

    def _handle_event(self, code: str, action: str, index: int) -> None:
        if code in [SmartMotionHuman]:
            new_state = action.lower() == start
            if new_state != self._attr_is_on or new_state:
                self._attr_is_on = new_state
                if new_state:
                    self._reset_auto_off()
                else:
                    self._cancel_auto_off()
                self.schedule_update_ha_state()
