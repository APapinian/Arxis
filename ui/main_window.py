from __future__ import annotations

import math
import os

# T-3: Global animasyon flag — False olunca tüm slide paneller anında açılır/kapanır
ANIMATIONS_ENABLED = True
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QLineEdit, QScrollArea, QSizePolicy,
    QProgressBar, QTextEdit, QStackedWidget, QGridLayout,
    QMessageBox, QDialog,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QPointF, QRectF, QRect,
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPolygonF, QPainterPath, QCursor, QPixmap,
    QKeySequence, QShortcut,
)

from ui.styles import DARK_THEME
from backend.managers import Package, PackageSource, PackageManagerHub, SOURCE_COLORS
from backend.system_monitor import SystemMonitor, NetSpeedMonitor


# ─── Icon Loading ─────────────────────────────────────────────────────────────

_ALIASES: dict[str, list[str]] = {
    "visual-studio-code-bin": ["code", "visual-studio-code", "code-oss"],
    "discord":    ["discord", "Discord"],
    "gimp":       ["gimp"],
    "vlc":        ["vlc"],
    "spotify":    ["spotify", "Spotify"],
    "firefox":    ["firefox", "org.mozilla.firefox"],
    "thunderbird":["thunderbird", "org.mozilla.Thunderbird"],
    "obs-studio": ["obs", "com.obsproject.Studio"],
    "libreoffice-fresh": ["libreoffice-startcenter", "libreoffice"],
    "libreoffice":["libreoffice-startcenter", "libreoffice"],
    "steam":      ["steam", "com.valvesoftware.Steam"],
    "com.valvesoftware.steam": ["steam"],
    "google-chrome": ["google-chrome", "google-chrome-stable"],
    "chromium":   ["chromium"],
    "neovim":     ["nvim", "neovim"],
}

_ICON_DIRS = [
    "/usr/share/icons/hicolor/256x256/apps",
    "/usr/share/icons/hicolor/128x128/apps",
    "/usr/share/icons/hicolor/64x64/apps",
    "/usr/share/icons/hicolor/48x48/apps",
    "/usr/share/icons/Papirus/64x64/apps",
    "/usr/share/icons/Papirus/48x48/apps",
    "/usr/share/icons/breeze/apps/48",
    "/usr/share/pixmaps",
    os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps"),
    os.path.expanduser("~/.local/share/icons/hicolor/48x48/apps"),
]

_icon_cache: dict[str, QPixmap | None] = {}

def load_app_icon(pkg_name: str, size: int) -> QPixmap | None:
    k = f"{pkg_name}:{size}"
    if k in _icon_cache:
        return _icon_cache[k]
    candidates = list(_ALIASES.get(pkg_name.lower(), []))
    candidates += [pkg_name.lower(), pkg_name.lower().split(".")[0], pkg_name.lower().split("-")[0]]
    for d in _ICON_DIRS:
        for name in candidates:
            for ext in (".png", ".svg", ".xpm"):
                path = os.path.join(d, name + ext)
                if os.path.isfile(path):
                    px = QPixmap(path)
                    if not px.isNull():
                        scaled = px.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                        _icon_cache[k] = scaled
                        return scaled
    _icon_cache[k] = None
    return None


# ─── Fallback Colors ──────────────────────────────────────────────────────────

_FALLBACK: dict[str, tuple[str, str]] = {
    "visual-studio-code-bin": ("#007acc", "#0d2a4a"),
    "discord":    ("#5865f2", "#1a1e40"), "gimp":      ("#9b7c4e", "#2a1e10"),
    "vlc":        ("#ff8800", "#3a2000"), "spotify":   ("#1db954", "#002a10"),
    "firefox":    ("#ff6b35", "#3a1a05"), "thunderbird":("#4a88cc", "#0a1e35"),
    "obs-studio": ("#cccccc", "#1a1a1a"), "libreoffice-fresh": ("#18a303", "#0a2a05"),
    "libreoffice":("#18a303", "#0a2a05"), "steam":     ("#c6d4df", "#1b2838"),
    "com.valvesoftware.steam": ("#c6d4df", "#1b2838"),
    "google-chrome": ("#4285f4", "#0a1a3a"), "chromium": ("#4285f4", "#0a1a3a"),
    "neovim":     ("#57a143", "#0a2010"), "htop":      ("#2da44e", "#0a1a10"),
    "git":        ("#f05030", "#2a0a05"), "python":    ("#306998", "#0a1a2a"),
}


# ─── App Icon Widget ──────────────────────────────────────────────────────────

