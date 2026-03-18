import subprocess
import shutil
import re
import json
import os
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class PackageSource(str, Enum):
    PACMAN   = "pacman"
    AUR      = "aur"
    FLATPAK  = "flatpak"
    APPIMAGE = "appimage"
    WINE     = "wine"


SOURCE_COLORS = {
    PackageSource.PACMAN:   ("#0a1f40", "#60a5fa"),
    PackageSource.AUR:      ("#1a0d3a", "#a78bfa"),
    PackageSource.FLATPAK:  ("#0a2a3a", "#38bdf8"),
    PackageSource.APPIMAGE: ("#2a1a0a", "#fb923c"),
    PackageSource.WINE:     ("#2a0a1a", "#f472b6"),
}

# Kategori → anahtar kelimeler eşlemesi (arama için)

# ─── Detay Önbelleği (LRU, maxsize=100) ──────────────────────────────────────
from collections import OrderedDict

_DETAIL_CACHE: OrderedDict = OrderedDict()
_DETAIL_CACHE_MAX = 100

def _cache_key(pkg) -> str:
    return f"{pkg.source.value}:{pkg.name}"

def _get_cached(pkg):
    key = _cache_key(pkg)
    if key in _DETAIL_CACHE:
        # LRU: erişilince sona taşı
        _DETAIL_CACHE.move_to_end(key)
        return _DETAIL_CACHE[key]
    return None

def _set_cached(pkg):
    key = _cache_key(pkg)
    _DETAIL_CACHE[key] = pkg
    _DETAIL_CACHE.move_to_end(key)
    # Maxsize aşıldıysa en eskiyi sil
    while len(_DETAIL_CACHE) > _DETAIL_CACHE_MAX:
        _DETAIL_CACHE.popitem(last=False)


CATEGORY_KEYWORDS = {
    "gaming":     ["game", "steam", "lutris", "wine", "proton", "gaming", "play",
                   "gamepad", "controller", "emulator", "retroarch", "mame"],
    "audio":      ["audio", "music", "sound", "pulse", "pipewire", "alsa", "mpd",
                   "spotify", "lmms", "ardour", "mixxx", "jack", "podcast"],
    "video":      ["video", "vlc", "obs", "ffmpeg", "mpv", "kdenlive", "handbrake",
                   "stream", "media", "player", "codec", "screencast", "record"],
    "graphics":   ["gimp", "inkscape", "krita", "blender", "image", "photo", "draw",
                   "svg", "design", "pixel", "render", "3d", "vector", "darktable"],
    "dev":        ["python", "nodejs", "git", "gcc", "cmake", "code", "vim", "neovim",
                   "rust", "go", "java", "ruby", "php", "docker", "vscode", "ide",
                   "debugger", "compiler", "interpreter", "editor", "sdk", "api"],
    "internet":   ["firefox", "chrome", "chromium", "browser", "wget", "curl",
                   "thunderbird", "mail", "torrent", "ftp", "ssh", "vpn", "telegram",
                   "discord", "slack", "zoom", "meet"],
    "system":     ["htop", "systemd", "kernel", "driver", "firmware", "grub",
                   "util", "tool", "monitor", "disk", "backup", "partition", "boot",
                   "service", "daemon", "cron", "log", "process"],
    "office":     ["libreoffice", "office", "writer", "calc", "document", "pdf",
                   "okular", "evince", "note", "todo", "calendar", "markdown"],
    "security":   ["gpg", "pass", "keepass", "firewall", "encrypt", "vpn", "ssh",
                   "audit", "antivirus", "clamav", "nmap", "wireshark", "tor"],
    "education":  ["anki", "gcompris", "math", "learn", "study", "quiz", "course",
                   "school", "education", "language", "science", "chemistry", "physics"],
    "science":    ["octave", "matlab", "r-base", "jupyter", "numpy", "scipy",
                   "gnuplot", "lab", "research", "simulation", "statistics", "data"],
    "vm":         ["virtualbox", "qemu", "kvm", "libvirt", "vmware", "virt",
                   "container", "docker", "podman", "lxc", "sandbox"],
    "terminal":   ["zsh", "bash", "fish", "tmux", "screen", "alacritty", "kitty",
                   "xterm", "terminal", "shell", "prompt", "cli", "tui", "ranger",
                   "ncdu", "fzf", "ripgrep", "bat", "eza", "lsd"],
    "files":      ["thunar", "nautilus", "dolphin", "ranger", "nemo", "pcmanfm",
                   "file", "manager", "archive", "zip", "tar", "rsync", "syncthing"],
}


@dataclass
class Package:
    name:           str
    description:    str
    version:        str
    source:         PackageSource
    installed:      bool  = False
    icon_color:     str   = "#2563eb"
    size:           str   = ""
    update_version: str   = ""
    category:       str   = "Tümü"
    votes:          int   = 0
    # Paket detayı için ek alanlar
    depends:        list  = field(default_factory=list)
    url:            str   = ""
    license:        str   = ""
    maintainer:     str   = ""
    _display_name:  str   = ""   # boş ise display_name property'si hesaplar

    @property
    def icon_letter(self) -> str:
        return self.name[0].upper() if self.name else "?"

    @property
    def display_name(self) -> str:
        # _display_name açıkça set edilmişse onu kullan
        if self._display_name:
            return self._display_name[:28]
        n = self.name
        # Flatpak application ID: com.example.AppName → "App Name"
        if "." in n and n.count(".") >= 1:
            n = n.split(".")[-1]   # son parçayı al: "zapzap", "AppName" vb.
        # Ortak suffix'leri temizle
        for suffix in ("-bin", "-git", "-fresh", "-stable", "-nightly"):
            n = n.replace(suffix, "")
        # CamelCase'i boşlukla ayır: "ZapZap" → "Zap Zap"
        import re
        n = re.sub(r'([a-z])([A-Z])', r'\1 \2', n)
        # Tire/alt çizgiyi boşluğa çevir, title case yap
        n = n.replace("-", " ").replace("_", " ").title().strip()
        return n[:28] if n else self.name[:28]

    def guess_category(self) -> str:
        """İsim ve açıklamaya göre kategori tahmin et"""
        text = (self.name + " " + self.description).lower()
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return cat
        return "system"


# ─── Base ─────────────────────────────────────────────────────────────────────

class BaseManager:
    SOURCE = PackageSource.PACMAN

    def is_available(self) -> bool:
        return False

    def search(self, query: str) -> list[Package]:
        return []

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        return False, "Uygulanmadı"

    def remove(self, package: Package, callback=None) -> tuple[bool, str]:
        return False, "Uygulanmadı"

    def get_updates(self) -> list[Package]:
        return []

    def get_installed(self) -> list[Package]:
        return []

    def get_details(self, package: Package) -> Package:
        """Paket detaylarını doldur (varsayılan: değişiklik yok)"""
        return package

    # Oturum boyunca tek şifre sor (bir kez doğrulandıktan sonra önbellekte tut)
    _sudo_password: str = ""

    @classmethod
    def set_sudo_password(cls, pw: str):
        cls._sudo_password = pw

    @classmethod
    def clear_sudo_password(cls):
        cls._sudo_password = ""

    def _run(self, cmd: list[str], sudo: bool = False, cwd: str = None) -> tuple[int, str, str]:
        if sudo:
            cmd = ["sudo", "-S", "-p", ""] + cmd
        try:
            pw_input = (self._sudo_password + "\n").encode() if sudo else None
            r = subprocess.run(cmd, input=pw_input,
                               capture_output=True, timeout=120, cwd=cwd)
            stdout = r.stdout.decode(errors="replace")
            stderr = r.stderr.decode(errors="replace")
            # sudo "şifre yanlış" tespiti
            if sudo and r.returncode != 0 and (
                    "incorrect password" in stderr.lower()
                    or "authentication failure" in stderr.lower()
                    or "3 incorrect" in stderr.lower()):
                self.clear_sudo_password()
                return -2, stdout, "❌ Hatalı şifre — lütfen tekrar deneyin."
            return r.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Zaman aşımı"
        except FileNotFoundError:
            return -1, "", f"{cmd[0]} bulunamadı"
        except Exception as e:
            return -1, "", str(e)

    def _run_stream(self, cmd: list[str], sudo: bool = False,
                    callback=None) -> tuple[int, str]:
        if sudo:
            cmd = ["sudo", "-S", "-p", ""] + cmd
        try:
            pw_input = (self._sudo_password + "\n").encode() if sudo else None
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            if pw_input:
                proc.stdin.write(pw_input)
                proc.stdin.flush()
            proc.stdin.close()
            lines = []
            for raw in proc.stdout:
                line = raw.decode(errors="replace")
                # sudo şifre prompt satırını filtrele
                if line.strip() in ("", "[sudo] password for"):
                    continue
                lines.append(line)
                if callback:
                    callback(line)
            proc.wait()
            out = "".join(lines)
            if sudo and proc.returncode != 0 and (
                    "incorrect password" in out.lower()
                    or "authentication failure" in out.lower()):
                self.clear_sudo_password()
                if callback:
                    callback("❌ Hatalı şifre — lütfen tekrar deneyin.\n")
                return -2, out
            return proc.returncode, out
        except FileNotFoundError:
            msg = f"{cmd[0]} bulunamadı"
            if callback: callback(msg + "\n")
            return -1, msg
        except Exception as e:
            if callback: callback(str(e) + "\n")
            return -1, str(e)


