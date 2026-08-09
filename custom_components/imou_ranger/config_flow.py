"""Config flow cho Imou Ranger 2 (ONVIF) — hỏi IP, tài khoản, mật khẩu."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RTSP_PORT,
    CONF_USERNAME,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_RTSP_PORT,
    DOMAIN,
)
from .hub import ImouOnvifHub


async def _validate(hass: HomeAssistant, data: dict) -> dict:
    """Thử kết nối camera, trả về thông tin thiết bị."""
    hub = ImouOnvifHub(
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        rtsp_port=data.get(CONF_RTSP_PORT, DEFAULT_RTSP_PORT),
    )
    return await hass.async_add_executor_job(hub.connect)


class ImouRangerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Xử lý luồng thêm tích hợp qua UI."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate(self.hass, user_input)
            except Exception:  # noqa: BLE001
                errors["base"] = "cannot_connect"
            else:
                serial = info.get("serial") or user_input[CONF_HOST]
                await self.async_set_unique_id(str(serial))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME) or DEFAULT_NAME,
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME, default="admin"): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Optional(CONF_RTSP_PORT, default=DEFAULT_RTSP_PORT): int,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        })
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
