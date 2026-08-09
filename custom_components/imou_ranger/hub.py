"""Bộ điều khiển ONVIF (đồng bộ) cho camera Imou Ranger 2.

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
        self.profile = None
        self.ptz_token = None
        self.info = {}

    # ---------------------------------------------------------------
    def connect(self):
        """Kết nối ONVIF, nạp profile + PTZ. Ném lỗi nếu thất bại."""
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
        self.profile = profiles[0]

        try:
            self.ptz = cam.create_ptz_service()
            cfgs = self.ptz.GetConfigurations()
            self.ptz_token = cfgs[0].token if cfgs else None
        except Exception:
            self.ptz = None
            self.ptz_token = None

        self.cam = cam
        return self.info

    def _ensure(self):
        if self.cam is None:
            self.connect()

    def _profile_by_subtype(self, subtype):
        try:
            profiles = self.media.GetProfiles()
            idx = 1 if subtype == 1 and len(profiles) > 1 else 0
            return profiles[idx]
        except Exception:
            return self.profile

    # ---------------------------------------------------------------
    def get_rtsp_url(self, subtype=0, with_credentials=True):
        self._ensure()
        if with_credentials:
            cred = f"{quote(self.username)}:{quote(self.password)}@"
        else:
            cred = ""
        return (
            f"rtsp://{cred}{self.host}:{self.rtsp_port}"
            f"/cam/realmonitor?channel=1&subtype={subtype}&unicast=true&proto=Onvif"
        )

    def get_snapshot_uri(self, subtype=0):
        self._ensure()
        with self._lock:
            prof = self._profile_by_subtype(subtype)
            res = self.media.GetSnapshotUri({"ProfileToken": prof.token})
            return res.Uri

    def get_snapshot(self, subtype=0):
        """Trả về bytes ảnh JPEG (digest auth, fallback basic)."""
        uri = self.get_snapshot_uri(subtype)
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
        with self._lock:
            req = self.ptz.create_type("ContinuousMove")
            req.ProfileToken = self.profile.token
            req.Velocity = {
                "PanTilt": {"x": float(pan), "y": float(tilt)},
                "Zoom": {"x": float(zoom)},
            }
            self.ptz.ContinuousMove(req)

    def stop(self):
        self._ensure()
        if not self.ptz_token:
            return
        with self._lock:
            req = self.ptz.create_type("Stop")
            req.ProfileToken = self.profile.token
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
        with self._lock:
            presets = self.ptz.GetPresets({"ProfileToken": self.profile.token})
        out = []
        for p in presets or []:
            out.append({
                "token": p.token,
                "name": getattr(p, "Name", None) or str(p.token),
            })
        return out

    def goto_preset(self, token):
        self._ensure()
        with self._lock:
            self.ptz.GotoPreset({
                "ProfileToken": self.profile.token,
                "PresetToken": str(token),
            })

    def set_preset(self, name=None, token=None):
        """Lưu vị trí PTZ hiện tại thành preset. Trả về token.

        Camera có thể trả lỗi nếu vừa di chuyển xong (chưa ổn định) —
        đảm bảo đã dừng rồi thử lại một lần.
        """
        self._ensure()
        params = {"ProfileToken": self.profile.token}
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
        with self._lock:
            self.ptz.RemovePreset({
                "ProfileToken": self.profile.token,
                "PresetToken": str(token),
            })