class AppIconWidget(QWidget):
    """Real system icon if found, else colored letter fallback."""
    def __init__(self, pkg_name: str, letter: str, color: str, size: int = 44):
        super().__init__()
        self.setFixedSize(size, size)
        self._size = size
        self._set(pkg_name, letter, color)

    def _set(self, pkg_name: str, letter: str, color: str):
        self._pixmap = load_app_icon(pkg_name, self._size)
        key = pkg_name.lower()
        self._fg, self._bg = _FALLBACK.get(key, (color, self._dark(color)))
        self._letter = letter.upper()[:2] if len(letter) >= 2 else letter.upper()

    def update_pkg(self, pkg_name: str, letter: str, color: str):
        """Widget'ı yeni paket için güncelle — __init__ çağırmadan"""
        self._set(pkg_name, letter, color)
        self.update()   # repaint

    @staticmethod
    def _dark(c: str) -> str:
        q = QColor(c)
        return QColor(q.red()//4, q.green()//4, q.blue()//4).name()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        s = self._size; r = s // 5
        if self._pixmap:
            clip = QPainterPath()
            clip.addRoundedRect(QRectF(0, 0, s, s), r, r)
            p.setClipPath(clip)
            px = self._pixmap
            p.drawPixmap((s - px.width())//2, (s - px.height())//2, px)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(self._bg)))
            p.drawRoundedRect(0, 0, s, s, r, r)
            p.setPen(QPen(QColor(self._fg + "44"), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(0, 0, s-1, s-1, r, r)
            p.setPen(QPen(QColor(self._fg)))
            f = QFont("Segoe UI", max(7, s//(3 if len(self._letter)<=2 else 4)))
            f.setBold(True); p.setFont(f)
            p.drawText(QRect(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, self._letter)
        p.end()


# ─── Arch Logo ────────────────────────────────────────────────────────────────

class ArchLogo(QWidget):
    def __init__(self, size: int = 34):
        super().__init__()
        self.setFixedSize(size, size)
        self._s = size; self._phase = 0.0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(50)

    def _tick(self): self._phase += 0.05; self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._s; glow = (math.sin(self._phase) + 1) / 2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(249, 115, 22, int(15 + glow * 30))))
        mg = int(glow * 3)
        p.drawEllipse(-mg, -mg, s + mg*2, s + mg*2)
        g = QLinearGradient(s/2, 0, s/2, s)
        g.setColorAt(0, QColor("#f97316")); g.setColorAt(1, QColor("#c2410c"))
        p.setBrush(QBrush(g))
        p.drawPolygon(QPolygonF([QPointF(s/2,1), QPointF(1,s-1), QPointF(s-1,s-1)]))
        p.setBrush(QBrush(QColor("#070b14")))
        p.drawPolygon(QPolygonF([
            QPointF(s/2, s*0.25), QPointF(s*0.18, s*0.82), QPointF(s*0.82, s*0.82)]))
        p.end()


# ─── Sidebar Wave ─────────────────────────────────────────────────────────────

class SidebarWave(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(160); self._phase = 0.0
        t = QTimer(self); t.timeout.connect(self._tick); t.start(40)

    def _tick(self): self._phase += 0.012; self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height(); ph = self._phase
        fade = QLinearGradient(0, 0, 0, h)
        fade.setColorAt(0, QColor(11,17,32,0)); fade.setColorAt(1, QColor(11,17,32,255))
        p.fillRect(0, 0, w, h, fade)
        for xf,yf,col,rad,off in [
            (0.6,0.35,"#f97316",50,0.0),(0.35,0.6,"#c2410c",65,1.1),(0.75,0.7,"#172035",45,2.2)]:
            x = w*xf + math.sin(ph+off)*18; y = h*yf + math.cos(ph*0.7+off)*12
            r = rad + math.sin(ph*1.3+off)*8
            gr = QRadialGradient(x, y, r)
            c = QColor(col); c.setAlpha(55); gr.setColorAt(0, c)
            c2 = QColor(col); c2.setAlpha(0); gr.setColorAt(1, c2)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(gr))
            p.drawEllipse(QRectF(x-r, y-r, r*2, r*2))
        path = QPainterPath()
        for i in range(w+1):
            y2 = h*0.5 + math.sin(i*0.04+ph)*14 + math.sin(i*0.07+ph*1.4)*7
            path.moveTo(i,y2) if i==0 else path.lineTo(i,y2)
        path.lineTo(w,h); path.lineTo(0,h); path.closeSubpath()
        wg = QLinearGradient(0,0,w,0)
        wg.setColorAt(0, QColor(249,115,22,12)); wg.setColorAt(0.5, QColor(249,115,22,22))
        wg.setColorAt(1, QColor(249,115,22,8))
        p.setBrush(QBrush(wg)); p.drawPath(path)
        p.end()


# ─── Stats Card ───────────────────────────────────────────────────────────────

class StatsCard(QWidget):
    """Sidebar system stats, all drawn with QPainter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(82)
        self._data = {'cpu': 0.0, 'ram': 0.0, 'ram_total': 8.0, 'net': 0.0}

    def update_stats(self, s: dict):
        self._data['cpu']       = s.get('cpu', 0)
        self._data['ram']       = s.get('ram_used', 0)
        self._data['ram_total'] = s.get('ram_total', 8)
        self.update()

    def update_net(self, mbps: float):
        self._data['net'] = mbps; self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Card bg
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(16, 24, 40)))
        p.drawRoundedRect(QRectF(0, 0, w, h), 11, 11)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 14), 1))
        p.drawRoundedRect(QRectF(0.5, 0.5, w-1, h-1), 11, 11)

        d = self._data
        rows = [
            ('CPU', d['cpu']/100, f"{d['cpu']:.0f}%"),
            ('RAM', d['ram']/max(1,d['ram_total']), f"{d['ram']:.1f}G"),
            ('NET', min(1.0, d['net']/10.0),
             f"{d['net']*1024:.0f}K" if d['net'] < 0.1 else f"{d['net']:.1f}M"),
        ]
        fL = QFont("JetBrains Mono", 8); fL.setBold(True)
        fV = QFont("JetBrains Mono", 8)
        for i, (lbl, pct, val) in enumerate(rows):
            y = 10 + i * 22
            p.setPen(QPen(QColor("#2e3a55")))
            p.setFont(fL)
            p.drawText(QRect(10, y, 28, 14), Qt.AlignmentFlag.AlignVCenter, lbl)
            track_x = 44; track_w = w - 44 - 40; track_y = y + 5
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(30, 45, 69)))
            p.drawRoundedRect(QRectF(track_x, track_y, track_w, 3), 1.5, 1.5)
            fw = track_w * max(0.0, min(1.0, pct))
            if fw > 0:
                g = QLinearGradient(track_x, 0, track_x+fw, 0)
                if i == 2:
                    g.setColorAt(0, QColor("#f97316")); g.setColorAt(1, QColor("#3b82f6"))
                else:
                    g.setColorAt(0, QColor("#f97316")); g.setColorAt(1, QColor("#fb923c"))
                p.setBrush(QBrush(g))
                p.drawRoundedRect(QRectF(track_x, track_y, fw, 3), 1.5, 1.5)
            p.setPen(QPen(QColor("#6b7a99")))
            p.setFont(fV)
            p.drawText(QRect(int(track_x+track_w+4), y, 36, 14),
                      Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, val)
        p.end()


# ─── Nav Item ─────────────────────────────────────────────────────────────────

class NavItem(QWidget):
    clicked_sig = pyqtSignal()

    def __init__(self, icon: str, label: str, active: bool = False, badge: str | None = None):
        super().__init__()
        self.setFixedHeight(40)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._active = active; self._hover = False
        self._hover_alpha = 0   # animasyonlu hover
        self._active_alpha = 255 if active else 0
        self._anim_timer = QTimer(self); self._anim_timer.timeout.connect(self._tick_anim)

        lay = QHBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFixedWidth(64)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sync_icon()
        lay.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self._sync_text(); self._text_lbl.hide()
        lay.addWidget(self._text_lbl, 1)

        self._badge = None
        if badge:
            b = QLabel(badge)
            b.setStyleSheet("QLabel{background:rgba(249,115,22,0.15);color:#fb923c;"
                            "border:1px solid rgba(249,115,22,0.2);border-radius:9px;"
                            "font-size:9px;font-weight:700;padding:1px 6px;}")
            b.setFixedHeight(18); b.setAlignment(Qt.AlignmentFlag.AlignCenter); b.hide()
            lay.addWidget(b); lay.setContentsMargins(0,0,8,0)
            self._badge = b

    def _tick_anim(self):
        target_h = 30 if self._hover else 0
        target_a = 22 if self._active else 0
        ch = int((target_h - self._hover_alpha) * 0.25) or (1 if self._hover_alpha < target_h else -1 if self._hover_alpha > target_h else 0)
        ca = int((target_a - self._active_alpha) * 0.25) or (1 if self._active_alpha < target_a else -1 if self._active_alpha > target_a else 0)
        self._hover_alpha  = max(0, min(30, self._hover_alpha + ch))
        self._active_alpha = max(0, min(22, self._active_alpha + ca))
        self.update()
        if self._hover_alpha == target_h and self._active_alpha == target_a:
            self._anim_timer.stop()

    def _sync_icon(self):
        c = "#f97316" if self._active else "#6b7a99"
        w = "700" if self._active else "400"
        self._icon_lbl.setStyleSheet(f"color:{c};font-size:15px;font-weight:{w};background:transparent;")

    def _sync_text(self):
        c = "#fb923c" if self._active else "#6b7a99"
        self._text_lbl.setStyleSheet(f"color:{c};font-size:14px;font-weight:500;background:transparent;")

    def set_expanded(self, v: bool):
        self._text_lbl.setVisible(v)
        self._icon_lbl.setFixedWidth(48 if v else 64)
        if self._badge: self._badge.setVisible(v)

    def set_active(self, a: bool):
        self._active = a; self._sync_icon(); self._sync_text()
        if ANIMATIONS_ENABLED:
            self._anim_timer.start(12)
        else:
            self._active_alpha = 22 if a else 0
            self.update()

    def set_badge(self, text: str):
        if not self._badge:
            b = QLabel(text)
            b.setStyleSheet("QLabel{background:rgba(249,115,22,0.15);color:#fb923c;"
                            "border:1px solid rgba(249,115,22,0.2);border-radius:9px;"
                            "font-size:9px;font-weight:700;padding:1px 6px;}")
            b.setFixedHeight(18); b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b.setVisible(self._text_lbl.isVisible())
            self.layout().addWidget(b); self.layout().setContentsMargins(0,0,8,0)
            self._badge = b
        else:
            self._badge.setText(text)
            self._badge.setVisible(bool(text) and self._text_lbl.isVisible())

    def enterEvent(self, e):
        self._hover = True
        if ANIMATIONS_ENABLED: self._anim_timer.start(12)
        else: self._hover_alpha = 30; self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        if ANIMATIONS_ENABLED: self._anim_timer.start(12)
        else: self._hover_alpha = 0; self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.clicked_sig.emit()
        super().mousePressEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Aktif arka plan
        if self._active_alpha > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(249, 115, 22, self._active_alpha)))
            p.drawRoundedRect(QRectF(2, 2, w-4, h-4), 10, 10)
            # Sol çizgi
            g = QLinearGradient(0, 0, 0, h)
            g.setColorAt(0, QColor("#f97316")); g.setColorAt(1, QColor("#fb923c"))
            p.setBrush(QBrush(g))
            bh = 18
            p.drawRoundedRect(QRectF(0, (h-bh)//2, 3, bh), 1.5, 1.5)
        elif self._hover_alpha > 0:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, self._hover_alpha)))
            p.drawRoundedRect(QRectF(2, 2, w-4, h-4), 10, 10)
        p.end()


# ─── Collapsible Sidebar ──────────────────────────────────────────────────────

class CollapsibleSidebar(QWidget):
    COLLAPSED = 64
    EXPANDED  = 220
    nav_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self._cw = self.COLLAPSED
        self._target = self.COLLAPSED
        self._is_open = False
        self._anim = QTimer(self); self._anim.timeout.connect(self._step)
        self.setFixedWidth(self.COLLAPSED)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # ── Logo row ──
        logo_row = QWidget(); logo_row.setFixedHeight(68)
        logo_row.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        logo_row.mousePressEvent = lambda e: (
            self.toggle() if e.button() == Qt.MouseButton.LeftButton else None)
        ll = QHBoxLayout(logo_row); ll.setContentsMargins(12,14,12,14); ll.setSpacing(10)

        logo_btn = QWidget(); logo_btn.setObjectName("logo_btn"); logo_btn.setFixedSize(40,40)
        lb = QHBoxLayout(logo_btn); lb.setContentsMargins(3,3,3,3); lb.addWidget(ArchLogo(32))
        ll.addWidget(logo_btn)

        self._title_lbl = QLabel("Arxis")
        self._title_lbl.setStyleSheet("color:white;font-size:16px;font-weight:700;background:transparent;")
        self._title_lbl.hide(); ll.addWidget(self._title_lbl, 1)
        lay.addWidget(logo_row)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame{color:rgba(255,255,255,0.055);}"); lay.addWidget(sep)
        lay.addSpacing(6)

        # ── Nav items ──
        self._nav: dict[str, NavItem] = {}
        for icon, label, key, badge in [
            ("⊞", "Keşfet",      "discover",    None),
            ("✓", "Yüklü",       "installed",   "247"),
            ("≡", "Kategoriler", "categories",  None),
            ("★", "Beğenilenler","favorites",   None),
            ("⊕", "Kuyruk",      "queue",       None),
            ("⇔", "Karşılaştır", "compare",     None),
            ("⊙", "Geçmiş",      "history",     None),
            ("◫", "Snapshot",    "snapshot",    None),
            ("⌥", "GitHub",      "github",      None),
            ("⚒", "Bakım",       "maintenance", None),
            ("⚙", "Ayarlar",     "settings",    None),
        ]:
            item = NavItem(icon, label, active=(key=="discover"), badge=badge)
            item.clicked_sig.connect(lambda k=key: self.nav_clicked.emit(k))
            wrap = QWidget()
            wl = QHBoxLayout(wrap); wl.setContentsMargins(6,2,6,2); wl.addWidget(item)
            lay.addWidget(wrap)
            self._nav[key] = item

        lay.addStretch()
        lay.addWidget(SidebarWave())

        # ── Stats ──
        stats_wrap = QWidget(); stats_wrap.setFixedHeight(96)
        sl = QVBoxLayout(stats_wrap); sl.setContentsMargins(10,0,10,12); sl.setSpacing(0)
        self._stats = StatsCard(); self._stats.hide(); sl.addWidget(self._stats)
        lay.addWidget(stats_wrap)

    def toggle(self):
        self._is_open = not self._is_open
        self._target = self.EXPANDED if self._is_open else self.COLLAPSED
        if not self._is_open:
            self._title_lbl.hide()
            for item in self._nav.values(): item.set_expanded(False)
            self._stats.hide()
        self._anim.start(8)

    def _step(self):
        diff = self._target - self._cw
        step = int(diff * 0.22) or (1 if diff > 0 else -1 if diff < 0 else 0)
        self._cw = max(self.COLLAPSED, min(self.EXPANDED, self._cw + step))
        self.setFixedWidth(self._cw)
        if self._cw == self._target:
            self._anim.stop()
            if self._is_open:
                self._title_lbl.show()
                for item in self._nav.values(): item.set_expanded(True)
                self._stats.show()

    def set_active(self, key: str):
        for k, item in self._nav.items(): item.set_active(k == key)

    def set_badge(self, key: str, text: str):
        if key in self._nav:
            self._nav[key].set_badge(text)

    def update_stats(self, s: dict): self._stats.update_stats(s)
    def update_net(self, mbps: float): self._stats.update_net(mbps)


# ─── Source Tag ───────────────────────────────────────────────────────────────

class SourceTag(QLabel):
    def __init__(self, source: PackageSource):
        bg, fg = SOURCE_COLORS.get(source, ("#1e293b", "#94a3b8"))
        super().__init__(source.value.upper())
        self.setStyleSheet(f"QLabel{{background:{bg};color:{fg};"
                           f"border:1px solid {fg}55;border-radius:4px;"
                           f"padding:0px 7px;font-size:10px;font-weight:bold;}}")
        self.setFixedHeight(18)


# ─── Badge ────────────────────────────────────────────────────────────────────

class Badge(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("QLabel{background:#dc2626;color:white;border-radius:9px;"
                           "font-size:10px;font-weight:bold;padding:1px 5px;min-width:18px;}")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setFixedHeight(18)


# ─── Featured Card ────────────────────────────────────────────────────────────

_CARD_THEMES = [
    {"bg1": "#080e20", "bg2": "#0d1a36", "accent": "#f97316"},
    {"bg1": "#060e12", "bg2": "#0c1d24", "accent": "#0ea5e9"},
    {"bg1": "#090d1a", "bg2": "#121d30", "accent": "#8b5cf6"},
]


class FeaturedCard(QWidget):
    action = pyqtSignal(object, str)

    def __init__(self, pkg: Package, idx: int = 0):
        super().__init__()
        self.pkg = pkg; self._t = _CARD_THEMES[idx % len(_CARD_THEMES)]
        self._hover = 0; self._hovering = False
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick)
        self.setMinimumSize(240, 168); self.setFixedHeight(168)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20,18,20,16); lay.setSpacing(8)
        top = QHBoxLayout(); top.setSpacing(14)

        icon_lbl = QLabel(); icon_lbl.setFixedSize(52, 52)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent;")
        px = load_app_icon(self.pkg.name, 48)
        if px:
            icon_lbl.setPixmap(px); top.addWidget(icon_lbl)
        else:
            iw = AppIconWidget(self.pkg.name, self.pkg.icon_letter, self.pkg.icon_color, 52)
            top.addWidget(iw)

        nl = QVBoxLayout(); nl.setSpacing(4)
        title = QLabel(self.pkg.display_name)
        title.setStyleSheet("color:white;font-size:16px;font-weight:700;background:transparent;")
        desc = self.pkg.description[:44] + ("…" if len(self.pkg.description)>44 else "")
        sub = QLabel(desc)
        sub.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
        tag_row = QHBoxLayout(); tag_row.setSpacing(6)
        tag_row.addWidget(SourceTag(self.pkg.source)); tag_row.addStretch()
        nl.addWidget(title); nl.addWidget(sub); nl.addLayout(tag_row)
        top.addLayout(nl); top.addStretch()
        lay.addLayout(top); lay.addStretch()

        br = QHBoxLayout()
        btn = QPushButton("Aç" if self.pkg.installed else "Kur")
        btn.setObjectName("open_btn" if self.pkg.installed else "install_btn")
        btn.setFixedWidth(106); btn.setFixedHeight(34)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda: self.action.emit(
            self.pkg, "open" if self.pkg.installed else "install"))
        br.addWidget(btn); br.addStretch()
        lay.addLayout(br)

    def enterEvent(self, e): self._hovering=True;  self._timer.start(16); super().enterEvent(e)
    def leaveEvent(self, e): self._hovering=False; self._timer.start(16); super().leaveEvent(e)

    def _tick(self):
        target = 255 if self._hovering else 0
        diff = target - self._hover
        step = int(diff*0.18) or (1 if diff>0 else -1 if diff<0 else 0)
        self._hover = max(0, min(255, self._hover+step))
        self.update()
        if self._hover == target: self._timer.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height(); t = self._t
        ac = QColor(t["accent"])

        clip = QPainterPath(); clip.addRoundedRect(QRectF(0,0,w,h),14,14)
        p.setClipPath(clip)

        g = QLinearGradient(0,0,w,h)
        g.setColorAt(0,QColor(t["bg1"])); g.setColorAt(1,QColor(t["bg2"]))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(g))
        p.drawRoundedRect(QRectF(0,0,w,h),14,14)

        gr = QRadialGradient(w*0.88, h*0.08, w*0.5)
        c1=QColor(ac); c1.setAlpha(38+int(self._hover*0.09)); gr.setColorAt(0,c1)
        c2=QColor(ac); c2.setAlpha(0); gr.setColorAt(1,c2)
        p.setBrush(QBrush(gr)); p.drawRoundedRect(QRectF(0,0,w,h),14,14)

        gr2 = QRadialGradient(w*0.5,h*1.1,w*0.55)
        c3=QColor(ac); c3.setAlpha(16+int(self._hover*0.05)); gr2.setColorAt(0,c3)
        c4=QColor(ac); c4.setAlpha(0); gr2.setColorAt(1,c4)
        p.setBrush(QBrush(gr2)); p.drawRoundedRect(QRectF(0,0,w,h),14,14)

        sg = QLinearGradient(0,0,0,h*0.38)
        sg.setColorAt(0,QColor(255,255,255,13)); sg.setColorAt(1,QColor(255,255,255,0))
        p.setBrush(QBrush(sg)); p.drawRoundedRect(QRectF(0,0,w,h),14,14)

        p.setClipping(False); p.setBrush(Qt.BrushStyle.NoBrush)
        ba = 50+int(self._hover*0.7)
        p.setPen(QPen(QColor(ac.red(),ac.green(),ac.blue(),ba),1))
        p.drawRoundedRect(QRectF(0.5,0.5,w-1,h-1),14,14)
        p.end()


# ─── Package Item ─────────────────────────────────────────────────────────────

class PackageItem(QWidget):
    """Clean, always-clickable package row. No GraphicsEffect."""
    action            = pyqtSignal(object, str)
    detail_requested  = pyqtSignal(object)
    compare_requested = pyqtSignal(object)
    favorite_requested = pyqtSignal(object)
    queue_requested    = pyqtSignal(object)

    def __init__(self, pkg: Package, update_mode: bool = False):
        super().__init__()
        self.pkg = pkg; self._update = update_mode
        self.setObjectName("package_item")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setToolTip(
            f"<b>{self.pkg.display_name}</b> {self.pkg.version}<br>"
            f"<span style='color:#6b7a99'>{self.pkg.description[:120]}</span><br>"
            f"<i>Sol tık: detay · Çift tık: hızlı kur/kaldır · Sağ tık: menü</i>"
        )
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(220)
        self._click_timer.timeout.connect(self._emit_detail)
        self._pending_click = False
        self._hover_val  = 0.0
        self._is_hovered = False
        self._hover_timer = QTimer(self); self._hover_timer.timeout.connect(self._tick_hover)
        self._build()

    def _tick_hover(self):
        target = 1.0 if self._is_hovered else 0.0
        diff = target - self._hover_val
        self._hover_val += diff * 0.25
        if abs(diff) < 0.02:
            self._hover_val = target; self._hover_timer.stop()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._hover_val > 0.01:
            p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, int(self._hover_val * 14))))
            p.drawRect(0, 0, self.width(), self.height())
            lg = QLinearGradient(0, 0, 0, self.height())
            la = int(self._hover_val * 150)
            lg.setColorAt(0, QColor(249,115,22,0)); lg.setColorAt(0.5, QColor(249,115,22,la)); lg.setColorAt(1, QColor(249,115,22,0))
            p.setBrush(QBrush(lg)); p.drawRect(0, 0, 2, self.height())
            p.end()

    def enterEvent(self, e):
        self._is_hovered = True
        if ANIMATIONS_ENABLED: self._hover_timer.start(12)
        else: self._hover_val = 1.0; self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._is_hovered = False
        if ANIMATIONS_ENABLED: self._hover_timer.start(12)
        else: self._hover_val = 0.0; self.update()
        super().leaveEvent(e)

    def _emit_detail(self):
        """Timer dolunca tek tık kesinleşti — detay sayfasını aç"""
        if self._pending_click:
            self._pending_click = False
            self.detail_requested.emit(self.pkg)

    def _build(self):
        lay = QHBoxLayout(self); lay.setContentsMargins(16,10,16,10); lay.setSpacing(14)
        lay.addWidget(AppIconWidget(self.pkg.name, self.pkg.icon_letter, self.pkg.icon_color, 40))

        info = QVBoxLayout(); info.setSpacing(3)
        nr = QHBoxLayout(); nr.setSpacing(8)
        nm = QLabel(self.pkg.display_name); nm.setObjectName("package_name")
        nr.addWidget(nm); nr.addWidget(SourceTag(self.pkg.source)); nr.addStretch()
        info.addLayout(nr)

        if self._update and self.pkg.update_version:
            sub = QLabel(f"v{self.pkg.version}  →  v{self.pkg.update_version}")
            sub.setStyleSheet("color:#fb923c;font-size:11px;background:transparent;"
                              "font-family:'JetBrains Mono',monospace;")
        else:
            d = self.pkg.description[:58] + ("…" if len(self.pkg.description)>58 else "")
            sub = QLabel(d or self.pkg.version); sub.setObjectName("package_desc")
        info.addWidget(sub)
        lay.addLayout(info, 1)

        if self._update:
            btn = QPushButton("Güncelle"); btn.setObjectName("update_btn")
            btn.clicked.connect(lambda: self.action.emit(self.pkg, "update"))
            btn.setFixedWidth(96); btn.setFixedHeight(32)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            lay.addWidget(btn)
        elif self.pkg.installed:
            # Kuruluysa: "Aç" + "Kaldır" yan yana
            open_btn = QPushButton("▶  Aç"); open_btn.setObjectName("open_btn")
            open_btn.setFixedWidth(72); open_btn.setFixedHeight(32)
            open_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            open_btn.clicked.connect(lambda: self.action.emit(self.pkg, "open"))
            lay.addWidget(open_btn)

            rm_btn = QPushButton("Kaldır"); rm_btn.setObjectName("remove_btn")
            rm_btn.setFixedWidth(80); rm_btn.setFixedHeight(32)
            rm_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            rm_btn.clicked.connect(self._on_click)
            lay.addWidget(rm_btn)
        else:
            btn = QPushButton("Kur"); btn.setObjectName("install_btn")
            btn.setFixedWidth(96); btn.setFixedHeight(32)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(self._on_click)
            lay.addWidget(btn)

    def _on_click(self):
        action = "remove" if self.pkg.installed else "install"
        if action == "remove":
            dlg = QMessageBox()
            dlg.setWindowTitle("Paket Kaldır")
            dlg.setText(f"<b>{self.pkg.display_name}</b> kaldırılsın mı?")
            dlg.setInformativeText("Bu işlem geri alınamaz.")
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
            dlg.button(QMessageBox.StandardButton.Yes).setText("Kaldır")
            dlg.button(QMessageBox.StandardButton.Cancel).setText("İptal")
            dlg.setStyleSheet(
                "QMessageBox{background:#0d1526;color:#e2e8f8;}"
                "QLabel{color:#e2e8f8;background:transparent;}"
                "QPushButton{background:#172035;color:#e2e8f8;border:1px solid #1e2d45;"
                "border-radius:6px;padding:6px 18px;min-width:70px;}"
                "QPushButton:hover{background:#f97316;border-color:#f97316;color:white;}")
            if dlg.exec() != QMessageBox.StandardButton.Yes:
                return
        self.action.emit(self.pkg, action)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # Çift tık için bekle — timer dolunca detay açılır
            self._pending_click = True
            self._click_timer.start()
        elif e.button() == Qt.MouseButton.MiddleButton:
            # Orta tık: hızlı kur/kaldır (çift tıkın alternatifi)
            action = "remove" if self.pkg.installed else "install"
            self.action.emit(self.pkg, action)
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            # Çift tık geldi — timer'ı iptal et, detay açılmasın
            self._click_timer.stop()
            self._pending_click = False
            # Hızlı kur/kaldır (onaysız)
            action = "remove" if self.pkg.installed else "install"
            self.action.emit(self.pkg, action)
        super().mouseDoubleClickEvent(e)

    def contextMenuEvent(self, e):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#0d1526;border:1px solid #1e2d45;border-radius:8px;"
            "color:#e2e8f8;font-size:13px;padding:4px;}"
            "QMenu::item{padding:7px 20px;border-radius:5px;}"
            "QMenu::item:selected{background:#172035;color:#f97316;}"
            "QMenu::separator{height:1px;background:#1e2d45;margin:3px 8px;}")
        if self.pkg.installed:
            act_main = menu.addAction("✕  Kaldır")
            act_main.triggered.connect(lambda: self._on_click())
        else:
            act_main = menu.addAction("↓  Kur")
            act_main.triggered.connect(lambda: self._on_click())

        # Beğenilenlere ekle / çıkar
        is_fav = self.favorite_requested is not None and hasattr(self, '_is_fav') and self._is_fav
        fav_label = "★  Beğenilenlerden Çıkar" if is_fav else "☆  Beğenilenlere Ekle"
        act_fav = menu.addAction(fav_label)
        act_fav.triggered.connect(lambda: self.favorite_requested.emit(self.pkg))

        # Kuyruğa ekle
        act_queue = menu.addAction("⊕  İndirme Kuyruğuna Ekle")
        act_queue.triggered.connect(lambda: self.queue_requested.emit(self.pkg))

        menu.addSeparator()
        act_detail = menu.addAction("⊡  Detayları Göster")
        act_detail.triggered.connect(lambda: self.detail_requested.emit(self.pkg))
        act_compare = menu.addAction("⇔  Karşılaştırmaya Ekle")
        act_compare.triggered.connect(lambda: self.compare_requested.emit(self.pkg))
        menu.addSeparator()
        act_copy_name = menu.addAction("⎘  İsmi Kopyala")
        act_copy_name.triggered.connect(self._copy_name)
        act_copy_ver = menu.addAction("⎘  Sürümü Kopyala")
        act_copy_ver.triggered.connect(self._copy_version)
        menu.exec(e.globalPos())

    def _copy_name(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.pkg.name)

    def _copy_version(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.pkg.version)


# ─── Category Icon ────────────────────────────────────────────────────────────

class CategoryIcon(QWidget):
    def __init__(self, kind: str, color: str, size: int = 48, parent=None):
        super().__init__(parent)
        self._kind=kind; self._color=QColor(color); self._sz=size
        self.setFixedSize(size, size)

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s=self._sz; c=self._color; pw=max(2,s//20)
        pen=QPen(c,pw,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush); m=s*0.14

        if self._kind=="gaming":
            p.drawRoundedRect(QRectF(m,s*0.3,s-m*2,s*0.42),s*0.1,s*0.1)
            cx,cy,hw=s*0.32,s*0.52,s*0.07
            p.drawLine(QPointF(cx-hw,cy),QPointF(cx+hw,cy))
            p.drawLine(QPointF(cx,cy-hw),QPointF(cx,cy+hw))
            for bx,by in [(s*0.68,s*0.46),(s*0.74,s*0.54),(s*0.62,s*0.54)]:
                p.drawEllipse(QPointF(bx,by),s*0.04,s*0.04)
        elif self._kind=="audio":
            p.drawEllipse(QRectF(m,s*0.6,s*0.28,s*0.22))
            p.drawLine(QPointF(m+s*0.28,s*0.71),QPointF(m+s*0.28,s*0.22))
            fp=QPainterPath(); fp.moveTo(m+s*0.28,s*0.22)
            fp.cubicTo(m+s*0.5,s*0.14,m+s*0.55,s*0.32,m+s*0.28,s*0.38); p.drawPath(fp)
            p.drawEllipse(QRectF(s*0.52,s*0.6,s*0.26,s*0.20))
            p.drawLine(QPointF(s*0.78,s*0.70),QPointF(s*0.78,s*0.22))
            p.drawLine(QPointF(m+s*0.28,s*0.22),QPointF(s*0.78,s*0.22))
        elif self._kind=="dev":
            p.setPen(QPen(c,max(3,s//14),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            for pts in [[(s*0.28,s*0.3),(s*0.14,s*0.5)],[(s*0.14,s*0.5),(s*0.28,s*0.7)],
                        [(s*0.72,s*0.3),(s*0.86,s*0.5)],[(s*0.86,s*0.5),(s*0.72,s*0.7)]]:
                p.drawLine(QPointF(*pts[0]),QPointF(*pts[1]))
            dc=QColor(c); dc.setAlpha(160); p.setPen(QPen(dc,pw))
            p.drawLine(QPointF(s*0.58,s*0.26),QPointF(s*0.42,s*0.74))
        elif self._kind=="graphics":
            p.drawEllipse(QRectF(m,m,s-m*2,s-m*2))
            for dx,dy in [(s*0.25,s*0.25),(s*0.5,s*0.18),(s*0.72,s*0.3),(s*0.78,s*0.52)]:
                fc=QColor(c); fc.setAlpha(200); p.setBrush(QBrush(fc)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(dx,dy),s*0.05,s*0.05)
            p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(pen)
        elif self._kind=="internet":
            p.drawEllipse(QRectF(m,m,s-m*2,s-m*2))
            p.drawLine(QPointF(s/2,m),QPointF(s/2,s-m))
            p.drawLine(QPointF(m,s/2),QPointF(s-m,s/2))
            p.drawArc(QRectF(s*0.25,m,s*0.5,s-m*2),0,180*16)
            dc=QColor(c); dc.setAlpha(100); p.setPen(QPen(dc,pw))
            p.drawArc(QRectF(s*0.25,m,s*0.5,s-m*2),180*16,180*16)
        elif self._kind=="system":
            teeth=8; outer=s*0.38; tooth_h=s*0.09; cx2=s/2; cy2=s/2
            gear=QPainterPath()
            for i in range(teeth*2):
                ang=(i/(teeth*2))*2*math.pi; r=outer if i%2==0 else outer-tooth_h
                gear.moveTo(cx2+math.cos(ang)*r,cy2+math.sin(ang)*r) if i==0 \
                    else gear.lineTo(cx2+math.cos(ang)*r,cy2+math.sin(ang)*r)
            gear.closeSubpath()
            fc=QColor(c); fc.setAlpha(30); p.setBrush(QBrush(fc)); p.setPen(pen)
            p.drawPath(gear); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(cx2,cy2),s*0.12,s*0.12)
        elif self._kind=="office":
            dw,dh=s*0.52,s*0.62; dx2=(s-dw)/2; dy2=(s-dh)/2; fold=dw*0.28
            doc=QPainterPath()
            doc.moveTo(dx2,dy2); doc.lineTo(dx2+dw-fold,dy2)
            doc.lineTo(dx2+dw,dy2+fold); doc.lineTo(dx2+dw,dy2+dh)
            doc.lineTo(dx2,dy2+dh); doc.closeSubpath()
            fc=QColor(c); fc.setAlpha(28); p.setBrush(QBrush(fc)); p.setPen(pen)
            p.drawPath(doc)
            for ly in [0.38,0.48,0.58,0.68]:
                p.drawLine(QPointF(dx2+dw*0.18,s*ly),QPointF(dx2+dw*0.82,s*ly))
        elif self._kind=="security":
            sh=QPainterPath(); sh.moveTo(s/2,m); sh.lineTo(s-m,s*0.3)
            sh.lineTo(s-m,s*0.55); sh.cubicTo(s-m,s*0.78,s/2,s*0.9,s/2,s*0.9)
            sh.cubicTo(m,s*0.9,m,s*0.78,m,s*0.55); sh.lineTo(m,s*0.3); sh.closeSubpath()
            fc=QColor(c); fc.setAlpha(30); p.setBrush(QBrush(fc)); p.setPen(pen)
            p.drawPath(sh)
            ck=QPen(c,max(3,s//13),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)
            p.setPen(ck); p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawLine(QPointF(s*0.36,s*0.54),QPointF(s*0.46,s*0.65))
            p.drawLine(QPointF(s*0.46,s*0.65),QPointF(s*0.64,s*0.42))
        p.end()


# ─── Category Card ────────────────────────────────────────────────────────────

class CategoryCard(QWidget):
    def __init__(self, kind: str, name: str, color: str, count: str = ""):
        super().__init__()
        self._color=QColor(color); self._hover=0; self._hovering=False
        self._timer=QTimer(self); self._timer.timeout.connect(self._tick)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(120)
        lay=QVBoxLayout(self); lay.setContentsMargins(20,18,20,14); lay.setSpacing(8)
        top=QHBoxLayout(); top.addWidget(CategoryIcon(kind,color,46)); top.addStretch()
        if count:
            cnt=QLabel(count)
            cnt.setStyleSheet(f"color:{color}77;font-size:11px;background:transparent;"
                              f"font-family:'JetBrains Mono',monospace;")
            top.addWidget(cnt)
        lay.addLayout(top); lay.addStretch()
        nm=QLabel(name)
        nm.setStyleSheet(f"color:{color};font-size:14px;font-weight:600;background:transparent;")
        lay.addWidget(nm)

    def enterEvent(self, e): self._hovering=True;  self._timer.start(16); super().enterEvent(e)
    def leaveEvent(self, e): self._hovering=False; self._timer.start(16); super().leaveEvent(e)

    def _tick(self):
        target=255 if self._hovering else 0; diff=target-self._hover
        step=int(diff*0.18) or (1 if diff>0 else -1 if diff<0 else 0)
        self._hover=max(0,min(255,self._hover+step)); self.update()
        if self._hover==target: self._timer.stop()

    def paintEvent(self, _):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height(); c=self._color
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c.red(),c.green(),c.blue(),16+int(self._hover*0.06))))
        p.drawRoundedRect(QRectF(0,0,w,h),14,14)
        if self._hover>0:
            tg=QLinearGradient(0,0,0,h*0.5)
            tg.setColorAt(0,QColor(c.red(),c.green(),c.blue(),int(self._hover*0.10)))
            tg.setColorAt(1,QColor(c.red(),c.green(),c.blue(),0))
            p.setBrush(QBrush(tg)); p.drawRoundedRect(QRectF(0,0,w,h),14,14)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(c.red(),c.green(),c.blue(),48+int(self._hover*0.6)),1))
        p.drawRoundedRect(QRectF(0.5,0.5,w-1,h-1),14,14)
        p.end()


class BandwidthGraph(QWidget):
    """İndirme sırasında anlık hız grafiği (QPainter)"""
    MAX_POINTS = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self._samples: list[float] = []   # MB/s
        self._peak = 0.0
        self._timer = QTimer(self); self._timer.timeout.connect(self._sample)
        self._net_prev: tuple[int, int] | None = None

    def start(self):
        self._samples.clear(); self._peak = 0.0; self._net_prev = None
        self._timer.start(500)

    def stop(self):
        self._timer.stop()

    def _sample(self):
        try:
            import psutil
            c = psutil.net_io_counters()
            now = (c.bytes_recv, c.bytes_sent)
            if self._net_prev:
                dl = max(0, now[0] - self._net_prev[0]) / (0.5 * 1024 * 1024)
                self._samples.append(dl)
                if len(self._samples) > self.MAX_POINTS:
                    self._samples.pop(0)
                self._peak = max(self._peak, dl)
            self._net_prev = now
        except Exception:
            pass
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        # Arka plan
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#0a1020")))
        p.drawRoundedRect(QRectF(0, 0, w, h), 6, 6)

        samples = self._samples
        if len(samples) < 2:
            p.setPen(QPen(QColor("#2e3a55")))
            f = QFont("JetBrains Mono", 9); p.setFont(f)
            p.drawText(QRect(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, "Bant genişliği bekleniyor…")
            p.end(); return

        peak = self._peak or 1.0
        # Dolgu
        path = QPainterPath()
        px = w / (self.MAX_POINTS - 1)
        pts = [(i * px, h - 6 - (s / peak) * (h - 12)) for i, s in enumerate(
            [0.0] * (self.MAX_POINTS - len(samples)) + samples)]
        path.moveTo(pts[0][0], h - 4)
        for x, y in pts:
            path.lineTo(x, y)
        path.lineTo(pts[-1][0], h - 4); path.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor(249, 115, 22, 100))
        grad.setColorAt(1, QColor(249, 115, 22, 10))
        p.fillPath(path, QBrush(grad))
        # Çizgi
        pen = QPen(QColor("#f97316"), 1.5)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        lp = QPainterPath()
        lp.moveTo(*pts[0])
        for x, y in pts[1:]: lp.lineTo(x, y)
        p.drawPath(lp)
        # Anlık hız etiketi
        cur = samples[-1]
        label = f"{cur:.1f} MB/s" if cur >= 1 else f"{cur*1024:.0f} KB/s"
        p.setPen(QPen(QColor("#fb923c")))
        f2 = QFont("JetBrains Mono", 8); p.setFont(f2)
        p.drawText(QRect(w-80, 2, 76, 14),
                   Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)
        p.end()


# ─── Action Drawer (right-sliding panel) ──────────────────────────────────────

class ActionWorker(QThread):
    line = pyqtSignal(str); done = pyqtSignal(bool, str)
    def __init__(self, hub, pkg, action):
        super().__init__(); self.hub=hub; self.pkg=pkg; self.action=action
    def run(self):
        cb = lambda l: self.line.emit(l)
        if self.action in ("install", "update"):
            ok, msg = self.hub.install(self.pkg, cb)
        elif self.action == "remove":
            ok, msg = self.hub.remove(self.pkg, cb)
        elif self.action == "open":
            import subprocess, shutil, os
            from backend.managers import PackageSource
            self.line.emit(f"🚀 Açılıyor: {self.pkg.display_name}\n")

            # AppImage: ~/.local/share/AppImages/ içinde ara
            if self.pkg.source == PackageSource.APPIMAGE:
                ai_dir = os.path.expanduser("~/.local/share/AppImages")
                if os.path.exists(ai_dir):
                    # İsim eşleştirme — display_name ve name her ikisini de dene
                    candidates = [
                        self.pkg.name.lower().replace(" ","").replace("-",""),
                        (self.pkg.display_name or "").lower().replace(" ","").replace("-",""),
                    ]
                    for f in sorted(os.listdir(ai_dir)):
                        if not f.endswith(".AppImage"): continue
                        fname = f.lower().replace(".appimage","").replace("-","").replace("_","")
                        if any(c and (c in fname or fname in c) for c in candidates):
                            path = os.path.join(ai_dir, f)
                            self.line.emit(f"📂 {path}\n")
                            # FUSE_yoksa APPIMAGE_EXTRACT_AND_RUN=1 env ile çalıştır
                            env = os.environ.copy()
                            env["APPIMAGE_EXTRACT_AND_RUN"] = "1"
                            subprocess.Popen([path], start_new_session=True, env=env)
                            self.done.emit(True, f"Açıldı: {f}"); return
                self.line.emit(f"❌ AppImage dosyası bulunamadı: {ai_dir}\n")
                self.done.emit(False, "AppImage bulunamadı"); return

            # Pacman/AUR: komut adıyla çalıştır
            pkg_cmd = self.pkg.name.lower()
            if shutil.which(pkg_cmd):
                subprocess.Popen([pkg_cmd], start_new_session=True)
                ok, msg = True, f"{pkg_cmd} başlatıldı."
            else:
                # Flatpak: flatpak run com.example.App
                if self.pkg.source == PackageSource.FLATPAK:
                    subprocess.Popen(["flatpak", "run", self.pkg.name], start_new_session=True)
                    ok, msg = True, f"flatpak run {self.pkg.name}"
                else:
                    # Son çare: xdg-open
                    subprocess.Popen(["xdg-open", pkg_cmd], start_new_session=True)
                    ok, msg = True, f"xdg-open ile açıldı."
            self.line.emit(f"✅ {msg}\n")
        else:
            ok, msg = False, f"Bilinmeyen aksiyon: {self.action}"
        self.done.emit(ok, msg)



class ActionDrawer(QWidget):
    W = 420

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("action_drawer")
        self._offset = self.W  # 0=visible, W=off-screen right
        self._target = self.W
        self._worker: QThread | None = None
        self._hub: PackageManagerHub | None = None
        self._timer = QTimer(self); self._timer.timeout.connect(self._step)
        self._build()
        self.hide()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(24,20,24,20); lay.setSpacing(14)

        # Header
        hdr = QHBoxLayout(); hdr.setSpacing(12)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(46, 46)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setStyleSheet(
            "background:#101828;border-radius:11px;color:#e2e8f8;font-size:14px;font-weight:700;")
        hdr.addWidget(self._icon_lbl)

        title_col = QVBoxLayout(); title_col.setSpacing(3)
        self._title_lbl = QLabel("İşlem")
        self._title_lbl.setStyleSheet("color:white;font-size:16px;font-weight:700;background:transparent;")
        self._pkg_lbl = QLabel("")
        self._pkg_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
        title_col.addWidget(self._title_lbl); title_col.addWidget(self._pkg_lbl)
        hdr.addLayout(title_col, 1)

        close_btn = QPushButton("✕"); close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(
            "QPushButton{background:#101828;color:#6b7a99;border:1px solid rgba(255,255,255,0.06);"
            "border-radius:8px;font-size:13px;}"
            "QPushButton:hover{background:#172035;color:#e2e8f8;}")
        close_btn.clicked.connect(self.slide_out)
        hdr.addWidget(close_btn)
        lay.addLayout(hdr)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame{color:rgba(255,255,255,0.06);}"); lay.addWidget(sep)

        # Progress
        self._prog = QProgressBar(); self._prog.setRange(0, 0)
        lay.addWidget(self._prog)

        # Bant genişliği grafiği
        self._bw_graph = BandwidthGraph()
        lay.addWidget(self._bw_graph)

        # Terminal
        self._term = QTextEdit(); self._term.setReadOnly(True)
        lay.addWidget(self._term, 1)

        # Finish button
        self._finish_btn = QPushButton("Tamamlandı")
        self._finish_btn.setObjectName("install_btn")
        self._finish_btn.setEnabled(False)
        self._finish_btn.clicked.connect(self.slide_out)
        lay.addWidget(self._finish_btn)

    def start(self, pkg: Package, action: str, hub: PackageManagerHub):
        self._hub = hub
        verb = {"install":"Kuruluyor","remove":"Kaldırılıyor","update":"Güncelleniyor"}.get(action,action)
        self._title_lbl.setText(verb)
        self._pkg_lbl.setText(pkg.display_name)

        # Update icon
        px = load_app_icon(pkg.name, 40)
        if px:
            self._icon_lbl.setPixmap(px); self._icon_lbl.setText("")
            self._icon_lbl.setStyleSheet("background:#101828;border-radius:11px;")
        else:
            self._icon_lbl.setPixmap(QPixmap())
            fg, bg = _FALLBACK.get(pkg.name.lower(), (pkg.icon_color, "#101828"))
            self._icon_lbl.setText(pkg.icon_letter.upper()[:2])
            self._icon_lbl.setStyleSheet(
                f"background:{bg};border-radius:11px;color:{fg};font-size:15px;font-weight:700;")

        self._prog.setRange(0, 0)
        self._prog.setStyleSheet("")
        self._term.clear()
        self._finish_btn.setEnabled(False); self._finish_btn.setText("Tamamlandı")
        self._bw_graph.start()

        # Önceki sinyal bağlantılarını temizle (birikim önleme)
        try:
            self._finish_btn.clicked.disconnect()
        except TypeError:
            pass
        self._finish_btn.clicked.connect(self.slide_out)

        if self._worker and self._worker.isRunning():
            self._worker.quit(); self._worker.wait(200)

        self._worker = ActionWorker(hub, pkg, action)
        # Önceki bağlantıları temizle
        try: self._worker.line.disconnect()
        except TypeError: pass
        try: self._worker.done.disconnect()
        except TypeError: pass
        self._worker.line.connect(self._append)
        self._worker.done.connect(self._finish)
        self._worker.start()

    def _append(self, text: str):
        self._term.append(text.rstrip())
        self._term.verticalScrollBar().setValue(self._term.verticalScrollBar().maximum())

    def _finish(self, ok: bool, msg: str):
        self._prog.setRange(0, 100); self._prog.setValue(100)
        self._bw_graph.stop()
        if ok:
            self._append("\n✅ İşlem başarıyla tamamlandı!")
        else:
            self._append(f"\n❌ Hata: {msg}")
            self._prog.setStyleSheet("QProgressBar::chunk{background:#dc2626;border-radius:4px;}")
        self._finish_btn.setEnabled(True)

    def slide_in(self):
        self._offset = self.W; self._target = 0
        self.show(); self.raise_(); self._place()
        if ANIMATIONS_ENABLED: self._timer.start(8)
        else: self._offset = 0; self._place()

    def slide_out(self):
        self._target = self.W
        if ANIMATIONS_ENABLED: self._timer.start(8)
        else: self._offset = self.W; self._place(); self.hide()

    def _step(self):
        diff = self._target - self._offset
        step = int(diff * 0.22) or (1 if diff > 0 else -1 if diff < 0 else 0)
        self._offset = max(0, min(self.W, self._offset + step))
        self._place()
        if self._offset == self._target:
            self._timer.stop()
            if self._target == self.W: self.hide()

    def _place(self):
        par = self.parent()
        if par is None: return
        x = par.width() - self.W + self._offset
        self.setGeometry(x, 0, self.W, par.height())

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#0b1120"))
        # Left orange glow border
        g = QLinearGradient(0, 0, 5, 0)
        g.setColorAt(0, QColor(249, 115, 22, 90)); g.setColorAt(1, QColor(249, 115, 22, 0))
        p.fillRect(QRect(0, 0, 5, self.height()), g)
        p.end()


# ─── Workers ─────────────────────────────────────────────────────────────────

class _AURCommentWorker(QThread):
    """AUR'dan son yorumları çek"""
    done = pyqtSignal(list)

    def __init__(self, pkg_name: str):
        super().__init__()
        self.pkg_name = pkg_name

    def run(self):
        try:
            import urllib.request, re
            url = f"https://aur.archlinux.org/packages/{self.pkg_name}"
            req = urllib.request.Request(url, headers={"User-Agent": "arxis/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read().decode(errors="replace")
            # Yorumları parse et
            comments = []
            # <div class="comment-header"> içindeki kullanıcı ve tarih
            blocks = re.findall(
                r'<h4[^>]*class="comment-header"[^>]*>(.*?)</h4>.*?'
                r'<div[^>]*class="article-content"[^>]*>(.*?)</div>',
                html, re.DOTALL)
            for hdr, body in blocks[:5]:
                user_m = re.search(r'href="/account/([^/"]+)', hdr)
                date_m = re.search(r'<span[^>]*title="([^"]+)"', hdr)
                text   = re.sub(r'<[^>]+>', '', body).strip()
                text   = re.sub(r'\s+', ' ', text)
                if text:
                    comments.append({
                        "user": user_m.group(1) if user_m else "?",
                        "date": date_m.group(1)[:10] if date_m else "",
                        "text": text,
                    })
            self.done.emit(comments)
        except Exception:
            self.done.emit([])


class SearchWorker(QThread):
    done = pyqtSignal(list)
    def __init__(self, hub, query, sources=None):
        super().__init__(); self.hub=hub; self.query=query; self.sources=sources
    def run(self): self.done.emit(self.hub.search_all(self.query, self.sources))


class UpdateCheckWorker(QThread):
    """Her 30 dakikada bir arka planda güncelleme kontrolü"""
    updates_found = pyqtSignal(int)   # güncelleme sayısı
    def __init__(self, hub): super().__init__(); self.hub=hub; self._stop=False
    def run(self):
        while not self._stop:
            try:
                pkgs = self.hub.get_all_updates()
                if not self._stop:
                    self.updates_found.emit(len(pkgs))
            except Exception:
                pass
            # 30 dakika bekle, 5 sn'lik dilimlerle (durdurulabilsin)
            for _ in range(360):
                if self._stop: return
                self.msleep(5000)
    def stop(self): self._stop = True; self.quit()


class CategorySearchWorker(QThread):
    done  = pyqtSignal(list)
    error = pyqtSignal(str)
    def __init__(self, hub, category):
        super().__init__(); self.hub=hub; self.category=category
    def run(self):
        try:
            self.done.emit(self.hub.search_by_category(self.category))
        except Exception as e:
            self.error.emit(str(e))
            self.done.emit([])


class BulkActionWorker(QThread):
    line = pyqtSignal(str); done = pyqtSignal(list)
    def __init__(self, hub, packages, action):
        super().__init__(); self.hub=hub; self.packages=packages; self.action=action
    def run(self):
        cb = lambda l: self.line.emit(l)
        if self.action == "install":
            results = self.hub.install_multiple(self.packages, cb)
        else:
            results = self.hub.remove_multiple(self.packages, cb)
        self.done.emit(results)


class DetailsWorker(QThread):
    done = pyqtSignal(object)
    def __init__(self, hub, pkg):
        super().__init__(); self.hub=hub; self.pkg=pkg
    def run(self): self.done.emit(self.hub.get_details(self.pkg))


class OrphanWorker(QThread):
    done = pyqtSignal(list)
    def __init__(self, hub): super().__init__(); self.hub=hub
    def run(self): self.done.emit(self.hub.get_orphans())


class MaintenanceWorker(QThread):
    """Güncelleme, orphan temizleme, cache gibi bakım işleri"""
    line = pyqtSignal(str)
    done = pyqtSignal(bool, str)

    def __init__(self, hub, task: str):
        super().__init__(); self.hub=hub; self.task=task

    def run(self):
        cb = lambda l: self.line.emit(l)
        if self.task == "update_pacman":
            ok, msg = self.hub.update_all_pacman(cb)
        elif self.task == "update_aur":
            ok, msg = self.hub.update_all_aur(cb)
        elif self.task == "update_flatpak":
            ok, msg = self.hub.update_all_flatpak(cb)
        elif self.task == "remove_orphans":
            ok, msg = self.hub.remove_orphans(cb)
        elif self.task == "clean_cache":
            ok, msg = self.hub.clean_cache(cb)
        elif self.task == "update_all":
            ok1, m1 = self.hub.update_all_pacman(cb)
            ok2, m2 = self.hub.update_all_aur(cb)
            ok3, m3 = self.hub.update_all_flatpak(cb)
            ok  = ok1 and ok2 and ok3
            msg = "\n".join([m1, m2, m3])
        else:
            ok, msg = False, f"Bilinmeyen görev: {self.task}"
        self.done.emit(ok, msg)


class SystemInfoWorker(QThread):
    done = pyqtSignal(dict)
    def __init__(self, hub): super().__init__(); self.hub=hub
    def run(self): self.done.emit(self.hub.get_system_info())


class GitHubFetchWorker(QThread):
    done = pyqtSignal(list)   # assets list
    error = pyqtSignal(str)
    def __init__(self, url: str):
        super().__init__(); self.url = url
        from backend.managers import GitHubReleaseManager
        self.mgr = GitHubReleaseManager()
    def run(self):
        if self.mgr.is_direct_asset(self.url):
            name = self.url.split("/")[-1]
            self.done.emit([{"name": name, "url": self.url,
                             "size": 0, "tag": "direct", "body": "", "published": ""}])
            return
        parsed = self.mgr.parse_url(self.url)
        if not parsed:
            self.error.emit("Geçerli bir GitHub URL'si giriniz."); return
        owner, repo = parsed
        assets = self.mgr.get_latest_assets(owner, repo)
        if not assets:
            self.error.emit(f"{owner}/{repo} için indirilebilir asset bulunamadı.")
        else:
            self.done.emit(assets)


class GitHubDownloadWorker(QThread):
    line = pyqtSignal(str)
    done = pyqtSignal(bool, str)
    def __init__(self, asset: dict):
        super().__init__(); self.asset = asset
        from backend.managers import GitHubReleaseManager
        self.mgr = GitHubReleaseManager()
    def run(self):
        ok, msg = self.mgr.download_and_install(self.asset, lambda l: self.line.emit(l))
        self.done.emit(ok, msg)


class SnapshotWorker(QThread):
    done = pyqtSignal(bool, str, dict)   # (ok, msg, snapshot)
    def __init__(self, hub, task: str, path: str = "", snapshot: dict = None):
        super().__init__()
        self.hub=hub; self.task=task; self.path=path; self.snapshot=snapshot or {}
        from backend.managers import SnapshotManager
        self.mgr = SnapshotManager()
    def run(self):
        if self.task == "create":
            snap = self.mgr.create_snapshot(self.hub)
            self.done.emit(True, "Snapshot oluşturuldu.", snap)
        elif self.task == "save":
            ok, msg = self.mgr.save(self.snapshot, self.path)
            self.done.emit(ok, msg, self.snapshot)
        elif self.task == "load":
            ok, data = self.mgr.load(self.path)
            self.done.emit(ok, "" if ok else data.get("error",""), data)
        elif self.task == "diff":
            diff = self.mgr.diff(self.snapshot, self.hub)
            self.done.emit(True, "", diff)


# ─── History Manager ──────────────────────────────────────────────────────────

import json, datetime, pathlib

class HistoryManager:
    PATH = pathlib.Path(__file__).parent.parent / "history.json"

    def __init__(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        self._data: list[dict] = []
        self._load()

    def _load(self):
        try:
            if self.PATH.exists():
                self._data = json.loads(self.PATH.read_text(encoding="utf-8"))
        except Exception:
            self._data = []

    def _save(self):
        try:
            self.PATH.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except Exception:
            pass

    def record(self, pkg_name: str, pkg_version: str,
               source: str, action: str, success: bool):
        entry = {
            "ts":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action":  action,          # install / remove / update
            "name":    pkg_name,
            "version": pkg_version,
            "source":  source,
            "success": success,
        }
        self._data.insert(0, entry)
        self._data = self._data[:500]   # max 500 kayıt tut
        self._save()

    def get_all(self) -> list[dict]:
        return list(self._data)

    def clear(self):
        self._data = []; self._save()


class FavoritesManager:
    """Beğenilen paketleri JSON'da saklar"""
    PATH = pathlib.Path.home() / ".config" / "arxis" / "favorites.json"

    def __init__(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        self._data: list[dict] = []
        self._load()

    def _load(self):
        try:
            if self.PATH.exists():
                self._data = json.loads(self.PATH.read_text(encoding="utf-8"))
        except Exception:
            self._data = []

    def _save(self):
        try:
            self.PATH.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except Exception:
            pass

    def add(self, pkg) -> bool:
        """Paketi beğenilenlere ekle. Zaten varsa False döner."""
        key = f"{pkg.source.value}:{pkg.name}"
        if any(e["key"] == key for e in self._data):
            return False
        self._data.insert(0, {
            "key":     key,
            "name":    pkg.name,
            "display": pkg.display_name,
            "source":  pkg.source.value,
            "version": pkg.version,
            "desc":    pkg.description[:120],
            "color":   pkg.icon_color,
            "ts":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._save(); return True

    def remove(self, pkg) -> bool:
        key = f"{pkg.source.value}:{pkg.name}"
        before = len(self._data)
        self._data = [e for e in self._data if e["key"] != key]
        if len(self._data) < before:
            self._save(); return True
        return False

    def is_favorite(self, pkg) -> bool:
        key = f"{pkg.source.value}:{pkg.name}"
        return any(e["key"] == key for e in self._data)

    def get_all(self) -> list[dict]:
        return list(self._data)

    def clear(self):
        self._data = []; self._save()


class DownloadQueue:
    """İndirme kuyruğu — paketleri sıraya al, sonra toplu kur"""
    PATH = pathlib.Path.home() / ".config" / "arxis" / "queue.json"

    def __init__(self):
        self.PATH.parent.mkdir(parents=True, exist_ok=True)
        self._data: list[dict] = []
        self._load()

    def _load(self):
        try:
            if self.PATH.exists():
                self._data = json.loads(self.PATH.read_text(encoding="utf-8"))
        except Exception:
            self._data = []

    def _save(self):
        try:
            self.PATH.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except Exception:
            pass

    def add(self, pkg) -> bool:
        key = f"{pkg.source.value}:{pkg.name}"
        if any(e["key"] == key for e in self._data):
            return False
        self._data.append({
            "key":     key,
            "name":    pkg.name,
            "display": pkg.display_name,
            "source":  pkg.source.value,
            "version": pkg.version,
            "desc":    pkg.description[:120],
            "color":   pkg.icon_color,
            "url":     getattr(pkg, "url", ""),
        })
        self._save(); return True

    def remove_by_key(self, key: str):
        self._data = [e for e in self._data if e["key"] != key]
        self._save()

    def get_all(self) -> list[dict]:
        return list(self._data)

    def clear(self):
        self._data = []; self._save()

    def count(self) -> int:
        return len(self._data)


class UpdatesWorker(QThread):
    done = pyqtSignal(list)
    def __init__(self, hub): super().__init__(); self.hub=hub
    def run(self): self.done.emit(self.hub.get_all_updates())



# ─── Bildirim Yöneticisi ──────────────────────────────────────────────────────

class NotificationToast(QWidget):
    """Sağ üstte beliren bildirim baloncuğu"""
    def __init__(self, message: str, success: bool = True, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(360)
        self._alpha = 0; self._target = 220; self._closing = False
        self._alive = True   # deleteLater öncesi False yapılır
        self._timer = QTimer(self); self._timer.timeout.connect(self._tick); self._timer.start(16)
        QTimer.singleShot(3500, self._start_close)

        color = "#3fb950" if success else "#f85149"
        bg    = "#0f2a10" if success else "#2a0f0f"
        icon  = "✓" if success else "✗"

        lay = QHBoxLayout(self); lay.setContentsMargins(14,12,14,12); lay.setSpacing(10)
        ic = QLabel(icon)
        ic.setStyleSheet(f"color:{color};font-size:16px;font-weight:bold;background:transparent;")
        ic.setFixedWidth(20)
        lay.addWidget(ic)
        msg = QLabel(message); msg.setWordWrap(True)
        msg.setStyleSheet(f"color:{color};font-size:13px;background:transparent;")
        lay.addWidget(msg, 1)
        self._bg = bg; self._color = color

    def is_alive(self) -> bool:
        return self._alive

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self._bg); c.setAlpha(self._alpha)
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 10, 10)
        bc = QColor(self._color); bc.setAlpha(int(self._alpha * 0.4))
        p.setBrush(Qt.BrushStyle.NoBrush); p.setPen(QPen(bc, 1))
        p.drawRoundedRect(QRectF(0.5,0.5,self.width()-1,self.height()-1), 10, 10)
        p.end()

    def _tick(self):
        diff = self._target - self._alpha
        step = max(1, int(abs(diff) * 0.18))
        self._alpha += step if diff > 0 else -step
        self._alpha = max(0, min(255, self._alpha))
        self.update()
        if self._alpha == self._target: self._timer.stop()
        if self._closing and self._alpha == 0:
            self._alive = False
            self._timer.stop()
            self.hide()
            self.deleteLater()

    def _start_close(self):
        self._closing = True; self._target = 0; self._timer.start(16)


class NotificationManager:
    """Bildirimleri sağ üst köşede yönetir"""
    def __init__(self, parent: QWidget):
        self._parent  = parent
        self._toasts: list[NotificationToast] = []
        self._enabled = True   # ayarlardan kontrol edilir

    def show(self, message: str, success: bool = True):
        if not self._enabled:
            return
        toast = NotificationToast(message, success, self._parent)
        toast.show()
        self._toasts.append(toast)
        self._reposition()
        toast.destroyed.connect(lambda: QTimer.singleShot(150, self._reposition))

    def _reposition(self):
        # Sadece Python tarafı hâlâ canlı olan toast'ları tut
        self._toasts = [t for t in self._toasts if t.is_alive()]
        par = self._parent
        y = 80
        for toast in reversed(self._toasts):
            toast.adjustSize()
            x = par.width() - toast.width() - 20
            toast.move(x, y)
            y += toast.height() + 8


# ─── Paket Detay Paneli ───────────────────────────────────────────────────────

class PackageDetailPage(QWidget):
    """Sol tıkla açılan tam ekran paket detay sayfası"""
    action            = pyqtSignal(object, str)
    compare_requested = pyqtSignal(object)
    back_requested    = pyqtSignal()

    def __init__(self, hub):
        super().__init__()
        self.hub = hub
        self._pkg = None
        self._details_worker = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)

        # Üst başlık barı
        hdr = QFrame(); hdr.setObjectName("glass_panel")
        hdr.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hdr.setFixedHeight(64)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24, 12, 24, 12); hl.setSpacing(14)

        back_btn = QPushButton("← Geri")
        back_btn.setObjectName("open_btn"); back_btn.setFixedHeight(34)
        back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_btn.clicked.connect(self.back_requested.emit)
        hl.addWidget(back_btn)

        self._hdr_icon = AppIconWidget("", "?", "#2563eb", 40)
        hl.addWidget(self._hdr_icon)

        title_col = QVBoxLayout(); title_col.setSpacing(2)
        self._hdr_name = QLabel("—")
        self._hdr_name.setStyleSheet("color:white;font-size:17px;font-weight:700;background:transparent;")
        self._hdr_ver = QLabel("")
        self._hdr_ver.setStyleSheet("color:#6b7a99;font-size:11px;background:transparent;"
                                     "font-family:'JetBrains Mono',monospace;")
        title_col.addWidget(self._hdr_name); title_col.addWidget(self._hdr_ver)
        hl.addLayout(title_col, 1)

        # U-7: SourceTag placeholder — show_package'de yenilenir
        self._hdr_source = SourceTag(PackageSource.PACMAN)
        self._hdr_source_idx = hl.count()   # SourceTag'in layout index'ini kaydet
        hl.addWidget(self._hdr_source)
        self._hdr_layout = hl   # show_package'de erişmek için ref sakla

        self._action_btn = QPushButton("Kur")
        self._action_btn.setObjectName("install_btn")
        self._action_btn.setFixedHeight(36); self._action_btn.setFixedWidth(110)
        self._action_btn.clicked.connect(self._on_action)
        hl.addWidget(self._action_btn)

        self._open_btn = QPushButton("▶  Aç")
        self._open_btn.setObjectName("open_btn")
        self._open_btn.setFixedHeight(36); self._open_btn.setFixedWidth(80)
        self._open_btn.clicked.connect(lambda: self.action.emit(self._pkg, "open"))
        self._open_btn.hide()   # sadece kuruluyken göster
        hl.addWidget(self._open_btn)

        self._cmp_btn = QPushButton("⇔ Karşılaştır")
        self._cmp_btn.setObjectName("open_btn")
        self._cmp_btn.setFixedHeight(36)
        self._cmp_btn.clicked.connect(lambda: self.compare_requested.emit(self._pkg))
        hl.addWidget(self._cmp_btn)

        lay.addWidget(hdr)

        # Scroll alanı
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:#070b14;}")

        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._body = QVBoxLayout(body); self._body.setContentsMargins(28, 24, 28, 32)
        self._body.setSpacing(18)
        scroll.setWidget(body)
        lay.addWidget(scroll, 1)

    def show_package(self, pkg, hub=None):
        self._pkg = pkg
        if hub: self.hub = hub

        # Header güncelle
        self._hdr_icon.update_pkg(pkg.name, pkg.icon_letter, pkg.icon_color)
        self._hdr_name.setText(pkg.display_name)
        self._hdr_ver.setText(f"v{pkg.version}  ·  {pkg.source.value.upper()}")

        # U-7: SourceTag'i yerinde güncelle — setParent(None) yerine yeni tag ekle
        old_tag = self._hdr_source
        new_tag = SourceTag(pkg.source)
        self._hdr_layout.replaceWidget(old_tag, new_tag)
        old_tag.deleteLater()
        self._hdr_source = new_tag

        if pkg.installed:
            self._action_btn.setText("Kaldır"); self._action_btn.setObjectName("remove_btn")
            self._open_btn.show()
        else:
            self._action_btn.setText("Kur"); self._action_btn.setObjectName("install_btn")
            self._open_btn.hide()
        self._action_btn.style().unpolish(self._action_btn)
        self._action_btn.style().polish(self._action_btn)

        # AppImage için "GitHub URL ile Kur" butonu — varsa göster
        from backend.managers import PackageSource as _PS
        if hasattr(self, '_gh_url_btn'):
            self._gh_url_btn.setParent(None)
            del self._gh_url_btn
        if pkg.source == _PS.APPIMAGE and not pkg.installed:
            self._gh_url_btn = QPushButton("🔗 GitHub URL ile Kur")
            self._gh_url_btn.setObjectName("open_btn")
            self._gh_url_btn.setFixedHeight(36)
            self._gh_url_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._gh_url_btn.setToolTip("GitHub releases URL'si yapıştırın")
            self._gh_url_btn.clicked.connect(lambda: self._ask_github_url(pkg))
            self._hdr_layout.insertWidget(self._hdr_layout.count() - 1, self._gh_url_btn)

        # Önceki worker'ı iptal et
        if hasattr(self, '_sim_worker') and self._sim_worker:
            try:
                self._sim_worker.done.disconnect()
                if self._sim_worker.isRunning():
                    self._sim_worker.quit()
            except Exception:
                pass
            self._sim_worker = None

        # Önbellek kontrolü
        cache_key = f"{pkg.source.value}:{pkg.name}"
        if hasattr(self, '_pkg_cache') and cache_key in self._pkg_cache:
            self._on_details(self._pkg_cache[cache_key])
            return

        # ── Faz 1: Mevcut bilgileri HEMEN göster ──────────────────────────
        self._on_details(pkg)   # elimizdeki verilerle anında render

        # ── Faz 2: Arka planda eksik detayları çek, gelince güncelle ──────
        # Sadece eksik alan varsa worker başlat
        needs_fetch = not all([pkg.url, pkg.license, pkg.maintainer, pkg.depends])
        if needs_fetch:
            self._details_worker = DetailsWorker(self.hub, pkg)
            self._details_worker.done.connect(self._on_details_enriched)
            self._details_worker.start()

    def _on_details(self, pkg):
        self._pkg = pkg
        # UI önbelleğine kaydet
        if not hasattr(self, '_pkg_cache'):
            self._pkg_cache = {}
        self._pkg_cache[f"{pkg.source.value}:{pkg.name}"] = pkg

        # Body temizle
        while self._body.count():
            w = self._body.takeAt(0)
            if w.widget(): w.widget().deleteLater()

    def _on_details_enriched(self, pkg):
        """Arka planda gelen ek bilgilerle sadece bilgi satırlarını güncelle"""
        self._pkg = pkg
        if not hasattr(self, '_pkg_cache'):
            self._pkg_cache = {}
        self._pkg_cache[f"{pkg.source.value}:{pkg.name}"] = pkg
        # Sadece info_grid etiketlerini güncelle — tam yeniden render yok
        # _info_labels sözlüğüne referans tutuyoruz
        lbl_map = getattr(self, '_info_labels_map', {})
        updates = {
            "Boyut":       pkg.size       or "—",
            "Lisans":      pkg.license    or "—",
            "Geliştirici": pkg.maintainer or "—",
            "Paket Adı":   pkg.name,
            "Sürüm":       pkg.version    or "—",
        }
        for key, val in updates.items():
            lbl = lbl_map.get(key)
            if lbl:
                try:
                    lbl.setText(val)
                    color = "#4ade80" if "✓" in val else "#f87171" if "✗" in val else "#9ba8c0"
                    lbl.setStyleSheet(f"color:{color};font-size:12px;background:transparent;")
                except RuntimeError:
                    pass

        # ── Üst bilgi satırı: ikon büyük + özet ──────────────────────────
        hero = QWidget(); hero.setObjectName("glass_panel")
        hero.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(hero); hl.setContentsMargins(20,16,20,16); hl.setSpacing(18)
        hl.addWidget(AppIconWidget(pkg.name, pkg.icon_letter, pkg.icon_color, 64))
        info_col = QVBoxLayout(); info_col.setSpacing(6)
        name_lbl = QLabel(pkg.display_name)
        name_lbl.setStyleSheet("color:#e2e8f8;font-size:20px;font-weight:700;background:transparent;")
        info_col.addWidget(name_lbl)
        meta_row = QHBoxLayout(); meta_row.setSpacing(10)
        meta_row.addWidget(SourceTag(pkg.source))
        ver_lbl = QLabel(f"v{pkg.version}")
        ver_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;"
                              "font-family:'JetBrains Mono',monospace;")
        meta_row.addWidget(ver_lbl)
        if pkg.size:
            sz_lbl = QLabel(f"· {pkg.size}")
            sz_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
            meta_row.addWidget(sz_lbl)
        if pkg.license:
            lic_lbl = QLabel(f"· {pkg.license}")
            lic_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
            meta_row.addWidget(lic_lbl)
        meta_row.addStretch()
        info_col.addLayout(meta_row)
        if pkg.description:
            short_desc = QLabel(pkg.description[:180] + ("…" if len(pkg.description) > 180 else ""))
            short_desc.setWordWrap(True)
            short_desc.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
            info_col.addWidget(short_desc)
        hl.addLayout(info_col, 1)
        self._body.addWidget(hero)

        # ── Bilgi satırları ───────────────────────────────────────────────
        self._body.addWidget(self._section("ℹ  Paket Bilgisi"))
        info_grid = QGridLayout(); info_grid.setSpacing(6); info_grid.setColumnMinimumWidth(0, 120)
        info_w = QWidget(); info_w.setLayout(info_grid)

        # Kaynak bazlı fallback etiketleri
        src = pkg.source.value
        size_fallback = {
            "pacman": "yükleniyor…",
            "aur":    "AUR'da boyut bilgisi yok",
            "flatpak":"yükleniyor…",
            "appimage":"kurulumdan sonra görünür",
        }.get(src, "—")
        lic_fallback  = {"pacman": "yükleniyor…", "flatpak":"yükleniyor…"}.get(src, "—")
        maint_fallback = {"aur": "yükleniyor…", "flatpak":"yükleniyor…"}.get(src, "—")

        rows = [
            ("Paket Adı",   pkg.name),
            ("Sürüm",       pkg.version or "—"),
            ("Kaynak",      pkg.source.value.upper()),
            ("Boyut",       pkg.size   or size_fallback),
            ("Lisans",      pkg.license or lic_fallback),
            ("Geliştirici", pkg.maintainer or maint_fallback),
            ("Kategori",    pkg.category or "—"),
            ("Durum",       "✓ Yüklü" if pkg.installed else "✗ Yüklü Değil"),
        ]

        self._info_labels_map = {}   # enriched güncelleme için referanslar
        for i, (k, v) in enumerate(rows):
            kl = QLabel(k + ":"); kl.setFixedWidth(120)
            kl.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;"
                             "font-family:'JetBrains Mono',monospace;")
            vl = QLabel(v)
            vl.setStyleSheet(
                f"color:{'#4ade80' if '✓' in v else '#f87171' if '✗' in v else '#9ba8c0'};"
                "font-size:12px;background:transparent;")
            info_grid.addWidget(kl, i, 0); info_grid.addWidget(vl, i, 1)
            self._info_labels_map[k] = vl   # enriched için referans kaydet
        self._body.addWidget(info_w)

        # ── Web sitesi ────────────────────────────────────────────────────
        if pkg.url:
            self._body.addWidget(self._section("🔗 Web Sitesi"))
            url_lbl = QLabel(f'<a href="{pkg.url}" style="color:#60a5fa;">{pkg.url}</a>')
            url_lbl.setOpenExternalLinks(True)
            url_lbl.setStyleSheet("background:transparent;font-size:12px;")
            self._body.addWidget(url_lbl)

        # ── Bağımlılıklar ─────────────────────────────────────────────────
        if pkg.depends:
            self._body.addWidget(self._section(f"📦 Bağımlılıklar ({len(pkg.depends)})"))
            deps_flow = QWidget()
            deps_lay  = QHBoxLayout(deps_flow)
            deps_lay.setContentsMargins(0,0,0,0); deps_lay.setSpacing(6)
            deps_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for dep in pkg.depends[:15]:
                tag = QLabel(dep)
                tag.setStyleSheet(
                    "background:#0d1829;color:#60a5fa;border:1px solid #1e3a5a;"
                    "border-radius:4px;padding:2px 8px;font-size:11px;"
                    "font-family:'JetBrains Mono',monospace;")
                deps_lay.addWidget(tag)
            if len(pkg.depends) > 15:
                more = QLabel(f"  +{len(pkg.depends)-15} daha…")
                more.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;")
                deps_lay.addWidget(more)
            deps_lay.addStretch()
            self._body.addWidget(deps_flow)

        # ── Benzer paketler (lazy) ────────────────────────────────────────
        self._body.addWidget(self._section("🔍 Benzer Paketler"))
        self._similar_lay = QVBoxLayout()
        sim_loading = QLabel("⏳ Yükleniyor…")
        sim_loading.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        self._similar_lay.addWidget(sim_loading)
        sim_w = QWidget(); sim_w.setLayout(self._similar_lay)
        self._body.addWidget(sim_w)
        sim_query = pkg.name.split("-")[0]
        self._sim_worker = SearchWorker(self.hub, sim_query)
        self._sim_worker.done.connect(lambda pkgs, p=pkg: self._show_similar(pkgs, p))
        self._sim_worker.finished.connect(lambda: setattr(self, '_sim_worker', None))
        self._sim_worker.start()

        # ── AUR yorumları ─────────────────────────────────────────────────
        if pkg.source.value == "aur":
            self._body.addWidget(self._section("💬 AUR Yorumları"))
            # Yorum sayısı + link
            aur_w = QWidget(); aur_w.setObjectName("glass_panel")
            aur_w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            aur_lay = QVBoxLayout(aur_w); aur_lay.setContentsMargins(16,12,16,12); aur_lay.setSpacing(8)

            self._aur_comments_lay = QVBoxLayout()
            aur_loading = QLabel("⏳ Yorumlar yükleniyor…")
            aur_loading.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
            self._aur_comments_lay.addWidget(aur_loading)
            aur_lay.addLayout(self._aur_comments_lay)

            more_link = QLabel(
                f'<a href="https://aur.archlinux.org/packages/{pkg.name}#comment-list" '
                f'style="color:#a78bfa;font-size:11px;">Tüm yorumları AUR\'da görüntüle →</a>')
            more_link.setOpenExternalLinks(True)
            more_link.setStyleSheet("background:transparent;")
            aur_lay.addWidget(more_link)
            self._body.addWidget(aur_w)

            # Yorumları arka planda çek
            self._aur_comment_worker = _AURCommentWorker(pkg.name)
            self._aur_comment_worker.done.connect(self._show_aur_comments)
            self._aur_comment_worker.start()

        self._body.addStretch()

    def _show_aur_comments(self, comments: list):
        try:
            _ = self._aur_comments_lay.count()
        except (RuntimeError, AttributeError):
            return
        while self._aur_comments_lay.count():
            w = self._aur_comments_lay.takeAt(0)
            if w.widget(): w.widget().deleteLater()

        if not comments:
            lbl = QLabel("Yorum bulunamadı veya AUR'a bağlanılamadı.")
            lbl.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;"
                              "font-style:italic;")
            self._aur_comments_lay.addWidget(lbl)
            return

        for c in comments[:5]:
            row = QWidget(); rl = QVBoxLayout(row)
            rl.setContentsMargins(0,6,0,6); rl.setSpacing(3)
            top = QHBoxLayout()
            user_lbl = QLabel(c.get("user","?"))
            user_lbl.setStyleSheet("color:#f97316;font-size:11px;font-weight:600;background:transparent;")
            date_lbl = QLabel(c.get("date",""))
            date_lbl.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;")
            top.addWidget(user_lbl); top.addStretch(); top.addWidget(date_lbl)
            body_lbl = QLabel(c.get("text","")[:200] + ("…" if len(c.get("text","")) > 200 else ""))
            body_lbl.setWordWrap(True)
            body_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
            rl.addLayout(top); rl.addWidget(body_lbl)
            # Ayırıcı
            sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("QFrame{color:rgba(255,255,255,0.04);}")
            rl.addWidget(sep)
            self._aur_comments_lay.addWidget(row)

    def _show_similar(self, pkgs, current_pkg):
        # Layout silinmişse (kullanıcı sayfayı değiştirdi) işlem yapma
        try:
            _ = self._similar_lay.count()
        except RuntimeError:
            return

        while self._similar_lay.count():
            w = self._similar_lay.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        shown = 0
        for p in pkgs:
            if p.name == current_pkg.name: continue
            item = PackageItem(p)
            item.action.connect(self.action)
            item.compare_requested.connect(self.compare_requested)
            item.detail_requested.connect(self.show_package)
            self._similar_lay.addWidget(item)
            shown += 1
            if shown >= 4: break
        if shown == 0:
            lbl = QLabel("Benzer paket bulunamadı.")
            lbl.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
            self._similar_lay.addWidget(lbl)

    def _section(self, title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:700;"
                          "background:transparent;margin-top:8px;")
        return lbl

    def _on_action(self):
        if self._pkg:
            action = "remove" if self._pkg.installed else "install"
            self.action.emit(self._pkg, action)

    def _ask_github_url(self, pkg):
        """AppImage için GitHub URL sor — kullanıcı yapıştırır, biz releases'den indiririz"""
        from PyQt6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(
            self,
            "GitHub URL ile Kur",
            f"'{pkg.display_name}' için GitHub repo veya release URL'si:\n"
            f"Örnek: https://github.com/ColinDuquesnoy/MellowPlayer",
            text=pkg.url or f"https://github.com/search?q={pkg.name.replace(' ','+')}")
        if ok and url.strip():
            # URL'yi paketin url alanına set et, sonra install gönder
            pkg.url = url.strip()
            self.action.emit(pkg, "install")


def _make_section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color:#2e3a55;font-size:10px;font-weight:700;"
                      "font-family:'JetBrains Mono',monospace;"
                      "letter-spacing:.08em;text-transform:uppercase;"
                      "background:transparent;")
    return lbl


def _make_glass_panel(title: str):
    """Başlıklı glass panel + içerik layout döndürür: (panel_widget, body_layout)"""
    panel = QWidget(); panel.setObjectName("glass_panel")
    panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    fl = QVBoxLayout(panel); fl.setContentsMargins(16, 14, 16, 14); fl.setSpacing(8)

    hdr = QHBoxLayout()
    lbl = QLabel(title)
    lbl.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
    hdr.addWidget(lbl); hdr.addStretch()
    fl.addLayout(hdr)

    body = QVBoxLayout(); body.setSpacing(0)
    fl.addLayout(body, 1)
    return panel, body


class DiscoverPage(QWidget):
    action            = pyqtSignal(object, str)
    compare_requested = pyqtSignal(object)
    detail_requested  = pyqtSignal(object)

    def __init__(self, hub: PackageManagerHub):
        super().__init__(); self.hub = hub
        self._build(); self._load()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(20)

        # Başlık + yenile butonu
        hdr = QHBoxLayout()
        hdr.addWidget(_make_section_label("Öne Çıkan"))
        hdr.addStretch()
        self._refresh_btn = QPushButton("↺  Yenile")
        self._refresh_btn.setObjectName("open_btn")
        self._refresh_btn.setFixedHeight(28); self._refresh_btn.setFixedWidth(90)
        self._refresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._refresh_btn.clicked.connect(self.refresh)
        hdr.addWidget(self._refresh_btn)
        lay.addLayout(hdr)

        self._feat_row = QHBoxLayout(); self._feat_row.setSpacing(14)
        lay.addLayout(self._feat_row)

        lay.addWidget(_make_section_label("Paket Yönetimi"))
        bottom = QHBoxLayout(); bottom.setSpacing(14)
        self._pop_frame, self._pop_lay = _make_glass_panel("Popüler Paketler")
        self._upd_frame, self._upd_lay = _make_glass_panel("Güncellemeler")
        bottom.addWidget(self._pop_frame, 1); bottom.addWidget(self._upd_frame, 1)
        lay.addLayout(bottom, 1)

    def _clear_all(self):
        """Mevcut içerikleri temizle"""
        while self._feat_row.count():
            item = self._feat_row.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self._pop_lay.count():
            item = self._pop_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        while self._upd_lay.count():
            item = self._upd_lay.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def _load(self):
        for i, pkg in enumerate(self.hub.get_featured()):
            card = FeaturedCard(pkg, i); card.action.connect(self.action)
            self._feat_row.addWidget(card)

        for pkg in self.hub.get_popular():
            item = PackageItem(pkg); item.action.connect(self.action)
            item.compare_requested.connect(self.compare_requested)
            item.detail_requested.connect(self.detail_requested)
            self._pop_lay.addWidget(item)
        self._pop_lay.addStretch()

        self._upd_worker = UpdatesWorker(self.hub)
        self._upd_worker.done.connect(self._on_updates)
        self._upd_worker.start()

    def refresh(self):
        """Her seferinde farklı paketler göster"""
        self._clear_all()
        self._load()

    def _on_updates(self, updates: list):
        for pkg in updates[:6]:
            item = PackageItem(pkg, update_mode=True); item.action.connect(self.action)
            item.compare_requested.connect(self.compare_requested)
            item.detail_requested.connect(self.detail_requested)
            self._upd_lay.addWidget(item)
        self._upd_lay.addStretch()


class SearchPage(QWidget):
    action            = pyqtSignal(object, str)
    compare_requested = pyqtSignal(object)
    detail_requested  = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._all_pkgs: list[Package] = []
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(12)

        self._title = QLabel("Arama Sonuçları"); self._title.setObjectName("section_title")
        lay.addWidget(self._title)

        # ── Filtre + Sıralama satırı ──
        ctrl = QHBoxLayout(); ctrl.setSpacing(8)

        # Kaynak filtre butonları
        self._src_filters: dict[str, QPushButton] = {}
        for src in ("Tümü", "Pacman", "AUR", "Flatpak", "AppImage"):
            b = QPushButton(src); b.setObjectName("filter_btn")
            b.setProperty("active", src == "Tümü")
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.clicked.connect(lambda _, s=src: self._apply_filter(s))
            ctrl.addWidget(b)
            self._src_filters[src] = b

        ctrl.addStretch()

        # Sıralama
        sort_lbl = QLabel("Sırala:")
        sort_lbl.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        ctrl.addWidget(sort_lbl)

        from PyQt6.QtWidgets import QComboBox
        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["İlgililik", "İsim (A-Z)", "Kaynak", "Yüklü önce"])
        self._sort_combo.setFixedWidth(140)
        self._sort_combo.currentIndexChanged.connect(self._apply_filter_current)
        ctrl.addWidget(self._sort_combo)
        lay.addLayout(ctrl)

        # Paket listesi
        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(body); self._list.setSpacing(0); self._list.addStretch()
        scroll = QScrollArea(); scroll.setWidget(body); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        lay.addWidget(scroll, 1)

    def show_results(self, pkgs: list, query: str):
        self._all_pkgs = pkgs
        self._title.setText(f'"{query}" — {len(pkgs)} sonuç')
        for name, btn in self._src_filters.items():
            btn.setProperty("active", name == "Tümü")
            btn.style().unpolish(btn); btn.style().polish(btn)
        self._render(pkgs)

    def _apply_filter(self, src: str):
        for name, btn in self._src_filters.items():
            btn.setProperty("active", name == src)
            btn.style().unpolish(btn); btn.style().polish(btn)
        self._apply_filter_current()

    def _apply_filter_current(self):
        active_src = next((n for n, b in self._src_filters.items()
                           if b.property("active")), "Tümü")
        src_map = {"Pacman": "pacman", "AUR": "aur",
                   "Flatpak": "flatpak", "AppImage": "appimage"}
        pkgs = self._all_pkgs
        if active_src != "Tümü":
            pkgs = [p for p in pkgs if p.source.value == src_map.get(active_src, "")]
        sort_idx = self._sort_combo.currentIndex()
        if sort_idx == 1:   pkgs = sorted(pkgs, key=lambda p: p.name.lower())
        elif sort_idx == 2: pkgs = sorted(pkgs, key=lambda p: p.source.value)
        elif sort_idx == 3: pkgs = sorted(pkgs, key=lambda p: (not p.installed, p.name.lower()))
        self._render(pkgs)

    def _render(self, pkgs: list, limit: int = 30):
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        if not pkgs:
            lbl = QLabel("Sonuç bulunamadı.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.addWidget(lbl)
        else:
            for pkg in pkgs[:limit]:
                item = PackageItem(pkg); item.action.connect(self.action)
                item.compare_requested.connect(self.compare_requested)
                self._list.addWidget(item)
            if len(pkgs) > limit:
                more = QPushButton(f"Daha Fazla Yükle  ({len(pkgs)-limit} paket kaldı)")
                more.setObjectName("open_btn"); more.setFixedHeight(38)
                more.clicked.connect(lambda _, p=pkgs, l=limit+30: self._render(p, l))
                self._list.addWidget(more)
        self._list.addStretch()


class InstalledPage(QWidget):
    action            = pyqtSignal(object, str)
    compare_requested = pyqtSignal(object)
    detail_requested = pyqtSignal(object)
    bulk_action = pyqtSignal(list, str)  # (packages, action)

    def __init__(self, hub: PackageManagerHub):
        super().__init__(); self.hub = hub
        self._selected: set = set()
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(12)

        # Başlık + toplu aksiyon
        top = QHBoxLayout()
        lbl = QLabel("Yüklü Paketler"); lbl.setObjectName("section_title")
        top.addWidget(lbl); top.addStretch()

        self._sel_lbl = QLabel("")
        self._sel_lbl.setStyleSheet("color:#fb923c;font-size:12px;background:transparent;")
        top.addWidget(self._sel_lbl)

        self._bulk_remove_btn = QPushButton("Seçilenleri Kaldır")
        self._bulk_remove_btn.setObjectName("remove_btn")
        self._bulk_remove_btn.setFixedHeight(32)
        self._bulk_remove_btn.hide()
        self._bulk_remove_btn.clicked.connect(self._on_bulk_remove)
        top.addWidget(self._bulk_remove_btn)
        lay.addLayout(top)

        # Arama filtresi
        search_row = QHBoxLayout()
        self._filter_input = QLineEdit()
        self._filter_input.setObjectName("search_input")
        self._filter_input.setPlaceholderText("Yüklü paketlerde ara...")
        self._filter_input.setMaximumWidth(300)
        self._filter_input.textChanged.connect(self._on_filter)
        search_row.addWidget(self._filter_input)
        search_row.addStretch()
        lay.addLayout(search_row)

        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(body); self._list.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidget(body); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        lay.addWidget(scroll, 1)
        self._all_pkgs: list[Package] = []
        self._loading = False
        self._load()

    def _on_loaded(self, pkgs: list):
        self._loading = False
        self._all_pkgs = pkgs
        self._render(self._all_pkgs)

    def _load(self):
        self._loading = False  # her seferinde sıfırla
        # Yükleniyor placeholder
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        lbl = QLabel("Yükleniyor…")
        lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
        self._list.addWidget(lbl)
        self._loading = True

        class _LoadWorker(QThread):
            done = pyqtSignal(list)
            def __init__(self, hub): super().__init__(); self.hub = hub
            def run(self): self.done.emit(self.hub.get_all_installed())

        self._load_worker = _LoadWorker(self.hub)
        self._load_worker.done.connect(self._on_loaded)
        # Güvenlik: 30sn sonra hâlâ yükleniyorsa flag'i sıfırla
        QTimer.singleShot(30000, lambda: setattr(self, '_loading', False))
        self._load_worker.start()

    def _on_filter(self, text: str):
        text = text.lower().strip()
        if not text:
            self._render(self._all_pkgs)
        else:
            filtered = [p for p in self._all_pkgs
                        if text in p.name.lower() or text in p.description.lower()]
            self._render(filtered)

    def _render(self, pkgs: list, limit: int = 50):
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        if not pkgs:
            lbl = QLabel("Yüklü paket bulunamadı.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
            self._list.addWidget(lbl)
        else:
            for pkg in pkgs[:limit]:
                item = PackageItem(pkg); item.action.connect(self.action)
                item.detail_requested.connect(self.detail_requested)
                item.compare_requested.connect(self.compare_requested)
                self._list.addWidget(item)
            if len(pkgs) > limit:
                more = QPushButton(f"Daha Fazla Yükle  ({len(pkgs)-limit} paket kaldı)")
                more.setObjectName("open_btn"); more.setFixedHeight(38)
                more.clicked.connect(lambda _, p=pkgs, l=limit+50: self._render(p, l))
                self._list.addWidget(more)
        self._list.addStretch()

    def _on_bulk_remove(self):
        pkgs = [p for p in self._all_pkgs if id(p) in self._selected]
        if not pkgs:
            return
        # Ö-4: Onay diyaloğu
        names = "\n".join(f"  • {p.display_name}" for p in pkgs[:10])
        if len(pkgs) > 10:
            names += f"\n  … ve {len(pkgs)-10} paket daha"
        dlg = QMessageBox()
        dlg.setWindowTitle("Toplu Kaldırma")
        dlg.setText(f"<b>{len(pkgs)} paket</b> kaldırılacak. Emin misiniz?")
        dlg.setInformativeText(names)
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Yes).setText(f"{len(pkgs)} Paketi Kaldır")
        dlg.button(QMessageBox.StandardButton.Cancel).setText("İptal")
        dlg.setStyleSheet(
            "QMessageBox{background:#0d1526;color:#e2e8f8;}"
            "QLabel{color:#e2e8f8;background:transparent;}"
            "QPushButton{background:#172035;color:#e2e8f8;border:1px solid #1e2d45;"
            "border-radius:6px;padding:6px 18px;min-width:80px;}"
            "QPushButton:hover{background:#f97316;border-color:#f97316;color:white;}")
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            self.bulk_action.emit(pkgs, "remove")


class CategoriesPage(QWidget):
    action            = pyqtSignal(object, str)
    compare_requested = pyqtSignal(object)
    detail_requested  = pyqtSignal(object)
    category_selected = pyqtSignal(str, str)

    _CATS = [
        ("gaming",    "Oyun",               "#7c3aed"),
        ("audio",     "Ses & Müzik",        "#2563eb"),
        ("video",     "Video & Medya",      "#dc2626"),
        ("dev",       "Geliştirme",         "#059669"),
        ("graphics",  "Grafik & Tasarım",   "#e11d48"),
        ("internet",  "İnternet",           "#0891b2"),
        ("system",    "Sistem Araçları",    "#d97706"),
        ("office",    "Ofis",               "#65a30d"),
        ("security",  "Güvenlik",           "#9333ea"),
        ("education", "Eğitim",             "#0d9488"),
        ("science",   "Bilim & Araştırma",  "#7c2d12"),
        ("vm",        "Sanal Makine",       "#1d4ed8"),
        ("terminal",  "Terminal Araçları",  "#14532d"),
        ("files",     "Dosya Yönetimi",     "#92400e"),
    ]

    def __init__(self, hub: PackageManagerHub):
        super().__init__()
        self.hub = hub
        self._worker = None
        self._build_grid()

    def _build_grid(self):
        self._stack = QStackedWidget()

        # ── Sayfa 0: kart grid ──
        grid_page = QWidget()
        lay = QVBoxLayout(grid_page); lay.setContentsMargins(28,24,28,24); lay.setSpacing(20)
        lbl = QLabel("Kategoriler"); lbl.setObjectName("section_title"); lay.addWidget(lbl)
        sub = QLabel("Bir kategoriye tıklayarak paketleri keşfet")
        sub.setStyleSheet("color:#2e3a55;font-size:13px;background:transparent;")
        lay.addWidget(sub)
        grid = QGridLayout(); grid.setSpacing(14)
        for i, (kind, name, color) in enumerate(self._CATS):
            card = CategoryCard(kind, name, color, "")
            card.mousePressEvent = lambda e, k=kind, n=name: self._on_cat_click(k, n)
            grid.addWidget(card, i // 4, i % 4)
        lay.addLayout(grid); lay.addStretch()
        self._stack.addWidget(grid_page)

        # ── Sayfa 1: paket listesi ──
        list_page = QWidget()
        ll = QVBoxLayout(list_page); ll.setContentsMargins(28,24,28,24); ll.setSpacing(16)

        # Başlık + geri butonu
        top = QHBoxLayout()
        self._back_btn = QPushButton("← Kategoriler")
        self._back_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#fb923c;border:none;"
            "font-size:13px;font-weight:600;padding:0;}"
            "QPushButton:hover{color:#f97316;}")
        self._back_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        top.addWidget(self._back_btn)
        top.addStretch()
        ll.addLayout(top)

        self._cat_title = QLabel(""); self._cat_title.setObjectName("section_title")
        ll.addWidget(self._cat_title)

        # Kaynak filtre butonları
        src_row = QHBoxLayout(); src_row.setSpacing(8)
        self._src_filters: dict[str, QPushButton] = {}
        for src_label in ("Tümü", "Pacman", "AUR", "Flatpak"):
            b = QPushButton(src_label); b.setObjectName("filter_btn")
            b.setProperty("active", src_label == "Tümü")
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.clicked.connect(lambda _, s=src_label: self._filter_source(s))
            src_row.addWidget(b)
            self._src_filters[src_label] = b
        src_row.addStretch()
        ll.addLayout(src_row)

        # Paket listesi
        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._pkg_list = QVBoxLayout(body); self._pkg_list.setSpacing(0)
        scroll = QScrollArea(); scroll.setWidget(body); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        ll.addWidget(scroll, 1)
        self._stack.addWidget(list_page)

        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0)
        root.addWidget(self._stack)
        self._all_pkgs: list[Package] = []

    def _on_cat_click(self, kind: str, name: str):
        self._cat_title.setText(f"{name} Paketleri")
        self._stack.setCurrentIndex(1)
        self._clear_list()
        # Yükleniyor göstergesi
        lbl = QLabel("⏳  Paketler yükleniyor...")
        lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pkg_list.addWidget(lbl)

        if self._worker and self._worker.isRunning():
            self._worker.quit()
        self._worker = CategorySearchWorker(self.hub, kind)
        self._worker.done.connect(self._on_pkgs_loaded)
        self._worker.error.connect(self._on_cat_error)
        self._worker.start()

    def _on_cat_error(self, msg: str):
        self._show_pkgs([])
        # Hata mesajını liste başına ekle
        err_lbl = QLabel(f"⚠  Arama hatası: {msg[:80]}")
        err_lbl.setStyleSheet("color:#f87171;font-size:12px;background:transparent;padding:8px;")
        self._pkg_list.insertWidget(0, err_lbl)

    def _on_pkgs_loaded(self, pkgs: list):
        self._all_pkgs = pkgs
        self._show_pkgs(pkgs)

    def _filter_source(self, src: str):
        for name, btn in self._src_filters.items():
            btn.setProperty("active", name == src)
            btn.style().unpolish(btn); btn.style().polish(btn)
        if src == "Tümü":
            self._show_pkgs(self._all_pkgs)
        else:
            src_map = {"Pacman": "pacman", "AUR": "aur", "Flatpak": "flatpak"}
            filtered = [p for p in self._all_pkgs if p.source.value == src_map.get(src, "")]
            self._show_pkgs(filtered)

    def _show_pkgs(self, pkgs: list, limit: int = 30):
        self._clear_list()
        if not pkgs:
            lbl = QLabel("Bu kategoride paket bulunamadı.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._pkg_list.addWidget(lbl)
        else:
            for pkg in pkgs[:limit]:
                item = PackageItem(pkg); item.action.connect(self.action)
                item.compare_requested.connect(self.compare_requested)
                item.detail_requested.connect(self.detail_requested)
                self._pkg_list.addWidget(item)
            if len(pkgs) > limit:
                more = QPushButton(f"Daha Fazla Yükle  ({len(pkgs)-limit} paket kaldı)")
                more.setObjectName("open_btn"); more.setFixedHeight(38)
                more.clicked.connect(lambda _, p=pkgs, l=limit+30: self._show_pkgs(p, l))
                self._pkg_list.addWidget(more)
        self._pkg_list.addStretch()

    def _clear_list(self):
        while self._pkg_list.count():
            w = self._pkg_list.takeAt(0)
            if w.widget(): w.widget().deleteLater()


class MaintenancePage(QWidget):
    """Sistem güncellemesi + orphan temizleyici + cache + sistem bilgisi"""

    def __init__(self, hub: PackageManagerHub):
        super().__init__()
        self.hub = hub
        self._worker: QThread | None = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(20)

        title = QLabel("Bakım & Güncelleme"); title.setObjectName("section_title")
        lay.addWidget(title)

        # ── Üst kısım: bilgi kartları + terminal yan yana ──
        top = QHBoxLayout(); top.setSpacing(16)

        # Sol: işlem butonları
        left = QVBoxLayout(); left.setSpacing(10)

        # Sistem bilgi kartı
        self._info_card = self._make_info_card()
        left.addWidget(self._info_card)

        # Güncelleme bölümü
        left.addWidget(self._section_lbl("Güncelleme"))
        for label, task, obj_name, desc in [
            ("Tüm Sistemi Güncelle",   "update_all",     "install_btn", "pacman -Syu + AUR + Flatpak"),
            ("Pacman Güncelle",        "update_pacman",  "install_btn", "pacman -Syu"),
            ("AUR Güncelle",           "update_aur",     "update_btn",  "yay/paru -Syu --aur"),
            ("Flatpak Güncelle",       "update_flatpak", "update_btn",  "flatpak update"),
        ]:
            left.addWidget(self._action_row(label, task, obj_name, desc))

        # Bakım bölümü
        left.addWidget(self._section_lbl("Bakım"))

        # Orphan listesi + temizle
        orphan_card = QWidget(); orphan_card.setObjectName("glass_panel")
        orphan_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ocl = QVBoxLayout(orphan_card); ocl.setContentsMargins(16, 12, 16, 12); ocl.setSpacing(8)

        orph_hdr = QHBoxLayout()
        orph_title = QLabel("Orphan Paketler")
        orph_title.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
        orph_hdr.addWidget(orph_title)
        orph_hdr.addStretch()
        self._orphan_count_lbl = QLabel("…")
        self._orphan_count_lbl.setStyleSheet("color:#fb923c;font-size:12px;background:transparent;"
                                              "font-family:'JetBrains Mono',monospace;")
        orph_hdr.addWidget(self._orphan_count_lbl)
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setStyleSheet("QPushButton{background:#172035;color:#6b7a99;border:none;"
                                   "border-radius:6px;font-size:14px;}"
                                   "QPushButton:hover{color:#e2e8f8;}")
        refresh_btn.clicked.connect(self._load_orphans)
        orph_hdr.addWidget(refresh_btn)
        ocl.addLayout(orph_hdr)

        self._orphan_list = QVBoxLayout()
        self._orphan_list.setSpacing(4)
        ocl.addLayout(self._orphan_list)

        remove_orph_btn = QPushButton("Orphan Paketleri Temizle")
        remove_orph_btn.setObjectName("remove_btn")
        remove_orph_btn.clicked.connect(lambda: self._run_task("remove_orphans", "Orphan Temizleniyor"))
        remove_orph_btn.setFixedHeight(34)
        ocl.addWidget(remove_orph_btn)
        left.addWidget(orphan_card)

        # Cache temizle
        left.addWidget(self._action_row("Paket Önbelleğini Temizle", "clean_cache",
                                         "remove_btn", "paccache -rk2  (son 2 sürüm korunur)"))
        left.addStretch()
        top.addLayout(left, 1)

        # Sağ: terminal çıktısı
        right = QVBoxLayout(); right.setSpacing(8)
        term_lbl = QLabel("Terminal Çıktısı")
        term_lbl.setStyleSheet("color:#2e3a55;font-size:10px;font-weight:600;"
                                "font-family:'JetBrains Mono',monospace;background:transparent;")
        right.addWidget(term_lbl)
        self._term = QTextEdit(); self._term.setReadOnly(True)
        self._term.setMinimumWidth(380)
        right.addWidget(self._term, 1)

        self._prog = QProgressBar(); self._prog.setRange(0, 0); self._prog.hide()
        right.addWidget(self._prog)

        self._clear_btn = QPushButton("Temizle")
        self._clear_btn.setObjectName("open_btn")
        self._clear_btn.setFixedHeight(30)
        self._clear_btn.clicked.connect(self._term.clear)
        right.addWidget(self._clear_btn)
        top.addLayout(right, 1)

        lay.addLayout(top, 1)

        # Orphan'ları başlangıçta yükle
        self._load_orphans()
        self._load_sysinfo()

    def _make_info_card(self) -> QWidget:
        card = QWidget(); card.setObjectName("glass_panel")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12); cl.setSpacing(6)
        lbl = QLabel("Sistem Bilgisi")
        lbl.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
        cl.addWidget(lbl)
        self._info_labels: dict[str, QLabel] = {}
        for key, display in [("kernel","Kernel"), ("disk_used","Disk (Kullanılan)"),
                               ("disk_free","Disk (Boş)"), ("pkg_pacman","Pacman Paketleri"),
                               ("pkg_aur","AUR Paketleri"), ("pkg_flatpak","Flatpak Paketleri")]:
            row = QHBoxLayout(); row.setSpacing(8)
            k = QLabel(display + ":"); k.setFixedWidth(140)
            k.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;"
                             "font-family:'JetBrains Mono',monospace;")
            v = QLabel("…"); v.setStyleSheet("color:#6b7a99;font-size:11px;background:transparent;")
            row.addWidget(k); row.addWidget(v); cl.addLayout(row)
            self._info_labels[key] = v
        return card

    def _section_lbl(self, text: str) -> QWidget:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#2e3a55;font-size:10px;font-weight:700;letter-spacing:.08em;"
                           "font-family:'JetBrains Mono',monospace;text-transform:uppercase;"
                           "background:transparent;")
        return lbl

    def _action_row(self, label: str, task: str, obj_name: str, desc: str) -> QWidget:
        w = QWidget(); w.setObjectName("glass_panel")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rl = QHBoxLayout(w); rl.setContentsMargins(16, 10, 16, 10); rl.setSpacing(12)
        info = QVBoxLayout(); info.setSpacing(2)
        lbl = QLabel(label); lbl.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
        sub = QLabel(desc); sub.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;"
                                               "font-family:'JetBrains Mono',monospace;")
        info.addWidget(lbl); info.addWidget(sub)
        rl.addLayout(info, 1)
        btn = QPushButton("Çalıştır"); btn.setObjectName(obj_name)
        btn.setFixedSize(90, 32)
        btn.clicked.connect(lambda: self._run_task(task, label))
        rl.addWidget(btn)
        return w

    def _load_orphans(self):
        # Listeyi temizle
        while self._orphan_list.count():
            w = self._orphan_list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        self._orphan_count_lbl.setText("yükleniyor…")
        self._orphan_worker = OrphanWorker(self.hub)
        self._orphan_worker.done.connect(self._on_orphans)
        self._orphan_worker.start()

    def _on_orphans(self, pkgs: list):
        while self._orphan_list.count():
            w = self._orphan_list.takeAt(0)
            if w.widget(): w.widget().deleteLater()

        if not pkgs:
            lbl = QLabel("✓  Orphan paket yok")
            lbl.setStyleSheet("color:#3fb950;font-size:12px;background:transparent;")
            self._orphan_list.addWidget(lbl)
            self._orphan_count_lbl.setText("0 paket")
        else:
            self._orphan_count_lbl.setText(f"{len(pkgs)} paket")
            for pkg in pkgs[:12]:
                row = QHBoxLayout()
                dot = QLabel("●"); dot.setFixedWidth(14)
                dot.setStyleSheet("color:#fb923c;font-size:8px;background:transparent;")
                name = QLabel(pkg.name); name.setStyleSheet(
                    "color:#6b7a99;font-size:11px;background:transparent;"
                    "font-family:'JetBrains Mono',monospace;")
                ver = QLabel(pkg.version); ver.setStyleSheet(
                    "color:#2e3a55;font-size:10px;background:transparent;")
                row.addWidget(dot); row.addWidget(name, 1); row.addWidget(ver)
                w = QWidget(); w.setLayout(row)
                self._orphan_list.addWidget(w)

    def _load_sysinfo(self):
        self._sysinfo_worker = SystemInfoWorker(self.hub)
        self._sysinfo_worker.done.connect(self._on_sysinfo)
        self._sysinfo_worker.start()

    def _on_sysinfo(self, info: dict):
        self._info_labels["kernel"].setText(info.get("kernel", "?"))
        self._info_labels["disk_used"].setText(info.get("disk_used", "?"))
        self._info_labels["disk_free"].setText(info.get("disk_free", "?"))
        counts = info.get("counts", {})
        self._info_labels["pkg_pacman"].setText(str(counts.get("pacman", "?")))
        self._info_labels["pkg_aur"].setText(str(counts.get("aur", "?")))
        self._info_labels["pkg_flatpak"].setText(str(counts.get("flatpak", "?")))

    def _run_task(self, task: str, label: str):
        if self._worker and self._worker.isRunning():
            self._append("⚠️  Başka bir işlem devam ediyor, lütfen bekleyin.\n")
            return
        self._append(f"\n{'═'*40}\n▶  {label}\n{'═'*40}\n")
        self._prog.setRange(0, 0); self._prog.show()
        self._worker = MaintenanceWorker(self.hub, task)
        self._worker.line.connect(self._append)
        self._worker.done.connect(self._on_done)
        self._worker.start()

    def _append(self, text: str):
        self._term.append(text.rstrip())
        self._term.verticalScrollBar().setValue(self._term.verticalScrollBar().maximum())

    def _on_done(self, ok: bool, msg: str):
        self._prog.hide()
        if ok:
            self._append("\n✅ Tamamlandı!")
        else:
            self._append(f"\n❌ Hata oluştu.")
        # Orphan ve sysinfo güncelle
        self._load_orphans()
        self._load_sysinfo()


