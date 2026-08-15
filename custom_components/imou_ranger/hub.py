"""Bộ điều khiển ONVIF (đồng bộ) cho camera Imou Ranger / Dual Lens.

Tất cả phương thức là blocking — HA gọi qua hass.async_add_executor_job.
"""
from __future__ import annotations

import logging
import threading
import time
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth

from onvif import ONVIFCamera

from .const import EVENT_IMOU_HUMAN, EVENT_IMOU_MOTION, EVENT_IMOU_VEHICLE

_LOGGER = logging.getLogger(__name__)


class ImouOnvifHub:
    """Bọc các thao tác ONVIF: info, stream, snapshot, PTZ, presets và Dahua Event Stream."""

    def __init__(self, host, port, username, password, rtsp_port=554):
        self.host = host
        self.port = int(port)
        self.username = username
        self.password = password
        self.rtsp_port = int(rtsp_port)

        self._lock = threading.Lock()
        self.cam = None
        self.media = None
        self.ptz = None
        self.profiles = []
        self.profile = None
        self.ptz_profile = None
        self.ptz_token = None
        self.info = {}

        # Quản lý luồng sự kiện (Dahua Event Stream)
        self._hass = None
        self._event_thread: threading.Thread | None = None
        self._event_stop: threading.Event = threading.Event()
        self._event_callbacks: list[callable] = []
        self._states = {
            "motion": False,
            "vehicle": False,
            "human": False,
        }

    # ---------------------------------------------------------------
    # Quản lý luồng sự kiện chuyển động / nhận diện xe / người
    # ---------------------------------------------------------------
    def start_event_listener(self, hass) -> None:
        """Bắt đầu luồng nền lắng nghe sự kiện từ camera."""
        self._hass = hass
        if self._event_thread and self._event_thread.is_alive():
            return
        self._event_stop.clear()
        self._event_thread = threading.Thread(
            target=self._run_event_stream,
            daemon=True,
            name=f"ImouEvent-{self.host}",
        )
        self._event_thread.start()
        _LOGGER.info("Đã khởi chạy luồng lắng nghe sự kiện cho camera %s", self.host)

    def stop_event_listener(self) -> None:
        """Dừng luồng lắng nghe sự kiện."""
        self._event_stop.set()
        _LOGGER.info("Đã gửi tín hiệu dừng event listener camera %s", self.host)

    def register_event_callback(self, callback: callable) -> None:
        """Đăng ký hàm callback khi có sự kiện."""
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)

    def unregister_event_callback(self, callback: callable) -> None:
        """Hủy đăng ký callback."""
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def get_state(self, state_type: str) -> bool:
        """Lấy trạng thái hiện tại (motion, vehicle, human)."""
        return self._states.get(state_type, False)

    def _run_event_stream(self) -> None:
        """Kết nối HTTP Stream tới /cgi-bin/eventManager.cgi và lắng nghe liên tục."""
        url = (
            f"http://{self.host}:{self.port}"
            "/cgi-bin/eventManager.cgi?action=attach"
            "&codes=[VideoMotion,SmartMotionHuman,SmartMotionVehicle,CrossLineDetection,CrossRegionDetection,AlarmLocal]"
        )
        auth = HTTPDigestAuth(self.username, self.password)

        while not self._event_stop.is_set():
            try:
                with requests.get(url, auth=auth, stream=True, timeout=(10, 60)) as r:
                    if r.status_code == 401:
                        # Fallback basic auth
                        r = requests.get(
                            url,
                            auth=(self.username, self.password),
                            stream=True,
                            timeout=(10, 60),
                        )

                    if r.status_code != 200:
                        _LOGGER.warning(
                            "Không thể mở event stream trên %s: HTTP %s (sẽ thử lại sau 10s)",
                            self.host,
                            r.status_code,
                        )
                        time.sleep(10)
                        continue

                    _LOGGER.info("Đã kết nối thành công event stream camera %s", self.host)
                    for line in r.iter_lines(chunk_size=512):
                        if self._event_stop.is_set():
                            break
                        if not line:
                            continue
                        try:
                            text = line.decode("utf-8", errors="ignore").strip()
                        except Exception:
                            continue

                        if "Code=" in text and "action=" in text:
                            self._process_event_line(text)

            except Exception as exc:
                if not self._event_stop.is_set():
                    _LOGGER.debug(
                        "Mất kết nối event stream camera %s: %s (tự kết nối lại sau 5s)",
                        self.host,
                        exc,
                    )
                    time.sleep(5)

    def _process_event_line(self, text: str) -> None:
        """Phân tích dòng sự kiện từ Dahua event stream."""
        parts = text.split(";")
        kv: dict[str, str] = {}
        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                kv[k.strip()] = v.strip()

        code = kv.get("Code", "")
        action = kv.get("action", "")  # "Start" hoặc "Stop"
        try:
            index = int(kv.get("index", 0))
        except ValueError:
            index = 0

        if not code or not action:
            return

        is_on = action.lower() == "start"

        event_type = None
        if code in ["VideoMotion", "CrossLineDetection", "CrossRegionDetection"]:
            self._states["motion"] = is_on
            event_type = EVENT_IMOU_MOTION
        elif code in ["SmartMotionVehicle"]:
            self._states["vehicle"] = is_on
            self._states["motion"] = is_on
            event_type = EVENT_IMOU_VEHICLE
        elif code in ["SmartMotionHuman"]:
            self._states["human"] = is_on
            self._states["motion"] = is_on
            event_type = EVENT_IMOU_HUMAN

        # Bắn sự kiện lên HA Event Bus
        if self._hass and event_type and is_on:
            event_data = {
                "host": self.host,
                "code": code,
                "action": action,
                "index": index,
                "device_name": self.info.get("model") or "Imou Camera",
            }
            try:
                self._hass.loop.call_soon_threadsafe(
                    self._hass.bus.async_fire, event_type, event_data
                )
            except Exception as err:
                _LOGGER.debug("Lỗi khi bắn event %s: %s", event_type, err)

        # Gọi các callback đã đăng ký từ entity
        for cb in list(self._event_callbacks):
            try:
                cb(code, action, index)
            except Exception as err:
                _LOGGER.error("Lỗi khi chạy callback event: %s", err)

    # ---------------------------------------------------------------

    def connect(self):
        """Kết nối ONVIF, nạp profiles + PTZ. Ném lỗi nếu thất bại."""
        cam = ONVIFCamera(self.host, self.port, self.username, self.password)
        cam.update_xaddrs()

        dev = cam.create_devicemgmt_service()
        di = dev.GetDeviceInformation()
        self.info = {
            "manufacturer": di.Manufacturer,
            "model": di.Model,
            "firmware": di.FirmwareVersion,
            "serial": di.SerialNumber,
        }

        self.media = cam.create_media_service()
        profiles = self.media.GetProfiles()
        if not profiles:
            raise RuntimeError("Camera không có media profile nào")
        self.profiles = profiles
        self.profile = profiles[0]

        try:
            self.ptz = cam.create_ptz_service()
            cfgs = self.ptz.GetConfigurations()
            self.ptz_token = cfgs[0].token if cfgs else None

            # Tìm profile nào hỗ trợ PTZ Configuration (ưu tiên mắt xoay)
            self.ptz_profile = None
            for p in profiles:
                if getattr(p, "PTZConfiguration", None):
                    self.ptz_profile = p
                    break
            if not self.ptz_profile:
                self.ptz_profile = self.profile
        except Exception:
            self.ptz = None
            self.ptz_token = None
            self.ptz_profile = self.profile

        self.cam = cam
        return self.info

    def _ensure(self):
        if self.cam is None:
            self.connect()

    def get_available_channels(self) -> list[int]:
        """Xác định số lượng mắt (kênh) của camera."""
        self._ensure()
        model = (self.info.get("model") or "").upper()
        if len(self.profiles) >= 3 or any(k in model for k in ["S2X", "S7X", "DUAL", "2-LENS", "2LENS", "6M0WED"]):
            return [1, 2]
        return [1]

    def _profile_by_channel_and_subtype(self, channel=1, subtype=1):
        try:
            profiles = self.media.GetProfiles()
            if channel == 2 and len(profiles) >= 3:
                idx = 3 if subtype == 1 and len(profiles) >= 4 else 2
                return profiles[idx]
            idx = 1 if subtype == 1 and len(profiles) > 1 else 0
            return profiles[idx]
        except Exception:
            return self.profile

    # ---------------------------------------------------------------
    def get_rtsp_url(self, channel=1, subtype=1, with_credentials=True):
        self._ensure()
        if with_credentials:
            cred = f"{quote(self.username)}:{quote(self.password)}@"
        else:
            cred = ""
        return (
            f"rtsp://{cred}{self.host}:{self.rtsp_port}"
            f"/cam/realmonitor?channel={channel}&subtype={subtype}&unicast=true&proto=Onvif"
        )

    def get_snapshot_uri(self, channel=1, subtype=1):
        self._ensure()
        with self._lock:
            prof = self._profile_by_channel_and_subtype(channel, subtype)
            res = self.media.GetSnapshotUri({"ProfileToken": prof.token})
            return res.Uri

    def get_snapshot(self, channel=1, subtype=1):
        """Trả về bytes ảnh JPEG (digest auth, fallback basic)."""
        uri = self.get_snapshot_uri(channel, subtype)
        r = requests.get(
            uri, auth=HTTPDigestAuth(self.username, self.password), timeout=10
        )
        if r.status_code == 401:
            r = requests.get(uri, auth=(self.username, self.password), timeout=10)
        r.raise_for_status()
        return r.content

    # ---------------------------------------------------------------
    # PTZ
    def continuous_move(self, pan=0.0, tilt=0.0, zoom=0.0):
        self._ensure()
        if not self.ptz_token:
            raise RuntimeError("Camera không hỗ trợ PTZ")
        prof = self.ptz_profile or self.profile
        with self._lock:
            req = self.ptz.create_type("ContinuousMove")
            req.ProfileToken = prof.token
            req.Velocity = {
                "PanTilt": {"x": float(pan), "y": float(tilt)},
                "Zoom": {"x": float(zoom)},
            }
            self.ptz.ContinuousMove(req)

    def stop(self):
        self._ensure()
        if not self.ptz_token:
            return
        prof = self.ptz_profile or self.profile
        with self._lock:
            req = self.ptz.create_type("Stop")
            req.ProfileToken = prof.token
            req.PanTilt = True
            req.Zoom = True
            self.ptz.Stop(req)

    def move_step(self, pan=0.0, tilt=0.0, zoom=0.0, duration=0.5):
        self.continuous_move(pan, tilt, zoom)
        time.sleep(max(0.05, min(float(duration), 5.0)))
        self.stop()

    # ---------------------------------------------------------------
    # Presets
    def get_presets(self):
        self._ensure()
        if not self.ptz_token:
            return []
        prof = self.ptz_profile or self.profile
        with self._lock:
            presets = self.ptz.GetPresets({"ProfileToken": prof.token})
        out = []
        for p in presets or []:
            out.append({
                "token": p.token,
                "name": getattr(p, "Name", None) or str(p.token),
            })
        return out

    def goto_preset(self, token):
        self._ensure()
        prof = self.ptz_profile or self.profile
        with self._lock:
            self.ptz.GotoPreset({
                "ProfileToken": prof.token,
                "PresetToken": str(token),
            })

    def set_preset(self, name=None, token=None):
        """Lưu vị trí PTZ hiện tại thành preset. Trả về token."""
        self._ensure()
        prof = self.ptz_profile or self.profile
        params = {"ProfileToken": prof.token}
        if name:
            params["PresetName"] = str(name)
        if token:
            params["PresetToken"] = str(token)
        try:
            self.stop()
        except Exception:
            pass
        last_err = None
        for attempt in range(2):
            try:
                with self._lock:
                    res = self.ptz.SetPreset(params)
                return getattr(res, "PresetToken", res)
            except Exception as err:  # noqa: BLE001
                last_err = err
                time.sleep(0.7)
        raise last_err

    def remove_preset(self, token):
        self._ensure()
        prof = self.ptz_profile or self.profile
        with self._lock:
            self.ptz.RemovePreset({
                "ProfileToken": prof.token,
                "PresetToken": str(token),
            })
