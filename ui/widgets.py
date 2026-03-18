"""
Yeniden kullanılabilir UI bileşenleri
"""

from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont, QFontMetrics,
    QLinearGradient, QPainterPath
)

from ui.icons import PACKAGE_ICONS, SOURCE_LABELS
from backend.package_manager import Package, PackageSource


class PackageIconWidget(QWidget):
    """Paket ikonu - renkli daire + harf"""

    def __init__(self, package_name: str, size: int = 40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        icon_data = PACKAGE_ICONS.get(package_name.lower(),
                    PACKAGE_ICONS.get(package_name.split("-")[0].lower(),
                    PACKAGE_ICONS["default"]))
        self.bg_color = QColor(icon_data["bg"])
        self.fg_color = QColor(icon_data["color"])
        self.letter = icon_data["letter"]
        self.size = size

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = self.size // 2
        # Arka plan dairesi
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(QPen(self.fg_color.darker(150), 1))
        painter.drawRoundedRect(0, 0, self.size, self.size, radius // 2, radius // 2)
        # Harf
        font = QFont("Segoe UI", max(8, self.size // 4))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(self.fg_color))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.letter)


class SourceBadge(QLabel):
    """Kaynak etiketi (Pacman, AUR, Flatpak...)"""

    def __init__(self, source: PackageSource, parent=None):
        super().__init__(parent)
        src_data = SOURCE_LABELS.get(source.value, SOURCE_LABELS["pacman"])
        self.setText(src_data["text"])
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {src_data['bg']};
                color: {src_data['color']};
                border: 1px solid {src_data['color']}44;
                border-radius: 3px;
                padding: 1px 6px;
                font-size: 10px;
                font-weight: 600;
            }}
        """)
        self.setFixedHeight(18)


class PackageListCard(QFrame):
    """Küçük paket listesi kartı (Popular Packages için)"""
    install_clicked = pyqtSignal(object)  # Package
    remove_clicked = pyqtSignal(object)

    def __init__(self, package: Package, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("packageCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # İkon
        icon = PackageIconWidget(self.package.icon_name or self.package.name, 40)
        layout.addWidget(icon)

        # İsim + Açıklama
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_row = QHBoxLayout()
        name_label = QLabel(self.package.name)
        name_label.setObjectName("packageName")
        name_row.addWidget(name_label)
        name_row.addWidget(SourceBadge(self.package.source))
        name_row.addStretch()
        info_layout.addLayout(name_row)

        desc_label = QLabel(self.package.description)
        desc_label.setObjectName("packageDesc")
        info_layout.addWidget(desc_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Buton
        if self.package.installed:
            btn = QPushButton("Kaldır")
            btn.setObjectName("removeBtn")
            btn.clicked.connect(lambda: self.remove_clicked.emit(self.package))
        else:
            btn = QPushButton("Kur")
            btn.setObjectName("installBtn")
            btn.clicked.connect(lambda: self.install_clicked.emit(self.package))

        btn.setFixedSize(80, 32)
        self.action_btn = btn
        layout.addWidget(btn)


class UpdateCard(QFrame):
    """Güncelleme kartı"""
    update_clicked = pyqtSignal(object)

    def __init__(self, package: Package, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("packageCard")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # İkon
        icon = PackageIconWidget(self.package.icon_name or self.package.name, 36)
        layout.addWidget(icon)

        # Bilgi
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(self.package.name)
        name_label.setObjectName("packageName")
        info_layout.addWidget(name_label)

        ver_text = f"v{self.package.version} → v{self.package.new_version}" if self.package.new_version else f"v{self.package.version}"
        ver_label = QLabel(ver_text)
        ver_label.setObjectName("versionLabel")
        info_layout.addWidget(ver_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Güncelle butonu
        btn = QPushButton("Güncelle")
        btn.setObjectName("updateBtn")
        btn.setFixedSize(90, 32)
        btn.clicked.connect(lambda: self.update_clicked.emit(self.package))
        layout.addWidget(btn)


class FeaturedCard(QFrame):
    """Öne çıkan büyük kart"""
    action_clicked = pyqtSignal(object)

    GRADIENTS = {
        "vscode":      ("#1E3A5F", "#0D2137"),
        "libreoffice": ("#1A3A1F", "#0D1F0D"),
        "steam":       ("#1B2838", "#0D1520"),
        "default":     ("#1E2430", "#0D1117"),
    }

    def __init__(self, package: Package, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("featuredCard")
        self.setMinimumSize(260, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(170)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(6)

        # Başlık satırı
        header = QHBoxLayout()
        icon = PackageIconWidget(self.package.icon_name or self.package.name, 48)
        header.addWidget(icon)
        header.addSpacing(10)

        title_col = QVBoxLayout()
        name = QLabel(self.package.name.replace("-bin", "").replace("-fresh", "").title())
        name.setStyleSheet("color: #E6EDF3; font-size: 18px; font-weight: 700;")
        title_col.addWidget(name)
        desc = QLabel(self.package.description)
        desc.setStyleSheet("color: #8B949E; font-size: 12px;")
        title_col.addWidget(desc)
        header.addLayout(title_col)
        header.addStretch()
        layout.addLayout(header)
        layout.addStretch()

        # Buton
        if self.package.installed:
            btn = QPushButton("Aç")
            btn.setObjectName("openBtn")
        else:
            btn = QPushButton("Kur")
            btn.setObjectName("installBtn")

        btn.setFixedSize(100, 34)
        btn.clicked.connect(lambda: self.action_clicked.emit(self.package))
        layout.addWidget(btn)

        # Gradient arkaplan
        key = self.package.icon_name or "default"
        colors = self.GRADIENTS.get(key, self.GRADIENTS["default"])
        self.setStyleSheet(f"""
            QFrame#featuredCard {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {colors[0]}, stop:1 {colors[1]});
                border: 1px solid #21262D;
                border-radius: 12px;
            }}
        """)


class SearchResultCard(QFrame):
    """Arama sonucu kartı"""
    install_clicked = pyqtSignal(object)
    remove_clicked = pyqtSignal(object)

    def __init__(self, package: Package, parent=None):
        super().__init__(parent)
        self.package = package
        self.setObjectName("packageCard")
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # İkon
        icon = PackageIconWidget(self.package.name, 44)
        layout.addWidget(icon)

        # Bilgi
        info = QVBoxLayout()
        info.setSpacing(3)

        top_row = QHBoxLayout()
        name = QLabel(self.package.name)
        name.setObjectName("packageName")
        top_row.addWidget(name)
        top_row.addWidget(SourceBadge(self.package.source))

        ver = QLabel(f"v{self.package.version}")
        ver.setObjectName("versionLabel")
        top_row.addWidget(ver)
        top_row.addStretch()
        info.addLayout(top_row)

        desc = QLabel(self.package.description or "Açıklama yok")
        desc.setObjectName("packageDesc")
        desc.setWordWrap(True)
        info.addWidget(desc)

        layout.addLayout(info)
        layout.addStretch()

        # Buton
        if self.package.installed:
            btn = QPushButton("Kaldır")
            btn.setObjectName("removeBtn")
            btn.clicked.connect(lambda: self.remove_clicked.emit(self.package))
        else:
            btn = QPushButton("Kur")
            btn.setObjectName("installBtn")
            btn.clicked.connect(lambda: self.install_clicked.emit(self.package))

        btn.setFixedSize(80, 32)
        layout.addWidget(btn)


class StatusIndicator(QWidget):
    """Alt durum çubuğu göstergesi"""

    def __init__(self, icon: str, label: str, value: str, color: str = "#6E7681", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        # İkon (unicode emoji veya karakter)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {color}; font-size: 12px;")
        layout.addWidget(icon_lbl)

        self.value_label = QLabel(f"{label}: {value}")
        self.value_label.setObjectName("statusItem")
        layout.addWidget(self.value_label)

    def update_value(self, label: str, value: str):
        self.value_label.setText(f"{label}: {value}")


class NotificationToast(QFrame):
    """Bildirim popup'ı"""

    def __init__(self, message: str, success: bool = True, parent=None):
        super().__init__(parent)
        self.setFixedWidth(360)
        color = "#3FB950" if success else "#F85149"
        bg = "#1A3A1A" if success else "#3A1A1A"
        icon = "✓" if success else "✗"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {color}66;
                border-radius: 8px;
                padding: 4px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")
        icon_lbl.setFixedWidth(20)
        layout.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(f"color: {color}; font-size: 13px;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        # Otomatik kapat — önce hide(), sonra deleteLater()
        # Direkt deleteLater() kullanmak _reposition'da RuntimeError'a yol açar
        self._close_timer = QTimer(self)
        self._close_timer.setSingleShot(True)
        self._close_timer.timeout.connect(self._safe_close)
        self._close_timer.start(4000)

    def _safe_close(self):
        self.hide()
        self.deleteLater()