# ─── Compare Panel ────────────────────────────────────────────────────────────

class ComparePanel(QWidget):
    """İki paketi yan yana karşılaştır (sağdan kayan panel)"""
    W = 680

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("action_drawer")
        self._pkgs: list = []
        self._offset = self.W; self._target = self.W
        self._timer = QTimer(self); self._timer.timeout.connect(self._step)
        self._build(); self.hide()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(22, 18, 22, 18); lay.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Paket Karşılaştırma")
        title.setStyleSheet("color:white;font-size:16px;font-weight:700;background:transparent;")
        hdr.addWidget(title); hdr.addStretch()
        clr_btn = QPushButton("Temizle"); clr_btn.setObjectName("open_btn")
        clr_btn.setFixedHeight(28); clr_btn.clicked.connect(self._clear)
        hdr.addWidget(clr_btn)
        close_btn = QPushButton("✕"); close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("QPushButton{background:#101828;color:#6b7a99;"
                                "border:1px solid rgba(255,255,255,0.06);border-radius:8px;}"
                                "QPushButton:hover{color:#e2e8f8;background:#172035;}")
        close_btn.clicked.connect(self.slide_out)
        hdr.addWidget(close_btn)
        lay.addLayout(hdr)

        hint = QLabel('Herhangi bir pakete sağ tıklayıp "Karşılaştırmaya Ekle" seçin (en fazla 2 paket)')
        hint.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;")
        hint.setWordWrap(True); lay.addWidget(hint)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame{color:rgba(255,255,255,0.06);}"); lay.addWidget(sep)

        self._cols = QHBoxLayout(); self._cols.setSpacing(12)
        lay.addLayout(self._cols, 1)

    def add_package(self, pkg, hub=None):
        if any(p.name == pkg.name for p in self._pkgs):
            return
        if len(self._pkgs) >= 2:
            self._pkgs.pop(0)
        self._pkgs.append(pkg)
        self._render(hub)
        self.slide_in()

    def _render(self, hub=None):
        while self._cols.count():
            w = self._cols.takeAt(0)
            if w.widget(): w.widget().deleteLater()

        if not self._pkgs:
            lbl = QLabel('Henüz paket eklenmedi.\nSağ tıklayıp "Karşılaştırmaya Ekle" seçin.')
            lbl.setStyleSheet("color:#2e3a55;font-size:13px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cols.addWidget(lbl)
            return

        for pkg in self._pkgs:
            col = QWidget(); col.setObjectName("glass_panel")
            col.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            cl = QVBoxLayout(col); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(8)

            # İkon + isim
            top = QHBoxLayout(); top.setSpacing(10)
            icon_w = AppIconWidget(pkg.name, pkg.icon_letter, pkg.icon_color, 40)
            top.addWidget(icon_w)
            name_col = QVBoxLayout(); name_col.setSpacing(2)
            name_lbl = QLabel(pkg.display_name)
            name_lbl.setStyleSheet("color:#e2e8f8;font-size:14px;font-weight:700;background:transparent;")
            name_col.addWidget(name_lbl)
            name_col.addWidget(SourceTag(pkg.source))
            top.addLayout(name_col, 1)
            cl.addLayout(top)

            # Özellikler
            rows = [
                ("Sürüm",    pkg.version),
                ("Kaynak",   pkg.source.value.upper()),
                ("Yüklü",    "✓ Evet" if pkg.installed else "✗ Hayır"),
                ("Boyut",    pkg.size or "?"),
                ("Lisans",   pkg.license or "?"),
                ("URL",      (pkg.url or "?")[:36] + ("…" if len(pkg.url or "") > 36 else "")),
            ]
            if pkg.depends:
                rows.append(("Bağımlılıklar", ", ".join(pkg.depends[:4])))

            for label, val in rows:
                row_w = QWidget(); rl = QHBoxLayout(row_w)
                rl.setContentsMargins(0, 3, 0, 3); rl.setSpacing(8)
                k = QLabel(label + ":"); k.setFixedWidth(100)
                k.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;"
                                "font-family:'JetBrains Mono',monospace;")
                v = QLabel(val)
                v.setStyleSheet("color:#6b7a99;font-size:11px;background:transparent;")
                v.setWordWrap(True)
                rl.addWidget(k); rl.addWidget(v, 1)
                cl.addWidget(row_w)

            # Açıklama
            if pkg.description:
                desc = QLabel(pkg.description[:160] + ("…" if len(pkg.description) > 160 else ""))
                desc.setWordWrap(True)
                desc.setStyleSheet("color:#4a5a77;font-size:11px;background:transparent;"
                                   "font-style:italic;")
                cl.addWidget(desc)
            cl.addStretch()
            self._cols.addWidget(col)

    def _clear(self):
        self._pkgs.clear()
        while self._cols.count():
            w = self._cols.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        lbl = QLabel("Temizlendi.")
        lbl.setStyleSheet("color:#2e3a55;font-size:13px;background:transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cols.addWidget(lbl)

    def slide_in(self):
        self._offset = self.W; self._target = 0
        self.show(); self.raise_(); self._place()
        if ANIMATIONS_ENABLED: self._timer.start(8)
        else: self._offset = 0; self._place()

    def slide_out(self):
        self._target = self.W
        if ANIMATIONS_ENABLED: self._timer.start(8)
        else: self._offset = self.W; self._place(); self.hide()

    def _step(self):
        diff = self._target - self._offset
        step = int(diff * 0.22) or (1 if diff > 0 else -1 if diff < 0 else 0)
        self._offset = max(0, min(self.W, self._offset + step))
        self._place()
        if self._offset == self._target:
            self._timer.stop()
            if self._target == self.W: self.hide()

    def _place(self):
        p = self.parent()
        if p:
            h = p.height(); w = self.W
            self.setGeometry(p.width() - w + self._offset, 0, w, h)


# ─── Snapshot Page ────────────────────────────────────────────────────────────

class SnapshotPage(QWidget):
    install_requested = pyqtSignal(list)   # U-9: eksik paketleri kur
    def __init__(self, hub):
        super().__init__()
        self.hub = hub
        self._current_snap: dict = {}
        self._worker = None
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QFileDialog, QSplitter
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(16)

        title = QLabel("Profil / Snapshot"); title.setObjectName("section_title")
        lay.addWidget(title)

        sub = QLabel("Kurulu paket listesini JSON olarak dışa aktarın ya da içe alarak karşılaştırın.")
        sub.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        lay.addWidget(sub)

        # Buton satırı
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        self._snap_btn = QPushButton("📷  Anlık Görüntü Al")
        self._snap_btn.setObjectName("install_btn"); self._snap_btn.setFixedHeight(36)
        self._snap_btn.clicked.connect(self._take_snapshot)
        btn_row.addWidget(self._snap_btn)

        self._save_btn = QPushButton("💾  Dışa Aktar (.json)")
        self._save_btn.setObjectName("open_btn"); self._save_btn.setFixedHeight(36)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_snapshot)
        btn_row.addWidget(self._save_btn)

        self._load_btn = QPushButton("📂  İçe Al ve Karşılaştır")
        self._load_btn.setObjectName("update_btn"); self._load_btn.setFixedHeight(36)
        self._load_btn.clicked.connect(self._load_snapshot)
        btn_row.addWidget(self._load_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

        # Durum etiketi
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
        lay.addWidget(self._status_lbl)

        # Splitter: snapshot bilgisi + diff
        splitter = QWidget(); sl = QHBoxLayout(splitter); sl.setSpacing(14)

        # Sol: snapshot özeti
        left = QWidget(); left.setObjectName("glass_panel")
        left.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        ll = QVBoxLayout(left); ll.setContentsMargins(16,14,16,14); ll.setSpacing(6)
        lhdr = QLabel("Snapshot")
        lhdr.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
        ll.addWidget(lhdr)
        self._snap_info = QTextEdit(); self._snap_info.setReadOnly(True)
        self._snap_info.setStyleSheet("QTextEdit{background:transparent;color:#6b7a99;"
                                       "border:none;font-family:'JetBrains Mono',monospace;"
                                       "font-size:11px;}")
        self._snap_info.setPlaceholderText("Snapshot almak için butona tıklayın…")
        ll.addWidget(self._snap_info, 1)
        sl.addWidget(left, 1)

        # Sağ: diff
        right = QWidget(); right.setObjectName("glass_panel")
        right.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rl = QVBoxLayout(right); rl.setContentsMargins(16,14,16,14); rl.setSpacing(6)
        rhdr = QLabel("Sistem Farkı")
        rhdr.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
        rl.addWidget(rhdr)
        self._diff_view = QTextEdit(); self._diff_view.setReadOnly(True)
        self._diff_view.setStyleSheet("QTextEdit{background:transparent;color:#6b7a99;"
                                       "border:none;font-family:'JetBrains Mono',monospace;"
                                       "font-size:11px;}")
        self._diff_view.setPlaceholderText("İçe alınan snapshot ile mevcut sistem karşılaştırılacak…")
        rl.addWidget(self._diff_view, 1)
        sl.addWidget(right, 1)

        lay.addWidget(splitter, 1)

    def _take_snapshot(self):
        self._snap_btn.setEnabled(False)
        self._status_lbl.setText("Snapshot alınıyor…")
        self._worker = SnapshotWorker(self.hub, "create")
        self._worker.done.connect(self._on_snapshot_created)
        self._worker.start()

    def _on_snapshot_created(self, ok: bool, msg: str, snap: dict):
        self._snap_btn.setEnabled(True)
        if not ok: self._status_lbl.setText("Hata!"); return
        self._current_snap = snap
        self._save_btn.setEnabled(True)
        counts = {src: len(pkgs) for src, pkgs in snap.get("packages", {}).items()}
        total = sum(counts.values())
        info_lines = [f"Oluşturuldu: {snap.get('created','')}",
                      f"Sistem: {snap.get('hostname','')}",
                      f"Toplam: {total} paket", ""]
        for src, cnt in counts.items():
            info_lines.append(f"  {src.upper():<12} {cnt} paket")
        self._snap_info.setText("\n".join(info_lines))
        self._status_lbl.setText(f"✅ {total} paket kaydedildi.")

    def _save_snapshot(self):
        from PyQt6.QtWidgets import QFileDialog
        import datetime
        default = f"arch-snapshot-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Snapshot Kaydet", default,
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*)")
        if not path: return
        self._worker = SnapshotWorker(self.hub, "save", path=path, snapshot=self._current_snap)
        self._worker.done.connect(lambda ok, msg, _: self._status_lbl.setText(
            f"✅ Kaydedildi: {path}" if ok else f"❌ Hata: {msg}"))
        self._worker.start()

    def _load_snapshot(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Snapshot Yükle", "",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*)")
        if not path: return
        self._status_lbl.setText("Karşılaştırılıyor…")
        self._worker = SnapshotWorker(self.hub, "load", path=path)
        self._worker.done.connect(self._on_snapshot_loaded)
        self._worker.start()

    def _on_snapshot_loaded(self, ok: bool, msg: str, snap: dict):
        if not ok:
            self._status_lbl.setText(f"❌ Yüklenemedi: {msg}"); return
        counts = {src: len(pkgs) for src, pkgs in snap.get("packages", {}).items()}
        total = sum(counts.values())
        info_lines = [f"Yüklendi: {snap.get('created','')}",
                      f"Sistem: {snap.get('hostname','')}",
                      f"Toplam: {total} paket", ""]
        for src, cnt in counts.items():
            info_lines.append(f"  {src.upper():<12} {cnt} paket")
        self._snap_info.setText("\n".join(info_lines))
        # Diff hesapla
        self._worker2 = SnapshotWorker(self.hub, "diff", snapshot=snap)
        self._worker2.done.connect(self._on_diff)
        self._worker2.start()

    def _on_diff(self, ok: bool, msg: str, diff: dict):
        missing  = diff.get("missing", [])
        extra    = diff.get("extra", [])
        ver_diff = diff.get("version_diff", [])
        lines = []
        if missing:
            lines.append(f"── Eksik ({len(missing)} paket) ──────────────")
            for p in missing[:30]:
                lines.append(f"  ✗ {p['name']:<30} {p['version']} [{p['source']}]")
        if extra:
            lines.append(f"\n── Ekstra ({len(extra)} paket) ──────────────")
            for p in extra[:30]:
                lines.append(f"  + {p['name']:<30} {p['version']} [{p['source']}]")
        if ver_diff:
            lines.append(f"\n── Sürüm Farkı ({len(ver_diff)} paket) ──────")
            for p in ver_diff[:30]:
                lines.append(f"  ≠ {p['name']:<30} {p['snap_ver']} → {p['current_ver']}")
        if not lines:
            lines = ["✅ Sistem snapshot ile birebir eşleşiyor!"]
        self._diff_view.setText("\n".join(lines))
        self._status_lbl.setText(
            f"Karşılaştırma: {len(missing)} eksik, {len(extra)} ekstra, {len(ver_diff)} sürüm farkı")

        # U-9: Eksik paket varsa kurulum butonu göster
        if hasattr(self, '_install_missing_btn'):
            self._install_missing_btn.setParent(None)
        if missing:
            self._missing_pkgs = missing
            self._install_missing_btn = QPushButton(
                f"⬇  {len(missing)} Eksik Paketi Kur")
            self._install_missing_btn.setObjectName("install_btn")
            self._install_missing_btn.setFixedHeight(36)
            self._install_missing_btn.clicked.connect(self._install_missing)
            # diff_view'in altına ekle
            self._diff_view.parent().layout().addWidget(self._install_missing_btn)

    def _install_missing(self):
        """Snapshot'ta eksik olan paketleri toplu kur"""
        if not hasattr(self, '_missing_pkgs') or not self._missing_pkgs:
            return
        from backend.managers import Package, PackageSource
        pkgs_to_install = []
        for p in self._missing_pkgs:
            src_map = {
                "pacman":   PackageSource.PACMAN,
                "aur":      PackageSource.AUR,
                "flatpak":  PackageSource.FLATPAK,
                "appimage": PackageSource.APPIMAGE,
            }
            src = src_map.get(p.get("source", ""), PackageSource.PACMAN)
            pkgs_to_install.append(Package(
                p["name"], "", p.get("version", ""), src))
        if pkgs_to_install:
            self._status_lbl.setText(
                f"⏳ {len(pkgs_to_install)} paket kuruluyor… (ActionDrawer'dan takip edin)")
            self._install_missing_btn.setEnabled(False)
            # Ana pencereye sinyal gönder
            self.install_requested.emit(pkgs_to_install)


