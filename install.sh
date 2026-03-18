#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  Arxis — Kurulum Scripti
# ─────────────────────────────────────────────────────────────────────────────
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

info()    { echo -e "  ${CYAN}→${NC}  $1"; }
success() { echo -e "  ${GREEN}✓${NC}  $1"; }
warn()    { echo -e "  ${YELLOW}⚠${NC}  $1"; }
error()   { echo -e "  ${RED}✗${NC}  $1"; echo ""; exit 1; }
step()    { echo -e "\n${BOLD}${BLUE}[$1]${NC} $2"; }
line()    { echo -e "${DIM}────────────────────────────────────────────${NC}"; }

clear
echo ""
echo -e "${BOLD}${CYAN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║           Arxis — Kurulum Sihirbazı       ║"
echo "  ║    Arch Linux için Grafik Paket Yöneticisi ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${DIM}Kurulum birkaç dakika sürebilir. Sabırla bekleyin.${NC}"
echo ""; line

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 1: Python kontrolü ───────────────────────────────────────────────────────
step "1/5" "Python Kontrolü"

command -v python3 &>/dev/null || error "Python3 bulunamadı! sudo pacman -S python"

PYTHON_VER=$(python3 --version 2>&1 | cut -d' ' -f2)
PY_MINOR=$(echo "$PYTHON_VER" | cut -d'.' -f2)
[ "$PY_MINOR" -lt 11 ] && error "Python 3.11+ gerekli. Mevcut: $PYTHON_VER"

success "Python $PYTHON_VER"
[ -f "requirements.txt" ] && success "requirements.txt bulundu" || error "requirements.txt bulunamadı!"

# ── 2: venv ───────────────────────────────────────────────────────────────────
step "2/5" "Sanal Ortam (venv)"

# pip'i DAHA ÖNCE aramıyoruz — venv kendi pip'ini zaten içeriyor
if [ -d "venv" ]; then
    warn "Mevcut venv bulundu — yeniden kullanılıyor"
    warn "Sıfırdan kurmak için: rm -rf venv && bash install.sh"
else
    info "python3 -m venv venv çalıştırılıyor..."
    python3 -m venv venv
    success "venv oluşturuldu"
fi

# Bundan sonra SADECE venv içindeki pip/python kullan
VENV_PY="$SCRIPT_DIR/venv/bin/python"
VENV_PIP="$SCRIPT_DIR/venv/bin/pip"

[ -f "$VENV_PIP" ] && success "venv/bin/pip hazır" || error "venv/bin/pip bulunamadı — python3 venv modülü eksik olabilir: sudo pacman -S python"

# ── 3: pip güncelle ──────────────────────────────────────────────────────────
step "3/5" "pip Güncelleme"
info "venv içindeki pip güncelleniyor..."
"$VENV_PY" -m pip install --upgrade pip --quiet
success "pip güncellendi"

# ── 4: Bağımlılıklar ─────────────────────────────────────────────────────────
step "4/5" "Bağımlılıklar Kuruluyor"
info "requirements.txt:"
cat requirements.txt | while IFS= read -r line; do
    echo -e "    ${DIM}$line${NC}"
done
echo ""
"$VENV_PIP" install -r requirements.txt
echo ""; success "Tüm bağımlılıklar kuruldu"

# ── 5: Sistem araçları ────────────────────────────────────────────────────────
step "5/5" "Sistem Araçları"

if command -v yay &>/dev/null; then
    success "AUR: yay"
elif command -v paru &>/dev/null; then
    success "AUR: paru"
else
    warn "yay/paru bulunamadı — AUR desteği devre dışı"
    info "https://github.com/Jguer/yay"
fi

command -v flatpak &>/dev/null && success "flatpak" || { warn "flatpak yok — sudo pacman -S flatpak"; }
command -v expac   &>/dev/null && success "expac (hızlı detaylar)" || { warn "expac yok — sudo pacman -S expac"; }

# ── run scriptleri ────────────────────────────────────────────────────────────

cat > run.sh << 'RUNEOF'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; RED='\033[0;31m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
echo ""
echo -e "${BOLD}${CYAN}  ⚙  Arxis başlatılıyor...${NC}"
echo -e "${DIM}  Arch Linux Paket Yöneticisi${NC}"
echo ""
if [ ! -d "venv" ]; then
    echo -e "  ${RED}✗${NC}  Sanal ortam bulunamadı!"
    echo -e "  ${YELLOW}→${NC}  Önce: ${BOLD}bash install.sh${NC}"
    echo ""; exit 1
fi
source venv/bin/activate
echo -e "  ${GREEN}✓${NC}  venv aktif — Python: $(python --version 2>&1 | cut -d' ' -f2)"
echo -e "  ${GREEN}✓${NC}  Dizin: $SCRIPT_DIR"
echo -e "${DIM}  ──────────────────────────────────────────${NC}"
echo ""
python main.py "$@"
RUNEOF
chmod +x run.sh

cat > run.fish << 'FISHEOF'
#!/usr/bin/env fish
set SCRIPT_DIR (cd (dirname (status --current-filename)); and pwd)
cd $SCRIPT_DIR
echo ""
echo -e "\033[1m\033[36m  ⚙  Arxis başlatılıyor...\033[0m"
echo -e "\033[2m  Arch Linux Paket Yöneticisi\033[0m"
echo ""
if not test -d venv
    echo -e "\033[31m  ✗  Sanal ortam bulunamadı!\033[0m"
    echo -e "\033[33m  →  Önce: \033[1mbash install.sh\033[0m"
    echo ""; exit 1
end
source venv/bin/activate.fish
set PY_VER (python --version 2>&1 | string split ' ' | tail -1)
echo -e "\033[32m  ✓\033[0m  venv aktif — Python: $PY_VER"
echo -e "\033[32m  ✓\033[0m  Dizin: $SCRIPT_DIR"
echo -e "\033[2m  ──────────────────────────────────────────\033[0m"
echo ""
python main.py $argv
FISHEOF
chmod +x run.fish

# ── Özet ─────────────────────────────────────────────────────────────────────
SHELL_NAME=$(basename "$SHELL")
echo ""; line; echo ""
echo -e "${BOLD}${GREEN}  ✓  Kurulum tamamlandı!${NC}"
echo ""
echo -e "  Uygulamayı başlatmak için:"
echo ""
if [ "$SHELL_NAME" = "fish" ]; then
    echo -e "    ${BOLD}${CYAN}fish${NC}  →  ${BOLD}./run.fish${NC}"
    echo -e "    ${DIM}bash${NC}  →  ${DIM}./run.sh${NC}"
else
    echo -e "    ${BOLD}${CYAN}bash${NC}  →  ${BOLD}./run.sh${NC}"
    echo -e "    ${DIM}fish${NC}  →  ${DIM}./run.fish${NC}"
fi
echo ""; echo -e "  ${DIM}Dizin: $SCRIPT_DIR${NC}"; echo ""; line; echo ""