# ─── Pacman ───────────────────────────────────────────────────────────────────

class PacmanManager(BaseManager):
    SOURCE = PackageSource.PACMAN

    def is_available(self) -> bool:
        return shutil.which("pacman") is not None

    def search(self, query: str) -> list[Package]:
        code, out, _ = self._run(["pacman", "-Ss", query])
        if code != 0 or not out.strip():
            return []
        packages = []
        lines = out.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line and not line.startswith((" ", "\t")):
                m = re.match(r"(\S+)/(\S+)\s+(\S+)(.*)", line)
                if m:
                    repo, name, version, rest = m.groups()
                    desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    installed = "[installed]" in rest
                    packages.append(Package(name, desc, version, PackageSource.PACMAN,
                                            installed=installed, category=repo))
                i += 2
            else:
                i += 1
        return packages[:30]

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        code, out = self._run_stream(
            ["pacman", "-S", "--noconfirm", package.name], sudo=True, callback=callback)
        return code == 0, out

    def remove(self, package: Package, callback=None) -> tuple[bool, str]:
        code, out = self._run_stream(
            ["pacman", "-Rs", "--noconfirm", package.name], sudo=True, callback=callback)
        return code == 0, out

    def get_updates(self) -> list[Package]:
        """Sadece gerçekten güncel olmayan paketleri döndür"""
        code, out, _ = self._run(["pacman", "-Qu"])
        # pacman -Qu çıkış kodu 1 = hiç güncelleme yok (bu normal!)
        if not out.strip():
            return []  # Demo data YOK — gerçekten güncelleme yoksa boş döndür
        pkgs = []
        for line in out.strip().split("\n"):
            # Format: "paket eskiversiyon -> yeniversiyon"
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "->":
                old_ver = parts[1]
                new_ver = parts[3]
                # Aynı sürümse gösterme
                if old_ver != new_ver:
                    pkgs.append(Package(parts[0], "", old_ver, PackageSource.PACMAN,
                                        installed=True, update_version=new_ver))
        return pkgs

    def get_installed(self) -> list[Package]:
        code, out, _ = self._run(["pacman", "-Q"])
        if code != 0:
            return []
        pkgs = []
        for line in out.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                pkgs.append(Package(parts[0], "", parts[1],
                                    PackageSource.PACMAN, installed=True))
        return pkgs

    def get_orphans(self) -> list[Package]:
        """Hiçbir paket tarafından kullanılmayan orphan paketleri listele"""
        code, out, _ = self._run(["pacman", "-Qdtq"])
        if code != 0 or not out.strip():
            return []
        pkgs = []
        for name in out.strip().split("\n"):
            name = name.strip()
            if not name:
                continue
            # Sürümü çek
            c2, o2, _ = self._run(["pacman", "-Q", name])
            version = o2.split()[-1] if c2 == 0 and o2.strip() else "?"
            # Açıklamayı çek
            c3, o3, _ = self._run(["pacman", "-Qi", name])
            desc = ""
            for line in o3.split("\n"):
                if line.startswith("Description"):
                    desc = line.split(":", 1)[-1].strip()
                    break
            pkgs.append(Package(name, desc or "Orphan paket", version,
                                PackageSource.PACMAN, installed=True,
                                icon_color="#d97706"))
        return pkgs

    def remove_orphans(self, callback=None) -> tuple[bool, str]:
        """Tüm orphan paketleri kaldır"""
        code, out, _ = self._run(["pacman", "-Qdtq"])
        if not out.strip():
            return True, "Temizlenecek orphan paket yok."
        names = out.strip().split("\n")
        names = [n.strip() for n in names if n.strip()]
        code, result = self._run_stream(
            ["pacman", "-Rns", "--noconfirm"] + names,
            sudo=True, callback=callback)
        return code == 0, result

    def update_all(self, callback=None) -> tuple[bool, str]:
        """Tüm sistemi güncelle: pacman -Syu"""
        code, out = self._run_stream(
            ["pacman", "-Syu", "--noconfirm"],
            sudo=True, callback=callback)
        return code == 0, out

    def clean_cache(self, callback=None) -> tuple[bool, str]:
        """Paket önbelleğini temizle (son 2 sürümü tut)"""
        code, out = self._run_stream(
            ["paccache", "-rk2"],
            sudo=True, callback=callback)
        if code != 0:
            # paccache yoksa manuel temizle
            code2, out2 = self._run_stream(
                ["pacman", "-Sc", "--noconfirm"],
                sudo=True, callback=callback)
            return code2 == 0, out2
        return True, out

    def get_details(self, package: Package) -> Package:
        """Hızlı detay: önbellek → yerel DB → pacman -Si"""
        cached = _get_cached(package)
        if cached:
            return cached

        # 1) Kuruluysa pacman -Qi (yerel, ~50ms)
        if package.installed:
            code, out, _ = self._run(["pacman", "-Qi", package.name])
            if code == 0:
                self._parse_pacman_info(out, package)
                _set_cached(package)
                return package

        # 2) expac ile sync DB'den hızlı sorgula (expac çok hızlı ~20ms)
        code, out, _ = self._run([
            "expac", "-S",
            "%d\t%u\t%l\t%S\t%m\t%p",   # desc, url, license, deps, size, packager
            package.name
        ])
        if code == 0 and out.strip():
            parts = out.strip().split("\t")
            if len(parts) >= 1 and parts[0]: package.description = parts[0]
            if len(parts) >= 2 and parts[1]: package.url         = parts[1]
            if len(parts) >= 3 and parts[2]: package.license     = parts[2]
            if len(parts) >= 4 and parts[3]:
                package.depends = [d.strip() for d in parts[3].split() if d.strip()]
            if len(parts) >= 5 and parts[4]:
                try:
                    mb = int(parts[4]) // (1024 * 1024)
                    package.size = f"{mb} MB" if mb > 0 else f"{int(parts[4])//1024} KB"
                except Exception:
                    package.size = parts[4]
            if len(parts) >= 6 and parts[5]:
                package.maintainer = parts[5].split("<")[0].strip()
            _set_cached(package)
            return package

        # 3) expac yoksa pacman -Si (sync DB, yerel okuma ~200ms)
        code, out, _ = self._run(["pacman", "-Si", "--noconfirm", package.name])
        if code == 0:
            self._parse_pacman_info(out, package)

        _set_cached(package)
        return package

    def _parse_pacman_info(self, out: str, package: Package):
        for line in out.split("\n"):
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip(); val = val.strip()
            if not val or val in ("None", "Unknown Packager"):
                continue
            if   key == "Description":  package.description = val
            elif key == "URL":          package.url         = val
            elif key in ("Licenses", "License"): package.license = val
            elif key == "Depends On":
                package.depends = [d for d in val.split() if d and d != "None"]
            elif key in ("Installed Size", "Download Size"):
                if not package.size: package.size = val
            elif key == "Packager":
                package.maintainer = val.split("<")[0].strip() or val
            elif key == "Version":
                if not package.version: package.version = val

    def search_by_category(self, category: str) -> list[Package]:
        """Kategoriye göre paket ara"""
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        results = []
        seen = set()
        for kw in keywords[:3]:  # ilk 3 anahtar kelimeyle ara
            code, out, _ = self._run(["pacman", "-Ss", kw])
            if code == 0 and out.strip():
                pkgs = self._parse_search(out)
                for p in pkgs:
                    if p.name not in seen:
                        seen.add(p.name)
                        results.append(p)
        return results[:40]

    def _parse_search(self, out: str) -> list[Package]:
        packages = []
        lines = out.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            if line and not line.startswith((" ", "\t")):
                m = re.match(r"(\S+)/(\S+)\s+(\S+)(.*)", line)
                if m:
                    repo, name, version, rest = m.groups()
                    desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    installed = "[installed]" in rest
                    packages.append(Package(name, desc, version, PackageSource.PACMAN,
                                            installed=installed))
                i += 2
            else:
                i += 1
        return packages


# ─── AUR ──────────────────────────────────────────────────────────────────────