# ─── GitHub Page ──────────────────────────────────────────────────────────────

class GitHubPage(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._assets: list[dict] = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(16)

        title = QLabel("GitHub'dan Kur"); title.setObjectName("section_title")
        lay.addWidget(title)

        sub = QLabel("GitHub repo URL'si, releases sayfası veya doğrudan dosya linki girin.")
        sub.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        lay.addWidget(sub)

        # URL giriş satırı
        url_row = QHBoxLayout(); url_row.setSpacing(10)
        self._url_input = QLineEdit()
        self._url_input.setObjectName("search_input")
        self._url_input.setPlaceholderText(
            "https://github.com/user/repo   veya   doğrudan .AppImage/.tar.gz linki")
        self._url_input.returnPressed.connect(self._fetch)
        url_row.addWidget(self._url_input, 1)
        self._fetch_btn = QPushButton("Getir")
        self._fetch_btn.setObjectName("install_btn"); self._fetch_btn.setFixedHeight(36)
        self._fetch_btn.setFixedWidth(90); self._fetch_btn.clicked.connect(self._fetch)
        url_row.addWidget(self._fetch_btn)
        lay.addLayout(url_row)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
        lay.addWidget(self._status_lbl)

        # Önizleme: release bilgisi + asset listesi
        preview = QWidget(); preview.setObjectName("glass_panel")
        preview.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pl = QVBoxLayout(preview); pl.setContentsMargins(18, 14, 18, 14); pl.setSpacing(8)

        self._repo_lbl = QLabel("─")
        self._repo_lbl.setStyleSheet("color:#e2e8f8;font-size:14px;font-weight:700;background:transparent;")
        pl.addWidget(self._repo_lbl)

        self._release_lbl = QLabel("")
        self._release_lbl.setStyleSheet("color:#fb923c;font-size:11px;background:transparent;"
                                         "font-family:'JetBrains Mono',monospace;")
        pl.addWidget(self._release_lbl)

        self._body_lbl = QLabel("")
        self._body_lbl.setStyleSheet("color:#4a5a77;font-size:11px;background:transparent;")
        self._body_lbl.setWordWrap(True)
        pl.addWidget(self._body_lbl)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("QFrame{color:rgba(255,255,255,0.05);}"); pl.addWidget(sep2)

        # Asset listesi
        self._asset_list = QVBoxLayout(); self._asset_list.setSpacing(6)
        pl.addLayout(self._asset_list)
        lay.addWidget(preview, 1)

        # Terminal çıktısı
        self._term = QTextEdit(); self._term.setReadOnly(True)
        self._term.setFixedHeight(160)
        self._term.setStyleSheet("QTextEdit{background:#060c18;color:#4ade80;"
                                  "border:none;font-family:'JetBrains Mono',monospace;font-size:11px;"
                                  "border-radius:6px;padding:6px;}")
        lay.addWidget(self._term)

        self._dl_prog = QProgressBar(); self._dl_prog.setRange(0, 0); self._dl_prog.hide()
        lay.addWidget(self._dl_prog)

    def _fetch(self):
        url = self._url_input.text().strip()
        if not url: return
        self._fetch_btn.setEnabled(False)
        self._status_lbl.setText("Bilgi alınıyor…")
        self._clear_assets()
        self._worker = GitHubFetchWorker(url)
        self._worker.done.connect(self._on_assets)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_assets(self, assets: list):
        self._fetch_btn.setEnabled(True)
        self._assets = assets
        if not assets: return
        a0 = assets[0]
        url = self._url_input.text().strip()
        import re
        m = re.search(r'github\.com/([^/]+/[^/?\s#]+)', url)
        self._repo_lbl.setText(m.group(1) if m else a0.get("name",""))
        self._release_lbl.setText(f"Tag: {a0.get('tag','')}   Tarih: {a0.get('published','')}")
        body = (a0.get("body") or "").strip()
        self._body_lbl.setText(body[:200] + ("…" if len(body) > 200 else "") if body else "")
        # Source-only repo uyarısı
        is_source_only = all(a.get("kind") == "source" for a in assets)
        if is_source_only:
            self._status_lbl.setText(
                "⚠  Bu release'te özel dosya yok — GitHub'ın otomatik kaynak arşivleri gösteriliyor.")
        else:
            self._status_lbl.setText(f"✓  {len(assets)} indirilebilir dosya bulundu.")
        self._clear_assets()
        for asset in assets:
            self._asset_list.addWidget(self._make_asset_row(asset))

    def _make_asset_row(self, asset: dict) -> QWidget:
        row = QWidget(); row.setObjectName("settings_row")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rl = QHBoxLayout(row); rl.setContentsMargins(12, 8, 12, 8); rl.setSpacing(10)

        # Tür etiketi
        kind = asset.get("kind", "asset")
        kind_lbl = QLabel("kaynak" if kind == "source" else "dosya")
        kind_lbl.setFixedWidth(46)
        kind_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kind_lbl.setStyleSheet(
            f"color:{'#fb923c' if kind == 'source' else '#60a5fa'};"
            f"background:{'#1a0d00' if kind == 'source' else '#001a2e'};"
            "font-size:10px;border-radius:4px;padding:2px 4px;")
        rl.addWidget(kind_lbl)

        name_lbl = QLabel(asset["name"])
        name_lbl.setStyleSheet("color:#e2e8f8;font-size:12px;background:transparent;"
                                "font-family:'JetBrains Mono',monospace;")
        rl.addWidget(name_lbl, 1)

        size_mb = (asset.get("size") or 0) / (1024 * 1024)
        if size_mb > 0:
            size_lbl = QLabel(f"{size_mb:.1f} MB")
            size_lbl.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;")
            rl.addWidget(size_lbl)

        btn_text = "⬇  İndir" if kind == "source" else "⬇  İndir & Kur"
        btn = QPushButton(btn_text); btn.setObjectName("install_btn")
        btn.setFixedHeight(30); btn.setFixedWidth(110)
        btn.clicked.connect(lambda _, a=asset: self._download(a))
        rl.addWidget(btn)
        return row

    def _on_error(self, msg: str):
        self._fetch_btn.setEnabled(True)
        self._status_lbl.setText(f"❌ {msg}")

    def _clear_assets(self):
        while self._asset_list.count():
            w = self._asset_list.takeAt(0)
            if w.widget(): w.widget().deleteLater()

    def _download(self, asset: dict):
        self._dl_prog.show(); self._dl_prog.setRange(0, 0)
        self._term.clear()
        self._status_lbl.setText(f"İndiriliyor: {asset['name']}")
        self._worker2 = GitHubDownloadWorker(asset)

        def on_line(l: str):
            self._term.append(l.rstrip())
            self._term.verticalScrollBar().setValue(
                self._term.verticalScrollBar().maximum())
            # U-10: Topbar'a yansıt — % parse et
            import re
            m = re.findall(r'(\d{1,3})\s*%', l)
            pct = int(m[-1]) if m else 0
            spd = 0.0
            sp = re.search(r'(\d+\.?\d*)\s*(MB|KB)/s', l)
            if sp:
                spd = float(sp.group(1))
                if sp.group(2) == "KB": spd /= 1024
            if hasattr(self, '_topbar_cb'):
                self._topbar_cb(asset['name'], pct, spd)

        self._worker2.line.connect(on_line)
        self._worker2.done.connect(self._on_download_done)
        self._worker2.start()

    def _on_download_done(self, ok: bool, msg: str):
        self._dl_prog.hide()
        if hasattr(self, '_topbar_cb'):
            del self._topbar_cb
        if ok:
            self._status_lbl.setText(f"✅ Tamamlandı: {msg}")
            self._term.append(f"\n✅ Başarıyla tamamlandı!")
        else:
            self._status_lbl.setText(f"❌ Hata: {msg}")
            self._term.append(f"\n❌ Hata: {msg}")


# ─── History Page ─────────────────────────────────────────────────────────────

class HistoryPage(QWidget):
    def __init__(self, history: HistoryManager):
        super().__init__()
        self._history = history
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(16)

        # Başlık + temizle butonu
        hdr = QHBoxLayout()
        title = QLabel("Kurulum Geçmişi"); title.setObjectName("section_title")
        hdr.addWidget(title); hdr.addStretch()

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Paket adı ara…")
        self._filter_input.setObjectName("search_input")
        self._filter_input.setFixedWidth(220)
        self._filter_input.textChanged.connect(self._on_filter)
        hdr.addWidget(self._filter_input)

        clear_btn = QPushButton("Geçmişi Temizle")
        clear_btn.setObjectName("remove_btn"); clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear)
        hdr.addWidget(clear_btn)

        export_json_btn = QPushButton("⬇ JSON")
        export_json_btn.setObjectName("open_btn"); export_json_btn.setFixedHeight(32)
        export_json_btn.clicked.connect(lambda: self._export("json"))
        hdr.addWidget(export_json_btn)

        export_csv_btn = QPushButton("⬇ CSV")
        export_csv_btn.setObjectName("open_btn"); export_csv_btn.setFixedHeight(32)
        export_csv_btn.clicked.connect(lambda: self._export("csv"))
        hdr.addWidget(export_csv_btn)

        lay.addLayout(hdr)

        # İstatistik kartları
        stats_row = QHBoxLayout(); stats_row.setSpacing(10)
        self._stat_install = self._stat_card("↓ Kurulum", "0", "#059669")
        self._stat_remove  = self._stat_card("✕ Kaldırma", "0", "#dc2626")
        self._stat_update  = self._stat_card("↑ Güncelleme", "0", "#2563eb")
        self._stat_fail    = self._stat_card("⚠ Başarısız", "0", "#d97706")
        for c in (self._stat_install, self._stat_remove, self._stat_update, self._stat_fail):
            stats_row.addWidget(c)
        lay.addLayout(stats_row)

        # Liste
        body = QWidget(); body.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(body); self._list.setSpacing(4)
        scroll = QScrollArea(); scroll.setWidget(body); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        lay.addWidget(scroll, 1)
        self._all_entries: list[dict] = []

    def _stat_card(self, label: str, value: str, color: str) -> QWidget:
        w = QWidget(); w.setObjectName("glass_panel")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cl = QVBoxLayout(w); cl.setContentsMargins(16, 10, 16, 10); cl.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{color};font-size:10px;font-weight:700;background:transparent;")
        val = QLabel(value)
        val.setStyleSheet("color:#e2e8f8;font-size:22px;font-weight:700;background:transparent;")
        cl.addWidget(lbl); cl.addWidget(val)
        w._val_lbl = val
        return w

    def refresh(self):
        self._all_entries = self._history.get_all()
        self._update_stats(self._all_entries)
        self._render(self._all_entries)

    def _update_stats(self, entries: list):
        installs = sum(1 for e in entries if e["action"] == "install" and e["success"])
        removes  = sum(1 for e in entries if e["action"] == "remove"  and e["success"])
        updates  = sum(1 for e in entries if e["action"] == "update"  and e["success"])
        fails    = sum(1 for e in entries if not e["success"])
        self._stat_install._val_lbl.setText(str(installs))
        self._stat_remove._val_lbl.setText(str(removes))
        self._stat_update._val_lbl.setText(str(updates))
        self._stat_fail._val_lbl.setText(str(fails))

    def _on_filter(self, text: str):
        text = text.lower().strip()
        filtered = [e for e in self._all_entries
                    if text in e.get("name","").lower()] if text else self._all_entries
        self._render(filtered)

    def _render(self, entries: list):
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        if not entries:
            lbl = QLabel("Henüz kayıt yok.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:30px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.addWidget(lbl)
            return
        action_icons = {"install": ("↓", "#059669"), "remove": ("✕", "#dc2626"),
                        "update":  ("↑", "#2563eb")}
        for entry in entries:
            row = QWidget(); row.setObjectName("glass_panel")
            row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            rl = QHBoxLayout(row); rl.setContentsMargins(14, 8, 14, 8); rl.setSpacing(12)

            icon_char, icon_color = action_icons.get(entry.get("action",""), ("?", "#6b7a99"))
            if not entry.get("success", True):
                icon_char, icon_color = "⚠", "#d97706"

            icon = QLabel(icon_char)
            icon.setFixedSize(28, 28)
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon.setStyleSheet(f"color:{icon_color};font-size:14px;font-weight:bold;"
                               f"background:rgba(255,255,255,0.04);border-radius:6px;")
            rl.addWidget(icon)

            info = QVBoxLayout(); info.setSpacing(1)
            name_lbl = QLabel(entry.get("name", "?"))
            name_lbl.setStyleSheet("color:#e2e8f8;font-size:13px;font-weight:600;background:transparent;")
            ver_src = QLabel(f"v{entry.get('version','?')}  ·  {entry.get('source','?').upper()}")
            ver_src.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;"
                                  "font-family:'JetBrains Mono',monospace;")
            info.addWidget(name_lbl); info.addWidget(ver_src)
            rl.addLayout(info, 1)

            ts = QLabel(entry.get("ts", ""))
            ts.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;"
                             "font-family:'JetBrains Mono',monospace;")
            ts.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            rl.addWidget(ts)
            self._list.addWidget(row)
        self._list.addStretch()

    def _clear(self):
        dlg = QMessageBox(); dlg.setWindowTitle("Geçmişi Temizle")
        dlg.setText("Tüm kurulum geçmişi silinsin mi?")
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Temizle")
        dlg.button(QMessageBox.StandardButton.Cancel).setText("İptal")
        dlg.setStyleSheet("QMessageBox{background:#0d1526;color:#e2e8f8;}"
                          "QLabel{color:#e2e8f8;background:transparent;}"
                          "QPushButton{background:#172035;color:#e2e8f8;border:1px solid #1e2d45;"
                          "border-radius:6px;padding:6px 18px;min-width:70px;}"
                          "QPushButton:hover{background:#dc2626;border-color:#dc2626;color:white;}")
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            self._history.clear(); self.refresh()

    def _export(self, fmt: str):
        """T-7: Geçmişi JSON veya CSV olarak dışa aktar"""
        from PyQt6.QtWidgets import QFileDialog
        import json, datetime
        entries = self._all_entries
        if not entries:
            return
        default = f"arxis-history-{datetime.datetime.now().strftime('%Y%m%d-%H%M')}.{fmt}"
        if fmt == "json":
            path, _ = QFileDialog.getSaveFileName(
                self, "JSON Olarak Kaydet", default, "JSON (*.json)")
            if not path: return
            try:
                import pathlib
                pathlib.Path(path).write_text(
                    json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                QMessageBox.warning(self, "Hata", str(e))
        elif fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(
                self, "CSV Olarak Kaydet", default, "CSV (*.csv)")
            if not path: return
            try:
                import csv, pathlib
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f, fieldnames=["ts","name","version","source","action","success"])
                    writer.writeheader()
                    writer.writerows(entries)
            except Exception as e:
                QMessageBox.warning(self, "Hata", str(e))




