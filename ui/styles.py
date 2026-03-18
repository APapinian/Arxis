"""Arxis — Tema sistemi. build_theme(t) → QSS string döndürür."""

# ─── Yardımcı renk fonksiyonları ──────────────────────────────────────────────

def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip('#')
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    return 0.2126*r + 0.7152*g + 0.0722*b

def _hex_alpha(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r,g,b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def _darken(hex_color: str, amt: float) -> str:
    h = hex_color.lstrip('#')
    r = max(0, int(h[0:2],16) - int(255*amt))
    g = max(0, int(h[2:4],16) - int(255*amt))
    b = max(0, int(h[4:6],16) - int(255*amt))
    return f"#{r:02x}{g:02x}{b:02x}"

def _lighten(hex_color: str, amt: float) -> str:
    h = hex_color.lstrip('#')
    r = min(255, int(h[0:2],16) + int(255*amt))
    g = min(255, int(h[2:4],16) + int(255*amt))
    b = min(255, int(h[4:6],16) + int(255*amt))
    return f"#{r:02x}{g:02x}{b:02x}"


# ─── 30 Tema Paleti ───────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {
    "Arch Midnight":    {"bg":"#070b14","panel":"#0b1120","ac":"#f97316","hi":"#60a5fa","tx":"#e2e8f8","su":"#2e3a55","bdr":"rgba(255,255,255,0.055)"},
    "Ocean Depth":      {"bg":"#060d1a","panel":"#0a1525","ac":"#f97316","hi":"#38bdf8","tx":"#e2e8f8","su":"#2e3a55","bdr":"rgba(255,255,255,0.055)"},
    "Terminal Green":   {"bg":"#0a0f0a","panel":"#0f1a0f","ac":"#00ff41","hi":"#39ff14","tx":"#b0ffb0","su":"#1a3a1a","bdr":"rgba(0,255,65,0.15)"},
    "Tokyo Night":      {"bg":"#1a1b2e","panel":"#212138","ac":"#ff007c","hi":"#7aa2f7","tx":"#c0caf5","su":"#3b3d5a","bdr":"rgba(122,162,247,0.15)"},
    "Gruvbox Warm":     {"bg":"#282828","panel":"#32302f","ac":"#fabd2f","hi":"#b8bb26","tx":"#ebdbb2","su":"#504945","bdr":"rgba(250,189,47,0.15)"},
    "Catppuccin Mocha": {"bg":"#1e1e2e","panel":"#313244","ac":"#cba6f7","hi":"#89b4fa","tx":"#cdd6f4","su":"#585b70","bdr":"rgba(203,166,247,0.15)"},
    "Nord Arctic":      {"bg":"#2e3440","panel":"#3b4252","ac":"#88c0d0","hi":"#81a1c1","tx":"#eceff4","su":"#4c566a","bdr":"rgba(136,192,208,0.15)"},
    "Dracula Pro":      {"bg":"#22212c","panel":"#2d2b3d","ac":"#ff79c6","hi":"#bd93f9","tx":"#f8f8f2","su":"#6272a4","bdr":"rgba(255,121,198,0.15)"},
    "Sahara Dusk":      {"bg":"#1a1208","panel":"#251a0a","ac":"#e8a020","hi":"#c17f24","tx":"#f0d9a0","su":"#4a3a18","bdr":"rgba(232,160,32,0.15)"},
    "Cyberpunk 2077":   {"bg":"#0d0d0f","panel":"#14141a","ac":"#f5d800","hi":"#00d9ff","tx":"#e8e8f0","su":"#2a2a3a","bdr":"rgba(245,216,0,0.15)"},
    "Everforest":       {"bg":"#1e2326","panel":"#272e33","ac":"#a7c080","hi":"#83c092","tx":"#d3c6aa","su":"#475258","bdr":"rgba(167,192,128,0.15)"},
    "Crimson Dark":     {"bg":"#0c0808","panel":"#180d0d","ac":"#cc0000","hi":"#ff4444","tx":"#f0d0d0","su":"#3a1010","bdr":"rgba(204,0,0,0.20)"},
    "Rose Pine":        {"bg":"#191724","panel":"#1f1d2e","ac":"#ebbcba","hi":"#c4a7e7","tx":"#e0def4","su":"#403d52","bdr":"rgba(235,188,186,0.15)"},
    "Monochrome":       {"bg":"#000000","panel":"#111111","ac":"#ffffff","hi":"#888888","tx":"#eeeeee","su":"#333333","bdr":"rgba(255,255,255,0.10)"},
    "Ice Storm":        {"bg":"#dde6f0","panel":"#eaf1f8","ac":"#1d4ed8","hi":"#0369a1","tx":"#0f172a","su":"#475569","bdr":"rgba(29,78,216,0.20)","light":True},
    "Volcanic":         {"bg":"#111111","panel":"#1a1a1a","ac":"#ff4500","hi":"#ff8c00","tx":"#f0e8e0","su":"#3a2a1a","bdr":"rgba(255,69,0,0.20)"},
    "Bubble Gum":       {"bg":"#1a0e1a","panel":"#241424","ac":"#ff6eb4","hi":"#00e5cc","tx":"#f8d8f0","su":"#3a1e3a","bdr":"rgba(255,110,180,0.15)"},
    "Arabian Night":    {"bg":"#0e0e1a","panel":"#16162a","ac":"#d4af37","hi":"#c0392b","tx":"#f0e8d0","su":"#2e2a14","bdr":"rgba(212,175,55,0.15)"},
    "Bioluminescent":   {"bg":"#000008","panel":"#08080f","ac":"#00ffcc","hi":"#0066ff","tx":"#b0f0ff","su":"#001a30","bdr":"rgba(0,255,204,0.15)"},
    "Game Boy":         {"bg":"#0f380f","panel":"#1a4a1a","ac":"#8bac0f","hi":"#306230","tx":"#9bbc0f","su":"#1a3a1a","bdr":"rgba(139,172,15,0.20)"},
    "Obsidian":         {"bg":"#080808","panel":"#121212","ac":"#c0c0c0","hi":"#e8e8e8","tx":"#f0f0f0","su":"#444444","bdr":"rgba(192,192,192,0.10)"},
    "Synthwave":        {"bg":"#120b1e","panel":"#1e1030","ac":"#ff2d78","hi":"#00ffff","tx":"#f0d0ff","su":"#3a1a5a","bdr":"rgba(255,45,120,0.20)"},
    "Matcha":           {"bg":"#0d1a0d","panel":"#142414","ac":"#6aaa64","hi":"#c8b560","tx":"#d4e8c0","su":"#2a4a2a","bdr":"rgba(106,170,100,0.15)"},
    "Fox Fire":         {"bg":"#0d0e1a","panel":"#161728","ac":"#ff6b2b","hi":"#ff3d00","tx":"#f0d8c8","su":"#2e2010","bdr":"rgba(255,107,43,0.20)"},
    "Amulet":           {"bg":"#071520","panel":"#0e2030","ac":"#00b4d8","hi":"#ffd60a","tx":"#d0e8f0","su":"#1a3a4a","bdr":"rgba(0,180,216,0.15)"},
    "Midnight Jazz":    {"bg":"#080508","panel":"#120c12","ac":"#8b0000","hi":"#f5e6c8","tx":"#e8d8c0","su":"#3a2020","bdr":"rgba(139,0,0,0.20)"},
    "Matrix Redux":     {"bg":"#000300","panel":"#060f06","ac":"#00ff41","hi":"#008f11","tx":"#00cc33","su":"#003a00","bdr":"rgba(0,255,65,0.12)"},
    "Blueberry":        {"bg":"#10081a","panel":"#1a1028","ac":"#6c63ff","hi":"#a78bfa","tx":"#e0d8f8","su":"#2e2050","bdr":"rgba(108,99,255,0.15)"},
    "Coral Reef":       {"bg":"#060d1a","panel":"#0e1a2a","ac":"#ff6b6b","hi":"#4ecdc4","tx":"#f0e8f8","su":"#1a2a3a","bdr":"rgba(255,107,107,0.15)"},
    "Lantern Festival": {"bg":"#0a0500","panel":"#160b00","ac":"#e63946","hi":"#f4a261","tx":"#f8e8d0","su":"#3a1a00","bdr":"rgba(230,57,70,0.20)"},

    # ── Pastel Temalar ──────────────────────────────────────────────────────────
    "Pastel Cloud":     {"bg":"#f5f0ff","panel":"#ede8ff","ac":"#7c3aed","hi":"#a78bfa","tx":"#1e1b4b","su":"#6b7280","bdr":"rgba(124,58,237,0.18)","light":True},
    "Pastel Peach":     {"bg":"#fff5f0","panel":"#ffe8dc","ac":"#ea580c","hi":"#fb923c","tx":"#1c0a00","su":"#78716c","bdr":"rgba(234,88,12,0.18)","light":True},
    "Pastel Mint":      {"bg":"#f0faf4","panel":"#e0f5ea","ac":"#059669","hi":"#34d399","tx":"#022c22","su":"#6b7280","bdr":"rgba(5,150,105,0.18)","light":True},
    "Pastel Rose":      {"bg":"#fff0f5","panel":"#ffe0ed","ac":"#db2777","hi":"#f472b6","tx":"#1a0010","su":"#9ca3af","bdr":"rgba(219,39,119,0.18)","light":True},
    "Pastel Sky":       {"bg":"#f0f8ff","panel":"#e0f0ff","ac":"#0284c7","hi":"#38bdf8","tx":"#0c1a2e","su":"#64748b","bdr":"rgba(2,132,199,0.18)","light":True},
}

