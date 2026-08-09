# HƯỚNG DẪN KẾT NỐI & ĐỒNG BỘ 2 CHIỀU HOME ASSISTANT (HAOS)

## 📌 Thông tin kết nối
- **IP HAOS (LAN)**: `192.168.1.17`
- **Samba Share**: `\\192.168.1.17\config`
- **Tên đăng nhập Samba**: `homeassistant`
- **Mật khẩu**: `HieuProX1902`
- **Thư mục Local PC**: `d:\hieu-haos-v1`

---

## 🚀 Các cách đồng bộ 2 chiều:

### 1. Đồng bộ Real-Time tự động (Khuyên dùng khi code)
Chạy script theo dõi file. Mỗi khi bạn lưu file (Ctrl+S) trên máy local, file sẽ ngay lập tức được đẩy sang HAOS:
```powershell
.\watch_sync.ps1
```

### 2. Kéo code mới nhất từ HAOS về Máy Local (Pull)
Nếu bạn chỉnh sửa dashboard/automation trực tiếp trên giao diện web Home Assistant, chạy lệnh này để kéo code mới nhất về PC:
```powershell
.\sync_pull.ps1
```

### 3. Đẩy toàn bộ code từ Local sang HAOS (Push thủ công)
Khi muốn đồng bộ thủ công toàn bộ thư mục từ máy local sang HAOS:
```powershell
.\sync_push.ps1
```

---

## ⚡ Các file chính đã kéo về máy:
- `configuration.yaml` - File cấu hình trung tâm HAOS
- `automations.yaml` - Các kịch bản tự động hóa
- `scripts.yaml` - Các script xử lý
- `secrets.yaml` - Mật khẩu và token bảo mật
- `dashboard_nha-c-a-hi-u.yaml` - File Dashboard chính
- `custom_components/` - Các tích hợp tùy chỉnh
- `www/` - Thẻ giao diện tùy chỉnh (Mushroom, Bubble Card, Sunsynk, ApexCharts...)
