"""
Paket yöneticisi backend işlemleri
Pacman, AUR, Flatpak, AppImage, Wine desteği
"""

import subprocess
import shutil
import os
import json
import re
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class PackageSource(Enum):
    PACMAN = "pacman"
    AUR = "aur"
    FLATPAK = "flatpak"
    APPIMAGE = "appimage"
    WINE = "wine"


@dataclass
class Package:
    name: str
    version: str
    description: str
    source: PackageSource
    installed: bool = False
    size: str = ""
    icon_name: str = ""
    category: str = "All"
    update_available: bool = False
    new_version: str = ""
    url: str = ""
    depends: list = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """İnsan okunabilir paket adı: tireler/alt çizgiler boşluğa çevrilir, baş harfler büyütülür"""
        return self.name.replace("-", " ").replace("_", " ").title()


class PackageManager:
    """Ana paket yöneticisi sınıfı"""

    def __init__(self):
        self._check_available_backends()

    def _check_available_backends(self):
        """Mevcut backend araçlarını kontrol et"""
        self.has_pacman = shutil.which("pacman") is not None
        self.has_yay = shutil.which("yay") is not None
        self.has_paru = shutil.which("paru") is not None
        self.has_flatpak = shutil.which("flatpak") is not None
        self.aur_helper = "yay" if self.has_yay else ("paru" if self.has_paru else None)

    def run_command(self, cmd: list, sudo: bool = False, password: str = None) -> tuple[int, str, str]:
        """Komut çalıştır ve sonucu döndür"""
        try:
            if sudo and password:
                cmd = ["sudo", "-S"] + cmd
                proc = subprocess.run(
                    cmd,
                    input=password + "\n",
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            else:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Zaman aşımı"
        except FileNotFoundError:
            return -1, "", f"Komut bulunamadı: {cmd[0]}"
        except Exception as e:
            return -1, "", str(e)

    # ── PACMAN ──────────────────────────────────────────────
    def pacman_search(self, query: str) -> list[Package]:
        if not self.has_pacman:
            return []
        rc, out, _ = self.run_command(["pacman", "-Ss", query])
        return self._parse_pacman_search(out)

    def _parse_pacman_search(self, output: str) -> list[Package]:
        packages = []
        lines = output.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if "/" in line and not line.startswith(" "):
                parts = line.split()
                if len(parts) >= 2:
                    repo_name = parts[0]
                    version = parts[1]
                    name = repo_name.split("/")[-1] if "/" in repo_name else repo_name
                    installed = "[installed]" in line.lower()
                    desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    packages.append(Package(
                        name=name,
                        version=version,
                        description=desc,
                        source=PackageSource.PACMAN,
                        installed=installed,
                    ))
                    i += 2
                    continue
            i += 1
        return packages

    def pacman_install(self, package: str, password: str) -> tuple[bool, str]:
        rc, out, err = self.run_command(["pacman", "-S", "--noconfirm", package], sudo=True, password=password)
        return rc == 0, err if rc != 0 else f"{package} başarıyla kuruldu."

    def pacman_remove(self, package: str, password: str) -> tuple[bool, str]:
        rc, out, err = self.run_command(["pacman", "-R", "--noconfirm", package], sudo=True, password=password)
        return rc == 0, err if rc != 0 else f"{package} başarıyla kaldırıldı."

    def pacman_get_installed(self) -> list[Package]:
        if not self.has_pacman:
            return []
        rc, out, _ = self.run_command(["pacman", "-Q"])
        packages = []
        for line in out.strip().split("\n"):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    packages.append(Package(
                        name=parts[0],
                        version=parts[1],
                        description="",
                        source=PackageSource.PACMAN,
                        installed=True,
                    ))
        return packages

    def pacman_get_updates(self) -> list[Package]:
        if not self.has_pacman:
            return []
        rc, out, _ = self.run_command(["pacman", "-Qu"])
        packages = []
        for line in out.strip().split("\n"):
            if line.strip() and "->" in line:
                parts = line.split()
                if len(parts) >= 4:
                    packages.append(Package(
                        name=parts[0],
                        version=parts[1],
                        new_version=parts[3],
                        description="",
                        source=PackageSource.PACMAN,
                        installed=True,
                        update_available=True,
                    ))
        return packages

    # ── AUR ─────────────────────────────────────────────────
    def aur_search(self, query: str) -> list[Package]:
        if not self.aur_helper:
            return []
        rc, out, _ = self.run_command([self.aur_helper, "-Ss", "--aur", query])
        return self._parse_aur_search(out)

    def _parse_aur_search(self, output: str) -> list[Package]:
        packages = []
        lines = output.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith("aur/"):
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].replace("aur/", "")
                    version = parts[1]
                    installed = "[installed]" in line.lower()
                    desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    packages.append(Package(
                        name=name,
                        version=version,
                        description=desc,
                        source=PackageSource.AUR,
                        installed=installed,
                    ))
                    i += 2
                    continue
            i += 1
        return packages

    def aur_install(self, package: str) -> tuple[bool, str]:
        if not self.aur_helper:
            return False, "AUR yardımcısı (yay/paru) bulunamadı."
        rc, out, err = self.run_command([self.aur_helper, "-S", "--noconfirm", package])
        return rc == 0, err if rc != 0 else f"{package} AUR'dan başarıyla kuruldu."

    # ── FLATPAK ─────────────────────────────────────────────
    def flatpak_search(self, query: str) -> list[Package]:
        if not self.has_flatpak:
            return []
        rc, out, _ = self.run_command(["flatpak", "search", "--columns=name,description,application,version", query])
        return self._parse_flatpak_search(out)

    def _parse_flatpak_search(self, output: str) -> list[Package]:
        packages = []
        for line in output.strip().split("\n")[1:]:  # Başlık satırını atla
            parts = line.split("\t")
            if len(parts) >= 4:
                packages.append(Package(
                    name=parts[0].strip(),
                    description=parts[1].strip(),
                    url=parts[2].strip(),
                    version=parts[3].strip() if len(parts) > 3 else "",
                    source=PackageSource.FLATPAK,
                ))
        return packages

    def flatpak_install(self, app_id: str) -> tuple[bool, str]:
        if not self.has_flatpak:
            return False, "Flatpak kurulu değil."
        rc, out, err = self.run_command(["flatpak", "install", "--noninteractive", "-y", app_id])
        return rc == 0, err if rc != 0 else f"{app_id} Flatpak'tan başarıyla kuruldu."

    def flatpak_get_installed(self) -> list[Package]:
        if not self.has_flatpak:
            return []
        rc, out, _ = self.run_command(["flatpak", "list", "--columns=name,application,version"])
        packages = []
        for line in out.strip().split("\n")[1:]:
            parts = line.split("\t")
            if len(parts) >= 3:
                packages.append(Package(
                    name=parts[0].strip(),
                    url=parts[1].strip(),
                    version=parts[2].strip(),
                    description="",
                    source=PackageSource.FLATPAK,
                    installed=True,
                ))
        return packages

    def flatpak_get_updates(self) -> list[Package]:
        if not self.has_flatpak:
            return []
        rc, out, _ = self.run_command(["flatpak", "remote-ls", "--updates"])
        packages = []
        for line in out.strip().split("\n"):
            if line.strip():
                parts = line.split()
                if parts:
                    packages.append(Package(
                        name=parts[0],
                        version="",
                        description="Flatpak güncelleme mevcut",
                        source=PackageSource.FLATPAK,
                        installed=True,
                        update_available=True,
                    ))
        return packages

    def flatpak_update_all(self) -> tuple[bool, str]:
        rc, out, err = self.run_command(["flatpak", "update", "-y"])
        return rc == 0, out if rc == 0 else err

    # ── SİSTEM BİLGİSİ ──────────────────────────────────────
    def get_system_stats(self) -> dict:
        stats = {}
        # CPU
        try:
            rc, out, _ = self.run_command(["cat", "/proc/loadavg"])
            if rc == 0:
                load = float(out.split()[0])
                stats["cpu"] = min(int(load * 10), 100)
        except:
            stats["cpu"] = 0
        # RAM
        try:
            rc, out, _ = self.run_command(["free", "-m"])
            if rc == 0:
                lines = out.strip().split("\n")
                for line in lines:
                    if line.startswith("Mem:"):
                        parts = line.split()
                        total = int(parts[1])
                        used = int(parts[2])
                        stats["ram_used"] = used
                        stats["ram_total"] = total
                        break
        except:
            stats["ram_used"] = 0
            stats["ram_total"] = 8192
        return stats

    def get_package_count(self) -> dict:
        counts = {}
        if self.has_pacman:
            rc, out, _ = self.run_command(["pacman", "-Qq"])
            counts["pacman"] = len(out.strip().split("\n")) if out.strip() else 0
        if self.has_flatpak:
            rc, out, _ = self.run_command(["flatpak", "list"])
            counts["flatpak"] = len(out.strip().split("\n")) if out.strip() else 0
        return counts

    def get_featured_packages(self) -> list[Package]:
        """Öne çıkan paketler - sabit liste"""
        return [
            Package("visual-studio-code-bin", "1.85.0", "Code editing. Redefined", PackageSource.AUR, icon_name="vscode"),
            Package("libreoffice-fresh", "7.6.4", "Powerful Office Suite", PackageSource.PACMAN, icon_name="libreoffice"),
            Package("steam", "1.0.0.75", "Gaming Platform", PackageSource.PACMAN, icon_name="steam", installed=True),
        ]

    def get_popular_packages(self) -> list[Package]:
        """Popüler paketler - sabit liste"""
        return [
            Package("discord", "0.0.39", "Chat for Communities", PackageSource.AUR, icon_name="discord"),
            Package("gimp", "2.10.36", "GNU Image Editor", PackageSource.PACMAN, icon_name="gimp"),
            Package("vlc", "3.0.20", "Video Player & Streamer", PackageSource.PACMAN, icon_name="vlc"),
            Package("spotify", "1.2.25", "Music Streaming Service", PackageSource.AUR, icon_name="spotify"),
        ]