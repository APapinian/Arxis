<div align="center">

<img src="arxis_logo_256.png" alt="Arxis Logo" width="120" />

# Arxis

**Arch Linux için modern, grafik arayüzlü paket yöneticisi**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-41cd52?style=flat-square&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793d1?style=flat-square&logo=arch-linux&logoColor=white)](https://archlinux.org)
[![License](https://img.shields.io/badge/License-GPLv2-orange?style=flat-square)](LICENSE)

[Kurulum](#-kurulum) · [Özellikler](#-özellikler) · [Ekran Görüntüleri](#-ekran-görüntüleri) · [Geliştirme](#-geliştirme)

</div>

---

## ✨ Nedir?

Arxis; Pacman, AUR, Flatpak, AppImage ve Wine kaynaklarını **tek bir pencerede** birleştiren, PyQt6 ile yazılmış açık kaynaklı bir paket yöneticisidir. Arama, kurulum, kaldırma, güncelleme, snapshot ve çok daha fazlasını sezgisel bir arayüzle sunar.

---

## 📦 Paket Kaynakları

| Kaynak | Araç | Özellik |
|--------|------|---------|
| **Pacman** | `pacman` | Resmi Arch depoları |
| **AUR** | `yay` / `paru` | Topluluk paketleri |
| **Flatpak** | `flatpak` | Flathub entegrasyonu |
| **AppImage** | — | appimage.github.io + GitHub Releases |
| **Wine** | `wine` | Windows uygulamaları |

---

## 🚀 Kurulum

### Gereksinimler

```bash
# Zorunlu
sudo pacman -S python python-pyqt6

# Önerilen
sudo pacman -S expac flatpak fuse2
sudo pacman -S yay | veya sudo pacman -S paru
```

### Hızlı Kurulum

```bash
git clone https://github.com/fatih-bucaklioglu/arxis
cd arxis
chmod +x run.sh install.sh run.fish
./install.sh
```

`install.sh` şunları otomatik yapar:

- Python 3.11+ kontrolü
- `python -m venv venv` ile izole sanal ortam
- `pip install -r requirements.txt`
- Sistem araçlarını (yay, flatpak, expac) kontrol eder
- `run.sh` ve `run.fish` scriptlerini oluşturur

### Uygulamayı Başlatma

```bash
# Bash
./run.sh

# Fish shell
./run.fish

# Manuel
source venv/bin/activate   # bash
source venv/bin/activate.fish  # fish
python main.py
```

---

## 🎯 Özellikler

### Arayüz

- **Collapsible sidebar** — 64px ikon modu / 220px genişletilmiş mod
- **Canlı arama** — 300ms debounce ile anlık sonuçlar
- **Smooth animasyonlar** — NavItem, PackageItem hover efektleri
- **35 tema** — Arch Midnight'tan Pastel Cloud'a, ayarlardan anında değiştir
- **Sağ tık menüsü** — Kur · Kaldır · Detay · Karşılaştır · ★ Beğen · ⊕ Kuyruğa Ekle

### Sayfalar

| Sayfa | Açıklama |
|-------|----------|
| 🔍 **Keşfet** | Her açılışta farklı öneriler, güncellemeler |
| ✓ **Yüklü** | Tüm kurulu paketler, toplu kaldırma, filtreleme |
| ≡ **Kategoriler** | Oyun · Geliştirme · Ses · Grafik · Güvenlik ve daha fazlası |
| ★ **Beğenilenler** | Sağ tıkla eklenen paketler, JSON'da saklanır |
| ⊕ **Kuyruk** | Paketleri biriktir, "Tümünü Kur" ile toplu kur |
| ⊙ **Geçmiş** | Kurulum/kaldırma geçmişi, CSV dışa aktarma |
| ◫ **Snapshot** | Sistem profilini kaydet, diff karşılaştır, geri yükle |
| ⌥ **GitHub** | Repo URL veya doğrudan asset linki ile kur |
| ⚒ **Bakım** | Orphan paketler, önbellek temizleme, sistem güncelleme |
| ⚙ **Ayarlar** | Tema, kaynak toggle'ları, animasyon, bildirim |

### AppImage Desteği

```
1. appimage.github.io feed'i üzerinden arama
2. Feed'de link yoksa → GitHub API ile arama
3. GitHub Releases'den x86_64 .AppImage indir
4. ~/.local/share/AppImages/ içine kaydet
5. FUSE yoksa APPIMAGE_EXTRACT_AND_RUN=1 ile çalıştır
```

Detay sayfasında **🔗 GitHub URL ile Kur** butonu ile doğrudan GitHub reposu da verilebilir.

### Tema Sistemi

35 yerleşik tema — ayarlar sayfasının en altındaki grid'den seçin, değişiklik **anında** uygulanır ve kaydedilir.

<details>
<summary>Tüm temalar</summary>

| # | İsim | Zemin | Aksanlar |
|---|------|-------|---------|
| 01 | Arch Midnight *(varsayılan)* | `#070b14` | `#f97316` |
| 02 | Ocean Depth | `#060d1a` | `#f97316` |
| 03 | Terminal Green | `#0a0f0a` | `#00ff41` |
| 04 | Tokyo Night | `#1a1b2e` | `#ff007c` |
| 05 | Gruvbox Warm | `#282828` | `#fabd2f` |
| 06 | Catppuccin Mocha | `#1e1e2e` | `#cba6f7` |
| 07 | Nord Arctic | `#2e3440` | `#88c0d0` |
| 08 | Dracula Pro | `#22212c` | `#ff79c6` |
| 09 | Sahara Dusk | `#1a1208` | `#e8a020` |
| 10 | Cyberpunk 2077 | `#0d0d0f` | `#f5d800` |
| 11 | Everforest | `#1e2326` | `#a7c080` |
| 12 | Crimson Dark | `#0c0808` | `#cc0000` |
| 13 | Rosé Pine | `#191724` | `#ebbcba` |
| 14 | Monochrome | `#000000` | `#ffffff` |
| 15 | Ice Storm *(açık)* | `#dde6f0` | `#1d4ed8` |
| 16 | Volcanic | `#111111` | `#ff4500` |
| 17 | Bubble Gum | `#1a0e1a` | `#ff6eb4` |
| 18 | Arabian Night | `#0e0e1a` | `#d4af37` |
| 19 | Bioluminescent | `#000008` | `#00ffcc` |
| 20 | Game Boy | `#0f380f` | `#8bac0f` |
| 21 | Obsidian | `#080808` | `#c0c0c0` |
| 22 | Synthwave | `#120b1e` | `#ff2d78` |
| 23 | Matcha | `#0d1a0d` | `#6aaa64` |
| 24 | Fox Fire | `#0d0e1a` | `#ff6b2b` |
| 25 | Amulet | `#071520` | `#00b4d8` |
| 26 | Midnight Jazz | `#080508` | `#8b0000` |
| 27 | Matrix Redux | `#000300` | `#00ff41` |
| 28 | Blueberry | `#10081a` | `#6c63ff` |
| 29 | Coral Reef | `#060d1a` | `#ff6b6b` |
| 30 | Lantern Festival | `#0a0500` | `#e63946` |
| 31 | Pastel Cloud | `#f5f0ff` | `#7c3aed` |
| 32 | Pastel Peach | `#fff5f0` | `#ea580c` |
| 33 | Pastel Mint | `#f0faf4` | `#059669` |
| 34 | Pastel Rose | `#fff0f5` | `#db2777` |
| 35 | Pastel Sky | `#f0f8ff` | `#0284c7` |

</details>

---

## 📁 Dosya Yapısı

```
arxis/
├── main.py                  # Giriş noktası
├── install.sh               # Kurulum scripti
├── run.sh                   # Bash başlatma
├── run.fish                 # Fish shell başlatma
├── requirements.txt         # PyQt6, psutil
├── ui/
│   ├── main_window.py       # Arayüz (~4800 satır)
│   └── styles.py            # 35 tema + build_theme()
└── backend/
    ├── managers.py          # Paket yöneticileri (~1840 satır)
    └── system_monitor.py    # CPU/RAM/ağ izleme
```

### Yapılandırma Dosyaları

| Dosya | Açıklama |
|-------|----------|
| `~/.config/arxis/settings.json` | Tema, kaynak toggle'ları |
| `~/.config/arxis/favorites.json` | Beğenilen paketler |
| `~/.config/arxis/queue.json` | İndirme kuyruğu |
| `~/.local/share/arxis/history.json` | Kurulum geçmişi |
| `~/.local/share/AppImages/` | AppImage kurulum dizini |

---

## ⌨️ Kısayollar

| Kısayol | İşlev |
|---------|-------|
| `Ctrl+F` | Arama kutusuna odaklan |
| `Ctrl+R` | Yüklü paketleri yenile |
| `Çift tık` | Hızlı kur / kaldır |
| `Orta tık` | Hızlı kur / kaldır |
| `Sağ tık` | Context menü |
| `ESC` | Açık paneli kapat |

---

## 🛠 Geliştirme

```bash
git clone https://github.com/fatih-bucaklioglu/arxis
cd arxis
python -m venv venv
source venv/bin/activate   # fish: source venv/bin/activate.fish
pip install -r requirements.txt
python main.py
```

### Yeni Tema Eklemek

`ui/styles.py` dosyasındaki `THEMES` sözlüğüne ekleyin:

```python
"Tema Adı": {
    "bg":    "#zemin",
    "panel": "#panel",
    "ac":    "#aksanlar",
    "hi":    "#vurgular",
    "tx":    "#metin",
    "su":    "#ikincil_metin",
    "bdr":   "rgba(255,255,255,0.055)",
    # Açık tema ise:
    # "light": True,
},
```

---

## 📋 Gereksinimler

| Paket | Sürüm | Zorunlu |
|-------|-------|---------|
| Python | 3.11+ | ✓ |
| PyQt6 | 6.5+ | ✓ |
| psutil | 5.9+ | ✓ |
| expac | herhangi | Önerilen |
| yay / paru | herhangi | AUR için |
| flatpak | herhangi | Flatpak için |
| fuse2 | herhangi | AppImage için |

---

## 📜 Lisans

GPLv2 — Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

<div align="center">

**Arxis** · Arch Linux topluluğu için ❤️ ile yapıldı

[⬆ Başa Dön](#arxis)

</div>