DEFAULT_THEME = "Arch Midnight"


def build_theme(t: dict) -> str:
    """Tema sözlüğünden tam QSS string oluştur"""
    bg    = t.get("bg",    "#070b14")
    panel = t.get("panel", "#0b1120")
    ac    = t.get("ac",    "#f97316")
    hi    = t.get("hi",    "#60a5fa")
    tx    = t.get("tx",    "#e2e8f8")
    su    = t.get("su",    "#2e3a55")
    bdr   = t.get("bdr",   "rgba(255,255,255,0.055)")
    is_light = t.get("light", False)

    ac_dim   = _hex_alpha(ac, 0.12)
    ac_med   = _hex_alpha(ac, 0.22)
    ac_bdr   = _hex_alpha(ac, 0.35)
    hi_dim   = _hex_alpha(hi, 0.12)
    hi_med   = _hex_alpha(hi, 0.22)
    hi_bdr   = _hex_alpha(hi, 0.30)
    panel2   = _lighten(panel, 0.04) if not is_light else _darken(panel, 0.04)
    # Açık temada hover çok açık renk vermemeli
    hover_bg = _darken(panel, 0.03) if is_light else _hex_alpha(tx, 0.025)
    # Açık temada widget arka planı transparent yerine bg rengi kullan
    widget_bg = bg if is_light else "transparent"
    search_bg = _darken(bg, 0.03) if is_light else _darken(bg, 0.02)

    return f"""
/* ─── Base ─── */
QMainWindow {{ background: {bg}; }}
QWidget {{ background: {widget_bg}; color: {tx}; font-family: 'Outfit', 'Segoe UI', sans-serif; }}
QDialog {{ background: {panel}; }}

/* ─── Açık tema fix: panel widget'ları doğru renk alsın ─── */
#sidebar, #top_bar, #status_bar, #glass_panel, #action_drawer,
#settings_row, #package_item, #search_input {{ background-color: inherit; }}

/* ─── Tooltip ─── */
QToolTip {{
    background: {panel}; color: {tx};
    border: 1px solid {ac_bdr};
    border-radius: 8px; padding: 8px 12px;
    font-size: 12px; opacity: 220;
}}

/* ─── Sidebar ─── */
#sidebar {{ background: {panel}; border-right: 1px solid {bdr}; }}

/* ─── Logo btn ─── */
#logo_btn {{ background: {ac_dim}; border: 1px solid {ac_bdr}; border-radius: 12px; }}
#logo_btn:hover {{ background: {ac_med}; }}

/* ─── Top bar ─── */
#top_bar {{ background: {panel}; border-bottom: 1px solid {bdr}; }}

/* ─── Search ─── */
#search_input {{
    background: {search_bg}; border: 1px solid {bdr};
    border-radius: 12px; color: {tx}; font-size: 13px; padding: 9px 14px;
    selection-background-color: {ac_dim};
}}
#search_input:focus {{ border: 1px solid {ac_bdr}; background: {panel}; }}

/* ─── Filter chips ─── */
#filter_btn {{
    background: transparent; border: 1px solid {bdr};
    border-radius: 10px; color: {su}; font-size: 12px; font-weight: 500; padding: 7px 16px;
}}
#filter_btn:hover {{ color: {tx}; background: {hover_bg}; }}
#filter_btn[active="true"] {{ background: {ac_dim}; border-color: {ac_bdr}; color: {ac}; }}

/* ─── Titles ─── */
#section_title {{ color: {tx}; font-size: 19px; font-weight: 700; background: transparent; }}

/* ─── Glass panel ─── */
#glass_panel {{ background: {panel}; border: 1px solid {bdr}; border-radius: 14px; }}

/* ─── Package rows ─── */
#package_item {{ background: transparent; border-bottom: 1px solid {bdr}; }}
#package_item:hover {{ background: {hover_bg}; }}
#package_name {{ color: {tx}; font-size: 13px; font-weight: 600; background: transparent; }}
#package_desc {{ color: {su}; font-size: 11px; background: transparent; font-family: 'JetBrains Mono', monospace; }}

/* ─── Buttons ─── */
#install_btn {{
    background: {hi_dim}; color: {'#1e40af' if is_light else hi};
    border: 1px solid {hi_bdr}; border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#install_btn:hover    {{ background: {hi_med}; }}
#install_btn:disabled {{ background: {panel}; color: {su}; border-color: transparent; }}

#remove_btn {{
    background: rgba(239,68,68,0.10); color: {'#b91c1c' if is_light else '#f87171'};
    border: 1px solid rgba(239,68,68,0.25); border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#remove_btn:hover {{ background: rgba(239,68,68,0.20); }}

#update_btn {{
    background: {ac_dim}; color: {ac};
    border: 1px solid {ac_bdr}; border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#update_btn:hover {{ background: {ac_med}; }}

#open_btn {{
    background: {panel}; color: {su}; border: 1px solid {bdr};
    border-radius: 9px; font-size: 12px; font-weight: 600; padding: 8px 20px;
}}
#open_btn:hover {{ background: {panel2}; color: {tx}; }}

/* ─── Status bar ─── */
#status_bar {{ background: {panel}; border-top: 1px solid {bdr}; }}
#status_item {{ color: {su}; font-size: 10px; font-family: 'JetBrains Mono', monospace; }}

/* ─── Scrollbars ─── */
QScrollBar:vertical {{ background: transparent; width: 4px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {bdr}; border-radius: 2px; min-height: 20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

/* ─── Progress ─── */
QProgressBar {{
    background: {panel}; border: none; border-radius: 4px; height: 6px; color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ac}, stop:1 {hi});
    border-radius: 4px;
}}

/* ─── Terminal ─── */
QTextEdit {{
    background: {bg}; color: {'#334155' if is_light else su}; border: 1px solid {bdr};
    border-radius: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 10px;
    selection-background-color: {ac_dim};
}}

/* ─── Drawer ─── */
#action_drawer {{ background: {panel}; }}

/* ─── Settings rows ─── */
#settings_row {{ background: {_darken(panel, 0.02) if is_light else _darken(panel, 0.01)}; border-radius: 10px; }}

/* ─── QLabel genel renk fix (açık tema) ─── */
QLabel {{ color: {tx}; background: transparent; }}
QPushButton {{ color: {tx}; }}
"""

    return f"""
/* ─── Base ─── */
QMainWindow {{ background: {bg}; }}
QWidget {{ background: transparent; color: {tx}; font-family: 'Outfit', 'Segoe UI', sans-serif; }}
QDialog {{ background: {panel}; }}

/* ─── Tooltip ─── */
QToolTip {{
    background: {panel}; color: {tx};
    border: 1px solid {ac_bdr};
    border-radius: 8px; padding: 8px 12px;
    font-size: 12px; opacity: 220;
}}

/* ─── Sidebar ─── */
#sidebar {{ background: {panel}; border-right: 1px solid {bdr}; }}

/* ─── Logo btn ─── */
#logo_btn {{ background: {ac_dim}; border: 1px solid {ac_bdr}; border-radius: 12px; }}
#logo_btn:hover {{ background: {ac_med}; }}

/* ─── Top bar ─── */
#top_bar {{ background: {panel}; border-bottom: 1px solid {bdr}; }}

/* ─── Search ─── */
#search_input {{
    background: {_darken(bg, 0.02)}; border: 1px solid {bdr};
    border-radius: 12px; color: {tx}; font-size: 13px; padding: 9px 14px;
    selection-background-color: {ac_dim};
}}
#search_input:focus {{ border: 1px solid {ac_bdr}; background: {panel}; }}

/* ─── Filter chips ─── */
#filter_btn {{
    background: transparent; border: 1px solid {bdr};
    border-radius: 10px; color: {su}; font-size: 12px; font-weight: 500; padding: 7px 16px;
}}
#filter_btn:hover {{ color: {tx}; background: {panel}; }}
#filter_btn[active="true"] {{ background: {ac_dim}; border-color: {ac_bdr}; color: {ac}; }}

/* ─── Titles ─── */
#section_title {{ color: {tx}; font-size: 19px; font-weight: 700; background: transparent; }}

/* ─── Glass panel ─── */
#glass_panel {{ background: {panel}; border: 1px solid {bdr}; border-radius: 14px; }}

/* ─── Package rows ─── */
#package_item {{ background: transparent; border-bottom: 1px solid {bdr}; }}
#package_item:hover {{ background: {tx_faint}; }}
#package_name {{ color: {tx}; font-size: 13px; font-weight: 600; background: transparent; }}
#package_desc {{ color: {su}; font-size: 11px; background: transparent; font-family: 'JetBrains Mono', monospace; }}

/* ─── Buttons ─── */
#install_btn {{
    background: {hi_dim}; color: {hi};
    border: 1px solid {hi_bdr}; border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#install_btn:hover    {{ background: {hi_med}; }}
#install_btn:disabled {{ background: {panel}; color: {su}; border-color: transparent; }}

#remove_btn {{
    background: rgba(239,68,68,0.10); color: #f87171;
    border: 1px solid rgba(239,68,68,0.18); border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#remove_btn:hover {{ background: rgba(239,68,68,0.20); }}

#update_btn {{
    background: {ac_dim}; color: {ac};
    border: 1px solid {ac_bdr}; border-radius: 8px;
    font-size: 11px; font-weight: 700; padding: 6px 14px;
}}
#update_btn:hover {{ background: {ac_med}; }}

#open_btn {{
    background: {panel}; color: {su}; border: 1px solid {bdr};
    border-radius: 9px; font-size: 12px; font-weight: 600; padding: 8px 20px;
}}
#open_btn:hover {{ background: {panel2}; color: {tx}; }}

/* ─── Status bar ─── */
#status_bar {{ background: {panel}; border-top: 1px solid {bdr}; }}
#status_item {{ color: {su}; font-size: 10px; font-family: 'JetBrains Mono', monospace; }}

/* ─── Scrollbars ─── */
QScrollBar:vertical {{ background: transparent; width: 4px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {bdr}; border-radius: 2px; min-height: 20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

/* ─── Progress ─── */
QProgressBar {{
    background: {panel}; border: none; border-radius: 4px; height: 6px; color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ac}, stop:1 {hi});
    border-radius: 4px;
}}

/* ─── Terminal ─── */
QTextEdit {{
    background: {bg}; color: {su}; border: 1px solid {bdr};
    border-radius: 10px; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 10px;
    selection-background-color: {ac_dim};
}}

/* ─── Drawer ─── */
#action_drawer {{ background: {panel}; }}

/* ─── Settings rows ─── */
#settings_row {{ background: {_darken(panel, 0.01)}; border-radius: 10px; }}
"""


# Varsayılan tema (geriye dönük uyumluluk)
DARK_THEME = build_theme(THEMES[DEFAULT_THEME])