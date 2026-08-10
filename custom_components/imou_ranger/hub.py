"""Bộ điều khiển ONVIF (đồng bộ) cho camera Imou Ranger / Dual Lens.

Tất cả phương thức là blocking — HA gọi qua hass.async_add_executor_job.
"""
from __future__ import annotations

import threading
import time
from urllib.parse import quote

import requests
from requests.auth import HTTPDigestAuth

from onvif import ONVIFCamera


class ImouOnvifHub:
    """Bọc các thao tác ONVIF: info, stream, snapshot, PTZ, presets."""

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