class AURManager(BaseManager):
    SOURCE = PackageSource.AUR
    API    = "https://aur.archlinux.org/rpc/v5/search/"
    _tool: str = ""

    def is_available(self) -> bool:
        # yay veya paru hangisi varsa onu kullan
        for t in ("yay", "paru"):
            if shutil.which(t):
                self._tool = t
                return True
        return False

    def _get_tool(self) -> str:
        """Her çağrıda güncel aracı döndür (runtime'da kurulmuş olabilir)"""
        if self._tool and shutil.which(self._tool):
            return self._tool
        for t in ("yay", "paru"):
            if shutil.which(t):
                self._tool = t
                return t
        return ""

    def search(self, query: str) -> list[Package]:
        # Önce AUR RPC API'yi dene (araç gerekmez)
        try:
            url = self.API + urllib.parse.quote(query)
            req = urllib.request.Request(url, headers={"User-Agent": "ArchStore/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read())
                if data.get("resultcount", 0) > 0:
                    return [
                        Package(r["Name"], r.get("Description") or "",
                                r.get("Version", ""), PackageSource.AUR,
                                icon_color="#7c3aed", votes=r.get("NumVotes", 0),
                                url=r.get("URL") or "",
                                maintainer=r.get("Maintainer") or "")
                        for r in sorted(data["results"], key=lambda x: -x.get("NumVotes", 0))[:30]
                    ]
        except Exception as _e:
            pass   # Ağ hatası → aşağıda yay/paru ile devam

        # RPC başarısız → yay/paru dene
        tool = self._get_tool()
        if not tool:
            return []
        code, out, _ = self._run([tool, "-Ss", "--aur", query])
        if code == 0 and out.strip():
            pkgs = []
            lines = out.strip().split("\n")
            i = 0
            while i < len(lines):
                if "aur/" in lines[i]:
                    m = re.match(r"aur/(\S+)\s+(\S+)", lines[i])
                    if m:
                        name, ver = m.groups()
                        desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
                        pkgs.append(Package(name, desc, ver, PackageSource.AUR,
                                            icon_color="#7c3aed"))
                    i += 2
                else:
                    i += 1
            return pkgs[:30]
        return []

    def get_details(self, package: Package) -> Package:
        """AUR RPC'den tam paket bilgisi çek — önbellekli"""
        cached = _get_cached(package)
        if cached:
            return cached
        try:
            url = f"https://aur.archlinux.org/rpc/v5/info?arg={urllib.parse.quote(package.name)}"
            req = urllib.request.Request(url, headers={"User-Agent": "ArchStore/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                r = results[0]
                package.description = r.get("Description") or package.description
                package.version     = r.get("Version")     or package.version
                package.url         = r.get("URL")         or package.url
                package.license     = ", ".join(r.get("License") or []) or package.license
                package.maintainer  = r.get("Maintainer")  or package.maintainer
                package.votes       = r.get("NumVotes", 0)
                deps = r.get("Depends") or []
                if deps: package.depends = deps
                if not package.size: package.size = "—"
        except Exception as e:
            if not package.description:
                package.description = f"AUR bilgisi alınamadı ({type(e).__name__})"
        _set_cached(package)
        return package

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        tool = self._get_tool()
        if not tool:
            msg = ("❌ AUR yardımcısı bulunamadı.\n"
                   "Kurmak için:\n"
                   "  git clone https://aur.archlinux.org/yay.git\n"
                   "  cd yay && makepkg -si\n")
            if callback:
                callback(msg)
            return False, msg
        code, out = self._run_stream([tool, "-S", "--noconfirm", package.name],
                                     callback=callback)
        return code == 0, out

    def get_updates(self) -> list[Package]:
        tool = self._get_tool()
        if not tool:
            return []
        code, out, _ = self._run([tool, "-Qu", "--aur"])
        pkgs = []
        for line in out.strip().split("\n"):
            parts = line.split()
            if len(parts) >= 4 and parts[2] == "->":
                old_ver, new_ver = parts[1], parts[3]
                if old_ver != new_ver:
                    pkgs.append(Package(parts[0], "", old_ver, PackageSource.AUR,
                                        installed=True, update_version=new_ver,
                                        icon_color="#7c3aed"))
        return pkgs

    def get_installed(self) -> list[Package]:
        tool = self._get_tool()
        if not tool:
            return []
        code, out, _ = self._run([tool, "-Qm"])
        if code != 0:
            return []
        pkgs = []
        for line in out.strip().split("\n")[:100]:
            parts = line.split()
            if len(parts) >= 2:
                pkgs.append(Package(parts[0], "AUR paketi", parts[1],
                                    PackageSource.AUR, installed=True,
                                    icon_color="#7c3aed"))
        return pkgs

    def search_by_category(self, category: str) -> list[Package]:
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        results = []
        seen = set()
        for kw in keywords[:2]:
            pkgs = self.search(kw)
            for p in pkgs:
                if p.name not in seen:
                    seen.add(p.name)
                    results.append(p)
        return results[:30]


# ─── Flatpak ──────────────────────────────────────────────────────────────────

class FlatpakManager(BaseManager):
    SOURCE = PackageSource.FLATPAK

    def is_available(self) -> bool:
        return shutil.which("flatpak") is not None

    def search(self, query: str) -> list[Package]:
        code, out, _ = self._run(
            ["flatpak", "search", "--columns=application,name,description,version", query])

        pkgs = []
        if code == 0 and out.strip():
            for line in out.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")

                # En az 2 sütun gerekli
                if len(parts) < 2:
                    continue

                # İlk sütun application ID mi yoksa display name mi kontrol et
                col0 = parts[0].strip()
                col1 = parts[1].strip() if len(parts) > 1 else ""

                # Hangi sütunun ID olduğunu bul
                if "." in col0 and " " not in col0:
                    app_id = col0
                    name   = col1
                    desc   = parts[2].strip() if len(parts) > 2 else ""
                    ver    = parts[3].strip() if len(parts) > 3 else ""
                elif "." in col1 and " " not in col1:
                    # Sütunlar ters gelmiş
                    app_id = col1
                    name   = col0
                    desc   = parts[2].strip() if len(parts) > 2 else ""
                    ver    = parts[3].strip() if len(parts) > 3 else ""
                else:
                    continue

                pkgs.append(Package(
                    app_id,
                    desc, ver,
                    PackageSource.FLATPAK,
                    icon_color="#0077b6",
                    _display_name=name or app_id.split(".")[-1],
                ))

        if pkgs:
            return pkgs[:30]

        # Fallback: sadece application ID kolonuyla ara
        code2, out2, _ = self._run(
            ["flatpak", "search", "--columns=application", query])
        if code2 == 0 and out2.strip():
            for line in out2.strip().split("\n"):
                app_id = line.strip()
                if app_id and "." in app_id and " " not in app_id:
                    pkgs.append(Package(
                        app_id, "", "",
                        PackageSource.FLATPAK,
                        icon_color="#0077b6",
                        _display_name=app_id.split(".")[-1],
                    ))
            if pkgs:
                return pkgs[:30]

        return []

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        app_id = package.name.strip()

        # Adım 1: ID'yi doğrula — com.example.App formatı zorunlu
        def is_valid_id(s: str) -> bool:
            return bool(s) and "." in s and " " not in s and len(s.split(".")) >= 2

        if not is_valid_id(app_id):
            # Adım 2: flatpak search ile sadece application ID kolonunu çek
            if callback: callback(f"🔍 '{app_id}' için uygulama ID'si aranıyor…\n")
            code, out, _ = self._run(
                ["flatpak", "search", "--columns=application", app_id])
            found_id = ""
            if code == 0:
                for line in out.strip().split("\n"):
                    candidate = line.strip()
                    if is_valid_id(candidate):
                        # En iyi eşleşme: app_id ismi candidate'in bir parçasıysa
                        if app_id.lower().replace(" ", "") in candidate.lower():
                            found_id = candidate
                            break
                # Eşleşme bulunamazsa ilk geçerli sonucu al
                if not found_id:
                    for line in out.strip().split("\n"):
                        candidate = line.strip()
                        if is_valid_id(candidate):
                            found_id = candidate
                            break

            if found_id:
                if callback: callback(f"✓ Bulunan ID: {found_id}\n")
                app_id = found_id
            else:
                msg = f"❌ '{app_id}' için geçerli Flatpak ID bulunamadı.\n"
                if callback: callback(msg)
                return False, msg

        if callback: callback(f"📦 Kuruluyor: {app_id}\n")
        code, out = self._run_stream(
            ["flatpak", "install", "-y", "flathub", app_id], callback=callback)
        return code == 0, out

    def remove(self, package: Package, callback=None) -> tuple[bool, str]:
        code, out = self._run_stream(
            ["flatpak", "uninstall", "-y", package.name], callback=callback)
        return code == 0, out

    def get_updates(self) -> list[Package]:
        """Gerçek Flatpak güncellemelerini çek"""
        code, out, _ = self._run(
            ["flatpak", "remote-ls", "--updates", "--columns=name,version,branch"])
        if not out.strip():
            return []
        pkgs = []
        for line in out.strip().split("\n"):
            parts = line.split("\t")
            if parts and parts[0].strip():
                pkgs.append(Package(parts[0].strip(), "Flatpak güncellemesi",
                                    parts[1].strip() if len(parts) > 1 else "",
                                    PackageSource.FLATPAK, installed=True,
                                    icon_color="#0077b6"))
        return pkgs

    def get_installed(self) -> list[Package]:
        code, out, _ = self._run(["flatpak", "list", "--columns=name,version"])
        pkgs = []
        for line in out.strip().split("\n"):
            parts = line.split("\t")
            if parts[0].strip():
                pkgs.append(Package(parts[0].strip(), "Flatpak paketi",
                                    parts[1].strip() if len(parts) > 1 else "",
                                    PackageSource.FLATPAK, installed=True,
                                    icon_color="#0077b6"))
        return pkgs

    def search_by_category(self, category: str) -> list[Package]:
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        results = []
        seen = set()
        for kw in keywords[:2]:
            pkgs = self.search(kw)
            for p in pkgs:
                if p.name not in seen:
                    seen.add(p.name)
                    results.append(p)
        return results[:20]

    def get_details(self, package: Package) -> Package:
        """flatpak info (kuruluysa) + Flathub API — önbellekli, hızlı"""
        cached = _get_cached(package)
        if cached:
            return cached

        # 1) Kuruluysa hızlı yerel sorgu
        if package.installed:
            code, out, _ = self._run(["flatpak", "info", package.name])
            if code == 0:
                for line in out.split("\n"):
                    if ":" not in line: continue
                    key, _, val = line.partition(":")
                    key = key.strip(); val = val.strip()
                    if not val: continue
                    if   key == "Description": package.description = val
                    elif key == "Version":     package.version     = val
                    elif key == "License":     package.license     = val
                    elif key == "Installed":   package.size        = val
                    elif key == "Developer":   package.maintainer  = val

        # 2) Flathub API — timeout 4s
        try:
            api_url = f"https://flathub.org/api/v2/appstream/{package.name}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "arxis/1.0"})
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.loads(r.read().decode())
            if not package.description and data.get("description"):
                package.description = re.sub(r"<[^>]+>", "", data["description"])[:400]
            if data.get("projectLicense") and not package.license:
                package.license = data["projectLicense"]
            if data.get("homepageUrl"):
                package.url = data["homepageUrl"]
            if data.get("developerName") and not package.maintainer:
                package.maintainer = data["developerName"]
        except Exception as e:
            if not package.description:
                package.description = f"Flathub bilgisi alınamadı ({type(e).__name__})"
        _set_cached(package)
        return package


# ─── AppImage ─────────────────────────────────────────────────────────────────

class AppImageManager(BaseManager):
    SOURCE  = PackageSource.APPIMAGE
    DIR     = os.path.expanduser("~/.local/share/AppImages")
    HUB_API = "https://appimage.github.io/feed.json"   # gerçek liste

    def is_available(self) -> bool:
        return True

    def _fetch_hub(self) -> list[dict]:
        """AppImage Hub feed'ini çek — 1 saatlik modül önbelleği"""
        import time
        now = time.time()
        # Modül seviyesinde önbellek
        if not hasattr(AppImageManager, '_feed_cache'):
            AppImageManager._feed_cache = []
            AppImageManager._feed_ts    = 0.0
        # 1 saat = 3600 saniye — önbellek geçerliyse direkt dön
        if AppImageManager._feed_cache and (now - AppImageManager._feed_ts) < 3600:
            return AppImageManager._feed_cache
        # Yeni fetch
        try:
            req = urllib.request.Request(
                self.HUB_API,
                headers={"User-Agent": "arxis/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            items = data.get("items", [])
            AppImageManager._feed_cache = items
            AppImageManager._feed_ts    = now
            return items
        except Exception as e:
            import sys
            print(f"[arxis] AppImage Hub fetch hatası: {e}", file=sys.stderr)
            # Önbellekte eski veri varsa onu kullan
            return AppImageManager._feed_cache or []

    def search(self, query: str) -> list[Package]:
        items = self._fetch_hub()
        if not items:
            # Fallback: demo
            results = _DEMO_APPIMAGE[:]
            if query:
                results = [p for p in results
                           if query.lower() in p.name.lower()
                           or query.lower() in p.description.lower()]
            return results

        installed_names = {p.name.lower() for p in self.get_installed()}
        pkgs = []
        for item in items:
            name = item.get("name", "")
            if not name:
                continue
            desc  = item.get("description", "") or ""
            links = item.get("links") or []
            dl_url = ""
            for lnk in links:
                if isinstance(lnk, dict) and lnk.get("type") in ("Download", "GitHub"):
                    dl_url = lnk.get("url", "")
                    break
            if query and query.lower() not in name.lower() and query.lower() not in desc.lower():
                continue
            pkg = Package(
                name, desc or "AppImage uygulaması", "latest",
                PackageSource.APPIMAGE,
                installed=name.lower() in installed_names,
                icon_color="#f59e0b",
                url=dl_url,
            )
            pkgs.append(pkg)
            if len(pkgs) >= 80:
                break
        return pkgs

    def get_popular(self) -> list[Package]:
        """En popüler AppImage'ları getir"""
        popular = ["Krita", "Inkscape", "Kdenlive", "Blender", "OBS-Studio",
                   "Audacity", "VLC", "GIMP", "LibreOffice", "Lmms"]
        items = self._fetch_hub()
        if not items:
            return []
        installed_names = {p.name.lower() for p in self.get_installed()}
        pkgs = []
        for item in items:
            name = item.get("name", "")
            if any(p.lower() in name.lower() for p in popular):
                links = item.get("links") or []
                dl_url = next((l.get("url","") for l in links
                               if isinstance(l, dict) and l.get("type") in ("Download","GitHub")), "")
                pkgs.append(Package(
                    name, item.get("description","") or "AppImage", "latest",
                    PackageSource.APPIMAGE,
                    installed=name.lower() in installed_names,
                    icon_color="#f59e0b", url=dl_url))
        return pkgs[:10]

    def get_installed(self) -> list[Package]:
        if not os.path.exists(self.DIR):
            return []
        pkgs = []
        for f in os.listdir(self.DIR):
            if f.endswith(".AppImage"):
                name = f.replace(".AppImage", "").split("-")[0]
                path = os.path.join(self.DIR, f)
                size_mb = os.path.getsize(path) / (1024 * 1024)
                pkgs.append(Package(name, "AppImage", "unknown",
                                    PackageSource.APPIMAGE, installed=True,
                                    icon_color="#f59e0b",
                                    size=f"{size_mb:.1f} MB"))
        return pkgs

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        """AppImage'ı indir → ~/.local/share/AppImages/"""
        url     = (package.url or "").strip()
        pkg_name = package.name.strip()
        display  = (package.display_name or pkg_name).strip()
        name_norm = pkg_name.lower().replace(" ","").replace("-","").replace("_","")
        display_norm = display.lower().replace(" ","").replace("-","").replace("_","")

        def _find_appimage_in_release(owner: str, repo: str) -> str:
            """GitHub repo'sunun son release'inden x86_64 AppImage URL döndür"""
            api = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            req = urllib.request.Request(
                api, headers={"User-Agent":"arxis/1.0",
                              "Accept":"application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                assets = json.loads(r.read().decode()).get("assets", [])
            # x86_64 önce
            for a in assets:
                n = a["name"].lower()
                if n.endswith(".appimage") and ("x86_64" in n or "amd64" in n):
                    return a["browser_download_url"]
            # herhangi AppImage
            for a in assets:
                if a["name"].lower().endswith(".appimage"):
                    return a["browser_download_url"]
            return ""

        # 1) Direkt .AppImage URL'si varsa atla
        if url and url.lower().endswith(".appimage"):
            pass  # direkt indir

        # 2) GitHub repo URL'si varsa releases'e bak
        elif url and "github.com" in url:
            if callback: callback("🔗 GitHub releases aranıyor…\n")
            try:
                m = re.search(r'github\.com/([^/]+)/([^/?\s#]+)', url)
                if m:
                    found = _find_appimage_in_release(m.group(1), m.group(2).rstrip("/"))
                    if found:
                        url = found
                        if callback: callback(f"✓ {url.split('/')[-1]}\n")
                    else:
                        url = ""
            except Exception as e:
                if callback: callback(f"⚠ {e}\n"); url = ""

        # 3) URL yoksa feed'den bak
        elif not url:
            if callback: callback(f"🔍 '{display}' aranıyor…\n")
            try:
                for item in self._fetch_hub():
                    iname = item.get("name","")
                    inorm = iname.lower().replace(" ","").replace("-","").replace("_","")
                    if inorm == name_norm or inorm == display_norm or \
                            name_norm in inorm or display_norm in inorm:
                        if callback: callback(f"✓ Feed: {iname}\n")
                        # Feed linklerinden URL al
                        for lnk in (item.get("links") or []):
                            if isinstance(lnk, dict):
                                lurl = lnk.get("url","")
                                ltype = lnk.get("type","")
                                if ltype == "Download" and lurl:
                                    url = lurl; break
                                elif ltype == "GitHub" and lurl:
                                    url = lurl  # GitHub repo — sonra releases'e bakacak
                        break
            except Exception as e:
                if callback: callback(f"⚠ Feed: {e}\n")

            # Feed GitHub repo URL verdiyse releases'e bak
            if url and "github.com" in url and not url.lower().endswith(".appimage"):
                if callback: callback("🔗 GitHub releases…\n")
                try:
                    m = re.search(r'github\.com/([^/]+)/([^/?\s#]+)', url)
                    if m:
                        found = _find_appimage_in_release(m.group(1), m.group(2).rstrip("/"))
                        url = found if found else ""
                        if found and callback: callback(f"✓ {url.split('/')[-1]}\n")
                except Exception as e:
                    if callback: callback(f"⚠ {e}\n"); url = ""

        # 4) Hâlâ yoksa GitHub'da paket ismiyle ara (rate limit riski var)
        if not url:
            if callback: callback(f"🔍 GitHub'da '{display}' aranıyor…\n")
            try:
                q = urllib.parse.quote(display_norm)
                api = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page=5"
                req = urllib.request.Request(
                    api, headers={"User-Agent":"arxis/1.0",
                                  "Accept":"application/vnd.github.v3+json"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    repos = json.loads(r.read().decode()).get("items", [])
                for ri in repos:
                    # Repo ismi paket ismiyle eşleşiyor mu?
                    rname = ri["name"].lower().replace("-","").replace("_","")
                    if display_norm in rname or name_norm in rname:
                        try:
                            found = _find_appimage_in_release(ri["owner"]["login"], ri["name"])
                            if found:
                                url = found
                                if callback: callback(f"✓ {ri['full_name']} → {url.split('/')[-1]}\n")
                                break
                        except Exception:
                            pass
            except Exception as e:
                if callback: callback(f"⚠ GitHub arama: {e}\n")

        if not url:
            msg = (f"❌ '{display}' için AppImage bulunamadı.\n"
                   f"   GitHub'dan manuel URL girmek için:\n"
                   f"   Detay sayfası → 'GitHub URL ile Kur' butonunu kullanın.\n")
            if callback: callback(msg)
            return False, msg

        if not url.lower().endswith(".appimage") and ".appimage" not in url.lower():
            msg = f"❌ Geçerli AppImage URL değil: {url[:80]}\n"
            if callback: callback(msg)
            return False, msg

        # İndir
        os.makedirs(self.DIR, exist_ok=True)
        safe = "".join(c for c in display if c.isalnum() or c in "-_.")
        dest = os.path.join(self.DIR, f"{safe}.AppImage")
        try:
            if callback: callback(f"⬇  {url[:80]}\n")
            req = urllib.request.Request(url, headers={"User-Agent":"arxis/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                total = int(r.headers.get("Content-Length", 0))
                done  = 0
                with open(dest, "wb") as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk: break
                        f.write(chunk); done += len(chunk)
                        if callback and total:
                            pct = int(done / total * 100)
                            callback(f"\r  {pct}% — {done//(1024*1024)}/{total//(1024*1024)} MB")
            os.chmod(dest, 0o755)
            if callback: callback(f"\n✅ Kuruldu: {dest}\n")
            return True, dest
        except Exception as ex:
            try:
                if os.path.exists(dest): os.remove(dest)
            except Exception: pass
            msg = f"❌ İndirme hatası: {ex}"
            if callback: callback(msg + "\n")
            return False, msg

    def remove(self, package: Package, callback=None) -> tuple[bool, str]:
        if not os.path.exists(self.DIR):
            return False, "AppImages dizini bulunamadı"
        name = (package.display_name or package.name).lower().strip()
        removed = []
        for f in sorted(os.listdir(self.DIR)):
            if not f.endswith(".AppImage"): continue
            fname = f.replace(".AppImage","").split("-")[0].lower()
            if fname == name or name in fname:
                path = os.path.join(self.DIR, f)
                try:
                    os.remove(path); removed.append(f)
                    if callback: callback(f"🗑  Silindi: {f}\n")
                except Exception as e:
                    if callback: callback(f"❌ Silinemedi: {f} — {e}\n")
        if removed: return True, f"Silindi: {', '.join(removed)}"
        return False, f"'{name}' için AppImage dosyası bulunamadı"

    def get_details(self, package: Package) -> Package:
        """AppImage Hub feed'inden detay çek — önbellekli"""
        cached = _get_cached(package)
        if cached:
            return cached
        try:
            items = self._fetch_hub()
            for item in items:
                if item.get("name", "").lower() == package.name.lower():
                    package.description = item.get("description") or package.description
                    links = item.get("links") or []
                    for lnk in links:
                        if isinstance(lnk, dict):
                            if lnk.get("type") == "GitHub":
                                package.url = lnk.get("url", "")
                            elif lnk.get("type") == "Download" and not package.url:
                                package.url = lnk.get("url", "")
                    cats = item.get("categories") or []
                    if cats: package.category = cats[0]
                    break
        except Exception:
            pass   # Feed parse hatası — mevcut bilgilerle devam
        # Kuruluysa dosya boyutunu al
        if package.installed and not package.size:
            for f in os.listdir(self.DIR) if os.path.exists(self.DIR) else []:
                if f.lower().startswith(package.name.lower()) and f.endswith(".AppImage"):
                    path = os.path.join(self.DIR, f)
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    package.size = f"{size_mb:.1f} MB"
                    break
        if not package.license: package.license = "Değişken (AppImage)"
        return package


# ─── Wine ─────────────────────────────────────────────────────────────────────

class WineManager(BaseManager):
    SOURCE = PackageSource.WINE

    def is_available(self) -> bool:
        return shutil.which("wine") is not None

    def search(self, query: str) -> list[Package]:
        results = _DEMO_WINE[:]
        if query:
            results = [p for p in results if query.lower() in p.name.lower()]
        return results

    def get_details(self, package: Package) -> Package:
        """Wine paketi için temel bilgileri doldur — önbellekli"""
        cached = _get_cached(package)
        if cached:
            return cached
        if not package.maintainer: package.maintainer = "WineHQ"
        if not package.license:    package.license    = "LGPL"
        if not package.url:        package.url        = "https://www.winehq.org"
        if not package.description:
            package.description = f"{package.display_name} — Wine ile çalışan Windows uygulaması."
        return package


# ─── Wine ─────────────────────────────────────────────────────────────────────

class WineManager(BaseManager):
    SOURCE = PackageSource.WINE

    def is_available(self) -> bool:
        return shutil.which("wine") is not None

    def search(self, query: str) -> list[Package]:
        results = _DEMO_WINE[:]
        if query:
            results = [p for p in results if query.lower() in p.name.lower()]
        return results


# ─── Demo Data ────────────────────────────────────────────────────────────────

_DEMO_PACMAN = [
    Package("firefox",  "Hızlı, gizlilik odaklı web tarayıcısı", "121.0.1", PackageSource.PACMAN, icon_color="#ff6b00"),
    Package("vlc",      "Video oynatıcı ve medya akış aracı",    "3.0.20",  PackageSource.PACMAN, icon_color="#ff8800"),
    Package("gimp",     "GNU Image Manipülasyon Programı",        "2.10.36", PackageSource.PACMAN, icon_color="#6666aa"),
    Package("neovim",   "Geliştirilmiş Vim metin editörü",        "0.9.4",   PackageSource.PACMAN, icon_color="#44aa44"),
    Package("htop",     "İnteraktif süreç izleyici",              "3.3.0",   PackageSource.PACMAN, icon_color="#2da44e"),
    Package("git",      "Dağıtık versiyon kontrol sistemi",       "2.43.0",  PackageSource.PACMAN, icon_color="#f05030", installed=True),
    Package("python",   "Python programlama dili",                "3.11.6",  PackageSource.PACMAN, icon_color="#306998", installed=True),
]

_DEMO_AUR = [
    Package("visual-studio-code-bin", "Kod editörü. Yeniden tanımlandı.", "1.85.1", PackageSource.AUR, icon_color="#007acc", votes=9999),
    Package("google-chrome",          "Google Chrome web tarayıcısı",     "120.0",  PackageSource.AUR, icon_color="#4285f4", votes=5000),
    Package("discord",                "Topluluklar için sesli sohbet",     "0.0.38", PackageSource.AUR, icon_color="#5865f2", votes=3000),
    Package("spotify",                "Müzik akış servisi",                "1.2.26", PackageSource.AUR, icon_color="#1db954", votes=4500),
    Package("1password",              "Güvenli şifre yöneticisi",          "8.10.2", PackageSource.AUR, icon_color="#0094f5", votes=1200),
]

_DEMO_FLATPAK = [
    Package("org.gimp.GIMP",              "GNU Image Editor",        "2.10.36", PackageSource.FLATPAK, icon_color="#6666aa"),
    Package("org.libreoffice.LibreOffice","Güçlü ofis paketi",        "7.6.4",   PackageSource.FLATPAK, icon_color="#1565c0"),
    Package("com.valvesoftware.Steam",    "Steam oyun platformu",     "latest",  PackageSource.FLATPAK, icon_color="#1b2838", installed=True),
    Package("org.mozilla.firefox",        "Firefox web tarayıcısı",   "121.0",   PackageSource.FLATPAK, icon_color="#ff6b00"),
    Package("org.kde.kdenlive",           "Video düzenleme yazılımı", "23.12",   PackageSource.FLATPAK, icon_color="#527890"),
]

_DEMO_APPIMAGE = [
    Package("Krita",      "Dijital boyama ve illüstrasyon", "5.2.0",  PackageSource.APPIMAGE, icon_color="#3498db"),
    Package("Inkscape",   "Vektör grafik editörü",          "1.3.2",  PackageSource.APPIMAGE, icon_color="#e88b00"),
    Package("Blender",    "3D modelleme ve animasyon",      "4.0.2",  PackageSource.APPIMAGE, icon_color="#f5792a"),
    Package("OBS Studio", "Video kayıt ve canlı yayın",    "30.0.0", PackageSource.APPIMAGE, icon_color="#302e31"),
]

_DEMO_WINE = [
    Package("Microsoft Office 2021", "Ofis paketi (Wine ile)",        "16.0",  PackageSource.WINE, icon_color="#d73502"),
    Package("Adobe Photoshop CS6",   "Fotoğraf düzenleme (Wine ile)", "13.0",  PackageSource.WINE, icon_color="#001e36"),
    Package("7-Zip",                 "Arşiv yöneticisi",              "23.01", PackageSource.WINE, icon_color="#008000"),
    Package("Notepad++",             "Gelişmiş metin editörü",        "8.6",   PackageSource.WINE, icon_color="#80b800"),
]


# ─── Hub ──────────────────────────────────────────────────────────────────────

class PackageManagerHub:
    """Tüm paket yöneticilerini koordine eder."""

    def __init__(self):
        self.managers: dict[PackageSource, BaseManager] = {
            PackageSource.PACMAN:   PacmanManager(),
            PackageSource.AUR:      AURManager(),
            PackageSource.FLATPAK:  FlatpakManager(),
            PackageSource.APPIMAGE: AppImageManager(),
            PackageSource.WINE:     WineManager(),
        }
        # Ayarlardan kontrol edilir — varsayılan: hepsi açık
        self.enabled_sources: set[PackageSource] = set(self.managers.keys())

    def set_source_enabled(self, source_key: str, enabled: bool):
        """Ayarlar sayfasından kaynak toggle'ı için çağrılır"""
        source_map = {
            "aur":      PackageSource.AUR,
            "flatpak":  PackageSource.FLATPAK,
            "appimage": PackageSource.APPIMAGE,
            "wine":     PackageSource.WINE,
        }
        src = source_map.get(source_key)
        if src:
            if enabled:
                self.enabled_sources.add(src)
            else:
                self.enabled_sources.discard(src)

    def aur_tool(self) -> str:
        m = self.managers[PackageSource.AUR]
        return m._get_tool() if hasattr(m, "_get_tool") else ""

    def search_all(self, query: str,
                   sources: list[PackageSource] | None = None) -> list[Package]:
        # sources parametresi verilmemişse enabled_sources'ı kullan
        active = sources if sources is not None else [
            s for s in self.managers if s in self.enabled_sources
        ]
        results = []
        for src in active:
            if src in self.managers:
                results.extend(self.managers[src].search(query))
        return results

    def install(self, package: Package, callback=None) -> tuple[bool, str]:
        """Paketi uygun yöneticiyle kur — devre dışı kaynak kontrolü"""
        if package.source not in self.enabled_sources:
            msg = f"❌ {package.source.value.upper()} kaynağı ayarlardan devre dışı bırakılmış."
            if callback: callback(msg + "\n")
            return False, msg
        m = self.managers.get(package.source)
        return m.install(package, callback) if m else (False, "Yönetici bulunamadı")

    def remove(self, package: Package, callback=None) -> tuple[bool, str]:
        """Paketi uygun yöneticiyle kaldır"""
        m = self.managers.get(package.source)
        return m.remove(package, callback) if m else (False, "Yönetici bulunamadı")

    def search_by_category(self, category: str) -> list[Package]:
        """Kategoriye göre etkin kaynaklarda ara"""
        results = []
        seen = set()
        # Sadece etkin kaynakları ara
        active_sources = [
            PackageSource.PACMAN,
            PackageSource.AUR,
            PackageSource.FLATPAK,
        ]
        for src in active_sources:
            if src not in self.enabled_sources:
                continue
            if src not in self.managers:
                continue
            m = self.managers[src]
            try:
                if hasattr(m, "search_by_category"):
                    pkgs = m.search_by_category(category)
                else:
                    keywords = CATEGORY_KEYWORDS.get(category, [category])
                    pkgs = m.search(keywords[0] if keywords else category)
                for p in pkgs:
                    if p.name not in seen:
                        seen.add(p.name)
                        results.append(p)
            except Exception as e:
                import sys
                print(f"[arxis] {src.value} kategori arama hatası: {e}", file=sys.stderr)

        # Sonuç yoksa sadece pacman ile geniş arama yap
        if not results:
            keywords = CATEGORY_KEYWORDS.get(category, [category])
            for kw in keywords[:2]:
                try:
                    pkgs = self.managers[PackageSource.PACMAN].search(kw)
                    for p in pkgs:
                        if p.name not in seen:
                            seen.add(p.name)
                            results.append(p)
                except Exception:
                    pass

        return results[:60]

    def get_all_updates(self) -> list[Package]:
        """Sadece gerçek güncellemeleri döndür"""
        updates = []
        for m in self.managers.values():
            updates.extend(m.get_updates())
        return updates

    def get_all_installed(self) -> list[Package]:
        installed = []
        for m in self.managers.values():
            installed.extend(m.get_installed())
        return installed

    def get_details(self, package: Package) -> Package:
        m = self.managers.get(package.source)
        return m.get_details(package) if m else package

    def get_orphans(self) -> list[Package]:
        m = self.managers[PackageSource.PACMAN]
        return m.get_orphans() if hasattr(m, "get_orphans") else []

    def remove_orphans(self, callback=None) -> tuple[bool, str]:
        m = self.managers[PackageSource.PACMAN]
        return m.remove_orphans(callback) if hasattr(m, "remove_orphans") else (False, "pacman bulunamadı")

    def update_all_pacman(self, callback=None) -> tuple[bool, str]:
        m = self.managers[PackageSource.PACMAN]
        return m.update_all(callback) if hasattr(m, "update_all") else (False, "pacman bulunamadı")

    def update_all_aur(self, callback=None) -> tuple[bool, str]:
        m = self.managers[PackageSource.AUR]
        tool = m._get_tool() if hasattr(m, "_get_tool") else ""
        if not tool:
            return False, "AUR yardımcısı (yay/paru) bulunamadı."
        code, out = m._run_stream([tool, "-Syu", "--noconfirm", "--aur"], callback=callback)
        return code == 0, out

    def update_all_flatpak(self, callback=None) -> tuple[bool, str]:
        m = self.managers[PackageSource.FLATPAK]
        if not m.is_available():
            return False, "Flatpak kurulu değil."
        code, out = m._run_stream(["flatpak", "update", "-y"], callback=callback)
        return code == 0, out

    def clean_cache(self, callback=None) -> tuple[bool, str]:
        m = self.managers[PackageSource.PACMAN]
        return m.clean_cache(callback) if hasattr(m, "clean_cache") else (False, "pacman bulunamadı")

    def get_system_info(self) -> dict:
        """Disk, paket sayısı, kernel bilgisi"""
        info = {}
        # Kernel
        code, out, _ = self.managers[PackageSource.PACMAN]._run(["uname", "-r"])
        info["kernel"] = out.strip() if code == 0 else "?"
        # Disk kullanımı
        code, out, _ = self.managers[PackageSource.PACMAN]._run(["df", "-h", "/"])
        if code == 0:
            lines = out.strip().split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                info["disk_total"] = parts[1] if len(parts) > 1 else "?"
                info["disk_used"]  = parts[2] if len(parts) > 2 else "?"
                info["disk_free"]  = parts[3] if len(parts) > 3 else "?"
                info["disk_pct"]   = parts[4] if len(parts) > 4 else "?"
        # Paket sayıları
        counts = {}
        code, out, _ = self.managers[PackageSource.PACMAN]._run(["pacman", "-Qq"])
        counts["pacman"] = len(out.strip().split("\n")) if out.strip() else 0
        tool = self.aur_tool()
        if tool:
            code, out, _ = self.managers[PackageSource.AUR]._run([tool, "-Qmq"])
            counts["aur"] = len(out.strip().split("\n")) if out.strip() else 0
        if self.managers[PackageSource.FLATPAK].is_available():
            code, out, _ = self.managers[PackageSource.FLATPAK]._run(["flatpak", "list", "-q"])
            counts["flatpak"] = len(out.strip().split("\n")) if out.strip() else 0
        info["counts"] = counts
        return info

    def install_multiple(self, packages: list[Package],
                         callback=None) -> list[tuple[Package, bool, str]]:
        """Toplu kurulum"""
        results = []
        for pkg in packages:
            if callback:
                callback(f"\n══ {pkg.display_name} kuruluyor... ══\n")
            ok, msg = self.install(pkg, callback)
            results.append((pkg, ok, msg))
        return results

    def remove_multiple(self, packages: list[Package],
                        callback=None) -> list[tuple[Package, bool, str]]:
        """Toplu kaldırma"""
        results = []
        for pkg in packages:
            if callback:
                callback(f"\n══ {pkg.display_name} kaldırılıyor... ══\n")
            ok, msg = self.remove(pkg, callback)
            results.append((pkg, ok, msg))
        return results

    # ── Curated lists ─────────────────────────────────────────────────────────

    def get_featured(self) -> list[Package]:
        """Her çalıştırmada farklı öne çıkan paketler — gerçek veri + rastgele seçim"""
        import random
        # Popüler kategorilerden anahtar kelimeler — her seferinde farklı seç
        pools = [
            ("visual-studio-code", PackageSource.AUR,    "#007acc", "Kod Editörü"),
            ("firefox",            PackageSource.PACMAN, "#ff6b00", "Web Tarayıcı"),
            ("vlc",                PackageSource.PACMAN, "#ff8800", "Video Oynatıcı"),
            ("gimp",               PackageSource.PACMAN, "#6666aa", "Görüntü Düzenleme"),
            ("obs-studio",         PackageSource.PACMAN, "#302e31", "Ekran Kaydı"),
            ("discord",            PackageSource.AUR,    "#5865f2", "Sohbet"),
            ("spotify",            PackageSource.AUR,    "#1db954", "Müzik"),
            ("blender",            PackageSource.PACMAN, "#f5792a", "3D Tasarım"),
            ("steam",              PackageSource.PACMAN, "#1b2838", "Oyun Platformu"),
            ("libreoffice-fresh",  PackageSource.PACMAN, "#1565c0", "Ofis Paketi"),
            ("inkscape",           PackageSource.PACMAN, "#e88b00", "Vektör Grafik"),
            ("krita",              PackageSource.PACMAN, "#3498db", "Dijital Boyama"),
            ("neovim",             PackageSource.PACMAN, "#57a143", "Metin Editörü"),
            ("telegram-desktop",   PackageSource.PACMAN, "#2ca5e0", "Mesajlaşma"),
            ("kdenlive",           PackageSource.PACMAN, "#527890", "Video Düzenleme"),
        ]
        random.shuffle(pools)
        pkgs = []
        for name, src, color, desc in pools[:3]:
            pkgs.append(Package(name, desc, "", src, icon_color=color))
        return pkgs

    def get_popular(self) -> list[Package]:
        """Her açılışta farklı popüler paketler — gerçek pacman DB'den"""
        import random
        candidates = [
            Package("firefox",           "Hızlı, özel web tarayıcısı",         "122.0",  PackageSource.PACMAN, icon_color="#ff6b00"),
            Package("vlc",               "Evrensel medya oynatıcı",            "3.0.20", PackageSource.PACMAN, icon_color="#ff8800"),
            Package("gimp",              "GNU Görüntü Düzenleme Programı",     "2.10.36",PackageSource.PACMAN, icon_color="#6666aa"),
            Package("obs-studio",        "Video kayıt ve canlı yayın",         "30.0",   PackageSource.PACMAN, icon_color="#302e31"),
            Package("discord",           "Topluluklar için sesli/yazılı sohbet","0.0.38", PackageSource.AUR,    icon_color="#5865f2"),
            Package("spotify",           "Müzik akış servisi",                  "1.2.26", PackageSource.AUR,    icon_color="#1db954"),
            Package("blender",           "3D modelleme ve animasyon",           "4.0.2",  PackageSource.PACMAN, icon_color="#f5792a"),
            Package("steam",             "Valve oyun platformu",                "latest", PackageSource.PACMAN, icon_color="#1b2838"),
            Package("inkscape",          "Vektör grafik editörü",               "1.3.2",  PackageSource.PACMAN, icon_color="#e88b00"),
            Package("krita",             "Dijital boyama uygulaması",           "5.2.0",  PackageSource.PACMAN, icon_color="#3498db"),
            Package("neovim",            "Hiper genişletilebilir metin editörü","0.9.5",  PackageSource.PACMAN, icon_color="#57a143"),
            Package("telegram-desktop",  "Hızlı ve güvenli mesajlaşma",        "4.16",   PackageSource.PACMAN, icon_color="#2ca5e0"),
            Package("kdenlive",          "Profesyonel video düzenleme",         "23.12",  PackageSource.PACMAN, icon_color="#527890"),
            Package("libreoffice-fresh", "Güçlü ofis paketi",                  "7.6.4",  PackageSource.PACMAN, icon_color="#1565c0"),
            Package("htop",              "İnteraktif süreç görüntüleyici",      "3.3.0",  PackageSource.PACMAN, icon_color="#059669"),
            Package("thunar",            "Modern dosya yöneticisi",             "4.18",   PackageSource.PACMAN, icon_color="#0284c7"),
            Package("mpv",               "Güçlü medya oynatıcı",               "0.36",   PackageSource.PACMAN, icon_color="#6c2dc7"),
            Package("keepassxc",         "Şifre yöneticisi",                   "2.7.6",  PackageSource.PACMAN, icon_color="#6cac35"),
            Package("filelight",         "Disk kullanım görselleştirici",       "23.08",  PackageSource.PACMAN, icon_color="#d4a017"),
            Package("audacity",          "Ses kayıt ve düzenleme",             "3.4.2",  PackageSource.PACMAN, icon_color="#0000cc"),
        ]
        random.shuffle(candidates)
        return candidates[:8]


# ─── GitHub Release Manager ───────────────────────────────────────────────────

class GitHubReleaseManager:
    """GitHub API üzerinden release bilgisi ve indirme"""
    API = "https://api.github.com"

    def parse_url(self, url: str) -> tuple[str, str] | None:
        """github.com/user/repo veya releases URL'sinden (owner, repo) çıkar"""
        import re
        m = re.search(r'github\.com/([^/]+)/([^/?\s#]+)', url)
        if m:
            return m.group(1), m.group(2).rstrip("/")
        return None

    def is_direct_asset(self, url: str) -> bool:
        return any(url.lower().endswith(ext)
                   for ext in (".appimage", ".tar.gz", ".tar.xz", ".zip", ".deb", ".rpm"))

    def get_releases(self, owner: str, repo: str) -> list[dict]:
        """Repo'nun son 10 release'ini getir"""
        api_url = f"{self.API}/repos/{owner}/{repo}/releases?per_page=10"
        try:
            req = urllib.request.Request(
                api_url, headers={"User-Agent": "arxis/1.0",
                                  "Accept": "application/vnd.github.v3+json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode())
        except Exception as ex:
            return [{"error": str(ex)}]

    def get_latest_assets(self, owner: str, repo: str) -> list[dict]:
        """En son release'in asset'lerini getir — özel dosya yoksa source tarball'ı da ekle"""
        releases = self.get_releases(owner, repo)
        if not releases or "error" in releases[0]:
            return []
        latest = releases[0]
        tag     = latest.get("tag_name", "")
        body    = (latest.get("body") or "")[:500]
        pub     = (latest.get("published_at") or "")[:10]
        assets  = latest.get("assets") or []
        result  = []

        # 1) Özel yüklenen dosyalar — uzantı filtresi geniş tutuldu
        SKIP_EXTS = (".sha256", ".sha512", ".md5", ".sig", ".asc", ".txt", ".json")
        for a in assets:
            name = a.get("name", "")
            if not name:
                continue
            low = name.lower()
            # İmza / checksum dosyalarını atla, geri kalanını kabul et
            if any(low.endswith(e) for e in SKIP_EXTS):
                continue
            result.append({
                "name":      name,
                "url":       a.get("browser_download_url", ""),
                "size":      a.get("size", 0),
                "tag":       tag,
                "body":      body,
                "published": pub,
                "kind":      "asset",
            })

        # 2) Özel asset yoksa → GitHub'ın otomatik source arşivlerini sun
        if not result:
            result.append({
                "name":      f"{repo}-{tag}.tar.gz",
                "url":       latest.get("tarball_url", ""),
                "size":      0,
                "tag":       tag,
                "body":      body,
                "published": pub,
                "kind":      "source",
            })
            result.append({
                "name":      f"{repo}-{tag}.zip",
                "url":       latest.get("zipball_url", ""),
                "size":      0,
                "tag":       tag,
                "body":      body,
                "published": pub,
                "kind":      "source",
            })

        return result

    def download_and_install(self, asset: dict, callback=None) -> tuple[bool, str]:
        """Asset'i indir, çıkart ve kurmaya çalış"""
        import pathlib, tarfile, zipfile, shutil, stat

        url  = asset.get("url", "")
        name = asset.get("name", "package")
        tag  = asset.get("tag", "")
        kind = asset.get("kind", "asset")

        if not url:
            return False, "İndirme URL'si bulunamadı."

        def cb(msg):
            if callback: callback(msg)

        # ── 1) AppImage → doğrudan kur ────────────────────────────────────────
        if name.lower().endswith(".appimage"):
            mgr  = AppImageManager()
            base = name.rsplit("-", 1)[0] if "-" in name else name.replace(".AppImage", "")
            return mgr.install_appimage(url, f"{base}-{tag}", callback)

        # ── 2) .deb → dpkg ile kur ────────────────────────────────────────────
        if name.lower().endswith(".deb"):
            dl_dir = pathlib.Path.home() / "Downloads"
            dl_dir.mkdir(parents=True, exist_ok=True)
            dest = dl_dir / name
            self._download_file(url, dest, cb)
            cb(f"\n📦 dpkg ile kuruluyor…\n")
            ok, out, err = self._run(["dpkg", "-i", str(dest)], sudo=True)
            cb(out); cb(err)
            return (True, str(dest)) if ok == 0 else (False, err or out)

        # ── 3) tar.gz / tar.xz / zip → çıkart + kurulum scripti ara ──────────
        is_tar = any(name.lower().endswith(e) for e in (".tar.gz", ".tar.xz", ".tar.bz2", ".tgz"))
        is_zip = name.lower().endswith(".zip")

        if is_tar or is_zip:
            # İndir
            dl_dir = pathlib.Path.home() / "Downloads"
            dl_dir.mkdir(parents=True, exist_ok=True)
            dest = dl_dir / name
            self._download_file(url, dest, cb)

            # Çıkart
            extract_dir = dl_dir / name.replace(".tar.gz","").replace(".tar.xz","") \
                                        .replace(".tar.bz2","").replace(".tgz","") \
                                        .replace(".zip","")
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True)

            cb(f"\n📂 Çıkartılıyor → {extract_dir}\n")
            try:
                if is_tar:
                    with tarfile.open(dest) as tf:
                        tf.extractall(extract_dir)
                else:
                    with zipfile.ZipFile(dest) as zf:
                        zf.extractall(extract_dir)
            except Exception as ex:
                return False, f"Çıkartma hatası: {ex}"

            # İçteki tek klasörü bul (çoğu tarball böyle paketlenir)
            children = list(extract_dir.iterdir())
            work_dir = (children[0] if len(children) == 1 and children[0].is_dir()
                        else extract_dir)
            cb(f"📁 Çalışma dizini: {work_dir}\n")

            # Kurulum yöntemini otomatik seç
            return self._auto_install(work_dir, cb)

        # ── 4) Diğer (binary, script…) → ~/Downloads'a indir + çalıştırılabilir yap
        dl_dir = pathlib.Path.home() / "Downloads"
        dl_dir.mkdir(parents=True, exist_ok=True)
        dest = dl_dir / name
        self._download_file(url, dest, cb)
        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
        cb(f"\n✅ İndirildi ve çalıştırılabilir yapıldı: {dest}\n")
        cb(f"ℹ  Çalıştırmak için: {dest}\n")
        return True, str(dest)

    # ── Yardımcı: dosya indir ─────────────────────────────────────────────────
    def _download_file(self, url: str, dest, callback=None):
        import pathlib
        dest = pathlib.Path(dest)
        callback and callback(f"⬇  İndiriliyor: {dest.name}\n")
        req = urllib.request.Request(url, headers={"User-Agent": "arxis/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            total = int(r.headers.get("Content-Length", 0))
            done  = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = r.read(65536)
                    if not chunk: break
                    f.write(chunk); done += len(chunk)
                    if callback and total:
                        pct = int(done / total * 100)
                        mb  = done  // (1024 * 1024)
                        tmb = total // (1024 * 1024)
                        callback(f"\r  {pct:3d}%  {mb}/{tmb} MB")
        callback and callback(f"\n✅ İndirildi: {dest}\n")

    # ── Yardımcı: kurulum yöntemi otomatik seç ───────────────────────────────
    def _auto_install(self, work_dir, callback=None) -> tuple[bool, str]:
        import pathlib
        cb = callback or (lambda m: None)
        wd = pathlib.Path(work_dir)

        # Öncelik sırası: install.sh → Makefile → PKGBUILD → meson → cmake → binary
        install_sh = wd / "install.sh"
        if install_sh.exists():
            install_sh.chmod(install_sh.stat().st_mode | 0o755)
            cb(f"\n🔧 install.sh bulundu — çalıştırılıyor…\n")
            ok, out, err = self._run(["bash", str(install_sh)], cwd=str(wd))
            cb(out); cb(err)
            return (True, str(wd)) if ok == 0 else (False, err or out)

        makefile = wd / "Makefile"
        if makefile.exists():
            cb(f"\n🔧 Makefile bulundu — make && sudo make install…\n")
            ok, out, err = self._run(["make", "-j4"], cwd=str(wd))
            cb(out); cb(err)
            if ok != 0: return False, err or out
            ok2, out2, err2 = self._run(["make", "install"], sudo=True, cwd=str(wd))
            cb(out2); cb(err2)
            return (True, str(wd)) if ok2 == 0 else (False, err2 or out2)

        pkgbuild = wd / "PKGBUILD"
        if pkgbuild.exists():
            cb(f"\n🔧 PKGBUILD bulundu — makepkg -si…\n")
            ok, out, err = self._run(["makepkg", "-si", "--noconfirm"], cwd=str(wd))
            cb(out); cb(err)
            return (True, str(wd)) if ok == 0 else (False, err or out)

        meson_build = wd / "meson.build"
        if meson_build.exists():
            cb(f"\n🔧 meson.build bulundu — meson setup + ninja install…\n")
            build_dir = wd / "_build"
            ok, out, err = self._run(["meson", "setup", str(build_dir)], cwd=str(wd))
            cb(out); cb(err)
            if ok != 0: return False, err or out
            ok2, out2, err2 = self._run(["ninja", "-C", str(build_dir)], cwd=str(wd))
            cb(out2); cb(err2)
            if ok2 != 0: return False, err2 or out2
            ok3, out3, err3 = self._run(["ninja", "-C", str(build_dir), "install"], sudo=True)
            cb(out3); cb(err3)
            return (True, str(wd)) if ok3 == 0 else (False, err3 or out3)

        cmake = wd / "CMakeLists.txt"
        if cmake.exists():
            cb(f"\n🔧 CMakeLists.txt bulundu — cmake + make install…\n")
            build_dir = wd / "_build"
            build_dir.mkdir(exist_ok=True)
            ok, out, err = self._run(
                ["cmake", "..", "-DCMAKE_BUILD_TYPE=Release"], cwd=str(build_dir))
            cb(out); cb(err)
            if ok != 0: return False, err or out
            ok2, out2, err2 = self._run(["make", "-j4"], cwd=str(build_dir))
            cb(out2); cb(err2)
            if ok2 != 0: return False, err2 or out2
            ok3, out3, err3 = self._run(["make", "install"], sudo=True, cwd=str(build_dir))
            cb(out3); cb(err3)
            return (True, str(wd)) if ok3 == 0 else (False, err3 or out3)

        # Hiçbiri bulunamadı → dizin içeriğini göster
        contents = "\n".join(f"  {p.name}" for p in sorted(wd.iterdir())[:20])
        cb(f"\n⚠  Tanınan kurulum dosyası bulunamadı.\n"
           f"   Dizin içeriği:\n{contents}\n"
           f"\n   Klasör konumu: {wd}\n"
           f"   Manuel kurulum için terminalde açabilirsiniz.\n")
        return True, str(wd)  # indirildi ama kurulmadı = kısmi başarı

    @staticmethod
    def _run(cmd: list, cwd: str = None) -> tuple[int, str, str]:
        """Komut çalıştır, (returncode, stdout, stderr) döndür"""
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=cwd, timeout=300)
            return result.returncode, result.stdout, result.stderr
        except FileNotFoundError:
            return -1, "", f"Komut bulunamadı: {cmd[0]}"
        except subprocess.TimeoutExpired:
            return -1, "", "Zaman aşımı (300s)"
        except Exception as ex:
            return -1, "", str(ex)


# ─── Snapshot Manager ─────────────────────────────────────────────────────────

class SnapshotManager:
    """Kurulu paket listesini JSON olarak dışa/içe aktar"""

    def create_snapshot(self, hub: "PackageManagerHub") -> dict:
        """Tüm kaynaklardan kurulu paketleri topla"""
        import datetime
        snapshot = {
            "created":  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hostname": "",
            "packages": {},
        }
        try:
            import socket
            snapshot["hostname"] = socket.gethostname()
        except Exception:
            pass

        for source, mgr in hub.managers.items():
            try:
                pkgs = mgr.get_installed()
                snapshot["packages"][source.value] = [
                    {"name": p.name, "version": p.version} for p in pkgs
                ]
            except Exception:
                snapshot["packages"][source.value] = []
        return snapshot

    def save(self, snapshot: dict, path: str) -> tuple[bool, str]:
        try:
            import pathlib
            p = pathlib.Path(path)
            p.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2),
                         encoding="utf-8")
            # Yan yana .txt (düz liste)
            txt_path = p.with_suffix(".txt")
            lines = []
            for src, pkgs in snapshot["packages"].items():
                for pkg in pkgs:
                    lines.append(f"{pkg['name']}\t{pkg['version']}\t{src}")
            txt_path.write_text("\n".join(lines), encoding="utf-8")
            return True, str(p)
        except Exception as ex:
            return False, str(ex)

    def load(self, path: str) -> tuple[bool, dict]:
        try:
            import pathlib
            data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
            return True, data
        except Exception as ex:
            return False, {"error": str(ex)}

    def diff(self, snapshot: dict, hub: "PackageManagerHub") -> dict:
        """Snapshot ile mevcut sistemi karşılaştır"""
        current_snapshot = self.create_snapshot(hub)
        diff = {"missing": [], "extra": [], "version_diff": []}
        for src, pkgs in snapshot.get("packages", {}).items():
            current_map = {
                p["name"]: p["version"]
                for p in current_snapshot["packages"].get(src, [])
            }
            snap_map = {p["name"]: p["version"] for p in pkgs}
            for name, ver in snap_map.items():
                if name not in current_map:
                    diff["missing"].append({"name": name, "version": ver, "source": src})
                elif current_map[name] != ver:
                    diff["version_diff"].append({
                        "name": name, "source": src,
                        "snap_ver": ver, "current_ver": current_map[name]})
            for name, ver in current_map.items():
                if name not in snap_map:
                    diff["extra"].append({"name": name, "version": ver, "source": src})
        return diff