# ─── Favorites Page ───────────────────────────────────────────────────────────

class FavoritesPage(QWidget):
    action           = pyqtSignal(object, str)
    detail_requested = pyqtSignal(object)

    def __init__(self, favorites: FavoritesManager, hub):
        super().__init__()
        self._fav = favorites; self._hub = hub
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(16)
        hdr = QHBoxLayout()
        title = QLabel("Beğenilenler"); title.setObjectName("section_title")
        hdr.addWidget(title); hdr.addStretch()
        clear_btn = QPushButton("Tümünü Temizle")
        clear_btn.setObjectName("remove_btn"); clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear_all)
        hdr.addWidget(clear_btn)
        lay.addLayout(hdr)

        sub = QLabel("Sağ tık → Beğenilenlere Ekle ile buraya paket ekleyebilirsiniz.")
        sub.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        lay.addWidget(sub)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(inner); self._list.setSpacing(0)
        self._list.setContentsMargins(0,0,0,0)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)

    def refresh(self):
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        entries = self._fav.get_all()
        if not entries:
            lbl = QLabel("Henüz beğenilen paket yok.\nSağ tık menüsünden ★ Beğenilenlere Ekle'yi deneyin.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:40px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.addWidget(lbl)
        else:
            from backend.managers import Package, PackageSource
            for e in entries:
                try:
                    src = PackageSource(e["source"])
                except Exception:
                    src = PackageSource.PACMAN
                pkg = Package(e["name"], e.get("desc",""), e.get("version",""),
                              src, icon_color=e.get("color","#6b7a99"),
                              _display_name=e.get("display", e["name"]))
                row = self._make_row(e, pkg)
                self._list.addWidget(row)
        self._list.addStretch()

    def _make_row(self, entry: dict, pkg) -> QWidget:
        w = QWidget(); w.setObjectName("package_item")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(w); hl.setContentsMargins(16,10,16,10); hl.setSpacing(12)
        icon = AppIconWidget(pkg.name, pkg.icon_letter, pkg.icon_color, 36)
        hl.addWidget(icon)
        info = QVBoxLayout(); info.setSpacing(2)
        nm = QLabel(pkg.display_name); nm.setObjectName("package_name")
        info.addWidget(nm)
        src_lbl = QLabel(f"{entry.get('source','').upper()}  ·  {entry.get('ts','')} ")
        src_lbl.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;"
                              "font-family:'JetBrains Mono',monospace;")
        info.addWidget(src_lbl)
        hl.addLayout(info, 1)
        # Kur butonu
        inst_btn = QPushButton("Kur"); inst_btn.setObjectName("install_btn")
        inst_btn.setFixedWidth(80); inst_btn.setFixedHeight(30)
        inst_btn.clicked.connect(lambda _, p=pkg: self.action.emit(p, "install"))
        hl.addWidget(inst_btn)
        # Çıkar butonu
        rm_btn = QPushButton("★"); rm_btn.setObjectName("remove_btn")
        rm_btn.setFixedWidth(36); rm_btn.setFixedHeight(30)
        rm_btn.setToolTip("Beğenilenlerden çıkar")
        rm_btn.clicked.connect(lambda _, k=entry["key"]: self._remove(k))
        hl.addWidget(rm_btn)
        w.mousePressEvent = lambda e, p=pkg: (
            self.detail_requested.emit(p) if e.button() == Qt.MouseButton.LeftButton else None)
        return w

    def _remove(self, key: str):
        self._fav._data = [e for e in self._fav._data if e["key"] != key]
        self._fav._save(); self.refresh()

    def _clear_all(self):
        self._fav.clear(); self.refresh()


