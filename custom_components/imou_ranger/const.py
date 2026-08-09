"""Hằng số cho tích hợp Imou Ranger 2 (ONVIF)."""

DOMAIN = "imou_ranger"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_RTSP_PORT = "rtsp_port"
CONF_NAME = "name"

DEFAULT_PORT = 80
DEFAULT_RTSP_PORT = 554
DEFAULT_NAME = "Imou Ranger 2"

# Dịch vụ PTZ / preset
SERVICE_PTZ_MOVE = "ptz_move"
SERVICE_PTZ_STOP = "ptz_stop"
SERVICE_PTZ_STEP = "ptz_step"
SERVICE_GOTO_PRESET = "goto_preset"
SERVICE_SET_PRESET = "set_preset"
SERVICE_REMOVE_PRESET = "remove_preset"

ATTR_PAN = "pan"
ATTR_TILT = "tilt"
ATTR_ZOOM = "zoom"
ATTR_DURATION = "duration"
ATTR_PRESET = "preset"
ATTR_NAME = "name"

# Tín hiệu nội bộ: phát khi danh sách preset thay đổi (lưu/xóa) để các
# entity liên quan (select/text) cập nhật ngay, không phải chờ polling.
SIGNAL_PRESETS_UPDATED = f"{DOMAIN}_presets_updated"

PLATFORMS = ["camera", "sensor", "select", "button", "text"]
