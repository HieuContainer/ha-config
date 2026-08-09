# Scripts khong lay duoc YAML qua giao dien

Cac script sau TON TAI va CHAY BINH THUONG nhung KHONG nam trong scripts.yaml
(Home Assistant bao: "Chi nhung tap lenh nam trong scripts.yaml la co the chinh sua"),
nen khong the lay noi dung qua API/UI. Nhieu kha nang chung duoc khai bao truc tiep
trong configuration.yaml (muc `script:`) hoac trong 1 file duoc `!include` rieng.

Danh sach:
- `script.cua_mo`
- `script.cua_dung`
- `script.cua_dong`

De lay dung noi dung, mo file qua add-on **File editor** / **Studio Code Server** / SSH
tren chinh HA (Settings > Add-ons), tim trong `configuration.yaml` muc `script:` hoac cac file duoc include.
