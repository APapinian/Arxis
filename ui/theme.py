"""
Tema ve renk paleti tanımlamaları
"""

COLORS = {
    # Ana renkler
    "bg_primary": "#0D1117",
    "bg_secondary": "#161B22",
    "bg_tertiary": "#1C2128",
    "bg_card": "#1E2430",
    "bg_hover": "#252D3A",
    "bg_active": "#1A3A5C",

    # Kenar çizgileri
    "border": "#30363D",
    "border_light": "#21262D",

    # Metin
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted": "#6E7681",
    "text_accent": "#58A6FF",

    # Vurgu renkleri
    "accent_blue": "#1F6FEB",
    "accent_blue_hover": "#388BFD",
    "accent_blue_light": "#58A6FF",
    "accent_green": "#3FB950",
    "accent_orange": "#D29922",
    "accent_red": "#F85149",
    "accent_purple": "#BC8CFF",

    # Özel
    "sidebar_bg": "#0D1117",
    "sidebar_active": "#1A3A5C",
    "status_bar": "#161B22",
    "search_bg": "#21262D",
    "tag_bg": "#21262D",
    "tag_active_bg": "#1F6FEB",
}

STYLESHEET = """
QMainWindow {
    background-color: #0D1117;
}

/* Ana widget */
QWidget {
    background-color: #0D1117;
    color: #E6EDF3;
    font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
    font-size: 13px;
}

/* Scroll Bar */
QScrollBar:vertical {
    background: #161B22;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #30363D;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #58A6FF;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #161B22;
    height: 8px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #30363D;
    border-radius: 4px;
}

/* Search Bar */
QLineEdit#searchBar {
    background-color: #21262D;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 8px 16px 8px 40px;
    color: #E6EDF3;
    font-size: 14px;
    selection-background-color: #1F6FEB;
}
QLineEdit#searchBar:focus {
    border: 1px solid #58A6FF;
    background-color: #1C2128;
}
QLineEdit#searchBar::placeholder {
    color: #6E7681;
}

/* Butonlar */
QPushButton {
    border-radius: 6px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    border: none;
    cursor: pointer;
}
QPushButton#installBtn {
    background-color: #1F6FEB;
    color: #FFFFFF;
}
QPushButton#installBtn:hover {
    background-color: #388BFD;
}
QPushButton#installBtn:pressed {
    background-color: #1A5DC8;
}
QPushButton#updateBtn {
    background-color: #21262D;
    color: #E6EDF3;
    border: 1px solid #30363D;
}
QPushButton#updateBtn:hover {
    background-color: #30363D;
    border-color: #58A6FF;
    color: #58A6FF;
}
QPushButton#openBtn {
    background-color: #21262D;
    color: #E6EDF3;
    border: 1px solid #30363D;
}
QPushButton#openBtn:hover {
    background-color: #30363D;
}
QPushButton#removeBtn {
    background-color: #3D1A1A;
    color: #F85149;
    border: 1px solid #6B2020;
}
QPushButton#removeBtn:hover {
    background-color: #5A2020;
}
QPushButton#categoryBtn {
    background-color: #21262D;
    color: #8B949E;
    border: 1px solid #30363D;
    border-radius: 20px;
    padding: 5px 16px;
    font-size: 12px;
    font-weight: 500;
}
QPushButton#categoryBtn:hover {
    background-color: #30363D;
    color: #E6EDF3;
}
QPushButton#categoryBtn[active="true"] {
    background-color: #1F6FEB;
    color: #FFFFFF;
    border-color: #1F6FEB;
}

/* Sidebar Butonları */
QPushButton#sidebarBtn {
    background-color: transparent;
    color: #8B949E;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 400;
}
QPushButton#sidebarBtn:hover {
    background-color: #1C2128;
    color: #E6EDF3;
}
QPushButton#sidebarBtn[active="true"] {
    background-color: #1A3A5C;
    color: #58A6FF;
    font-weight: 600;
}

/* Card Widget */
QFrame#packageCard {
    background-color: #1E2430;
    border: 1px solid #21262D;
    border-radius: 10px;
}
QFrame#packageCard:hover {
    border-color: #30363D;
    background-color: #252D3A;
}
QFrame#featuredCard {
    border-radius: 12px;
    border: 1px solid #21262D;
}

/* Section Labels */
QLabel#sectionTitle {
    color: #E6EDF3;
    font-size: 16px;
    font-weight: 700;
}
QLabel#packageName {
    color: #E6EDF3;
    font-size: 14px;
    font-weight: 600;
}
QLabel#packageDesc {
    color: #8B949E;
    font-size: 12px;
}
QLabel#versionLabel {
    color: #6E7681;
    font-size: 11px;
}

/* Status Bar */
QFrame#statusBar {
    background-color: #161B22;
    border-top: 1px solid #21262D;
}
QLabel#statusItem {
    color: #6E7681;
    font-size: 11px;
}

/* Tab Widget */
QTabWidget::pane {
    border: none;
    background: #0D1117;
}
QTabBar::tab {
    background: transparent;
    color: #8B949E;
    padding: 8px 20px;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}
QTabBar::tab:selected {
    color: #58A6FF;
    border-bottom: 2px solid #1F6FEB;
}
QTabBar::tab:hover {
    color: #E6EDF3;
}

/* Tooltip */
QToolTip {
    background-color: #1C2128;
    color: #E6EDF3;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
}

/* Progress Bar */
QProgressBar {
    background-color: #21262D;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #1F6FEB;
    border-radius: 4px;
}

/* ComboBox */
QComboBox {
    background-color: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 5px 10px;
    color: #E6EDF3;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1C2128;
    border: 1px solid #30363D;
    selection-background-color: #1F6FEB;
    color: #E6EDF3;
}

/* Message Box */
QMessageBox {
    background-color: #1C2128;
}

/* Input Dialog */
QInputDialog {
    background-color: #1C2128;
}
"""
