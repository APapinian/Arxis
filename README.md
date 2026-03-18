# ⚙️ Arxis

> Arch Linux için modern, grafik arayüzlü paket yöneticisi.  
> Pacman · AUR · Flatpak · AppImage · GitHub — hepsi tek pencerede.

---

## ✨ Özellikler

### Paket Kaynakları
- **Pacman** — resmi Arch depolarından kurulum/kaldırma/güncelleme
- **AUR** — `yay` veya `paru` ile AUR paket desteği
- **Flatpak** — Flathub entegrasyonu, uygulama ID ile doğru kurulum
- **AppImage** — appimage.github.io feed'inden arama ve `~/.local/share/AppImages`'a kurulum
- **Wine / Proton** — Wine tabanlı paket yönetimi

### Arayüz
- Koyu tema, animasyonlu sidebar ve sağdan kayan paneller
- Canlı arama (300ms debounce)
- Sağ tık context menüsü: Kur · Kaldır · Detay · **Karşılaştırmaya Ekle**
- Bildirim toast'ları (başarı/hata)
- Bant genişliği grafiği (kurulum sırasında anlık MB/s)

### Sayfalar

| Sayfa | Açıklama |
|---|---|
| **Keşfet** | Öne çıkan ve popüler paketler, güncelleme listesi |
| **Yüklü** | Kurulu paketler, toplu kaldırma, canlı filtre |
| **Kategoriler** | Oyun · Geliştirme · Ses · Grafik · Güvenlik… |
| **⇔ Karşılaştır** | İki paketi yan yana sürüm/lisans/bağımlılık karşılaştırması |
| **⊙ Geçmiş** | Kurulum/kaldırma geçmişi, istatistikler, JSON/CSV dışa aktarma |
| **◫ Snapshot** | Kurulu paket listesini JSON olarak kaydet, fark görüntüleme |
| **⌥ GitHub** | GitHub repo/release URL'sinden doğrudan kur (`install.sh` · `Makefile` · `meson` · `cmake`) |
| **⚒ Bakım** | Yetim paket temizleme, önbellek temizleme, sistem bilgisi |
| **⚙ Ayarlar** | Toggle switch'ler, `~/.config/arxis/settings.json`'a kalıcı kayıt |

### Güvenlik
- Sudo şifresi **uygulama içi diyalog**dan alınır, terminale yazılmaz
- Şifre oturum boyunca bellekte tutulur, diske yazılmaz
- Uygulama kapanınca sıfırlanır

---

## 📦 Gereksinimler

- **Python** >= 3.11
- **Arch Linux** (veya türevleri: Manjaro, EndeavourOS…)
- `pacman` (zorunlu)
- `yay` veya `paru` (AUR için, opsiyonel)
- `flatpak` (opsiyonel)

### Python bağımlılıkları

```bash
pip install -r requirements.txt
```

| Paket | Sürüm | Amaç |
|---|---|---|
| `PyQt6` | ≥ 6.5.0 | Arayüz |
| `psutil` | ≥ 5.9.0 | CPU/RAM/ağ izleme |

---

## 🚀 Kurulum

```bash
# Repoyu klonla
git clone https://github.com/KULLANICI_ADI/arxis.git
cd arxis

# Sanal ortam oluştur (önerilir)
python -m venv venv
source venv/bin/activate

# Bağımlılıkları kur
pip install -r requirements.txt

# Başlat
python main.py
```

---

## 📁 Proje Yapısı

```
arxis/
├── main.py                  # Giriş noktası
├── requirements.txt
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Tüm arayüz sınıfları (~3500 satır)
│   └── styles.py            # Koyu tema CSS
└── backend/
    ├── __init__.py
    ├── managers.py          # Paket yöneticisi katmanı (~1300 satır)
    └── system_monitor.py    # CPU/RAM/ağ izleme thread'leri
```

---

## ⌨️ Klavye Kısayolları

| Kısayol | Eylem |
|---|---|
| `Ctrl+F` | Arama sayfasına odaklan |
| `Ctrl+R` | Yüklü paketleri yenile |
| `Esc` | Açık paneli kapat |

---

## 🖼️ Ekran Görüntüleri

> *(ekran görüntüleri eklenecek)*

---

## 🤝 Katkı

Pull request'ler ve issue'lar memnuniyetle karşılanır.

---

## 📄 Lisans

MIT