# ─── Queue Page ───────────────────────────────────────────────────────────────

class QueuePage(QWidget):
    install_all = pyqtSignal(list)

    def __init__(self, queue: DownloadQueue):
        super().__init__()
        self._queue = queue
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(16)

        hdr = QHBoxLayout()
        title = QLabel("İndirme Kuyruğu"); title.setObjectName("section_title")
        hdr.addWidget(title); hdr.addStretch()
        clear_btn = QPushButton("Kuyruğu Temizle")
        clear_btn.setObjectName("remove_btn"); clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear); hdr.addWidget(clear_btn)
        lay.addLayout(hdr)

        sub = QLabel("Sağ tık → ⊕ Kuyruğa Ekle ile paket biriktirin, sonra hepsini birden kurun.")
        sub.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        lay.addWidget(sub)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")
        inner = QWidget(); inner.setStyleSheet("background:transparent;")
        self._list = QVBoxLayout(inner); self._list.setSpacing(0)
        self._list.setContentsMargins(0,0,0,0)
        scroll.setWidget(inner)
        lay.addWidget(scroll, 1)

        # Alt buton
        self._install_btn = QPushButton("⬇  Tümünü Kur")
        self._install_btn.setObjectName("install_btn")
        self._install_btn.setFixedHeight(42)
        self._install_btn.clicked.connect(self._install_all)
        lay.addWidget(self._install_btn)

    def refresh(self):
        while self._list.count():
            w = self._list.takeAt(0)
            if w.widget(): w.widget().deleteLater()
        entries = self._queue.get_all()
        self._install_btn.setText(f"⬇  Tümünü Kur ({len(entries)} paket)")
        self._install_btn.setEnabled(bool(entries))
        if not entries:
            lbl = QLabel("Kuyruk boş.\nSağ tık menüsünden ⊕ Kuyruğa Ekle'yi kullanın.")
            lbl.setStyleSheet("color:#2e3a55;font-size:14px;padding:40px;background:transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list.addWidget(lbl)
        else:
            from backend.managers import Package, PackageSource
            for e in entries:
                try: src = PackageSource(e["source"])
                except Exception: src = PackageSource.PACMAN
                pkg = Package(e["name"], e.get("desc",""), e.get("version",""),
                              src, icon_color=e.get("color","#6b7a99"),
                              _display_name=e.get("display", e["name"]),
                              url=e.get("url",""))
                row = self._make_row(e, pkg)
                self._list.addWidget(row)
        self._list.addStretch()

    def _make_row(self, entry: dict, pkg) -> QWidget:
        w = QWidget(); w.setObjectName("package_item")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hl = QHBoxLayout(w); hl.setContentsMargins(16,10,16,10); hl.setSpacing(12)
        icon = AppIconWidget(pkg.name, pkg.icon_letter, pkg.icon_color, 36)
        hl.addWidget(icon)
        info = QVBoxLayout(); info.setSpacing(2)
        nm = QLabel(pkg.display_name); nm.setObjectName("package_name")
        info.addWidget(nm)
        src_lbl = QLabel(entry.get("source","").upper())
        src_lbl.setStyleSheet("color:#2e3a55;font-size:10px;background:transparent;"
                              "font-family:'JetBrains Mono',monospace;")
        info.addWidget(src_lbl)
        hl.addLayout(info, 1)
        rm_btn = QPushButton("✕"); rm_btn.setObjectName("remove_btn")
        rm_btn.setFixedWidth(36); rm_btn.setFixedHeight(30)
        rm_btn.setToolTip("Kuyruktan çıkar")
        rm_btn.clicked.connect(lambda _, k=entry["key"]: self._remove(k))
        hl.addWidget(rm_btn)
        return w

    def _remove(self, key: str):
        self._queue.remove_by_key(key); self.refresh()

    def _clear(self):
        self._queue.clear(); self.refresh()

    def _install_all(self):
        entries = self._queue.get_all()
        if not entries: return
        from backend.managers import Package, PackageSource
        pkgs = []
        for e in entries:
            try: src = PackageSource(e["source"])
            except Exception: src = PackageSource.PACMAN
            pkgs.append(Package(e["name"], e.get("desc",""), e.get("version",""),
                                src, icon_color=e.get("color","#6b7a99"),
                                _display_name=e.get("display", e["name"]),
                                url=e.get("url","")))
        self.install_all.emit(pkgs)


# ─── Settings Page ────────────────────────────────────────────────────────────

class ToggleSwitch(QWidget):
    """iOS tarzı açma/kapama anahtarı"""
    toggled = pyqtSignal(bool)

    def __init__(self, state: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedSize(52, 28)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._state  = state
        self._offset = 28.0 if state else 4.0   # top pozisyon
        self._anim   = QTimer(self); self._anim.timeout.connect(self._step)

    @property
    def state(self) -> bool:
        return self._state

    def set_state(self, v: bool, animate: bool = False):
        self._state = v
        self._target = 28.0 if v else 4.0
        if animate:
            self._anim.start(10)
        else:
            self._offset = self._target
            self.update()

    def _step(self):
        diff = self._target - self._offset
        self._offset += diff * 0.25
        if abs(diff) < 0.5:
            self._offset = self._target
            self._anim.stop()
        self.update()

    def mousePressEvent(self, _):
        self._state  = not self._state
        self._target = 28.0 if self._state else 4.0
        self._anim.start(10)
        self.toggled.emit(self._state)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Arka plan
        track_color = QColor("#166534") if self._state else QColor("#374151")
        p.setBrush(QBrush(track_color)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, 52, 28), 14, 14)
        # Knob
        knob_color = QColor("#ffffff")
        p.setBrush(QBrush(knob_color))
        p.drawEllipse(QRectF(self._offset, 4, 20, 20))
        p.end()


class SettingsPage(QWidget):
    # Ayar değişince ana pencereye sinyal gönder
    setting_changed = pyqtSignal(str, bool)   # (key, value)

    CONFIG_PATH = None   # __init__'te belirlenir

    # Varsayılan ayarlar
    DEFAULTS: dict[str, tuple[str, str, bool]] = {
        # key: (section, label, default)
        "aur":           ("Paket Kaynakları", "AUR (yay / paru)",            True),
        "flatpak":       ("Paket Kaynakları", "Flatpak",                     True),
        "appimage":      ("Paket Kaynakları", "AppImage",                    True),
        "wine":          ("Paket Kaynakları", "Wine / Proton",               True),
        "auto_update":   ("Genel",            "Otomatik güncelleme kontrolü (30dk)", True),
        "notifications": ("Genel",            "Bildirim göster",             True),
        "live_search":   ("Genel",            "Canlı arama (yazarken ara)",  True),
        "history":       ("Genel",            "İndirme geçmişini tut",       True),
        "bandwidth":     ("Görünüm",          "Bant genişliği grafiği",      True),
        "animations":    ("Görünüm",          "Panel animasyonları",         True),
    }

    def __init__(self):
        super().__init__()
        import pathlib
        self.CONFIG_PATH = pathlib.Path.home() / ".config" / "arxis" / "settings.json"
        self._switches: dict[str, ToggleSwitch] = {}
        self._cfg = self._load()
        self._build()

    # ── Kalıcı kayıt ─────────────────────────────────────────────────────────
    def _load(self) -> dict:
        try:
            import json
            if self.CONFIG_PATH.exists():
                return json.loads(self.CONFIG_PATH.read_text())
        except Exception:
            pass
        return {k: v[2] for k, v in self.DEFAULTS.items()}

    def _save(self):
        try:
            import json
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.CONFIG_PATH.write_text(
                json.dumps(self._cfg, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def get(self, key: str) -> bool:
        return self._cfg.get(key, self.DEFAULTS.get(key, (None, None, True))[2])

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(6)

        title = QLabel("Ayarlar"); title.setObjectName("section_title")
        lay.addWidget(title)
        sub = QLabel("Değişiklikler anında uygulanır ve kaydedilir.")
        sub.setStyleSheet("color:#2e3a55;font-size:12px;background:transparent;")
        lay.addWidget(sub)
        lay.addSpacing(10)

        # Bölümlere göre grupla
        sections: dict[str, list[str]] = {}
        for key, (sec, lbl, _) in self.DEFAULTS.items():
            sections.setdefault(sec, []).append(key)

        for sec, keys in sections.items():
            # Bölüm başlığı
            sl = QLabel(sec)
            sl.setStyleSheet("color:#2e3a55;font-size:10px;font-weight:700;"
                             "font-family:'JetBrains Mono',monospace;"
                             "letter-spacing:.08em;text-transform:uppercase;"
                             "background:transparent;margin-top:12px;")
            lay.addWidget(sl)

            for key in keys:
                _, lbl, default = self.DEFAULTS[key]
                state = self._cfg.get(key, default)
                lay.addWidget(self._make_row(key, lbl, state))

        # ── Tema Bölümü ──────────────────────────────────────────────────────
        lay.addSpacing(16)
        theme_hdr = QLabel("Tema")
        theme_hdr.setStyleSheet("color:#2e3a55;font-size:10px;font-weight:700;"
                                "font-family:'JetBrains Mono',monospace;"
                                "letter-spacing:.08em;text-transform:uppercase;"
                                "background:transparent;margin-top:12px;")
        lay.addWidget(theme_hdr)

        self._theme_grid = QWidget()
        self._theme_grid.setStyleSheet("background:transparent;")
        tg_lay = QGridLayout(self._theme_grid)
        tg_lay.setSpacing(8); tg_lay.setContentsMargins(0,0,0,0)
        self._theme_cards: dict[str, QWidget] = {}
        self._build_theme_grid(tg_lay)
        lay.addWidget(self._theme_grid)

        # Sıfırla butonu
        lay.addSpacing(16)
        reset_btn = QPushButton("↺  Varsayılanlara Sıfırla")
        reset_btn.setObjectName("open_btn")
        reset_btn.setFixedHeight(34); reset_btn.setFixedWidth(220)
        reset_btn.clicked.connect(self._reset)
        lay.addWidget(reset_btn)
        lay.addStretch()

    def _build_theme_grid(self, grid_lay: QGridLayout):
        from ui.styles import THEMES
        current = self._cfg.get('theme', 'Arch Midnight')
        for i, (name, t) in enumerate(THEMES.items()):
            card = self._make_theme_card(name, t, name == current)
            self._theme_cards[name] = card
            grid_lay.addWidget(card, i // 3, i % 3)

    def _make_theme_card(self, name: str, t: dict, active: bool) -> QWidget:
        card = QWidget(); card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        card.setFixedHeight(64)
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Animasyon için
        card._active = active
        card._hover_alpha = 0
        card._anim = QTimer(); card._anim.setInterval(12)

        bg    = t.get("bg",    "#070b14")
        panel = t.get("panel", "#0b1120")
        ac    = t.get("ac",    "#f97316")
        hi    = t.get("hi",    "#60a5fa")
        bdr_color = ac if active else "rgba(255,255,255,0.08)"

        card.setStyleSheet(
            f"QWidget{{background:{panel};border:2px solid {bdr_color};"
            f"border-radius:10px;}}")

        lay = QHBoxLayout(card); lay.setContentsMargins(10, 8, 10, 8); lay.setSpacing(8)

        # Renk önizleme çemberleri
        swatch_w = QWidget(); swatch_w.setFixedSize(40, 40)
        swatch_w.setStyleSheet("background:transparent;")
        sw_lay = QHBoxLayout(swatch_w); sw_lay.setContentsMargins(0,0,0,0); sw_lay.setSpacing(3)
        for color in (bg, ac, hi):
            dot = QWidget(); dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background:{color};border-radius:5px;")
            sw_lay.addWidget(dot)
        lay.addWidget(swatch_w)

        # İsim
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(
            f"color:{'#e2e8f8' if active else '#6b7a99'};"
            "font-size:11px;font-weight:600;background:transparent;")
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl, 1)

        # Aktif işareti
        if active:
            check = QLabel("✓")
            check.setStyleSheet(f"color:{ac};font-size:14px;font-weight:700;"
                                "background:transparent;")
            lay.addWidget(check)
            card._check_lbl = check
        else:
            card._check_lbl = None

        card._name_lbl = name_lbl
        card._theme_name = name
        card._theme_t = t

        card.mousePressEvent = lambda e, n=name, c=card: self._select_theme(n, c)
        return card

    def _select_theme(self, name: str, clicked_card: QWidget):
        """Tema seç — kart stilini güncelle, ana pencereye uygula"""
        from ui.styles import THEMES
        self._cfg['theme'] = name
        self._save()

        for card_name, card in self._theme_cards.items():
            t = THEMES.get(card_name, {})
            ac = t.get("ac", "#f97316")
            is_active = (card_name == name)
            card.setStyleSheet(
                f"QWidget{{background:{t.get('panel','#0b1120')};"
                f"border:2px solid {''+ac if is_active else 'rgba(255,255,255,0.08)'};"
                f"border-radius:10px;}}")
            card._name_lbl.setStyleSheet(
                f"color:{'#e2e8f8' if is_active else '#6b7a99'};"
                "font-size:11px;font-weight:600;background:transparent;")
            # Checkmark
            if hasattr(card, '_check_lbl') and card._check_lbl:
                card._check_lbl.deleteLater()
                card._check_lbl = None
            if is_active:
                check = QLabel("✓")
                check.setStyleSheet(f"color:{ac};font-size:14px;font-weight:700;"
                                    "background:transparent;")
                card.layout().addWidget(check)
                card._check_lbl = check

        # Ana pencereye uygula
        main_win = self.window()
        if hasattr(main_win, 'apply_theme'):
            main_win.apply_theme(name)

    def _make_row(self, key: str, label: str, state: bool) -> QWidget:
        w = QWidget(); w.setObjectName("settings_row")
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        rl = QHBoxLayout(w); rl.setContentsMargins(18, 11, 18, 11); rl.setSpacing(12)

        lbl = QLabel(label)
        lbl.setStyleSheet("background:transparent;color:#e2e8f8;font-size:13px;")
        rl.addWidget(lbl, 1)

        # Durum metni
        state_lbl = QLabel("Açık" if state else "Kapalı")
        state_lbl.setFixedWidth(44)
        state_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        state_lbl.setStyleSheet(
            f"color:{'#4ade80' if state else '#6b7a99'};"
            "font-size:11px;background:transparent;"
            "font-family:'JetBrains Mono',monospace;")
        rl.addWidget(state_lbl)

        sw = ToggleSwitch(state)
        self._switches[key] = sw

        def on_toggle(val, k=key, sl=state_lbl):
            self._cfg[k] = val
            self._save()
            sl.setText("Açık" if val else "Kapalı")
            sl.setStyleSheet(
                f"color:{'#4ade80' if val else '#6b7a99'};"
                "font-size:11px;background:transparent;"
                "font-family:'JetBrains Mono',monospace;")
            self.setting_changed.emit(k, val)

        sw.toggled.connect(on_toggle)
        rl.addWidget(sw)
        return w

    def _reset(self):
        for key, (_, _, default) in self.DEFAULTS.items():
            self._cfg[key] = default
            if key in self._switches:
                self._switches[key].set_state(default, animate=True)
            self.setting_changed.emit(key, default)
        self._save()
        # Durum etiketlerini de güncelle
        self._refresh_labels()

    def _refresh_labels(self):
        # Tüm satırları yeniden render et yerine switches üzerinden sinyal yolla
        for key, sw in self._switches.items():
            sw.set_state(self._cfg.get(key, True), animate=False)


# ─── Status Bar ───────────────────────────────────────────────────────────────

class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("status_bar"); self.setFixedHeight(34)
        lay = QHBoxLayout(self); lay.setContentsMargins(22,0,22,0); lay.setSpacing(0)
        self._pkg  = self._item("●", "57,420 paket", dot=True)
        self._dl   = self._item("↓",  "0 KB/s")
        self._cpu  = self._item("⚡", "CPU 0%")
        self._ram  = self._item("▣",  "RAM 0/8 GB")
        for w in (self._pkg, self._dl, self._cpu, self._ram):
            lay.addWidget(w); lay.addWidget(self._sep())
        lay.addStretch()

    def _item(self, icon: str, text: str, dot: bool = False) -> QWidget:
        w = QWidget()
        hl = QHBoxLayout(w); hl.setContentsMargins(0,0,16,0); hl.setSpacing(6)
        if dot:
            d = QLabel(icon)
            d.setStyleSheet("color:#f97316;font-size:8px;background:transparent;")
            hl.addWidget(d)
        else:
            ic = QLabel(icon); ic.setObjectName("status_item"); hl.addWidget(ic)
        tx = QLabel(text); tx.setObjectName("status_item"); hl.addWidget(tx)
        w._lbl = tx; return w

    def _sep(self) -> QFrame:
        f = QFrame(); f.setFrameShape(QFrame.Shape.VLine)
        f.setStyleSheet("QFrame{color:rgba(255,255,255,0.04);}"); f.setContentsMargins(0,6,16,6)
        return f

    def update_stats(self, s: dict):
        self._pkg._lbl.setText(f"{s.get('packages_count',57420):,} paket")
        self._cpu._lbl.setText(f"CPU {s.get('cpu',0):.0f}%")
        self._ram._lbl.setText(
            f"RAM {s.get('ram_used',0):.1f} / {s.get('ram_total',8):.0f} GB")

    def update_speed(self, mbps: float):
        self._dl._lbl.setText(f"{mbps*1024:.0f} KB/s" if mbps < 0.1 else f"{mbps:.1f} MB/s")


# ─── Main Window ─────────────────────────────────────────────────────────────

class ArchPackageStore(QMainWindow):
    def __init__(self):
        super().__init__()
        self.hub = PackageManagerHub()
        self._history   = HistoryManager()
        self._favorites = FavoritesManager()
        self._queue     = DownloadQueue()
        self.setWindowTitle("Arxis")
        self.setMinimumSize(900, 600); self.resize(1380, 840)
        self._current_theme = "Arch Midnight"
        self.setStyleSheet(DARK_THEME)
        self._workers: list[QThread] = []
        self._build_ui()
        self._apply_saved_settings()
        self._start_monitors()

    def apply_theme(self, theme_name: str):
        """Temayı anında uygula ve kaydet"""
        from ui.styles import THEMES, build_theme
        t = THEMES.get(theme_name)
        if not t:
            return
        self._current_theme = theme_name
        qss = build_theme(t)
        self.setStyleSheet(qss)
        # Kaydedilmiş ayarlara yaz
        if hasattr(self, '_setts'):
            self._setts._cfg['theme'] = theme_name
            self._setts._save()

    def _apply_saved_settings(self):
        if not hasattr(self, '_setts'): return
        for key in ("aur", "flatpak", "appimage", "wine"):
            enabled = self._setts.get(key)
            self.hub.set_source_enabled(key, enabled)
        # Kaydedilmiş temayı uygula
        saved_theme = self._setts._cfg.get('theme', 'Arch Midnight')
        if saved_theme != 'Arch Midnight':
            self.apply_theme(saved_theme)

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        rl = QHBoxLayout(root); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        self._sidebar = CollapsibleSidebar()
        self._sidebar.nav_clicked.connect(self._nav)
        rl.addWidget(self._sidebar)
        self._right = self._build_right()
        rl.addWidget(self._right, 1)
        self._drawer  = ActionDrawer(self._right)
        # Ö-7: PackageDetailPanel (eski) kaldırıldı — _detail_page (yeni) kullanılıyor
        # Eski referans _show_detail() → _show_detail_page() ile yönlendiriliyor
        self._compare = ComparePanel(self._right)
        self._notifs  = NotificationManager(self._right)

    def _build_right(self) -> QWidget:
        w = QWidget()
        rl = QVBoxLayout(w); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)
        rl.addWidget(self._build_topbar())

        self._stack = QStackedWidget()

        # Detay sayfası (idx=0 — özel, geri butonu ile çıkılır)
        self._detail_page = PackageDetailPage(self.hub)
        self._detail_page.action.connect(self._handle_action)
        self._detail_page.compare_requested.connect(self._handle_compare)
        self._detail_page.back_requested.connect(self._detail_page_back)

        self._discover  = DiscoverPage(self.hub)
        self._discover.action.connect(self._handle_action)
        self._discover.compare_requested.connect(self._handle_compare)
        self._discover.detail_requested.connect(self._show_detail_page)

        self._search    = SearchPage()
        self._search.action.connect(self._handle_action)
        self._search.compare_requested.connect(self._handle_compare)
        self._search.detail_requested.connect(self._show_detail_page)

        self._installed = InstalledPage(self.hub)
        self._installed.action.connect(self._handle_action)
        self._installed.detail_requested.connect(self._show_detail_page)
        self._installed.bulk_action.connect(self._handle_bulk)
        self._installed.compare_requested.connect(self._handle_compare)

        self._cats  = CategoriesPage(self.hub)
        self._cats.action.connect(self._handle_action)
        self._cats.compare_requested.connect(self._handle_compare)
        self._cats.detail_requested.connect(self._show_detail_page)

        # Beğeni ve kuyruk sinyallerini tüm sayfalara bağla
        for page in (self._discover, self._search, self._installed, self._cats):
            if hasattr(page, 'favorite_requested'):
                page.favorite_requested.connect(self._handle_favorite)
            if hasattr(page, 'queue_requested'):
                page.queue_requested.connect(self._handle_queue)

        self._hist  = HistoryPage(self._history)
        self._favs  = FavoritesPage(self._favorites, self.hub)
        self._favs.action.connect(self._handle_action)
        self._favs.detail_requested.connect(self._show_detail_page)
        self._qpage = QueuePage(self._queue)
        self._qpage.install_all.connect(self._handle_bulk_install)
        self._snap  = SnapshotPage(self.hub)
        self._snap.install_requested.connect(self._handle_bulk_install)
        self._ghub  = GitHubPage()
        self._ghub._topbar_cb = lambda name, pct, spd: self._update_topbar_download(name, pct, spd)
        self._maint = MaintenancePage(self.hub)
        self._setts = SettingsPage()
        self._setts.setting_changed.connect(self._on_setting_changed)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea{border:none;background:#070b14;}")
        # Stack sırası: detail=0, discover=1, search=2, installed=3,
        #               cats=4, hist=5, favs=6, queue=7, snap=8, github=9, maint=10, setts=11
        for pg in (self._detail_page, self._discover, self._search, self._installed,
                   self._cats, self._hist, self._favs, self._qpage,
                   self._snap, self._ghub, self._maint, self._setts):
            self._stack.addWidget(pg)
        scroll.setWidget(self._stack)
        self._stack.setCurrentIndex(1)   # Başlangıç: discover

        rl.addWidget(scroll, 1)
        self._status = StatusBar(); rl.addWidget(self._status)
        return w

    def _build_topbar(self) -> QFrame:
        tb = QFrame(); tb.setObjectName("top_bar"); tb.setFixedHeight(64)
        lay = QHBoxLayout(tb); lay.setContentsMargins(24,10,24,10); lay.setSpacing(12)

        self._page_title = QLabel("Keşfet")
        self._page_title.setStyleSheet(
            "color:white;font-size:18px;font-weight:700;background:transparent;")
        lay.addWidget(self._page_title)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("search_input")
        self._search_input.setPlaceholderText("paket, kategori veya komut ara…")
        self._search_input.setMinimumWidth(300); self._search_input.setMaximumWidth(480)
        self._search_input.returnPressed.connect(self._do_search)
        self._search_debounce = QTimer(); self._search_debounce.setSingleShot(True)
        self._search_debounce.setInterval(300)
        self._search_debounce.timeout.connect(self._do_search)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        lay.addWidget(self._search_input)
        lay.addStretch()

        # ── Aktif Görevler butonu ──────────────────────────────────────────
        self._tasks_btn = QPushButton("⚡ Görevler")
        self._tasks_btn.setObjectName("filter_btn")
        self._tasks_btn.setFixedHeight(32)
        self._tasks_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._tasks_btn.clicked.connect(self._show_tasks_drawer)
        self._tasks_btn.hide()   # görev yokken gizle
        lay.addWidget(self._tasks_btn)

        # ── Steam tarzı indirme göstergesi ───────────────────────────────
        self._dl_widget = QWidget()
        self._dl_widget.setFixedSize(200, 40)
        self._dl_widget.hide()
        dl_lay = QVBoxLayout(self._dl_widget)
        dl_lay.setContentsMargins(8, 4, 8, 4); dl_lay.setSpacing(2)

        dl_top = QHBoxLayout(); dl_top.setSpacing(6)
        self._dl_name_lbl = QLabel("İndiriliyor…")
        self._dl_name_lbl.setStyleSheet(
            "color:#e2e8f8;font-size:10px;background:transparent;"
            "font-family:'JetBrains Mono',monospace;")
        self._dl_speed_lbl = QLabel("")
        self._dl_speed_lbl.setStyleSheet(
            "color:#f97316;font-size:10px;background:transparent;"
            "font-family:'JetBrains Mono',monospace;")
        dl_top.addWidget(self._dl_name_lbl, 1)
        dl_top.addWidget(self._dl_speed_lbl)
        dl_lay.addLayout(dl_top)

        self._dl_bar = QProgressBar()
        self._dl_bar.setRange(0, 100); self._dl_bar.setValue(0)
        self._dl_bar.setFixedHeight(4)
        self._dl_bar.setTextVisible(False)
        self._dl_bar.setStyleSheet(
            "QProgressBar{background:#1e2d45;border-radius:2px;border:none;}"
            "QProgressBar::chunk{background:#f97316;border-radius:2px;}")
        dl_lay.addWidget(self._dl_bar)
        lay.addWidget(self._dl_widget)

        self._filters: dict[str, QPushButton] = {}
        return tb

    def _nav(self, key: str):
        # "compare" özel: panel aç, stack değişmesin
        if key == "compare":
            if hasattr(self, '_compare'):
                self._compare.slide_in()
            return

        # Ana sayfaya gidince history'yi temizle
        if hasattr(self, '_nav_history'):
            self._nav_history.clear()

        # detail=0, discover=1, search=2, installed=3,
        # cats=4, hist=5, favs=6, queue=7, snap=8, github=9, maint=10, setts=11
        idx    = {"discover":1,"installed":3,"categories":4,
                  "history":5,"favorites":6,"queue":7,
                  "snapshot":8,"github":9,"maintenance":10,"settings":11}
        titles = {"discover":"Keşfet","installed":"Yüklü Paketler",
                  "categories":"Kategoriler","history":"Kurulum Geçmişi",
                  "favorites":"Beğenilenler","queue":"İndirme Kuyruğu",
                  "snapshot":"Profil / Snapshot","github":"GitHub'dan Kur",
                  "maintenance":"Bakım & Güncelleme","settings":"Ayarlar"}
        self._page_title.setText(titles.get(key, key))
        self._sidebar.set_active(key)
        self._stack.setCurrentIndex(idx.get(key, 1))
        if key == "history":
            self._hist.refresh()
        elif key == "discover":
            self._discover.refresh()
        elif key == "favorites":
            self._favs.refresh()
        elif key == "queue":
            self._qpage.refresh()

    def _show_detail_page(self, pkg):
        """Sol tık → tam ekran detay sayfası — breadcrumb history ile"""
        # Mevcut konumu history stack'e ekle (detay sayfasındayken yeni detay açılırsa da ekle)
        if not hasattr(self, '_nav_history'):
            self._nav_history = []
        current_idx = self._stack.currentIndex()
        current_title = self._page_title.text()
        # Çok derin history'yi engelle (max 10)
        if len(self._nav_history) >= 10:
            self._nav_history.pop(0)
        self._nav_history.append((current_idx, current_title))

        self._detail_page.show_package(pkg, self.hub)
        self._page_title.setText(pkg.display_name)
        self._stack.setCurrentIndex(0)

    def _detail_page_back(self):
        """Geri — history stack'ten bir önceki konuma dön"""
        if not hasattr(self, '_nav_history') or not self._nav_history:
            # History boşsa Keşfet'e dön
            self._nav("discover")
            return
        prev_idx, prev_title = self._nav_history.pop()
        self._stack.setCurrentIndex(prev_idx)
        self._page_title.setText(prev_title)

    def _handle_compare(self, pkg):
        self._compare.add_package(pkg, self.hub)

    def _handle_favorite(self, pkg):
        if self._favorites.is_favorite(pkg):
            self._favorites.remove(pkg)
            self._notifs.show(f"★  {pkg.display_name} beğenilenlerden çıkarıldı.", success=False)
        else:
            self._favorites.add(pkg)
            self._notifs.show(f"★  {pkg.display_name} beğenilenlere eklendi!", success=True)

    def _handle_queue(self, pkg):
        if self._queue.add(pkg):
            count = self._queue.count()
            self._notifs.show(
                f"⊕  {pkg.display_name} kuyruğa eklendi. ({count} paket)", success=True)
            # Sidebar badge güncelle
            self._sidebar.set_badge("queue", str(count))
        else:
            self._notifs.show(f"  {pkg.display_name} zaten kuyrukta.", success=False)

    def _on_setting_changed(self, key: str, value: bool):
        """Ayar değişince ilgili bileşeni anında güncelle"""
        if key == "auto_update":
            if value:
                self._upd_check.start()
            else:
                self._upd_check.stop()
                self._sidebar.set_badge("maintenance", None)

        elif key == "notifications":
            # NotificationManager'a flag ekle
            self._notifs._enabled = value

        elif key == "live_search":
            # Ö-6: Doğru attribute: self._search_debounce (ana pencerede)
            if hasattr(self, '_search_debounce'):
                # Kapalıysa interval=0 → debounce yok, Enter gerekli
                # Açıksa interval=300ms → yazarken otomatik arama
                self._search_debounce.setInterval(300 if value else 0)
                # textChanged bağlantısını da güncelle
                try:
                    self._search_input.textChanged.disconnect()
                except Exception:
                    pass
                if value:
                    self._search_input.textChanged.connect(
                        lambda _: self._search_debounce.start()
                        if self._search_input.text().strip() else self._nav("discover"))

        elif key == "bandwidth":
            if hasattr(self._drawer, '_bw_graph'):
                self._drawer._bw_graph.setVisible(value)

        elif key == "animations":
            # T-3: Global flag güncelle — tüm slide paneller bunu okur
            import ui.main_window as _mw
            _mw.ANIMATIONS_ENABLED = value
            # ToggleSwitch animasyonlarını da kapat
            if not value:
                for sw in self._setts._switches.values():
                    sw._anim.setInterval(1)

        elif key in ("aur", "flatpak", "appimage", "wine"):
            # Ö-2: Hub'a bildir — arama ve kurulum bunu kontrol eder
            self.hub.set_source_enabled(key, value)
            src_name = {"aur":"AUR","flatpak":"Flatpak",
                        "appimage":"AppImage","wine":"Wine"}.get(key, key.upper())
            self._notifs.show(
                f"{'✓' if value else '✗'}  {src_name} kaynağı "
                f"{'etkinleştirildi' if value else 'devre dışı bırakıldı'}",
                success=value)

    def _filter(self, f: str):
        """T-2: Kategori bazlı filtreleme — Kategoriler sayfasına yönlendir"""
        if f == "Tümü":
            self._nav("discover")
            return
        # Kategori anahtar kelimesini bul
        filter_map = {
            "Ses":        "audio",
            "Geliştirme": "dev",
            "Oyun":       "gaming",
            "Sistem":     "system",
            "Grafik":     "graphics",
            "İnternet":   "internet",
            "Ofis":       "office",
            "Güvenlik":   "security",
        }
        cat_key = filter_map.get(f, f.lower())
        self._nav("categories")
        # Kategoriler sayfasını aç ve ilgili kategoriye git
        QTimer.singleShot(50, lambda: self._cats._on_cat_click(cat_key, f))

    def _show_tasks_drawer(self):
        """Aktif görevler butonuna tıklanınca drawer'ı öne getir"""
        if hasattr(self, '_drawer') and self._drawer.isVisible():
            self._drawer.raise_()
        else:
            self._notifs.show("Şu an aktif görev yok.", success=True)

    def _update_topbar_download(self, pkg_name: str, pct: int, speed_mbps: float):
        """Topbar indirme göstergesini güncelle"""
        if not hasattr(self, '_dl_widget'): return
        self._dl_widget.show()
        short = (pkg_name[:20] + "…") if len(pkg_name) > 20 else pkg_name
        self._dl_name_lbl.setText(short)
        if speed_mbps > 0:
            self._dl_speed_lbl.setText(
                f"{speed_mbps:.1f} MB/s" if speed_mbps >= 1 else f"{speed_mbps*1024:.0f} KB/s")
        self._dl_bar.setValue(max(0, min(100, pct)))
        self._tasks_btn.show()
        self._tasks_btn.setText(f"⚡ {short}")

    def _hide_topbar_download(self):
        if hasattr(self, '_dl_widget'):
            self._dl_widget.hide()
            self._tasks_btn.hide()

    def _on_search_text_changed(self, text: str):
        """U-3: Metin varsa debounce başlat, boşsa Keşfet'e dön"""
        if text.strip():
            self._search_debounce.start()
        else:
            self._search_debounce.stop()
            self._nav("discover")

    def _do_search(self):
        query = self._search_input.text().strip()
        if not query: self._nav("discover"); return
        self._page_title.setText(f'"{query}"')
        self._stack.setCurrentIndex(2)
        self._search.show_results([], query)

        # P-1: Önceki arama worker'ını iptal et
        if hasattr(self, '_active_search_worker') and self._active_search_worker:
            try:
                self._active_search_worker.done.disconnect()
                if self._active_search_worker.isRunning():
                    self._active_search_worker.quit()
            except Exception:
                pass
            if self._active_search_worker in self._workers:
                self._workers.remove(self._active_search_worker)

        w = SearchWorker(self.hub, query)
        w.done.connect(lambda pkgs: self._search.show_results(pkgs, query))
        w.finished.connect(lambda: (
            self._workers.remove(w) if w in self._workers else None,
            setattr(self, '_active_search_worker', None)))
        self._active_search_worker = w
        w.start(); self._workers.append(w)

    def _ask_sudo_password(self) -> bool:
        """Şifre diyaloğu göster. True = şifre alındı, False = iptal."""
        from backend.managers import BaseManager
        # Zaten şifre önbellekte varsa tekrar sorma
        if BaseManager._sudo_password:
            return True

        dlg = QDialog(self)
        dlg.setWindowTitle("Yetki Gerekiyor")
        dlg.setFixedWidth(400)
        dlg.setStyleSheet(
            "QDialog{background:#0d1526;}"
            "QLabel{color:#e2e8f8;background:transparent;}"
            "QLineEdit{background:#101828;color:#e2e8f8;border:1px solid #1e2d45;"
            "border-radius:8px;padding:10px 14px;font-size:13px;}"
            "QLineEdit:focus{border-color:#f97316;}"
            "QPushButton{border-radius:8px;padding:9px 22px;font-size:13px;font-weight:600;}"
        )
        lay = QVBoxLayout(dlg); lay.setContentsMargins(28, 24, 28, 24); lay.setSpacing(14)

        # İkon + başlık
        hdr = QHBoxLayout(); hdr.setSpacing(14)
        icon_lbl = QLabel("🔒")
        icon_lbl.setStyleSheet("font-size:32px;background:transparent;")
        hdr.addWidget(icon_lbl)
        title_col = QVBoxLayout(); title_col.setSpacing(4)
        t1 = QLabel("Yönetici Yetkisi Gerekiyor")
        t1.setStyleSheet("color:#e2e8f8;font-size:15px;font-weight:700;background:transparent;")
        t2 = QLabel("Bu işlem için sudo şifresi gerekiyor.")
        t2.setStyleSheet("color:#6b7a99;font-size:12px;background:transparent;")
        title_col.addWidget(t1); title_col.addWidget(t2)
        hdr.addLayout(title_col, 1)
        lay.addLayout(hdr)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame{color:rgba(255,255,255,0.06);}"); lay.addWidget(sep)

        user_lbl = QLabel("Kullanıcı")
        user_lbl.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;")
        lay.addWidget(user_lbl)
        import os
        user_field = QLineEdit(os.environ.get("USER", ""))
        user_field.setReadOnly(True)
        user_field.setStyleSheet("QLineEdit{background:#080f1e;color:#2e3a55;"
                                  "border:1px solid #0d1829;border-radius:8px;"
                                  "padding:10px 14px;font-size:13px;}")
        lay.addWidget(user_field)

        pw_lbl = QLabel("Şifre")
        pw_lbl.setStyleSheet("color:#2e3a55;font-size:11px;background:transparent;")
        lay.addWidget(pw_lbl)
        pw_field = QLineEdit(); pw_field.setEchoMode(QLineEdit.EchoMode.Password)
        pw_field.setPlaceholderText("••••••••")
        lay.addWidget(pw_field)

        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color:#f87171;font-size:11px;background:transparent;")
        err_lbl.hide(); lay.addWidget(err_lbl)

        # Butonlar
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        cancel_btn = QPushButton("İptal")
        cancel_btn.setStyleSheet(
            "QPushButton{background:#172035;color:#6b7a99;border:1px solid #1e2d45;}"
            "QPushButton:hover{background:#1e2d45;color:#e2e8f8;}")
        ok_btn = QPushButton("Onayla")
        ok_btn.setStyleSheet(
            "QPushButton{background:#f97316;color:white;border:none;}"
            "QPushButton:hover{background:#ea6c10;}")
        ok_btn.setDefault(True)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(ok_btn)
        lay.addLayout(btn_row)

        result = {"ok": False}

        def on_ok():
            pw = pw_field.text()
            if not pw:
                err_lbl.setText("Şifre boş olamaz."); err_lbl.show(); return
            # Hızlı doğrulama: sudo -S true
            import subprocess
            r = subprocess.run(
                ["sudo", "-S", "-p", "", "true"],
                input=(pw + "\n").encode(),
                capture_output=True, timeout=5)
            if r.returncode == 0:
                BaseManager.set_sudo_password(pw)
                result["ok"] = True
                dlg.accept()
            else:
                err_lbl.setText("❌ Hatalı şifre, tekrar deneyin.")
                err_lbl.show()
                pw_field.clear(); pw_field.setFocus()

        ok_btn.clicked.connect(on_ok)
        cancel_btn.clicked.connect(dlg.reject)
        pw_field.returnPressed.connect(on_ok)
        pw_field.setFocus()
        dlg.exec()
        return result["ok"]

    def _handle_action(self, pkg: Package, action: str):
        from backend.managers import PackageSource
        needs_sudo = pkg.source in (PackageSource.PACMAN, PackageSource.AUR)
        if needs_sudo and action in ("install", "remove", "update"):
            if not self._ask_sudo_password():
                return
        self._drawer.start(pkg, action, self.hub)
        self._drawer.slide_in()
        # Topbar indirme göstergesi
        self._update_topbar_download(pkg.display_name, 0, 0)
        # Terminal çıktısından % değerini parse et + bant genişliğinden hız
        self._topbar_bytes = 0
        def _sync_speed():
            if not hasattr(self._drawer, '_bw_graph'): return
            samples = self._drawer._bw_graph._samples
            spd = samples[-1] if samples else 0.0
            # Terminal çıktısından yüzde satırını bul
            pct = 0
            try:
                term_text = self._drawer._term.toPlainText()
                import re
                # "xx%" veya "xx/100" gibi kalıplar
                m = re.findall(r'(\d{1,3})\s*%', term_text)
                if m: pct = min(99, int(m[-1]))
                # pacman "[######    ]" tarzı progress
                elif '##' in term_text:
                    bars = term_text.count('#')
                    pct = min(99, bars * 5)
            except Exception:
                pass
            self._update_topbar_download(pkg.display_name, pct, spd)
        self._topbar_sync = QTimer()
        self._topbar_sync.timeout.connect(_sync_speed)
        self._topbar_sync.start(500)
        # Önceki tüm bağlantıları kes (lambda birikimini önle)
        try:
            self._drawer._worker.done.disconnect()
        except (TypeError, AttributeError):
            pass
        self._drawer._worker.done.connect(
            lambda ok, msg, p=pkg, a=action: self._on_action_done(ok, msg, p, a))

    def _on_action_done(self, ok: bool, msg: str, pkg: Package, action: str):
        if hasattr(self, '_topbar_sync'):
            self._topbar_sync.stop()
        self._hide_topbar_download()
        verb = {"install": "kuruldu", "remove": "kaldırıldı",
                "update": "güncellendi", "open": "açıldı"}.get(action, "işlendi")
        self._notifs.show(f"{pkg.display_name} {verb}.", success=ok)
        if action != "open":
            self._history.record(pkg.name, pkg.version, pkg.source.value, action, ok)

        if ok and action in ("install", "remove", "update"):
            cache_key = f"{pkg.source.value}:{pkg.name}"
            from backend.managers import _DETAIL_CACHE
            _DETAIL_CACHE.pop(cache_key, None)
            if hasattr(self._detail_page, '_pkg_cache'):
                self._detail_page._pkg_cache.pop(cache_key, None)
            QTimer.singleShot(1000, self._refresh_installed)
        elif not ok:
            import sys
            print(f"[arxis] Kurulum başarısız: {msg[:100]}", file=sys.stderr)

    def _show_detail(self, pkg: Package):
        """Ö-7: Eski panel kaldırıldı — yeni tam sayfa kullan"""
        self._show_detail_page(pkg)

    def _handle_bulk_install(self, packages: list):
        """U-9: Snapshot eksik paket kurulumu"""
        if packages:
            self._handle_bulk(packages, "install")

    def _handle_bulk(self, packages: list, action: str):
        if not packages:
            return
        names = ", ".join(p.display_name for p in packages[:3])
        if len(packages) > 3:
            names += f" ve {len(packages)-3} diğeri"
        self._drawer._title_lbl.setText(
            f"Toplu {'Kurulum' if action=='install' else 'Kaldırma'}")
        self._drawer._pkg_lbl.setText(names)
        self._drawer._prog.setRange(0, 0)
        self._drawer._term.clear()
        self._drawer._finish_btn.setEnabled(False)
        self._drawer.show(); self._drawer.raise_(); self._drawer._place()
        self._drawer.slide_in()

        w = BulkActionWorker(self.hub, packages, action)
        w.line.connect(self._drawer._append)
        w.done.connect(lambda results: self._on_bulk_done(results, action))
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        w.start(); self._workers.append(w)

    def _on_bulk_done(self, results: list, action: str):
        ok_count  = sum(1 for _, ok, _ in results if ok)
        fail_count = len(results) - ok_count
        self._drawer._prog.setRange(0, 100); self._drawer._prog.setValue(100)
        self._drawer._finish_btn.setEnabled(True)
        if fail_count == 0:
            self._notifs.show(f"{ok_count} paket başarıyla işlendi.", success=True)
        else:
            self._notifs.show(f"{ok_count} başarılı, {fail_count} hatalı.", success=False)
        if ok_count > 0:
            QTimer.singleShot(500, self._refresh_installed)

    def _start_monitors(self):
        self._sys_mon = SystemMonitor()
        self._sys_mon.stats_updated.connect(self._status.update_stats)
        self._sys_mon.stats_updated.connect(self._sidebar.update_stats)
        self._sys_mon.start()
        self._net_mon = NetSpeedMonitor()
        self._net_mon.speed_updated.connect(self._status.update_speed)
        self._net_mon.speed_updated.connect(self._sidebar.update_net)
        self._net_mon.start()
        self._upd_check = UpdateCheckWorker(self.hub)
        self._upd_check.updates_found.connect(self._on_updates_found)
        self._upd_check.start()
        self._setup_shortcuts()
        # Ö-9: expac kontrolü — 2 saniye sonra yap (UI hazır olsun)
        QTimer.singleShot(2000, self._check_expac)

    def _check_expac(self):
        """expac kurulu değilse kullanıcıya bildir"""
        import shutil
        if not shutil.which("expac"):
            self._notifs.show(
                "⚡ expac kurulu değil — paket detayları yavaş yüklenir.\n"
                "Hızlandırmak için: sudo pacman -S expac",
                success=False)

    def _on_updates_found(self, count: int):
        if count > 0:
            self._sidebar.set_badge("maintenance", str(count))
            self._notifs.show(f"{count} güncelleme mevcut.", success=True)
        else:
            self._sidebar.set_badge("maintenance", "")

    def _setup_shortcuts(self):
        # Ctrl+F → arama kutusuna odaklan
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: (self._search_input.setFocus(), self._search_input.selectAll()))
        # Esc → açık paneli kapat veya detay sayfasından geri dön
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_escape)
        # Ctrl+R → yüklü paketleri yenile
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self._refresh_installed)

    def _on_escape(self):
        """T-8: Esc — detay sayfasındaysa geri dön, yoksa panelleri kapat"""
        if self._stack.currentIndex() == 0:
            # Detail page açık — geri dön
            self._detail_page_back()
        else:
            self._close_panels()

    def _close_panels(self):
        if hasattr(self, '_compare') and self._compare.isVisible():
            self._compare.slide_out()
        elif hasattr(self, '_drawer') and self._drawer.isVisible():
            self._drawer.slide_out()

    def _refresh_installed(self):
        if hasattr(self, '_installed'):
            self._installed._load()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        QTimer.singleShot(0, self._reposition_panels)

    def _reposition_panels(self):
        if hasattr(self, '_drawer')  and self._drawer.isVisible():  self._drawer._place()
        if hasattr(self, '_compare') and self._compare.isVisible(): self._compare._place()
        if hasattr(self, '_notifs'): self._notifs._reposition()

    @staticmethod
    def _refresh(w: QWidget):
        w.style().unpolish(w); w.style().polish(w)

    def closeEvent(self, event):
        # Timer'ları durdur
        for attr in ('_topbar_sync', '_search_debounce'):
            t = getattr(self, attr, None)
            if t: t.stop()

        # stop() → wait() sırasıyla: önce hepsini durdur, sonra bekle
        monitors = []
        for attr in ('_sys_mon', '_net_mon', '_upd_check'):
            t = getattr(self, attr, None)
            if t:
                try: t.stop()
                except Exception: pass
                monitors.append(t)

        # Diğer worker'lar
        extras = []
        for attr in ('_drawer', '_detail_page', '_discover'):
            page = getattr(self, attr, None)
            if page:
                for wattr in ('_worker', '_details_worker', '_upd_worker',
                              '_orphan_worker', '_sysinfo_worker', '_sim_worker'):
                    w = getattr(page, wattr, None)
                    if w and isinstance(w, QThread):
                        extras.append(w)

        all_threads = monitors + extras + list(self._workers)

        # Hepsini bekle
        for t in all_threads:
            try:
                if t and t.isRunning():
                    t.quit()
                    if not t.wait(2000):
                        t.terminate()
                        t.wait(500)
            except Exception:
                pass

        self._workers.clear()
        event.accept()