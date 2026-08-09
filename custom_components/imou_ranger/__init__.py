"""Tích hợp Imou Ranger 2 qua ONVIF (local)."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
import homeassistant.helpers.entity_registry as er

from .const import (
    ATTR_DURATION,
    ATTR_NAME,
    ATTR_PAN,
    ATTR_PRESET,
    ATTR_TILT,
    ATTR_ZOOM,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RTSP_PORT,
    CONF_USERNAME,
    DEFAULT_RTSP_PORT,
    DOMAIN,
    PLATFORMS,
    SERVICE_GOTO_PRESET,
    SERVICE_PTZ_MOVE,
    SERVICE_PTZ_STEP,
    SERVICE_PTZ_STOP,
    SERVICE_REMOVE_PRESET,
    SERVICE_SET_PRESET,
)
from .hub import ImouOnvifHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Thiết lập tích hợp từ config entry."""
    data = entry.data
    hub = ImouOnvifHub(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, 80),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        rtsp_port=data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT),
    )

    try:
        await hass.async_add_executor_job(hub.connect)
    except Exception as err:  # noqa: BLE001
        _LOGGER.error("Không kết nối được camera ONVIF %s: %s", data[CONF_HOST], err)
        raise HomeAssistantError(f"Không kết nối được camera: {err}") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _register_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Gỡ tích hợp."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            _unregister_services(hass)
    return unload_ok


def _resolve_hubs(hass: HomeAssistant, call: ServiceCall):
    """Tìm hub từ entity_id/device trong service call (mặc định: tất cả)."""
    hubs = list(hass.data.get(DOMAIN, {}).values())
    entity_ids = call.data.get("entity_id")
    if not entity_ids:
        return hubs

    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]
    registry = er.async_get(hass)
    selected = []
    for eid in entity_ids:
        ent = registry.async_get(eid)
        if ent and ent.config_entry_id in hass.data.get(DOMAIN, {}):
            selected.append(hass.data[DOMAIN][ent.config_entry_id])
    return selected or hubs


def _register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_PTZ_MOVE):
        return

    async def _run(func_name, call: ServiceCall, **kwargs):
        for hub in _resolve_hubs(hass, call):
            func = getattr(hub, func_name)
            await hass.async_add_executor_job(lambda f=func: f(**kwargs))

    async def ptz_move(call: ServiceCall):
        await _run("continuous_move", call,
                   pan=call.data.get(ATTR_PAN, 0.0),
                   tilt=call.data.get(ATTR_TILT, 0.0),
                   zoom=call.data.get(ATTR_ZOOM, 0.0))

    async def ptz_step(call: ServiceCall):
        await _run("move_step", call,
                   pan=call.data.get(ATTR_PAN, 0.0),
                   tilt=call.data.get(ATTR_TILT, 0.0),
                   zoom=call.data.get(ATTR_ZOOM, 0.0),
                   duration=call.data.get(ATTR_DURATION, 0.5))

    async def ptz_stop(call: ServiceCall):
        await _run("stop", call)

    async def goto_preset(call: ServiceCall):
        await _run("goto_preset", call, token=call.data[ATTR_PRESET])

    async def set_preset(call: ServiceCall):
        await _run("set_preset", call, name=call.data.get(ATTR_NAME))

    async def remove_preset(call: ServiceCall):
        await _run("remove_preset", call, token=call.data[ATTR_PRESET])

    base = {vol.Optional("entity_id"): cv.entity_ids}

    hass.services.async_register(DOMAIN, SERVICE_PTZ_MOVE, ptz_move, schema=vol.Schema({
        **base,
        vol.Optional(ATTR_PAN, default=0.0): vol.Coerce(float),
        vol.Optional(ATTR_TILT, default=0.0): vol.Coerce(float),
        vol.Optional(ATTR_ZOOM, default=0.0): vol.Coerce(float),
    }))
    hass.services.async_register(DOMAIN, SERVICE_PTZ_STEP, ptz_step, schema=vol.Schema({
        **base,
        vol.Optional(ATTR_PAN, default=0.0): vol.Coerce(float),
        vol.Optional(ATTR_TILT, default=0.0): vol.Coerce(float),
        vol.Optional(ATTR_ZOOM, default=0.0): vol.Coerce(float),
        vol.Optional(ATTR_DURATION, default=0.5): vol.Coerce(float),
    }))
    hass.services.async_register(DOMAIN, SERVICE_PTZ_STOP, ptz_stop,
                                 schema=vol.Schema(base))
    hass.services.async_register(DOMAIN, SERVICE_GOTO_PRESET, goto_preset,
                                 schema=vol.Schema({**base, vol.Required(ATTR_PRESET): cv.string}))
    hass.services.async_register(DOMAIN, SERVICE_SET_PRESET, set_preset,
                                 schema=vol.Schema({**base, vol.Optional(ATTR_NAME): cv.string}))
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_PRESET, remove_preset,
                                 schema=vol.Schema({**base, vol.Required(ATTR_PRESET): cv.string}))


def _unregister_services(hass: HomeAssistant) -> None:
    for svc in (SERVICE_PTZ_MOVE, SERVICE_PTZ_STEP, SERVICE_PTZ_STOP,
                SERVICE_GOTO_PRESET, SERVICE_SET_PRESET, SERVICE_REMOVE_PRESET):
        if hass.services.has_service(DOMAIN, svc):
            hass.services.async_remove(DOMAIN, svc)
