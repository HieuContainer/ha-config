# 🏠 Hieu Home Assistant - Huong Dan Quan Ly Code

> **Du an:** Cau hinh Home Assistant cua Nha Hieu
> **HAOS IP (LAN):** `192.168.1.17`
> **Truy cap tu Internet:** `https://minhhieubg.online`
> **GitHub Backup:** `https://github.com/HieuContainer/ha-config`
> **Thu muc Local PC:** `d:\hieu-haos-v1`

---

## QUAN TRONG - Doc Truoc

Dashboard **"Nha Cua Hieu"** dang chay o che do **Storage Mode** - nghia la HAOS luu giao dien trong bo nho noi bo (file `.storage/lovelace.nha_c_a_hi_u`), **khong doc truc tiep tu file YAML**.

Co **2 cach** de sua giao dien:

| Cach | Phu hop khi | Ket qua |
|------|------------|---------|
| Sua tren Web HAOS | Sua nhanh 1-2 cho nho | Thay doi ngay lap tuc |
| Sua code YAML tren VS Code | Sua nhieu cho, muon Git backup | Can copy lai vao HAOS qua RAW editor |

---

## CACH 1: Sua Nhanh Tren Web (De Nhat)

Dung khi chi muon doi ten the, mau sac, them/xoa 1 the nho.

1. Mo trinh duyet - truy cap `https://minhhieubg.online`
2. Tren Dashboard "Nha Cua Hieu" - bam **but chi (but ky) o goc tren phai**
3. Chon the muon sua - bam **"Chinh sua"**
4. Sua xong - bam **"Luu"** - thay doi hien ra ngay!

> Sau khi sua tren web xong, nen chay `.\sync_pull.ps1` de keo ban moi nhat ve Local PC.

---

## CACH 2: Sua Code YAML Tren VS Code (Chuyen Nghiep)

### Buoc 1 - Keo code moi nhat tu HAOS ve may

> **BAT BUOC lam truoc khi sua** de tranh bi ghi de mat cong!

```powershell
.\sync_pull.ps1
```

### Buoc 2 - Tim dung file can sua

| Ban muon sua | Mo file nay |
|-------------|------------|
| Giao dien "Nha Cua Hieu" | `dashboard_nha-c-a-hi-u.yaml` |
| Dashboard phu | `dashboard_nha-c-a-hi-u-2.yaml` |
| Kich ban tu dong (automation) | `automations.yaml` |
| Script | `scripts.yaml` |
| Cai dat he thong, sensor | `configuration.yaml` |
| Mau sac giao dien (theme toi) | `themes/noctis/noctis.yaml` |

> Cau truc Dashboard chinh (`dashboard_nha-c-a-hi-u.yaml`):
> - Dong 1 den 1087: Tab "Che do Phone"
> - Dong 1089 den cuoi: Tab "Che do PC"

### Buoc 3 - Sua code

Dung `Ctrl + F` trong VS Code de tim nhanh chu can sua.

### Buoc 4 - Day code len HAOS

```powershell
.\sync_push.ps1
```

### Buoc 5 - Ap dung vao Dashboard Storage Mode

> Dashboard "Nha Cua Hieu" dung **Storage Mode** nen can them 1 buoc:
> 1. Vao `https://minhhieubg.online` - bam but chi (but ky)
> 2. Bam **"Chinh sua code thu (RAW)"** o menu 3 cham
> 3. Xoa het noi dung cu - Dan noi dung file YAML moi vao - Luu

---

## DONG BO 2 CHIEU - Quy Trinh Chuan

```
HAOS (minhhieubg.online)
     |  sync_pull.ps1  (keo ve may)
d:\hieu-haos-v1  (Local PC - VS Code)
     |  sync_push.ps1  (day len HAOS)
HAOS (minhhieubg.online)
     |  git push / git pull
GitHub (github.com/HieuContainer/ha-config)
```

---

## BO SCRIPT CO SAN

Mo Terminal trong VS Code tai `d:\hieu-haos-v1`:

```powershell
# Keo code moi nhat tu HAOS ve Local PC
.\sync_pull.ps1

# Day code tu Local PC len HAOS
.\sync_push.ps1

# Luu phien ban len GitHub
git add .
git commit -m "Mo ta thay doi"
git push
```

---

## THONG TIN KET NOI (Bao Mat)

```
IP HAOS (LAN):     192.168.1.17
Samba Share:       \\192.168.1.17\config
Samba User:        homeassistant
Samba Pass:        [xem file .env]
SSH:               ssh root@192.168.1.17 (port 22)
```

Chi tiet trong file `.env` (khong commit len GitHub).

---

## CAU TRUC THU MUC

```
d:\hieu-haos-v1\
|-- configuration.yaml           <- Cai dat he thong
|-- automations.yaml             <- Kich ban tu dong hoa
|-- scripts.yaml                 <- Script lenh
|-- dashboard_nha-c-a-hi-u.yaml <- Giao dien Dashboard chinh
|-- dashboard_nha-c-a-hi-u-2.yaml <- Dashboard phu
|-- secrets.yaml                 <- Mat khau (KHONG commit Git)
|-- custom_components/           <- Tich hop tuy chinh (Tuya, HACS...)
|-- www/                         <- The giao dien JS (Mushroom, Bubble Card...)
|-- themes/noctis/               <- Theme toi Noctis
```

---

## CAU HOI THUONG GAP

**H: Toi sua file YAML nhung HAOS khong thay doi?**
> A: Dashboard dang dung Storage Mode. Phai copy noi dung YAML vao HAOS qua giao dien RAW editor (but chi → 3 cham → Chinh sua code thu).

**H: Lenh `git` bao loi "not recognized"?**
> A: Dong VS Code va mo lai. Hoac goi truc tiep: `& "C:\Program Files\Git\cmd\git.exe" push`

**H: Lenh `.\sync_push.ps1` bao loi "running scripts is disabled"?**
> A: Chay 1 lan: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**H: Khong ket noi duoc Samba (\\192.168.1.17\config)?**
> A: Kiem tra HAOS co dang bat Add-on **Samba Share** khong. Vao HAOS → Settings → Add-ons → Samba share → Start.

**H: Git bao loi "Repository not found" khi push?**
> A: Kiem tra da tao repo tai github.com/HieuContainer/ha-config chua. Va chay: `git remote -v` de xac nhan.
