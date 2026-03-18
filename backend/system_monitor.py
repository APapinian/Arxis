import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemMonitor(QThread):
    """Emits system stats every 2 seconds."""
    stats_updated = pyqtSignal(dict)

    PKG_COUNT_INTERVAL = 300   # P-4: pacman -Q her 5 dakikada bir

    def __init__(self):
        super().__init__()
        self._running = True
        self._cached_pkg_count = 57420
        self._last_pkg_count_ts = 0.0

    def run(self):
        while self._running:
            self.stats_updated.emit(self._collect())
            for _ in range(20):
                if not self._running:
                    return
                self.msleep(100)

    def stop(self):
        self._running = False
        self.quit()

    def _collect(self) -> dict:
        if not HAS_PSUTIL:
            return {"cpu": 0, "ram_used": 0, "ram_total": 8,
                    "packages_count": self._cached_pkg_count}
        try:
            cpu  = psutil.cpu_percent(interval=0.3)
            mem  = psutil.virtual_memory()
            return {
                "cpu":            cpu,
                "ram_used":       mem.used  / 1024**3,
                "ram_total":      mem.total / 1024**3,
                "packages_count": self._pkg_count(),
            }
        except Exception:
            return {"cpu": 0, "ram_used": 0, "ram_total": 8,
                    "packages_count": self._cached_pkg_count}

    def _pkg_count(self) -> int:
        """P-4: pacman -Qq pahalı — 5 dakikada bir çalıştır"""
        now = time.time()
        if (now - self._last_pkg_count_ts) < self.PKG_COUNT_INTERVAL:
            return self._cached_pkg_count
        try:
            r = subprocess.run(["pacman", "-Qq"], capture_output=True,
                               text=True, timeout=4)
            if r.returncode == 0:
                count = len(r.stdout.strip().splitlines())
                self._cached_pkg_count = count
                self._last_pkg_count_ts = now
                return count
        except Exception:
            pass
        return self._cached_pkg_count


class NetSpeedMonitor(QThread):
    """Emits download speed (MB/s) every second."""
    speed_updated = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._running = True

    def run(self):
        if not HAS_PSUTIL:
            return
        last = psutil.net_io_counters().bytes_recv
        while self._running:
            for _ in range(10):
                if not self._running:
                    return
                self.msleep(100)
            cur   = psutil.net_io_counters().bytes_recv
            speed = max(0.0, (cur - last) / 1024**2)
            last  = cur
            self.speed_updated.emit(speed)

    def stop(self):
        self._running = False
        self.quit()